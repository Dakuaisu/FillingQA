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

from api.config import REPO_ROOT
from api.db import connect
from eval.generate.seed_build import (
    Blocked,
    check_no_context,
    key_free,
    no_context_stage,
    redacted_responses,
    stratum_table,
)
from eval.generate.seeding import prompt_sha
from scripts.seed_run import DRAW, RAW, TEMPLATES, load_chunk, read_jsonl

DROPPED = REPO_ROOT / "eval" / "seeding" / "dropped_v1.jsonl"
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
    print("next: near-duplicate stage (not run here); no candidates or reserve written")


if __name__ == "__main__":
    main()
