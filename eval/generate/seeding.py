"""LLM seeding (PRD 11.1 Stage 1 and 2; TRADEOFFS, LLM seeding). Pure, no model call.

Allocation: within a ticker, slots go to (form, item_code) strata in proportion
to their eligible chunk counts, by largest remainder.
"""

from __future__ import annotations

import hashlib
import json
import random
import re
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction

from api.numbers import NumberFormatError, parse_number, to_base_units


def pick_extra(tickers: list[str], seed: int, n: int) -> list[str]:
    """The `n` tickers that get one slot above the even share, picked by the seed."""
    return sorted(random.Random(f"{seed}:extra").sample(sorted(tickers), n))


def allocate(counts: dict[tuple, int], n: int) -> dict[tuple, int]:
    """Largest-remainder apportionment of `n` slots over strata by chunk count.

    Ties on the remainder go to the larger stratum, then to the smaller key, so
    the result depends on the counts only. No stratum gets more slots than chunks.
    """
    total = sum(counts.values())
    if n > total:
        raise ValueError(f"{n} slots for {total} chunks")
    quota = {k: Fraction(n * c, total) for k, c in counts.items() if c}
    slots = {k: int(q) for k, q in quota.items()}
    order = sorted(quota, key=lambda k: (-(quota[k] - slots[k]), -counts[k], k))
    for k in order[: n - sum(slots.values())]:
        slots[k] += 1
    assert all(slots[k] <= counts[k] for k in slots)
    return {k: v for k, v in sorted(slots.items()) if v}


# --- Stage 2 filters and review aids (key-free) -------------------------------

KINDS = ("factual", "interpretive")
FIGURE = re.compile(r"\(?-?\$?\s?\d[\d,]*(?:\.\d+)?\)?%?")
PERSONAL = re.compile(r"\b(it|its|they|them|their|he|she|his|her)\b", re.I)
DEICTIC = re.compile(
    r"\b(this|these|that|those)\s+(table|section|filing|report|document|passage|text|"
    r"excerpt|chunk|statement|note|period|quarter|year|company|segment)s?\b",
    re.I,
)


@dataclass(frozen=True)
class Drop:
    filter: str
    reason: str
    sign_only: bool = False  # answer_in_quote: |answer| is in the quote with the other sign


def normalize_verbatim(text: str) -> str:
    """Whitespace runs to one space, table pipes to spaces. Nothing else."""
    return " ".join(text.replace("|", " ").split())


def quote_in_chunk(quote: str, chunk_text: str) -> bool:
    q = normalize_verbatim(quote)
    return bool(q) and q in normalize_verbatim(chunk_text)


def parse_figure(text: str) -> Decimal:
    """A printed figure with `api.numbers.parse_number`; a trailing % is dropped."""
    return parse_number(text.strip().removesuffix("%").strip())


def figures(text: str) -> list[Decimal]:
    """Every printed figure in a text, normalized by `parse_figure`."""
    out = []
    for m in FIGURE.finditer(text):
        tok = m.group(0)
        if tok.endswith(")") and not tok.startswith("("):
            tok = tok[:-1]
        if tok.startswith("(") and not tok.rstrip("%").endswith(")"):
            tok = tok[1:]
        try:
            out.append(parse_figure(tok))
        except NumberFormatError:
            continue
    return out


MAGNITUDE = {"thousands": 3, "millions": 6, "billions": 9}
SCALE_EXCEPTION = re.compile(r"\b(thousands|millions|billions)\b[^|\n]{0,40}?\bexcept\b", re.I)
PER_SHARE_EXCEPTION = re.compile(r"\bexcept\b[^|\n]{0,40}?\bper share\b", re.I)


def mixed_signals(
    raw_text: str, unit_scale: str | None, span_scales: list[int | None]
) -> list[str]:
    """Why a table's caption scale may not apply to every figure in it (F-90).

    Either signal marks the table mixed: a scale-exception clause in the chunk
    text ("In millions, except per share data" -- in filings it sits in a column
    header cell, not the caption line), or a tagged span in the chunk whose ix
    scale is not the caption's magnitude (an absent scale counts as 0). Neither
    covers an untagged per-share, percent or count row, so scale is confirmed at
    review for every table item.
    """
    reasons = []
    m = SCALE_EXCEPTION.search(raw_text)
    if m:
        reasons.append(f"scale exception clause {m.group(0)!r}")
    if unit_scale is not None:
        want = MAGNITUDE[unit_scale.strip().lower()]
        other = sorted({0 if sc is None else sc for sc in span_scales} - {want})
        if other:
            reasons.append(f"tagged spans at ix scale {other}, caption {unit_scale} ({want})")
    return reasons


def attach_scale(
    figure: str, unit_scale: str | None, mixed: list[str], span_scale: int | None = None
) -> tuple[Decimal, list[str]]:
    """(value, flags). The caption scale is applied only to a figure from a table
    nothing marks as mixed; a percent is never scaled. NULL or mixed: the printed
    value and a flag, never a guess. `span_scale` (the answer's own tagged span,
    if any) is reported for the reviewer, not applied."""
    value = parse_figure(figure)
    flags = []
    if span_scale is not None:
        flags.append(f"answer is a tagged span at ix scale {span_scale} (review aid, not applied)")
    if figure.strip().endswith("%"):
        return value, flags
    if unit_scale is None:
        return value, ["scale unknown: chunk has no unit_scale", *flags]
    if mixed:
        return value, [f"scale not applied, mixed table: {'; '.join(mixed)}", *flags]
    return to_base_units(value, unit_scale), flags


def answer_flags(answer: str) -> list[str]:
    """Sheet flags on a stored answer. A parenthesized figure is kept as printed:
    code does not decide whether "(2,815)" is -2,815 or an outflow of 2,815 (F-87)."""
    a = answer.strip().removeprefix("$").strip()
    return ["parenthesized figure: sign wording set at review (F-87)"] if a.startswith("(") else []


def unanchored_pronoun(question: str, company_names: list[str]) -> str | None:
    """The rule: a deictic phrase pointing at the source ("this table", "these
    periods") is always unanchored; a personal pronoun (it, its, they, ...) is
    unanchored unless a company name or ticker occurs before it in the question."""
    m = DEICTIC.search(question)
    if m:
        return f"deictic reference {m.group(0)!r}"
    p = PERSONAL.search(question)
    if p:
        names = [n for n in company_names if n]
        first = min((question.find(n) for n in names if n in question), default=-1)
        if first < 0 or first > p.start():
            return f"pronoun {p.group(0)!r} before any company name"
    return None


def parse_response(text: str) -> tuple[list[dict] | None, str | None]:
    """The model's JSON, or (None, reason). One fenced block or a bare object."""
    s = text.strip()
    fence = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", s, re.S)
    if fence:
        s = fence.group(1)
    try:
        doc = json.loads(s)
    except json.JSONDecodeError as e:
        return None, f"not JSON: {e.msg}"
    qs = doc.get("questions") if isinstance(doc, dict) else None
    if not isinstance(qs, list) or len(qs) != 2:
        return None, "expected an object with a list of 2 questions"
    keys = {"kind", "question", "answer", "supporting_quote"}
    for q in qs:
        if not isinstance(q, dict) or set(q) != keys:
            return None, f"question keys must be {sorted(keys)}"
        if not all(isinstance(q[k], str) and q[k].strip() for k in keys):
            return None, "every field must be a non-empty string"
    if sorted(q["kind"] for q in qs) != list(KINDS):
        return None, "need one factual and one interpretive question"
    return qs, None


def filter_question(
    q: dict, chunk_text: str, company_names: list[str], numeric: bool
) -> Drop | None:
    """Key-free Stage 2 filters on one question, in order; the first failure drops it.

    `numeric`: the item takes a figure as its answer (table items), so the
    figure must appear inside the supporting quote and not in the question.
    """
    if not quote_in_chunk(q["supporting_quote"], chunk_text):
        return Drop("quote_verbatim", "supporting quote not in the chunk (whitespace/pipes only)")
    if numeric:
        try:
            value = parse_figure(q["answer"])
        except NumberFormatError:
            return Drop("answer_figure", f"answer {q['answer']!r} is not a printed figure")
        quoted = figures(q["supporting_quote"])
        if value not in quoted:
            sign_only = value != 0 and -value in quoted
            why = "only with the opposite sign" if sign_only else "not"
            return Drop("answer_in_quote", f"figure {q['answer']!r} {why} in the supporting quote",
                        sign_only)  # fmt: skip
        if value in figures(q["question"]):
            return Drop("question_leaks_answer", f"figure {q['answer']!r} appears in the question")
    if not any(n in q["question"] for n in company_names if n):
        return Drop("names_company", "question names no company or ticker")
    why = unanchored_pronoun(q["question"], company_names)
    if why:
        return Drop("unanchored_pronoun", why)
    return None


def near_duplicates(new: list, existing: list, threshold: float) -> list[tuple[int, float] | None]:
    """Per new vector: (index into existing + earlier new, cosine) above `threshold`, or None.

    Vectors are compared by cosine; earlier new items count as existing for later
    ones, so of two near-duplicates the first in draw order survives.
    """
    import numpy as np

    pool = [np.asarray(v, dtype=float) for v in existing]
    out = []
    for v in new:
        v = np.asarray(v, dtype=float)
        best = None
        for j, w in enumerate(pool):
            cos = float(v @ w / (np.linalg.norm(v) * np.linalg.norm(w)))
            if cos > threshold and (best is None or cos > best[1]):
                best = (j, cos)
        out.append(best)
        pool.append(v)
    return out


def same_number_elsewhere(
    value: Decimal, chunk_texts: dict[str, str], tagged: dict[str, set[Decimal]]
) -> tuple[list[str], list[str]]:
    """Review aid, never evidence: (chunks with a tagged span of `value`, chunks
    printing it only as a bare figure). `chunk_texts` and `tagged` are one filer's."""
    tagged_hits = sorted(c for c, vals in tagged.items() if value in vals)
    bare = sorted(c for c, t in chunk_texts.items() if c not in tagged_hits and value in figures(t))
    return tagged_hits, bare


def quote_elsewhere(quote: str, chunk_texts: dict[str, str]) -> list[str]:
    """Review aid: chunks containing the supporting quote verbatim (normalized)."""
    return sorted(c for c, t in chunk_texts.items() if quote_in_chunk(quote, t))


# --- Stage 1 prompt ---------------------------------------------------------------

CHUNK_SLOT = "<<CHUNK>>"


def render_prompt(template: str, chunk_text: str) -> str:
    """The seeding prompt for one chunk: the template with its single slot filled."""
    if template.count(CHUNK_SLOT) != 1:
        raise ValueError(f"template must hold {CHUNK_SLOT} exactly once")
    return template.replace(CHUNK_SLOT, chunk_text)


def prompt_sha(template: str) -> str:
    return hashlib.sha256(template.encode("utf-8")).hexdigest()
