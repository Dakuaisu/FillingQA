"""xbrl_auto comparison items (PRD 11.1 comparison row, Stage 3; TRADEOFFS). Pure.

A pair is two eligible keys (F-75) of one filer and line item, same period kind
and fiscal quarter, `gap` fiscal years apart by the own-period filing's dei
label. It is eligible only if no chunk holds a tagged exact-value span of both
sides (F-83): then, and only then, every evidence set needs both chunks.
"""

from __future__ import annotations

import random
import re
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal

from eval.generate.pool import PoolKey
from eval.generate.schema import EvalItem
from eval.generate.xbrl_items import ItemError, format_value, period_info

NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


@dataclass(frozen=True)
class Pair:
    kind: str  # annual | quarter | ytd | instant
    gap: int  # fiscal years between the sides
    earlier: PoolKey
    later: PoolKey

    @property
    def ticker(self) -> str:
        return self.later.ticker

    @property
    def line_item(self) -> str:
        return self.later.line_item

    @property
    def stratum(self) -> tuple[str, str, str]:
        return (self.ticker, self.line_item, self.kind)

    @property
    def sort_key(self) -> tuple:
        return self.earlier.sort_key + self.later.sort_key

    @property
    def members(self) -> frozenset[tuple]:
        return frozenset({self.earlier.key, self.later.key})


def chunks(k: PoolKey) -> set[str]:
    return {c for _, cs in k.evidence for c in cs}


def shares_chunk(p: Pair) -> bool:
    return bool(chunks(p.earlier) & chunks(p.later))


def tokens(text: str) -> set[str]:
    """Printed numbers in a text, as printed ("13,840", "0.90")."""
    return {m.group(0).rstrip(",") for m in NUMBER.finditer(text)}


def build_pairs(eligible: list[PoolKey], gaps: list[int]) -> list[Pair]:
    """Every pair, shared chunk or not; a slot holding two keys pairs with nothing."""
    slots: dict[tuple, list[PoolKey]] = defaultdict(list)
    for k in eligible:
        slots[(k.cik, k.line_item, period_info(k).kind, k.fiscal_quarter, k.fiscal_year)].append(k)
    pairs = []
    for (cik, item, kind, q, fy), ks in slots.items():
        for gap in gaps:
            prev = slots.get((cik, item, kind, q, fy - gap))
            if prev and len(ks) == 1 and len(prev) == 1:
                pairs.append(Pair(kind, gap, prev[0], ks[0]))
    return sorted(pairs, key=lambda p: (p.sort_key, p.gap))


def eligible_pairs(pairs: list[Pair], exclude: set[tuple]) -> list[Pair]:
    """No shared gold chunk (F-83); neither side among `exclude` (drawn xbrl_numeric keys)."""
    return [
        p for p in pairs
        if not shares_chunk(p) and p.earlier.key not in exclude and p.later.key not in exclude
    ]  # fmt: skip


def cooccurrence(p: Pair, printed: dict[tuple, set[str]], index: dict) -> set[str]:
    """Chunks of the filer printing both sides' printed values, tagged there or not.

    `printed`: period key -> printed tokens of its exact-value spans;
    `index`: cik -> token -> chunk ids. A token match, so an upper bound.
    """
    found = []
    for k in (p.earlier, p.later):
        found.append(set().union(*(index[k.cik].get(t, set()) for t in printed[k.key])))
    return found[0] & found[1]


def evidence(p: Pair) -> tuple[list[list[str]], list[str]]:
    """(gold_evidence_sets, gold_accessions): every (a, b) combination, uncapped."""
    if shares_chunk(p):
        raise ValueError(f"{p.ticker} {p.line_item} {p.earlier.period_end}/{p.later.period_end}: "
                         "the sides share a chunk; not an eligible pair")  # fmt: skip
    sets = sorted(sorted((a, b)) for a in chunks(p.earlier) for b in chunks(p.later))
    accessions = sorted({a for k in (p.earlier, p.later) for a, _ in k.evidence})
    return sets, accessions


def difference(p: Pair) -> Decimal:
    return p.later.value - p.earlier.value


def reference_answer(p: Pair) -> tuple[str, str]:
    """(reference answer, scale tag): both values with their period labels, then the
    difference, later minus earlier on the fact values, at the shared printed scale."""
    a, b = p.earlier, p.later
    if a.unit != b.unit:
        raise ItemError(f"units {a.unit} / {b.unit}")
    if a.unit == "USD" and set(a.own_scales) != set(b.own_scales):
        raise ItemError(f"sides print at scales {list(a.own_scales)} / {list(b.own_scales)}")
    va, tag = format_value(a.value, a.unit, a.own_scales)
    vb, _ = format_value(b.value, b.unit, b.own_scales)
    d = difference(p)
    dv, _ = format_value(abs(d), b.unit, b.own_scales)
    direction = "an increase of" if d > 0 else "a decrease of" if d < 0 else "a difference of"
    prep = "at" if p.kind == "instant" else "for"
    pa, pb = period_info(a).period, period_info(b).period
    return f"{vb} {prep} {pb}, compared with {va} {prep} {pa}: {direction} {dv}.", tag


def build_comparison_items(
    draw: list[Pair],
    *,
    forms: dict[str, list[dict]],
    labels: dict[str, str],
    company_names: dict[str, str],
    seed: int,
    dataset_version: str,
) -> tuple[list[dict], list[tuple[str, str]]]:
    """(items, problems). One RNG draw per pair, so a problem never shifts later picks."""
    rng = random.Random(f"{seed}:comparison_templates")
    items, problems = [], []
    for n, p in enumerate(draw, start=1):
        form = rng.choice(forms["instant" if p.kind == "instant" else "duration"])
        try:
            answer, scale_tag = reference_answer(p)
        except ItemError as e:
            problems.append((f"{p.ticker} {p.line_item} {p.earlier.period_end}/"
                             f"{p.later.period_end}", str(e)))  # fmt: skip
            continue
        sets, accessions = evidence(p)
        question = form["text"].format(
            company=company_names[p.ticker], label=labels[p.line_item],
            earlier=period_info(p.earlier).period, later=period_info(p.later).period,
        )  # fmt: skip
        items.append(
            EvalItem(
                item_id=f"cmp_{n:04d}",
                question=question,
                question_type="comparison",
                difficulty="medium",
                reference_answer=answer,
                gold_evidence_sets=sets,
                gold_accessions=accessions,
                expected_abstain=False,
                tags=[
                    p.ticker,
                    p.line_item,
                    f"FY{p.earlier.fiscal_year}",
                    f"FY{p.later.fiscal_year}",
                    p.kind,
                    f"gap{p.gap}",
                    f"template:{form['id']}",
                    scale_tag,
                ],
                source="xbrl_auto",
                xbrl_fact_id=p.later.xbrl_fact_id,
                reviewed_by_human=False,
                dataset_version=dataset_version,
            ).to_dict()
        )
    return items, problems
