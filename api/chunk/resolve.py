"""Resolve each xbrl_span to the chunk that contains it. Phase 2 step 2.

python -m api.chunk.resolve

A span belongs to a chunk whose [char_start, char_end) contains it. Table chunks
never overlap anything (split parts tile their table), so a span in a table has
one candidate. Prose can have two, for reasons counted separately:

- overlap: consecutive prose chunks share trailing paragraphs (PRD 6.3 rule 4);
- split paragraph: sentence pieces of an oversized paragraph share the block's
  offsets (chunker decision 6, kept for prose).

With several candidates the earliest chunk wins. Spans before the first Item have
no chunk by design (chunker decision 1) and are reported apart, so the resolve
rate's denominator is explained.
"""

from __future__ import annotations

from dataclasses import dataclass

from api.config import span_resolution
from api.db import connect


@dataclass
class Resolution:
    spans: int = 0
    before_first_item: int = 0
    unique: int = 0
    overlap: int = 0
    split_paragraph: int = 0
    unresolved_in_item: int = 0

    @property
    def resolved(self) -> int:
        return self.unique + self.overlap + self.split_paragraph

    @property
    def rate(self) -> float:
        return self.resolved / self.spans if self.spans else 0.0

    @property
    def rate_in_items(self) -> float:
        within = self.spans - self.before_first_item
        return self.resolved / within if within else 0.0


ChunkRange = tuple[str, int, int]  # chunk_id, char_start, char_end
SpanRange = tuple[int, int, int]  # span_id, char_start, char_end


def resolve(spans: list[SpanRange], chunks: list[ChunkRange]) -> tuple[dict[int, str], Resolution]:
    """span_id -> chunk_id for every span that lands in a chunk."""
    stats = Resolution(spans=len(spans))
    ordered = sorted(chunks, key=lambda c: (c[1], c[0]))
    first_item = ordered[0][1] if ordered else None
    assigned: dict[int, str] = {}
    for span_id, start, end in spans:
        owners = [c for c in ordered if c[1] <= start and end <= c[2]]
        if not owners:
            if first_item is None or start < first_item:
                stats.before_first_item += 1
            else:
                stats.unresolved_in_item += 1
            continue
        assigned[span_id] = owners[0][0]
        if len(owners) == 1:
            stats.unique += 1
        elif len({(c[1], c[2]) for c in owners}) < len(owners):
            stats.split_paragraph += 1
        else:
            stats.overlap += 1
    return assigned, stats


def main() -> None:
    floor = span_resolution()["min_rate"]
    totals = Resolution()
    with connect() as conn:
        filings = conn.execute(
            """
            SELECT c.ticker, f.accession FROM filings f JOIN companies c USING (cik)
             WHERE f.parse_status = 'parsed' ORDER BY c.ticker, f.filing_date
            """
        ).fetchall()
        conn.commit()
        print(
            f"{'ticker':6} {'accession':22} {'spans':>5} {'preItem':>7} {'unique':>6} "
            f"{'overlap':>7} {'splitPara':>9} {'unresInItem':>11} {'rate':>6} {'inItems':>7}"
        )
        for ticker, accession in filings:
            chunks = conn.execute(
                "SELECT chunk_id, char_start, char_end FROM chunks WHERE accession = %s",
                (accession,),
            ).fetchall()
            spans = conn.execute(
                "SELECT span_id, char_start, char_end FROM xbrl_spans WHERE accession = %s",
                (accession,),
            ).fetchall()
            assigned, r = resolve(spans, chunks)
            with conn.transaction():
                conn.execute(
                    "UPDATE xbrl_spans SET chunk_id = NULL WHERE accession = %s", (accession,)
                )
                with conn.cursor() as cur:
                    cur.executemany(
                        "UPDATE xbrl_spans SET chunk_id = %s WHERE span_id = %s",
                        [(chunk_id, span_id) for span_id, chunk_id in assigned.items()],
                    )
            for field in ("spans", "before_first_item", "unique", "overlap",
                          "split_paragraph", "unresolved_in_item"):  # fmt: skip
                setattr(totals, field, getattr(totals, field) + getattr(r, field))
            print(
                f"{ticker:6} {accession:22} {r.spans:5} {r.before_first_item:7} {r.unique:6} "
                f"{r.overlap:7} {r.split_paragraph:9} {r.unresolved_in_item:11} "
                f"{r.rate:6.3f} {r.rate_in_items:7.3f}"
            )
    print(
        f"total spans {totals.spans}, resolved {totals.resolved} ({totals.rate:.3f}; "
        f"{totals.rate_in_items:.3f} within Items), before first Item {totals.before_first_item}"
    )
    if totals.rate < floor:
        raise SystemExit(f"span resolution {totals.rate:.3f} < {floor}: offsets did not survive")


if __name__ == "__main__":
    main()
