"""Table extraction against the committed fixture filings (PRD 6.2 step 3).

Expected values are written out rather than blessed with --snapshot-update. Each
was hand-verified on 2026-10-01 (TRADEOFFS, "A blessed snapshot is only a test
if the baseline was verified"):

- every income statement row checked by arithmetic: AAPL 10-K 307,003 + 109,158
  = 416,161, 416,161 - 220,960 = 195,201, down to net income 112,010 and diluted
  EPS 112,010 / 15,004.697 = 7.46; AAPL 10-Q 111,184 - 56,403 = 54,781 down to
  29,578; TGT 10-K 104,780 - 75,511 - 21,535 - 2,617 = 5,117 down to 3,705
- column labels compared against the printed period headers
- TGT's 186 layout tables inspected by text: 80 page footers, ~70 running
  headers, cover-page and signature tables, the table of contents
"""

from __future__ import annotations

import re

import pytest

from api.numbers import parse_number
from api.parse.ixbrl import extract
from api.parse.sections import detect_sections
from api.parse.tables import (
    context_line,
    document_labels,
    extract_tables,
    is_nil,
    is_value,
    item_label,
    section_of,
)
from tests.conftest import AAPL_10K, AAPL_10Q, TGT_10K, fixture_bytes

FIXTURES = ((AAPL_10K, "10-K"), (AAPL_10Q, "10-Q"), (TGT_10K, "10-K"))


@pytest.fixture(scope="module")
def parsed():
    out = {}
    for accession, form in FIXTURES:
        doc = extract(fixture_bytes(accession))
        out[accession] = (doc, form, detect_sections(doc, form), extract_tables(doc))
    return out


@pytest.mark.parametrize(
    ("accession", "data", "layout"),
    [(AAPL_10K, 43, 11), (AAPL_10Q, 25, 6), (TGT_10K, 64, 186)],
)
def test_data_layout_split(parsed, accession, data, layout):
    tables = parsed[accession][3]
    assert sum(t.kind == "data" for t in tables) == data
    assert sum(t.kind == "layout" for t in tables) == layout


@pytest.mark.parametrize("accession", [AAPL_10K, AAPL_10Q, TGT_10K])
def test_caption_scale_never_contradicts_ixbrl_scale(parsed, accession):
    for table in parsed[accession][3]:
        if table.unit_scale and table.ix_scales:
            assert table.unit_scale in table.ix_scales, table.title


def income_statement(parsed, accession):
    doc, form, sections, tables = parsed[accession]
    table = next(
        t
        for t in tables
        if t.kind == "data" and t.title and re.search(r"statements? of operations", t.title, re.I)
    )
    company, period = document_labels(doc, form)
    item = item_label(section_of(table.block, sections), form)
    return table, context_line(table, company, period, item)


def rows_by_label(table):
    return {row[0]: row[1:] for row in table.body}


def test_aapl_10k_income_statement(parsed):
    table, context = income_statement(parsed, AAPL_10K)
    assert context == (
        "[Table: CONSOLIDATED STATEMENTS OF OPERATIONS | Apple Inc. | FY2025 10-K | Item 8 "
        "| in millions, USD]"
    )
    assert table.fiscal_periods == [
        "Years ended September 27, 2025",
        "Years ended September 28, 2024",
        "Years ended September 30, 2023",
    ]
    rows = rows_by_label(table)
    assert rows["Total net sales"] == ["416,161", "391,035", "383,285"]
    assert rows["Net income"] == ["$112,010", "$93,736", "$96,995"]
    assert rows["Other income/(expense), net"] == ["(321)", "269", "(565)"]


def test_aapl_10q_income_statement(parsed):
    table, context = income_statement(parsed, AAPL_10Q)
    assert context == (
        "[Table: CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS (Unaudited) | Apple Inc. "
        "| Q2 FY2026 10-Q | Part I, Item 1 | in millions, USD]"
    )
    assert table.fiscal_periods == [
        "Three Months Ended March 28, 2026",
        "Three Months Ended March 29, 2025",
        "Six Months Ended March 28, 2026",
        "Six Months Ended March 29, 2025",
    ]
    rows = rows_by_label(table)
    assert rows["Total net sales"] == ["111,184", "95,359", "254,940", "219,659"]
    assert rows["Net income"] == ["$29,578", "$24,780", "$71,675", "$61,110"]


def test_tgt_10k_income_statement(parsed):
    table, context = income_statement(parsed, TGT_10K)
    assert context == (
        "[Table: Consolidated Statements of Operations | TARGET CORPORATION | FY2025 10-K "
        "| Item 8 | in millions, USD]"
    )
    # TGT prints its own fiscal-year labels; fiscal 2025 ended 2026-01-31.
    assert table.fiscal_periods == ["2025", "2024", "2023"]
    rows = rows_by_label(table)
    assert rows["Net sales"] == ["$104,780", "$106,566", "$107,412"]
    assert rows["Net earnings"] == ["$3,705", "$4,091", "$4,138"]
    assert rows["Diluted earnings per share"] == ["$8.13", "$8.86", "$8.94"]


def test_rowspan_keeps_term_debt_headers_over_their_columns(parsed):
    """Regression: without rowspan, every header in this table sat one column left."""
    table = next(t for t in parsed[AAPL_10K][3] if t.title == "Term Debt")
    assert table.columns[1:] == [
        "Maturities (calendar year)",
        "2025 Amount (in millions)",
        "2025 Effective Interest Rate",
        "2024 Amount (in millions)",
        "2024 Effective Interest Rate",
    ]
    rows = rows_by_label(table)
    assert rows["Fixed-rate 0.000% – 4.850% notes"] == [  # noqa: RUF001
        "2025 – 2062",  # noqa: RUF001
        "$86,781",
        "0.03% – 5.75%",  # noqa: RUF001
        "$97,341",
        "0.03% – 6.65%",  # noqa: RUF001
    ]


_FIGURE = re.compile(r"\(?\$?\s?\d[\d,]*(?:\.\d+)?\)?")


def _figures(cell: str) -> list:
    if is_nil(cell.strip("$%")):
        return [0]
    return [abs(parse_number(m.group(0))) for m in _FIGURE.finditer(cell)]


@pytest.mark.parametrize("accession", [AAPL_10K, AAPL_10Q, TGT_10K])
def test_every_tagged_figure_survives_extraction_in_order(parsed, accession):
    """An independent check: iXBRL tags each figure where it prints, so the tagged
    figures inside a table, in document order, must appear in the extracted cells
    read row by row. A dropped, duplicated or reordered cell breaks the sequence.
    """
    doc, _, _, tables = parsed[accession]
    for table in tables:
        if table.kind != "data":
            continue
        block = table.block
        positions: dict[tuple[int, int], str] = {}
        for span in doc.spans:
            if span.is_numeric and block.char_start <= span.char_start < block.char_end:
                # One printed figure can carry several nested facts.
                positions.setdefault((span.char_start, span.char_end), span.raw_text)
        tagged = [abs(parse_number(raw)) for raw in positions.values()]
        cells = iter(n for row in table.body for cell in row for n in _figures(cell))
        assert all(any(t == c for c in cells) for t in tagged), table.title


@pytest.mark.parametrize("accession", [AAPL_10K, AAPL_10Q, TGT_10K])
def test_no_value_cell_holds_several_figures(parsed, accession):
    """Catches columns collapsing into one, which the order check above cannot:
    the figures stay in order, they just all land in the same cell."""
    for table in parsed[accession][3]:
        for row in table.body:
            for cell in row[1:]:
                parts = cell.split()
                assert not (len(parts) > 1 and all(is_value(p) for p in parts)), (table.title, cell)


def test_stacked_period_blocks_keep_their_columns(parsed):
    """Regression: the mid-table "Six Months Ended March 29, 2025" header spans
    every region column and used to merge all seven into one. Totals checked by
    hand: 92,963 + 58,315 + 34,515 + 16,285 + 17,581 = 219,659."""
    table = next(
        t
        for t in parsed[AAPL_10Q][3]
        if t.kind == "data" and t.body and t.body[0][0] == "Net sales" and t.scale_source == "ixbrl"
    )
    net_sales = [row[1:] for row in table.body if row[0] == "Net sales"]
    assert net_sales == [
        ["$103,622", "$66,201", "$46,023", "$17,814", "$21,280", "$—", "$254,940"],
        ["$92,963", "$58,315", "$34,515", "$16,285", "$17,581", "$—", "$219,659"],
    ]


@pytest.mark.parametrize(
    ("accession", "caption", "ixbrl"),
    [(AAPL_10K, 35, 3), (AAPL_10Q, 22, 2), (TGT_10K, 48, 2)],
)
def test_scale_source_breakdown(parsed, accession, caption, ixbrl):
    """Fallback tables hand-checked: AAPL's are continuations of "(in millions)"
    tables; TGT's are RSU/PSU unit counts in thousands, per-share fair values
    tagged at scale 0."""
    data = [t for t in parsed[accession][3] if t.kind == "data"]
    assert sum(t.scale_source == "caption" for t in data) == caption
    assert sum(t.scale_source == "ixbrl" for t in data) == ixbrl
    assert all(t.block.scale_source == t.scale_source for t in data)


def test_mixed_magnitudes_stay_unscaled(parsed):
    # AAPL Note 3: net income in millions, shares in thousands, and no "except".
    table = next(t for t in parsed[AAPL_10K][3] if t.title == "Note 3 – Earnings Per Share")  # noqa: RUF001
    assert table.ix_scales == {"millions", "thousands"}
    assert table.unit_scale is None and table.scale_source is None


@pytest.mark.parametrize("accession", [AAPL_10K, AAPL_10Q, TGT_10K])
def test_every_currency_figure_carries_its_tables_scale(parsed, accession):
    """The invariant behind the monetary veto: in a table given a scale, from a
    caption or from iXBRL, no dollar figure is tagged at a different scale. Held
    on all 12 dev-slice filings (2026-10-01), so the veto never fired there."""
    doc, _, _, tables = parsed[accession]
    words = {3: "thousands", 6: "millions", 9: "billions"}
    for table in tables:
        if table.kind != "data" or not table.unit_scale:
            continue
        assert not table.scale_conflict
        block = table.block
        inside = (s for s in doc.spans if block.char_start <= s.char_start < block.char_end)
        for span in inside:
            unit = doc.units.get(span.unit_ref or "")
            if span.is_numeric and unit and unit.is_monetary:
                assert words.get(span.scale) == table.unit_scale, (table.title, span.raw_text)
