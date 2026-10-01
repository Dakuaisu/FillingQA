"""xbrl_auto comparison pairs and items (F-83, TRADEOFFS), on real pool rows."""

from __future__ import annotations

import dataclasses
import json
import re
from collections import Counter
from decimal import Decimal

import pytest

from eval.generate.comparison import (
    build_comparison_items,
    build_pairs,
    difference,
    eligible_pairs,
    evidence,
    reference_answer,
    shares_chunk,
)
from eval.generate.pool import Shortfall, sample
from eval.generate.schema import validate_item
from eval.generate.xbrl_items import ItemError
from tests.unit.test_pool import POOL
from tests.unit.test_xbrl_items import LABELS, TEMPLATES

PAIRS = build_pairs(POOL.eligible, [1, 2])


def pair(ticker, line_item, kind, gap, later_end):
    return next(
        p for p in PAIRS
        if (p.ticker, p.line_item, p.kind, p.gap, p.later.period_end)
        == (ticker, line_item, kind, gap, later_end)
    )  # fmt: skip


def test_shared_chunk_pair_is_rejected():
    # AAPL inventory, FY2023 to FY2024 year end (the shape of PRD 7.1's example):
    # the FY2024 10-K balance sheet prints both, so one chunk is sufficient.
    p = pair("AAPL", "inventory", "instant", 1, "2024-09-28")
    assert p.earlier.period_end == "2023-09-30" and shares_chunk(p)
    assert p not in eligible_pairs(PAIRS, set())
    with pytest.raises(ValueError, match="share a chunk"):
        evidence(p)


def test_two_years_apart_pair_is_accepted_with_every_combination():
    # TGT cost of sales, Q3 FY2023 vs Q3 FY2025: no 10-Q prints both quarters.
    p = pair("TGT", "cost_of_revenue", "quarter", 2, "2025-11-01")
    assert p.earlier.period_end == "2023-10-28" and not shares_chunk(p)
    assert p in eligible_pairs(PAIRS, set())
    sets, accessions = evidence(p)
    a = {c for _, cs in p.earlier.evidence for c in cs}
    b = {c for _, cs in p.later.evidence for c in cs}
    assert len(sets) == len(a) * len(b) and all(len(s) == 2 for s in sets)
    assert {frozenset(s) for s in sets} == {frozenset((x, y)) for x in a for y in b}
    assert set(accessions) == {acc for k in (p.earlier, p.later) for acc, _ in k.evidence}
    assert reference_answer(p)[0] == (
        "$18,137 million for the third quarter of fiscal 2025, compared with "
        "$18,149 million for the third quarter of fiscal 2023: a decrease of $12 million."
    )


def test_excluded_keys_drop_the_pair():
    p = pair("TGT", "cost_of_revenue", "quarter", 2, "2025-11-01")
    assert p not in eligible_pairs(PAIRS, {p.earlier.key})


def test_difference_on_negative_zero_and_sign_flip_pairs():
    neg = pair("PFE", "income_tax", "quarter", 2, "2025-09-28")  # -964 -> -216
    assert difference(neg) == Decimal("748000000")
    assert reference_answer(neg)[0].endswith(": an increase of $748 million.")
    assert reference_answer(neg)[0].startswith("-$216 million for the third quarter")
    zero = pair("TGT", "share_repurchases", "ytd", 2, "2025-11-01")  # 0 -> 408
    assert reference_answer(zero)[0] == (
        "$408 million for the first three quarters of fiscal 2025, compared with "
        "$0 million for the first three quarters of fiscal 2023: an increase of $408 million."
    )
    up = pair("PFE", "eps_diluted", "quarter", 2, "2025-09-28")  # -0.42 -> 0.62
    assert reference_answer(up)[0].endswith(": an increase of $1.04.")
    down = pair("PFE", "eps_diluted", "quarter", 2, "2026-06-28")  # 0.01 -> -0.04
    assert difference(down) == Decimal("-0.05")
    assert reference_answer(down)[0].endswith(": a decrease of $0.05.")


def test_equal_values_give_a_numeric_zero_difference():
    # No equal-value pair exists in the pool (comparison_supply); a real pair with
    # the earlier value set equal to the later one.
    p = pair("TGT", "cost_of_revenue", "quarter", 2, "2025-11-01")
    p = dataclasses.replace(p, earlier=dataclasses.replace(p.earlier, value=p.later.value))
    assert reference_answer(p)[0].endswith(": a difference of $0 million.")


def test_sides_at_different_scales_are_reported():
    # Real pair (comparison_supply): NVDA income tax, first half of fiscal 2025 vs
    # 2027. The later 10-Q prints the figure as "23,400" (scale 6) and "23.4"
    # (scale 9), F-80; the earlier side prints at scale 6 only.
    p = pair("NVDA", "income_tax", "ytd", 2, "2026-07-26")
    assert (p.earlier.period_end, p.earlier.own_scales, p.later.own_scales) == (
        "2024-07-28", (6,), (6, 9),
    )  # fmt: skip
    assert p in eligible_pairs(PAIRS, set())
    with pytest.raises(ItemError, match="scales"):
        reference_answer(p)


def draw(seed=3, n=1, exclude=frozenset()):
    pool = eligible_pairs(PAIRS, set(exclude))
    have = Counter(p.ticker for p in pool)
    tickers = sorted(t for t in have if have[t] >= 3 * n)
    alloc = {t: n for t in tickers}
    return sample(pool, seed, sum(alloc.values()), alloc), alloc


def test_sampler_is_seeded_and_never_reuses_a_key():
    d, alloc = draw()
    assert [p.sort_key for p in d] == [p.sort_key for p in draw()[0]]
    assert Counter(p.ticker for p in d) == Counter(alloc)
    keys = [k for p in d for k in p.members]
    assert len(keys) == len(set(keys))
    big, _ = draw(n=2)
    keys = [k for p in big for k in p.members]
    assert len(keys) == len(set(keys))


def test_sampler_short_when_conflicts_exhaust_a_ticker():
    pool = eligible_pairs(PAIRS, set())
    tgt = [p for p in pool if p.ticker == "TGT"]
    distinct = len({k for p in tgt for k in p.members})
    with pytest.raises(Shortfall):
        sample(tgt, 1, distinct, {"TGT": distinct})  # more pairs than disjoint pairs exist


def test_items_validate_carry_kind_and_gap_and_are_byte_identical():
    d, _ = draw()
    build = lambda: build_comparison_items(  # noqa: E731
        d, forms=TEMPLATES["comparison_forms"], labels=LABELS,
        company_names=TEMPLATES["company_names"], seed=3, dataset_version="test",
    )  # fmt: skip
    items, problems = build()
    assert problems == [] and len(items) == len(d)
    assert all(validate_item(i) == [] for i in items)
    assert json.dumps(items) == json.dumps(build()[0])
    for p, i in zip(d, items, strict=True):
        assert (i["question_type"], i["source"], i["difficulty"]) == (
            "comparison",
            "xbrl_auto",
            "medium",
        )
        assert i["xbrl_fact_id"] == p.later.xbrl_fact_id and i["reviewed_by_human"] is False
        assert p.kind in i["tags"] and f"gap{p.gap}" in i["tags"]


def test_no_form_words_a_direction():
    words = re.compile(r"\b(increase|decrease|grow|grew|rise|rose|fall|fell|decline|drop)", re.I)
    for forms in TEMPLATES["comparison_forms"].values():
        assert len(forms) in range(4, 7)
        for f in forms:
            assert not words.search(f["text"]), f["id"]
