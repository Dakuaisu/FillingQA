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


def main() -> None:
    line_items = load_line_items()
    record = yaml.safe_load(FREEZE_FILE.read_text(encoding="utf-8"))
    parsed = {e["accession"]: e for e in record["filings"] if e["status"] == "parsed"}
    tickers = list(dict.fromkeys(e["ticker"] for e in parsed.values()))
    all_tags = {i["tag"] for i in line_items} | {
        i["variant"] for i in line_items if i.get("variant")
    }

    spans: dict[tuple, list[tuple]] = defaultdict(list)  # key -> [(chunk_id, value, raw_text)]
    with connect() as conn:
        paths = dict(
            conn.execute(
                "SELECT accession, raw_path FROM filings WHERE accession = ANY(%s)",
                (list(parsed),),
            ).fetchall()
        )
        for accession, raw_path in paths.items():
            root = etree.fromstring(
                Path(raw_path).read_bytes(), etree.XMLParser(recover=True, huge_tree=True)
            )
            contexts = parse_contexts(root)
            for concept, ref, chunk_id, value, raw_text in conn.execute(
                "SELECT concept, context_ref, chunk_id, value, raw_text FROM xbrl_spans "
                "WHERE accession = %s AND concept = ANY(%s)",
                (accession, list(all_tags)),
            ).fetchall():
                ctx = contexts.get(ref)
                if ctx is None or ctx.is_dimensional:
                    continue  # F-32: a segment figure is not the company-level fact
                start, end = (
                    (None, ctx.instant) if ctx.instant else (ctx.period_start, ctx.period_end)
                )
                spans[(accession, concept, start, end)].append((chunk_id, value, raw_text))

        facts = conn.execute(
            """
            SELECT x.accession, c.ticker, f.form_type, x.concept, x.period_start, x.period_end,
                   x.value, x.unit
              FROM xbrl_facts x JOIN filings f USING (accession) JOIN companies c ON c.cik = f.cik
             WHERE x.accession = ANY(%s) AND x.concept = ANY(%s)
            """,
            (list(parsed), list(all_tags)),
        ).fetchall()
        tagged = {(f[1], f[3]) for f in facts}
        resolved = resolve_tags(line_items, tagged, tickers)
        by_tag = {(t, tag): item_id for (item_id, t), (tag, _) in resolved.items()}

        table: dict[tuple, Counter] = defaultdict(Counter)
        supply: dict[str, Counter] = defaultdict(Counter)
        totals: Counter = Counter()
        f72: Counter = Counter()
        queue, captions = [], {}
        revenue_pairs: dict[tuple, dict] = defaultdict(dict)
        revenue = next(i for i in line_items if i["id"] == "revenue")
        for accession, ticker, form, concept, start, end, value, unit in facts:
            period = (start.isoformat() if start else None, end.isoformat())
            if concept in (revenue["tag"], revenue["variant"]):
                revenue_pairs[(ticker, accession, period)][concept] = value
            item_id = by_tag.get((ticker, concept))
            if item_id is None:
                continue  # a tag this filer does not resolve to
            found = spans.get((accession, concept, *period), [])
            prd_gold = {cid for cid, _, _ in found if cid}
            gold = {cid for cid, v, _ in found if cid and v == value}
            b = bucket(len(gold))
            table[(item_id, ticker, form)][b] += 1
            supply[ticker][(form, b)] += 1
            totals[b] += 1
            f72["facts"] += 1
            f72["gold smaller under exact value"] += len(gold) < len(prd_gold)
            if bucket(len(prd_gold)) != b:
                f72[f"bucket {bucket(len(prd_gold))} -> {b}"] += 1
            if not gold:
                reason = "no visible span (F-48)" if not found else "no exact-value span in a chunk"
                queue.append([accession, ticker, form, concept, start, end, value, unit, reason])
            if resolved[(item_id, ticker)][1] == "variant" and (ticker, item_id) not in captions:
                hit = next(((cid, raw) for cid, v, raw in found if cid and v == value), None)
                if hit:
                    text = conn.execute(
                        "SELECT raw_text FROM chunks WHERE chunk_id = %s", (hit[0],)
                    ).fetchone()[0]
                    row = next((ln for ln in text.splitlines() if hit[1] in ln), "")
                    caption = row.strip("| ").split(" | ")[0] if row.startswith("|") else row[:80]
                    captions[(ticker, item_id)] = (concept, accession, period, hit[1], caption)

    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with QUEUE_FILE.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["accession", "ticker", "form", "concept", "period_start", "period_end",
                         "value", "unit", "reason"])  # fmt: skip
        writer.writerows(sorted(queue, key=lambda r: (r[1], r[0], r[3], str(r[5]))))

    print(f"list: {len(line_items)} line items, {len(all_tags)} tags "
          f"({CONCEPTS_FILE.relative_to(REPO_ROOT)})")  # fmt: skip
    print(f"frozen parsed accessions: {len(parsed)}; listed facts: {f72['facts']}")
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
