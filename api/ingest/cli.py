"""Ingestion entry point. Reads an accession list from api/config.yaml, never a window.

python -m api.ingest.cli --corpus      # the frozen eval corpus (F-42)
python -m api.ingest.cli --dev-slice   # the parser-development slice
"""

from __future__ import annotations

import argparse

from api.config import companies, corpus_filings, dev_slice
from api.db import connect
from api.ingest.edgar import EdgarClient
from api.ingest.filings import IngestReport, ingest_accessions
from api.ingest.xbrl_facts import FactsReport, load_companyfacts


def print_report(report: IngestReport) -> None:
    print(
        f"{report.ticker:5s} cik={report.cik} "
        f"discovered={report.discovered} "
        f"inserted={report.inserted} "
        f"already_present={report.already_present} "
        f"downloaded={report.downloaded_bytes / 1_048_576:.1f}MB"
    )


def print_facts(report: FactsReport, source: str) -> None:
    print(
        f"{report.ticker:5s} companyfacts={source} facts={report.facts} "
        f"linked_inserted={report.linked_inserted} linked_present={report.linked_present} "
        f"linked_accessions={report.linked_accessions} "
        f"unlinked_inserted={report.unlinked_inserted} unlinked_present={report.unlinked_present} "
        f"promoted={report.promoted}"
    )


def ingest_list(entries: list[dict[str, str]]) -> None:
    by_ticker: dict[str, list[dict[str, str]]] = {}
    for entry in entries:
        by_ticker.setdefault(entry["ticker"].upper(), []).append(entry)

    with connect() as conn, EdgarClient() as client:
        for ticker, rows in by_ticker.items():
            wanted = {r["accession"]: r["form"] for r in rows}
            report = ingest_accessions(conn, client, ticker, wanted)
            print_report(report)
            # After the filings rows exist, so facts can link to them. Each source
            # is stamped with the company's pinned CIK; facts link by accession.
            for source in companies()[ticker]["companyfacts_ciks"]:
                facts = client.fetch_companyfacts(source)
                print_facts(load_companyfacts(conn, ticker, report.cik, facts), source)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest SEC filings from an accession list.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--corpus", action="store_true", help="corpus.filings in api/config.yaml")
    mode.add_argument("--dev-slice", action="store_true", help="corpus.dev_slice")
    args = parser.parse_args()
    ingest_list(corpus_filings() if args.corpus else dev_slice())


if __name__ == "__main__":
    main()
