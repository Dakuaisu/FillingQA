"""Query router and metadata filters (PRD 7.1).

The router is one small-tier model call with structured JSON output (PRD 7.1's
schema). Its entities, fiscal periods and form types become hard metadata
filters only when its confidence is at least `retrieval.filter_confidence_min`;
below it retrieval runs unfiltered. A filtered retrieval that returns nothing
falls back to unfiltered and is counted as a `filter_zero_recall` event.
"""

from __future__ import annotations

import json
import re

INTENTS = ("lookup", "comparison", "synthesis", "unsupported")
KEYS = {"intent", "entities", "fiscal_periods", "form_types", "sub_queries", "confidence"}
FORMS = {"10-K", "10-Q"}
PERIOD = re.compile(r"^(?:Q([1-4])\s*)?FY\s?(\d{4})$", re.I)
FENCE = re.compile(r"```(?:json)?\s*(.*?)\s*```", re.S)

PROMPT = """Route a question about SEC filings. The corpus holds 10-K and 10-Q filings of \
these companies only:
<<COMPANIES>>

Return only a JSON object, with no other text, with exactly these keys:
{"intent": one of "lookup", "comparison", "synthesis", "unsupported",
 "entities": [{"ticker": "...", "company_name": "..."}] for companies the question names,
 "fiscal_periods": ["FY2024"] or ["Q2 FY2025"] for the fiscal periods it names, else [],
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


def filters(route: dict, tickers: set[str], min_confidence: float) -> dict | None:
    """Hard filters {tickers, fiscal_years, fiscal_quarters, form_types}, or None when
    the confidence is below the minimum or nothing usable was extracted. Unknown
    tickers, unparseable periods and other forms are dropped, never guessed."""
    if route["confidence"] < min_confidence:
        return None
    tk = sorted({e.get("ticker", "").upper() for e in route["entities"]
                 if isinstance(e, dict)} & tickers)  # fmt: skip
    years, quarters = set(), set()
    for p in route["fiscal_periods"]:
        m = PERIOD.match(str(p).strip())
        if m:
            years.add(int(m.group(2)))
            if m.group(1):
                quarters.add(int(m.group(1)))
    forms = sorted({str(f).upper() for f in route["form_types"]} & FORMS)
    out = {"tickers": tk, "fiscal_years": sorted(years), "fiscal_quarters": sorted(quarters),
           "form_types": forms}  # fmt: skip
    return out if any(out.values()) else None


def allowed_chunks(meta: list[tuple[str, str, int, int | None, str]], f: dict) -> set[str]:
    """Chunk ids passing the filters; `meta` is (chunk_id, ticker, fiscal_year,
    fiscal_quarter, form_type) per chunk. An empty filter list does not restrict."""
    out = set()
    for cid, ticker, fy, fq, form in meta:
        if f["tickers"] and ticker not in f["tickers"]:
            continue
        if f["fiscal_years"] and fy not in f["fiscal_years"]:
            continue
        if f["fiscal_quarters"] and fq not in f["fiscal_quarters"]:
            continue
        if f["form_types"] and form not in f["form_types"]:
            continue
        out.add(cid)
    return out
