"""companyfacts flattening and guards. No network, no database.

Every row is copied verbatim from AAPL's companyfacts (CIK 0000320193),
accession 0000320193-25-000079, the FY2025 10-K -- the same filing whose income
statement the table tests check: 416,161 printed in millions is 416161000000.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from api.config import ConfigError, sectors
from api.ingest.filings import sector_of
from api.ingest.xbrl_facts import conflicts, flatten, is_comparative

AAPL_10K = "0000320193-25-000079"

COMPANYFACTS = {
    "facts": {
        "us-gaap": {
            "RevenueFromContractWithCustomerExcludingAssessedTax": {
                "label": "Revenue from Contract with Customer, Excluding Assessed Tax",
                "units": {
                    "USD": [
                        {"start": "2024-09-29", "end": "2025-09-27", "val": 416161000000,
                         "accn": AAPL_10K, "fy": 2025, "fp": "FY", "form": "10-K",
                         "filed": "2025-10-31", "frame": "CY2025"},
                        {"start": "2022-09-25", "end": "2023-09-30", "val": 383285000000,
                         "accn": AAPL_10K, "fy": 2025, "fp": "FY", "form": "10-K",
                         "filed": "2025-10-31", "frame": "CY2023"},
                    ]
                },
            },
            "EarningsPerShareDiluted": {
                "label": "Earnings Per Share, Diluted",
                "units": {
                    "USD/shares": [
                        {"start": "2024-09-29", "end": "2025-09-27", "val": Decimal("7.46"),
                         "accn": AAPL_10K, "fy": 2025, "fp": "FY", "form": "10-K",
                         "filed": "2025-10-31", "frame": "CY2025"},
                    ]
                },
            },
            "InventoryNet": {
                "label": "Inventory, Net",
                "units": {
                    "USD": [
                        {"end": "2025-09-27", "val": 5718000000, "accn": AAPL_10K, "fy": 2025,
                         "fp": "FY", "form": "10-K", "filed": "2025-10-31"},
                    ]
                },
            },
        }
    }
}  # fmt: skip


@pytest.fixture
def facts():
    return {(f.concept, f.period_end): f for f in flatten(COMPANYFACTS, "0000320193")}


def test_values_stay_in_base_units(facts):
    revenue = facts[
        ("us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax", date(2025, 9, 27))
    ]
    assert revenue.value == Decimal("416161000000")  # never rescaled -- PRD 6.5.2 Trap 2
    assert revenue.unit == "USD"


def test_fractional_values_are_exact(facts):
    eps = facts[("us-gaap:EarningsPerShareDiluted", date(2025, 9, 27))]
    assert eps.value == Decimal("7.46")


def test_concept_carries_its_taxonomy_like_an_ix_name(facts):
    assert all(concept.startswith("us-gaap:") for concept, _ in facts)


def test_instant_facts_have_no_period_start(facts):
    assert facts[("us-gaap:InventoryNet", date(2025, 9, 27))].period_start is None


def test_every_fact_keeps_its_accession(facts):
    assert {f.accession for f in facts.values()} == {AAPL_10K}


def test_fy_is_the_reporting_filings_not_the_facts():
    # The FY2023 comparative in the FY2025 10-K carries fy 2025 (TRADEOFFS
    # finding #5) -- which is why the period, not fy, says what a fact describes.
    old = next(f for f in flatten(COMPANYFACTS, "0000320193") if f.period_end == date(2023, 9, 30))
    assert old.fiscal_year == 2025


def test_comparative_means_before_the_filings_own_period():
    filing_end = date(2025, 9, 27)
    assert is_comparative(date(2023, 9, 30), filing_end)
    assert not is_comparative(date(2025, 9, 27), filing_end)


def test_conflicts_finds_a_key_with_two_values():
    pairs = [("k1", Decimal(1)), ("k1", Decimal(1)), ("k2", Decimal(1)), ("k2", Decimal(2))]
    assert conflicts(pairs) == {"k2": {Decimal(1), Decimal(2)}}


def test_no_conflicts_in_real_rows():
    assert conflicts((f.key, f.value) for f in flatten(COMPANYFACTS, "0000320193")) == {}


def test_sectors_come_from_config():
    labels = sectors()
    assert labels["AAPL"] == "tech"
    assert labels["COST"] == labels["TGT"] == "retail"


def test_unknown_ticker_has_no_sector():
    with pytest.raises(ConfigError, match="ZZZZ"):
        sector_of("ZZZZ")
