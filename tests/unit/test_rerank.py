"""Reranking helpers (PRD 7.3): ordering, floor, top-n, and the one-pass call."""

from __future__ import annotations

from api.config import rerank as rerank_cfg
from api.query.rerank import apply_floor, order, rerank, sigmoid, top_n_for


def test_order_and_floor():
    ranked = order(["b", "a", "c"], [0.5, 0.5, 0.9])
    assert ranked == [("c", 0.9), ("a", 0.5), ("b", 0.5)]
    assert apply_floor(ranked, 0.6) == [("c", 0.9)]
    assert apply_floor(ranked, 0.95) == []  # all below the floor: abstain


def test_top_n_by_type_and_config():
    cfg = rerank_cfg()
    assert top_n_for("synthesis", cfg) == 10 and top_n_for("table", cfg) == 8
    assert cfg["floor_calibration"] == "pending" and cfg["score_floor"] == 0.30


def test_rerank_scores_every_candidate_in_one_pass():
    calls = []

    class Fake:
        def predict(self, pairs, batch_size, activation_fn, convert_to_numpy):
            calls.append((len(pairs), batch_size))
            return [activation_fn(x) for x in (2.0, -1.0, 0.0)]

    ranked, secs = rerank(Fake(), "q", [("a", "x"), ("b", "y"), ("c", "z")])
    assert calls == [(3, 3)] and secs >= 0
    assert [c for c, _ in ranked] == ["a", "c", "b"]
    assert ranked[0][1] == sigmoid(2.0)
