"""Parser validation suite and parse-quality score: PRD 6.2.

Three separate steps, deliberately:

- `measure` reads quantities the parser already produces.
- `check` turns them into assertions. Any failure quarantines the filing; this is
  the only thing that does (PRD 6.2: "do not let bad parses into the index
  silently").
- `score` summarizes the same quantities as one tracked number. It never gates:
  "when you change the parser, this number tells you whether you helped".

python -m api.parse.validate
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

import psycopg

from api.config import REPO_ROOT, data_dir, parser_bounds
from api.db import connect
from api.parse.ixbrl import ExtractedDocument, extract, verify_spans, write_normalized
from api.parse.sections import (
    REQUIRED_10K_ITEMS,
    REQUIRED_10Q_ITEMS,
    detect_sections,
    missing_required,
)
from api.parse.tables import extract_tables, is_value

# The code that produces parser output. This module is excluded: it measures
# that output and changing it does not change a single offset.
PARSER_SOURCES = (
    *sorted(p for p in (REPO_ROOT / "api" / "parse").glob("*.py") if p.name != "validate.py"),
    REPO_ROOT / "api" / "numbers.py",
)


def parser_version() -> str:
    """Hash of the parser's own source. A hand-bumped version can be forgotten;
    this one cannot, which is what the F-42 freeze check relies on."""
    digest = hashlib.sha256()
    for path in PARSER_SOURCES:
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def alpha_char_ratio(text: str) -> float:
    """Letters over all characters. PRD 6.2 names it without defining it."""
    return sum(ch.isalpha() for ch in text) / len(text) if text else 0.0


@dataclass
class Measurements:
    form_type: str
    sections: int = 0
    missing_items: list[str] = field(default_factory=list)
    required_items: int = 0
    has_item_1a: bool = False
    # Text length of each required Item found, keyed as in `min_required_item_chars`.
    item_chars: dict[str, int] = field(default_factory=dict)
    data_tables: int = 0
    scaled_caption: int = 0
    scaled_ixbrl: int = 0
    scale_eligible: int = 0  # data tables with a caption or a tagged magnitude
    collapsed_tables: int = 0
    numeric_spans: int = 0
    resolved_spans: int = 0
    span_mismatches: int = 0
    alpha_ratio: float = 0.0
    fiscal_year: int | None = None
    fiscal_period: str | None = None


def _collapsed(cell: str) -> bool:
    parts = cell.split()
    return len(parts) > 1 and all(is_value(p) for p in parts)


def required_item_chars(sections: list, form_type: str) -> dict[str, int]:
    """Length of each required Item: 10-K by item code, 10-Q part-qualified."""
    if form_type == "10-K":
        wanted = set(REQUIRED_10K_ITEMS)
        return {s.item_code: s.char_end - s.char_start for s in sections if s.item_code in wanted}
    wanted = {f"{p}.{i}" for p, i in REQUIRED_10Q_ITEMS}
    return {
        s.qualified_code: s.char_end - s.char_start for s in sections if s.qualified_code in wanted
    }


def measure(doc: ExtractedDocument, form_type: str) -> Measurements:
    sections = detect_sections(doc, form_type)
    data = [t for t in extract_tables(doc) if t.kind == "data"]
    numeric = [s for s in doc.spans if s.is_numeric]
    return Measurements(
        form_type=form_type,
        sections=len(sections),
        missing_items=missing_required(sections, form_type),
        required_items=len(REQUIRED_10K_ITEMS if form_type == "10-K" else REQUIRED_10Q_ITEMS),
        # PRD 6.2: the 1A assertion is 10-K only. A 10-Q's Part II 1A is optional.
        has_item_1a=any(s.item_code == "1A" for s in sections),
        item_chars=required_item_chars(sections, form_type),
        data_tables=len(data),
        scaled_caption=sum(t.scale_source == "caption" for t in data),
        scaled_ixbrl=sum(t.scale_source == "ixbrl" for t in data),
        scale_eligible=sum(1 for t in data if t.unit_scale or t.ix_scales),
        collapsed_tables=sum(1 for t in data if any(_collapsed(c) for r in t.body for c in r[1:])),
        numeric_spans=len(numeric),
        resolved_spans=sum(1 for s in numeric if s.value is not None),
        span_mismatches=len(verify_spans(doc)),
        alpha_ratio=alpha_char_ratio(doc.text),
        fiscal_year=doc.fiscal_year,
        fiscal_period=doc.fiscal_period,
    )


def check(m: Measurements, bounds: dict) -> list[str]:
    """Failed assertions, as messages. Empty means the filing passes."""
    failures = []
    if m.sections < bounds["min_sections"]:
        failures.append(f"{m.sections} sections < {bounds['min_sections']}")
    if m.missing_items:
        failures.append(f"required Items missing: {m.missing_items}")
    floors = bounds["min_required_item_chars"].get(m.form_type, {})
    short = [
        f"Item {code} is {n} chars < {floors[code]}"
        for code, n in sorted(m.item_chars.items())
        if code in floors and n < floors[code]
    ]
    if short:
        # Existence is not content: a cross-reference stub or a mis-detected
        # section passes the required-Items check (F-66).
        failures.append("required Item too short: " + "; ".join(short))
    if m.form_type == "10-K" and not m.has_item_1a:
        failures.append("10-K has no Item 1A")
    if m.data_tables < bounds["min_data_tables"]:
        failures.append(f"{m.data_tables} data tables < {bounds['min_data_tables']}")
    lo, hi = bounds["alpha_ratio"]["min"], bounds["alpha_ratio"]["max"]
    if not lo < m.alpha_ratio < hi:
        failures.append(f"alpha ratio {m.alpha_ratio:.3f} outside ({lo}, {hi})")
    if m.fiscal_year is None:
        # TRADEOFFS finding #5: never default a fiscal label.
        failures.append("no dei:DocumentFiscalYearFocus")
    if m.span_mismatches:
        failures.append(f"{m.span_mismatches} iXBRL spans do not slice back to their text")
    return failures


def score_components(m: Measurements, bounds: dict) -> dict[str, float | None]:
    """Each in [0, 1]; None where the quantity is undefined for this filing."""
    lo, hi = bounds["alpha_ratio"]["min"], bounds["alpha_ratio"]["max"]
    scaled = m.scaled_caption + m.scaled_ixbrl
    return {
        "scale_coverage": scaled / m.scale_eligible if m.scale_eligible else None,
        "uncollapsed_tables": 1 - m.collapsed_tables / m.data_tables if m.data_tables else None,
        "span_resolution": m.resolved_spans / m.numeric_spans if m.numeric_spans else None,
        "required_items": 1 - len(m.missing_items) / m.required_items,
        "alpha_in_bounds": 1.0 if lo < m.alpha_ratio < hi else 0.0,
    }


def score(m: Measurements, bounds: dict) -> float:
    """Unweighted mean of the defined components. Equal weights because there is
    no measured basis yet for any other; an undefined component is left out
    rather than counted as perfect or as zero."""
    defined = [v for v in score_components(m, bounds).values() if v is not None]
    return sum(defined) / len(defined)


def fiscal_quarter(fiscal_period: str | None) -> int | None:
    """'Q1'..'Q3' -> 1..3. 'FY' is a 10-K, which has no quarter."""
    if fiscal_period and fiscal_period.startswith("Q") and fiscal_period[1:].isdigit():
        return int(fiscal_period[1:])
    return None


SpanRow = tuple[str, str, str, Decimal, int | None, str, int, int]


def span_rows(doc: ExtractedDocument, accession: str) -> list[SpanRow]:
    """xbrl_spans rows for one filing: numeric spans with a parsed value.

    `xbrl_spans.value` is NOT NULL and PRD 6.5.2 scopes the table to
    ix:nonFraction, so word-form figures that do not parse (F-33) are left out
    rather than given an invented value; `span_resolution` already counts them.
    Dimensional contexts are kept -- filtering them is Phase 3's job (F-32).
    """
    return [
        (
            accession,
            s.concept,
            s.context_ref,
            s.value,
            s.scale,
            s.raw_text,
            s.char_start,
            s.char_end,
        )
        for s in doc.spans
        if s.is_numeric and s.value is not None
    ]


_INSERT_SPAN = """
    INSERT INTO xbrl_spans
        (accession, concept, context_ref, value, scale, raw_text, char_start, char_end)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""


def validate_filing(
    conn: psycopg.Connection, accession: str, form_type: str, raw_path: str, version: str
) -> tuple[Measurements, list[str], float, int]:
    bounds = parser_bounds()
    doc = extract(Path(raw_path).read_bytes())
    m = measure(doc, form_type)
    failures = check(m, bounds)
    value = score(m, bounds)

    norm_path = data_dir() / "norm" / f"{accession}.txt"
    write_normalized(doc, norm_path)
    rows = [] if failures else span_rows(doc, accession)

    # One transaction per filing: the spans' offsets mean something only against
    # the text at norm_path, so the two must never be out of step (F-42). A
    # quarantined filing keeps no spans -- a bad parse feeds nothing downstream.
    with conn.transaction():
        conn.execute("DELETE FROM xbrl_spans WHERE accession = %s", (accession,))
        with conn.cursor() as cur:
            cur.executemany(_INSERT_SPAN, rows)
        conn.execute(
            """
        UPDATE filings
           SET parse_status = %s, parse_error = %s, parse_score = %s,
               parser_version = %s, norm_path = %s,
               fiscal_year = %s, fiscal_quarter = %s
         WHERE accession = %s
        """,
            (
                "quarantined" if failures else "parsed",
                "; ".join(failures) or None,
                value,
                version,
                str(norm_path),
                m.fiscal_year,
                fiscal_quarter(m.fiscal_period),
                accession,
            ),
        )
    return m, failures, value, len(rows)


def main() -> None:
    version = parser_version()
    print(f"parser_version {version}")
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT c.ticker, f.accession, f.form_type, f.raw_path
              FROM filings f JOIN companies c USING (cik)
             ORDER BY c.ticker, f.filing_date
            """
        ).fetchall()
        # End the read's implicit transaction, so each filing's
        # conn.transaction() below is a real transaction and not a savepoint.
        conn.commit()
        bounds = parser_bounds()
        print(
            f"{'ticker':6} {'accession':22} {'form':4} {'FY':>4} {'fp':>2} {'sect':>4} "
            f"{'miss':>4} {'data':>4} {'alpha':>5} {'scale':>5} {'uncol':>5} {'spans':>5} "
            f"{'items':>5} {'score':>5} {'rows':>5} {'skip':>4}  status"
        )
        for ticker, accession, form_type, raw_path in rows:
            m, failures, value, written = validate_filing(
                conn, accession, form_type, raw_path, version
            )
            c = score_components(m, bounds)

            def f(x: float | None) -> str:
                return "  n/a" if x is None else f"{x:5.3f}"

            print(
                f"{ticker:6} {accession:22} {form_type:4} {m.fiscal_year or '-':>4} "
                f"{m.fiscal_period or '-':>2} {m.sections:4} {len(m.missing_items):4} "
                f"{m.data_tables:4} {m.alpha_ratio:5.3f} {f(c['scale_coverage'])} "
                f"{f(c['uncollapsed_tables'])} {f(c['span_resolution'])} "
                f"{f(c['required_items'])} {value:5.3f} {written:5} "
                f"{m.numeric_spans - m.resolved_spans:4}  "
                + ("quarantined: " + "; ".join(failures) if failures else "parsed")
            )


if __name__ == "__main__":
    main()
