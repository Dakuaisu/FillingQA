"""Phase 1 exit: the offsets check on STORED rows.

Reads every xbrl_spans row back from Postgres, slices the file at its filing's
norm_path by [char_start:char_end], and compares to raw_text. Unlike
`verify_spans`, nothing here comes from the in-memory parse: if the text on disk
and the rows in the database have drifted apart, this is where it shows.

python -m scripts.check_stored_spans
"""

from __future__ import annotations

from pathlib import Path

from api.db import connect


def main() -> None:
    with connect() as conn:
        filings = conn.execute(
            """
            SELECT c.ticker, f.accession, f.norm_path
              FROM filings f JOIN companies c USING (cik)
             ORDER BY c.ticker, f.filing_date
            """
        ).fetchall()
        print(f"{'ticker':6} {'accession':22} {'rows':>5} {'mismatch':>8} {'out_of_range':>12}")
        total_rows = total_bad = 0
        for ticker, accession, norm_path in filings:
            text = Path(norm_path).read_text(encoding="utf-8")
            rows = conn.execute(
                "SELECT char_start, char_end, raw_text FROM xbrl_spans WHERE accession = %s",
                (accession,),
            ).fetchall()
            out_of_range = sum(1 for s, e, _ in rows if not 0 <= s < e <= len(text))
            mismatch = sum(1 for s, e, raw in rows if text[s:e] != raw)
            total_rows += len(rows)
            total_bad += mismatch
            print(f"{ticker:6} {accession:22} {len(rows):5} {mismatch:8} {out_of_range:12}")
        print(f"total rows {total_rows}, mismatches {total_bad}")


if __name__ == "__main__":
    main()
