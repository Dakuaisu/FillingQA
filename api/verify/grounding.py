"""Numeric grounding and unit scale for figure claims (PRD 7.5). Pure.

Decisions in TRADEOFFS ("numeric grounding (PRD 7.5), and F-82, F-85, F-87"):
magnitudes, not signs (F-87); a zero is grounded by a printed 0 or a nil
inline-XBRL span (F-82); a number printed nowhere is grounded as derived only
when it is the difference or percent change of two of the answer's own grounded
figures (F-85). Exact Decimal equality throughout; no tolerance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from api.numbers import NumberFormatError, parse_number
from eval.metrics.numeric import FIGURE, FIGURE_UNITS, SCALE_WORDS, mask

CAPTION = re.compile(r"^\[Table:[^\n]*\|\s*in\s+(thousands|millions|billions)\b", re.I | re.M)
EXCEPT_PER_SHARE = re.compile(r"except\s+(?:for\s+)?per[\s-]share", re.I)
PERIOD = re.compile(
    r"\b(?:Q[1-4]|FY\s?'?\d{2,4}|fiscal\s+(?:year\s+)?\d{4}|(?:19|20)\d{2}|"
    r"(?:year|quarter|months|weeks)\s+ended)\b"
    r"|\b(?:first|second|third|fourth)\s+quarter\b",
    re.I,
)
CAPTION_SCALE = {"thousands": 3, "millions": 6, "billions": 9}


@dataclass(frozen=True)
class Num:
    value: Decimal  # magnitude, base units (percent: the percentage itself)
    pct: bool
    printed: str


@dataclass
class ChunkNumbers:
    scaled: set[Decimal] = field(default_factory=set)  # stated scale or printed scale word
    raw: set[Decimal] = field(default_factory=set)  # as printed
    pct: set[Decimal] = field(default_factory=set)
    except_per_share: bool = False
    zero_span: bool = False  # holds an inline-XBRL span of value 0 (F-82)
    unscaled: set[Decimal] = field(default_factory=set)  # printed bare, chunk states no scale


def _figures(text: str):
    for m in FIGURE.finditer(mask(text)):
        try:
            v = abs(parse_number(m.group("num")))
        except NumberFormatError:
            continue
        yield m, v


def chunk_numbers(text: str, zero_span: bool = False) -> ChunkNumbers:
    cap = CAPTION.search(text)
    scale = CAPTION_SCALE[cap.group(1).lower()] if cap else None
    out = ChunkNumbers(except_per_share=bool(EXCEPT_PER_SHARE.search(text)), zero_span=zero_span)
    for m, v in _figures(text):
        if m.group("pct"):
            out.pct.add(v)
            continue
        out.raw.add(v)
        if m.group("scale"):
            out.scaled.add(v * Decimal(10) ** SCALE_WORDS[m.group("scale").lower()])
        elif scale is not None:
            out.scaled.add(v * Decimal(10) ** scale)
        else:
            out.unscaled.add(v)
    return out


def claim_numbers(text: str, figure: dict | None) -> list[Num]:
    """The claim's figures (text and figure object), each magnitude once."""
    out: list[Num] = []
    for m, v in _figures(text):
        if m.group("pct"):
            out.append(Num(v, True, m.group(0).strip()))
        else:
            sw = m.group("scale")
            out.append(Num(v * Decimal(10) ** SCALE_WORDS[sw.lower()] if sw else v, False,
                           m.group(0).strip()))  # fmt: skip
    f = figure_value(figure)
    if f is not None:
        out.append(f)
    seen, uniq = set(), []
    for n in out:
        if (n.value, n.pct) not in seen:
            seen.add((n.value, n.pct))
            uniq.append(n)
    return uniq


def figure_value(figure: dict | None) -> Num | None:
    if not figure or figure.get("value") is None:
        return None
    v = abs(Decimal(str(figure["value"])))
    unit = (figure.get("unit") or "").lower()
    if unit == "percent":
        return Num(v, True, f"figure {figure['value']} percent")
    return Num(
        v * Decimal(10) ** FIGURE_UNITS.get(unit, 0), False, f"figure {figure['value']} {unit}"
    )


def grounded_in(n: Num, chunks: dict[str, ChunkNumbers]) -> list[str]:
    """Cited chunk ids printing the number (any candidate), or a zero by span."""
    hits = []
    for cid, c in chunks.items():
        if n.pct:
            ok = n.value in c.pct
        else:
            ok = n.value in c.scaled or n.value in c.raw or (n.value == 0 and c.zero_span)
        if ok:
            hits.append(cid)
    return hits


UNSTATED_SCALES = (3, 6, 9, 12)


def unscaled_in(n: Num, chunks: dict[str, ChunkNumbers]) -> list[str]:
    """Cited chunks stating no scale that print n's digits: n is a bare printed
    number times 10^3, 10^6, 10^9 or 10^12 (F-130; the scale cannot be checked)."""
    if n.pct:
        return []
    scales = [Decimal(10) ** k for k in UNSTATED_SCALES]
    return [
        cid
        for cid, c in chunks.items()
        if any(n.value == v * f for v in c.unscaled for f in scales)
    ]


def unit_ok(figure: dict | None, chunks: dict[str, ChunkNumbers]) -> bool | None:
    """The figure object's scaled value is printed at that scale in a cited chunk.
    None when the claim has no figure object."""
    f = figure_value(figure)
    if f is None:
        return None
    for c in chunks.values():
        if f.pct:
            if f.value in c.pct:
                return True
            continue
        as_is = f.value in c.raw and (
            c.except_per_share or (not c.scaled and (figure.get("unit") or "") == "ones")
        )
        if f.value in c.scaled or (f.value == 0 and c.zero_span) or as_is:
            return True
    return False


def period_stated(text: str) -> bool:
    return bool(PERIOD.search(text))


def _decimals(printed: str) -> int:
    m = re.search(r"\d+(?:,\d{3})*\.(\d+)", printed)
    return len(m.group(1)) if m else 0


def derived(n: Num, others: list[Num]) -> bool:
    """n is |a - b| or the percent change between a and b, for two of `others`
    (the answer's other grounded figures), at n's printed precision."""
    amounts = [o.value for o in others if not o.pct]
    q = Decimal(1).scaleb(-_decimals(n.printed))
    for i, a in enumerate(amounts):
        for b in amounts[i + 1 :]:
            if not n.pct and abs(a - b) == n.value:
                return True
            if n.pct:
                for base, new in ((a, b), (b, a)):
                    if (
                        base
                        and abs((new - base) / base * 100).quantize(q, ROUND_HALF_UP) == n.value
                    ):
                        return True
    return False


def ground_answer(claims: list[dict], chunk_text: dict[str, str],
                  zero_span_chunks: set[str]) -> list[dict]:  # fmt: skip
    """Per claim: numbers with where and how each is grounded (`printed`,
    `printed_unscaled` when the chunk states no scale, `derived`),
    `numbers_grounded`, `numbers_derived`, `unit_ok` (true / false / "unknown" /
    None), `period_stated`. Only the claim's own cited chunks that were given to
    the generator count (`chunk_text`)."""
    parsed = {cid: chunk_numbers(t, cid in zero_span_chunks) for cid, t in chunk_text.items()}
    rows = []
    for c in claims:
        cited = {x: parsed[x] for x in c["citations"] if x in parsed}
        found = []
        for n in claim_numbers(c["text"], c.get("figure")):
            hits = grounded_in(n, cited)
            if hits:
                found.append({"num": n, "in": hits, "how": "printed"})
                continue
            bare = unscaled_in(n, cited)
            found.append({"num": n, "in": bare, "how": "printed_unscaled" if bare else None})
        rows.append({"claim": c, "cited": cited, "numbers": found})
    pool = [x["num"] for r in rows for x in r["numbers"] if x["how"]]
    out = []
    for r in rows:
        nums, any_derived = [], False
        for x in r["numbers"]:
            how = x["how"]
            if how is None and derived(x["num"], [p for p in pool if p is not x["num"]]):
                how, any_derived = "derived", True
            nums.append({"printed": x["num"].printed, "value": str(x["num"].value),
                         "pct": x["num"].pct, "grounded_in": x["in"], "how": how})  # fmt: skip
        c = r["claim"]
        fv = figure_value(c.get("figure"))
        unit = unit_ok(c.get("figure"), r["cited"])
        if unit is False and fv is not None:
            hows = {
                n["how"] for n in nums if Decimal(n["value"]) == fv.value and n["pct"] == fv.pct
            }
            if "derived" in hows:
                unit = True  # derived from the answer's own figures at their printed scale (F-85)
            elif "printed_unscaled" in hows:
                unit = "unknown"  # the chunk states no scale (F-130)
        out.append({
            "numbers": nums,
            "numbers_grounded": all(n["how"] for n in nums),
            "numbers_derived": any_derived,
            "unit_ok": unit,
            "period_stated": period_stated(c["text"]),
            "citations_supporting": sorted({cid for n in nums for cid in n["grounded_in"]}),
        })  # fmt: skip
    return out
