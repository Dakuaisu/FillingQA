"""The CI gate (PRD 11.5): thresholds read as they are, pending fails. Inline data."""

from __future__ import annotations

from eval.compare import format_table, passed, rows

TH = {"absolute_minimums": {"sufficiency_at_10": 0.82, "faithfulness_pre": 0.72},
      "by_source": {"handwritten": {"sufficiency_at_10": 0.72},
                    "xbrl_auto": {"sufficiency_at_10": 0.9}},
      "maximums": {"over_abstention_rate": 0.15},
      "regression_tolerance": {"sufficiency_at_10": -0.03, "cost_per_query": 0.2}}  # fmt: skip


def col(suff, faith=0.8, over=0.1):
    return {"sufficiency@10": suff, "generation": {"status": "ok", "faithfulness_pre": faith},
            "abstention": {"over_abstention_rate": over}}  # fmt: skip


def report(agg=0.9, hand=0.8, xbrl=0.95, subset="s1", dev=False):
    cols = {"aggregate": col(agg), "handwritten": col(hand), "xbrl_auto": col(xbrl)}
    return {"columns": cols, "subset": {"sha256": subset}, "development_run": dev,
            "backend": "anthropic_api"}  # fmt: skip


def status(table, metric, scope, rule=None):
    return next(r["status"] for r in table if r["metric"] == metric and r["scope"] == scope
                and (rule is None or r["rule"].startswith(rule)))  # fmt: skip


TH_NO_COST = {**TH, "regression_tolerance": {"sufficiency_at_10": -0.03}}


def test_a_report_meeting_every_threshold_passes():
    t = rows(report(), TH_NO_COST, report(agg=0.91))
    assert passed(t), format_table(t)


def test_minimums_maximums_by_source_and_the_handwritten_override():
    t = rows(report(agg=0.81, hand=0.73, xbrl=0.89), TH_NO_COST, report())
    assert status(t, "sufficiency_at_10", "aggregate", "min") == "fail"
    assert status(t, "sufficiency_at_10", "handwritten", "min") == "pass"  # 0.72 override, not 0.82
    assert status(t, "sufficiency_at_10", "xbrl_auto") == "fail"
    r = report()
    r["columns"]["aggregate"]["abstention"]["over_abstention_rate"] = 0.2
    assert status(rows(r, TH_NO_COST, report()), "over_abstention_rate", "aggregate") == "fail"


def test_regression_needs_a_same_subset_baseline():
    t = rows(report(agg=0.86), TH_NO_COST, report(agg=0.90))
    assert status(t, "sufficiency_at_10", "aggregate", "delta") == "fail"  # -0.04 < -0.03
    t = rows(report(), TH_NO_COST, report(subset="other"))
    row = next(r for r in t if r["rule"].startswith("delta"))
    assert row["status"] == "fail" and "same subset" in row["why"]
    assert (
        status(rows(report(), TH_NO_COST, None), "sufficiency_at_10", "aggregate", "delta")
        == "pending"
    )


def test_pending_unmeasured_and_empty_slices_fail_the_gate():
    r = report()
    r["columns"]["aggregate"]["generation"] = {"status": "pending NLI threshold (F-125)"}
    r["columns"]["handwritten"] = None
    t = rows(r, TH, report())
    assert status(t, "faithfulness_pre", "aggregate") == "pending"
    assert status(t, "sufficiency_at_10", "handwritten", "min") == "pending"
    assert status(t, "cost_per_query", "aggregate") == "pending"
    assert not passed(t)
    assert "GATE FAILED" in format_table(t, markdown=True)


def test_a_development_run_never_passes():
    t = rows(report(dev=True), TH_NO_COST, report())
    assert not passed(t) and status(t, "backend", "run") == "fail"


def test_ci_backend_override(monkeypatch):
    import pytest

    from api.config import ConfigError, generation

    monkeypatch.setenv("FILINGQA_GENERATION_BACKEND", "anthropic_api")
    assert generation()["backend"] == "anthropic_api"
    monkeypatch.setenv("FILINGQA_GENERATION_BACKEND", "openai")
    with pytest.raises(ConfigError):
        generation()


def test_without_a_gated_run_every_row_is_pending_for_that_reason():
    t = rows(None, TH, None)
    assert not passed(t) and {r["status"] for r in t} == {"pending"}
    assert all(r["why"].startswith("pending:") for r in t)
    assert next(r for r in t if r["metric"] == "faithfulness_pre")["why"] == (
        "pending: no gated run exists (F-59)"
    )
