"""Draw the fast-eval subset (PRD 11.5: 60 stratified items for PRs).

python -m scripts.draw_fast            # writes eval/fast_subset_v1.yaml; refuses to overwrite

Quotas by source in proportion to each source's size in the planned set (the
candidates on disk, plus the hand-written targets of `eval_handwritten`, F-103),
largest remainder. Within a source, items are drawn by seed in proportion to
question type. The handwritten quota is reserved and empty until F-103 lands;
it is filled by a v2 draw then, never by moving the other sources' items.
"""

from __future__ import annotations

import random
from collections import Counter

import yaml

from api.config import REPO_ROOT, eval_handwritten
from scripts.eval_run import DATASETS, read_jsonl

SIZE, SEED = 60, 20261007
OUT = REPO_ROOT / "eval" / "fast_subset_v1.yaml"


def largest_remainder(sizes: dict[str, int], n: int) -> dict[str, int]:
    total = sum(sizes.values())
    exact = {k: n * v / total for k, v in sizes.items()}
    take = {k: int(x) for k, x in exact.items()}
    for k in sorted(sizes, key=lambda k: (-(exact[k] - take[k]), k))[: n - sum(take.values())]:
        take[k] += 1
    return take


def draw(items: dict[str, dict], handwritten_planned: int, n: int, seed: int) -> dict:
    by_source = Counter(it["source"] for it in items.values())
    sizes = {**by_source, "handwritten": by_source.get("handwritten", 0) or handwritten_planned}
    quotas = largest_remainder(dict(sorted(sizes.items())), n)
    rng, chosen = random.Random(seed), {}
    for src in sorted(quotas):
        pool = {i: it for i, it in items.items() if it["source"] == src}
        if not pool:
            chosen[src] = []
            continue
        types = Counter(it["question_type"] for it in pool.values())
        per_type = largest_remainder(dict(sorted(types.items())), quotas[src])
        picked = []
        for qt, k in per_type.items():
            ids = sorted(i for i, it in pool.items() if it["question_type"] == qt)
            picked += sorted(rng.sample(ids, k))
        chosen[src] = picked
    return {"seed": seed, "size": n, "quotas": quotas, "planned_sizes": sizes,
            "items": chosen}  # fmt: skip


def main() -> None:
    if OUT.exists():
        raise SystemExit(f"{OUT} exists; a drawn subset is never redrawn (make a v2)")
    items = {it["item_id"]: it for p in DATASETS for it in read_jsonl(p)}
    planned = sum(eval_handwritten()["targets"].values())
    doc = draw(items, planned, SIZE, SEED)
    header = ("# Fast-eval subset v1 (PRD 11.5), drawn by `python -m scripts.draw_fast`.\n"
              "# The handwritten quota is reserved and empty until F-103 lands.\n")  # fmt: skip
    OUT.write_text(header + yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    print(f"wrote {OUT}: quotas {doc['quotas']}; drawn "
          f"{ {k: len(v) for k, v in doc['items'].items()} }")  # fmt: skip


if __name__ == "__main__":
    main()
