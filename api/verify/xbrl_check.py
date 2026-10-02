"""Runtime XBRL validation of figure claims (PRD 6.5.4, 7.5).

Decisions in TRADEOFFS ("runtime XBRL validation"). The core (`concept_tags`,
`period_ends_for`, `classify`) is pure; `XbrlIndex` loads facts once per company.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

import yaml

from api.query.router import LABEL, QUARTERS, dates_in

WORD = re.compile(r"[^a-z0-9&()\- ]+")


def norm(text: str) -> str:
    t = WORD.sub(" ", (text or "").lower().replace(",", " ").replace("'", ""))
    return re.sub(r"\s+", " ", t).strip()


def load_concepts(concepts_path, synonyms_path) -> dict[str, list[str]]:
    """normalized phrase -> candidate tags (line item's tag and variant)."""
    with open(concepts_path, encoding="utf-8") as fh:
        items = yaml.safe_load(fh)["line_items"]
    with open(synonyms_path, encoding="utf-8") as fh:
        syn = yaml.safe_load(fh)
    out: dict[str, list[str]] = {}
    for it in items:
        tags = [t for t in (it["tag"], it.get("variant")) if t]
        for phrase in [it["label"], it["id"].replace("_", " "), *syn.get(it["id"], [])]:
            out[norm(phrase)] = tags
    return out


def concept_tags(concept: str | None, phrases: dict[str, list[str]]) -> list[str]:
    return phrases.get(norm(concept or ""), [])


def period_ends_for(period: str | None, ticker: str,
                    filings: list[tuple[str, date, int, int | None]]) -> list[date]:  # fmt: skip
    """A stated date is the period end; an FY / quarter label is the period end of
    the filer's own filing for it (FY and Q4: the 10-K). `filings` is (ticker,
    period_end, fiscal_year, fiscal_quarter)."""
    text = (period or "").strip()
    found = dates_in(text)
    if found:
        return sorted(set(found))
    m = LABEL.match(text)
    if not m:
        return []
    fy = int(m.group(3))
    q = int(m.group(1)) if m.group(1) else QUARTERS.get((m.group(2) or "").lower())
    q = None if q == 4 else q
    return sorted({pe for t, pe, y, fq in filings if t == ticker and y == fy and fq == q})


def within(a: Decimal, b: Decimal, tol_pct: float) -> bool:
    a, b = abs(a), abs(b)
    if b == 0:
        return a == 0
    return abs(a - b) / b * 100 <= Decimal(str(tol_pct))


def classify(magnitude: Decimal, cited: set[str], period_ends: list[date],
             facts: list[tuple[str, date, Decimal]], tol_pct: float) -> dict:  # fmt: skip
    """`facts`: (accession, period_end, value) for the company and the concept's
    tags, every filing. Status verified | restatement | contradiction | no_fact,
    with `period_ok` true / false / None."""
    at_period = [f for f in facts if f[1] in period_ends]
    in_cited = [f for f in at_period if f[0] in cited]
    hit = next((f for f in in_cited if within(magnitude, f[2], tol_pct)), None)
    if hit:
        return {"status": "verified", "accession": hit[0], "fact_value": str(hit[2]),
                "period_ok": True}  # fmt: skip
    if not in_cited:
        return {"status": "no_fact", "period_ok": None}
    other = next((f for f in at_period if f[0] not in cited and within(magnitude, f[2], tol_pct)),
                 None)  # fmt: skip
    if other:
        cited_values = sorted({str(f[2]) for f in in_cited})
        return {"status": "restatement", "accession": other[0], "fact_value": str(other[2]),
                "cited_values": cited_values, "period_ok": True}  # fmt: skip
    wrong_period = any(
        f[0] in cited and f[1] not in period_ends and within(magnitude, f[2], tol_pct)
        for f in facts
    )
    return {"status": "contradiction", "cited_values": sorted({str(f[2]) for f in in_cited}),
            "period_ok": False if wrong_period else None}  # fmt: skip


class XbrlIndex:
    """Facts by (cik, tag), loaded on first use."""

    def __init__(self, conn):
        self.conn = conn
        self.cache: dict[tuple[str, str], list[tuple[str, date, Decimal]]] = {}
        self.cik = dict(conn.execute("SELECT ticker, cik FROM companies").fetchall())

    def facts(self, ticker: str, tags: list[str]) -> list[tuple[str, date, Decimal]]:
        out = []
        for tag in tags:
            key = (self.cik[ticker], tag)
            if key not in self.cache:
                self.cache[key] = [tuple(r) for r in self.conn.execute(
                    "SELECT accession, period_end, value FROM xbrl_facts "
                    "WHERE cik = %s AND concept = %s", key).fetchall()]  # fmt: skip
            out += self.cache[key]
        return out
