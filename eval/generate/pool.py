"""The xbrl_auto pool and sampler (F-75, TRADEOFFS sampler design). Pure functions.

Input rows are facts as `scripts.concept_coverage.classify_facts` returns them.
The unit is the key (cik, concept, period_start, period_end). A key is eligible
when (a) it has one value across all parsed accessions, (b) every fact of it is
in the 1-3 bucket, and (c) a parsed filing reports the period as its own.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal

ELIGIBLE = "eligible"
NOT_SAMPLED = "comparative_only"
REVIEW_REASONS = ("value_differs", "mixed_key", "gt3")
NO_GOLD = "no_gold"  # PRD 6.5.3 human labeling, eval/human_label_queue.csv


@dataclass(frozen=True)
class PoolKey:
    cik: str
    ticker: str
    line_item: str
    concept: str
    period_start: str | None
    period_end: str
    value: Decimal
    unit: str
    xbrl_fact_id: int
    own_accession: str
    own_form: str
    fiscal_year: int
    fiscal_quarter: int | None
    evidence: tuple[tuple[str, tuple[str, ...]], ...]  # (accession, exact-value chunk ids)
    own_scales: tuple[int | None, ...]  # ix scale of the own filing's exact-value spans

    @property
    def key(self) -> tuple:
        return (self.cik, self.concept, self.period_start, self.period_end)

    @property
    def stratum(self) -> tuple[str, str, str]:
        return (self.ticker, self.line_item, self.own_form)

    @property
    def gold_accessions(self) -> list[str]:
        return evidence_for(self)[1]

    @property
    def gold_evidence_sets(self) -> list[list[str]]:
        return evidence_for(self)[0]


@dataclass
class Pool:
    eligible: list[PoolKey] = field(default_factory=list)
    category: dict[int, str] = field(default_factory=dict)  # fact_id -> category


def classify_key(facts: list[dict]) -> str:
    if len({f["value"] for f in facts}) > 1:
        return "value_differs"
    buckets = {f["bucket"] for f in facts}
    if "0" in buckets:
        return NO_GOLD
    if buckets == {">3"}:
        return "gt3"
    if buckets != {"1-3"}:
        return "mixed_key"
    if all(f["is_comparative"] for f in facts):
        return NOT_SAMPLED
    return ELIGIBLE


def build_pool(rows: list[dict]) -> Pool:
    keys: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        keys[(r["cik"], r["concept"], *r["period"])].append(r)
    pool = Pool()
    for key in sorted(keys, key=lambda k: (k[0], k[1], k[2] or "", k[3])):
        facts = keys[key]
        cat = classify_key(facts)
        for f in facts:
            pool.category[f["fact_id"]] = cat
        if cat != ELIGIBLE:
            continue
        own = [f for f in facts if not f["is_comparative"]]
        if len({f["accession"] for f in own}) != 1:
            raise ValueError(f"key {key} has {len(own)} own-period facts; F-75 assumes one")
        o = own[0]
        evidence: dict[str, set[str]] = defaultdict(set)
        for f in facts:
            evidence[f["accession"]].update(f["gold"])
        pool.eligible.append(
            PoolKey(
                cik=o["cik"],
                ticker=o["ticker"],
                line_item=o["line_item"],
                concept=o["concept"],
                period_start=o["period"][0],
                period_end=o["period"][1],
                value=o["value"],
                unit=o["unit"],
                xbrl_fact_id=o["fact_id"],
                own_accession=o["accession"],
                own_form=o["form"],
                fiscal_year=o["filing_fiscal_year"],
                fiscal_quarter=o["filing_fiscal_quarter"],
                evidence=tuple((a, tuple(sorted(c))) for a, c in sorted(evidence.items())),
                own_scales=tuple(o["exact_scales"]),
            )
        )
    return pool


class Shortfall(Exception):
    """A ticker has fewer eligible keys than its allocation; no backfill."""

    def __init__(self, short: dict[str, tuple[int, int]]):
        self.short = short  # ticker -> (eligible keys, allocation)
        super().__init__(
            "; ".join(f"{t}: {have} eligible < {want}" for t, (have, want) in short.items())
        )


def sample(eligible: list[PoolKey], seed: int, total: int, per_ticker: dict[str, int]):
    """Seeded draw: per ticker, round-robin over its strata in shuffled order."""
    if sum(per_ticker.values()) != total:
        raise ValueError(f"per_ticker sums to {sum(per_ticker.values())}, total is {total}")
    by_ticker: dict[str, dict[tuple, list[PoolKey]]] = defaultdict(lambda: defaultdict(list))
    for k in sorted(eligible, key=lambda k: (k.key[0], k.key[1], k.key[2] or "", k.key[3])):
        by_ticker[k.ticker][k.stratum].append(k)
    short = {
        t: (sum(len(v) for v in by_ticker[t].values()), n)
        for t, n in per_ticker.items()
        if sum(len(v) for v in by_ticker[t].values()) < n
    }
    if short:
        raise Shortfall(short)
    rng = random.Random(seed)
    draw: list[PoolKey] = []
    for ticker in sorted(per_ticker):
        strata = [list(by_ticker[ticker][s]) for s in sorted(by_ticker[ticker])]
        for keys in strata:
            rng.shuffle(keys)
        rng.shuffle(strata)
        taken: list[PoolKey] = []
        while len(taken) < per_ticker[ticker]:
            for keys in strata:
                if keys and len(taken) < per_ticker[ticker]:
                    taken.append(keys.pop())
        draw.extend(taken)
    return draw


def evidence_for(key: PoolKey, accession: str | None = None) -> tuple[list[list[str]], list[str]]:
    """(gold_evidence_sets, gold_accessions): every accession, or one filing's only."""
    ev = [(a, c) for a, c in key.evidence if accession is None or a == accession]
    return [[c] for c in sorted({c for _, cs in ev for c in cs})], [a for a, _ in ev]
