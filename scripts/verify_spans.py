"""Prove the iXBRL offset coordinate system holds.

Two checks, because only one of them is real evidence.

  1. `verify_spans` compares normalized_text[start:end] against span.raw_text.
     raw_text was itself taken from that slice, so this check is close to
     tautological: it proves only that nothing mutated the text after the
     offsets were recorded. Necessary, not sufficient.

  2. The independent check re-parses the document with lxml, looks each ix
     element up by its `id`, normalizes that element's own itertext, and
     compares it to the slice. lxml's view of the element's text is computed
     with no reference to the emitter's cursor, so agreement here is real
     evidence that the offsets point where they claim to.

Usage:
    python -m scripts.verify_spans <accession> [--sample N]
    python -m scripts.verify_spans --all
"""

from __future__ import annotations

import argparse
import random
import re
import sys
from pathlib import Path

import psycopg
from lxml import etree

from api.config import dsn
from api.parse.ixbrl import IX_NAMESPACES, ExtractedDocument, extract, verify_spans

_WS = re.compile(r"\s+")


def independent_mismatches(doc: ExtractedDocument, raw: bytes) -> list[tuple[str, str, str]]:
    """Compare each span's slice against lxml's own reading of that element."""
    root = etree.fromstring(raw, etree.XMLParser(recover=True, huge_tree=True))
    by_id: dict[str, etree._Element] = {}
    for ns in IX_NAMESPACES:
        for tag in ("nonFraction", "nonNumeric"):
            for el in root.iter(f"{{{ns}}}{tag}"):
                if el.get("id"):
                    by_id[el.get("id")] = el

    bad = []
    checked = 0
    for span in doc.spans:
        el = by_id.get(span.element_id or "")
        if el is None:
            continue
        checked += 1
        expected = "".join(el.itertext())
        actual = doc.text[span.char_start : span.char_end]
        # Compare with ALL whitespace removed. lxml's itertext() concatenates
        # child text with no separator, while the emitter inserts the line break
        # a block boundary actually renders -- so a multi-paragraph nonNumeric
        # block differs by exactly those newlines, and the emitter is the more
        # faithful of the two. Stripping whitespace tests what matters here: that
        # the offsets bracket the right characters.
        if _WS.sub("", expected) != _WS.sub("", actual):
            bad.append((span.element_id or "?", expected, actual))
    return bad, checked


def report(accession: str, raw_path: Path, sample: int) -> tuple[int, int]:
    raw = raw_path.read_bytes()
    doc = extract(raw)

    tautological = verify_spans(doc)
    independent, checked = independent_mismatches(doc, raw)

    numeric = [s for s in doc.spans if s.is_numeric]
    resolved = sum(
        1 for s in numeric if (c := doc.contexts.get(s.context_ref)) is not None and c.resolves
    )
    dimensional = sum(
        1
        for s in numeric
        if (c := doc.contexts.get(s.context_ref)) is not None and c.is_dimensional
    )

    print(f"\n{'=' * 78}\n{accession}   {raw_path.name}\n{'=' * 78}")
    print(f"  normalized text     {len(doc.text):>9,} chars   sha256 {doc.text_sha256[:16]}..")
    print(
        f"  ix spans            {len(doc.spans):>9,}   (numeric {len(numeric)}, "
        f"non-numeric {len(doc.spans) - len(numeric)})"
    )
    print(f"  contexts            {len(doc.contexts):>9,}")
    print(
        f"  contextRef resolves {resolved:>9,} / {len(numeric)}  ({resolved / len(numeric):.1%})"
        if numeric
        else "  no numeric spans"
    )
    print(
        f"  on dimensional ctx  {dimensional:>9,} / {len(numeric)}  "
        f"({dimensional / len(numeric):.1%})"
        if numeric
        else ""
    )
    print(f"  values unparsed     {doc.unparsed_values:>9,}")
    print(
        f"  dei fiscal label    fiscal_year={doc.fiscal_year} fiscal_period={doc.fiscal_period!r}"
    )
    print(
        f"  slice == raw_text   {len(doc.spans) - len(tautological)}/{len(doc.spans)} "
        f"({len(tautological)} mismatched)"
    )
    print(
        f"  slice == lxml text  {checked - len(independent)}/{checked} "
        f"({len(independent)} mismatched)  <- the independent check"
    )

    for eid, expected, actual in independent[:5]:
        print(f"      id={eid}\n        lxml ={expected[:110]!r}\n        slice={actual[:110]!r}")

    if sample and doc.spans:
        rng = random.Random(20260830)
        picked = rng.sample(doc.spans, min(sample, len(doc.spans)))
        print(f"\n  {sample} random spans -- text[start:end] vs the element's own text:")
        print(f"  {'offsets':>17}  {'slice from normalized text':<26} {'lxml element text':<26} ok")
        by_id = {s.element_id: s for s in doc.spans}
        _, _ = by_id, None
        el_map = dict(
            (e.get("id"), _WS.sub(" ", "".join(e.itertext())).strip())
            for ns in IX_NAMESPACES
            for tag in ("nonFraction", "nonNumeric")
            for e in etree.fromstring(raw, etree.XMLParser(recover=True, huge_tree=True)).iter(
                f"{{{ns}}}{tag}"
            )
            if e.get("id")
        )
        for s in picked:
            sl = doc.text[s.char_start : s.char_end]
            ex = el_map.get(s.element_id or "", "<no id>")
            if sl == ex:
                ok = "OK"
            elif _WS.sub("", sl) == _WS.sub("", ex):
                # Same characters, differing only in the line breaks the emitter
                # inserts at block boundaries inside a multi-paragraph block.
                ok = "OK*"
            else:
                ok = "FAIL"
            print(f"  [{s.char_start:>7},{s.char_end:>7}]  {sl[:24]!r:<26} {ex[:24]!r:<26} {ok}")

    return len(tautological), len(independent)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("accession", nargs="?")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--sample", type=int, default=0)
    args = ap.parse_args()

    with psycopg.connect(dsn()) as conn, conn.cursor() as cur:
        if args.all:
            cur.execute("SELECT accession, raw_path FROM filings ORDER BY accession")
        else:
            cur.execute(
                "SELECT accession, raw_path FROM filings WHERE accession = %s", (args.accession,)
            )
        rows = cur.fetchall()

    if not rows:
        sys.exit("no matching filings")

    total_t = total_i = 0
    for accession, raw_path in rows:
        t, i = report(accession, Path(raw_path), args.sample)
        total_t += t
        total_i += i

    print(f"\n{'=' * 78}")
    print(
        f"TOTAL across {len(rows)} filing(s):  "
        f"{total_t} raw_text mismatches, {total_i} independent mismatches"
    )
    if total_i:
        sys.exit(1)


if __name__ == "__main__":
    main()
