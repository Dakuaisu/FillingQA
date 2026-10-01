"""Write the corpus freeze record (F-42). Run once, at the end of Phase 2.

python -m scripts.write_freeze

Covers every accession in `corpus.filings`. For each: `(accession, text_sha256,
parser_version)` per F-42, plus status. A quarantined filing carries its reason
and finding ID; its normalized text hash is recorded too, so the verifier can
re-derive it like any other. Refuses to write if a stored normalized text
differs from a fresh parse -- the record must describe what the pipeline holds.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from datetime import date
from pathlib import Path

import yaml

from api.chunk.store import chunker_version
from api.config import REPO_ROOT, corpus_filings
from api.db import connect
from api.parse.ixbrl import extract
from api.parse.validate import parser_version

FREEZE_FILE = REPO_ROOT / "api" / "corpus_freeze.yaml"

# Why each quarantined filing is out. Keyed by ticker and form, because the
# reason is structural and identical across that company's 10-Ks.
QUARANTINE_FINDINGS = {
    ("JPM", "10-K"): "F-66",
    ("XOM", "10-K"): "F-70",
}


def main() -> None:
    version = parser_version()
    listed = corpus_filings()
    entries, counts = [], Counter()
    with connect() as conn:
        for item in listed:
            accession = item["accession"]
            status, error, raw_path, norm_path, stored = conn.execute(
                "SELECT parse_status, parse_error, raw_path, norm_path, parser_version "
                "FROM filings WHERE accession = %s",
                (accession,),
            ).fetchone()
            if stored != version:
                raise SystemExit(f"{accession}: parsed by {stored}, current {version}; re-validate")
            text = extract(Path(raw_path).read_bytes()).text
            stored_text = Path(norm_path).read_text(encoding="utf-8")
            if stored_text != text:
                raise SystemExit(f"{accession}: {norm_path} differs from a fresh parse")
            entry = {
                "accession": accession,
                "ticker": item["ticker"],
                "form": item["form"],
                "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "parser_version": version,
                "status": status,
            }
            if status != "parsed":
                entry["reason"] = error
                entry["finding"] = QUARANTINE_FINDINGS[(item["ticker"], item["form"])]
            entries.append(entry)
            counts[(item["ticker"], item["form"], status)] += 1

    per_ticker = {}
    for ticker in dict.fromkeys(e["ticker"] for e in entries):
        per_ticker[ticker] = {
            "10-K": {s: counts[(ticker, "10-K", s)] for s in ("parsed", "quarantined")},
            "10-Q": {s: counts[(ticker, "10-Q", s)] for s in ("parsed", "quarantined")},
        }
    record = {
        "frozen_on": date.today().isoformat(),
        "corpus_as_of": "2026-10-01",
        "parser_version": version,
        "chunker_version": chunker_version(),
        "notes": (
            "PRD 4.4 corpus, frozen at the end of Phase 2 (F-42); not to be re-ingested "
            "(PRD 11.4). Comparability is judged on text_sha256 under parser_version; a "
            "raw-byte hash difference alone is logged, not a failure (F-43). Known "
            "residual: one content block dropped as navigation, TGT 10-K Item 15's "
            "'Notes to Consolidated Financial Statements' list item (F-58). Verify with "
            "python -m scripts.verify_freeze."
        ),
        "totals": {
            "listed": len(entries),
            "parsed": sum(e["status"] == "parsed" for e in entries),
            "quarantined": sum(e["status"] != "parsed" for e in entries),
        },
        "per_ticker": per_ticker,
        "filings": entries,
    }
    FREEZE_FILE.write_text(yaml.safe_dump(record, sort_keys=False, width=100), encoding="utf-8")
    print(f"wrote {FREEZE_FILE.relative_to(REPO_ROOT)}: {record['totals']}")


if __name__ == "__main__":
    main()
