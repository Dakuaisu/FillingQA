"""Pipeline lists per PRD 11.6 config (eval/pipeline.py). Synthetic ids and scores."""

from __future__ import annotations

import pytest

from eval.pipeline import PIPELINES, context_for, depth_disagreements, depths

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


RC = {"k_dense": 50, "k_sparse": 50}
RR = {"top_n": 8, "top_n_synthesis": 10}
QT = {"x": {"question_type": "xbrl_numeric"}, "s": {"question_type": "synthesis"}}


def test_depths_follow_the_pipeline_config():
    kw = {"retrieve_depth": 10, "retrieval_cfg": RC, "rerank_cfg": RR, "baseline_top_k": 5}
    assert depths("config_1_dense", **kw) == {"retrieve_depth": 10, "generator_top_k": 5}
    want = {"retrieve_depth": 50, "generator_top_k": {"default": 8, "synthesis": 10}}
    assert depths("config_3_hybrid", **kw) == want == depths("config_4_rerank", **kw)
    with pytest.raises(ValueError):
        depths("config_2", **kw)


def test_meta_and_stored_lists_agree_only_when_the_meta_is_true():
    meta = {
        "pipeline": "config_4_rerank",
        **depths(
            "config_4_rerank", retrieve_depth=10, retrieval_cfg=RC, rerank_cfg=RR, baseline_top_k=5
        ),
    }
    fused = [f"c{i}" for i in range(50)]
    ok = [
        {"item_id": "x", "retrieved": fused, "generator_input": fused[:8]},
        {"item_id": "s", "retrieved": fused, "generator_input": fused[:3]},
    ]  # floor shortened
    assert depth_disagreements(meta, ok, QT) == []
    stale = {"pipeline": "config_4_rerank", "retrieve_depth": 10, "generator_top_k": 5}
    assert depth_disagreements(stale, ok, QT) == ["x", "s"]
    fell = [{"item_id": "x", "retrieved": fused, "generator_input": fused[:3],
             "rerank_fell_back": True}]  # fmt: skip
    assert depth_disagreements(meta, fell, QT) == ["x"]


def test_answer_one_lists_match_depths_for_every_pipeline():
    kw = {"retrieve_depth": 10, "retrieval_cfg": RC, "rerank_cfg": RR, "baseline_top_k": 5}
    dense, fused = [f"d{i}" for i in range(10)], [f"c{i}" for i in range(50)]
    cfg = {**RR, "timeout_ms": 800, "score_floor": 0.3}
    for pl in PIPELINES:
        meta = {"pipeline": pl, **depths(pl, **kw)}
        for iid in ("x", "s"):
            c = context_for(pl, dense=dense, fused=fused,
                            reranked=[(x, 0.9) for x in fused], rerank_seconds=0.2,
                            rerank_cfg=cfg, question_type=QT[iid]["question_type"],
                            baseline_top_k=5)  # fmt: skip
            r = {"item_id": iid, **c}
            assert depth_disagreements(meta, [r], QT) == [], (pl, iid)
