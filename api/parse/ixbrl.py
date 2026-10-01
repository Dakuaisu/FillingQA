"""Single-pass inline-XBRL extraction and HTML normalization.

PRD 6.2 step 1 says to harvest `<ix:*>` spans "keyed by character offset" BEFORE
flattening the HTML, because flattening destroys the offsets. But PRD 6.2's own
`Block.char_start` is "offset into normalized doc text", and PRD 6.5.3 resolves
spans to chunks, which are built from that normalized text. An offset into raw
HTML and an offset into normalized text are different coordinate systems, and
converting between them after the fact is the unstated work behind PRD 16's
"iXBRL offsets don't survive parsing" risk.

So extraction and flattening are ONE traversal. The walker emits normalized text
and, for each `ix` element, records where that element's text landed *in the text
being emitted*. The spans are therefore born in the coordinate system everything
downstream uses, and nothing has to be converted.

The invariant this module exists to hold, checked by
`verify_spans` and by the test suite:

    normalized_text[span.char_start:span.char_end] == span.raw_text

If that ever fails, every offset in the database is meaningless and no amount of
downstream work can recover it.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

from lxml import etree

from api.numbers import NumberFormatError, apply_scale, parse_number

# iXBRL 1.1 is what every filing in a three-year window uses; 1.0 is handled
# because the cost is one extra string and the failure mode of not handling it
# is silently extracting zero facts from an older filing.
IX_NAMESPACES = (
    "http://www.xbrl.org/2013/inlineXBRL",  # 1.1
    "http://www.xbrl.org/2008/inlineXBRL",  # 1.0
)
XBRLI_NS = "http://www.xbrl.org/2003/instance"
ISO4217_NS = "http://www.xbrl.org/2003/iso4217"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

# Never rendered, so never emitted: no visible text means no meaningful offset.
SKIP_TAGS = frozenset({"head", "script", "style", "title", "meta", "link"})
# `ix:header` carries the hidden fact block, contexts, units and references.
# `ix:hidden` is explicitly non-rendered by the iXBRL spec.
SKIP_IX_TAGS = frozenset({"header", "hidden", "references", "resources"})

# Block-level elements force a line break, so normalized text keeps the document's
# visual grouping. Without this, a table row and the paragraph after it run
# together into one line and every later section boundary becomes ambiguous.
BLOCK_TAGS = frozenset(
    {
        "address",
        "article",
        "aside",
        "blockquote",
        "div",
        "dl",
        "dd",
        "dt",
        "fieldset",
        "figure",
        "footer",
        "form",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "tbody",
        "tfoot",
        "thead",
        "tr",
        "ul",
    }
)
CELL_TAGS = frozenset({"td", "th"})
HEADING_TAGS = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})

_DISPLAY_NONE = re.compile(r"display\s*:\s*none", re.I)
_WS = re.compile(r"\s+")


@dataclass
class XbrlSpan:
    """One inline-XBRL fact and where its text sits in the normalized document."""

    concept: str
    context_ref: str
    char_start: int
    char_end: int
    raw_text: str
    value: Decimal | None = None
    scale: int | None = None
    sign: str | None = None
    unit_ref: str | None = None
    is_numeric: bool = True
    # The ix element's own `id`. Carried so the offsets can be checked against
    # lxml's independent view of the same element -- see `independent_mismatches`.
    element_id: str | None = None


@dataclass
class Anchor:
    """An in-document link (`<a href="#...">`) and where its text sits."""

    char_start: int
    char_end: int
    target: str  # the href fragment, without '#'


@dataclass
class Block:
    """One leaf block of the document: a paragraph, a heading, or a whole table.

    PRD 6.2's Block, recorded by the same traversal that emits the text, so its
    offsets live in the same coordinate system as the spans.

    Only LEAF blocks are recorded -- the innermost block element containing text.
    Filings nest divs many levels deep for layout, and recording every level
    would produce thousands of overlapping ranges saying nothing about structure.
    A table is always one block: PRD 6.3 rule 1 says a table is never split, and
    that begins here.
    """

    tag: str
    char_start: int
    char_end: int
    kind: str = "paragraph"  # 'paragraph' | 'heading' | 'table'
    # Tables only: rows of cells, each (char_start, char_end, colspan, rowspan).
    # The offsets index the same normalized text, so cell contents never get a
    # second coordinate system of their own.
    rows: list[list[tuple[int, int, int, int]]] | None = None
    # Tables only: where the unit scale came from, 'caption' | 'ixbrl' | None,
    # so unit-scale accuracy can be broken out by source in Phase 3.
    scale_source: str | None = None
    # In-document links inside this block, in normalized-text coordinates. Used
    # to recognise navigation (F-54); the text itself is unchanged.
    anchors: list[Anchor] = field(default_factory=list)

    @property
    def length(self) -> int:
        return self.char_end - self.char_start


@dataclass
class Context:
    """A resolved xbrli:context: the period a fact describes."""

    context_id: str
    period_start: str | None = None
    period_end: str | None = None
    instant: str | None = None
    is_dimensional: bool = False

    @property
    def resolves(self) -> bool:
        return bool(self.instant or self.period_end)


@dataclass
class Unit:
    """A resolved xbrli:unit: measures as (namespace, local name) pairs."""

    unit_id: str
    numerator: list[tuple[str, str]] = field(default_factory=list)
    denominator: list[tuple[str, str]] = field(default_factory=list)

    @property
    def is_monetary(self) -> bool:
        """A bare currency amount. USD-per-share is a divide, so it is not: it
        belongs with the per-share figures a caption's "except" covers."""
        return (
            not self.denominator and len(self.numerator) == 1 and self.numerator[0][0] == ISO4217_NS
        )


@dataclass
class ExtractedDocument:
    """Everything the single pass produced."""

    text: str
    spans: list[XbrlSpan] = field(default_factory=list)
    blocks: list[Block] = field(default_factory=list)
    contexts: dict[str, Context] = field(default_factory=dict)
    units: dict[str, Unit] = field(default_factory=dict)
    # Where each in-document link target (`id` / `name`) begins in the
    # normalized text, so an index row's href can be resolved to a position.
    anchor_targets: dict[str, int] = field(default_factory=dict)
    dei: dict[str, str] = field(default_factory=dict)
    unparsed_values: int = 0

    @property
    def text_sha256(self) -> str:
        return hashlib.sha256(self.text.encode("utf-8")).hexdigest()

    @property
    def fiscal_year(self) -> int | None:
        raw = self.dei.get("dei:DocumentFiscalYearFocus")
        return int(raw) if raw and raw.isdigit() else None

    @property
    def fiscal_period(self) -> str | None:
        """'FY' | 'Q1' | 'Q2' | 'Q3', as the issuer labels it."""
        return self.dei.get("dei:DocumentFiscalPeriodFocus")


def _localname(el: etree._Element) -> str:
    tag = el.tag
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1].lower()


def _namespace(el: etree._Element) -> str:
    tag = el.tag
    if isinstance(tag, str) and tag.startswith("{"):
        return tag[1 : tag.index("}")]
    return ""


def _span(el: etree._Element, attr: str) -> int:
    try:
        return max(1, int(el.get(attr, "1")))
    except ValueError:
        return 1


class _Emitter:
    """Accumulates normalized text and knows how long it is so far.

    Whitespace is collapsed as it is written rather than afterwards. Collapsing
    afterwards would shift every offset already recorded, which is exactly the
    bug this module is built to avoid.
    """

    def __init__(self) -> None:
        self._parts: list[str] = []
        self._len = 0
        self._pending_breaks = 0

    def __len__(self) -> int:
        return self._len

    def _write(self, s: str) -> None:
        self._parts.append(s)
        self._len += len(s)

    def _tail(self) -> str:
        return self._parts[-1][-1:] if self._parts else ""

    def _flush_breaks(self) -> None:
        if self._pending_breaks and self._parts:
            self._write("\n" * self._pending_breaks)
        self._pending_breaks = 0

    def text(self, raw: str) -> None:
        if not raw:
            return
        collapsed = _WS.sub(" ", raw)
        if not collapsed.strip():
            # Whitespace-only node: it can still separate two words.
            if self._parts and not self._pending_breaks and self._tail() not in (" ", "\n"):
                self._flush_breaks()
                self._write(" ")
            return

        self._flush_breaks()
        if collapsed.startswith(" ") and (not self._parts or self._tail() in (" ", "\n")):
            collapsed = collapsed.lstrip(" ")
        self._write(collapsed)

    def separator(self) -> None:
        """A soft break between table cells."""
        if self._parts and not self._pending_breaks and self._tail() not in (" ", "\n"):
            self._write(" ")

    def line_break(self, count: int = 1) -> None:
        """Request a break. Deferred so trailing breaks never pad the document."""
        if self._parts:
            self._pending_breaks = max(self._pending_breaks, count)

    def build(self) -> str:
        return "".join(self._parts)


class _Walker:
    """One depth-first pass: emits text, records ix spans as it goes."""

    def __init__(self) -> None:
        self.out = _Emitter()
        self.spans: list[XbrlSpan] = []
        self.blocks: list[Block] = []
        self.dei: dict[str, str] = {}
        self.unparsed = 0
        self._table_depth = 0
        self.anchors: list[Anchor] = []
        self.targets: dict[str, int] = {}
        # One entry per open <table>; a row or cell belongs to the innermost one.
        self._table_rows: list[list[list[tuple[int, int, int, int]]]] = []

    # -- ix element handling ------------------------------------------------

    def _record(self, el: etree._Element, start: int, end: int) -> None:
        concept = el.get("name")
        if not concept:
            return
        if el.get(f"{{{XSI_NS}}}nil") == "true":
            return  # a nil fact has no value to record

        local = _localname(el)
        raw = self.out.build()[start:end]
        # Tighten onto the actual glyphs: leading or trailing space inside the
        # recorded range would make the slice differ from the element's own text.
        lead = len(raw) - len(raw.lstrip())
        trail = len(raw) - len(raw.rstrip())
        start, end = start + lead, end - trail
        raw = raw[lead : len(raw) - trail] if trail else raw[lead:]

        if local == "nonnumeric":
            # Non-numeric facts carry no value; dei:* ones carry the labels that
            # populate filings.fiscal_year (TRADEOFFS finding #5).
            self.spans.append(
                XbrlSpan(
                    concept=concept,
                    context_ref=el.get("contextRef", ""),
                    char_start=start,
                    char_end=end,
                    raw_text=raw,
                    is_numeric=False,
                    element_id=el.get("id"),
                )
            )
            return

        scale = el.get("scale")
        sign = el.get("sign")
        value: Decimal | None
        try:
            value = parse_number(raw)
            if scale is not None:
                value = apply_scale(value, int(scale))
            if sign == "-":
                value = -value
        except (NumberFormatError, ValueError):
            # Recorded without a value rather than dropped: the span is still a
            # real document location, and a silent drop would inflate the
            # resolution rate that Phase 2 asserts on.
            value = None
            self.unparsed += 1

        self.spans.append(
            XbrlSpan(
                concept=concept,
                context_ref=el.get("contextRef", ""),
                char_start=start,
                char_end=end,
                raw_text=raw,
                value=value,
                scale=int(scale) if scale is not None else None,
                sign=sign,
                unit_ref=el.get("unitRef"),
                element_id=el.get("id"),
            )
        )

    # -- traversal ----------------------------------------------------------

    def visit(self, el: etree._Element) -> None:
        if not isinstance(el.tag, str):  # comment or processing instruction
            self._tail_text(el)
            return

        ns = _namespace(el)
        local = _localname(el)
        is_ix = ns in IX_NAMESPACES

        if is_ix and local in SKIP_IX_TAGS:
            # Hidden facts still carry values we need -- the dei fiscal labels
            # live here -- but they have no rendered position, so they get a
            # value and no span.
            self._harvest_hidden(el)
            self._tail_text(el)
            return

        if local in SKIP_TAGS and not is_ix:
            self._tail_text(el)
            return

        style = el.get("style") or ""
        if _DISPLAY_NONE.search(style):
            self._tail_text(el)
            return

        block = local in BLOCK_TAGS and not is_ix
        is_table = local == "table" and not is_ix

        if block or (local == "br" and not is_ix):
            self.out.line_break()
        elif local in CELL_TAGS and not is_ix:
            self.out.separator()

        start = len(self.out) if is_ix else None
        if not is_ix:
            for attr in ("id", "name"):
                key = el.get(attr)
                if key and key not in self.targets:
                    self.targets[key] = len(self.out)
        block_start = len(self.out) if block else None
        blocks_before = len(self.blocks)

        if is_table:
            self._table_depth += 1
            self._table_rows.append([])
        elif local == "tr" and not is_ix and self._table_rows:
            self._table_rows[-1].append([])

        cell_start = len(self.out) if local in CELL_TAGS and not is_ix else None
        href = (el.get("href") or "") if local == "a" and not is_ix else ""
        anchor_start = len(self.out) if href.startswith("#") else None

        self.out.text(el.text or "")
        for child in el:
            self.visit(child)

        if cell_start is not None and self._table_rows and self._table_rows[-1]:
            self._table_rows[-1][-1].append(
                (cell_start, len(self.out), _span(el, "colspan"), _span(el, "rowspan"))
            )

        if is_ix and start is not None:
            self._record(el, start, len(self.out))

        if anchor_start is not None:
            raw = self.out.build()[anchor_start:]
            lead, trail = len(raw) - len(raw.lstrip()), len(raw) - len(raw.rstrip())
            a_start, a_end = anchor_start + lead, len(self.out) - trail
            if a_end > a_start:
                self.anchors.append(Anchor(a_start, a_end, href[1:]))

        if block:
            self.out.line_break()

        if is_table:
            self._table_depth -= 1
            rows = self._table_rows.pop()
            # Discard any blocks recorded inside: a table is one block, always.
            del self.blocks[blocks_before:]
            self._add_block(local, block_start, len(self.out), kind="table", rows=rows)
        elif block and self._table_depth == 0 and len(self.blocks) == blocks_before:
            # A leaf block: nothing inside it recorded a block of its own.
            kind = "heading" if local in HEADING_TAGS else "paragraph"
            self._add_block(local, block_start, len(self.out), kind=kind)

        self._tail_text(el)

    def _add_block(
        self,
        tag: str,
        start: int | None,
        end: int,
        kind: str,
        rows: list[list[tuple[int, int, int, int]]] | None = None,
    ) -> None:
        if start is None:
            return
        raw = self.out.build()[start:end]
        lead = len(raw) - len(raw.lstrip())
        trail = len(raw) - len(raw.rstrip())
        start, end = start + lead, end - trail
        if end <= start:
            return  # a layout-only element with no text of its own
        self.blocks.append(Block(tag=tag, char_start=start, char_end=end, kind=kind, rows=rows))

    def _tail_text(self, el: etree._Element) -> None:
        self.out.text(el.tail or "")

    def _harvest_hidden(self, el: etree._Element) -> None:
        """Deliberately a no-op: dei facts are harvested by `harvest_dei`.

        Kept as an explicit hook so the skip path reads as a decision rather than
        an omission. Hidden facts are collected from the whole tree instead --
        see `harvest_dei` for why doing it here is not enough.
        """


def harvest_dei(root: etree._Element) -> dict[str, str]:
    """Collect dei:* fact values from anywhere in the document.

    Separate from the text walk on purpose. The fiscal labels that populate
    filings.fiscal_year (TRADEOFFS finding #5) sit inside `ix:hidden`, which in
    a real filing is itself wrapped in a `<div style="display:none">`. The walker
    skips that subtree before it ever reaches `ix:header`, so harvesting from
    inside the walk finds nothing -- which is exactly the bug this replaced: the
    extractor reported fiscal_year=None on a filing that plainly tags it.

    These facts have no rendered position, so they get values and no spans.
    """
    found: dict[str, str] = {}
    for ns in IX_NAMESPACES:
        for tag in ("nonNumeric", "nonFraction"):
            for fact in root.iter(f"{{{ns}}}{tag}"):
                name = fact.get("name")
                if name and name.startswith("dei:"):
                    found.setdefault(name, "".join(fact.itertext()).strip())
    return found


def parse_contexts(root: etree._Element) -> dict[str, Context]:
    """Resolve every xbrli:context to the period it describes."""
    contexts: dict[str, Context] = {}
    for ctx in root.iter(f"{{{XBRLI_NS}}}context"):
        cid = ctx.get("id")
        if not cid:
            continue
        period = ctx.find(f"{{{XBRLI_NS}}}period")

        def _text(node, name):
            if node is None:
                return None
            found = node.findtext(f"{{{XBRLI_NS}}}{name}")
            return found.strip() if found else None

        contexts[cid] = Context(
            context_id=cid,
            period_start=_text(period, "startDate"),
            period_end=_text(period, "endDate"),
            instant=_text(period, "instant"),
            # A segmented context is a dimensional breakdown (by product, by
            # geography) rather than a company-level figure. Downstream needs to
            # tell them apart: a segment revenue line is not "revenue".
            is_dimensional=ctx.find(f"{{{XBRLI_NS}}}entity/{{{XBRLI_NS}}}segment") is not None,
        )
    return contexts


def _measure(el: etree._Element) -> tuple[str, str]:
    """Resolve a measure's QName ("iso4217:USD") through the element's own nsmap."""
    prefix, _, local = (el.text or "").strip().rpartition(":")
    return (el.nsmap.get(prefix or None, ""), local)


def parse_units(root: etree._Element) -> dict[str, Unit]:
    units: dict[str, Unit] = {}
    for el in root.iter(f"{{{XBRLI_NS}}}unit"):
        uid = el.get("id")
        if not uid:
            continue
        unit = Unit(unit_id=uid)
        divide = el.find(f"{{{XBRLI_NS}}}divide")
        if divide is None:
            unit.numerator = [_measure(m) for m in el.findall(f"{{{XBRLI_NS}}}measure")]
        else:
            for side, target in (
                ("unitNumerator", unit.numerator),
                ("unitDenominator", unit.denominator),
            ):
                target.extend(
                    _measure(m)
                    for m in divide.iter(f"{{{XBRLI_NS}}}measure")
                    if m.getparent().tag == f"{{{XBRLI_NS}}}{side}"
                )
        units[uid] = unit
    return units


def extract(raw: bytes) -> ExtractedDocument:
    """Run the single pass over one filing's bytes."""
    parser = etree.XMLParser(recover=True, huge_tree=True, resolve_entities=False)
    root = etree.fromstring(raw, parser)
    if root is None:
        raise ValueError("document did not parse")

    contexts = parse_contexts(root)
    units = parse_units(root)

    walker = _Walker()
    walker.visit(root)
    text = walker.out.build()

    # Attach each in-document anchor to the leaf block that contains it. Blocks
    # are ordered and non-overlapping, so one forward pass suffices.
    blocks = iter(walker.blocks)
    block = next(blocks, None)
    for anchor in walker.anchors:
        while block is not None and block.char_end <= anchor.char_start:
            block = next(blocks, None)
        if block is not None and block.char_start <= anchor.char_start < block.char_end:
            block.anchors.append(anchor)

    walker.dei = harvest_dei(root)
    # A dei fact can also be rendered rather than hidden; fill any gaps from the
    # visible spans without letting them override the tagged values.
    for span in walker.spans:
        if span.concept.startswith("dei:"):
            walker.dei.setdefault(span.concept, span.raw_text)

    return ExtractedDocument(
        text=text,
        spans=walker.spans,
        blocks=walker.blocks,
        contexts=contexts,
        units=units,
        anchor_targets=walker.targets,
        dei=walker.dei,
        unparsed_values=walker.unparsed,
    )


def verify_spans(doc: ExtractedDocument) -> list[XbrlSpan]:
    """Return spans whose recorded offsets do not slice back to their own text.

    This is the load-bearing invariant of the whole parsing stage. An empty list
    means the coordinate system holds.
    """
    return [s for s in doc.spans if doc.text[s.char_start : s.char_end] != s.raw_text]


def write_normalized(doc: ExtractedDocument, path: Path) -> str:
    """Persist normalized text and return its sha256."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_text(doc.text, encoding="utf-8")
    tmp.replace(path)
    return doc.text_sha256
