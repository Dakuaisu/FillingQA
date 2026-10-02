"""Router parsing, period resolution, confidence-gated filters, filtered BM25 (PRD 7.1).
Period ends are the stored values for NVDA, TGT (non-calendar) and PFE, XOM (calendar)."""

from __future__ import annotations

import json
from datetime import date

import pytest

from api.query.bm25 import build
from api.query.router import (
    RouterParseError,
    allowed_chunks,
    filters,
    parse,
    render,
    resolve_period,
)

TICKERS = {"AAPL", "BAC", "COST", "JPM", "NVDA", "PFE", "TGT", "XOM"}
ENDS = [
    ("NVDA", date(2025, 1, 26), 2025, None), ("NVDA", date(2025, 10, 26), 2026, 3),
    ("NVDA", date(2026, 1, 25), 2026, None),
    ("TGT", date(2025, 2, 1), 2024, None), ("TGT", date(2026, 1, 31), 2025, None),
    ("PFE", date(2024, 12, 31), 2024, None), ("BAC", date(2024, 12, 31), 2024, None),
    ("XOM", date(2024, 6, 30), 2024, 2),
]  # fmt: skip


def route(**kw):
    base = {"intent": "lookup", "entities": [{"ticker": "AAPL", "company_name": "Apple Inc."}],
            "fiscal_periods": ["FY2024"], "form_types": ["10-K"],
            "sub_queries": ["Apple inventories FY2024"], "confidence": 0.9}  # fmt: skip
    return {**base, **kw}


def test_parse_is_strict():
    assert parse(json.dumps(route()))["intent"] == "lookup"
    assert parse("```json\n" + json.dumps(route()) + "\n```")["confidence"] == 0.9
    no_sub = {k: v for k, v in route().items() if k != "sub_queries"}
    bads = (route(intent="other"), route(confidence=1.2), route(confidence=True),
            route(entities="AAPL"), no_sub)  # fmt: skip
    for bad in bads:
        with pytest.raises(RouterParseError):
            parse(json.dumps(bad))
    with pytest.raises(RouterParseError):
        parse("Intent: lookup")


def test_f119_dates_resolve_to_the_filers_own_fiscal_year():
    # xbrl_0083: NVIDIA's year ended January 25, 2026 is its FY2026.
    assert resolve_period("January 25, 2026", ["NVDA"], ENDS) == [[2026, None]]
    assert resolve_period("as of Jan. 25, 2026", ["NVDA"], ENDS) == [[2026, None]]
    # xbrl_0125: Target's year ended January 31, 2026 is its fiscal 2025; the 2026 is ignored.
    assert resolve_period("fiscal year ended January 31, 2026", ["TGT"], ENDS) == [[2025, None]]
    # Calendar-year filers: the year in the date is the fiscal year.
    assert resolve_period("December 31, 2024", ["PFE"], ENDS) == [[2024, None]]
    assert resolve_period("three months ended June 30, 2024", ["XOM"], ENDS) == [[2024, 2]]
    # A date that is no filing's period end is unresolved, not guessed.
    assert resolve_period("January 31, 2026", ["NVDA"], ENDS) is None


def test_fy_labels_are_literal_and_other_text_is_unresolved():
    assert resolve_period("FY2025", ["NVDA"], ENDS) == [[2025, None]]
    assert resolve_period("Q3 FY2024", [], ENDS) == [[2024, 3]]
    assert resolve_period("third quarter of fiscal 2024", [], ENDS) == [[2024, 3]]
    assert resolve_period("fiscal year 2023", [], ENDS) == [[2023, None]]
    # cmp_0018 and xbrl_0100's stated periods: a quarter label with a leading article.
    assert resolve_period("the third quarter of fiscal 2023", [], ENDS) == [[2023, 3]]
    assert resolve_period("the third quarter of fiscal 2026", [], ENDS) == [[2026, 3]]
    # Year-to-date phrases stay unresolved (F-124: no fourth rule).
    assert resolve_period("the first three quarters of fiscal 2024", [], ENDS) is None
    for text in ("last year", "2024", "calendar 2024"):
        assert resolve_period(text, [], ENDS) is None


def test_filters_are_gated_on_confidence_and_drop_what_they_cannot_use():
    f = filters(route(), TICKERS, 0.6, ENDS)
    assert f == {"tickers": ["AAPL"], "periods": [[2024, None]], "form_types": ["10-K"],
                 "unresolved_periods": []}  # fmt: skip
    assert filters(route(confidence=0.59), TICKERS, 0.6, ENDS) is None
    f = filters(route(entities=[{"ticker": "NFLX"}], fiscal_periods=["Q2 FY2025", "last year"],
                      form_types=["proxy"]), TICKERS, 0.6, ENDS)  # fmt: skip
    assert f == {"tickers": [], "periods": [[2025, 2]], "form_types": [],
                 "unresolved_periods": ["last year"]}  # fmt: skip
    assert filters(route(entities=[], fiscal_periods=[], form_types=[]), TICKERS, 0.6, ENDS) is None
    tgt = route(entities=[{"ticker": "TGT"}], fiscal_periods=["fiscal year ended January 31, 2026"])
    f = filters(tgt, TICKERS, 0.6, ENDS)
    assert f["periods"] == [[2025, None]]


def test_allowed_chunks_and_filtered_bm25():
    meta = [("a1", "AAPL", 2024, None, "10-K"), ("a2", "AAPL", 2025, 1, "10-Q"),
            ("a3", "AAPL", 2025, 2, "10-Q"), ("b1", "BAC", 2024, None, "10-K")]  # fmt: skip
    f = {"tickers": ["AAPL"], "periods": [[2024, None]], "form_types": []}
    assert allowed_chunks(meta, f) == {"a1"}
    f = {"tickers": ["AAPL"], "periods": [[2025, 2], [2024, None]], "form_types": []}
    assert allowed_chunks(meta, f) == {"a1", "a3"}
    idx = build([("a1", "inventories apple"), ("a2", "inventories"), ("b1", "inventories")],
                "k", 1.2, 0.75)  # fmt: skip
    assert [c for c, _ in idx.search("inventories", 10, allowed={"a2", "b1"})] == ["a2", "b1"]


def test_prompt_lists_the_corpus_companies_and_asks_for_periods_verbatim():
    p = render("What was Apple's revenue?", {"AAPL": "Apple", "BAC": "Bank of America"})
    assert "- AAPL: Apple" in p and p.rstrip().endswith("Question: What was Apple's revenue?")
    assert "never convert a date into a fiscal year" in p


def test_dense_search_dispatches_on_config(monkeypatch):
    import api.query.retrieve as r

    monkeypatch.setattr(r, "dense_exact_top_k", lambda conn, q, k: ["exact"])
    monkeypatch.setattr(
        r, "dense_top_k", lambda conn, q, k, ef: ([r.Retrieved("hnsw", 0.0, "")], "")
    )
    assert r.dense_search(None, "v", 5, {"dense_search": "exact", "hnsw_ef_search": 100}) == [
        "exact"
    ]
    assert r.dense_search(None, "v", 5, {"dense_search": "hnsw", "hnsw_ef_search": 100}) == ["hnsw"]
    assert r.dense_search(None, "v", 5, {"hnsw_ef_search": 100}) == ["exact"]
