"""Concept coverage on the frozen corpus (F-15) for the list in eval/concepts.yaml.

python -m scripts.concept_coverage

Measurement only: generates no eval item and runs no retrieval.

- Facts: linked facts of the parsed accessions in api/corpus_freeze.yaml.
- Tag per filer: a line item's named tag; its variant only for a filer with no
  fact under the named tag in that set (eval/concepts.yaml).
- Gold chunks of a fact: distinct chunks holding a span of the same accession,
  concept and period, on a NON-dimensional context (F-32), whose value equals
  the fact's (F-72). PRD 6.5.3's literal key -- context only -- is measured
  beside it.
- Buckets (PRD 6.5.3): 0 gold -> human labeling, 1-3 -> auto, >3 -> review.

Writes eval/human_label_queue.csv (every listed fact with no gold chunk) and
prints the table, list totals, per-ticker supply, F-72 counts, the two-revenue-
tag check, and one printed row caption per variant-only filer.
"""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from pathlib import Path

import yaml
from lxml import etree

from api.config import REPO_ROOT
from api.db import connect
from api.parse.ixbrl import parse_contexts
from eval.generate.gold import Span, select_gold
from scripts.write_freeze import FREEZE_FILE

CONCEPTS_FILE = REPO_ROOT / "eval" / "concepts.yaml"
QUEUE_FILE = REPO_ROOT / "eval" / "human_label_queue.csv"


def bucket(n: int) -> str:
    return "0" if n == 0 else "1-3" if n <= 3 else ">3"


def load_line_items() -> list[dict]:
    return yaml.safe_load(CONCEPTS_FILE.read_text(encoding="utf-8"))["line_items"]


def resolve_tags(line_items: list[dict], tagged: set[tuple[str, str]], tickers: list[str]):
    """(line item id, ticker) -> (tag, 'named' | 'variant'), only where the filer has facts."""
    out = {}
    for item in line_items:
        for ticker in tickers:
            if (ticker, item["tag"]) in tagged:
                out[(item["id"], ticker)] = (item["tag"], "named")
            elif item.get("variant") and (ticker, item["variant"]) in tagged:
                out[(item["id"], ticker)] = (item["variant"], "variant")
    return out


def load_spans_and_facts():
    """(line_items, tickers, spans, facts) for the frozen parsed accessions.

    `spans` maps (accession, concept, period_start, period_end) to every span of
    a listed tag on that period, dimensional ones flagged, in table order.
    """
    line_items = load_line_items()
    record = yaml.safe_load(FREEZE_FILE.read_text(encoding="utf-8"))
    parsed = {e["accession"]: e for e in record["filings"] if e["status"] == "parsed"}
    tickers = list(dict.fromkeys(e["ticker"] for e in parsed.values()))
    all_tags = {i["tag"] for i in line_items} | {
        i["variant"] for i in line_items if i.get("variant")
    }
    spans: dict[tuple, list[Span]] = defaultdict(list)
    with connect() as conn:
        for accession, raw_path in conn.execute(
            "SELECT accession, raw_path FROM filings WHERE accession = ANY(%s)", (list(parsed),)
        ).fetchall():
            contexts = parse_contexts(
                etree.fromstring(
                    Path(raw_path).read_bytes(), etree.XMLParser(recover=True, huge_tree=True)
                )
            )
            for concept, ref, chunk_id, value, raw_text, scale in conn.execute(
                "SELECT concept, context_ref, chunk_id, value, raw_text, scale FROM xbrl_spans "
                "WHERE accession = %s AND concept = ANY(%s) ORDER BY span_id",
                (accession, list(all_tags)),
            ).fetchall():
                ctx = contexts.get(ref)
                if ctx is None:
                    continue
                start, end = (
                    (None, ctx.instant) if ctx.instant else (ctx.period_start, ctx.period_end)
                )
                spans[(accession, concept, start, end)].append(
                    Span(chunk_id, value, raw_text, scale, ctx.is_dimensional)
                )
        facts = conn.execute(
            """
            SELECT x.fact_id, x.cik, x.accession, c.ticker, f.form_type, x.concept,
                   x.period_start, x.period_end, x.value, x.unit, x.is_comparative,
                   f.fiscal_year, f.fiscal_quarter
              FROM xbrl_facts x JOIN filings f USING (accession) JOIN companies c ON c.cik = f.cik
             WHERE x.accession = ANY(%s) AND x.concept = ANY(%s)
             ORDER BY x.fact_id
            """,
            (list(parsed), list(all_tags)),
        ).fetchall()
    return line_items, tickers, spans, facts


def classify_facts():
    """Every listed fact with its resolved line item and gold chunks; the one loader.

    Returns (line_items, tickers, resolved, rows, unresolved). `rows` are the facts
    under the tag their filer resolves to; `unresolved` the facts under a listed
    tag the filer does not resolve to (kept for the two-revenue-tag check). Gold
    is `eval.generate.gold.select_gold`.
    """
    line_items, tickers, spans, facts = load_spans_and_facts()
    resolved = resolve_tags(line_items, {(f[3], f[5]) for f in facts}, tickers)
    by_tag = {(t, tag): item_id for (item_id, t), (tag, _) in resolved.items()}
    rows, unresolved = [], []
    for fid, cik, acc, ticker, form, concept, start, end, value, unit, comp, fy, fq in facts:
        period = (start.isoformat() if start else None, end.isoformat())
        sel = select_gold(value, spans.get((acc, concept, *period), []))
        row = {
            "fact_id": fid, "cik": cik, "accession": acc, "ticker": ticker, "form": form,
            "line_item": by_tag.get((ticker, concept)), "concept": concept, "period": period,
            "value": value, "unit": unit, "is_comparative": comp,
            "filing_fiscal_year": fy, "filing_fiscal_quarter": fq,
            "gold": list(sel.gold), "bucket": bucket(len(sel.gold)),
            "exact_spans": [(s.chunk_id, s.raw_text) for s in sel.exact],
            "exact_scales": sorted({s.scale for s in sel.exact}, key=lambda x: (x is None, x)),
            "prd_gold_count": sel.prd_key_count, "has_span": sel.has_span,
        }  # fmt: skip
        (rows if row["line_item"] else unresolved).append(row)
    return line_items, tickers, resolved, rows, unresolved


def main() -> None:
    line_items, tickers, resolved, rows, unresolved = classify_facts()
    all_tags = {i["tag"] for i in line_items} | {
        i["variant"] for i in line_items if i.get("variant")
    }
    accessions = {r["accession"] for r in rows + unresolved}

    table: dict[tuple, Counter] = defaultdict(Counter)
    supply: dict[str, Counter] = defaultdict(Counter)
    totals: Counter = Counter()
    f72: Counter = Counter()
    queue, captions = [], {}
    revenue_pairs: dict[tuple, dict] = defaultdict(dict)
    revenue = next(i for i in line_items if i["id"] == "revenue")
    for r in sorted(rows + unresolved, key=lambda r: r["fact_id"]):
        ticker, accession, concept, period = r["ticker"], r["accession"], r["concept"], r["period"]
        if concept in (revenue["tag"], revenue["variant"]):
            revenue_pairs[(ticker, accession, period)][concept] = r["value"]
    with connect() as conn:
        for r in rows:
            item_id, ticker, form, b = r["line_item"], r["ticker"], r["form"], r["bucket"]
            table[(item_id, ticker, form)][b] += 1
            supply[ticker][(form, b)] += 1
            totals[b] += 1
            f72["facts"] += 1
            f72["gold smaller under exact value"] += len(r["gold"]) < r["prd_gold_count"]
            if bucket(r["prd_gold_count"]) != b:
                f72[f"bucket {bucket(r['prd_gold_count'])} -> {b}"] += 1
            if not r["gold"]:
                reason = (
                    "no visible span (F-48)"
                    if not r["has_span"]
                    else "no exact-value span in a chunk"
                )
                start, end = r["period"]
                queue.append([r["accession"], ticker, form, r["concept"], start, end,
                              r["value"], r["unit"], reason])  # fmt: skip
            if (
                resolved[(item_id, ticker)][1] == "variant"
                and (ticker, item_id) not in captions
                and r["exact_spans"]
            ):
                cid, raw = r["exact_spans"][0]
                text = conn.execute(
                    "SELECT raw_text FROM chunks WHERE chunk_id = %s", (cid,)
                ).fetchone()[0]
                line = next((ln for ln in text.splitlines() if raw in ln), "")
                caption = line.strip("| ").split(" | ")[0] if line.startswith("|") else line[:80]
                captions[(ticker, item_id)] = (
                    r["concept"], r["accession"], r["period"], raw, caption,
                )  # fmt: skip

    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with QUEUE_FILE.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["accession", "ticker", "form", "concept", "period_start", "period_end",
                         "value", "unit", "reason"])  # fmt: skip
        writer.writerows(sorted(queue, key=lambda r: (r[1], r[0], r[3], str(r[5]))))

    print(f"list: {len(line_items)} line items, {len(all_tags)} tags "
          f"({CONCEPTS_FILE.relative_to(REPO_ROOT)})")  # fmt: skip
    print(f"frozen parsed accessions: {len(accessions)}; listed facts: {f72['facts']}")
    print(f"buckets on exact-value gold: 0 {totals['0']}, 1-3 {totals['1-3']}, >3 {totals['>3']}")
    print(f"human-label queue ({QUEUE_FILE.relative_to(REPO_ROOT)}): {len(queue)}")
    print(f"F-72, exact-value gold vs PRD 6.5.3 context key: "
          f"{ {k: v for k, v in f72.items() if k != 'facts'} }\n")  # fmt: skip

    print("cell = tag (N named / V variant) and facts as 0 / 1-3 / >3 gold chunks; '-' = none")
    print(f"{'line item':26} {'form':4} " + " ".join(f"{t:>15}" for t in tickers))
    for item in line_items:
        for form in ("10-K", "10-Q"):
            cells = []
            for t in tickers:
                c = table.get((item["id"], t, form))
                kind = resolved.get((item["id"], t), (None, None))[1]
                mark = "N" if kind == "named" else "V"
                cells.append(f"{mark} {c['0']:>3}/{c['1-3']:>3}/{c['>3']:>3}" if c else "-")
            print(f"{item['id'][:26]:26} {form:4} " + " ".join(f"{x:>15}" for x in cells))

    print("\nper-ticker supply (facts by bucket 0 / 1-3 / >3):")
    for t in tickers:
        s = supply[t]
        k = "/".join(str(s[("10-K", b)]) for b in ("0", "1-3", ">3"))
        q = "/".join(str(s[("10-Q", b)]) for b in ("0", "1-3", ">3"))
        print(f"  {t:5} 10-K {k:>12}   10-Q {q:>12}")

    print("\nvariant resolution:")
    for item in line_items:
        if item.get("variant"):
            named = [t for t in tickers if resolved.get((item["id"], t), ("", ""))[1] == "named"]
            variant = [
                t for t in tickers if resolved.get((item["id"], t), ("", ""))[1] == "variant"
            ]
            print(f"  {item['id']}: named {named}; variant {variant}")

    print("\ntwo-tag check -- filings with facts under both revenue tags for one period:")
    both = sorted(k for k, v in revenue_pairs.items() if len(v) == 2)
    for ticker, accession, period in both:
        v = revenue_pairs[(ticker, accession, period)]
        named, var = v[revenue["tag"]], v[revenue["variant"]]
        same = "equal" if named == var else "DIFFERENT"
        print(f"  {ticker:5} {accession} {period[0]}..{period[1]}  Revenues {named}  "
              f"RevenueFromContract... {var}  {same}")  # fmt: skip

    print("\nvariant captions -- one exact-value gold span per variant-only filer:")
    for (ticker, item_id), (concept, accession, period, raw, caption) in sorted(captions.items()):
        print(
            f"  {ticker:5} {item_id:16} {concept.split(':')[1]} {accession} {period[1]}: "
            f"printed {raw!r} in row {caption!r}"
        )


if __name__ == "__main__":
    main()
