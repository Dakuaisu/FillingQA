"""Retrieval-only run over the candidates: dense, sparse and hybrid (PRD 7.2, F-13).

python -m scripts.retrieval_run [--compare RUN_ID]

Output convention: retrieval-only runs are written to
eval/runs/<run_id>.retrieval.json (report and per-item lists in one file), beside
the eval runs' <run_id>.json / .meta.json / .results.jsonl.

No model call. Per item: dense top-k_dense, sparse top-k_sparse, and their RRF
fusion (the pre-rerank list). Prints retrieval metrics at eval_run.k per source
column for each list, and, with --compare, how many items' dense top-k equal the
stored list of an earlier run. Writes eval/runs/<run_id>.retrieval.json.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import uuid

import yaml

from api.config import REPO_ROOT, eval_run, retrieval
from api.db import connect
from api.index.embed import load_model
from api.query.retrieve import dense_search, embed_question, load_bm25, rrf_fuse, sparse
from eval.runner import COLUMNS, SOURCES, retrieval_slice
from scripts.write_freeze import FREEZE_FILE

DATASETS = sorted((REPO_ROOT / "eval" / "candidates").glob("*_candidates.jsonl"))
RUNS = REPO_ROOT / "eval" / "runs"
LISTS = ("dense", "sparse", "hybrid")


def read_jsonl(path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").split("\n") if x.strip()]


def main() -> None:
    cfg, k = retrieval(), eval_run()["k"]
    items = {it["item_id"]: it for p in DATASETS for it in read_jsonl(p)}
    model, emb = load_model()
    results, dense_seconds = [], []
    with connect() as conn:
        index, rebuilt, key = None, None, None
        if cfg["sparse"]["backend"] == "bm25":
            index, rebuilt = load_bm25(conn, cfg["sparse"])
            key = index.key
        for iid, it in items.items():
            vec = embed_question(model, emb, it["question"])
            t0 = time.perf_counter()
            dense = dense_search(conn, vec, cfg["k_dense"], cfg)
            dense_seconds.append(time.perf_counter() - t0)
            sp = sparse(conn, it["question"], cfg["k_sparse"], cfg["sparse"], index)
            w = cfg["weights"]
            hybrid = rrf_fuse([dense, sp], [w["dense"], w["sparse"]], cfg["rrf_k"])
            results.append({"item_id": iid, "dense": dense, "sparse": sp,
                            "hybrid": hybrid[: max(cfg["k_dense"], cfg["k_sparse"])]})  # fmt: skip
    freeze = yaml.safe_load(FREEZE_FILE.read_text(encoding="utf-8"))
    run_id = uuid.uuid4().hex[:12]
    lat = sorted(dense_seconds)
    report = {"run_id": run_id, "kind": "retrieval-only, no model call", "retrieval": cfg, "k": k,
              "dense_search": cfg.get("dense_search", "exact"),
              "dense_latency_s": {"p50": round(lat[len(lat) // 2], 4),
                                  "p95": round(lat[int(0.95 * (len(lat) - 1))], 4),
                                  "max": round(lat[-1], 4), "n": len(lat)},
              "sparse_backend": cfg["sparse"]["backend"], "bm25_index_key": key,
              "bm25_index_rebuilt": rebuilt,
              "parser_version": freeze["parser_version"],
              "chunker_version": freeze["chunker_version"],
              "datasets": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in DATASETS},
              "columns": {}}  # fmt: skip
    for lst in LISTS:
        by = {s: [r for r in results if items[r["item_id"]]["source"] == s] for s in SOURCES}
        report["columns"][lst] = {
            **{s: retrieval_slice(items, rs, k, lst) if rs else None for s, rs in by.items()},
            "aggregate": retrieval_slice(items, results, k, lst),
        }
    if "--compare" in sys.argv:
        other = sys.argv[sys.argv.index("--compare") + 1]
        stored = {r["item_id"]: r["retrieved"] for r in read_jsonl(RUNS / f"{other}.results.jsonl")}
        same = sum(stored.get(r["item_id"]) == r["dense"][:k] for r in results)
        report["dense_top_k_equal_to"] = {other: same}
    (RUNS / f"{run_id}.retrieval.json").write_text(
        json.dumps({"report": report, "results": results}, indent=1) + "\n", encoding="utf-8"
    )
    print(f"retrieval run {run_id}: {len(results)} items; k {k}; {cfg}")
    if key:
        print(f"bm25 index key {key[:16]} ({'rebuilt' if rebuilt else 'from cache'})")
    print(
        f"dense search {report['dense_search']}: latency per question {report['dense_latency_s']}"
    )
    if "dense_top_k_equal_to" in report:
        print(f"dense top-{k} identical to the stored list of: {report['dense_top_k_equal_to']}")
    metrics = (f"sufficiency@{k}", f"recall@{k}", "mrr", f"ndcg@{k}", f"precision@{k}")
    print(f"{'list / metric':28}" + "".join(f"{c:>14}" for c in COLUMNS))
    for lst in LISTS:
        for m in metrics:
            cells = [report["columns"][lst][c][m] if report["columns"][lst][c] else None
                     for c in COLUMNS]  # fmt: skip
            print(f"{lst + ' ' + m:28}" + "".join(
                f"{'-' if v is None else f'{v:.3f}':>14}" for v in cells))  # fmt: skip


if __name__ == "__main__":
    main()
