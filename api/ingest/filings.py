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

from api.config import ConfigError, companies, data_dir
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


def merge_pages(submissions: dict[str, Any], pages: dict[str, dict]) -> dict[str, Any]:
    """`submissions` with the named paginated files' rows appended to `recent`.

    `pages` maps a `filings.files` name to that file's columns. The merged
    payload lists only the files NOT merged under `filings.files`.
    """
    recent = submissions["filings"]["recent"]
    merged = {key: list(values) for key, values in recent.items()}
    for page in pages.values():
        for key in merged:
            merged[key].extend(page.get(key) or [None] * len(page["accessionNumber"]))
    remaining = [f for f in submissions["filings"].get("files") or [] if f.get("name") not in pages]
    return {**submissions, "filings": {"recent": merged, "files": remaining}}


def submissions_since(client: EdgarClient, cik: str, start: date) -> dict[str, Any]:
    """Submissions with paginated files merged until the data reaches `start`.

    Large filers outgrow `filings.recent` within a year -- JPM's covers only
    2025-10-01 onward, against 70 older files. Pages are listed newest first and
    read in that order until a page's own earliest filingDate predates `start`.
    The listing's `filingTo` is not used: it is not exact at the edges (JPM page
    020 says 2023-10-31 and holds a 2023-11-01 filing).
    """
    submissions = client.fetch_submissions(cik)
    pages: dict[str, dict] = {}
    if min(submissions["filings"]["recent"]["filingDate"], default="") >= start.isoformat():
        for f in submissions["filings"].get("files") or []:
            page = client.fetch_submissions_page(f["name"])
            pages[f["name"]] = page
            if min(page["filingDate"], default="") < start.isoformat():
                break
    merged = merge_pages(submissions, pages)
    # The loop above is the coverage guarantee: it stops only on data older than
    # `start` or on the last page. Unread pages are older still.
    merged["filings"]["files"] = []
    return merged


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
        return companies()[ticker.upper()]["sector"]
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

    # The pinned CIK, never a live ticker lookup: SEC's mapping moves (F-62).
    cik = companies()[ticker.upper()]["cik"]
    submissions = client.fetch_submissions(cik)
    recent = set(submissions["filings"]["recent"]["accessionNumber"])
    if not set(wanted) <= recent:
        # Older accessions live in paginated files, newest first. Read them in
        # order until every asked-for accession has been seen; select_accessions
        # still raises on any that never appears. Page metadata is not trusted
        # (see submissions_since).
        pages: dict[str, dict] = {}
        for f in submissions["filings"].get("files") or []:
            pages[f["name"]] = page = client.fetch_submissions_page(f["name"])
            recent |= set(page["accessionNumber"])
            if set(wanted) <= recent:
                break
        submissions = merge_pages(submissions, pages)
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
