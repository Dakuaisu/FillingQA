"""Heading tables (F-63): which short layout tables are Item/Part headings.

Cell text is verbatim from the filings named; the tiny documents only give the
cells offsets to live at.
"""

from __future__ import annotations

from api.parse.ixbrl import Anchor, Block, ExtractedDocument
from api.parse.sections import is_heading_table, text_without_anchors


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
