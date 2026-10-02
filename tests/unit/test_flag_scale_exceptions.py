"""Owner review D5: scale-exception flags on review sheets. Inline data; real clause
patterns from the F-90 measurement (eval/generate/seeding.py)."""

from __future__ import annotations

from scripts.flag_scale_exceptions import flag_sheet, flag_worksheet, flagged_chunks

ROWS = [("a", "table", "millions", "| | in millions, except per share data |"),
        ("b", "table", "millions", "| Diluted earnings per share | 1.08 |"),
        ("c", "prose", None, "in millions, except per share amounts"),
        ("d", "table", None, "in millions, except per share")]  # fmt: skip


def test_only_scaled_tables_with_a_clause_are_flagged_and_nothing_else_changes():
    flagged = flagged_chunks(ROWS)
    assert flagged == {"a"}
    gold = {"x1": ["a", "b"], "x2": ["b"]}
    blank = {"decision": None, "evidence_sets": None, "note": ""}
    doc = {"decisions": [{"item_id": "x1", **blank}, {"item_id": "x2", **blank}]}
    assert flag_worksheet(doc, gold, flagged) == 1
    assert doc["decisions"][0]["scale_exception"] is True
    assert doc["decisions"][0]["scale_exception_chunks"] == ["a"]
    assert doc["decisions"][0]["decision"] is None and "scale_exception" not in doc["decisions"][1]
    sheet = "# s\n\n## x1 (table, AAPL)\n\nbody\n\n## x2\n"
    text, n = flag_sheet(sheet, gold, flagged)
    assert n == 1 and "## x1 (table, AAPL)\n**Scale exception (F-90):**" in text
    again, m = flag_sheet(text, gold, flagged)  # idempotent
    assert m == 1 and again == text
