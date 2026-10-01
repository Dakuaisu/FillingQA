"""Tests for discovery, filtering and URL construction. No network, no database."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from api.config import dev_slice
from api.ingest.filings import (
    DiscoveredFiling,
    IngestError,
    assert_recent_covers_window,
    discover,
    select_accessions,
    window_start,
)


def submissions(rows, files=None):
    """Build a submissions payload from (accession, form, filed, report, doc) rows."""
    keys = ("accessionNumber", "form", "filingDate", "reportDate", "primaryDocument")
    recent = {k: [r[i] for r in rows] for i, k in enumerate(keys)}
    return {"filings": {"recent": recent, "files": files or []}}


ROWS = [
    ("0000320193-25-000001", "10-K", "2025-11-01", "2025-09-27", "aapl-20250927.htm"),
    ("0000320193-26-000002", "10-Q", "2026-02-01", "2025-12-27", "aapl-20251227.htm"),
    ("0000320193-26-000003", "10-Q", "2026-05-01", "2026-03-28", "aapl-20260328.htm"),
    ("0000320193-24-000009", "10-K", "2024-11-01", "2024-09-28", "aapl-20240928.htm"),
    ("0000320193-26-000004", "8-K", "2026-06-01", "2026-06-01", "ea0001.htm"),
    ("0000320193-26-000005", "4", "2026-06-02", "", "xslF345X05/doc4.xml"),
]


# ------------------------------------------------------------------ window


def test_window_start_subtracts_whole_years():
    assert window_start(date(2026, 8, 30), 1) == date(2025, 8, 30)
    assert window_start(date(2026, 8, 30), 3) == date(2023, 8, 30)


def test_window_start_handles_leap_day():
    assert window_start(date(2024, 2, 29), 1) == date(2023, 2, 28)


# ---------------------------------------------------------------- discover


def test_only_10k_and_10q_inside_the_window_are_selected():
    found, _ = discover(submissions(ROWS), "0000320193", date(2025, 8, 30))
    assert [f.accession for f in found] == [
        "0000320193-25-000001",
        "0000320193-26-000002",
        "0000320193-26-000003",
    ]


def test_forms_outside_the_set_are_dropped():
    found, _ = discover(submissions(ROWS), "0000320193", date(2020, 1, 1))
    assert {f.form_type for f in found} == {"10-K", "10-Q"}


def test_filings_older_than_the_window_are_dropped():
    found, _ = discover(submissions(ROWS), "0000320193", date(2025, 8, 30))
    assert all(f.filing_date >= date(2025, 8, 30) for f in found)


def test_period_end_comes_from_report_date_not_filing_date():
    found, _ = discover(submissions(ROWS), "0000320193", date(2025, 8, 30))
    tenk = next(f for f in found if f.form_type == "10-K")
    assert tenk.filing_date == date(2025, 11, 1)
    assert tenk.period_end == date(2025, 9, 27)  # the fiscal period, not the filing


def test_filings_without_a_report_date_are_skipped_not_defaulted():
    rows = [("0000320193-26-000006", "10-Q", "2026-06-01", "", "x.htm")]
    found, skipped = discover(submissions(rows), "0000320193", date(2025, 1, 1))
    assert found == []
    assert skipped == 1


def test_results_are_ordered_by_filing_date():
    found, _ = discover(submissions(ROWS), "0000320193", date(2020, 1, 1))
    assert [f.filing_date for f in found] == sorted(f.filing_date for f in found)


# --------------------------------------------------------------- cap check


def test_window_fully_inside_recent_passes():
    assert assert_recent_covers_window(submissions(ROWS), date(2024, 1, 1)) is None


def test_window_reaching_past_recent_raises_when_older_files_exist():
    payload = submissions(ROWS, files=[{"name": "CIK0000320193-submissions-001.json"}])
    with pytest.raises(IngestError, match=r"filings\.files"):
        assert_recent_covers_window(payload, date(2010, 1, 1))


def test_no_older_files_means_recent_is_the_whole_history():
    # An empty `files` list means nothing was paginated away, so a window that
    # predates the oldest entry is simply a company with a short history.
    assert assert_recent_covers_window(submissions(ROWS, files=[]), date(2010, 1, 1)) is None


def test_empty_recent_is_an_error():
    with pytest.raises(IngestError, match="no filings"):
        assert_recent_covers_window(submissions([]), date(2025, 1, 1))


# ------------------------------------------------------- accession lists


def test_select_accessions_returns_exactly_the_requested_filings():
    wanted = {"0000320193-26-000003": "10-Q", "0000320193-24-000009": "10-K"}
    found = select_accessions(submissions(ROWS), "0000320193", wanted)
    assert [f.accession for f in found] == ["0000320193-24-000009", "0000320193-26-000003"]
    assert found[1].period_end == date(2026, 3, 28)


def test_missing_accession_raises_rather_than_substituting():
    wanted = {"0000320193-26-000003": "10-Q", "0000320193-26-000099": "10-Q"}
    with pytest.raises(IngestError, match="0000320193-26-000099"):
        select_accessions(submissions(ROWS), "0000320193", wanted)


def test_form_disagreeing_with_sec_raises():
    with pytest.raises(IngestError, match="SEC says 10-K"):
        select_accessions(submissions(ROWS), "0000320193", {"0000320193-25-000001": "10-Q"})


def test_requested_accession_without_report_date_raises():
    with pytest.raises(IngestError, match="reportDate"):
        select_accessions(submissions(ROWS), "0000320193", {"0000320193-26-000005": "4"})


def test_dev_slice_is_twelve_unique_accessions():
    entries = dev_slice()
    assert len(entries) == 12
    assert len({e["accession"] for e in entries}) == 12
    assert {e["ticker"] for e in entries} == {"AAPL", "COST", "TGT"}


# ---------------------------------------------------------- urls and paths


def make_filing(document="aapl-20240928.htm"):
    return DiscoveredFiling(
        accession="0000320193-24-000123",
        cik="0000320193",
        form_type="10-K",
        filing_date=date(2024, 11, 1),
        period_end=date(2024, 9, 28),
        primary_document=document,
    )


def test_source_url_points_at_the_primary_document():
    url = make_filing().source_url
    assert url == (
        "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm"
    )


def test_source_url_is_not_the_full_submission_text_bundle():
    # The .txt dissemination file concatenates every exhibit and is far larger.
    assert not make_filing().source_url.endswith(".txt")


def test_archives_path_drops_cik_zero_padding():
    assert "/data/320193/" in make_filing().source_url


def test_raw_path_preserves_the_real_document_extension():
    root = Path("/data")
    assert make_filing("x.html").raw_path(root).suffix == ".html"
    assert make_filing("x.htm").raw_path(root).suffix == ".htm"


def test_raw_path_is_namespaced_by_cik_and_named_by_accession():
    path = make_filing().raw_path(Path("/data"))
    assert path.parent.name == "0000320193"
    assert path.stem == "0000320193-24-000123"
