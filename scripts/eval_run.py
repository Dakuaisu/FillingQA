"""Run the eval over candidate items and print the report (PRD 11.4).

python -m scripts.eval_run                     # plan only: no retrieval, no model call
python -m scripts.eval_run --run [--limit N]   # new run
python -m scripts.eval_run --resume RUN_ID     # continue a run from its results file
python -m scripts.eval_run --run --baseline-out eval/baselines/main.json

The pipeline is `eval_run.pipeline` (PRD 11.6 configs: config_1_dense,
config_3_hybrid, config_4_rerank; eval/pipeline.py). Each result stores the
pre-rerank list (`retrieved`), the reranked list, and what the generator received.

Each item's result is appended to eval/runs/<run_id>.results.jsonl as it
completes, so a killed process loses at most the item in flight; --resume skips
recorded items after checking the backend, datasets and freeze versions still
match the run's meta. A call with no usable response halts the run (exit 1) with
the error in <run_id>.errors.jsonl and the item left unrecorded. When no item is
pending, the report is written to <run_id>.json and printed. Refuses a baseline
path for a development backend before any work (F-59).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import uuid
from collections import Counter
from datetime import UTC, datetime

import yaml

from api.config import REPO_ROOT, baseline, eval_run, generation, rerank, retrieval
from api.generate import claude_cli
from api.generate.generator import generate, refuse_dev_baseline
from eval.runner import build_report, format_report
from scripts.write_freeze import FREEZE_FILE

DATASETS = sorted((REPO_ROOT / "eval" / "candidates").glob("*_candidates.jsonl"))
TIER = "tier_small"
TRANSPORT_RETRIES = 3


def arg(name: str) -> str | None:
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else None


def append(path, record: dict) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def read_jsonl(path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").split("\n") if x]


STAGES = {
    "config_1_dense": "dense top-k (no fusion, no rerank)",
    "config_3_hybrid": "BM25 + dense, RRF-fused pre-rerank list (no rerank)",
    "config_4_rerank": "BM25 + dense, RRF-fused pre-rerank list; reranked list stored beside it",
}


def current_meta(gen: dict, run_cfg: dict) -> dict:
    """Everything a resumed run must match. Names the PRD 11.6 pipeline (F-61)."""
    from api.db import connect
    from api.query.rerank import machine
    from api.query.retrieve import load_bm25

    freeze = yaml.safe_load(FREEZE_FILE.read_text(encoding="utf-8"))
    pipeline, rc = run_cfg["pipeline"], retrieval()
    meta = {
        "backend": gen["backend"], "model_requested": gen[TIER], "tier": TIER,
        "pipeline": pipeline, "retrieval_stage": STAGES[pipeline],
        "retrieve_depth": run_cfg["retrieve_depth"], "generator_top_k": baseline()["top_k"],
        "hnsw_ef_search": rc["hnsw_ef_search"], "k_dense": rc["k_dense"],
        "parser_version": freeze["parser_version"], "chunker_version": freeze["chunker_version"],
        "datasets": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in DATASETS},
    }  # fmt: skip
    if pipeline != "config_1_dense":
        meta["retrieval"] = rc
        if rc["sparse"]["backend"] == "bm25":
            with connect() as conn:
                meta["bm25_index_key"] = load_bm25(conn, rc["sparse"])[0].key
    if pipeline == "config_4_rerank":
        meta["rerank"] = rerank()
        meta["machine"] = machine()
    return meta


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
        if pipeline == "config_4_rerank":
            self.reranker = load_reranker(self.rrcfg)


def texts_for(conn, ids: list[str]) -> dict[str, str]:
    rows = conn.execute("SELECT chunk_id, text FROM chunks WHERE chunk_id = ANY(%s)", (ids,))
    return dict(rows.fetchall())


def answer_one(conn, ctx: Context, it: dict, gen: dict, run_cfg: dict) -> dict:
    from api.query.rerank import rerank as rerank_one
    from api.query.retrieve import Retrieved, dense_top_k, embed_question, rrf_fuse, sparse
    from eval.pipeline import context_for

    t0 = time.monotonic()
    pipeline, rc = run_cfg["pipeline"], ctx.rcfg
    vec = embed_question(ctx.model, ctx.emb, it["question"])
    depth = run_cfg["retrieve_depth"] if pipeline == "config_1_dense" else rc["k_dense"]
    dense = [r.chunk_id for r in dense_top_k(conn, vec, depth, rc["hnsw_ef_search"])[0]]
    fused, reranked, secs = [], None, None
    if pipeline != "config_1_dense":
        sp = sparse(conn, it["question"], rc["k_sparse"], rc["sparse"], ctx.index)
        w = rc["weights"]
        fused = rrf_fuse([dense, sp], [w["dense"], w["sparse"]], rc["rrf_k"])
        fused = fused[: max(rc["k_dense"], rc["k_sparse"])]
    if pipeline == "config_4_rerank":
        texts = texts_for(conn, fused)
        reranked, secs = rerank_one(ctx.reranker, it["question"], [(c, texts[c]) for c in fused])
    c = context_for(pipeline, dense=dense, fused=fused, reranked=reranked, rerank_seconds=secs,
                    rerank_cfg=ctx.rrcfg, question_type=it["question_type"],
                    baseline_top_k=baseline()["top_k"])  # fmt: skip
    record = {
        "item_id": it["item_id"], "pipeline": pipeline, "retrieved": c["retrieved"],
        "retrieved_post_rerank": c["retrieved_post_rerank"],
        "generator_input": c["generator_input"], "rerank_seconds": secs,
        "rerank_fell_back": c["fell_back"], "claims_pre": [], "claims_post": [],
    }  # fmt: skip
    if c["abstain"]:  # every chunk below the score floor: no generator call (PRD 7.3)
        return {**record, "answer": {"text": "", "claims": [], "abstained": True},
                "verdict": "ABSTAIN", "model_served": None, "backend": gen["backend"],
                "usage": None, "latency_s": round(time.monotonic() - t0, 2),
                "answered_at": datetime.now(UTC).isoformat(timespec="seconds")}  # fmt: skip
    texts = texts_for(conn, c["generator_input"])
    chunks = [Retrieved(cid, 0.0, texts[cid]) for cid in c["generator_input"]]
    last = None
    for _ in range(TRANSPORT_RETRIES):
        try:
            a = generate(it["question"], chunks, gen, TIER)
            break
        except claude_cli.TransportError as e:
            last = e
    else:
        raise last
    if gen[TIER] not in a.model.split(","):
        raise claude_cli.CliError(f"served {a.model}, requested {gen[TIER]}")
    return {
        **record, "answer": {"text": a.text, "claims": [], "abstained": False}, "verdict": "PASS",
        "model_served": a.model, "backend": a.backend,
        "usage": {"input_tokens": a.input_tokens, "output_tokens": a.output_tokens,
                  "cache_read_tokens": a.cache_read_tokens,
                  "cache_creation_tokens": a.cache_creation_tokens},
        "latency_s": round(time.monotonic() - t0, 2),
        "answered_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }  # fmt: skip


def run_items(todo: list[str], answer, results_path, errors_path) -> int:
    """Answer each pending item in order, appending each result as it completes.
    0 when done; 1 on a call with no usable response (error filed, item unrecorded)."""
    for n, iid in enumerate(todo, start=1):
        try:
            rec = answer(iid)
        except claude_cli.CliError as e:
            at = datetime.now(UTC).isoformat(timespec="seconds")
            append(errors_path, {"item_id": iid, "error": str(e), "at": at})
            print(f"HALT at {iid}: {e}")
            return 1
        append(results_path, rec)
        print(f"[{n}/{len(todo)}] {iid} {rec.get('latency_s')}s", flush=True)
    return 0


def main() -> None:
    gen, run_cfg = generation(), eval_run()
    baseline_out = arg("--baseline-out")
    if baseline_out:
        refuse_dev_baseline(gen["backend"], baseline_out)
    items = {}
    for p in DATASETS:
        for it in read_jsonl(p):
            items[it["item_id"]] = it
    runs = REPO_ROOT / run_cfg["runs_dir"]
    meta = current_meta(gen, run_cfg)

    if arg("--resume"):
        run_id = arg("--resume")
        saved = json.loads((runs / f"{run_id}.meta.json").read_text(encoding="utf-8"))
        diff = {k for k in meta if meta[k] != saved.get(k)}
        if diff:
            raise SystemExit(f"run {run_id} cannot resume: {sorted(diff)} changed since it began")
        order = saved["item_order"]
    elif "--run" in sys.argv:
        run_id = uuid.uuid4().hex[:12]
        order = list(items)[: int(arg("--limit"))] if arg("--limit") else list(items)
        runs.mkdir(parents=True, exist_ok=True)
        (runs / f"{run_id}.meta.json").write_text(
            json.dumps({**meta, "run_id": run_id, "k": run_cfg["k"], "item_order": order},
                       indent=1) + "\n", encoding="utf-8")  # fmt: skip
    else:
        sources = dict(Counter(i["source"] for i in items.values()))
        print(f"backend {gen['backend']} ({gen[TIER]}, {TIER}); items {len(items)} {sources}; "
              f"k {run_cfg['k']}")  # fmt: skip
        print("plan only: pass --run to retrieve and generate")
        return

    results_path = runs / f"{run_id}.results.jsonl"
    done = {r["item_id"] for r in read_jsonl(results_path)}
    todo = [i for i in order if i not in done]
    print(f"run {run_id}: backend {gen['backend']}; items {len(order)}; recorded {len(done)}; "
          f"pending {len(todo)}", flush=True)  # fmt: skip
    if todo:
        from api.db import connect

        with connect() as conn:
            ctx = Context(conn, run_cfg["pipeline"])
            code = run_items(
                todo,
                lambda iid: answer_one(conn, ctx, items[iid], gen, run_cfg),
                results_path,
                runs / f"{run_id}.errors.jsonl",
            )
        if code:
            print(f"resume with --resume {run_id}")
            sys.exit(code)
    results = read_jsonl(results_path)
    report = build_report(items, results, {**meta, "run_id": run_id}, run_cfg["k"],
                          run_cfg["nli_threshold"])  # fmt: skip
    (runs / f"{run_id}.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(format_report(report))
    if baseline_out:
        (REPO_ROOT / baseline_out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
