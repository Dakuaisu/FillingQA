"""Router parsing, confidence-gated filters and filtered BM25 (PRD 7.1). Inline data."""

from __future__ import annotations

import json

import pytest

from api.query.bm25 import build
from api.query.router import RouterParseError, allowed_chunks, filters, parse, render

TICKERS = {"AAPL", "BAC", "COST", "JPM", "NVDA", "PFE", "TGT", "XOM"}


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


def test_filters_are_gated_on_confidence_and_drop_what_they_cannot_use():
    f = filters(route(), TICKERS, 0.6)
    assert f == {
        "tickers": ["AAPL"],
        "fiscal_years": [2024],
        "fiscal_quarters": [],
        "form_types": ["10-K"],
    }
    assert filters(route(confidence=0.59), TICKERS, 0.6) is None
    f = filters(route(entities=[{"ticker": "NFLX"}], fiscal_periods=["Q2 FY2025", "last year"],
                      form_types=["proxy"]), TICKERS, 0.6)  # fmt: skip
    assert f == {"tickers": [], "fiscal_years": [2025], "fiscal_quarters": [2], "form_types": []}
    assert filters(route(entities=[], fiscal_periods=[], form_types=[]), TICKERS, 0.6) is None


def test_allowed_chunks_and_filtered_bm25():
    meta = [("a1", "AAPL", 2024, None, "10-K"), ("a2", "AAPL", 2025, 1, "10-Q"),
            ("b1", "BAC", 2024, None, "10-K")]  # fmt: skip
    f = {"tickers": ["AAPL"], "fiscal_years": [2024], "fiscal_quarters": [], "form_types": []}
    assert allowed_chunks(meta, f) == {"a1"}
    idx = build([("a1", "inventories apple"), ("a2", "inventories"), ("b1", "inventories")],
                "k", 1.2, 0.75)  # fmt: skip
    assert [c for c, _ in idx.search("inventories", 10, allowed={"a2", "b1"})] == ["a2", "b1"]


def test_prompt_lists_the_corpus_companies():
    p = render("What was Apple's revenue?", {"AAPL": "Apple", "BAC": "Bank of America"})
    assert "- AAPL: Apple" in p and p.rstrip().endswith("Question: What was Apple's revenue?")
