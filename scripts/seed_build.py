"""Rebuild the seeded items offline from eval/seeding/raw_v1.jsonl. No model call.

python -m scripts.seed_build

Writes eval/seeding/dropped_v1.jsonl (key-free drops with filter, reason and
sign_only) and prints the key-free survivors per stratum in draw order with
counts per filter. Refuses to write candidates or the reserve while any
survivor lacks a no-context record. Never reads the verification file.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from api.config import REPO_ROOT
from api.db import connect
from eval.generate.seed_build import Blocked, key_free, require_no_context
from scripts.seed_run import DRAW, RAW, TEMPLATES, load_chunk, read_jsonl

DROPPED = REPO_ROOT / "eval" / "seeding" / "dropped_v1.jsonl"
NO_CONTEXT = REPO_ROOT / "eval" / "seeding" / "no_context_v1.jsonl"


def main() -> None:
    draw = json.loads(DRAW.read_text(encoding="utf-8"))
    raw = read_jsonl(RAW)
    names = yaml.safe_load(TEMPLATES.read_text(encoding="utf-8"))["company_names"]
    company_names = sorted(set(names) | set(names.values()))
    with connect() as conn:
        chunks = {r["chunk_id"]: load_chunk(conn, r["chunk_id"]) for r in raw}
    survivors, dropped, counts = key_free(raw, draw, chunks, company_names)
    Path(DROPPED).write_text("".join(json.dumps(d) + "\n" for d in dropped), encoding="utf-8")
    print(f"raw records {len(raw)}; {dict(sorted(counts.items()))}")
    print(f"wrote {DROPPED.relative_to(REPO_ROOT)}: {len(dropped)} drops")
    print("key-free survivors per stratum, in draw order:")
    for key in sorted(survivors):
        ids = [f"{s['chunk_id']}{' [flags]' if s['flags'] else ''}" for s in survivors[key]]
        print(f"  {' '.join(key)}: {ids}")
    if not survivors:
        print("  none")
    no_context = {r["chunk_id"]: r for r in read_jsonl(NO_CONTEXT)}
    try:
        require_no_context(survivors, no_context)
    except Blocked as e:
        print(f"stopped after the key-free stage: {e}")
        return
    if survivors:
        raise SystemExit("no-context match rule not decided (TRADEOFFS); nothing written")
    print("no survivors: no candidates or reserve to write")


if __name__ == "__main__":
    main()
