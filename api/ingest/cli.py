"""Ingestion entry point.

python -m api.ingest.cli --dev-slice
python -m api.ingest.cli --tickers COST,TGT,AAPL --years 1
"""

from __future__ import annotations

import argparse

from api.config import dev_slice
from api.db import connect
from api.ingest.edgar import EdgarClient
from api.ingest.filings import IngestReport, ingest_accessions, ingest_company
from api.ingest.xbrl_facts import FactsReport, load_companyfacts


def print_report(report: IngestReport) -> None:
    print(
        f"{report.ticker:5s} cik={report.cik} "
        f"discovered={report.discovered} "
        f"inserted={report.inserted} "
        f"already_present={report.already_present} "
        f"downloaded={report.downloaded_bytes / 1_048_576:.1f}MB"
        + (f" skipped_no_period={report.skipped_no_period}" if report.skipped_no_period else "")
    )


def print_facts(report: FactsReport) -> None:
    print(
        f"{report.ticker:5s} facts={report.facts} "
        f"linked_inserted={report.linked_inserted} linked_present={report.linked_present} "
        f"linked_accessions={report.linked_accessions} "
        f"unlinked_inserted={report.unlinked_inserted} unlinked_present={report.unlinked_present}"
    )


def ingest_facts(conn, client: EdgarClient, report: IngestReport) -> None:
    # After the filings rows exist, so this company's facts can link to them.
    facts = client.fetch_companyfacts(report.cik)
    print_facts(load_companyfacts(conn, report.ticker, report.cik, facts))


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest SEC filings.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--dev-slice", action="store_true", help="the accession list in api/config.yaml"
    )
    mode.add_argument("--tickers", help="comma-separated, e.g. COST,TGT,AAPL")
    parser.add_argument("--years", type=int, default=3, help="filing-date window, in years")
    args = parser.parse_args()

    with connect() as conn, EdgarClient() as client:
        if args.dev_slice:
            by_ticker: dict[str, dict[str, str]] = {}
            for entry in dev_slice():
                wanted = by_ticker.setdefault(entry["ticker"].upper(), {})
                wanted[entry["accession"]] = entry["form"]
            for ticker, wanted in by_ticker.items():
                report = ingest_accessions(conn, client, ticker, wanted)
                print_report(report)
                ingest_facts(conn, client, report)
            return

        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        for ticker in tickers:
            report = ingest_company(conn, client, ticker, years_back=args.years)
            print_report(report)
            ingest_facts(conn, client, report)


if __name__ == "__main__":
    main()
