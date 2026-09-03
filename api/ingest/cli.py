"""Ingestion entry point.

python -m api.ingest.cli --tickers COST,TGT,AAPL --years 1
"""

from __future__ import annotations

import argparse

from api.db import connect
from api.ingest.edgar import EdgarClient
from api.ingest.filings import ingest_company


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest SEC filings for the given tickers.")
    parser.add_argument("--tickers", required=True, help="comma-separated, e.g. COST,TGT,AAPL")
    parser.add_argument("--years", type=int, default=3, help="filing-date window, in years")
    args = parser.parse_args()

    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]

    with connect() as conn, EdgarClient() as client:
        for ticker in tickers:
            report = ingest_company(conn, client, ticker, years_back=args.years)
            print(
                f"{report.ticker:5s} cik={report.cik} "
                f"discovered={report.discovered} "
                f"inserted={report.inserted} "
                f"already_present={report.already_present} "
                f"downloaded={report.downloaded_bytes / 1_048_576:.1f}MB"
                + (
                    f" skipped_no_period={report.skipped_no_period}"
                    if report.skipped_no_period
                    else ""
                )
            )


if __name__ == "__main__":
    main()
