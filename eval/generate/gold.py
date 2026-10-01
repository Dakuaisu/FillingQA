"""Which chunks are gold for a fact (PRD 6.5.3, F-32, F-72). Pure.

`spans` are every xbrl_spans row of the fact's accession, concept and period,
dimensional or not. A chunk is gold when it holds a span that is
non-dimensional (F-32: a segment figure is not the company-level fact) and
whose value equals the fact's (F-72: a rounded mention cannot yield the answer).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Span:
    chunk_id: str | None
    value: Decimal
    raw_text: str | None
    scale: int | None
    dimensional: bool


@dataclass(frozen=True)
class GoldSelection:
    gold: tuple[str, ...]  # sorted distinct chunk ids
    exact: tuple[Span, ...]  # the gold spans, in input order
    prd_key_count: int  # distinct chunks under PRD 6.5.3's literal key, non-dimensional
    has_span: bool  # any non-dimensional span, in a chunk or not


def select_gold(fact_value: Decimal, spans: list[Span]) -> GoldSelection:
    company = [s for s in spans if not s.dimensional]
    exact = tuple(s for s in company if s.chunk_id and s.value == fact_value)
    return GoldSelection(
        gold=tuple(sorted({s.chunk_id for s in exact})),
        exact=exact,
        prd_key_count=len({s.chunk_id for s in company if s.chunk_id}),
        has_span=bool(company),
    )
