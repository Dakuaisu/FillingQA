"""Heading tables (F-63): which short layout tables are Item/Part headings.

Cell text is verbatim from the filings named; the tiny documents only give the
cells offsets to live at.
"""

from __future__ import annotations

from api.parse.ixbrl import Anchor, Block, ExtractedDocument
from api.parse.sections import detect_sections, is_heading_table, text_without_anchors


def table(rows: list[list[str]], anchors: tuple[str, ...] = ()) -> tuple[ExtractedDocument, Block]:
    text, cells_rows, links = "", [], []
    for row in rows:
        cells = []
        for cell in row:
            start = len(text)
            text += cell
            cells.append((start, len(text), 1, 1))
            if cell in anchors:
                links.append(Anchor(start, len(text), "toc"))
            text += " "
        cells_rows.append(cells)
        text += "\n"
    block = Block("table", 0, len(text.rstrip()), kind="table", rows=cells_rows, anchors=links)
    return ExtractedDocument(text=text, blocks=[block]), block


def test_one_row_heading_split_across_cells():
    # PFE 10-K 0000078003-25-000054: "ITEM 1." and "BUSINESS" in separate cells.
    doc, block = table([["ITEM 1.", "BUSINESS"]])
    assert is_heading_table(doc, block)


def test_heading_with_title_row_and_a_navigation_link():
    # BAC 10-K 0000070858-25-000139, Item 7's heading table.
    doc, block = table(
        [
            ["Item 7. Bank of America Corporation and Subsidiaries"],
            [
                "Management's Discussion and Analysis of Financial Condition"
                " and Results of Operations"
            ],
            ["Table of Contents"],
        ],
        anchors=("Table of Contents",),
    )
    assert is_heading_table(doc, block)
    assert "Table of Contents" not in text_without_anchors(doc, block)


def test_an_index_listing_several_items_is_not_a_heading():
    # BAC 10-Q 0000070858-25-000200, Part II index rows with page numbers.
    doc, block = table(
        [
            ["Item 1. Legal Proceedings", "96"],
            ["Item 1A. Risk Factors", "96"],
            ["Item 2. Unregistered Sales of Equity Securities and Use of Proceeds", "96"],
        ]
    )
    assert not is_heading_table(doc, block)


def test_a_heading_must_be_the_first_row():
    doc, block = table([["Index to Financial Statements"], ["ITEM 8. FINANCIAL STATEMENTS"]])
    assert not is_heading_table(doc, block)


# ------------------------------------------- F-64: Part tracking and indexes


def document(blocks: list[tuple[str, list[list[str]] | None]]) -> ExtractedDocument:
    """Blocks in order: (paragraph text, None) or (None, table rows)."""
    text, out = "", []
    for para, rows in blocks:
        start = len(text)
        if rows is None:
            text += para
            out.append(Block("p", start, len(text), kind="paragraph"))
        else:
            cells_rows = []
            for row in rows:
                cells = []
                for cell in row:
                    s = len(text)
                    text += cell
                    cells.append((s, len(text), 1, 1))
                    text += " "
                cells_rows.append(cells)
            out.append(Block("table", start, len(text.rstrip()), kind="table", rows=cells_rows))
        text += "\n"
    return ExtractedDocument(text=text, blocks=out)


def test_part_headings_inside_an_index_do_not_set_the_part():
    # BAC 10-Q 0000070858-25-000200: the index's Part headings, then MD&A first.
    doc = document(
        [
            ("Part I. Financial Information", None),
            (
                None,
                [["Item 1. Financial Statements", "44"], ["Item 2. Management's Discussion", "3"]],
            ),
            ("Part II. Other Information", None),
            (None, [["Item 1. Legal Proceedings", "96"], ["Item 1A. Risk Factors", "96"]]),
            ("Item 2. Management's Discussion and Analysis of Financial Condition", None),
            ("Part I. Financial Information", None),
            ("Item 1. Financial Statements", None),
            ("Part II. Other Information", None),
            ("Item 1. Legal Proceedings", None),
        ]
    )
    codes = [s.qualified_code for s in detect_sections(doc, "10-Q")]
    assert codes == ["I.2", "I.1", "II.1"]  # MD&A before the statements is legal


def test_an_item_before_any_part_heading_is_part_one():
    # JPM 10-Q: Items 3 and 4 appear with no Part heading before them.
    doc = document([("Item 3. Quantitative and Qualitative Disclosures About Market Risk.", None)])
    assert [s.qualified_code for s in detect_sections(doc, "10-Q")] == ["I.3"]


# ------------------------------------- F-65: table-of-contents-anchor fallback


def linked_document(blocks):
    """Blocks in order: ("p", text, target_id_or_None) or ("t", rows, links).

    In a table, `links` maps a cell's text to the target id its link points at.
    A paragraph with a target id is where that link lands.
    """
    text, out, targets = "", [], {}
    for kind, content, extra in blocks:
        start = len(text)
        if kind == "p":
            if extra:
                targets[extra] = start
            text += content
            out.append(Block("p", start, len(text), kind="paragraph"))
        else:
            rows, anchors = [], []
            for row in content:
                cells = []
                for cell in row:
                    s = len(text)
                    text += cell
                    cells.append((s, len(text), 1, 1))
                    if cell in extra:
                        anchors.append(Anchor(s, len(text), extra[cell]))
                    text += " "
                rows.append(cells)
            out.append(Block("table", start, len(text.rstrip()), kind="table", rows=rows,
                             anchors=anchors))  # fmt: skip
        text += "\n"
    return ExtractedDocument(text=text, blocks=out, anchor_targets=targets)


def test_index_links_fill_items_primary_detection_missed():
    # JPM 10-Q shape: the index is split over two tables, the first holding only
    # Item 1; the body has no Item 1 or Item 2 headings, only Items 3 and 4.
    doc = linked_document(
        [
            ("t", [["Part I – Financial information", "Page"], ["Item 1.", "Financial Statements"]],  # noqa: RUF001
             {"Financial Statements": "fs"}),
            ("t", [["Item 2.", "Management's Discussion and Analysis", "7"],
                   ["Item 3.", "Quantitative and Qualitative Disclosures", "181"]],
             {"Management's Discussion and Analysis": "mdna"}),
            ("p", "Executive overview of results for the quarter.", "mdna"),
            ("p", "Consolidated statements of income (unaudited)", "fs"),
            ("p", "Item 3. Quantitative and Qualitative Disclosures About Market Risk.", None),
        ]
    )  # fmt: skip
    sections = detect_sections(doc, "10-Q")
    assert [s.qualified_code for s in sections] == ["I.2", "I.1", "I.3"]
    assert doc.text[sections[1].char_start :].startswith("Consolidated statements of income")


def test_a_row_without_a_link_contributes_nothing():
    # Page numbers alone are not positions (F-55).
    doc = linked_document(
        [
            ("t", [["Item 1.", "Financial Statements", "78"], ["Item 2.", "MD&A", "7"]], {}),
            ("p", "Consolidated statements of income", None),
        ]
    )
    assert detect_sections(doc, "10-Q") == []


def test_index_part_link_starts_the_part_before_a_running_header():
    # JPM FY2025 10-K: the "Part IV" running header begins after Item 15's heading.
    doc = linked_document(
        [
            ("t", [["Part III"], ["Item 14.", "Principal Accounting Fees"], ["Part IV"],
                   ["Item 15.", "Exhibits"]],
             {"Part III": "p3", "Part IV": "p4", "Exhibits": "i15"}),
            ("p", "Item 14. Principal Accounting Fees and Services.", "p3"),
            ("p", "Item 15. Exhibits, Financial Statement Schedules.", "p4"),
            ("p", "Part IV", None),
        ]
    )  # fmt: skip
    codes = [s.qualified_code for s in detect_sections(doc, "10-K")]
    assert codes == ["III.14", "IV.15"]
