"""Pipeline lists per PRD 11.6 config (eval/pipeline.py). Synthetic ids and scores."""

from __future__ import annotations

import pytest

from eval.pipeline import (
    budget_for,
    context_for,
    depth_disagreements,
    depths,
    interleave,
    post_for_query,
    queries_for,
)

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
    for pl in ("config_1_dense", "config_3_hybrid", "config_4_rerank"):
        meta = {"pipeline": pl, **depths(pl, **kw)}
        for iid in ("x", "s"):
            c = context_for(pl, dense=dense, fused=fused,
                            reranked=[(x, 0.9) for x in fused], rerank_seconds=0.2,
                            rerank_cfg=cfg, question_type=QT[iid]["question_type"],
                            baseline_top_k=5)  # fmt: skip
            r = {"item_id": iid, **c}
            assert depth_disagreements(meta, [r], QT) == [], (pl, iid)


BUDGETS = {"lookup": {"tier": "tier_small", "k": 20, "top_n": 5, "sub_queries": 1},
           "comparison": {"tier": "tier_large", "k": 50, "top_n": 8, "sub_queries": 2},
           "synthesis": {"tier": "tier_large", "k": 50, "top_n": 10, "sub_queries": 1},
           "unrouted": {"tier": "tier_small", "k": 50, "top_n": 8, "sub_queries": 1}}  # fmt: skip


def test_budgets_follow_prd_7_1_intents():
    assert budget_for({"intent": "lookup"}, BUDGETS) == ("lookup", BUDGETS["lookup"])
    assert budget_for({"intent": "unsupported"}, BUDGETS) == ("unsupported", None)
    assert budget_for(None, BUDGETS) == ("unrouted", BUDGETS["unrouted"])
    cmp = BUDGETS["comparison"]
    assert queries_for("Q?", {"sub_queries": ["a FY24", "a FY23"]}, cmp) == ["a FY24", "a FY23"]
    assert queries_for("Q?", {"sub_queries": ["a FY24"]}, cmp) == ["a FY24", "Q?"]
    assert queries_for("Q?", {"sub_queries": ["x", "y"]}, BUDGETS["lookup"]) == ["Q?"]


def test_post_rerank_per_query_and_interleave():
    cfg = {"timeout_ms": 800, "score_floor": 0.3}
    ranked = [("b", 0.9), ("a", 0.5), ("c", 0.1)]
    assert post_for_query(["a", "b", "c"], ranked, 0.2, cfg, 5) == (["b", "a"], False)
    assert post_for_query(["a", "b", "c"], ranked, 0.9, cfg, 2) == (["a", "b"], True)
    assert interleave([["a", "b", "c"], ["x", "a", "y"]], 4) == ["a", "x", "b", "c"]
    assert interleave([[], []], 8) == []


def test_routed_meta_and_lists_agree_per_intent():
    meta = {"pipeline": "config_4_routed", **depths(
        "config_4_routed", retrieve_depth=10, retrieval_cfg=RC, rerank_cfg=RR, baseline_top_k=5,
        budgets=BUDGETS)}  # fmt: skip
    assert meta["retrieve_depth"]["comparison"] == 100 and meta["generator_top_k"]["lookup"] == 5
    ids = [f"c{i}" for i in range(100)]
    ok = [{"item_id": "x", "intent": "lookup", "retrieved": ids[:20], "generator_input": ids[:5]},
          {"item_id": "s", "intent": "comparison", "retrieved": ids, "generator_input": ids[:8]},
          {"item_id": "x", "intent": None, "retrieved": ids[:12], "generator_input": ids[:3]},
          {"item_id": "s", "intent": "unsupported", "retrieved": [],
           "generator_input": []}]  # fmt: skip
    assert depth_disagreements(meta, ok, QT) == []
    bad = [{"item_id": "x", "intent": "lookup", "retrieved": ids[:50], "generator_input": ids[:5]},
           {"item_id": "s", "intent": "synthesis", "retrieved": ids[:50],
            "generator_input": ids[:11]},
           {"item_id": "x", "intent": "unsupported", "retrieved": ids[:1],
            "generator_input": []}]  # fmt: skip
    assert depth_disagreements(meta, bad, QT) == ["x", "s", "x"]
