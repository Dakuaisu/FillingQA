"""Pipeline lists per PRD 11.6 config (eval/pipeline.py). Synthetic ids and scores."""

from __future__ import annotations

import pytest

from eval.pipeline import context_for

CFG = {"top_n": 2, "top_n_synthesis": 3, "score_floor": 0.3, "timeout_ms": 800}
DENSE = ["d1", "d2", "d3", "d4", "d5", "d6"]
FUSED = ["f1", "f2", "f3", "f4"]
RERANKED = [("f3", 0.9), ("f1", 0.5), ("f2", 0.2), ("f4", 0.1)]


def ctx(pipeline, **kw):
    args = {"dense": DENSE, "fused": FUSED, "reranked": RERANKED, "rerank_seconds": 0.2,
            "rerank_cfg": CFG, "question_type": "table", "baseline_top_k": 5}  # fmt: skip
    return context_for(pipeline, **{**args, **kw})


def test_dense_and_hybrid():
    c = ctx("config_1_dense")
    assert c["retrieved"] == DENSE and c["generator_input"] == DENSE[:5]
    assert c["retrieved_post_rerank"] is None
    c = ctx("config_3_hybrid")
    assert c["retrieved"] == FUSED and c["generator_input"] == ["f1", "f2"]


def test_rerank_floor_top_n_and_synthesis():
    c = ctx("config_4_rerank")
    assert c["retrieved"] == FUSED and c["retrieved_post_rerank"] == ["f3", "f1"]
    assert c["generator_input"] == ["f3", "f1"] and not c["fell_back"] and not c["abstain"]
    c = ctx("config_4_rerank", question_type="synthesis")
    assert c["retrieved_post_rerank"] == ["f3", "f1"]  # f2, f4 below the floor


def test_timeout_falls_back_to_rrf_order_and_empty_floor_abstains():
    c = ctx("config_4_rerank", rerank_seconds=0.9)
    assert c["fell_back"] and c["retrieved_post_rerank"] == ["f1", "f2"]
    c = ctx("config_4_rerank", reranked=[("f1", 0.1), ("f2", 0.05)])
    assert c["abstain"] and c["generator_input"] == []


def test_unknown_pipeline_and_missing_rerank():
    with pytest.raises(ValueError):
        ctx("config_9")
    with pytest.raises(ValueError):
        ctx("config_4_rerank", reranked=None)
