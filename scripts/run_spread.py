"""Run-to-run spread between two eval runs on the same config and candidates (F-60).

python -m scripts.run_spread RUN_A RUN_B

Prints, per metric and source column, run A, run B and B minus A, and per item:
whether the retrieved list is identical and whether numeric correctness flips.
The spread is reported noise, never a reason to move a threshold. When the runs'
pipelines or ef_search differ the table is labelled direction only: a difference
between them is not attributed to any one component.
"""

from __future__ import annotations

import json
import sys

from api.config import REPO_ROOT
from eval.metrics.numeric import score_item
from eval.runner import COLUMNS

RUNS = REPO_ROOT / "eval" / "runs"
CANDIDATES = sorted((REPO_ROOT / "eval" / "candidates").glob("*_candidates.jsonl"))
METRICS = [
    ("Sufficiency@10", lambda c: c["sufficiency@10"]),
    ("Recall@10", lambda c: c["recall@10"]),
    ("MRR", lambda c: c["mrr"]),
    ("nDCG@10", lambda c: c["ndcg@10"]),
    ("Sufficiency post-rerank", lambda c: c.get("sufficiency@10_post_rerank")),
    ("Numeric accuracy (gated)", lambda c: c["numeric"]["numeric_accuracy"]),
    ("  strict first figure", lambda c: c["numeric"]["strict_first_figure"]),
    ("  within 0.5%", lambda c: c["numeric"]["tolerant_0_5pct"]),
    ("  comparison values only", lambda c: c["numeric"]["comparison_values_only"]),
]


def read_jsonl(path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").split("\n") if x.strip()]


def main() -> None:
    a_id, b_id = sys.argv[1], sys.argv[2]
    a = json.loads((RUNS / f"{a_id}.json").read_text(encoding="utf-8"))
    b = json.loads((RUNS / f"{b_id}.json").read_text(encoding="utf-8"))
    keys = ("backend", "model_requested", "datasets", "parser_version", "chunker_version", "k")
    same = {k: a.get(k) == b.get(k) for k in keys}
    print(f"run A {a_id} vs run B {b_id}; same config: {same}")
    cfg = {r: (d.get("pipeline", "config_1_dense"), d.get("hnsw_ef_search"))
           for r, d in ((a_id, a), (b_id, b))}  # fmt: skip
    for r, (pl, ef) in cfg.items():
        efs = ef if ef is not None else "not recorded (pgvector default 40, F-109)"
        print(f"  {r}: pipeline {pl}, hnsw ef_search {efs}")
    if cfg[a_id] != cfg[b_id]:
        print("DIRECTION ONLY: the pipelines differ; no difference is attributed to a component")
    print(f"served models A {a['served_models']} B {b['served_models']}")
    print(f"{'metric: A / B (B - A)':30}" + "".join(f"{c:>24}" for c in COLUMNS))
    for name, get in METRICS:
        cells = []
        for c in COLUMNS:
            ca, cb = a["columns"].get(c), b["columns"].get(c)
            va, vb = (get(ca) if ca else None), (get(cb) if cb else None)
            fa, fb = ("-" if v is None else f"{v:.3f}" for v in (va, vb))
            diff = "" if va is None or vb is None else f" ({vb - va:+.3f})"
            cells.append("-" if va is None and vb is None else f"{fa} / {fb}{diff}")
        print(f"{name:30}" + "".join(f"{x:>24}" for x in cells))
    items = {it["item_id"]: it for p in CANDIDATES for it in read_jsonl(p)}
    ra = {r["item_id"]: r for r in read_jsonl(RUNS / f"{a_id}.results.jsonl")}
    rb = {r["item_id"]: r for r in read_jsonl(RUNS / f"{b_id}.results.jsonl")}
    common = sorted(set(ra) & set(rb))
    same_ret = sum(ra[i]["retrieved"] == rb[i]["retrieved"] for i in common)
    flips = {"A only": [], "B only": []}
    for i in common:
        sa, sb = score_item(items[i], ra[i]["answer"]), score_item(items[i], rb[i]["answer"])
        if sa.excluded is None and sa.correct != sb.correct:
            flips["A only" if sa.correct else "B only"].append(i)
    print(f"items in both runs: {len(common)}; identical retrieved list: {same_ret}")
    print(f"numeric correctness flips: correct in A only {len(flips['A only'])}, "
          f"in B only {len(flips['B only'])}")  # fmt: skip
    for k, v in flips.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
