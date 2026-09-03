"""Shared fixtures: real SEC filings, loaded from the committed gzip archives.

CLAUDE.md rule 2 -- fixtures are real filings, never synthetic ones. The manifest
records each one's accession, source URL and sha256 of the uncompressed bytes, and
`fixture_bytes` re-checks that hash on every load, so a corrupted or swapped
archive fails loudly instead of quietly changing what the tests assert against.
"""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

FIXTURE_DIR = Path(__file__).parent / "fixtures"
FILINGS_DIR = FIXTURE_DIR / "filings"
MANIFEST = FIXTURE_DIR / "manifest.json"


def load_manifest() -> dict[str, dict]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return {entry["accession"]: entry for entry in data["filings"]}


MANIFEST_BY_ACCESSION = load_manifest()

# Referenced by name in tests so a failure says which filing broke.
AAPL_10K = "0000320193-25-000079"
AAPL_10Q = "0000320193-26-000013"
TGT_10K = "0000027419-26-000016"


def fixture_bytes(accession: str) -> bytes:
    """Uncompressed filing bytes, verified against the manifest hash."""
    entry = MANIFEST_BY_ACCESSION[accession]
    raw = gzip.decompress((FILINGS_DIR / entry["file"]).read_bytes())
    actual = hashlib.sha256(raw).hexdigest()
    if actual != entry["sha256"]:
        raise AssertionError(
            f"fixture {accession} does not match the manifest hash: "
            f"expected {entry['sha256']}, got {actual}"
        )
    return raw


@pytest.fixture(scope="session")
def manifest() -> dict[str, dict]:
    return MANIFEST_BY_ACCESSION


@pytest.fixture(scope="session")
def aapl_10k() -> bytes:
    return fixture_bytes(AAPL_10K)


@pytest.fixture(scope="session")
def aapl_10q() -> bytes:
    return fixture_bytes(AAPL_10Q)


@pytest.fixture(scope="session")
def tgt_10k() -> bytes:
    return fixture_bytes(TGT_10K)
