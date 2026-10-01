"""Chunker structure (PRD 6.3) on the committed fixture filings.

Structure tests inject a whitespace word counter -- they test section boundaries,
table atomicity and headers, not size. Size tests at the end use the pinned bge
tokenizer (F-53), the same counts the embedding model will see.
"""

from __future__ import annotations

import itertools
import re
from datetime import date

import pytest

from api.chunk.chunker import chunk_document, furniture_keys, split_sentences
from api.chunk.context import DocumentMeta
from api.chunk.tokens import count_tokens, sequence_length
from api.config import chunking, embedding
from api.parse.ixbrl import extract
from api.parse.sections import detect_sections
from api.parse.tables import extract_tables
from tests.conftest import AAPL_10K, AAPL_10Q, TGT_10K, fixture_bytes


def words(text: str) -> int:
    return len(text.split())


FIXTURES = {
    AAPL_10K: ("AAPL", "0000320193", "10-K", 2025, date(2025, 9, 27)),
    AAPL_10Q: ("AAPL", "0000320193", "10-Q", 2026, date(2026, 3, 28)),
    TGT_10K: ("TGT", "0000027419", "10-K", 2025, date(2026, 1, 31)),
}


@pytest.fixture(scope="module", params=list(FIXTURES))
def chunked(request):
    accession = request.param
    ticker, cik, form, fy, period_end = FIXTURES[accession]
    doc = extract(fixture_bytes(accession))
    meta = DocumentMeta(
        accession, cik, ticker, doc.dei["dei:EntityRegistrantName"], form, fy,
        doc.fiscal_period, period_end,
    )  # fmt: skip
    sections = detect_sections(doc, form)
    tables = extract_tables(doc)
    chunks, stats = chunk_document(doc, meta, sections, tables, words, chunking())
    return doc, meta, sections, tables, chunks, stats


def test_chunk_ids_are_unique(chunked):
    chunks = chunked[4]
    assert len({c.chunk_id for c in chunks}) == len(chunks)


def test_every_chunk_starts_with_its_context_header(chunked):
    _, meta, _, _, chunks, _ = chunked
    for c in chunks:
        header = c.text.splitlines()[0]
        assert header.startswith(f"[{meta.company_name} ({meta.ticker}) | {meta.form_type} | ")
        assert meta.period_label in header
        assert c.text == f"{header}\n{c.raw_text}"


def test_no_chunk_crosses_a_section_boundary(chunked):
    _, _, sections, _, chunks, _ = chunked
    for c in chunks:
        owners = [s for s in sections if s.char_start <= c.char_start and c.char_end <= s.char_end]
        assert len(owners) == 1, c.chunk_id
        assert owners[0].qualified_code == c.item_code


def test_nothing_before_the_first_item_is_chunked(chunked):
    _, _, sections, _, chunks, stats = chunked
    assert stats.blocks_before_first_item == sections[0].block_start > 0
    assert min(c.char_start for c in chunks) >= sections[0].char_start


def test_every_data_table_in_an_item_is_a_table_chunk_and_never_prose(chunked):
    _, _, sections, tables, chunks, _ = chunked
    data = [t for t in tables if t.kind == "data" and t.block.char_start >= sections[0].char_start]
    table_chunks = [c for c in chunks if c.chunk_type == "table"]
    for t in data:
        parts = [
            c
            for c in table_chunks
            if t.block.char_start <= c.char_start and c.char_end <= t.block.char_end
        ]
        assert parts, t.title
        assert min(c.char_start for c in parts) == t.block.char_start
        assert max(c.char_end for c in parts) == t.block.char_end
    for c in chunks:
        if c.chunk_type == "prose":
            for t in data:
                assert c.char_end <= t.block.char_start or c.char_start >= t.block.char_end


def test_headerless_tables_get_no_label_line(chunked):
    """F-50 residual: a table with no printed labels gets no label line at all,
    so a "|---|" separator only ever follows a label line with text in it."""
    for c in chunked[4]:
        if c.chunk_type != "table":
            continue
        lines = c.raw_text.splitlines()
        assert lines[0].startswith("[Table")
        for above, line in itertools.pairwise(lines):
            if line.startswith("|---"):
                assert above.replace("|", "").strip(), c.chunk_id


def test_layout_tables_with_prose_are_kept(chunked):
    """F-46: AAPL's critical audit matter table is a layout table with real prose."""
    _, meta, _, _, chunks, stats = chunked
    if meta.accession == AAPL_10K:
        prose = "\n".join(c.raw_text for c in chunks if c.chunk_type == "prose")
        assert "We tested controls relating to the evaluation of uncertain tax positions" in prose
    assert stats.layout_as_prose > 0


def test_page_furniture_is_dropped(chunked):
    # Footers end "<company> ... Form 10-K ... <page>": "Apple Inc. | 2025 Form
    # 10-K | 55", "TARGET CORPORATION 2025 Form 10-K 8". The signature block
    # "TARGET CORPORATION By: /s/ ..." is content and must survive.
    footer = re.compile(r"Form 10-[KQ]\s*\|?\s*\d+$")
    _, _, _, _, chunks, stats = chunked
    assert stats.furniture_dropped > 0
    for c in chunks:
        if c.chunk_type == "prose":
            assert not any(footer.search(line) for line in c.raw_text.splitlines()), c.chunk_id


def test_furniture_keys_keep_repeated_sentences():
    texts = ["Apple Inc. | 2025 Form 10-K | 1", "Apple Inc. | 2025 Form 10-K | 2"] * 3
    texts += ["Not applicable."] * 6 + ["None."] * 4
    keys = furniture_keys(texts, min_repeats=5)
    assert keys == {"Apple Inc. | # Form #-K | #"}


def test_split_sentences_keeps_every_word():
    text = "Revenue rose. Margins fell (as expected). “Quoted” start. U.S. sales grew."
    pieces = split_sentences(text)
    assert " ".join(pieces).split() == text.split()
    assert len(pieces) >= 3


# ------------------------------------------------- size, with the real tokenizer


@pytest.fixture(scope="module", params=list(FIXTURES))
def tokenized(request):
    accession = request.param
    ticker, cik, form, fy, period_end = FIXTURES[accession]
    doc = extract(fixture_bytes(accession))
    meta = DocumentMeta(
        accession, cik, ticker, doc.dei["dei:EntityRegistrantName"], form, fy,
        doc.fiscal_period, period_end,
    )  # fmt: skip
    tables = extract_tables(doc)
    chunks, stats = chunk_document(
        doc, meta, detect_sections(doc, form), tables, count_tokens, chunking(),
        sequence_length=sequence_length, max_seq_length=embedding()["max_seq_length"],
    )  # fmt: skip
    return doc, meta, tables, chunks, stats


# Over-limit chunks per fixture. TGT's 10-K had two (its exhibit index) until the
# sentence splitter learned that a sentence may start with a digit (F-56).
OVER_LIMIT = {AAPL_10K: 0, AAPL_10Q: 0, TGT_10K: 0}


def test_chunks_fit_the_budget_or_are_counted(tokenized):
    """Every chunk, prose and table, fits the target as a real sequence length,
    except single units that cannot be split -- and those are counted, never
    truncated."""
    _, meta, _, chunks, stats = tokenized
    target, limit = chunking()["target_tokens"], embedding()["max_seq_length"]
    over = [c for c in chunks if c.token_count > limit]
    assert len(over) == stats.over_max_seq_length == OVER_LIMIT[meta.accession]
    for c in chunks:
        if c in over:
            assert len(split_sentences(c.raw_text)) == 1, c.chunk_id
        else:
            assert c.token_count <= target, (c.chunk_id, c.token_count)


def test_token_count_is_the_real_sequence_length(tokenized):
    for c in tokenized[3][:20]:
        assert c.token_count == sequence_length(c.text)


def test_split_table_parts_tile_their_table(tokenized):
    """Parts take offsets from their own rows, so every iXBRL span in a split
    table resolves to exactly one part (Phase 3 gold labels)."""
    doc, _, tables, chunks, stats = tokenized
    by_start = {t.block.char_start: t for t in tables}
    parts: dict[int, list] = {}
    for c in chunks:
        if c.chunk_type == "table":
            parts.setdefault(int(c.chunk_id.split(":")[1].split(".")[0]), []).append(c)
    split = {b: cs for b, cs in parts.items() if len(cs) > 1}
    assert len(split) == stats.tables_split
    for block_index, cs in split.items():
        table = by_start[doc.blocks[block_index].char_start]
        assert cs[0].char_start == table.block.char_start
        assert cs[-1].char_end == table.block.char_end
        for a, b in itertools.pairwise(cs):
            assert a.char_end <= b.char_start
        for span in doc.spans:
            if table.block.char_start <= span.char_start < table.block.char_end:
                owners = [c for c in cs if c.char_start <= span.char_start < c.char_end]
                assert len(owners) <= 1, span.raw_text
        labels = {c.raw_text.splitlines()[1] for c in cs if any(table.columns)}
        assert len(labels) <= 1  # the same label line repeated in every part


def test_aapl_10k_statements_split_at_this_budget():
    doc = extract(fixture_bytes(AAPL_10K))
    meta = DocumentMeta(AAPL_10K, "0000320193", "AAPL", "Apple Inc.", "10-K", 2025, "FY",
                        date(2025, 9, 27))  # fmt: skip
    _, stats = chunk_document(
        doc, meta, detect_sections(doc, "10-K"), extract_tables(doc), count_tokens, chunking(),
        sequence_length=sequence_length,
    )  # fmt: skip
    assert stats.tables_split == 9


def test_a_sentence_may_start_with_a_digit():
    # TGT 10-K exhibit index, verbatim (F-56).
    text = (
        "(filed as Exhibit 4.1 to Target’s Current Report on Form 8-K on May 1, 2007, and "  # noqa: RUF001
        "incorporated herein by reference). 4.2 Description of Securities (filed as Exhibit "
        "(4)D to Target's Annual Report on Form 10-K for the year ended January 30, 2021, and "
        "incorporated herein by reference). 10.1 * Target Corporation"
    )
    pieces = split_sentences(text)
    assert [p.split()[0] for p in pieces] == ["(filed", "4.2", "10.1"]
    assert "Exhibit 4.1 to" in pieces[0]  # no split inside "4.1" -- no whitespace there


# ------------------------------------------------------------- F-54 navigation


def test_anchors_sit_inside_their_block():
    doc = extract(fixture_bytes(TGT_10K))
    anchors = [(b, a) for b in doc.blocks for a in b.anchors]
    assert len(anchors) == 405  # every in-document link in TGT's 10-K, as measured
    for block, anchor in anchors:
        assert block.char_start <= anchor.char_start < anchor.char_end <= block.char_end
        assert anchor.target and not anchor.target.startswith("#")


def test_running_headers_are_navigation_and_cross_references_are_not(tokenized):
    _, meta, _, chunks, stats = tokenized
    prose = "\n".join(c.raw_text for c in chunks if c.chunk_type == "prose")
    assert "Table of Contents" not in prose  # F-54: no nav residue left in prose
    if meta.accession == TGT_10K:
        # 26 blocks, keyed on the shared {Table of Contents, Index} link targets;
        # includes Item 15's "•Notes to Consolidated Financial Statements" list
        # item, which shares the Notes link target and has no full stop (F-58).
        assert stats.navigation_dropped == 26
        # The rarer running headers: those repeated 5+ times with identical text
        # ("RISK FACTORS ...", 10x) are already furniture, which runs first.
        assert stats.nav_samples["CYBERSECURITY"] == 2
        assert stats.nav_samples["PROPERTIES"] == 1
        assert stats.nav_samples["•"] == 1
        # A hyperlinked sentence ends in "." and survives the furniture guard.
        assert "See accompanying Notes to Consolidated Financial Statements." in prose
    else:
        assert stats.navigation_dropped == 0
