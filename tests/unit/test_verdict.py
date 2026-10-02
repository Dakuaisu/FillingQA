"""PRD 7.5 verdict aggregation and the gate's entity targets. Inline data."""

from __future__ import annotations

from api.verify.gate import targets_in
from api.verify.verdict import ABSTAIN, PARTIAL, PASS, supported, verdict

OK = {"citation_valid": True, "entity_ok": True, "numbers_grounded": True, "unit_ok": True,
      "period_stated": True, "xbrl_contradiction": False, "entail": None}  # fmt: skip
FIG = {"value": 1, "unit": "millions"}


def fig(**bad):
    return {"claim_id": "c", "figure": FIG, "checks": {**OK, **bad}}


def prose(entail):
    return {"claim_id": "p", "figure": None, "checks": {**OK, "entail": entail}}


def test_supported_routes_by_claim_type_and_requires_citation_validity():
    assert supported(fig(), 0.5) and not supported(fig(numbers_grounded=False), 0.5)
    assert not supported(fig(citation_valid=False), 0.5)  # F-10
    assert not supported(fig(xbrl_contradiction=True), 0.5)
    assert supported(prose(0.8), 0.5) and not supported(prose(0.2), 0.5)


def test_verdict_thresholds_and_the_contradiction_hard_stop():
    assert verdict([], 0.5) == (ABSTAIN, [])
    assert verdict([fig()] * 10, 0.5)[0] == PASS
    assert verdict([fig()] * 9 + [fig(unit_ok=False)], 0.5)[0] == PASS
    assert verdict([fig()] * 7 + [fig(unit_ok=False)] * 3, 0.5)[0] == PARTIAL
    assert verdict([fig()] * 5 + [fig(unit_ok=False)] * 5, 0.5)[0] == ABSTAIN
    v, post = verdict([fig()] * 9 + [fig(xbrl_contradiction=True)], 0.5)
    assert v == ABSTAIN and len(post) == 9


def test_verdict_is_pending_while_a_prose_claim_has_no_threshold():
    assert verdict([fig(), prose(0.9)], None) == (None, None)
    assert verdict([fig()], None)[0] == PASS


def test_entity_targets_come_from_the_question_text():
    names = {"AAPL": ["Apple", "Apple Inc."], "TGT": ["Target"], "JPM": ["JPMorgan Chase"]}
    assert targets_in("What did Apple report for FY2024?", names) == {"AAPL"}
    assert targets_in("Compare JPM and Target revenue.", names) == {"JPM", "TGT"}
    assert targets_in("What is a pineapple?", names) == set()
