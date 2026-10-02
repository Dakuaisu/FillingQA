"""The served and measured answer path (PRD 7.1-7.5): one function, used by
`POST /api/v1/query` and by `scripts.eval_run`, with the same config, so the
shipped path is the measured path.

`answer_question` runs the router, metadata filters and intent budgets, hybrid
retrieval with reranking, structured generation and the verification gate, and
returns the full record the eval stores (every list, every check).
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

import yaml

from api.config import REPO_ROOT, generation, rerank, retrieval, router
from api.generate import claude_cli
from api.generate.generator import generate, generate_structured

TEMPLATES = REPO_ROOT / "eval" / "templates.yaml"
TRANSPORT_RETRIES = 3
SERVED_PIPELINE = "config_4_routed"


class Context:
    """Everything loaded once per run: embedder, BM25 index, reranker."""

    def __init__(self, conn, pipeline: str):
        from api.index.embed import load_model
        from api.query.rerank import load_reranker
        from api.query.retrieve import load_bm25

        self.model, self.emb = load_model()
        self.rcfg, self.rrcfg = retrieval(), rerank()
        self.index = self.key = self.reranker = None
        if pipeline != "config_1_dense" and self.rcfg["sparse"]["backend"] == "bm25":
            self.index, _ = load_bm25(conn, self.rcfg["sparse"])
            self.key = self.index.key
        if pipeline in ("config_4_rerank", "config_4_routed"):
            self.reranker = load_reranker(self.rrcfg)
        if pipeline == "config_4_routed":
            from api.query.router import PERIOD_ENDS_SQL

            self.router = router()
            self.companies = yaml.safe_load(TEMPLATES.read_text(encoding="utf-8"))["company_names"]
            self.chunk_meta = conn.execute(
                "SELECT chunk_id, ticker, fiscal_year, fiscal_quarter, form_type FROM chunks"
            ).fetchall()
            self.period_ends = conn.execute(PERIOD_ENDS_SQL).fetchall()
        self.gate = None
        if generation().get("structured"):
            from api.verify.gate import Gate
            from api.verify.nli import Nli

            names = yaml.safe_load(TEMPLATES.read_text(encoding="utf-8"))["company_names"]
            self.gate = Gate(conn, names, Nli())


def texts_for(conn, ids: list[str]) -> dict[str, str]:
    rows = conn.execute("SELECT chunk_id, text FROM chunks WHERE chunk_id = ANY(%s)", (ids,))
    return dict(rows.fetchall())


def call_model(prompt_or_chunks, question, gen: dict, tier: str):
    """One generator or router call with eval_run's transport retries and served-model check."""
    from api.generate.generator import complete

    last = None
    for _ in range(TRANSPORT_RETRIES):
        try:
            if question is None:
                a = complete(prompt_or_chunks, gen, tier)
            elif gen.get("structured"):
                a = generate_structured(question, prompt_or_chunks, gen, tier)
            else:
                a = generate(question, prompt_or_chunks, gen, tier)
            break
        except claude_cli.TransportError as e:
            last = e
    else:
        raise last
    if gen[tier] not in a.model.split(","):
        raise claude_cli.CliError(f"served {a.model}, requested {gen[tier]}")
    return a


def answer_fields(a, given: list[str], ctx=None, question: str = "", texts=None,
                  nli_threshold: float | None = None) -> dict:  # fmt: skip
    """The answer part of a result. Structured (PRD 7.4): claims, the model's own
    abstention (`sufficient_evidence` false), contract violations, and the PRD 7.5
    gate's claims_pre / claims_post / verdict; plain: text only."""
    from api.generate.claims import contract_violations

    if a.structured is None:
        return {"answer": {"text": a.text, "claims": [], "abstained": False}, "verdict": "PASS"}
    doc = a.structured
    abstained = not doc["sufficient_evidence"]
    out = {"answer": {"text": a.text, "claims": doc["answer_claims"], "abstained": abstained},
           "verdict": "ABSTAIN" if abstained else "PASS", "structured": doc,
           "contract_violations": contract_violations(doc, given)}  # fmt: skip
    if abstained:
        out["abstain_reason"] = "insufficient_evidence"
    if ctx is not None and ctx.gate is not None:
        from api.verify.verdict import item_verdict

        g = ctx.gate.verify(question, doc["answer_claims"], given, texts or {}, nli_threshold)
        v, why = item_verdict(abstained, g["verify_verdict"], g["claims_pre"])
        out.update({"claims_pre": g["claims_pre"], "claims_post": g["claims_post"],
                    "gate_verdict": g["verify_verdict"], "verdict": v})  # fmt: skip
        if why:
            out["abstain_reason"] = why
    return out


def answer_question(
    conn, ctx: Context, question: str, gen: dict, run_cfg: dict, item_id: str | None = None
) -> dict:
    """PRD 7.1 router in front of Config 4: filters, and per intent the tier, k,
    top-n and sub-queries. Every query's lists are stored."""
    from api.query.rerank import rerank as rerank_one
    from api.query.retrieve import (
        Retrieved,
        dense_filtered_top_k,
        dense_search,
        embed_question,
        rrf_fuse,
    )
    from api.query.router import RouterParseError, allowed_chunks, filters, parse, render
    from eval.pipeline import budget_for, interleave, post_for_query, queries_for

    t0 = time.monotonic()
    rc, rr = ctx.rcfg, ctx.rrcfg
    ra = call_model(render(question, ctx.companies), None, gen, ctx.router["tier"])
    try:
        route, parse_error = parse(ra.text), None
    except RouterParseError as e:
        route, parse_error = None, str(e)
    intent, budget = budget_for(route, ctx.router["budgets"])
    f = None
    if route and rc.get("metadata_filter"):
        f = filters(route, set(ctx.companies), rc["filter_confidence_min"], ctx.period_ends)
    record = {
        "item_id": item_id, "pipeline": "config_4_routed",
        "router": {"response": ra.text, "model_served": ra.model, "parse_error": parse_error,
                   "usage": {"input_tokens": ra.input_tokens, "output_tokens": ra.output_tokens,
                             "cache_read_tokens": ra.cache_read_tokens,
                             "cache_creation_tokens": ra.cache_creation_tokens}},
        "intent": intent, "router_confidence": route["confidence"] if route else None,
        "filters": f, "budget": budget, "queries": [], "claims_pre": [], "claims_post": [],
    }  # fmt: skip
    if budget is None:  # unsupported: declined, no retrieval, no generator call (PRD 7.1)
        return {**record, "retrieved": [], "retrieved_post_rerank": [], "generator_input": [],
                "filter_zero_recall": False, "rerank_fell_back": False, "rerank_seconds": None,
                "answer": {"text": "", "claims": [], "abstained": True}, "verdict": "ABSTAIN",
                "abstain_reason": "unsupported", "tier": None, "model_served": None,
                "backend": gen["backend"], "usage": None,
                "latency_s": round(time.monotonic() - t0, 2),
                "answered_at": datetime.now(UTC).isoformat(timespec="seconds")}  # fmt: skip
    allowed = allowed_chunks(ctx.chunk_meta, f) if f else None
    k, w = budget["k"], rc["weights"]
    per_query = []
    for q in queries_for(question, route, budget):
        vec = embed_question(ctx.model, ctx.emb, q)
        fused, zero = [], False
        if allowed is not None:
            dense = dense_filtered_top_k(conn, vec, k, allowed) if allowed else []
            sp = [c for c, _ in ctx.index.search(q, k, allowed)]
            fused = rrf_fuse([dense, sp], [w["dense"], w["sparse"]], rc["rrf_k"])[:k]
            zero = not fused
        if not fused:  # unfiltered, or the filter returned nothing (filter_zero_recall)
            dense = dense_search(conn, vec, k, rc)
            sp = [c for c, _ in ctx.index.search(q, k)]
            fused = rrf_fuse([dense, sp], [w["dense"], w["sparse"]], rc["rrf_k"])[:k]
        texts = texts_for(conn, fused)
        ranked, secs = rerank_one(ctx.reranker, q, [(c, texts[c]) for c in fused])
        post, fell = post_for_query(fused, ranked, secs, rr, budget["top_n"])
        per_query.append({"query": q, "filter_zero_recall": zero, "retrieved": fused,
                          "retrieved_post_rerank": post, "rerank_seconds": secs,
                          "rerank_fell_back": fell})  # fmt: skip
    lists = [x["retrieved"] for x in per_query]
    retrieved = lists[0] if len(lists) == 1 else rrf_fuse(lists, [1.0] * len(lists), rc["rrf_k"])
    post = interleave([x["retrieved_post_rerank"] for x in per_query], budget["top_n"])
    record.update({
        "queries": per_query, "retrieved": retrieved, "retrieved_post_rerank": post,
        "generator_input": post, "tier": budget["tier"],
        "filter_zero_recall": any(x["filter_zero_recall"] for x in per_query),
        "rerank_fell_back": any(x["rerank_fell_back"] for x in per_query),
        "rerank_seconds": max(x["rerank_seconds"] for x in per_query),
    })  # fmt: skip
    if not post:  # every chunk below the score floor: no generator call (PRD 7.3)
        return {**record, "answer": {"text": "", "claims": [], "abstained": True},
                "verdict": "ABSTAIN", "abstain_reason": "score_floor", "model_served": None,
                "backend": gen["backend"], "usage": None,
                "latency_s": round(time.monotonic() - t0, 2),
                "answered_at": datetime.now(UTC).isoformat(timespec="seconds")}  # fmt: skip
    texts = texts_for(conn, post)
    a = call_model([Retrieved(c, 0.0, texts[c]) for c in post], question, gen,
                   budget["tier"])  # fmt: skip
    return {
        **record, **answer_fields(a, post, ctx, question, texts, run_cfg["nli_threshold"]),
        "model_served": a.model, "backend": a.backend,
        "usage": {"input_tokens": a.input_tokens, "output_tokens": a.output_tokens,
                  "cache_read_tokens": a.cache_read_tokens,
                  "cache_creation_tokens": a.cache_creation_tokens},
        "latency_s": round(time.monotonic() - t0, 2),
        "answered_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }  # fmt: skip
