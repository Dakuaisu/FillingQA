"""Item-for-item consistency of an eval run's stored lists with the deterministic
runs that share its components.

python -m scripts.run_consistency EVAL_RUN RETRIEVAL_RUN RERANK_RUN

Pre-rerank: the eval run's `retrieved` against the retrieval run's `hybrid`.
Post-rerank: the eval run's `retrieved_post_rerank` against the rerank run's
`post_floor` (same floor and top-n), unless the eval run fell back to RRF order.
Each differing item is classed: identical set in another order, a different
set, the eval run fell back (timeout), or missing from one run. Prints counts per
source and the differing item ids with the first rank that differs.
"""

from __future__ import annotations

import json
import sys
from collections import Counter

from api.config import REPO_ROOT
from eval.runner import SOURCES
from scripts.eval_run import DATASETS, read_jsonl

RUNS = REPO_ROOT / "eval" / "runs"


def classify(got: list[str] | None, want: list[str] | None) -> tuple[str, int | None]:
    if got is None or want is None:
        return "missing", None
    if got == want:
        return "identical", None
    first = next((i for i, (a, b) in enumerate(zip(got, want, strict=False)) if a != b),
                 min(len(got), len(want)))  # fmt: skip
    return ("same_set_reordered" if set(got) == set(want) else "different_set"), first + 1


def main() -> None:
    eval_id, ret_id, rr_id = sys.argv[1:4]
    items = {it["item_id"]: it for p in DATASETS for it in read_jsonl(p)}
    ev = {r["item_id"]: r for r in read_jsonl(RUNS / f"{eval_id}.results.jsonl")}
    ret_doc = json.loads((RUNS / f"{ret_id}.retrieval.json").read_text(encoding="utf-8"))
    ret = {r["item_id"]: r for r in ret_doc["results"]}
    rr_doc = json.loads((RUNS / f"{rr_id}.rerank.json").read_text(encoding="utf-8"))
    rr = {r["item_id"]: r for r in rr_doc["results"]}
    counts, diffs = Counter(), []
    for iid, r in ev.items():
        src = items[iid]["source"]
        cls, rank = classify(r["retrieved"], ret.get(iid, {}).get("hybrid"))
        counts[("pre", src, cls)] += 1
        if cls != "identical":
            diffs.append(("pre", iid, cls, rank))
        if r.get("rerank_fell_back"):
            cls, rank = "eval_fell_back_to_rrf", None
        else:
            cls, rank = classify(r["retrieved_post_rerank"], rr.get(iid, {}).get("post_floor"))
        counts[("post", src, cls)] += 1
        if cls != "identical":
            diffs.append(("post", iid, cls, rank))
    dev = rr_doc["report"]["device"]
    print(f"eval run {eval_id}: {len(ev)} items; pre-rerank vs retrieval run {ret_id} (hybrid); "
          f"post-rerank vs rerank run {rr_id} (post_floor, device {dev})")  # fmt: skip
    classes = {lst: sorted({c for x, _, c in counts if x == lst}) for lst in ("pre", "post")}
    print(f"{'list / class':34}" + "".join(f"{s:>12}" for s in (*SOURCES, "total")))
    for lst in ("pre", "post"):
        for c in classes[lst]:
            row = [counts.get((lst, s, c), 0) for s in SOURCES]
            print(f"{lst + ' ' + c:34}" + "".join(f"{x:>12}" for x in (*row, sum(row))))
    for lst, iid, cls, rank in diffs:
        print(f"  {lst:4} {iid:12} {cls:24} first differing rank {rank}")


if __name__ == "__main__":
    main()
