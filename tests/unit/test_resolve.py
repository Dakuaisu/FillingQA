"""Span -> chunk resolution (Phase 2 step 2)."""

from __future__ import annotations

from datetime import date

from api.chunk.chunker import chunk_document
from api.chunk.context import DocumentMeta
from api.chunk.resolve import resolve
from api.chunk.store import chunker_version
from api.chunk.tokens import count_tokens, sequence_length
from api.config import chunking
from api.parse.ixbrl import extract
from api.parse.sections import detect_sections
from api.parse.tables import extract_tables
from api.parse.validate import span_rows
from tests.conftest import AAPL_10K, fixture_bytes


def test_categories_on_plain_ranges():
    # (span_id, start, end) against (chunk_id, start, end). Ranges, not filings.
    chunks = [("a", 100, 200), ("b", 180, 300), ("p0", 400, 500), ("p1", 400, 500)]
    spans = [(1, 50, 60), (2, 120, 130), (3, 185, 190), (4, 450, 460), (5, 350, 360)]
    assigned, r = resolve(spans, chunks)
    assert r.before_first_item == 1  # span 1 precedes every chunk
    assert r.unique == 1 and assigned[2] == "a"
    assert r.overlap == 1 and assigned[3] == "a"  # earliest chunk wins
    assert r.split_paragraph == 1 and assigned[4] == "p0"
    assert r.unresolved_in_item == 1  # span 5 falls between chunks
    assert 5 not in assigned and 1 not in assigned


def test_aapl_10k_spans_resolve_into_chunks_that_contain_them():
    doc = extract(fixture_bytes(AAPL_10K))
    meta = DocumentMeta(AAPL_10K, "0000320193", "AAPL", "Apple Inc.", "10-K", 2025, "FY",
                        date(2025, 9, 27))  # fmt: skip
    chunks, _ = chunk_document(
        doc, meta, detect_sections(doc, "10-K"), extract_tables(doc), count_tokens, chunking(),
        sequence_length=sequence_length,
    )  # fmt: skip
    rows = span_rows(doc, AAPL_10K)
    spans = [(i, row[6], row[7]) for i, row in enumerate(rows)]
    assigned, r = resolve(spans, [(c.chunk_id, c.char_start, c.char_end) for c in chunks])
    # As measured on the stored rows: 962 spans, 2 dei cover facts before Item 1.
    assert (r.spans, r.before_first_item, r.unresolved_in_item) == (962, 2, 0)
    assert r.resolved == 960
    by_id = {c.chunk_id: c for c in chunks}
    for span_id, chunk_id in assigned.items():
        assert rows[span_id][5] in by_id[chunk_id].raw_text


def test_chunker_version_is_stable_and_short():
    assert chunker_version() == chunker_version()
    assert len(chunker_version()) == 12
