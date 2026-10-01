"""Filing discovery, download and registration.

Discover -> filter -> store raw bytes -> record a row in `filings`. No parsing:
a stored filing sits at parse_status='pending', which is the work queue PRD 6.1
calls `enqueue_parse`. A separate queue would be infrastructure for its own sake
at this corpus size.

Idempotency is enforced at two layers, deliberately. The disk cache in
edgar.py stops the byte download; `ON CONFLICT (accession) DO NOTHING` stops the
row insert. Either alone would make a re-run cheap; both make it free and prove
it (PRD 6.1: "re-running ingestion must be a no-op").
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import psycopg

from api.config import ConfigError, data_dir, sectors
from api.ingest.edgar import EdgarClient

FORM_TYPES = ("10-K", "10-Q")

ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession_nodash}/{document}"


class IngestError(RuntimeError):
    """Ingestion cannot proceed without losing filings we were asked for."""


@dataclass(frozen=True)
class DiscoveredFiling:
    """One filing selected for ingestion, before it has been downloaded."""

    accession: str
    cik: str
    form_type: str
    filing_date: date
    period_end: date
    primary_document: str

    @property
    def accession_nodash(self) -> str:
        return self.accession.replace("-", "")

    @property
    def source_url(self) -> str:
        return ARCHIVES_URL.format(
            # The Archives path uses the CIK without zero padding.
            cik=int(self.cik),
            accession_nodash=self.accession_nodash,
            document=self.primary_document,
        )

    def raw_path(self, root: Path) -> Path:
        # Keep the real extension rather than assuming .htm, so the file on disk
        # never claims a format it does not have.
        suffix = Path(self.primary_document).suffix or ".htm"
        return root / "raw" / self.cik / f"{self.accession}{suffix}"


@dataclass
class IngestReport:
    ticker: str
    cik: str
    discovered: int = 0
    inserted: int = 0
    already_present: int = 0
    skipped_no_period: int = 0
    downloaded_bytes: int = 0


def window_start(today: date, years_back: int) -> date:
    """First filing_date included in the ingestion window."""
    try:
        return today.replace(year=today.year - years_back)
    except ValueError:
        # 29 February in a non-leap target year.
        return today.replace(month=2, day=28, year=today.year - years_back)


def assert_recent_covers_window(submissions: dict[str, Any], start: date) -> None:
    """Fail if part of the requested window lives outside `filings.recent`.

    `filings.recent` holds only the most recent slice of a company's history --
    roughly the last thousand filings -- and anything older is paginated into the
    files listed under `filings.files`. For eight large-cap companies over three
    years this never overflows, but "never overflows" is an assumption about data
    we do not control, and the failure mode is silent: filings simply go missing
    from the corpus and every recall metric computed afterwards is quietly wrong.

    So it is asserted, not assumed. If it ever fires, the fix is to also read the
    files named in `filings.files`.
    """
    recent = submissions["filings"]["recent"]
    dates = recent.get("filingDate") or []
    older_files = submissions["filings"].get("files") or []

    if not dates:
        raise IngestError("submissions.filings.recent contains no filings")

    oldest = min(dates)
    if oldest > start.isoformat() and older_files:
        raise IngestError(
            f"filings.recent only reaches back to {oldest}, but the requested "
            f"window starts {start.isoformat()}, and {len(older_files)} older "
            f"file(s) are listed in filings.files. Part of the window is not in "
            f"`recent` and would be silently dropped. Read the paginated files: "
            f"{[f.get('name') for f in older_files]}"
        )


def discover(
    submissions: dict[str, Any],
    cik: str,
    start: date,
    forms: tuple[str, ...] = FORM_TYPES,
) -> tuple[list[DiscoveredFiling], int]:
    """Select filings of the given forms filed on or after `start`.

    Returns the selected filings and a count of those dropped for having no
    reportDate (period_end is NOT NULL and must not be invented).
    """
    recent = submissions["filings"]["recent"]
    columns = ("accessionNumber", "form", "filingDate", "reportDate", "primaryDocument")
    rows = zip(*(recent[c] for c in columns), strict=True)

    selected: list[DiscoveredFiling] = []
    skipped_no_period = 0

    for accession, form, filed, report, document in rows:
        if form not in forms:
            continue
        if filed < start.isoformat():
            continue
        if not report:
            # Without a period of report there is no period_end, and deriving one
            # would be exactly the guesswork TRADEOFFS finding #5 rejected.
            skipped_no_period += 1
            continue

        selected.append(
            DiscoveredFiling(
                accession=accession,
                cik=cik,
                form_type=form,
                filing_date=date.fromisoformat(filed),
                period_end=date.fromisoformat(report),
                primary_document=document,
            )
        )

    selected.sort(key=lambda f: (f.filing_date, f.accession))
    return selected, skipped_no_period


def select_accessions(
    submissions: dict[str, Any],
    cik: str,
    wanted: dict[str, str],
) -> list[DiscoveredFiling]:
    """Select exactly the requested accessions; `wanted` maps accession -> form.

    Raises on any accession absent from `filings.recent`, and on a form that
    disagrees with SEC's. Never substitutes a nearby filing: a silent swap would
    change the corpus without changing its definition.
    """
    recent = submissions["filings"]["recent"]
    columns = ("accessionNumber", "form", "filingDate", "reportDate", "primaryDocument")
    by_accession = {row[0]: row for row in zip(*(recent[c] for c in columns), strict=True)}

    missing = sorted(a for a in wanted if a not in by_accession)
    if missing:
        older = [f.get("name") for f in submissions["filings"].get("files") or []]
        raise IngestError(
            f"CIK {cik}: accession(s) {missing} not found in filings.recent "
            f"(paginated files not searched: {older})"
        )

    selected: list[DiscoveredFiling] = []
    for accession, expected_form in wanted.items():
        _, form, filed, report, document = by_accession[accession]
        if form != expected_form:
            raise IngestError(f"{accession}: config says {expected_form}, SEC says {form}")
        if not report:
            raise IngestError(f"{accession}: no reportDate, so period_end cannot be set")
        selected.append(
            DiscoveredFiling(
                accession=accession,
                cik=cik,
                form_type=form,
                filing_date=date.fromisoformat(filed),
                period_end=date.fromisoformat(report),
                primary_document=document,
            )
        )

    selected.sort(key=lambda f: (f.filing_date, f.accession))
    return selected


def sector_of(ticker: str) -> str:
    """Fails rather than leaving NULL: an unlabelled company is a config error."""
    try:
        return sectors()[ticker.upper()]
    except KeyError:
        raise ConfigError(f"{ticker} has no sector in api/config.yaml") from None


def upsert_company(
    conn: psycopg.Connection, cik: str, ticker: str, submissions: dict, sector: str
) -> None:
    """Register the company.

    `sector` is our corpus-design label from api/config.yaml (PRD 4.4: four
    sectors, two confusable pairs), not SEC data; `sic_code` carries SEC's own
    classification alongside it, unmodified.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO companies (cik, ticker, name, sic_code, sector)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (cik) DO UPDATE
                SET ticker = EXCLUDED.ticker,
                    name = EXCLUDED.name,
                    sic_code = EXCLUDED.sic_code,
                    sector = EXCLUDED.sector
            """,
            (cik, ticker.upper(), submissions["name"], submissions.get("sic") or None, sector),
        )


def record_filing(
    conn: psycopg.Connection,
    filing: DiscoveredFiling,
    raw_path: Path,
    content_hash: str,
) -> bool:
    """Insert the filings row. Returns True if a new row was created.

    fiscal_year and fiscal_quarter are deliberately absent: they are NULL until
    parsing reads dei:DocumentFiscalYearFocus. See TRADEOFFS finding #5.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO filings (
                accession, cik, form_type, filing_date, period_end,
                source_url, raw_path, content_hash
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (accession) DO NOTHING
            RETURNING accession
            """,
            (
                filing.accession,
                filing.cik,
                filing.form_type,
                filing.filing_date,
                filing.period_end,
                filing.source_url,
                str(raw_path),
                content_hash,
            ),
        )
        return cur.fetchone() is not None


def ingest_company(
    conn: psycopg.Connection,
    client: EdgarClient,
    ticker: str,
    *,
    years_back: int = 3,
    today: date | None = None,
    root: Path | None = None,
) -> IngestReport:
    """Discover, download and register one company's filings."""
    root = root if root is not None else data_dir()
    start = window_start(today or date.today(), years_back)

    cik = client.resolve_cik(ticker)
    submissions = client.fetch_submissions(cik)
    assert_recent_covers_window(submissions, start)

    upsert_company(conn, cik, ticker, submissions, sector_of(ticker))
    filings, skipped = discover(submissions, cik, start)

    report = IngestReport(
        ticker=ticker.upper(),
        cik=cik,
        discovered=len(filings),
        skipped_no_period=skipped,
    )
    _store(conn, client, filings, root, report)
    return report


def ingest_accessions(
    conn: psycopg.Connection,
    client: EdgarClient,
    ticker: str,
    wanted: dict[str, str],
    *,
    root: Path | None = None,
) -> IngestReport:
    """Download and register exactly the given accessions for one company."""
    root = root if root is not None else data_dir()

    cik = client.resolve_cik(ticker)
    submissions = client.fetch_submissions(cik)
    filings = select_accessions(submissions, cik, wanted)

    upsert_company(conn, cik, ticker, submissions, sector_of(ticker))
    report = IngestReport(ticker=ticker.upper(), cik=cik, discovered=len(filings))
    _store(conn, client, filings, root, report)
    return report


def _store(
    conn: psycopg.Connection,
    client: EdgarClient,
    filings: list[DiscoveredFiling],
    root: Path,
    report: IngestReport,
) -> None:
    for filing in filings:
        path = filing.raw_path(root)
        existed = path.exists()

        # The primary document, not the .txt dissemination bundle: that bundle
        # concatenates every exhibit in the submission and is far larger, and
        # nothing downstream reads the exhibits.
        body = client.download_document(filing.source_url, path)

        if not existed:
            report.downloaded_bytes += len(body)

        content_hash = hashlib.sha256(body).hexdigest()
        if record_filing(conn, filing, path, content_hash):
            report.inserted += 1
        else:
            report.already_present += 1

    conn.commit()
