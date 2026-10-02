"""Query router and metadata filters (PRD 7.1).

The router is one small-tier model call with structured JSON output (PRD 7.1's
schema). It extracts only what the question states: tickers, and each period as
the question words it. Code maps periods to stored metadata (`resolve_period`):
a date resolves through `filings.period_end` to that filing's own fiscal year
and quarter; an FY label is used literally; anything else is left unresolved,
never guessed (F-119). Filters apply only when the confidence is at least
`retrieval.filter_confidence_min`; below it retrieval runs unfiltered. A
filtered retrieval that returns nothing falls back to unfiltered and is counted
as a `filter_zero_recall` event.
"""

from __future__ import annotations

import contextlib
import json
import re
from datetime import date

INTENTS = ("lookup", "comparison", "synthesis", "unsupported")
KEYS = {"intent", "entities", "fiscal_periods", "form_types", "sub_queries", "confidence"}
FORMS = {"10-K", "10-Q"}
QUARTERS = {"first": 1, "second": 2, "third": 3, "fourth": 4}
LABEL = re.compile(
    r"^(?:(?:Q([1-4])|(first|second|third|fourth)\s+quarter(?:\s+of)?)\s*)?"
    r"(?:FY|fiscal(?:\s+year)?)\s*'?(\d{4})$", re.I)  # fmt: skip
_NAMES = ("january", "february", "march", "april", "may", "june", "july", "august",
          "september", "october", "november", "december")  # fmt: skip
MONTHS = {**{n: i for i, n in enumerate(_NAMES, 1)}, **{n[:3]: i for i, n in enumerate(_NAMES, 1)},
          "sept": 9}  # fmt: skip
DATE_TEXT = re.compile(r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2}),\s*(\d{4})\b")
DATE_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.S)

PROMPT = """Route a question about SEC filings. The corpus holds 10-K and 10-Q filings of \
these companies only:
<<COMPANIES>>

Return only a JSON object, with no other text, with exactly these keys:
{"intent": one of "lookup", "comparison", "synthesis", "unsupported",
 "entities": [{"ticker": "...", "company_name": "..."}] for companies the question names,
 "fiscal_periods": each period exactly as the question words it, copied verbatim, e.g.
   "January 25, 2026", "FY2025", "Q3 FY2024", "fiscal year ended January 31, 2026";
   never convert a date into a fiscal year; [] if it names none,
 "form_types": ["10-K"] or ["10-Q"] if it names or implies a form, else [],
 "sub_queries": [search queries; two for a comparison, else one],
 "confidence": a number from 0 to 1, how sure you are of the entities and periods}

Question: <<QUESTION>>
"""


class RouterParseError(ValueError):
    """The router's output is not PRD 7.1's JSON; recorded, never re-asked."""


def render(question: str, companies: dict[str, str]) -> str:
    listing = "\n".join(f"- {t}: {n}" for t, n in sorted(companies.items()))
    return PROMPT.replace("<<COMPANIES>>", listing).replace("<<QUESTION>>", question)


def parse(text: str) -> dict:
    m = FENCE.fullmatch(text.strip())
    s = m.group(1) if m else text.strip()
    try:
        doc = json.loads(s)
    except json.JSONDecodeError as e:
        raise RouterParseError(f"not JSON: {e.msg}") from e
    if not isinstance(doc, dict) or set(doc) != KEYS:
        raise RouterParseError(f"keys must be {sorted(KEYS)}")
    if doc["intent"] not in INTENTS:
        raise RouterParseError(f"intent {doc['intent']!r} not in {INTENTS}")
    c = doc["confidence"]
    if isinstance(c, bool) or not isinstance(c, (int, float)) or not 0 <= c <= 1:
        raise RouterParseError(f"confidence {c!r} not a number in [0, 1]")
    for k in ("entities", "fiscal_periods", "form_types", "sub_queries"):
        if not isinstance(doc[k], list):
            raise RouterParseError(f"{k} must be a list")
    return doc


def dates_in(text: str) -> list[date]:
    out = []
    for mon, day, year in DATE_TEXT.findall(text):
        m = MONTHS.get(mon.lower())
        if m:
            with contextlib.suppress(ValueError):
                out.append(date(int(year), m, int(day)))
    for y, m, d in DATE_ISO.findall(text):
        with contextlib.suppress(ValueError):
            out.append(date(int(y), int(m), int(d)))
    return out


PeriodEnds = list[tuple[str, date, int, int | None]]


def resolve_period(text: str, tickers: list[str], period_ends: PeriodEnds) -> list[list] | None:
    """[[fiscal_year, fiscal_quarter or None], ...] for one stated period, or None.
    A stated date (also inside "fiscal year ended <date>") resolves through the
    filings whose period_end it is, to their own fiscal year and quarter; the year
    written in the date is not used. Otherwise an FY label is taken literally.
    `period_ends` is (ticker, period_end, fiscal_year, fiscal_quarter) per filing."""
    found = dates_in(text)
    if found:
        hits = sorted({(fy, fq) for t, pe, fy, fq in period_ends
                       if pe in found and (not tickers or t in tickers) and fy is not None},
                      key=lambda x: (x[0], x[1] or 0))  # fmt: skip
        return [list(h) for h in hits] or None
    m = LABEL.match(str(text).strip())
    if not m:
        return None
    q = int(m.group(1)) if m.group(1) else QUARTERS.get((m.group(2) or "").lower())
    return [[int(m.group(3)), q]]


def filters(
    route: dict, tickers: set[str], min_confidence: float, period_ends: PeriodEnds
) -> dict | None:
    """Hard filters {tickers, periods, form_types, unresolved_periods}, or None when
    the confidence is below the minimum or nothing usable was extracted. Unknown
    tickers, unresolvable periods and other forms are dropped, never guessed."""
    if route["confidence"] < min_confidence:
        return None
    tk = sorted({e.get("ticker", "").upper() for e in route["entities"]
                 if isinstance(e, dict)} & tickers)  # fmt: skip
    periods, unresolved = [], []
    for p in route["fiscal_periods"]:
        r = resolve_period(str(p), tk, period_ends)
        if r is None:
            unresolved.append(str(p))
        else:
            periods += [x for x in r if x not in periods]
    forms = sorted({str(f).upper() for f in route["form_types"]} & FORMS)
    if not (tk or periods or forms):
        return None
    return {"tickers": tk, "periods": periods, "form_types": forms,
            "unresolved_periods": unresolved}  # fmt: skip


def allowed_chunks(meta: list[tuple[str, str, int, int | None, str]], f: dict) -> set[str]:
    """Chunk ids passing the filters; `meta` is (chunk_id, ticker, fiscal_year,
    fiscal_quarter, form_type) per chunk. An empty filter list does not restrict;
    a period with no quarter admits the whole fiscal year."""
    out = set()
    for cid, ticker, fy, fq, form in meta:
        if f["tickers"] and ticker not in f["tickers"]:
            continue
        if f["periods"] and not any(fy == y and (q is None or fq == q) for y, q in f["periods"]):
            continue
        if f["form_types"] and form not in f["form_types"]:
            continue
        out.add(cid)
    return out


PERIOD_ENDS_SQL = """
    SELECT c.ticker, f.period_end, f.fiscal_year, f.fiscal_quarter
      FROM filings f JOIN companies c USING (cik)
"""
