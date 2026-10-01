"""Materialize the eval corpus's accession list, once (F-42).

python -m scripts.materialize_corpus --as-of 2026-10-01

PRD 4.4 defines the corpus as a 3-year filing-date window. A window evaluated at
run time makes the corpus a function of the run date, so it is evaluated here,
once, at an explicit as-of date, and the result -- not the window -- is committed
under `corpus.filings` in api/config.yaml. Ingest reads that list and nothing
else (TRADEOFFS, "Every corpus is an accession list").

Selection is the dev slice's rule: exact form match on 10-K and 10-Q (no
amendments), filed within [as_of - 3 years, as_of], reportDate present. Each
company's filings come from its pinned `cik` (F-62), not a ticker lookup; the
live lookup is printed only to report where SEC's mapping now differs.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import date

from api.config import companies
from api.ingest.edgar import EdgarClient
from api.ingest.filings import FORM_TYPES, discover, submissions_since

YEARS = 3  # PRD 4.4; used here once, never at ingest


def window_start(as_of: date, years_back: int) -> date:
    """First filing_date in the window. Lives here: nothing at ingest reads a window."""
    try:
        return as_of.replace(year=as_of.year - years_back)
    except ValueError:
        # 29 February in a non-leap target year.
        return as_of.replace(month=2, day=28, year=as_of.year - years_back)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", required=True, type=date.fromisoformat)
    args = parser.parse_args()
    start = window_start(args.as_of, YEARS)

    entries, skipped = [], 0
    with EdgarClient() as client:
        for ticker, company in companies().items():
            cik = company["cik"]
            live = client.resolve_cik(ticker)
            if live != cik:
                print(f"# {ticker}: pinned cik {cik}, SEC's ticker map now says {live}")
            found, no_period = discover(
                submissions_since(client, cik, start), cik, start, FORM_TYPES
            )
            skipped += no_period
            entries += [
                {
                    "ticker": ticker,
                    "accession": f.accession,
                    "form": f.form_type,
                    "period_end": f.period_end.isoformat(),
                    "filed": f.filing_date.isoformat(),
                }
                for f in found
                if f.filing_date <= args.as_of
            ]

    duplicates = [a for a, n in Counter(e["accession"] for e in entries).items() if n > 1]
    if duplicates:
        raise SystemExit(f"accessions listed more than once: {duplicates}")

    print(f"# as_of {args.as_of}, window start {start}, {len(entries)} filings, "
          f"{skipped} skipped for no reportDate")  # fmt: skip
    for e in entries:
        print(
            f"    - {{ticker: {e['ticker']}, accession: {e['accession']}, form: {e['form']}, "
            f'period_end: "{e["period_end"]}", filed: "{e["filed"]}"}}'
        )


if __name__ == "__main__":
    main()
