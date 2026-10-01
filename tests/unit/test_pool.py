"""xbrl_auto pool and sampler (F-75), on real pool rows.

tests/fixtures/xbrl_pool_rows.json is written by
`python -m scripts.xbrl_pool --write-fixture` from the frozen corpus.
"""

from __future__ import annotations

import json
from collections import Counter
from decimal import Decimal
from pathlib import Path

import pytest

from eval.generate.pool import ELIGIBLE, Shortfall, build_pool, sample

ROWS_FILE = Path(__file__).resolve().parent.parent / "fixtures" / "xbrl_pool_rows.json"


def load_rows() -> list[dict]:
    rows = json.loads(ROWS_FILE.read_text(encoding="utf-8"))["rows"]
    for r in rows:
        r["value"] = Decimal(r["value"])
        r["period"] = tuple(r["period"])
    return rows


ROWS = load_rows()
POOL = build_pool(ROWS)
BY_KEY = {k.key: k for k in POOL.eligible}
TICKERS = sorted({k.ticker for k in POOL.eligible})


def category_of(cik, concept, start, end) -> set[str]:
    return {
        POOL.category[r["fact_id"]]
        for r in ROWS
        if (r["cik"], r["concept"], *r["period"]) == (cik, concept, start, end)
    }


def test_every_fact_lands_in_exactly_one_category():
    assert len(POOL.category) == len(ROWS)
    assert set(POOL.category) == {r["fact_id"] for r in ROWS}
    assert set(POOL.category.values()) == {
        "eligible", "value_differs", "mixed_key", "gt3", "comparative_only",
    }  # fmt: skip
    eligible_facts = sum(1 for c in POOL.category.values() if c == ELIGIBLE)
    keys_of_eligible = {
        (r["cik"], r["concept"], *r["period"])
        for r in ROWS
        if POOL.category[r["fact_id"]] == ELIGIBLE
    }
    assert eligible_facts >= len(keys_of_eligible) == len(POOL.eligible)


def test_eligible_key_gold_spans_every_accession_label_from_own_filing():
    # AAPL inventory at FY2024 year end, PRD 11.1's example item: own filing
    # 0000320193-24-000123 (10-K, FY2024); four later filings carry it as a comparative.
    k = BY_KEY[("0000320193", "us-gaap:InventoryNet", None, "2024-09-28")]
    assert k.value == Decimal("7286000000")
    assert (k.own_accession, k.own_form, k.xbrl_fact_id) == ("0000320193-24-000123", "10-K", 42179)
    assert (k.fiscal_year, k.fiscal_quarter) == (2024, None)  # not a comparative row's 2025
    assert len(k.gold_accessions) == 5
    assert ["0000320193-24-000123:416.0:416.0"] in k.gold_evidence_sets
    assert ["0000320193-25-000079:402.0:402.0"] in k.gold_evidence_sets
    assert all(len(s) == 1 for s in k.gold_evidence_sets)
    assert len(k.gold_evidence_sets) == 8  # 1 + 1 + 2 + 2 + 2 chunks across the five


def test_value_differs_goes_to_review():
    # TGT FY2023 cost of sales: 77,736M as filed, 77,828M in the two later 10-Ks.
    assert category_of("0000027419", "us-gaap:CostOfGoodsAndServicesSold",
                       "2023-01-29", "2024-02-03") == {"value_differs"}  # fmt: skip


def test_mixed_and_gt3_and_comparative_only_are_not_eligible():
    # BAC total assets at 2022-12-31: 1-3 in a 10-Q, >3 in the 10-K.
    assert category_of("0000070858", "us-gaap:Assets", None, "2022-12-31") == {"mixed_key"}
    assert category_of("0000019617", "us-gaap:NetIncomeLoss", "2022-01-01", "2022-09-30") == {"gt3"}
    # TGT FY2021 cost of sales appears only as a comparative in the FY2023 10-K.
    assert category_of("0000027419", "us-gaap:CostOfGoodsAndServicesSold",
                       "2021-01-31", "2022-01-29") == {"comparative_only"}  # fmt: skip
    assert not any(k.key[1] == "us-gaap:NetIncomeLoss" and k.ticker == "JPM" for k in POOL.eligible)


def test_same_seed_same_draw_and_other_seed_differs():
    alloc = {t: 3 for t in TICKERS}
    a = sample(POOL.eligible, 7, sum(alloc.values()), alloc)
    b = sample(list(reversed(POOL.eligible)), 7, sum(alloc.values()), alloc)
    c = sample(POOL.eligible, 8, sum(alloc.values()), alloc)
    assert [k.key for k in a] == [k.key for k in b]
    assert [k.key for k in a] != [k.key for k in c]


def test_allocation_round_robin_and_no_duplicates():
    alloc = {t: 4 for t in TICKERS}
    draw = sample(POOL.eligible, 1, sum(alloc.values()), alloc)
    assert Counter(k.ticker for k in draw) == Counter(alloc)
    assert len({k.key for k in draw}) == len(draw)
    for t in TICKERS:
        strata = Counter(k.stratum for k in draw if k.ticker == t)
        available = {k.stratum for k in POOL.eligible if k.ticker == t}
        # round-robin: no stratum gets a second key while another available one has none
        if len(available) >= alloc[t]:
            assert max(strata.values()) == 1


def test_shortfall_is_reported_not_backfilled():
    have = Counter(k.ticker for k in POOL.eligible)
    alloc = {t: 1 for t in TICKERS}
    alloc["BAC"] = have["BAC"] + 1
    with pytest.raises(Shortfall) as e:
        sample(POOL.eligible, 1, sum(alloc.values()), alloc)
    assert e.value.short == {"BAC": (have["BAC"], have["BAC"] + 1)}


def test_allocation_must_sum_to_total():
    with pytest.raises(ValueError):
        sample(POOL.eligible, 1, 10, {t: 1 for t in TICKERS})
