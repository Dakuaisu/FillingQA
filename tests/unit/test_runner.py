"""Eval report shape (PRD 11.2, 11.4). Synthetic items and results, no retrieval."""

from __future__ import annotations

import pytest

from eval.runner import DEV_BANNER, build_report, format_report

ITEMS = {
    "x1": {"item_id": "x1", "source": "xbrl_auto", "question_type": "xbrl_numeric",
           "reference_answer": "$7,286 million as of September 28, 2024.", "tags": [],
           "gold_evidence_sets": [["a"], ["b"]], "expected_abstain": False},
    "s1": {"item_id": "s1", "source": "llm_seeded", "question_type": "table",
           "reference_answer": "44.1%", "tags": ["kind:factual", "unit_scale_unknown"],
           "gold_evidence_sets": [["c"]], "expected_abstain": False},
    "s2": {"item_id": "s2", "source": "llm_seeded", "question_type": "synthesis",
           "reference_answer": "It expects supply to recover.", "tags": ["kind:interpretive"],
           "gold_evidence_sets": [["d"]], "expected_abstain": False},
}  # fmt: skip


def result(iid, retrieved, text, model="claude-haiku-4-5-20251001"):
    return {"item_id": iid, "retrieved": retrieved, "retrieved_post_rerank": None,
            "answer": {"text": text, "claims": [], "abstained": False}, "verdict": "PASS",
            "model_served": model}  # fmt: skip


RESULTS = [result("x1", ["z", "b"], "$7,286 million"), result("s1", ["c"], "44.1%"),
           result("s2", ["q"], "Supply recovers.")]  # fmt: skip


def meta(backend):
    return {"run_id": "r1", "backend": backend, "model_requested": "m",
            "retrieval_stage": "dense top-k"}  # fmt: skip


def test_report_breaks_out_by_source_and_aggregates():
    r = build_report(ITEMS, RESULTS, meta("claude_cli"), 10)
    assert r["development_run"] and r["served_models"] == {"claude-haiku-4-5-20251001": 3}
    cols = r["columns"]
    assert cols["handwritten"] is None
    assert cols["xbrl_auto"]["sufficiency@10"] == 1.0
    assert cols["xbrl_auto"]["ndcg@10"] == pytest.approx(1 / 1.5849625007211563)
    assert cols["llm_seeded"]["sufficiency@10"] == 0.5
    assert cols["llm_seeded"]["numeric"]["excluded"] == {"unit_scale_unknown": 1, "not numeric": 1}
    assert cols["aggregate"]["numeric"]["numeric_accuracy"] == 1.0
    assert cols["aggregate"]["numeric"]["n"] == 1


def test_every_report_is_stamped_and_dev_runs_carry_the_banner():
    dev = format_report(build_report(ITEMS, RESULTS, meta("claude_cli"), 10))
    api = format_report(build_report(ITEMS, RESULTS, meta("anthropic_api"), 10))
    assert "backend: claude_cli" in dev and DEV_BANNER in dev
    assert "backend: anthropic_api" in api and DEV_BANNER not in api
    assert "excluded unit_scale_unknown" in dev and "served models" in dev


def test_partial_verdict_is_refused_until_placed():
    bad = [{**RESULTS[0], "verdict": "PARTIAL"}]
    with pytest.raises(NotImplementedError, match="F-21"):
        build_report(ITEMS, bad, meta("claude_cli"), 10)
