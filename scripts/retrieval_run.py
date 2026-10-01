"""Retrieval-only run over the candidates: dense, sparse and hybrid (PRD 7.2, F-13).

python -m scripts.retrieval_run [--compare RUN_ID]

No model call. Per item: dense top-k_dense, sparse top-k_sparse, and their RRF
fusion (the pre-rerank list). Prints retrieval metrics at eval_run.k per source
column for each list, and, with --compare, how many items' dense top-k equal the
stored list of an earlier run. Writes eval/runs/<run_id>.retrieval.json.
"""

from __future__ import annotations

import hashlib
import json
import sys
import uuid

import yaml

from api.config import REPO_ROOT, eval_run, retrieval
from api.db import connect
from api.index.embed import load_model
from api.query.retrieve import dense_top_k, embed_question, rrf_fuse, sparse_top_k
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
    results = []
    with connect() as conn:
        for iid, it in items.items():
            vec = embed_question(model, emb, it["question"])
            dense = [r.chunk_id for r in dense_top_k(conn, vec, cfg["k_dense"])[0]]
            sparse = [r.chunk_id for r in sparse_top_k(conn, it["question"], cfg["k_sparse"])]
            w = cfg["weights"]
            hybrid = rrf_fuse([dense, sparse], [w["dense"], w["sparse"]], cfg["rrf_k"])
            results.append({"item_id": iid, "dense": dense, "sparse": sparse,
                            "hybrid": hybrid[: max(cfg["k_dense"], cfg["k_sparse"])]})  # fmt: skip
    freeze = yaml.safe_load(FREEZE_FILE.read_text(encoding="utf-8"))
    run_id = uuid.uuid4().hex[:12]
    report = {"run_id": run_id, "kind": "retrieval-only, no model call", "retrieval": cfg, "k": k,
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
