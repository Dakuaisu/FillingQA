"""Validate hand-written item files (PRD 11.1 Stage 4).

python -m scripts.handwritten_validate [FILE ...]   # default: eval/handwritten/*.jsonl

Prints counts per type against PRD 11.1's targets and every problem; exit 1 if
any. Cited chunk ids must exist in the frozen corpus; questions must not be
near-duplicates (cosine > eval_seeding.near_duplicate_cosine) of a candidate or
of an earlier hand-written item. Templates: eval/handwritten/templates/.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

from api.config import REPO_ROOT, eval_handwritten, eval_seeding
from api.db import connect
from eval.generate.handwritten import check
from scripts.write_freeze import FREEZE_FILE

FILES = sorted((REPO_ROOT / "eval" / "handwritten").glob("*.jsonl"))
CANDIDATES = sorted((REPO_ROOT / "eval" / "candidates").glob("*_candidates.jsonl"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").split("\n") if x.strip()]


def main() -> None:
    files = [Path(a) for a in sys.argv[1:]] or FILES
    items = [it for f in files for it in read_jsonl(f)]
    cfg = eval_handwritten()
    existing = [it for p in CANDIDATES for it in read_jsonl(p)]
    freeze = yaml.safe_load(FREEZE_FILE.read_text(encoding="utf-8"))
    parsed = [e["accession"] for e in freeze["filings"] if e["status"] == "parsed"]
    with connect() as conn:
        known = {r[0] for r in conn.execute(
            "SELECT chunk_id FROM chunks WHERE accession = ANY(%s)", (parsed,))}  # fmt: skip
    vectors, existing_vectors = [], []
    if items:
        from api.index.embed import load_model

        model, _ = load_model()
        enc = lambda xs: list(model.encode(xs, normalize_embeddings=True, convert_to_numpy=True))  # noqa: E731
        vectors = enc([it.get("question", "") for it in items])
        existing_vectors = enc([it["question"] for it in existing])
    problems, counts = check(
        items, targets=cfg["targets"], dataset_version=cfg["dataset_version"], known_chunks=known,
        existing_ids={it["item_id"] for it in existing}, vectors=vectors,
        existing_vectors=existing_vectors, threshold=eval_seeding()["near_duplicate_cosine"],
    )  # fmt: skip
    print(f"files: {[str(f.relative_to(REPO_ROOT)) for f in files]}; items {len(items)}")
    for qt, want in cfg["targets"].items():
        print(f"  {qt}: {counts[qt]} of {want}")
    print(f"problems: {len(problems)}")
    for p in problems:
        print(f"  {p}")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
