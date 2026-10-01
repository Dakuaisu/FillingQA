"""Claim-level generation metrics (PRD 11.2, 7.5; F-10, F-09). Inline claims."""

from __future__ import annotations

import pytest

from eval.metrics.generation import NA, generation_metrics, supported

OK = {"citation_valid": True, "numbers_grounded": True, "unit_ok": True, "period_stated": True,
      "period_ok": True, "entity_ok": True, "xbrl_contradiction": False, "entail": 0.0}  # fmt: skip


def fig(cid, cites=("a",), supporting=("a",), **checks):
    return {"claim_id": cid, "text": "Inventories were $7,286 million.", "citations": list(cites),
            "figure": {"value": 7286, "unit": "millions"},
            "checks": {**OK, "citations_supporting": list(supporting), **checks}}  # fmt: skip


def prose(cid, entail, cites=("a",), supporting=("a",), **checks):
    checks = {**OK, "entail": entail, "citations_supporting": list(supporting), **checks}
    return {"claim_id": cid, "text": "Demand rose.", "citations": list(cites), "checks": checks}


def test_supported_requires_citation_validity_for_figure_claims_f10():
    assert supported(fig("c1"), 0.5)
    assert not supported(fig("c1", citation_valid=False), 0.5)  # F-10
    assert not supported(fig("c1", numbers_grounded=False), 0.5)
    assert not supported(fig("c1", xbrl_contradiction=True), 0.5)
    assert supported(prose("c2", 0.8), 0.5) and not supported(prose("c2", 0.3), 0.5)
    assert not supported(prose("c2", 0.9, citation_valid=False), 0.5)
    with pytest.raises(ValueError, match="numbers_grounded"):
        supported({"claim_id": "x", "figure": {"value": 1}, "checks": {"citation_valid": True,
                   "entity_ok": True}}, 0.5)  # fmt: skip


def test_no_claims_prints_na():
    results = [{"answer": {"abstained": False}, "claims_pre": [], "claims_post": []},
               {"answer": {"text": "x"}}]  # fmt: skip
    assert generation_metrics(results, 0.5) == {"status": NA}


def test_faithfulness_pre_over_answered_items_with_answer_rate_f09():
    results = [
        {"answer": {"abstained": False},
         "claims_pre": [fig("c1"), fig("c2", numbers_grounded=False)], "claims_post": [fig("c1")]},
        {"answer": {"abstained": False},
         "claims_pre": [prose("c3", 0.9), prose("c4", 0.1, citations_supporting=[])],
         "claims_post": [prose("c3", 0.9)]},
        # An abstained item's claims never enter the faithfulness denominators.
        {"answer": {"abstained": True}, "claims_pre": [fig("c5", unit_ok=False)],
         "claims_post": []},
    ]  # fmt: skip
    m = generation_metrics(results, 0.5)
    assert m["answer_rate"] == pytest.approx(2 / 3)
    assert m["faithfulness_pre"] == pytest.approx(2 / 4)
    assert m["faithfulness_post"] == 1.0
    assert m["verifier_lift"] == pytest.approx(0.5)
    assert m["claim_retention"] == pytest.approx(2 / 4)
    assert m["citation_coverage"] == 1.0
    assert m["citation_precision"] == pytest.approx(3 / 4)
    assert m["unit_scale_accuracy"] == 1.0  # the abstained item's unit error is not counted
    assert m["claims_pre"] == 4


def test_unit_period_and_xbrl_rates_are_over_figure_claims():
    results = [{"answer": {"abstained": False}, "claims_post": [],
                "claims_pre": [fig("c1", unit_ok=False), fig("c2", period_ok=False),
                               fig("c3", xbrl_contradiction=True), prose("c4", 0.9)]}]  # fmt: skip
    m = generation_metrics(results, 0.5)
    assert m["unit_scale_accuracy"] == pytest.approx(2 / 3)
    assert m["period_accuracy"] == pytest.approx(2 / 3)
    assert m["xbrl_contradiction_rate"] == pytest.approx(1 / 3)
    assert m["citation_coverage"] == 1.0 and m["faithfulness_post"] is None
