"""Parser validation suite and parse-quality score.

`check` and `score` take a Measurements record, so each assertion is exercised by
moving one measured quantity across its bound. The baseline record is the AAPL
FY2025 10-K as actually measured on 2026-10-01; the fixture test at the end
re-measures the three committed filings.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from api.config import parser_bounds
from api.parse.ixbrl import extract
from api.parse.validate import (
    Measurements,
    alpha_char_ratio,
    check,
    fiscal_quarter,
    measure,
    parser_version,
    score,
    score_components,
    span_rows,
    stub_items,
)
from tests.conftest import AAPL_10K, AAPL_10Q, TGT_10K, fixture_bytes

BOUNDS = parser_bounds()

AAPL_10K_MEASURED = Measurements(
    form_type="10-K",
    sections=23,
    missing_items=[],
    required_items=5,
    has_item_1a=True,
    item_chars={"1": 15995, "1A": 68042, "7": 18023, "7A": 3023, "8": 61072},
    data_tables=43,
    scaled_caption=32,
    scaled_ixbrl=5,
    scale_eligible=38,  # F-50: the percentage table no longer has a borrowed scale
    collapsed_tables=0,
    numeric_spans=967,
    resolved_spans=962,
    span_mismatches=0,
    alpha_ratio=0.765,
    fiscal_year=2025,
    fiscal_period="FY",
)


def test_bounds_come_from_config():
    assert BOUNDS["min_sections"] == 5
    assert BOUNDS["min_data_tables"] == 10
    assert BOUNDS["alpha_ratio"] == {"min": 0.4, "max": 0.95}


def test_a_good_filing_passes():
    assert check(AAPL_10K_MEASURED, BOUNDS) == []


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"sections": 4}, "4 sections < 5"),
        ({"missing_items": ["7A"]}, "required Items missing"),
        ({"has_item_1a": False}, "no Item 1A"),
        ({"data_tables": 9}, "9 data tables < 10"),
        ({"alpha_ratio": 0.39}, "alpha ratio"),
        ({"alpha_ratio": 0.96}, "alpha ratio"),
        ({"fiscal_year": None}, "DocumentFiscalYearFocus"),
        ({"span_mismatches": 1}, "do not slice back"),
    ],
)
def test_each_assertion_quarantines(change, message):
    failures = check(replace(AAPL_10K_MEASURED, **change), BOUNDS)
    assert len(failures) == 1
    assert message in failures[0]


def test_an_item_7_stub_quarantines():
    # JPM's 10-K, as measured: Item 7 points to Annual Report pages (F-66).
    jpm = replace(AAPL_10K_MEASURED, item_chars={**AAPL_10K_MEASURED.item_chars, "7": 395})
    failures = check(jpm, BOUNDS)
    assert len(failures) == 1 and "Item 7 is 395 chars <= 1000" in failures[0]


@pytest.mark.parametrize("code, chars", [("7A", 217), ("8", 206)])
def test_7a_and_8_may_be_stubs(code, chars):
    # BAC's Item 7A points into Item 7; NVDA's Item 8 points to Item 15 (F-68, F-69).
    filing = replace(AAPL_10K_MEASURED, item_chars={**AAPL_10K_MEASURED.item_chars, code: chars})
    assert check(filing, BOUNDS) == []
    assert stub_items(filing.item_chars, BOUNDS["stub_max_chars"]) == [code]


@pytest.mark.parametrize("code", ["1", "1A"])
def test_items_1_and_1a_must_not_be_stubs(code):
    filing = replace(AAPL_10K_MEASURED, item_chars={**AAPL_10K_MEASURED.item_chars, code: 400})
    assert "cross-reference stub" in check(filing, BOUNDS)[0]


def test_10q_items_must_not_be_stubs():
    tenq = replace(
        AAPL_10K_MEASURED, form_type="10-Q", has_item_1a=False, required_items=2,
        item_chars={"I.1": 30000, "I.2": 900},
    )  # fmt: skip
    assert "Item I.2 is 900 chars" in check(tenq, BOUNDS)[0]


def test_stub_bound_is_one_config_value():
    assert BOUNDS["stub_max_chars"] == 1000
    assert "min_required_item_chars" not in BOUNDS


def test_item_1a_is_required_of_a_10k_only():
    tenq = replace(
        AAPL_10K_MEASURED, form_type="10-Q", has_item_1a=False, required_items=2, item_chars={}
    )
    assert check(tenq, BOUNDS) == []


def test_score_is_the_mean_of_defined_components():
    components = score_components(AAPL_10K_MEASURED, BOUNDS)
    assert components["scale_coverage"] == pytest.approx(37 / 38)
    assert components["span_resolution"] == pytest.approx(962 / 967)
    assert score(AAPL_10K_MEASURED, BOUNDS) == pytest.approx((37 / 38 + 1 + 962 / 967 + 1 + 1) / 5)


def test_undefined_components_are_left_out_not_scored():
    no_scale_evidence = replace(
        AAPL_10K_MEASURED, scale_eligible=0, scaled_caption=0, scaled_ixbrl=0
    )
    assert score_components(no_scale_evidence, BOUNDS)["scale_coverage"] is None
    assert score(no_scale_evidence, BOUNDS) == pytest.approx((1 + 962 / 967 + 1 + 1) / 4)


def test_score_does_not_gate():
    # A filing with a low score but no failed assertion is still not quarantined.
    weak = replace(AAPL_10K_MEASURED, scaled_caption=0, scaled_ixbrl=0, resolved_spans=0)
    assert score(weak, BOUNDS) < 0.7
    assert check(weak, BOUNDS) == []


@pytest.mark.parametrize(("fp", "quarter"), [("Q1", 1), ("Q3", 3), ("FY", None), (None, None)])
def test_fiscal_quarter(fp, quarter):
    assert fiscal_quarter(fp) == quarter


def test_alpha_char_ratio_counts_letters_over_all_characters():
    assert alpha_char_ratio("ab 12") == pytest.approx(2 / 5)
    assert alpha_char_ratio("") == 0.0


def test_parser_version_is_stable_across_calls():
    assert parser_version() == parser_version()
    assert len(parser_version()) == 12


@pytest.mark.parametrize(
    ("accession", "form"), [(AAPL_10K, "10-K"), (AAPL_10Q, "10-Q"), (TGT_10K, "10-K")]
)
def test_committed_fixtures_pass_validation(accession, form):
    assert check(measure(extract(fixture_bytes(accession)), form), BOUNDS) == []


def test_aapl_10k_measurements_match_the_baseline():
    measured = measure(extract(fixture_bytes(AAPL_10K)), "10-K")
    assert measured.alpha_ratio == pytest.approx(0.765, abs=5e-4)
    assert replace(measured, alpha_ratio=0.765) == AAPL_10K_MEASURED


@pytest.fixture(scope="module")
def aapl_10k_doc():
    return extract(fixture_bytes(AAPL_10K))


def test_span_rows_are_the_resolved_numeric_spans(aapl_10k_doc):
    rows = span_rows(aapl_10k_doc, AAPL_10K)
    resolved = [s for s in aapl_10k_doc.spans if s.is_numeric and s.value is not None]
    assert len(rows) == len(resolved) == 962  # 967 numeric, 5 word-form skipped (F-33)


def test_span_rows_slice_back_to_their_raw_text(aapl_10k_doc):
    text = aapl_10k_doc.text
    for accession, _, _, value, _, raw_text, start, end in span_rows(aapl_10k_doc, AAPL_10K):
        assert accession == AAPL_10K
        assert value is not None
        assert 0 <= start < end <= len(text)
        assert text[start:end] == raw_text


def test_span_rows_keep_dimensional_contexts(aapl_10k_doc):
    # F-32 filtering is Phase 3's; context_ref is stored for it.
    refs = {row[2] for row in span_rows(aapl_10k_doc, AAPL_10K)}
    assert any(aapl_10k_doc.contexts[r].is_dimensional for r in refs)
