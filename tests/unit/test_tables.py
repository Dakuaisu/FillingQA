"""Pure-function tests for table extraction. Every string is copied from a real
filing in the dev slice; the source is noted where it matters."""

from __future__ import annotations

from decimal import Decimal

import pytest

from api.numbers import parse_number
from api.parse.ixbrl import extract
from api.parse.tables import (
    Cell,
    _caption_window_start,
    _first_body_row,
    _merge_fragments,
    classify,
    detect_unit_scale,
    extract_tables,
    is_nil,
    is_value,
    ixbrl_scale,
)
from tests.conftest import AAPL_10K, AAPL_10Q, TGT_10K, fixture_bytes

# ------------------------------------------------------------ unit scale


@pytest.mark.parametrize(
    ("caption", "expected"),
    [
        ("(in thousands, except per share data)", "thousands"),
        ("(dollars in millions)", "millions"),  # AAPL MD&A
        ("(millions)", "millions"),  # TGT, inside the table, no "in"
        ("(amounts in millions, except par value and share data)", "millions"),  # COST
        (
            "(In millions, except number of shares, which are reflected in thousands, "
            "and per-share amounts)",
            "millions",  # AAPL income statement: thousands is the exception
        ),
        ("Membership was made up of the following (in thousands):", "thousands"),  # COST
    ],
)
def test_detect_unit_scale_reads_the_main_scale(caption, expected):
    assert detect_unit_scale(caption) == expected


def test_two_scales_without_except_is_ambiguous():
    # AAPL Note 3: net income and share counts really are on different scales.
    assert detect_unit_scale("(net income in millions and shares in thousands):") is None


def test_a_scale_word_in_prose_is_not_a_caption():
    assert detect_unit_scale("we employ thousands of team members") is None


def test_the_caption_nearest_the_table_wins():
    text = "(in thousands)\nsome text\nOperating expenses were as follows (dollars in millions):"
    assert detect_unit_scale(text) == "millions"


def test_no_caption_returns_none():
    assert detect_unit_scale("The components of lease expense were as follows:") is None


# ------------------------------------------------------- iXBRL scale fallback

# Each set is (scale attribute, is_monetary) per tagged figure, as observed on a
# real dev-slice table, with the count of fallback tables showing it.
USD, NOT_USD = True, False


@pytest.mark.parametrize(
    ("tagged", "expected"),
    [
        ({(6, USD)}, "millions"),  # 54 fallback tables, e.g. AAPL segment continuations
        ({(6, USD), (-2, NOT_USD)}, "millions"),  # 5, COST: percentages tagged at -2
        ({(3, NOT_USD), (0, NOT_USD)}, "thousands"),  # 6, TGT RSUs: units, per-share at 0
        ({(6, USD), (None, NOT_USD)}, "millions"),  # TGT EPS: usdPerShare, no scale attr
        ({(6, USD), (0, NOT_USD)}, "millions"),  # per-share at 0 is the "except" set
    ],
)
def test_one_magnitude_gives_the_scale(tagged, expected):
    assert ixbrl_scale(tagged) == (expected, False)


@pytest.mark.parametrize(
    "tagged",
    [
        {(6, USD), (3, NOT_USD), (0, NOT_USD)},  # AAPL statements: dollars and shares
        {(6, USD), (3, USD)},  # two magnitudes
        {(-2, NOT_USD)},  # percentages only
        set(),
    ],
)
def test_mixed_or_absent_magnitude_gives_none_without_conflict(tagged):
    assert ixbrl_scale(tagged) == (None, False)


@pytest.mark.parametrize(
    "tagged",
    [
        {(6, USD), (None, USD)},  # a dollar figure at units under "in millions"
        {(6, USD), (0, USD)},
        {(3, NOT_USD), (None, USD)},  # dollars at units in a thousands-of-shares table
    ],
)
def test_off_scale_currency_figure_vetoes_the_fallback(tagged):
    # Not observed on the slice -- the veto never fired -- so these pairs are
    # constructed. They are what the rule exists to stop.
    assert ixbrl_scale(tagged) == (None, True)


# ----------------------------------------------------------------- values


@pytest.mark.parametrize("text", ["34,550", "(95,699)", "10%", "$7.49", "$(861)", "14,948,500"])
def test_printed_figures_are_values(text):
    assert is_value(text)


@pytest.mark.parametrize("text", ["—", "$", "Change", "2025 – 2062", "Item 1A."])  # noqa: RUF001
def test_non_figures_are_not_values(text):
    assert not is_value(text)


def test_dollar_sign_before_parenthesized_negative():
    # TGT gift card table: `$` and `(861)` sit in adjacent cells.
    assert parse_number("$(861)") == Decimal(-861)
    assert parse_number("$ (861)") == Decimal(-861)


# -------------------------------------------------------------- fragments


def row(*cells: tuple[int, int, str]) -> list[Cell]:
    return [Cell(start, end, text) for start, end, text in cells]


def test_dollar_and_percent_fragments_join_their_figure():
    # AAPL 10-K operating expenses, first data row.
    merged = _merge_fragments(
        row((0, 3, "Research and development"), (3, 4, "$"), (4, 5, "34,550"), (9, 11, "10"),
            (11, 12, "%"))
    )  # fmt: skip
    assert [(c.col_start, c.col_end, c.text) for c in merged] == [
        (0, 3, "Research and development"),
        (3, 5, "$34,550"),
        (9, 12, "10%"),
    ]


# ----------------------------------------------------------- classification


def test_page_footer_is_layout():
    # TGT 10-K: 80 of these, one per page. One number per row is a page number.
    assert classify([row((0, 1, "TARGET CORPORATION"), (1, 2, "2025 Form 10-K"), (2, 3, "8"))]) == (
        "layout"
    )


def test_table_of_contents_is_layout():
    assert classify([row((0, 1, "Item 1A."), (1, 2, "Risk Factors"), (2, 3, "5"))]) == "layout"


def test_two_figures_in_a_row_is_data():
    assert classify([row((0, 3, "SG&A expenses"), (3, 4, "$"), (4, 5, "24,966"), (9, 10, "$"),
                         (10, 11, "22,810"))]) == "data"  # fmt: skip


# ------------------------------------------------- F-50: caption window boundary


@pytest.fixture(scope="module")
def aapl_10k():
    return extract(fixture_bytes(AAPL_10K))


def test_caption_search_stops_at_the_preceding_table(aapl_10k):
    # AAPL 10-K: the percentage-only "Gross margin percentage:" table continues
    # the gross margin table directly above it, whose caption is "(dollars in
    # millions)". The window must end at that table, not reach its caption.
    tables = extract_tables(aapl_10k)
    pct = next(t for t in tables if t.body and t.body[0][0] == "Gross margin percentage:")
    index = aapl_10k.blocks.index(pct.block)
    previous = max(
        (b for b in aapl_10k.blocks[:index] if b.kind == "table"), key=lambda b: b.char_end
    )
    assert _caption_window_start(aapl_10k, index) == previous.char_end
    assert pct.unit_scale is None and pct.scale_source is None


def test_header_less_continuation_stays_header_less(aapl_10k):
    # Never borrow the preceding table's column labels (TRADEOFFS, F-50).
    pct = next(
        t for t in extract_tables(aapl_10k) if t.body and t.body[0][0] == "Gross margin percentage:"
    )
    assert pct.header_rows == 0
    assert not any(pct.columns)


# --------------------------------------------- F-51: dash-only rows are body rows

# Cells and column positions copied verbatim from AAPL 10-Q 0000320193-26-000020,
# "Purchases of Equity Securities by the Issuer and Affiliated Purchasers" -- the
# only table on the slice with this shape, and not one of the committed fixtures.
REPURCHASES = [
    row(
        (0, 3, "Periods"),
        (6, 9, "Total Number of Shares Purchased"),
        (12, 15, "Average Price Paid Per Share"),
        (
            18,
            21,
            "Total Number of Shares Purchased as Part of Publicly Announced Plans or Programs",
        ),
    ),
    row((0, 3, "March 29, 2026 to May 2, 2026:")),
    row(
        (0, 3, "Open market and privately negotiated purchases"),
        (6, 8, "—"),
        (12, 14, "$—"),
        (18, 20, "—"),
    ),
]


def test_a_dash_only_row_is_a_body_row():
    assert _first_body_row(REPURCHASES) == 2


def test_a_label_only_row_is_not_made_a_body_row():
    assert _first_body_row(REPURCHASES[:2]) == 2  # nothing in it is a figure or a dash


@pytest.mark.parametrize("accession", [AAPL_10K, AAPL_10Q, TGT_10K])
def test_no_column_label_carries_a_dash(accession):
    for table in extract_tables(extract(fixture_bytes(accession))):
        for label in table.columns:
            assert not any(is_nil(word.strip("$%")) for word in label.split()), label
