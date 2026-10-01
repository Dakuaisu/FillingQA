"""Write chunks to Postgres. Phase 2 step 1's persistence.

python -m api.chunk.store

Per filing, in one transaction: delete its chunks, insert the new ones. Deleting
sets the filing's `xbrl_spans.chunk_id` to NULL (ON DELETE SET NULL); spans are
re-resolved by `api.chunk.resolve`.

Chunks are offsets into the text at `filings.norm_path`, so a filing is chunked
only if a fresh parse reproduces that text exactly under the stored
`parser_version` -- otherwise the offsets would point into a different string.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import psycopg
import yaml

from api.chunk.chunker import Chunk, ChunkStats, chunk_document
from api.chunk.context import DocumentMeta
from api.chunk.tokens import count_tokens, sequence_length
from api.config import REPO_ROOT, chunking, embedding
from api.db import connect
from api.parse.ixbrl import extract
from api.parse.sections import detect_sections
from api.parse.tables import extract_tables
from api.parse.validate import parser_version

# Everything that shapes chunk output: the chunker's code, the vendored tokenizer
# and the `chunking:` config. This writer and the span resolver are excluded --
# they store and link chunks, and changing them does not change one.
CHUNKER_SOURCES = sorted(
    p
    for p in (REPO_ROOT / "api" / "chunk").iterdir()
    if p.is_file() and p.suffix in {".py", ".json"} and p.name not in {"store.py", "resolve.py"}
)


def chunker_version() -> str:
    digest = hashlib.sha256()
    for path in CHUNKER_SOURCES:
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    digest.update(yaml.safe_dump(chunking(), sort_keys=True).encode())
    return digest.hexdigest()[:12]


class StaleParseError(RuntimeError):
    """The stored normalized text is not what the current parser produces."""


_INSERT = """
    INSERT INTO chunks (
        chunk_id, accession, cik, ticker, form_type, fiscal_year, fiscal_quarter,
        item_code, section_title, chunk_type, text, raw_text, token_count,
        char_start, char_end, unit_scale, content_hash, chunker_version
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def _row(c: Chunk, version: str) -> tuple:
    return (
        c.chunk_id, c.accession, c.cik, c.ticker, c.form_type, c.fiscal_year,
        c.fiscal_quarter, c.item_code, c.section_title, c.chunk_type, c.text,
        c.raw_text, c.token_count, c.char_start, c.char_end, c.unit_scale,
        c.content_hash, version,
    )  # fmt: skip


def chunk_filing(
    conn: psycopg.Connection, filing: tuple, version: str
) -> tuple[list[Chunk], ChunkStats]:
    accession, cik, ticker, form, raw_path, norm_path, fiscal_year, period_end, stored = filing
    if stored != parser_version():
        raise StaleParseError(f"{accession}: parsed by {stored}; re-run api.parse.validate first")
    doc = extract(Path(raw_path).read_bytes())
    if Path(norm_path).read_text(encoding="utf-8") != doc.text:
        raise StaleParseError(f"{accession}: text at {norm_path} differs from a fresh parse")

    meta = DocumentMeta(
        accession, cik, ticker, doc.dei["dei:EntityRegistrantName"], form, fiscal_year,
        doc.fiscal_period, period_end,
    )  # fmt: skip
    chunks, stats = chunk_document(
        doc, meta, detect_sections(doc, form), extract_tables(doc), count_tokens, chunking(),
        sequence_length=sequence_length, max_seq_length=embedding()["max_seq_length"],
    )  # fmt: skip
    with conn.transaction():
        conn.execute("DELETE FROM chunks WHERE accession = %s", (accession,))
        with conn.cursor() as cur:
            cur.executemany(_INSERT, [_row(c, version) for c in chunks])
    return chunks, stats


def main() -> None:
    version = chunker_version()
    print(f"chunker_version {version}  parser_version {parser_version()}")
    with connect() as conn:
        filings = conn.execute(
            """
            SELECT f.accession, f.cik, c.ticker, f.form_type, f.raw_path, f.norm_path,
                   f.fiscal_year, f.period_end, f.parser_version
              FROM filings f JOIN companies c USING (cik)
             WHERE f.parse_status = 'parsed'
             ORDER BY c.ticker, f.filing_date
            """
        ).fetchall()
        conn.commit()  # so each filing's transaction below is a real one
        print(f"{'ticker':6} {'accession':22} {'chunks':>6} {'prose':>5} {'table':>5} {'>512':>4}")
        for filing in filings:
            chunks, stats = chunk_filing(conn, filing, version)
            prose = sum(c.chunk_type == "prose" for c in chunks)
            print(
                f"{filing[2]:6} {filing[0]:22} {len(chunks):6} {prose:5} "
                f"{len(chunks) - prose:5} {stats.over_max_seq_length:4}"
            )


if __name__ == "__main__":
    main()
