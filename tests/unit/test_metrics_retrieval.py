"""Retrieval metrics (PRD 11.2, F-77). Synthetic ranked lists of chunk ids."""

from __future__ import annotations

from math import isclose, log2

import pytest

from eval.metrics.retrieval import mrr, ndcg_at_k, precision_at_k, recall_at_k, sufficiency_at_k

EIGHT = [[f"g{i}"] for i in range(8)]  # F-77's example: 8 single-chunk alternatives
PAIR = [["a", "b"]]  # one two-chunk comparison set


def test_sufficiency_needs_a_whole_set():
    assert sufficiency_at_k(["x", "g3"], EIGHT, 2) is True
    assert sufficiency_at_k(["a", "x", "b"], PAIR, 2) is False
    assert sufficiency_at_k(["a", "x", "b"], PAIR, 3) is True


def test_recall_is_best_per_set_coverage():
    assert recall_at_k(["a", "x"], PAIR, 10) == 0.5
    assert recall_at_k(["x"], [["a", "b"], ["c"]], 10) == 0.0
    assert recall_at_k(["c"], [["a", "b"], ["c"]], 10) == 1.0


def test_precision_is_over_k_against_the_union():
    assert precision_at_k(["g0", "x", "g1", "y"], EIGHT, 4) == 0.5
    assert precision_at_k(["g0"], EIGHT, 10) == 0.1


def test_mrr_first_chunk_of_any_set():
    assert mrr(["x", "y", "b"], PAIR) == pytest.approx(1 / 3)
    assert mrr(["x"], PAIR) == 0.0


def test_ndcg_takes_the_best_set_f77():
    # One of 8 alternatives at rank 1: 1.0 (union-as-relevant would give ~0.25).
    assert ndcg_at_k(["g5", "x", "y"], EIGHT, 10) == 1.0
    assert isclose(ndcg_at_k(["x", "g5"], EIGHT, 10), 1 / log2(3))
    # Two-chunk set: one at rank 1, the other missing -> 1 / (1 + 1/log2 3) = 0.613.
    assert isclose(ndcg_at_k(["a", "x"], PAIR, 10), 1 / (1 + 1 / log2(3)))
    assert ndcg_at_k(["a", "b"], PAIR, 10) == 1.0
    assert ndcg_at_k(["b", "a"], PAIR, 10) == 1.0


def test_ndcg_counts_a_chunk_once_and_ideal_ignores_list_length():
    assert ndcg_at_k(["a", "a", "b"], PAIR, 10) == ndcg_at_k(["a", "x", "b"], PAIR, 10)
    # A list shorter than k does not shrink the ideal: one of two found, rank 1.
    assert isclose(ndcg_at_k(["a"], PAIR, 10), 1 / (1 + 1 / log2(3)))
    # IDCG over min(|set|, k): a 3-chunk set at k=2, both slots filled -> 1.0.
    assert ndcg_at_k(["a", "b"], [["a", "b", "c"]], 2) == 1.0


def test_abstain_items_have_no_retrieval_score():
    for f in (lambda: sufficiency_at_k(["a"], [], 10), lambda: recall_at_k(["a"], [], 10),
              lambda: precision_at_k(["a"], [], 10), lambda: mrr(["a"], []),
              lambda: ndcg_at_k(["a"], [], 10)):  # fmt: skip
        assert f() is None
    with pytest.raises(ValueError):
        ndcg_at_k(["a"], PAIR, 0)
