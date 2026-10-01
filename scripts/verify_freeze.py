"""Re-derive text_sha256 for every frozen accession and fail on any difference.

python -m scripts.verify_freeze

Reads api/corpus_freeze.yaml, re-parses each filing's raw document from disk, and
compares the normalized text's sha256 with the frozen value. A different
`parser_version` is reported first: under a new parser, a text change may be the
parser's, which the F-42 rule treats differently from the filing's.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml

from api.db import connect
from api.parse.ixbrl import extract
from api.parse.validate import parser_version
from scripts.write_freeze import FREEZE_FILE


def main() -> int:
    record = yaml.safe_load(FREEZE_FILE.read_text(encoding="utf-8"))
    current = parser_version()
    if current != record["parser_version"]:
        print(f"parser_version {current} != frozen {record['parser_version']}")
    failures = []
    with connect() as conn:
        for entry in record["filings"]:
            raw_path = conn.execute(
                "SELECT raw_path FROM filings WHERE accession = %s", (entry["accession"],)
            ).fetchone()[0]
            text = extract(Path(raw_path).read_bytes()).text
            digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
            if digest != entry["text_sha256"]:
                failures.append(entry["accession"])
                print(f"MISMATCH {entry['accession']}: {digest} != {entry['text_sha256']}")
    print(f"verified {len(record['filings'])} frozen accessions; mismatches {len(failures)}")
    return 1 if failures or current != record["parser_version"] else 0


if __name__ == "__main__":
    sys.exit(main())
