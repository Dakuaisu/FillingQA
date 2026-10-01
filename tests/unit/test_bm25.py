"""Okapi BM25 (TRADEOFFS: BM25 sparse retrieval). Inline texts, hand-computed scores."""

from __future__ import annotations

import math

import pytest

from api.query.bm25 import StaleIndexError, build, corpus_key, load_or_build, tokenize


def test_tokenizer_keeps_filing_tokens_intact():
    assert tokenize("[Apple Inc. (AAPL) | 10-Q | Q2 FY2025 | Part I, Item 7A: Market Risk]") == [
        "apple", "inc", "aapl", "10-q", "q2", "fy2025", "part", "i", "item", "7a", "market", "risk",
    ]  # fmt: skip
    assert tokenize("Net sales were $7,286 million, or 1,434.5 thousand; non-GAAP 8-K.") == [
        "net", "sales", "were", "7286", "million", "or", "1434.5", "thousand", "non-gaap", "8-k",
    ]  # fmt: skip
    assert tokenize("Losses") == ["losses"]  # no stemming


def test_scores_match_the_okapi_formula():
    rows = [("c1", "apple sales sales"), ("c2", "apple"), ("c3", "bank deposits")]
    idx = build(rows, "k", 1.2, 0.75)
    assert idx.avgdl == pytest.approx(2.0)
    idf_apple = math.log(1 + (3 - 2 + 0.5) / (2 + 0.5))
    idf_sales = math.log(1 + (3 - 1 + 0.5) / (1 + 0.5))

    def term(idf, tf, dl):
        return idf * tf * 2.2 / (tf + 1.2 * (1 - 0.75 + 0.75 * dl / 2.0))

    got = dict(idx.search("Apple sales?", 10))
    assert got["c1"] == pytest.approx(term(idf_apple, 1, 3) + term(idf_sales, 2, 3))
    assert got["c2"] == pytest.approx(term(idf_apple, 1, 1))
    assert "c3" not in got  # no matching term: no score, not listed
    assert [c for c, _ in idx.search("apple sales", 10)] == ["c1", "c2"]


def test_idf_is_never_negative_and_ties_go_to_the_smaller_id():
    idx = build([("b", "x"), ("a", "x"), ("c", "x")], "k", 1.2, 0.75)
    assert idx.idf("x") > 0
    assert [c for c, _ in idx.search("x", 3)] == ["a", "b", "c"]


def test_cache_is_reused_rebuilt_on_change_and_stale_use_refused(tmp_path):
    path = tmp_path / "bm25.pkl"
    rows = [("c1", "apple"), ("c2", "bank")]
    idx, rebuilt = load_or_build(path, rows, "v1", 1.2, 0.75)
    assert rebuilt and path.exists()
    assert load_or_build(path, rows, "v1", 1.2, 0.75)[1] is False
    assert load_or_build(path, [("c1", "apple!"), ("c2", "bank")], "v1", 1.2, 0.75)[1] is True
    assert load_or_build(path, rows, "v2", 1.2, 0.75)[1] is True  # chunker_version changed
    idx, _ = load_or_build(path, rows, "v2", 1.2, 0.75)
    idx.check(corpus_key("v2", rows))
    with pytest.raises(StaleIndexError):
        idx.check(corpus_key("v1", rows))
