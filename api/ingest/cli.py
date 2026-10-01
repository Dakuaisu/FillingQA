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


def print_report(report: IngestReport) -> None:
    print(
        f"{report.ticker:5s} cik={report.cik} "
        f"discovered={report.discovered} "
        f"inserted={report.inserted} "
        f"already_present={report.already_present} "
        f"downloaded={report.downloaded_bytes / 1_048_576:.1f}MB"
        + (f" skipped_no_period={report.skipped_no_period}" if report.skipped_no_period else "")
    )


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
                print_report(ingest_accessions(conn, client, ticker, wanted))
            return

        tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
        for ticker in tickers:
            print_report(ingest_company(conn, client, ticker, years_back=args.years))


if __name__ == "__main__":
    main()
