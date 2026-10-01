"""Section detection: group blocks into the filing's Items.

PRD 6.2 step 2 suggests matching Item headings "with a tolerant regex plus a
fallback that uses the table-of-contents anchors". Run over the flattened text
that does not work, and the way it fails is quiet:

  - Headings are not at line starts. The renderer puts them inline with the
    surrounding text, so a `^ITEM` anchor finds nothing in the body and matches
    only the table of contents -- 26 of AAPL's 54 text matches are TOC rows.
  - Cross-references are lexically identical to headings. "in conjunction with
    Part II, Item 7, "Management's Discussion..."" is a reference; "Item 7.
    Management's Discussion..." is the heading. Same characters.

Detection therefore runs on BLOCKS, not on text. A heading is a short, standalone
block whose text begins with the Item pattern -- which a mid-sentence reference
never is, and which a TOC row is not either because the TOC lives inside a table
and a table is a single block. A short table counts as a heading only when its
first row is its one and only heading-like row (F-63). On AAPL's 10-K this yields 23 headings and no
false positives, against 61 raw text matches.

10-Q part qualification
-----------------------
A 10-Q has Part I and Part II, each with its own Item 1 and Item 1A: Part I
Item 1 is Financial Statements, Part II Item 1 is Legal Proceedings. A bare
item_code is therefore ambiguous for the 72 of 96 corpus filings that are 10-Qs,
so the current Part is tracked and carried on every section.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from api.parse.ixbrl import Block, ExtractedDocument

# A heading block is short. Titles run long -- Item 12's is 103 characters on
# AAPL's 10-K -- but a block carrying a heading plus body text is far longer, and
# the cutoff separates them cleanly with room to spare.
MAX_HEADING_CHARS = 200

# The dashes are en/em dashes on purpose: filings separate the item number from
# its title with typographic dashes, not ASCII hyphens.
_ITEM = re.compile(
    r"^ITEM\s+(?P<num>\d{1,2})\s*(?P<suffix>[A-C])?\s*[.:—–-]?\s*(?P<title>.*)$",  # noqa: RUF001
    re.I | re.S,
)
_PART = re.compile(
    r"^PART\s+(?P<part>I{1,3}V?|IV|V)\b\s*[.:—–|-]?\s*(?P<rest>.*)$",  # noqa: RUF001
    re.I,
)

# PRD 6.2: a 10-K that does not yield these has not been parsed correctly.
REQUIRED_10K_ITEMS = ("1", "1A", "7", "7A", "8")
# Part I Item 1 is the financial statements; Part I Item 2 is MD&A.
REQUIRED_10Q_ITEMS = (("I", "1"), ("I", "2"))


@dataclass
class Section:
    """One Item of the filing, with the block range it covers."""

    item_code: str  # "1A", "7", ...
    title: str
    order: int
    char_start: int
    char_end: int
    block_start: int
    block_end: int
    part: str | None = None  # "I" | "II" | "III" | "IV"

    @property
    def qualified_code(self) -> str:
        """Part-qualified code. Ambiguous without the part on a 10-Q."""
        return f"{self.part}.{self.item_code}" if self.part else self.item_code


def block_text(doc: ExtractedDocument, block: Block) -> str:
    return " ".join(doc.text[block.char_start : block.char_end].split())


def text_without_anchors(doc: ExtractedDocument, block: Block) -> str:
    """Block text with in-document link text removed ("Table of Contents")."""
    parts, pos = [], block.char_start
    for anchor in sorted(block.anchors, key=lambda a: a.char_start):
        parts.append(doc.text[pos : anchor.char_start])
        pos = anchor.char_end
    parts.append(doc.text[pos : block.char_end])
    return " ".join("".join(parts).split())


def is_heading_table(doc: ExtractedDocument, block: Block) -> bool:
    """A layout table that is a heading, not a table of contents (F-63).

    Some filers wrap each Item or Part heading in a table -- PFE and XOM put
    every 10-K heading in a one-row table ("ITEM 1." | "BUSINESS"), BAC adds a
    title row and a "Table of Contents" link. A table of contents or a
    cross-reference index lists many headings, one per row. So: the first
    non-empty row matches a heading, and no other row does.
    """
    rows = []
    for row in block.rows or []:
        text = " ".join(" ".join(doc.text[s:e].split()) for s, e, *_ in row).strip()
        if text:
            rows.append(" ".join(text.split()))
    matches = [i for i, text in enumerate(rows) if _ITEM.match(text) or _PART.match(text)]
    return matches == [0]


def _heading_match(text: str) -> tuple[str, str] | None:
    """Return (item_code, title) if this text is an Item heading."""
    m = _ITEM.match(text)
    if not m:
        return None
    code = m.group("num") + (m.group("suffix") or "").upper()
    return code, " ".join(m.group("title").split())


def detect_sections(doc: ExtractedDocument, form_type: str) -> list[Section]:
    """Group the document's blocks into Items, in document order."""
    headings: list[tuple[int, str, str, str | None]] = []  # block_idx, code, title, part
    current_part: str | None = None

    for idx, block in enumerate(doc.blocks):
        if block.length > MAX_HEADING_CHARS:
            # Anything long is body text that merely starts with "Item".
            continue
        if block.kind == "table":
            if not is_heading_table(doc, block):
                continue
            text = text_without_anchors(doc, block)
        else:
            text = block_text(doc, block)

        part_match = _PART.match(text)
        if part_match and not _ITEM.match(part_match.group("rest")):
            current_part = part_match.group("part").upper()
            continue

        found = _heading_match(text)
        if found:
            headings.append((idx, found[0], found[1], current_part))

    sections: list[Section] = []
    for order, (block_idx, code, title, part) in enumerate(headings):
        next_block = headings[order + 1][0] if order + 1 < len(headings) else len(doc.blocks)
        char_end = (
            doc.blocks[next_block - 1].char_end
            if next_block > 0
            else doc.blocks[block_idx].char_end
        )
        sections.append(
            Section(
                item_code=code,
                title=title,
                order=order,
                char_start=doc.blocks[block_idx].char_start,
                char_end=char_end,
                block_start=block_idx,
                block_end=next_block,
                part=part,
            )
        )

    return sections


def missing_required(sections: list[Section], form_type: str) -> list[str]:
    """Required Items this filing did not yield. Non-empty means quarantine.

    PRD 6.2: "Do not let bad parses into the index silently."
    """
    if form_type == "10-K":
        present = {s.item_code for s in sections}
        return [i for i in REQUIRED_10K_ITEMS if i not in present]

    if form_type == "10-Q":
        present = {(s.part, s.item_code) for s in sections}
        return [f"{p}.{i}" for p, i in REQUIRED_10Q_ITEMS if (p, i) not in present]

    return []
