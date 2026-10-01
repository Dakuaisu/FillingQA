"""Table extraction: PRD 6.2 step 3.

Works on the cell ranges the single-pass walker recorded (`Block.rows`), so every
cell is a slice of the normalized text and nothing here re-parses HTML.

Filings lay tables out on a fine column grid. A printed figure like `$ 34,550`
or `10 %` is split across adjacent cells (`$` | `34,550`, `10` | `%`), and blank
spacer columns separate one value column from the next. A header cell's colspan
covers the fragments beneath it. So logical columns are recovered by merging the
column ranges of body cells: overlapping ranges are one column, and the spacer
gaps are where columns end.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from api.numbers import NumberFormatError, parse_number
from api.parse.ixbrl import Block, ExtractedDocument
from api.parse.sections import Section

log = logging.getLogger(__name__)

CAPTION_WINDOW = 500

# Printed beside a figure in its own cell. `$` attaches to the figure on its
# right; the others close a figure on their left.
_PREFIX_FRAGMENTS = frozenset({"$"})
_SUFFIX_FRAGMENTS = frozenset({"%", ")", ")%", "%)"})

_YEAR = re.compile(r"^(19|20)\d{2}$")
_DIGIT = re.compile(r"\d")

# A scale word inside parentheses -- "(in thousands, except per share data)",
# "(dollars in millions)", TGT's bare "(millions)" -- or an unparenthesized
# "in millions". A bare scale word in prose ("thousands of employees") is not a
# caption, which is why the word alone is not enough.
_CAPTION = re.compile(
    r"\(([^()]*?\b(thousands|millions|billions)\b[^()]*)\)|\bin\s+(thousands|millions|billions)\b",
    re.I,
)
_SCALE_WORD = re.compile(r"\b(thousands|millions|billions)\b", re.I)
_PERIOD_LABEL = re.compile(r"\b(19|20)\d{2}\b")
_ONLY_PARENTHETICALS = re.compile(r"^(\([^()]*\)\s*)+$")
_PAGE_ARTIFACT = re.compile(r"form 10-[kq]|table of contents|^\d+$", re.I)

IX_SCALE_WORDS = {3: "thousands", 6: "millions", 9: "billions"}


def ixbrl_scale(tagged: set[tuple[int | None, bool]]) -> tuple[str | None, bool]:
    """The table's scale from its tagged figures, as (scale, conflict).

    `tagged` holds (scale attribute, is_monetary) per figure. Only magnitude
    scales count toward the choice. `0` (per-share amounts, counts) and `-2`
    (percentages) sit inside "in millions" tables the way "except per share"
    sits inside a caption, so they do not make a table mixed. Two magnitudes --
    AAPL's statements tag dollars at 6 and share counts at 3 -- give None.

    Monetary veto: dollars are not in the "except" set. A currency figure at any
    scale other than the chosen magnitude means the header would mis-scale it by
    10^6 -- invisibly -- so the answer is None and a reported conflict.
    """
    words = {IX_SCALE_WORDS[s] for s, _ in tagged if s in IX_SCALE_WORDS}
    if len(words) != 1:
        return None, False
    chosen = words.pop()
    if any(monetary and IX_SCALE_WORDS.get(s) != chosen for s, monetary in tagged):
        return None, True
    return chosen, False


def detect_unit_scale(text: str) -> str | None:
    """The scale stated by the caption closest to the END of `text`.

    `text` is what precedes the table (and its header rows), so the last caption
    is the nearest one. The table's scale is the one stated before "except": in
    "(In millions, except number of shares, which are reflected in thousands)"
    thousands is the exception. A caption naming two scales with no "except" --
    AAPL's "(net income in millions and shares in thousands)" -- returns None:
    the table has no single scale, and picking one would mis-scale half its rows.
    """
    matches = list(_CAPTION.finditer(text))
    if not matches:
        return None
    caption = matches[-1].group(0)
    main = re.split(r"\bexcept\b", caption, maxsplit=1, flags=re.I)[0]
    words = {w.lower() for w in _SCALE_WORD.findall(main)}
    return words.pop() if len(words) == 1 else None


def is_value(text: str) -> bool:
    """A printed figure with at least one digit: `34,550`, `(95,699)`, `10%`, `$7.49`."""
    if not _DIGIT.search(text):
        return False
    try:
        parse_number(text.rstrip("%").strip())
    except NumberFormatError:
        return False
    return True


def is_nil(text: str) -> bool:
    """A dash printed where a figure would be."""
    return text in {"—", "–", "-"}  # noqa: RUF001


@dataclass
class Cell:
    col_start: int
    col_end: int
    text: str


@dataclass
class Table:
    block: Block
    kind: str  # 'data' | 'layout'
    header_rows: int = 0
    title: str | None = None
    columns: list[str] = field(default_factory=list)  # label per logical column
    body: list[list[str]] = field(default_factory=list)
    unit_scale: str | None = None
    ix_scales: set[str] = field(default_factory=set)
    scale_source: str | None = None  # 'caption' | 'ixbrl' | None
    scale_conflict: bool = False  # iXBRL fallback vetoed by a monetary figure
    currency: str | None = None
    fiscal_periods: list[str] = field(default_factory=list)


def _cell_rows(doc: ExtractedDocument, block: Block) -> list[list[Cell]]:
    """Place cells on the column grid, honouring colspan and rowspan.

    A cell with rowspan=2 occupies its columns in the next row too, so that
    row's cells start further right than their position in the HTML suggests.
    AAPL's Term Debt header is offset by exactly one column without this.
    """
    rows = []
    occupied: dict[int, int] = {}  # column -> rows it stays occupied for
    for raw in block.rows or []:
        col, cells = 0, []
        for start, end, colspan, rowspan in raw:
            while occupied.get(col, 0) > 0:
                col += 1
            text = " ".join(doc.text[start:end].split())
            if text:
                cells.append(Cell(col, col + colspan, text))
            if rowspan > 1:
                for c in range(col, col + colspan):
                    occupied[c] = rowspan
            col += colspan
        occupied = {c: n - 1 for c, n in occupied.items() if n - 1 > 0}
        rows.append(cells)
    return [r for r in rows if r]


def _merge_fragments(row: list[Cell]) -> list[Cell]:
    """`$` | `34,550` -> `$34,550` and `10` | `%` -> `10%`, widening the range."""
    out: list[Cell] = []
    pending: Cell | None = None
    for cell in row:
        if cell.text in _PREFIX_FRAGMENTS:
            pending = cell
            continue
        if pending is not None:
            cell = Cell(pending.col_start, cell.col_end, pending.text + cell.text)
            pending = None
        if cell.text in _SUFFIX_FRAGMENTS and out:
            prev = out[-1]
            out[-1] = Cell(prev.col_start, cell.col_end, prev.text + cell.text)
            continue
        out.append(cell)
    if pending is not None:
        out.append(pending)
    return out


def _first_body_row(rows: list[list[Cell]]) -> int:
    """Header rows are those before the first row holding a non-year figure.

    PRD 6.2 says "first row(s) with no numeric cells". Taken literally that makes
    `2025 | 2024 | 2023` a data row, and it is the most common header in the
    corpus, so a bare year does not count as a figure here.
    """
    for i, row in enumerate(rows):
        if any(is_value(c.text) and not _YEAR.match(c.text) for c in row):
            return i
    return len(rows)


def _value_groups(body: list[list[Cell]]) -> list[tuple[int, int]]:
    """Logical value columns: merged column ranges of every body cell right of
    the label column.

    Not only figures: AAPL's Term Debt table prints maturities ("2028 - 2035")
    and rate ranges in their own columns, and grouping on figures alone folded
    them into the row label and shifted every column header onto the wrong values.

    But a text cell that bridges two figure columns is a period header repeated
    mid-table (AAPL 10-Q segment tables stack "Six Months Ended March 28, 2026"
    and "...March 29, 2025" blocks), not a column, and would merge them all.
    """
    cells = [c for row in body for c in row if c.col_start > 0]
    figure_groups = _merge_ranges(
        [(c.col_start, c.col_end) for c in cells if is_value(c.text) or is_nil(c.text)]
    )

    def bridges(c: Cell) -> bool:
        return sum(1 for s, e in figure_groups if c.col_start < e and c.col_end > s) > 1

    columns = [
        (c.col_start, c.col_end)
        for c in cells
        if not is_value(c.text) and not is_nil(c.text) and not bridges(c)
    ]
    return _merge_ranges(figure_groups + columns)


def _merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    groups: list[list[int]] = []
    for start, end in sorted(ranges):
        if groups and start < groups[-1][1]:
            groups[-1][1] = max(groups[-1][1], end)
        else:
            groups.append([start, end])
    return [(s, e) for s, e in groups]


def _group_of(cell: Cell, groups: list[tuple[int, int]]) -> int:
    """0 is the label column; value columns are 1..n."""
    for i, (start, end) in enumerate(groups, start=1):
        if cell.col_start < end and cell.col_end > start:
            return i
    return 0


def classify(rows: list[list[Cell]]) -> str:
    """'data' if some row holds two or more figures, else 'layout' (F-35).

    Layout tables are page furniture and form scaffolding: running headers
    (`BUSINESS | Table of Contents`), footers (`TARGET CORPORATION | 2025 Form
    10-K | 8`), cover-page checkboxes, and tables of contents. None of them has
    two figures in one row. Measured, not assumed: the per-filing split for the
    12-filing dev slice is in docs/WORKLOG.md.
    """
    for row in rows:
        if sum(1 for c in _merge_fragments(row) if is_value(c.text)) >= 2:
            return "data"
    return "layout"


def _title_before(doc: ExtractedDocument, index: int) -> str | None:
    """The nearest short heading before the table, within the caption window.

    Walks back over preceding blocks. Captions and page furniture are skipped,
    and so are lead-in sentences ending in ":" ("...are as follows:"), because
    the heading usually sits just above them. A sentence ending in "." means we
    have walked into prose, and another table means there is no heading.
    """
    table = doc.blocks[index]
    for block in reversed(doc.blocks[:index]):
        if table.char_start - block.char_end > CAPTION_WINDOW or block.kind == "table":
            return None
        text = " ".join(doc.text[block.char_start : block.char_end].split())
        if not text or _ONLY_PARENTHETICALS.match(text) or _PAGE_ARTIFACT.search(text):
            continue
        if text.endswith(":"):
            continue
        if len(text) <= 100 and text[-1] not in ".;":
            return text
        return None
    return None


def _in_value_area(cell: Cell, groups: list[tuple[int, int]]) -> bool:
    return bool(groups) and cell.col_start >= groups[0][0]


def extract_table(doc: ExtractedDocument, index: int) -> Table:
    block = doc.blocks[index]
    rows = _cell_rows(doc, block)
    kind = classify(rows)
    table = Table(block=block, kind=kind)
    if kind == "layout":
        return table

    merged = [_merge_fragments(r) for r in rows]
    first_body = _first_body_row(merged)
    groups = _value_groups(merged[first_body:])

    # Header rows end at the last row that labels a value column. Label-only
    # rows after it ("ASSETS:", "Net sales:") are row labels and belong to the
    # body; before it they are titles or captions.
    pre = merged[:first_body]
    labelled = [i for i, row in enumerate(pre) if any(_in_value_area(c, groups) for c in row)]
    header_end = labelled[-1] + 1 if labelled else 0
    header, body = merged[:header_end], merged[header_end:]
    table.header_rows = header_end

    labels: list[list[str]] = [[] for _ in range(len(groups) + 1)]
    for row in header:
        is_label_row = any(_in_value_area(c, groups) for c in row)
        for cell in row:
            if _in_value_area(cell, groups):
                # A super-header such as AAPL's "2025" above five region columns
                # spans several value columns and labels each of them.
                for i, (start, end) in enumerate(groups, start=1):
                    if cell.col_start < end and cell.col_end > start:
                        labels[i].append(cell.text)
            elif _ONLY_PARENTHETICALS.match(cell.text):
                continue
            elif is_label_row:
                labels[0].append(cell.text)
            elif table.title is None:
                table.title = cell.text
    table.columns = [" ".join(parts) for parts in labels]
    if table.title is None:
        table.title = _title_before(doc, index)
    if table.title is None and table.columns[0]:
        # TGT puts the title in the label cell of the column-header row.
        table.title = _CAPTION.sub("", table.columns[0]).strip() or None
        if table.title and _ONLY_PARENTHETICALS.match(table.title):
            table.title = None

    for row in body:
        out = [""] * (len(groups) + 1)
        for cell in row:
            g = _group_of(cell, groups)
            out[g] = f"{out[g]} {cell.text}".strip()
        table.body.append(out)

    header_text = "\n".join(c.text for row in pre for c in row)
    preceding = doc.text[max(0, block.char_start - CAPTION_WINDOW) : block.char_start]
    tagged = {
        (span.scale, unit.is_monetary if (unit := doc.units.get(span.unit_ref or "")) else False)
        for span in doc.spans
        if span.is_numeric and block.char_start <= span.char_start < block.char_end
    }
    table.ix_scales = {IX_SCALE_WORDS[s] for s, _ in tagged if s in IX_SCALE_WORDS}

    # Caption first, then iXBRL, never section inheritance (TRADEOFFS F-45): a
    # wrong scale is an invisible 10^6 error, a missing one is detectable.
    table.unit_scale = detect_unit_scale(preceding + "\n" + header_text)
    if table.unit_scale:
        table.scale_source = "caption"
    else:
        fallback, table.scale_conflict = ixbrl_scale(tagged)
        if fallback is not None:
            table.unit_scale, table.scale_source = fallback, "ixbrl"
        elif table.scale_conflict:
            log.warning(
                "table %r at %d: iXBRL scale vetoed, a currency figure is off-scale",
                table.title,
                block.char_start,
            )
    block.scale_source = table.scale_source

    table.currency = "USD" if any(c.text.startswith("$") for r in body for c in r) else None
    table.fiscal_periods = [c for c in table.columns[1:] if _PERIOD_LABEL.search(c)]
    return table


def extract_tables(doc: ExtractedDocument) -> list[Table]:
    return [extract_table(doc, i) for i, b in enumerate(doc.blocks) if b.kind == "table"]


def document_labels(doc: ExtractedDocument, form_type: str) -> tuple[str, str]:
    """(company, period label) for the context line, from the issuer's dei tags.

    The period label is the issuer's own fiscal label, never derived from a
    calendar date (TRADEOFFS finding #5): TGT's fiscal 2025 ends in 2026.
    """
    company = doc.dei.get("dei:EntityRegistrantName", "")
    fy, fp = doc.fiscal_year, doc.fiscal_period
    period = f"FY{fy}" if fp == "FY" else f"{fp} FY{fy}"
    return company, f"{period} {form_type}"


def item_label(section: Section | None, form_type: str) -> str:
    if section is None:
        return "no Item"
    # A 10-Q has an Item 1 in both Parts (F-04), so the Part is part of the label.
    if form_type == "10-Q" and section.part:
        return f"Part {section.part}, Item {section.item_code}"
    return f"Item {section.item_code}"


def section_of(block: Block, sections: list[Section]) -> Section | None:
    for section in sections:
        if section.char_start <= block.char_start < section.char_end:
            return section
    return None


def context_line(table: Table, company: str, period_label: str, item: str) -> str:
    units = ", ".join(
        p for p in (f"in {table.unit_scale}" if table.unit_scale else None, table.currency) if p
    )
    parts = [f"Table: {table.title}" if table.title else "Table", company, period_label, item]
    if units:
        parts.append(units)
    return "[" + " | ".join(parts) + "]"


def _md(cell: str) -> str:
    return cell.replace("|", "\\|")


def to_markdown(table: Table, context: str) -> str:
    width = len(table.columns)
    lines = [
        context,
        "| " + " | ".join(_md(c) for c in table.columns) + " |",
        "|" + "---|" * width,
    ]
    lines += ["| " + " | ".join(_md(c) for c in row) + " |" for row in table.body]
    return "\n".join(lines)
