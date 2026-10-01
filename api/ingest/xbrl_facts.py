"""companyfacts ingestion: PRD 6.5.

companyfacts is every fact a company has ever tagged, across every filing. Each
fact is stored against the accession that reported it (PRD 6.5.2 Trap 1), in
base units exactly as SEC reports them (Trap 2: documents print scaled values,
companyfacts does not -- nothing is scaled here).

Facts from a filing in `filings` go to `xbrl_facts`; the rest -- older years,
8-Ks, proxy statements -- go to `xbrl_facts_unlinked`, kept for restatement
detection (TRADEOFFS finding #3).
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any

import psycopg

from api.ingest.filings import IngestError

FactKey = tuple[str, str, date | None, date, str | None, str]


@dataclass(frozen=True)
class Fact:
    cik: str
    accession: str
    concept: str  # 'us-gaap:InventoryNet' -- same form as an ix:nonFraction `name`
    label: str | None
    value: Decimal  # base units, as reported
    unit: str
    period_start: date | None  # None for instant (balance-sheet) facts
    period_end: date
    fiscal_year: int | None
    fiscal_period: str | None
    form_type: str

    @property
    def key(self) -> FactKey:
        """The table's unique key. period_start is in it: TRADEOFFS finding #1."""
        return (
            self.accession,
            self.concept,
            self.period_start,
            self.period_end,
            self.fiscal_period,
            self.unit,
        )


@dataclass
class FactsReport:
    ticker: str
    facts: int = 0
    linked_inserted: int = 0
    linked_present: int = 0
    unlinked_inserted: int = 0
    unlinked_present: int = 0
    linked_accessions: int = 0
    promoted: int = 0  # staged unlinked rows removed because their filing joined the corpus


def flatten(companyfacts: dict[str, Any], cik: str) -> list[Fact]:
    """One Fact per entry under facts/{taxonomy}/{concept}/units/{unit}."""
    facts = []
    for taxonomy, concepts in companyfacts["facts"].items():
        for name, body in concepts.items():
            for unit, rows in body["units"].items():
                for row in rows:
                    facts.append(
                        Fact(
                            cik=cik,
                            accession=row["accn"],
                            concept=f"{taxonomy}:{name}",
                            label=body.get("label"),
                            # Through str: an int stays exact, and a value parsed
                            # as Decimal is unchanged. A float would not be.
                            value=Decimal(str(row["val"])),
                            unit=unit,
                            period_start=_date(row.get("start")),
                            period_end=date.fromisoformat(row["end"]),
                            fiscal_year=row.get("fy"),
                            fiscal_period=row.get("fp"),
                            form_type=row["form"],
                        )
                    )
    return facts


def _date(raw: str | None) -> date | None:
    return date.fromisoformat(raw) if raw else None


def conflicts(pairs: Iterable[tuple[Any, Decimal]]) -> dict[Any, set[Decimal]]:
    """Keys seen with more than one distinct value.

    The whole point of the key is that it identifies one fact. Two values under
    one key means either the key is wrong (finding #1 was exactly this) or the
    source changed; either way, keeping one silently is the bug Trap 1 warns of.
    """
    seen: dict[Any, set[Decimal]] = defaultdict(set)
    for key, value in pairs:
        seen[key].add(value)
    return {k: v for k, v in seen.items() if len(v) > 1}


def is_comparative(fact_period_end: date, filing_period_end: date) -> bool:
    """A fact describing a period that ended before the filing's own period.

    The prior-year column of a 10-K, or last year-end's balance in a 10-Q.
    """
    return fact_period_end < filing_period_end


_LINKED_INSERT = """
    INSERT INTO xbrl_facts (
        cik, accession, concept, label, value, unit, period_start, period_end,
        fiscal_year, fiscal_period, form_type, is_comparative
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT ON CONSTRAINT xbrl_facts_key DO NOTHING
"""

_UNLINKED_INSERT = """
    INSERT INTO xbrl_facts_unlinked (
        cik, accession, concept, label, value, unit, period_start, period_end,
        fiscal_year, fiscal_period, form_type
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT ON CONSTRAINT xbrl_facts_unlinked_key DO NOTHING
"""


def _existing(conn: psycopg.Connection, table: str, cik: str) -> dict[FactKey, Decimal]:
    rows = conn.execute(
        f"SELECT accession, concept, period_start, period_end, fiscal_period, unit, value "
        f"FROM {table} WHERE cik = %s",
        (cik,),
    ).fetchall()
    return {tuple(r[:6]): r[6] for r in rows}


def load_companyfacts(
    conn: psycopg.Connection, ticker: str, cik: str, companyfacts: dict[str, Any]
) -> FactsReport:
    facts = flatten(companyfacts, cik)
    report = FactsReport(ticker=ticker.upper(), facts=len(facts))

    clashing = conflicts((f.key, f.value) for f in facts)
    if clashing:
        sample = next(iter(clashing.items()))
        raise IngestError(f"{ticker}: {len(clashing)} fact key(s) carry two values, e.g. {sample}")

    period_end_of = dict(
        conn.execute("SELECT accession, period_end FROM filings WHERE cik = %s", (cik,)).fetchall()
    )
    linked = [f for f in facts if f.accession in period_end_of]
    unlinked = [f for f in facts if f.accession not in period_end_of]
    report.linked_accessions = len({f.accession for f in linked})

    # A re-run must be a no-op. If companyfacts has since changed a value we
    # already stored, ON CONFLICT DO NOTHING would hide it, so check first.
    # Linked facts are also checked against xbrl_facts_unlinked: a filing added
    # to the corpus after its facts were staged there must not carry a changed
    # value across the move.
    checks = (("xbrl_facts", linked), ("xbrl_facts_unlinked", unlinked + linked))
    for table, group in checks:
        stored = _existing(conn, table, cik)
        drift = [f for f in group if f.key in stored and stored[f.key] != f.value]
        if drift:
            raise IngestError(
                f"{ticker}: {len(drift)} stored fact(s) in {table} now carry a different "
                f"value in companyfacts, e.g. {drift[0]} (stored {stored[drift[0].key]})"
            )

    before = _counts(conn, cik)
    with conn.transaction(), conn.cursor() as cur:
        cur.executemany(
            _LINKED_INSERT,
            [
                (
                    *_columns(f),
                    is_comparative(f.period_end, period_end_of[f.accession]),
                )
                for f in linked
            ],
        )
        cur.executemany(_UNLINKED_INSERT, [_columns(f) for f in unlinked])
        # Promote: facts staged as unlinked whose filing is now in `filings`
        # live in xbrl_facts from here on, never in both tables.
        cur.execute(
            """
            DELETE FROM xbrl_facts_unlinked u
             USING filings f
             WHERE u.accession = f.accession AND u.cik = %s
            """,
            (cik,),
        )
        report.promoted = cur.rowcount
    after = _counts(conn, cik)
    conn.commit()

    report.linked_inserted = after[0] - before[0]
    report.linked_present = len(linked) - report.linked_inserted
    report.unlinked_inserted = after[1] - before[1] + report.promoted
    report.unlinked_present = len(unlinked) - report.unlinked_inserted
    return report


def _columns(f: Fact) -> tuple:
    return (
        f.cik,
        f.accession,
        f.concept,
        f.label,
        f.value,
        f.unit,
        f.period_start,
        f.period_end,
        f.fiscal_year,
        f.fiscal_period,
        f.form_type,
    )


def _counts(conn: psycopg.Connection, cik: str) -> tuple[int, int]:
    linked = conn.execute("SELECT count(*) FROM xbrl_facts WHERE cik = %s", (cik,)).fetchone()
    unlinked = conn.execute(
        "SELECT count(*) FROM xbrl_facts_unlinked WHERE cik = %s", (cik,)
    ).fetchone()
    return linked[0], unlinked[0]
