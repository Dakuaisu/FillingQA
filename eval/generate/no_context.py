"""The no-context filter (PRD 11.1 Stage 2; TRADEOFFS: no-context filter rule). Pure.

A table item is answerable without its chunk, and dropped, when any figure in
the no-context answer, normalized by its own scale word, is within 0.5% of the
item's value in magnitude -- the PRD's own tolerance for "the same figure"
(6.5.4, 7.5). Scale unknown or mixed table: printed values are compared with the
same tolerance and a match is flagged `digits_only`. Within 5% but not 0.5% is a
near-match, recorded for review, not dropped. Interpretive items are not judged
by code.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal

from api.numbers import NumberFormatError
from eval.generate.seeding import parse_figure

TOLERANCE = Decimal("0.005")
NEAR = Decimal("0.05")
QUESTION_SLOT = "<<QUESTION>>"
SCALE_WORDS = {"thousand": 3, "million": 6, "billion": 9, "trillion": 12}
FIGURE_WITH_SCALE = re.compile(
    r"(?P<num>\(?-?\$?\s?\d[\d,]*(?:\.\d+)?\)?%?)"
    r"(?:\s*(?P<scale>thousand|million|billion|trillion)s?\b)?",
    re.I,
)
UNKNOWN = re.compile(r"\bunknown\b", re.I)


@dataclass(frozen=True)
class Figure:
    printed: Decimal  # the number as printed, sign included, no scale applied
    value: Decimal  # scaled by the figure's own scale word, if any
    text: str


@dataclass
class Match:
    dropped: bool = False
    digits_only: bool = False
    near: bool = False
    sign_only: bool = False  # a magnitude match whose sign disagrees with the item's
    unknown: bool = False
    matched_text: str | None = None
    figures: list[str] = field(default_factory=list)


def render(template: str, question: str) -> str:
    if template.count(QUESTION_SLOT) != 1:
        raise ValueError(f"template must hold {QUESTION_SLOT} exactly once")
    return template.replace(QUESTION_SLOT, question)


def figures(answer: str) -> list[Figure]:
    out = []
    for m in FIGURE_WITH_SCALE.finditer(answer):
        tok = m.group("num")
        if tok.endswith(")") and not tok.startswith("("):
            tok = tok[:-1]
        if tok.startswith("(") and not tok.rstrip("%").endswith(")"):
            tok = tok[1:]
        try:
            printed = parse_figure(tok)
        except NumberFormatError:
            continue
        scale = m.group("scale")
        value = printed * Decimal(10) ** SCALE_WORDS[scale.lower()] if scale else printed
        out.append(Figure(printed, value, m.group(0).strip()))
    return out


def within(a: Decimal, target: Decimal, tol: Decimal) -> bool:
    if target == 0:
        return a == 0
    return abs(abs(a) - abs(target)) <= tol * abs(target)


def match(answer: str, printed: Decimal, value: Decimal | None) -> Match:
    """`printed`: the item's figure as printed (sign included); `value`: its value
    in base units, or None when the scale is unknown or the table is mixed."""
    figs = figures(answer)
    m = Match(figures=[f.text for f in figs], unknown=not figs and bool(UNKNOWN.search(answer)))
    target = value if value is not None else printed
    for f in figs:
        got = f.value if value is not None else f.printed
        if within(got, target, TOLERANCE):
            m.dropped, m.digits_only, m.matched_text = True, value is None, f.text
            m.sign_only = (got < 0) != (printed < 0) and got != 0
            return m
        if within(got, target, NEAR):
            m.near = True
    return m
