"""Numeric accuracy (PRD 11.2; TRADEOFFS: numeric accuracy normalization, F-81). Pure.

Gated: exact at the reference's printed precision after scale normalization,
magnitude only, any answer figure. Reported beside it, never gated: the strict
variant (the answer's first figures only), 0.5%-tolerant accuracy, sign
agreement, figure count, fallback use, values-only accuracy for comparisons.

The free-text extractor is new code (not the frozen no-context one, F-97): it
masks dates, period labels, form names, item numbers, period lengths and bare
years before it reads a figure.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from api.numbers import NumberFormatError, parse_number

SCALE_WORDS = {"thousand": 3, "million": 6, "billion": 9, "trillion": 12}
FIGURE_UNITS = {"thousands": 3, "millions": 6, "billions": 9, "trillions": 12}
TAG_SCALES = {"unit_scale_thousands": 3, "unit_scale_millions": 6, "unit_scale_billions": 9}
TOLERANCE = Decimal("0.005")

_MONTH = (r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|"
          r"Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)")  # fmt: skip
MASKS = [
    re.compile(rf"\b{_MONTH}\.?\s+\d{{1,2}}(?:st|nd|rd|th)?,?\s+\d{{4}}\b", re.I),
    re.compile(r"\b\d{4}-\d{2}-\d{2}\b"),
    re.compile(r"\b\d{1,2},\s+(?:19|20)\d{2}\b"),
    re.compile(r"\bQ[1-4]\b", re.I),
    re.compile(r"\b(?:FY|fiscal(?:\s+year)?)\s*'?\d{2,4}\b", re.I),
    re.compile(r"\b(?:Form\s+)?(?:10-K|10-Q|8-K|20-F|S-1)(?:/A)?\b", re.I),
    re.compile(r"\b(?:Item|Note|Part|Section|Exhibit)\s+[IVX\d]+[A-C]?(?:\.\d+)?\b", re.I),
    re.compile(r"\b\d+[\s-](?:weeks?|months?|days?|quarters?|years?)\b", re.I),
    re.compile(
        r"(?<![$\d,.])\b(?:19|20)\d{2}\b(?![\d,.%]|\s*(?:thousand|million|billion|trillion))", re.I
    ),
]
FIGURE = re.compile(
    r"(?P<neg>[-\u2212]\s*)?(?P<open>\()?\s*\$?\s*"
    r"(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"\s*(?P<close>\))?\s*(?P<pct>%)?(?:\s*(?P<scale>thousand|million|billion|trillion)s?\b)?",
    re.I,
)
ZERO_WORDS = re.compile(r"\b(?:none|nil|zero)\b|^\s*[-\u2013\u2014]\s*$", re.I)


@dataclass(frozen=True)
class Fig:
    value: Decimal  # base units, signed
    explicit_sign: bool  # a minus, parentheses, or a signed figure object
    text: str


@dataclass(frozen=True)
class Ref:
    value: Decimal  # base units, signed
    quantum: Decimal  # base-unit value of the reference's last printed digit


def mask(text: str) -> str:
    for m in MASKS:
        text = m.sub(lambda x: " " * len(x.group(0)), text)
    return text


def text_figures(text: str) -> list[Fig]:
    out = []
    for m in FIGURE.finditer(mask(text)):
        try:
            v = parse_number(m.group("num"))
        except NumberFormatError:
            continue
        paren = bool(m.group("open") and m.group("close"))
        neg = paren or bool(m.group("neg"))
        scale = m.group("scale")
        if scale and not m.group("pct"):
            v = v * Decimal(10) ** SCALE_WORDS[scale.lower()]
        out.append(Fig(-v if neg else v, neg, m.group(0).strip()))
    return out


def object_figures(claims: list[dict]) -> list[Fig]:
    out = []
    for c in claims:
        f = c.get("figure")
        if not f or f.get("value") is None:
            continue
        v = Decimal(str(f["value"]))
        unit = (f.get("unit") or "").lower()
        if unit in FIGURE_UNITS:
            v = v * Decimal(10) ** FIGURE_UNITS[unit]
        out.append(Fig(v, True, str(f)))
    return out


def answer_figures(answer: dict) -> tuple[list[Fig], bool]:
    """(figures in answer order, used the free-text fallback)."""
    objs = object_figures(answer.get("claims") or [])
    if objs:
        return objs, False
    return text_figures(answer.get("text") or ""), True


def _ref(printed: str, scale: int) -> Ref:
    s = printed.strip().removesuffix("%").strip()
    v = parse_number(s)
    places = len(s.split(".", 1)[1].rstrip(")").strip()) if "." in s else 0
    unit = Decimal(10) ** scale
    return Ref(v * unit, Decimal(1).scaleb(-places) * unit)


def reference_figures(item: dict) -> tuple[list[Ref] | None, str | None]:
    """(reference figures, exclusion reason). Comparison: [later, earlier, difference]."""
    qt, ref = item["question_type"], item["reference_answer"] or ""
    figs = [m for m in FIGURE.finditer(mask(ref))]
    if qt in ("xbrl_numeric", "comparison"):
        need = 1 if qt == "xbrl_numeric" else 3
        if len(figs) < need:
            raise ValueError(f"{item['item_id']}: reference has {len(figs)} figures, need {need}")
        out = []
        for m in figs[:need]:
            sc = m.group("scale")
            r = _ref(m.group("num"), 0 if m.group("pct") or not sc else SCALE_WORDS[sc.lower()])
            neg = bool(m.group("neg")) or bool(m.group("open") and m.group("close"))
            out.append(Ref(-r.value if neg else r.value, r.quantum))
        return out, None
    if qt == "table" and "kind:factual" in item["tags"]:
        if "unit_scale_unknown" in item["tags"]:
            return None, "unit_scale_unknown"
        scale = next((v for t, v in TAG_SCALES.items() if t in item["tags"]), None)
        if scale is None:
            raise ValueError(f"{item['item_id']}: no unit_scale tag")
        return [_ref(ref.strip().removeprefix("$").strip(), scale)], None
    return None, "not numeric"


def exact(a: Decimal, r: Ref) -> bool:
    return (abs(a) / r.quantum).quantize(Decimal(1), ROUND_HALF_UP) == abs(r.value) / r.quantum


def tolerant(a: Decimal, r: Ref) -> bool:
    if r.value == 0:
        return a == 0
    return abs(abs(a) - abs(r.value)) <= TOLERANCE * abs(r.value)


@dataclass
class ItemScore:
    item_id: str
    excluded: str | None = None
    correct: bool = False
    strict: bool = False
    tolerant: bool = False
    values_only: bool | None = None  # comparison items
    sign_agree: bool | None = None  # None when the matched figure states no sign
    figure_count: int = 0
    fallback: bool = False
    matched: list[str] = field(default_factory=list)


def score_item(item: dict, answer: dict) -> ItemScore:
    """`answer`: {"text", "claims" (PRD 7.4, may be empty), "abstained"}."""
    refs, why = reference_figures(item)
    s = ItemScore(item["item_id"], excluded=why)
    if refs is None:
        return s
    if answer.get("abstained"):
        return s  # in the denominator, not correct; zero words never count (F-09)
    figs, s.fallback = answer_figures(answer)
    if not figs and all(r.value == 0 for r in refs) and ZERO_WORDS.search(answer.get("text") or ""):
        figs = [Fig(Decimal(0), False, "zero word")]
    s.figure_count = len(figs)
    hits = [next((f for f in figs if exact(f.value, r)), None) for r in refs]
    s.correct = all(hits)
    s.matched = [h.text for h in hits if h]
    s.strict = len(figs) >= len(refs) and all(
        any(exact(f.value, r) for f in figs[: len(refs)]) for r in refs
    )
    s.tolerant = all(any(tolerant(f.value, r) for f in figs) for r in refs)
    if len(refs) == 3:
        s.values_only = all(any(exact(f.value, r) for f in figs) for r in refs[:2])
    signed = [(h, r) for h, r in zip(hits, refs, strict=True) if h and h.explicit_sign]
    if signed:
        s.sign_agree = all((h.value < 0) == (r.value < 0) for h, r in signed)
    return s


def aggregate(scores: list[ItemScore]) -> dict:
    scored = [s for s in scores if s.excluded is None]
    excluded: dict[str, int] = {}
    for s in scores:
        if s.excluded:
            excluded[s.excluded] = excluded.get(s.excluded, 0) + 1
    n = len(scored)
    rate = lambda xs: (sum(xs) / len(xs)) if xs else None  # noqa: E731
    comp = [s.values_only for s in scored if s.values_only is not None]
    signs = [s.sign_agree for s in scored if s.sign_agree is not None]
    return {
        "n": n,
        "excluded": excluded,
        "numeric_accuracy": rate([s.correct for s in scored]),
        "strict_first_figure": rate([s.strict for s in scored]),
        "tolerant_0_5pct": rate([s.tolerant for s in scored]),
        "comparison_values_only": rate(comp),
        "sign_agreement": rate(signs),
        "sign_agreement_n": len(signs),
        "fallback_used": sum(s.fallback for s in scored),
        "mean_figure_count": rate([s.figure_count for s in scored]),
    }
