"""HTTP API (PRD 9): `uvicorn api.server:app`, base `/api/v1`.

`POST /query` calls `api.pipeline.answer_question`, the function the eval runner
calls, with the same config: the shipped path is the measured path. Only the
specified pipeline (`config_4_routed`) is served. Responses follow PRD 9's shapes
plus `backend`, `model_served` and `development` (OWNER DECISION, dev
generator): a `claude_cli` answer is a development answer and says so. Decisions
in TRADEOFFS ("HTTP API as first built"). Deferred endpoints: F-140.
"""

from __future__ import annotations

import threading
import time
import uuid

import psycopg
import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api import pipeline, tracing
from api.config import REPO_ROOT, eval_run, generation
from api.db import connect
from api.generate.generator import DEV_BACKENDS
from api.index.embed import EmbeddingCheckError
from eval.metrics.cost import DEV_NA, cost_per_query

FREEZE_FILE = REPO_ROOT / "api" / "corpus_freeze.yaml"
EXCERPT_CHARS = 400
NEAREST = 3
ABSTAIN_TEXT = {
    "insufficient_evidence": "The generator found the retrieved evidence insufficient to answer.",
    "xbrl_contradiction": (
        "A stated figure contradicted the cited filing's own XBRL data, so the answer was withheld."
    ),
    "verifier": "Too few of the answer's claims could be verified against the cited filings.",
    "unsupported": "This question is outside what the indexed SEC filings can answer.",
    "score_floor": "No retrieved evidence passed the relevance floor.",
}

CHUNK_SQL = """
    SELECT c.chunk_id, c.ticker, co.name, c.form_type, c.fiscal_year, c.fiscal_quarter,
           c.item_code, c.section_title, c.page_hint, c.chunk_type, c.text, f.source_url,
           c.accession, c.unit_scale
      FROM chunks c JOIN filings f USING (accession) JOIN companies co ON co.cik = c.cik
     WHERE c.chunk_id = ANY(%s)
"""
CHUNK_KEYS = ("chunk_id", "ticker", "company_name", "form_type", "fiscal_year", "fiscal_quarter",
              "item_code", "section_title", "page_hint", "chunk_type", "text", "source_url",
              "accession", "unit_scale")  # fmt: skip


class QueryRequest(BaseModel):
    question: str
    filters: dict | None = None
    options: dict | None = None


def excerpt(text: str) -> str:
    body = "\n".join(line for line in text.split("\n") if not line.startswith("["))
    body = body.strip() or text
    return body[:EXCERPT_CHARS]


def fetch_chunks(ids: list[str]) -> dict[str, dict]:
    if not ids:
        return {}
    with connect() as conn:
        rows = conn.execute(CHUNK_SQL, (sorted(set(ids)),)).fetchall()
    return {r[0]: dict(zip(CHUNK_KEYS, r, strict=True)) for r in rows}


def citation(meta: dict) -> dict:
    return {"chunk_id": meta["chunk_id"], "ticker": meta["ticker"],
            "company_name": meta["company_name"], "form_type": meta["form_type"],
            "fiscal_year": meta["fiscal_year"], "fiscal_quarter": meta["fiscal_quarter"],
            "item_code": meta["item_code"], "section_title": meta["section_title"],
            "page_hint": meta["page_hint"],  # null: not computed (F-55)
            "chunk_type": meta["chunk_type"], "excerpt": excerpt(meta["text"]),
            "source_url": meta["source_url"]}  # fmt: skip


def restated_in(xbrl: dict) -> str | None:
    """The other filing whose fact matches, when the cited filing's value was restated."""
    return xbrl.get("accession") if xbrl.get("status") == "restatement" else None


def claim_out(c: dict) -> dict:
    k = c.get("checks") or {}
    xbrl = k.get("xbrl") or {}
    return {"claim_id": c["claim_id"], "text": c["text"], "citations": c["citations"],
            "figure": c.get("figure"), "entailment_score": k.get("entail"),
            "numbers_grounded": k.get("numbers_grounded"), "unit_ok": k.get("unit_ok"),
            "xbrl": xbrl.get("status"), "xbrl_fact_value": xbrl.get("fact_value"),
            "restated_in": restated_in(xbrl)}  # fmt: skip


def confidence(r: dict) -> float | None:
    """Fraction of the generator's claims the gate kept; 0.0 on ABSTAIN; null while
    the verdict waits on the NLI threshold (F-125). Not a calibrated probability."""
    if r["verdict"] == "ABSTAIN":
        return 0.0
    pre, post = r.get("claims_pre") or [], r.get("claims_post")
    if post is None or not pre:
        return None
    return len(post) / len(pre)


def build_response(r: dict, chunks: dict[str, dict], latency_ms: int, prices: dict) -> dict:
    """PRD 9's /query response from a pipeline record."""
    dev = r.get("backend") in DEV_BACKENDS
    cost = cost_per_query([r], prices, dev)
    base = {
        "query_id": uuid.uuid4().hex, "verdict": r["verdict"],
        "backend": r.get("backend"), "model_served": r.get("model_served"), "development": dev,
        "confidence": confidence(r),
        "metadata": {
            "intent": r.get("intent"), "cache_hit": False, "latency_ms": latency_ms,
            "cost_usd": cost if isinstance(cost, float) else None,
            "cost_note": DEV_NA if cost == DEV_NA else (None if isinstance(cost, float) else cost),
            "chunks_retrieved": len(r.get("retrieved") or []),
            "chunks_used": len(r.get("generator_input") or []), "trace_id": None,
        },
    }  # fmt: skip
    if r["verdict"] == "ABSTAIN":
        model_reason = (r.get("structured") or {}).get("abstain_reason")
        reason = r.get("abstain_reason") or "verifier"
        near = [c for c in (r.get("retrieved_post_rerank") or r.get("retrieved") or [])][:NEAREST]
        return {**base, "answer": None,
                "abstain_reason": model_reason if reason == "insufficient_evidence" and model_reason
                else ABSTAIN_TEXT.get(reason, reason),
                "nearest_evidence": [{"chunk_id": c, "excerpt": excerpt(chunks[c]["text"]),
                                      "rerank_score": None} for c in near if c in chunks],
                "claims": [], "citations": []}  # fmt: skip
    shown = r["claims_post"] if r.get("claims_post") is not None else (r.get("claims_pre") or [])
    cited = sorted({x for c in shown for x in c["citations"]})
    return {**base, "answer": " ".join(c["text"].strip() for c in shown),
            "verification_pending": r["verdict"] == "PENDING_NLI",
            "claims": [claim_out(c) for c in shown],
            "citations": [citation(chunks[x]) for x in cited if x in chunks]}  # fmt: skip


def corpus_summary() -> dict:
    with connect() as conn:
        companies = conn.execute("SELECT ticker, name FROM companies ORDER BY ticker").fetchall()
        rows = conn.execute(
            "SELECT ticker, form_type, fiscal_year, count(*) FROM chunks GROUP BY 1, 2, 3 "
            "ORDER BY 1, 2, 3").fetchall()  # fmt: skip
        last = conn.execute("SELECT max(ingested_at) FROM filings").fetchone()[0]
    freeze = yaml.safe_load(FREEZE_FILE.read_text(encoding="utf-8"))
    by = {}
    for t, form, fy, n in rows:
        by.setdefault(t, []).append({"form_type": form, "fiscal_year": fy, "chunks": n})
    return {"companies": [{"ticker": t, "name": n, "chunks": by.get(t, [])} for t, n in companies],
            "total_chunks": sum(r[3] for r in rows),
            "last_ingested_at": last.isoformat() if last else None,
            "freeze": {k: freeze.get(k) for k in ("frozen_on", "parser_version",
                                                   "chunker_version")},
            "filings": freeze["totals"],
            "quarantined": [{k: f.get(k) for k in ("accession", "ticker", "form", "reason",
                                                   "finding")}
                            for f in freeze["filings"] if f["status"] != "parsed"]}  # fmt: skip


def health() -> dict:
    with connect() as conn:
        n, emb = conn.execute("SELECT count(*), count(embedding) FROM chunks").fetchone()
    gen = generation()
    return {"status": "ok", "database": "reachable", "chunks": n, "chunks_with_embeddings": emb,
            "pipeline": eval_run()["pipeline"], "backend": gen["backend"],
            "development": gen["backend"] in DEV_BACKENDS, "tracing": tracing.status()}  # fmt: skip


def check_length(ctx, question: str) -> None:
    """PRD 9's 422, before any model call: the question must fit the embedder's
    own window (no separate limit is invented)."""
    n = len(ctx.model.tokenizer(question, truncation=False)["input_ids"])
    if n > ctx.emb["max_seq_length"]:
        raise EmbeddingCheckError(
            f"question is {n} tokens, over max_seq_length {ctx.emb['max_seq_length']}"
        )


def load_context(conn):
    return pipeline.Context(conn, pipeline.SERVED_PIPELINE)


def load_prices() -> dict:
    from eval.runner import _prices

    return _prices()


def create_app() -> FastAPI:
    app = FastAPI(title="FilingQA", version="1", docs_url="/docs")
    state = {"ctx": None, "conn": None}
    lock = threading.Lock()

    @app.exception_handler(RequestValidationError)
    async def malformed(request: Request, exc: RequestValidationError):
        return JSONResponse(status_code=400, content={"error": "malformed request",
                                                      "detail": exc.errors()})  # fmt: skip

    @app.post("/api/v1/query")
    def query(req: QueryRequest):
        if not req.question.strip():
            raise HTTPException(400, "question is empty")
        if req.filters or req.options:
            raise HTTPException(400, "filters and options overrides are not supported yet (F-140)")
        run_cfg = eval_run()
        if run_cfg["pipeline"] != pipeline.SERVED_PIPELINE:
            raise HTTPException(503, f"configured pipeline {run_cfg['pipeline']} is not served")
        t0 = time.monotonic()
        with lock:  # one model set, one GPU: queries run one at a time
            try:
                if state["ctx"] is None:
                    state["conn"] = connect()
                    state["ctx"] = load_context(state["conn"])
                check_length(state["ctx"], req.question)
                with tracing.trace("query", pipeline=run_cfg["pipeline"]) as root:
                    if root is not None:
                        root.content("question", req.question)
                    r = pipeline.answer_question(state["conn"], state["ctx"], req.question,
                                                 generation(), run_cfg)  # fmt: skip
                    if root is not None:
                        root.set(verdict=r["verdict"], intent=r.get("intent"),
                                 backend=r.get("backend"))  # fmt: skip
            except EmbeddingCheckError as e:
                raise HTTPException(422, f"question exceeds the length limit: {e}") from e
            except psycopg.OperationalError as e:
                raise HTTPException(503, f"index unavailable: {e}") from e
        cited = [x for c in (r.get("claims_pre") or []) for x in c["citations"]]
        ids = [
            *cited,
            *(r.get("retrieved_post_rerank") or []),
            *(r.get("retrieved") or [])[:NEAREST],
        ]
        latency = int((time.monotonic() - t0) * 1000)
        return build_response(r, fetch_chunks(ids), latency, load_prices())

    @app.get("/api/v1/chunks/{chunk_id}")
    def chunk(chunk_id: str):
        rows = fetch_chunks([chunk_id])
        if chunk_id not in rows:
            raise HTTPException(404, f"no chunk {chunk_id}")
        m = rows[chunk_id]
        return {**citation(m), "text": m["text"], "accession": m["accession"],
                "unit_scale": m["unit_scale"]}  # fmt: skip

    @app.get("/api/v1/corpus/summary")
    def summary():
        return corpus_summary()

    @app.get("/api/v1/metrics")
    def metrics():
        from api import metrics as m

        return m.build()

    @app.get("/api/v1/health")
    def healthcheck():
        try:
            return health()
        except psycopg.OperationalError as e:
            return JSONResponse(status_code=503, content={"status": "unavailable",
                                                          "detail": str(e)})  # fmt: skip

    return app


app = create_app()
