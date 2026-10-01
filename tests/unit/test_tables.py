"""Pure-function tests for table extraction. Every string is copied from a real
filing in the dev slice; the source is noted where it matters."""

from __future__ import annotations

from decimal import Decimal

import pytest

from api.numbers import parse_number
from api.parse.tables import (
    Cell,
    _merge_fragments,
    classify,
    detect_unit_scale,
    is_value,
    ixbrl_scale,
)

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
