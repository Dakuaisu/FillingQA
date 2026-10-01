"""Materialize the eval corpus's accession list, once (F-42).

python -m scripts.materialize_corpus --as-of 2026-10-01

PRD 4.4 defines the corpus as a 3-year filing-date window. A window evaluated at
run time makes the corpus a function of the run date, so it is evaluated here,
once, at an explicit as-of date, and the result -- not the window -- is committed
under `corpus.filings` in api/config.yaml. Ingest reads that list and nothing
else (TRADEOFFS, "Every corpus is an accession list").

Selection is the dev slice's rule: exact form match on 10-K and 10-Q (no
amendments), filed within [as_of - 3 years, as_of], reportDate present.
"""

from __future__ import annotations

import argparse
from datetime import date

import yaml

from api.config import CORPUS_FILE
from api.ingest.edgar import EdgarClient
from api.ingest.filings import FORM_TYPES, discover, submissions_since, window_start

YEARS = 3  # PRD 4.4; used here once, never at ingest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--as-of", required=True, type=date.fromisoformat)
    args = parser.parse_args()
    start = window_start(args.as_of, YEARS)

    tickers = [c["ticker"] for c in yaml.safe_load(CORPUS_FILE.read_text())["corpus"]["companies"]]
    entries, skipped = [], 0
    with EdgarClient() as client:
        for ticker in tickers:
            cik = client.resolve_cik(ticker)
            submissions = submissions_since(client, cik, start)
            found, no_period = discover(submissions, cik, start, FORM_TYPES)
            skipped += no_period
            for f in found:
                if f.filing_date > args.as_of:
                    continue
                entries.append(
                    {
                        "ticker": ticker,
                        "accession": f.accession,
                        "form": f.form_type,
                        "period_end": f.period_end.isoformat(),
                        "filed": f.filing_date.isoformat(),
                    }
                )
    print(f"# as_of {args.as_of}, window start {start}, {len(entries)} filings, "
          f"{skipped} skipped for no reportDate")  # fmt: skip
    for e in entries:
        print(
            f"    - {{ticker: {e['ticker']}, accession: {e['accession']}, form: {e['form']}, "
            f"period_end: {e['period_end']}, filed: {e['filed']}}}"
        )


if __name__ == "__main__":
    main()
