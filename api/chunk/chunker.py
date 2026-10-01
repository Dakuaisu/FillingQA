"""Structure-aware chunker: PRD 6.3.

Rules, in PRD priority order, and how each is held:

1. A table is never split -- unless it alone exceeds the budget, and then only
   by row groups, each part repeating the context line and column labels.
2. A chunk never crosses a section boundary: chunks are built per Item.
3. Every chunk starts with a context header naming company, form, fiscal label
   and Item.
4. Prose is packed to the target size with overlap at paragraph boundaries;
   a paragraph larger than the budget is split at sentence boundaries.
5. Tables get their own chunks and are never merged with prose. A prose run also
   ends at every data table, so no prose chunk's offsets span a table.

Layout tables (F-35) are not data, but some carry prose -- audit matters, the
cybersecurity oversight table (F-46) -- so they chunk as prose. Page furniture
(running headers, footers, page numbers) is dropped (PRD 6.2 step 4).

Blocks before the first Item -- cover page and table of contents -- belong to no
Item and are not chunked; they are counted in ChunkStats.

Token counting is injected: unit counts without special tokens, and each final
chunk's `token_count` as the model's sequence length, special tokens included.
A chunk over `max_seq_length` is counted in ChunkStats, never truncated (F-53).
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field

from api.chunk.context import DocumentMeta, chunk_header, table_lines
from api.parse.ixbrl import ExtractedDocument
from api.parse.sections import Section
from api.parse.tables import Table

CountTokens = Callable[[str], int]

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z(“\"])")


@dataclass
class Chunk:
    chunk_id: str
    accession: str
    cik: str
    ticker: str
    form_type: str
    fiscal_year: int
    fiscal_quarter: int | None
    item_code: str  # part-qualified on a 10-Q ("I.1"), plain on a 10-K ("1A")
    section_title: str
    chunk_type: str  # 'prose' | 'table'
    text: str  # with context header
    raw_text: str  # without it, for display
    token_count: int
    char_start: int
    char_end: int
    unit_scale: str | None = None

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()


@dataclass
class ChunkStats:
    blocks_before_first_item: int = 0
    furniture_dropped: int = 0
    layout_as_prose: int = 0
    tables_split: int = 0
    over_max_seq_length: int = 0
    headerless_tables: int = 0
    paragraphs_split: int = 0
    furniture_samples: Counter = field(default_factory=Counter)


@dataclass
class _Unit:
    """A piece of prose: a whole block, or one sentence group of an oversized one."""

    block: int
    piece: int
    text: str
    char_start: int
    char_end: int
    tokens: int


def _normalize(text: str) -> str:
    return re.sub(r"\d+", "#", " ".join(text.split()))


def furniture_keys(texts: list[str], min_repeats: int) -> set[str]:
    """Digit-normalized texts that repeat at least `min_repeats` times and do not
    end like a sentence.

    Measured on the 10-Ks: page footers repeat 58-80 times, "Table of Contents"
    69, bare page numbers 68; real content repeats at most 8 ("Apple Inc."), and
    the repeated content that matters -- "None.", "Not applicable.", "See
    accompanying Notes..." -- ends in a full stop, which is why the punctuation
    test exists.
    """
    counts = Counter(_normalize(t) for t in texts)
    return {
        key
        for key, n in counts.items()
        if n >= min_repeats and not key.rstrip().endswith((".", ":"))
    }


def split_sentences(text: str) -> list[str]:
    return [s for s in _SENTENCE_END.split(text) if s.strip()]


def chunk_document(
    doc: ExtractedDocument,
    meta: DocumentMeta,
    sections: list[Section],
    tables: list[Table],
    count_tokens: CountTokens,
    config: dict,
    *,
    sequence_length: CountTokens | None = None,
    max_seq_length: int | None = None,
) -> tuple[list[Chunk], ChunkStats]:
    """`count_tokens` counts pieces; `sequence_length` gives a final chunk's real
    model input length (defaults to `count_tokens`)."""
    seq = sequence_length or count_tokens
    special = seq("") - count_tokens("")
    target = config["target_tokens"] - special
    overlap = int(target * config["overlap_pct"])
    stats = ChunkStats()
    table_at = {t.block.char_start: t for t in tables}

    def text_of(i: int) -> str:
        b = doc.blocks[i]
        return " ".join(doc.text[b.char_start : b.char_end].split())

    candidates = [
        i
        for i, b in enumerate(doc.blocks)
        if not (b.kind == "table" and table_at[b.char_start].kind == "data")
    ]
    furniture = furniture_keys([text_of(i) for i in candidates], config["furniture_min_repeats"])

    stats.blocks_before_first_item = sections[0].block_start if sections else len(doc.blocks)
    chunks: list[Chunk] = []

    for section in sections:
        header = chunk_header(meta, section)
        run: list[_Unit] = []

        # The budget covers the whole embedded text, header included.
        budget = target - count_tokens(header)

        for i in range(section.block_start, section.block_end):
            block = doc.blocks[i]
            table = table_at.get(block.char_start) if block.kind == "table" else None
            if table is not None and table.kind == "data":
                chunks.extend(_pack_prose(run, header, meta, section, budget, overlap))
                run = []
                chunks.extend(
                    _table_chunks(i, table, header, meta, section, count_tokens, target, stats)
                )
                continue

            text = text_of(i)
            if not text:
                continue
            if _normalize(text) in furniture:
                stats.furniture_dropped += 1
                stats.furniture_samples[_normalize(text)[:60]] += 1
                continue
            if table is not None:
                stats.layout_as_prose += 1

            tokens = count_tokens(text)
            if tokens <= budget:
                run.append(_Unit(i, 0, text, block.char_start, block.char_end, tokens))
                continue
            # A paragraph over budget is split at sentence boundaries, never inside
            # a sentence. Sentence pieces share the block's offsets: sub-block
            # offsets would need a second coordinate system.
            stats.paragraphs_split += 1
            for n, piece in enumerate(_group(split_sentences(text), count_tokens, budget)):
                run.append(
                    _Unit(i, n, piece, block.char_start, block.char_end, count_tokens(piece))
                )
        chunks.extend(_pack_prose(run, header, meta, section, budget, overlap))

    for chunk in chunks:
        chunk.token_count = seq(chunk.text)
        if max_seq_length is not None and chunk.token_count > max_seq_length:
            stats.over_max_seq_length += 1
    return chunks, stats


def _group(sentences: list[str], count_tokens: CountTokens, target: int) -> list[str]:
    pieces: list[str] = []
    current: list[str] = []
    for sentence in sentences:
        candidate = " ".join([*current, sentence])
        if current and count_tokens(candidate) > target:
            pieces.append(" ".join(current))
            current = [sentence]
        else:
            current.append(sentence)
    if current:
        pieces.append(" ".join(current))
    return pieces


def _pack_prose(
    units: list[_Unit],
    header: str,
    meta: DocumentMeta,
    section: Section,
    target: int,
    overlap: int,
) -> list[Chunk]:
    """Greedy packing to `target`, carrying trailing units up to `overlap` tokens
    into the next chunk. Overlap is whole units only -- paragraph or sentence
    boundaries, never mid-sentence (PRD 6.3 rule 4)."""
    chunks: list[Chunk] = []
    start = 0
    while start < len(units):
        end, used = start, 0
        while end < len(units) and (end == start or used + units[end].tokens <= target):
            used += units[end].tokens
            end += 1
        chunks.append(_prose_chunk(units[start:end], header, meta, section))
        if end >= len(units):
            break
        back, carried = end, 0
        while back - 1 > start and carried + units[back - 1].tokens <= overlap:
            back -= 1
            carried += units[back].tokens
        start = back
    return chunks


def _prose_chunk(units: list[_Unit], header: str, meta: DocumentMeta, section: Section) -> Chunk:
    first, last = units[0], units[-1]
    raw = "\n".join(u.text for u in units)
    return _chunk(
        meta,
        section,
        chunk_id=f"{meta.accession}:{first.block}.{first.piece}:{last.block}.{last.piece}",
        chunk_type="prose",
        header=header,
        raw=raw,
        char_start=first.char_start,
        char_end=last.char_end,
    )


def _table_chunks(
    index: int,
    table: Table,
    header: str,
    meta: DocumentMeta,
    section: Section,
    count_tokens: CountTokens,
    target: int,
    stats: ChunkStats,
) -> list[Chunk]:
    if not any(table.columns):
        stats.headerless_tables += 1
    rows = list(range(len(table.body)))
    raw = "\n".join(table_lines(table, meta, section, table.body))
    groups = [rows]
    if count_tokens(f"{header}\n{raw}") > target and len(rows) > 1:
        stats.tables_split += 1
        groups = _row_groups(table, header, meta, section, count_tokens, target)

    chunks = []
    for n, group in enumerate(groups):
        raw = "\n".join(table_lines(table, meta, section, [table.body[i] for i in group]))
        # A part covers only its own rows, so an iXBRL span resolves to exactly
        # one part. The first part also covers the header rows and the last runs
        # to the table's end, so the parts tile the table with no gaps.
        start = table.block.char_start if n == 0 else table.body_offsets[group[0]][0]
        end = table.block.char_end if n == len(groups) - 1 else table.body_offsets[group[-1]][1]
        chunks.append(
            _chunk(
                meta,
                section,
                chunk_id=f"{meta.accession}:{index}.{n}:{index}.{n}",
                chunk_type="table",
                header=header,
                raw=raw,
                char_start=start,
                char_end=end,
                unit_scale=table.unit_scale,
            )
        )
    return chunks


def _row_groups(
    table: Table,
    header: str,
    meta: DocumentMeta,
    section: Section,
    count_tokens: CountTokens,
    target: int,
) -> list[list[int]]:
    """Split body rows so each part, header, context line and labels included,
    fits the target. Returns row indices into `table.body`."""
    groups: list[list[int]] = []
    current: list[int] = []
    for i in range(len(table.body)):
        candidate = [*current, i]
        lines = table_lines(table, meta, section, [table.body[r] for r in candidate])
        if current and count_tokens(header + "\n" + "\n".join(lines)) > target:
            groups.append(current)
            current = [i]
        else:
            current = candidate
    if current:
        groups.append(current)
    return groups


def _chunk(
    meta: DocumentMeta,
    section: Section,
    *,
    chunk_id: str,
    chunk_type: str,
    header: str,
    raw: str,
    char_start: int,
    char_end: int,
    unit_scale: str | None = None,
) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        accession=meta.accession,
        cik=meta.cik,
        ticker=meta.ticker,
        form_type=meta.form_type,
        fiscal_year=meta.fiscal_year,
        fiscal_quarter=meta.fiscal_quarter,
        item_code=section.qualified_code,
        section_title=section.title,
        chunk_type=chunk_type,
        text=f"{header}\n{raw}",
        raw_text=raw,
        token_count=0,  # set by chunk_document once the text is final
        char_start=char_start,
        char_end=char_end,
        unit_scale=unit_scale,
    )
