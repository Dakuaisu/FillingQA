"""Runtime XBRL validation (PRD 6.5.4): cited filing, period end, restatement. Inline data."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from api.config import REPO_ROOT, verification
from api.verify.xbrl_check import (
    claim_kind,
    classify,
    concept_tags,
    load_concepts,
    of_kind,
    period_ends_for,
)

FILINGS = [("AAPL", date(2023, 9, 30), 2023, None), ("AAPL", date(2024, 9, 28), 2024, None),
           ("AAPL", date(2024, 6, 29), 2024, 3),
           ("NVDA", date(2026, 1, 25), 2026, None)]  # fmt: skip
K23, K24 = "0000320193-23-000106", "0000320193-24-000123"
FACTS = [(K23, date(2023, 9, 30), Decimal("6331000000")),
         (K24, date(2023, 9, 30), Decimal("6400000000")),  # restated in the FY2024 10-K
         (K24, date(2024, 9, 28), Decimal("7286000000"))]  # fmt: skip
M = Decimal(10) ** 6


def test_concepts_resolve_through_the_hand_written_map_only():
    cfg = verification()
    phrases = load_concepts(
        REPO_ROOT / "eval" / "concepts.yaml", REPO_ROOT / cfg["concept_synonyms"]
    )
    assert concept_tags("Inventories", phrases) == ["us-gaap:InventoryNet"]
    assert concept_tags("Total net sales", phrases)[0] == "us-gaap:Revenues"
    assert concept_tags("Net income", phrases) == ["us-gaap:NetIncomeLoss"]
    assert concept_tags("Difference in net income", phrases) == []


def test_period_text_to_period_end():
    assert period_ends_for("September 28, 2024", "AAPL", FILINGS) == [date(2024, 9, 28)]
    assert period_ends_for("FY2024", "AAPL", FILINGS) == [date(2024, 9, 28)]
    assert period_ends_for("Q3 FY2024", "AAPL", FILINGS) == [date(2024, 6, 29)]
    assert period_ends_for("Q4 FY2024", "AAPL", FILINGS) == [date(2024, 9, 28)]
    assert period_ends_for("FY2026", "NVDA", FILINGS) == [date(2026, 1, 25)]
    assert period_ends_for("last year", "AAPL", FILINGS) == []


def test_verified_restatement_contradiction_and_no_fact():
    fy24 = [date(2024, 9, 28)]
    assert classify(7286 * M, {K24}, fy24, FACTS, 0.5)["status"] == "verified"
    assert classify(7300 * M, {K24}, fy24, FACTS, 0.5)["status"] == "verified"  # within 0.5%
    # The FY2023 10-K's original figure, cited from that filing: verified, not a contradiction.
    assert classify(6331 * M, {K23}, [date(2023, 9, 30)], FACTS, 0.5)["status"] == "verified"
    # Cited from the FY2024 10-K, which restated it: the original matches another filing.
    r = classify(6331 * M, {K24}, [date(2023, 9, 30)], FACTS, 0.5)
    assert r["status"] == "restatement" and r["accession"] == K23 and r["period_ok"]
    r = classify(7500 * M, {K24}, fy24, FACTS, 0.5)
    assert r["status"] == "contradiction" and r["period_ok"] is None
    # The right number for the wrong period.
    r = classify(7286 * M, {K24}, [date(2023, 9, 30)], FACTS, 0.5)
    assert r["status"] == "contradiction" and r["period_ok"] is False
    assert classify(7286 * M, {"other"}, fy24, FACTS, 0.5)["status"] == "no_fact"
    # Sign is not compared (F-87).
    assert classify(-7286 * M, {K24}, fy24, FACTS, 0.5)["status"] == "verified"


def test_unit_kind_must_match_before_a_contradiction_is_possible():
    usd = {"value": 46.2, "unit": "percent", "currency": None, "concept": "Gross margin"}
    assert claim_kind(usd, "Gross margin was 46.2% in fiscal 2024.") is None
    eps = {"value": 6.11, "unit": "ones", "currency": "USD", "concept": "Diluted EPS"}
    assert claim_kind(eps, "Diluted EPS was $6.11.") == "per_share"
    rev = {"value": 391035, "unit": "millions", "currency": "USD", "concept": "Revenue"}
    assert claim_kind(rev, "Revenue was $391,035 million.") == "monetary"
    shares = {"value": 15, "unit": "billions", "currency": None, "concept": "Shares outstanding"}
    assert claim_kind(shares, "15 billion shares.") == "shares"
    facts = [(K24, date(2024, 9, 28), Decimal("7286000000"), "USD"),
             (K24, date(2024, 9, 28), Decimal("6.11"), "USD/shares")]  # fmt: skip
    assert of_kind(facts, "per_share") == [(K24, date(2024, 9, 28), Decimal("6.11"))]
    # A per-share claim never meets the dollar fact: no fact, not a contradiction.
    assert classify(Decimal("7.0"), {K24}, [date(2024, 9, 28)], of_kind(facts[:1], "per_share"),
                    0.5)["status"] == "no_fact"  # fmt: skip
