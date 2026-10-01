"""Reciprocal Rank Fusion (PRD 7.2). Synthetic rankings of chunk ids."""

from __future__ import annotations

import pytest

from api.config import retrieval
from api.query.retrieve import rrf_fuse


def test_rrf_scores_and_order():
    dense, sparse = ["a", "b", "c"], ["c", "d", "a"]
    out = rrf_fuse([dense, sparse], [1.0, 1.0], 60)
    # a: 1/61 + 1/63; c: 1/63 + 1/61 -> tie, broken by best rank (both 1), then id.
    assert out[:2] == ["a", "c"] and set(out) == {"a", "b", "c", "d"}
    # b and d both score 1/62 with best rank 2: the smaller id comes first.
    assert out.index("b") < out.index("d")


def test_weights_shift_the_order():
    out = rrf_fuse([["a"], ["b"]], [1.0, 1.5], 60)
    assert out == ["b", "a"]


def test_a_document_counts_once_per_ranking_and_lengths_must_match():
    assert rrf_fuse([["a", "a", "b"]], [1.0], 60) == ["a", "b"]
    with pytest.raises(ValueError):
        rrf_fuse([["a"]], [1.0, 1.0], 60)
    assert rrf_fuse([[], []], [1.0, 1.0], 60) == []


def test_config_holds_prd_values():
    cfg = retrieval()
    assert (cfg["k_dense"], cfg["k_sparse"], cfg["rrf_k"]) == (50, 50, 60)
    assert cfg["weights"] == {"dense": 1.0, "sparse": 1.0}
