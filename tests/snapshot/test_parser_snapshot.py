"""Snapshot tests for parser output against committed real filings (PRD 15).

The snapshot is a compact *summary* rather than the full extraction: section
list, block and span counts, context resolution, fiscal labels, and the text
hash. A dump of 200k characters would be diffable but not readable, and a
baseline nobody can read is a baseline nobody checks.

Every value here was hand-verified against the filing before the snapshot was
committed -- see docs/TRADEOFFS.md, "A blessed snapshot is only a test if the
baseline was verified".
"""

from __future__ import annotations

import itertools

from api.parse.ixbrl import extract
from api.parse.sections import detect_sections, missing_required
from tests.conftest import AAPL_10K, AAPL_10Q, TGT_10K, fixture_bytes


def parse_summary(raw: bytes, form_type: str) -> dict:
    doc = extract(raw)
    sections = detect_sections(doc, form_type)
    numeric = [s for s in doc.spans if s.is_numeric]
    resolved = sum(
        1 for s in numeric if (c := doc.contexts.get(s.context_ref)) is not None and c.resolves
    )
    dimensional = sum(
        1
        for s in numeric
        if (c := doc.contexts.get(s.context_ref)) is not None and c.is_dimensional
    )
    return {
        "text_chars": len(doc.text),
        "text_sha256": doc.text_sha256,
        "blocks_total": len(doc.blocks),
        "blocks_table": sum(1 for b in doc.blocks if b.kind == "table"),
        "blocks_paragraph": sum(1 for b in doc.blocks if b.kind == "paragraph"),
        "spans_total": len(doc.spans),
        "spans_numeric": len(numeric),
        "spans_unparsed": doc.unparsed_values,
        "contexts": len(doc.contexts),
        "contextref_resolved": resolved,
        "contextref_dimensional": dimensional,
        "fiscal_year": doc.fiscal_year,
        "fiscal_period": doc.fiscal_period,
        "missing_required_items": missing_required(sections, form_type),
        "sections": [
            {
                "code": s.qualified_code,
                "title": s.title,
                "chars": s.char_end - s.char_start,
            }
            for s in sections
        ],
    }


def test_aapl_10k_snapshot(snapshot):
    assert parse_summary(fixture_bytes(AAPL_10K), "10-K") == snapshot


def test_aapl_10q_snapshot(snapshot):
    assert parse_summary(fixture_bytes(AAPL_10Q), "10-Q") == snapshot


def test_tgt_10k_snapshot(snapshot):
    assert parse_summary(fixture_bytes(TGT_10K), "10-K") == snapshot


# --- invariants that must hold regardless of what the snapshot happens to say ---


def test_every_span_slices_back_to_its_own_text():
    """The load-bearing invariant. If this fails, every offset is meaningless."""
    from api.parse.ixbrl import verify_spans

    for accession in (AAPL_10K, AAPL_10Q, TGT_10K):
        doc = extract(fixture_bytes(accession))
        assert verify_spans(doc) == [], f"{accession} has spans whose offsets do not slice back"


def test_spans_lie_within_the_normalized_text():
    for accession in (AAPL_10K, AAPL_10Q, TGT_10K):
        doc = extract(fixture_bytes(accession))
        for span in doc.spans:
            assert 0 <= span.char_start < span.char_end <= len(doc.text)


def test_blocks_are_ordered_and_non_overlapping():
    for accession in (AAPL_10K, AAPL_10Q, TGT_10K):
        doc = extract(fixture_bytes(accession))
        for prev, nxt in itertools.pairwise(doc.blocks):
            assert prev.char_end <= nxt.char_start, f"{accession}: blocks overlap"


def test_sections_tile_the_document_in_order():
    for accession, form in ((AAPL_10K, "10-K"), (AAPL_10Q, "10-Q"), (TGT_10K, "10-K")):
        doc = extract(fixture_bytes(accession))
        sections = detect_sections(doc, form)
        assert sections, f"{accession} yielded no sections"
        for prev, nxt in itertools.pairwise(sections):
            assert prev.char_start < nxt.char_start
            assert prev.char_end <= nxt.char_start


def test_tenq_part_qualification_disambiguates_item_one():
    """Part I Item 1 is Financial Statements; Part II Item 1 is Legal Proceedings."""
    doc = extract(fixture_bytes(AAPL_10Q))
    codes = {s.qualified_code: s.title for s in detect_sections(doc, "10-Q")}
    assert "I.1" in codes and "II.1" in codes
    assert codes["I.1"] != codes["II.1"]
    assert "Financial Statements" in codes["I.1"]
    assert "Legal Proceedings" in codes["II.1"]


def test_fixture_hashes_match_the_manifest(manifest):
    for accession in manifest:
        fixture_bytes(accession)  # raises if the archive drifted from its hash
