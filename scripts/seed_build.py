"""Rebuild the seeded items offline from eval/seeding/raw_v1.jsonl. No model call.

python -m scripts.seed_build

Writes eval/seeding/dropped_v1.jsonl (key-free drops with filter, reason and
sign_only) and prints the key-free survivors per stratum in draw order with
counts per filter; with no-context records for every survivor, applies the
no-context stage (drops appended to the same file) and prints its counts per
stratum. Writes no candidates or reserve. Never reads the verification file.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import yaml

from api.config import REPO_ROOT, eval_seeding
from api.db import connect
from eval.generate.seed_build import (
    Blocked,
    check_no_context,
    drop_near_duplicates,
    fill_slots,
    key_free,
    no_context_stage,
    redacted_responses,
    stratum_table,
)
from eval.generate.seeding import near_duplicates, prompt_sha
from scripts.seed_run import DRAW, RAW, TEMPLATES, load_chunk, read_jsonl

DROPPED = REPO_ROOT / "eval" / "seeding" / "dropped_v1.jsonl"
CANDIDATES = sorted((REPO_ROOT / "eval" / "candidates").glob("*_candidates.jsonl"))
NO_CONTEXT = REPO_ROOT / "eval" / "seeding" / "no_context_v1.jsonl"
NC_PROMPT = REPO_ROOT / "eval" / "generate" / "prompts" / "no_context_v1.txt"


def main() -> None:
    draw = json.loads(DRAW.read_text(encoding="utf-8"))
    raw = read_jsonl(RAW)
    names = yaml.safe_load(TEMPLATES.read_text(encoding="utf-8"))["company_names"]
    company_names = sorted(set(names) | set(names.values()))
    with connect() as conn:
        chunks = {r["chunk_id"]: load_chunk(conn, r["chunk_id"]) for r in raw}
    draw_sha = hashlib.sha256(DRAW.read_bytes()).hexdigest()
    survivors, dropped, counts = key_free(raw, draw, draw_sha, chunks, company_names)
    Path(DROPPED).write_text("".join(json.dumps(d) + "\n" for d in dropped), encoding="utf-8")
    print(f"raw records {len(raw)}; {dict(sorted(counts.items()))}")
    print(f"wrote {DROPPED.relative_to(REPO_ROOT)}: {len(dropped)} drops")
    print(f"model_served: {dict(Counter(r.get('model_served') for r in raw))}")
    print(f"responses redacted (a quote_verbatim drop there is not a filter result): "
          f"{redacted_responses(raw) or 'none'}")  # fmt: skip
    print("slotted strata: survivors / slots_1x / drawn / pending")
    for key, n, slots, drawn, pend in stratum_table(draw, survivors, raw):
        print(f"  {' '.join(key):34} {n:2} / {slots} / {drawn} / {pend}")
    print("key-free survivors in draw order:")
    for key in sorted(survivors):
        ids = [f"{s['chunk_id']}{' [flags]' if s['flags'] else ''}" for s in survivors[key]]
        print(f"  {' '.join(key)}: {ids}")
    if not survivors:
        print("  none")
    nc_sha = prompt_sha(NC_PROMPT.read_text(encoding="utf-8"))
    records = check_no_context(survivors, read_jsonl(NO_CONTEXT), nc_sha)
    try:
        kept, nc_drops, nc_counts = no_context_stage(survivors, records)
    except Blocked as e:
        print(f"stopped after the key-free stage: {e}")
        return
    with Path(DROPPED).open("a", encoding="utf-8") as fh:
        fh.write("".join(json.dumps(d) + "\n" for d in nc_drops))
    print(f"\nno-context stage: {len(nc_drops)} dropped, appended to "
          f"{DROPPED.relative_to(REPO_ROOT)}")  # fmt: skip
    print(
        "slotted strata: survivors / slots_1x / no-context dropped / near-matches / "
        "digits-only / sign-only"
    )
    tot = Counter()
    for key, _, slots, _, _ in stratum_table(draw, survivors, raw):
        c = nc_counts.get(key, Counter())
        tot.update(c)
        n = len(kept.get(key, []))
        print(f"  {' '.join(key):34} {n:2} / {slots} / {c['dropped']} / {c['near']} / "
              f"{c['digits_only']} / {c['sign_only']}")  # fmt: skip
    print(f"  totals: kept {sum(len(v) for v in kept.values())}; {dict(tot)}")
    near_duplicate_and_slots(kept, draw)


def near_duplicate_and_slots(kept: dict, draw: dict) -> None:
    """Near-duplicate stage (cosine on question embeddings, against the existing
    candidates and earlier seeded questions in draw order), then slot fill. Prints
    counts; writes no candidates or reserve (the llm_seeded item fields are not
    decided)."""
    from api.index.embed import load_model

    threshold = eval_seeding()["near_duplicate_cosine"]
    existing = [(i["item_id"], i["question"]) for p in CANDIDATES for i in read_jsonl(p)]
    seeded = sorted((s for ss in kept.values() for s in ss), key=lambda s: s["draw_index"])
    model, _ = load_model()
    encode = lambda texts: model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)  # noqa: E731
    ex_vecs = list(encode([q for _, q in existing]))
    new_vecs = encode([s["question"]["question"] for s in seeded])
    vectors = {s["chunk_id"]: v for s, v in zip(seeded, new_vecs, strict=True)}
    hits = near_duplicates([vectors[s["chunk_id"]] for s in seeded], ex_vecs, threshold)
    names = [i for i, _ in existing] + [s["chunk_id"] for s in seeded]
    after, nd_drops = drop_near_duplicates(kept, vectors, ex_vecs, threshold)
    with Path(DROPPED).open("a", encoding="utf-8") as fh:
        fh.write("".join(json.dumps(d) + "\n" for d in nd_drops))
    print(f"\nnear-duplicate stage (cosine > {threshold}, question embeddings, against "
          f"{len(existing)} existing candidates and earlier seeded questions): "
          f"{len(nd_drops)} dropped, appended to {DROPPED.relative_to(REPO_ROOT)}")  # fmt: skip
    for s, hit in zip(seeded, hits, strict=True):
        if hit is not None:
            print(f"  {s['chunk_id']} ~ {names[hit[0]]} (cosine {hit[1]:.3f}): "
                  f"{s['question']['question'][:90]}")  # fmt: skip
    best = [max((float(v @ w) for w in ex_vecs), default=0.0) for v in new_vecs]
    print(f"  highest cosine of a seeded question to an existing candidate: max "
          f"{max(best):.3f}, median {sorted(best)[len(best) // 2]:.3f}")  # fmt: skip

    candidates, reserve, short = fill_slots(after, draw)
    n_c = sum(len(v) for v in candidates.values())
    n_r = sum(len(v) for v in reserve.values())
    slots = {k: sum(s["slots_1x"] for st in d["per_ticker"].values() for s in st)
             for k, d in draw["kinds"].items()}  # fmt: skip
    by_kind = Counter(k[0] for k, v in candidates.items() for _ in v)
    print(f"\nslot fill (first survivors in draw order): candidates {n_c} "
          f"({dict(by_kind)} of slots {slots}); reserve {n_r}")  # fmt: skip
    print(f"  short strata ({len(short)}): " + ", ".join(
        f"{' '.join(k)} {got}/{want}" for k, (got, want) in sorted(short.items())))  # fmt: skip
    print("no candidates or reserve file written: the llm_seeded item fields are not decided")


if __name__ == "__main__":
    main()
