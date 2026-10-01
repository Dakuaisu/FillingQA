"""xbrl_numeric candidate items from drawn pool keys. Pure.

Question wording comes from eval/templates.yaml; the period label from the
own-period filing's dei labels (F-75); the value at the scale that filing
prints. Nothing here reads the database.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from eval.generate.pool import PoolKey, evidence_for
from eval.generate.schema import EvalItem

ORDINAL = {1: "first", 2: "second", 3: "third", 4: "fourth"}
SCALE_WORD = {0: "", 3: " thousand", 6: " million", 9: " billion"}
SCALE_TAG = {0: "unit_scale_ones", 3: "unit_scale_thousands", 6: "unit_scale_millions",
             9: "unit_scale_billions"}  # fmt: skip
# Inclusive day counts printed as months: calendar and 13/14-week quarters and their
# sums, with slack for filers whose quarters end on a nearby weekday (PFE: 88, 179
# days). Costco's 12-week quarters (84, 168, 252 days) fall outside and are printed
# in weeks, as Costco prints them ("12 Weeks Ended", "24 Weeks Ended").
MONTH_DAYS = ((85, 98, "three months"), (175, 189, "six months"), (262, 280, "nine months"))
QUARTERS = {2: "two", 3: "three"}


class ItemError(ValueError):
    """A drawn key that cannot become an item as specified; reported, never patched."""


def long_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d:%B} {d.day}, {d.year}"


@dataclass(frozen=True)
class PeriodInfo:
    kind: str  # annual | quarter | ytd | instant
    period: str
    dates: str  # "the three months ended ..." or, for an instant, the date
    filing: str


def period_info(key: PoolKey) -> PeriodInfo:
    fy, q, form = key.fiscal_year, key.fiscal_quarter, key.own_form
    if form == "10-K" and q is None:
        filing = f"fiscal {fy} 10-K"
    elif form == "10-Q" and q in (1, 2, 3):
        filing = f"10-Q for the {ORDINAL[q]} quarter of fiscal {fy}"
    else:
        raise ItemError(f"own filing {form} with fiscal quarter {q}")
    if key.period_start is None:
        at = f"the end of fiscal {fy}" if q is None else (
            f"the end of the {ORDINAL[q]} quarter of fiscal {fy}"
        )  # fmt: skip
        return PeriodInfo("instant", at, long_date(key.period_end), filing)
    days = (date.fromisoformat(key.period_end) - date.fromisoformat(key.period_start)).days + 1
    end = long_date(key.period_end)
    if q is None:
        if 357 <= days <= 371:
            return PeriodInfo("annual", f"fiscal {fy}", f"the fiscal year ended {end}", filing)
        raise ItemError(f"{days}-day period in a 10-K")
    span = next((w for lo, hi, w in MONTH_DAYS if lo <= days <= hi), None)
    if span is None and days % 7 == 0:
        span = f"{days // 7} weeks"
    if span is None:
        raise ItemError(f"{days}-day period is neither months nor whole weeks")
    if days <= 120:
        return PeriodInfo("quarter", f"the {ORDINAL[q]} quarter of fiscal {fy}",
                          f"the {span} ended {end}", filing)  # fmt: skip
    if q in QUARTERS and 80 * q <= days <= 95 * q:
        return PeriodInfo("ytd", f"the first {QUARTERS[q]} quarters of fiscal {fy}",
                          f"the {span} ended {end}", filing)  # fmt: skip
    raise ItemError(f"{days}-day period in a 10-Q labelled Q{q}")


def format_value(value: Decimal, unit: str, scales: tuple[int | None, ...]) -> tuple[str, str]:
    """(answer text, scale tag). USD at the one scale the filing prints; EPS unscaled."""
    sign = "-" if value < 0 else ""
    if unit == "USD/shares":
        a = abs(value).normalize()
        places = max(2, -a.as_tuple().exponent)
        return f"{sign}${a:,.{places}f}", "unit_scale_none"
    if unit != "USD":
        raise ItemError(f"unit {unit!r} has no format")
    if len(scales) != 1 or scales[0] not in SCALE_WORD:
        raise ItemError(f"own filing's exact-value spans print scales {list(scales)}")
    s = scales[0]
    n = abs(value).scaleb(-s).normalize()
    text = f"{int(n):,}" if n == n.to_integral_value() else f"{n:,f}"
    return f"{sign}${text}{SCALE_WORD[s]}", SCALE_TAG[s]


def build_items(
    draw: list[PoolKey],
    *,
    forms: dict[str, list[dict]],
    labels: dict[str, str],
    company_names: dict[str, str],
    seed: int,
    dataset_version: str,
) -> tuple[list[dict], list[tuple[str, str]]]:
    """(items, problems). One RNG draw per key, so a problem never shifts later picks."""
    rng = random.Random(f"{seed}:templates")
    items, problems = [], []
    for n, key in enumerate(draw, start=1):
        kind = "instant" if key.period_start is None else "duration"
        form = rng.choice(forms[kind])
        try:
            p = period_info(key)
            answer, scale_tag = format_value(key.value, key.unit, key.own_scales)
        except ItemError as e:
            problems.append((f"{key.ticker} {key.line_item} {key.period_end} "
                             f"{key.own_accession}", str(e)))  # fmt: skip
            continue
        question = form["text"].format(
            company=company_names[key.ticker],
            label=labels[key.line_item],
            period=p.period,
            dates=p.dates,
            date=p.dates,
            filing=p.filing,
        )
        sets, accessions = evidence_for(
            key, key.own_accession if form["scope"] == "filing" else None
        )
        when = f"as of {p.dates}" if p.kind == "instant" else f"for {p.dates}"
        items.append(
            EvalItem(
                item_id=f"xbrl_{n:04d}",
                question=question,
                question_type="xbrl_numeric",
                difficulty="easy",
                reference_answer=f"{answer} {when}.",
                gold_evidence_sets=sets,
                gold_accessions=accessions,
                expected_abstain=False,
                tags=[
                    key.ticker,
                    key.line_item,
                    f"FY{key.fiscal_year}",
                    key.own_form,
                    p.kind,
                    f"template:{form['id']}",
                    scale_tag,
                ],
                source="xbrl_auto",
                xbrl_fact_id=key.xbrl_fact_id,
                reviewed_by_human=False,
                dataset_version=dataset_version,
            ).to_dict()
        )
    return items, problems


def spot_check_ids(items: list[dict], seed: int, n: int) -> list[str]:
    ids = sorted(i["item_id"] for i in items)
    return sorted(random.Random(f"{seed}:spot_check").sample(ids, min(n, len(ids))))
