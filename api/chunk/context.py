"""Context lines: the chunk header (PRD 6.3 rule 3) and table serialization.

Every label here comes from the issuer's own tags or the printed table. Nothing
is inferred: a chunk that asserts a period, unit or column the filing does not
print at that location is a false grounding for any claim that cites it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from api.parse.sections import Section
from api.parse.tables import Table, context_line


@dataclass(frozen=True)
class DocumentMeta:
    accession: str
    cik: str
    ticker: str
    company_name: str
    form_type: str
    fiscal_year: int
    fiscal_period: str  # 'FY' | 'Q1' | 'Q2' | 'Q3', from dei
    period_end: date

    @property
    def fiscal_quarter(self) -> int | None:
        return int(self.fiscal_period[1:]) if self.fiscal_period.startswith("Q") else None

    @property
    def period_label(self) -> str:
        """The issuer's fiscal label, never derived from a date (finding #5)."""
        return (
            f"FY{self.fiscal_year}"
            if self.fiscal_period == "FY"
            else f"{self.fiscal_period} FY{self.fiscal_year}"
        )


def item_label(section: Section, form_type: str) -> str:
    # A 10-Q has an Item 1 in both Parts (F-04), so the Part is part of the label.
    if form_type == "10-Q" and section.part:
        return f"Part {section.part}, Item {section.item_code}"
    return f"Item {section.item_code}"


def chunk_header(meta: DocumentMeta, section: Section) -> str:
    """`[Apple Inc. (AAPL) | 10-K | FY2025 | Item 1A: Risk Factors]`"""
    item = item_label(section, meta.form_type)
    return (
        f"[{meta.company_name} ({meta.ticker}) | {meta.form_type} | {meta.period_label} | "
        f"{item}: {section.title}]"
    )


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |"


def table_lines(
    table: Table, meta: DocumentMeta, section: Section, rows: list[list[str]]
) -> list[str]:
    """Context line, then the column labels if the table prints any, then rows.

    A header-less continuation (F-50) gets no label line at all rather than an
    empty one -- and never its neighbour's labels.
    """
    lines = [context_line(table, meta.company_name, f"{meta.period_label} {meta.form_type}",
                          item_label(section, meta.form_type))]  # fmt: skip
    if any(table.columns):
        lines.append(_row(table.columns))
        lines.append("|" + "---|" * len(table.columns))
    lines.extend(_row(r) for r in rows)
    return lines
