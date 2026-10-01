"""The review CLI (PRD 11.1 Stage 5). Never edits a candidates file.

python -m scripts.review worksheet SHEET.md          # fill-in file for the sheet's items
python -m scripts.review import WORKSHEET.yaml --reviewer NAME
python -m scripts.review status                      # what the decisions change

`import` appends the worksheet's decisions to eval/review/decisions_v1.jsonl, the
only thing that sets reviewed_by_human = true; any invalid entry and nothing is
appended. `status` prints, per candidates file, accepted / rejected / evidence
edits / undecided and every change, from the candidates plus the decisions.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

import yaml

from api.config import REPO_ROOT
from eval.review_decisions import effective, records, sheet_item_ids, worksheet
from scripts.write_freeze import FREEZE_FILE

CANDIDATES = sorted((REPO_ROOT / "eval" / "candidates").glob("*_candidates.jsonl"))
REVIEW = REPO_ROOT / "eval" / "review"
DECISIONS = REVIEW / "decisions_v1.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").split("\n") if x.strip()]


def all_items() -> dict[str, dict]:
    return {it["item_id"]: it for p in CANDIDATES for it in read_jsonl(p)}


def known_chunks() -> set[str]:
    from api.db import connect

    freeze = yaml.safe_load(FREEZE_FILE.read_text(encoding="utf-8"))
    parsed = [e["accession"] for e in freeze["filings"] if e["status"] == "parsed"]
    with connect() as conn:
        return {r[0] for r in conn.execute(
            "SELECT chunk_id FROM chunks WHERE accession = ANY(%s)", (parsed,))}  # fmt: skip


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    items = all_items()
    if cmd == "worksheet":
        sheet = Path(sys.argv[2])
        ids = sheet_item_ids(sheet.read_text(encoding="utf-8"), set(items))
        out = REVIEW / "worksheets" / f"{sheet.stem}.yaml"
        if out.exists() and any(
            e.get("decision") for e in yaml.safe_load(out.read_text())["decisions"]
        ):
            raise SystemExit(f"{out} already holds decisions; import or move it first")
        out.write_text(
            yaml.safe_dump(worksheet(sheet.name, ids), sort_keys=False), encoding="utf-8"
        )
        print(f"wrote {out.relative_to(REPO_ROOT)}: {len(ids)} items from {sheet.name}")
    elif cmd == "import":
        ws = yaml.safe_load(Path(sys.argv[2]).read_text(encoding="utf-8"))
        reviewer = sys.argv[sys.argv.index("--reviewer") + 1] if "--reviewer" in sys.argv else ""
        now = datetime.now(UTC).isoformat(timespec="seconds")
        recs, errors = records(ws, reviewer, now, items, known_chunks())
        if errors:
            print("nothing imported:")
            for e in errors:
                print(f"  {e}")
            sys.exit(1)
        with DECISIONS.open("a", encoding="utf-8") as fh:
            fh.write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs))
        print(f"appended {len(recs)} decisions to {DECISIONS.relative_to(REPO_ROOT)}: "
              f"{dict(Counter(r['decision'] for r in recs))}")  # fmt: skip
    elif cmd == "status":
        decisions = read_jsonl(DECISIONS)
        print(f"decisions on file: {len(decisions)} ({DECISIONS.relative_to(REPO_ROOT)})")
        latest = {d["item_id"]: d["decision"] for d in decisions}
        for p in CANDIDATES:
            its = read_jsonl(p)
            _, changes = effective(its, decisions)
            c = Counter(latest.get(i["item_id"], "undecided") for i in its)
            print(f"  {p.name}: {len(its)} items; {dict(sorted(c.items()))}")
            for ch in changes:
                print(f"    {ch}")
    else:
        raise SystemExit(f"unknown command {cmd!r}: worksheet | import | status")


if __name__ == "__main__":
    main()
