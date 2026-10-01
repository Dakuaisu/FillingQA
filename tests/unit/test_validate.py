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
)
from tests.conftest import AAPL_10K, AAPL_10Q, TGT_10K, fixture_bytes

BOUNDS = parser_bounds()

AAPL_10K_MEASURED = Measurements(
    form_type="10-K",
    sections=23,
    missing_items=[],
    required_items=5,
    has_item_1a=True,
    data_tables=43,
    scaled_caption=35,
    scaled_ixbrl=3,
    scale_eligible=39,
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


def test_item_1a_is_required_of_a_10k_only():
    tenq = replace(AAPL_10K_MEASURED, form_type="10-Q", has_item_1a=False, required_items=2)
    assert check(tenq, BOUNDS) == []


def test_score_is_the_mean_of_defined_components():
    components = score_components(AAPL_10K_MEASURED, BOUNDS)
    assert components["scale_coverage"] == pytest.approx(38 / 39)
    assert components["span_resolution"] == pytest.approx(962 / 967)
    assert score(AAPL_10K_MEASURED, BOUNDS) == pytest.approx((38 / 39 + 1 + 962 / 967 + 1 + 1) / 5)


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
