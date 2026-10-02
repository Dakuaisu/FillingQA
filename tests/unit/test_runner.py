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


def test_partial_verdict_counts_as_answered():
    r = build_report(ITEMS, [{**RESULTS[0], "verdict": "PARTIAL"}], meta("claude_cli"), 10)
    assert r["columns"]["aggregate"]["abstention"]["partial_rate"] == 1.0


def test_results_are_appended_per_item_and_a_failed_call_halts(tmp_path):
    from api.generate.claude_cli import CliError
    from scripts.eval_run import read_jsonl, run_items

    results, errors = tmp_path / "r.jsonl", tmp_path / "e.jsonl"

    def answer(iid):
        if iid == "x3":
            raise CliError("claude CLI error (error_during_execution): 'usage limit'")
        return {"item_id": iid, "latency_s": 1.0}

    assert run_items(["x1", "x2", "x3", "x4"], answer, results, errors) == 1
    assert [r["item_id"] for r in read_jsonl(results)] == ["x1", "x2"]  # x3 unrecorded
    (err,) = read_jsonl(errors)
    assert err["item_id"] == "x3" and "usage limit" in err["error"] and err["at"]
    # Resume: only what is not recorded is answered again.
    done = {r["item_id"] for r in read_jsonl(results)}
    todo = [i for i in ["x1", "x2", "x3", "x4"] if i not in done]
    assert run_items(todo, lambda iid: {"item_id": iid, "latency_s": 1.0}, results, errors) == 0
    assert [r["item_id"] for r in read_jsonl(results)] == ["x1", "x2", "x3", "x4"]


def test_generation_metrics_print_na_without_claims_and_faithfulness_carries_answer_rate():
    out = format_report(build_report(ITEMS, RESULTS, meta("claude_cli"), 10))
    assert "n/a: no claims" in out
    claim = {"claim_id": "c1", "text": "t", "citations": ["b"], "figure": {"value": 7286},
             "checks": {"citation_valid": True, "numbers_grounded": True, "unit_ok": True,
                        "period_stated": True, "period_ok": True, "entity_ok": True,
                        "xbrl_contradiction": False, "entail": 0.0,
                        "citations_supporting": ["b"]}}  # fmt: skip
    with_claims = [{**RESULTS[0], "claims_pre": [claim], "claims_post": [claim]}]
    with pytest.raises(ValueError, match="nli_threshold"):
        build_report(ITEMS, with_claims, meta("claude_cli"), 10)
    out = format_report(build_report(ITEMS, with_claims, meta("claude_cli"), 10, 0.5))
    assert "1.000 [1.000]" in out


def test_floor_empties_are_counted_per_source_tagged_or_not():
    abst = {"verdict": "ABSTAIN", "answer": {"text": "", "claims": [], "abstained": True},
            "retrieved_post_rerank": []}  # fmt: skip
    floor = {**result("x1", ["a"], ""), **abst, "rerank_fell_back": False}
    tagged = {**result("s1", ["c"], ""), **abst, "abstain_reason": "score_floor"}
    fell_back = {
        **result("s2", ["d"], "x"),
        "retrieved_post_rerank": ["d"],
        "rerank_fell_back": True,
    }
    cols = build_report(ITEMS, [floor, tagged, fell_back], meta("claude_cli"), 10)["columns"]
    assert cols["xbrl_auto"]["floor_empties"] == 1 and cols["llm_seeded"]["floor_empties"] == 1
    assert cols["llm_seeded"]["rerank_fell_back"] == 1 and cols["aggregate"]["floor_empties"] == 2
    assert "floor_empties" in format_report(build_report(ITEMS, [floor], meta("claude_cli"), 10))


def test_routed_report_counts_filters_and_prints_the_intent_matrix():
    routed = [{**result("x1", ["a"], "$7,286 million"), "intent": "lookup", "filters": {"t": 1},
               "filter_zero_recall": True},
              {**result("s2", ["d"], ""), "intent": "unsupported", "abstain_reason": "unsupported",
               "verdict": "ABSTAIN", "answer": {"text": "", "claims": [], "abstained": True}},
              {**result("s1", ["c"], "44.1%"), "intent": "lookup", "filters": None}]  # fmt: skip
    m = {**meta("claude_cli"), "pipeline": "config_4_routed"}
    r = build_report(ITEMS, routed, m, 10)
    assert r["columns"]["xbrl_auto"]["filter_zero_recall"] == 1
    assert r["columns"]["llm_seeded"]["declined_unsupported"] == 1
    assert r["columns"]["aggregate"]["filtered"] == 1
    assert r["intent_matrix"]["llm_seeded"] == {"synthesis": {"unsupported": 1},
                                                "table": {"lookup": 1}}  # fmt: skip
    text = format_report(r)
    assert "F-118" in text and "F-110" in text and "router intent by question type" in text
    assert "F-118" not in format_report(build_report(ITEMS, RESULTS, meta("claude_cli"), 10))
