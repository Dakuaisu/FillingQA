"""Flag review items whose gold chunk has a scale-exception clause (owner review D5, F-90).

python -m scripts.flag_scale_exceptions

A gold chunk is flagged by the F-90 measurement's definition (`scripts.seed_supply`):
a table chunk with a `unit_scale` whose raw text matches `SCALE_EXCEPTION`
("in millions, except ...") or `PER_SHARE_EXCEPTION` ("except ... per share"), so
the caption's scale may not apply to every figure in it. For each review worksheet
(`eval/review/worksheets/*.yaml`) a flagged entry gains `scale_exception: true` and
`scale_exception_chunks`; each spot-check sheet (`eval/candidates/*.md`) gains a
line under the item's heading. Decisions, evidence sets and items are not touched.
Re-running is idempotent.
"""

from __future__ import annotations

import re

import yaml

from api.config import REPO_ROOT
from api.db import connect
from eval.generate.seeding import PER_SHARE_EXCEPTION, SCALE_EXCEPTION
from scripts.eval_run import DATASETS, read_jsonl

WORKSHEETS = REPO_ROOT / "eval" / "review" / "worksheets"
SHEETS = REPO_ROOT / "eval" / "candidates"
NOTE = ("**Scale exception (F-90):** gold chunk(s) {chunks} carry a scale-exception "
        "clause; the caption's scale may not apply to every figure. Check the scale.")  # fmt: skip


def flagged_chunks(rows: list[tuple[str, str, str | None, str]]) -> set[str]:
    """`rows`: (chunk_id, chunk_type, unit_scale, raw_text)."""
    return {cid for cid, kind, scale, raw in rows
            if kind == "table" and scale is not None
            and (SCALE_EXCEPTION.search(raw) or PER_SHARE_EXCEPTION.search(raw))}  # fmt: skip


def flag_worksheet(doc: dict, gold: dict[str, list[str]], flagged: set[str]) -> int:
    n = 0
    for e in doc["decisions"]:
        hits = sorted(c for c in gold[e["item_id"]] if c in flagged)
        e.pop("scale_exception", None)
        e.pop("scale_exception_chunks", None)
        if hits:
            e["scale_exception"] = True
            e["scale_exception_chunks"] = hits
            n += 1
    return n


def flag_sheet(text: str, gold: dict[str, list[str]], flagged: set[str]) -> tuple[str, int]:
    """Insert the note after each flagged item's `## <item_id>` heading."""
    text = re.sub(r"\n\*\*Scale exception \(F-90\):\*\*[^\n]*\n", "\n", text)
    out, n = [], 0
    for line in text.split("\n"):
        out.append(line)
        m = re.match(r"^## (\S+)(?:\s.*)?$", line)
        if m and m.group(1) in gold:
            hits = sorted(c for c in gold[m.group(1)] if c in flagged)
            if hits:
                out.append(NOTE.format(chunks=", ".join(f"`{c}`" for c in hits)))
                n += 1
    return "\n".join(out), n


def main() -> None:
    items = {it["item_id"]: it for p in DATASETS for it in read_jsonl(p)}
    gold = {i: sorted({c for s in it["gold_evidence_sets"] for c in s}) for i, it in items.items()}
    ids = sorted({c for cs in gold.values() for c in cs})
    with connect() as conn:
        rows = conn.execute("SELECT chunk_id, chunk_type, unit_scale, raw_text FROM chunks "
                            "WHERE chunk_id = ANY(%s)", (ids,)).fetchall()  # fmt: skip
    flagged = flagged_chunks(rows)
    for ws in sorted(WORKSHEETS.glob("*.yaml")):
        doc = yaml.safe_load(ws.read_text(encoding="utf-8"))
        n = flag_worksheet(doc, gold, flagged)
        ws.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
        sheet = SHEETS / doc["sheet"]
        text, m = flag_sheet(sheet.read_text(encoding="utf-8"), gold, flagged)
        sheet.write_text(text, encoding="utf-8")
        print(f"{ws.name}: {n} of {len(doc['decisions'])} entries flagged; {sheet.name}: {m} notes")


if __name__ == "__main__":
    main()
