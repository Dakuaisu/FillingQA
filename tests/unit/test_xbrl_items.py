"""xbrl_numeric candidates: period wording, value format, items (real pool rows)."""

from __future__ import annotations

import json
from decimal import Decimal

import pytest
import yaml

from api.config import REPO_ROOT
from eval.generate.pool import sample
from eval.generate.schema import validate_item
from eval.generate.xbrl_items import (
    ItemError,
    build_items,
    format_value,
    period_info,
    spot_check_ids,
)
from tests.unit.test_pool import BY_KEY, POOL, TICKERS

TEMPLATES = yaml.safe_load((REPO_ROOT / "eval" / "templates.yaml").read_text(encoding="utf-8"))
LABELS = {
    i["id"]: i["label"]
    for i in yaml.safe_load((REPO_ROOT / "eval" / "concepts.yaml").read_text(encoding="utf-8"))[
        "line_items"
    ]
}
COST_TAX = ("0000909832", "us-gaap:IncomeTaxExpenseBenefit")
TGT_COGS = ("0000027419", "us-gaap:CostOfGoodsAndServicesSold")


def info(cik_concept, start, end):
    return period_info(BY_KEY[(*cik_concept, start, end)])


def test_period_wording_from_dates_and_own_filing_label():
    p = info(TGT_COGS, "2023-07-30", "2023-10-28")
    assert (p.kind, p.period, p.dates) == (
        "quarter", "the third quarter of fiscal 2023", "the three months ended October 28, 2023",
    )  # fmt: skip
    p = info(TGT_COGS, "2023-01-29", "2023-10-28")  # same 10-Q, year to date
    assert (p.kind, p.period, p.dates) == (
        "ytd", "the first three quarters of fiscal 2023", "the nine months ended October 28, 2023",
    )  # fmt: skip
    # TGT fiscal 2024 ends 2025-02-01: the label is the filing's dei label, not the date's year.
    p = info(TGT_COGS, "2024-02-04", "2025-02-01")
    assert (p.kind, p.period, p.filing) == ("annual", "fiscal 2024", "fiscal 2024 10-K")


def test_costco_weeks():
    assert (
        info(COST_TAX, "2023-09-04", "2023-11-26").dates == "the 12 weeks ended November 26, 2023"
    )
    p = info(COST_TAX, "2023-09-04", "2024-05-12")
    assert (p.kind, p.dates) == ("ytd", "the 36 weeks ended May 12, 2024")


def test_instant_wording():
    k = BY_KEY[("0000320193", "us-gaap:InventoryNet", None, "2024-09-28")]
    p = period_info(k)
    assert (p.kind, p.period, p.dates) == (
        "instant",
        "the end of fiscal 2024",
        "September 28, 2024",
    )
    k = BY_KEY[("0000320193", "us-gaap:InventoryNet", None, "2024-06-29")]
    assert period_info(k).period == "the end of the third quarter of fiscal 2024"


def test_format_value():
    assert format_value(Decimal("7286000000"), "USD", (6,)) == (
        "$7,286 million",
        "unit_scale_millions",
    )
    assert format_value(Decimal("-320000000"), "USD", (6,))[0] == "-$320 million"
    assert format_value(Decimal("3411738000000"), "USD", (6,))[0] == "$3,411,738 million"
    assert format_value(Decimal("201000000000"), "USD", (9,))[0] == "$201 billion"
    assert format_value(Decimal("1234500000"), "USD", (6,))[0] == "$1,234.5 million"
    assert format_value(Decimal("6.98"), "USD/shares", (0, None)) == ("$6.98", "unit_scale_none")
    assert format_value(Decimal("4.2"), "USD/shares", (0,))[0] == "$4.20"
    assert format_value(Decimal("-0.45"), "USD/shares", (0,))[0] == "-$0.45"


def test_format_value_reports_instead_of_picking():
    with pytest.raises(ItemError, match="scales"):
        format_value(Decimal("7286000000"), "USD", (3, 6))
    with pytest.raises(ItemError, match="scales"):
        format_value(Decimal("7286000000"), "USD", (None,))
    with pytest.raises(ItemError, match="unit"):
        format_value(Decimal("5"), "shares", (0,))


def make(seed=11):
    alloc = {t: 4 for t in TICKERS}
    draw = sample(POOL.eligible, seed, sum(alloc.values()), alloc)
    return build_items(draw, forms=TEMPLATES["forms"], labels=LABELS,
                       company_names=TEMPLATES["company_names"], seed=seed,
                       dataset_version="test")  # fmt: skip


def test_items_validate_and_are_byte_identical_per_seed():
    items, problems = make()
    assert problems == [] and len(items) == 4 * len(TICKERS)
    assert all(validate_item(i) == [] for i in items)
    dump = lambda xs: "".join(json.dumps(i) + "\n" for i in xs)  # noqa: E731
    assert dump(items) == dump(make()[0])
    assert dump(items) != dump(make(seed=12)[0])
    for i in items:
        assert (i["question_type"], i["source"], i["difficulty"]) == (
            "xbrl_numeric",
            "xbrl_auto",
            "easy",
        )
        assert i["reviewed_by_human"] is False
        assert sum(t.startswith("template:") for t in i["tags"]) == 1


def test_filing_scoped_form_takes_gold_from_that_filing_only():
    alloc = {t: 4 for t in TICKERS}
    draw = sample(POOL.eligible, 11, sum(alloc.values()), alloc)
    only_filing = {
        kind: [f for f in forms if f["scope"] == "filing"]
        for kind, forms in TEMPLATES["forms"].items()
    }
    items, _ = build_items(draw, forms=only_filing, labels=LABELS,
                           company_names=TEMPLATES["company_names"], seed=11,
                           dataset_version="test")  # fmt: skip
    for key, item in zip(draw, items, strict=True):
        assert item["gold_accessions"] == [key.own_accession]
        own = dict(key.evidence)[key.own_accession]
        assert item["gold_evidence_sets"] == [[c] for c in own]
        assert item["xbrl_fact_id"] == key.xbrl_fact_id


def test_reference_answer_matches_prd_example():
    k = BY_KEY[("0000320193", "us-gaap:InventoryNet", None, "2024-09-28")]
    items, _ = build_items([k], forms=TEMPLATES["forms"], labels=LABELS,
                           company_names=TEMPLATES["company_names"], seed=1,
                           dataset_version="test")  # fmt: skip
    assert items[0]["reference_answer"] == "$7,286 million as of September 28, 2024."


def test_spot_check_is_seeded():
    items, _ = make()
    assert spot_check_ids(items, 5, 4) == spot_check_ids(list(reversed(items)), 5, 4)
    assert len(spot_check_ids(items, 5, 4)) == 4
