"""The xbrl_auto pool and a seeded draw over it. No question text, no dataset file.

python -m scripts.xbrl_pool                  # accounting, review queue, draw
python -m scripts.xbrl_pool --write-fixture  # real rows/spans for the pool and gold tests

Writes eval/review_queue.csv: every fact whose key is routed to review, with the
reason (value_differs, mixed_key, gt3).
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict

import yaml

from api.config import REPO_ROOT, eval_sampler
from eval.generate.pool import ELIGIBLE, NOT_SAMPLED, REVIEW_REASONS, Shortfall, build_pool, sample
from scripts.concept_coverage import classify_facts, load_spans_and_facts
from scripts.write_freeze import FREEZE_FILE

REVIEW_FILE = REPO_ROOT / "eval" / "review_queue.csv"
FIXTURE_FILE = REPO_ROOT / "tests" / "fixtures" / "xbrl_pool_rows.json"
GOLD_FIXTURE_FILE = REPO_ROOT / "tests" / "fixtures" / "xbrl_gold_spans.json"
# Every span of these (accession, concept, period) keys, for tests/unit/test_gold.py:
# PFE total assets with a rounded "201" (billion) mention (F-72); AAPL FY2024 net
# income, also tagged on dimensional equity-statement contexts (F-32).
GOLD_FIXTURE_KEYS = (
    ("0000078003-26-000095", "us-gaap:Assets", None, "2026-06-28"),
    ("0000320193-25-000079", "us-gaap:NetIncomeLoss", "2023-10-01", "2024-09-28"),
)
FIXTURE_FIELDS = (
    "fact_id", "cik", "accession", "ticker", "form", "line_item", "concept", "period",
    "value", "unit", "is_comparative", "filing_fiscal_year", "filing_fiscal_quarter",
    "gold", "bucket", "exact_scales",
)  # fmt: skip
# (ticker, line item) pairs whose rows cover every pool category.
FIXTURE_SLICE = {
    ("TGT", "cost_of_revenue"), ("TGT", "sga"), ("JPM", "net_income"),
    ("BAC", "total_assets"), ("PFE", "income_tax"), ("XOM", "eps_diluted"),
    ("AAPL", "inventory"), ("COST", "income_tax"), ("PFE", "share_repurchases"),
    ("TGT", "share_repurchases"), ("PFE", "eps_diluted"), ("NVDA", "income_tax"),
}  # fmt: skip


def fixture_header() -> dict:
    record = yaml.safe_load(FREEZE_FILE.read_text(encoding="utf-8"))
    return {
        "source": "python -m scripts.xbrl_pool --write-fixture",
        "parser_version": record["parser_version"],  # chunk ids depend on both
        "chunker_version": record["chunker_version"],
    }


def write_fixtures(rows: list[dict]) -> None:
    out = [
        {k: (str(r[k]) if k == "value" else r[k]) for k in FIXTURE_FIELDS}
        for r in rows
        if (r["ticker"], r["line_item"]) in FIXTURE_SLICE
    ]
    out.sort(key=lambda r: r["fact_id"])
    doc = {**fixture_header(), "rows": out}
    FIXTURE_FILE.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {len(out)} rows to {FIXTURE_FILE.relative_to(REPO_ROOT)}")

    _, _, spans, facts = load_spans_and_facts()
    keys = []
    for acc, concept, start, end in GOLD_FIXTURE_KEYS:
        fact = next(
            f for f in facts
            if (f[2], f[5], f[6].isoformat() if f[6] else None, f[7].isoformat())
            == (acc, concept, start, end)
        )  # fmt: skip
        keys.append({
            "accession": acc, "concept": concept, "period": [start, end],
            "fact_id": fact[0], "fact_value": str(fact[8]),
            "spans": [
                {"chunk_id": sp.chunk_id, "value": str(sp.value), "raw_text": sp.raw_text,
                 "scale": sp.scale, "dimensional": sp.dimensional}
                for sp in spans[(acc, concept, start, end)]
            ],
        })  # fmt: skip
    doc = {**fixture_header(), "keys": keys}
    GOLD_FIXTURE_FILE.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {sum(len(k['spans']) for k in keys)} spans to "
          f"{GOLD_FIXTURE_FILE.relative_to(REPO_ROOT)}")  # fmt: skip


def main() -> None:
    _, tickers, _, rows, _ = classify_facts()
    if "--write-fixture" in sys.argv:
        write_fixtures(rows)
        return
    pool = build_pool(rows)
    cats = Counter(pool.category[r["fact_id"]] for r in rows)
    print(f"facts: {len(rows)}; by category: {dict(sorted(cats.items()))}; "
          f"sum {sum(cats.values())}")  # fmt: skip
    assert sum(cats.values()) == len(rows) == len(pool.category)
    key_cats = Counter()
    seen = set()
    for r in rows:
        k = (r["cik"], r["concept"], *r["period"])
        if k not in seen:
            seen.add(k)
            key_cats[pool.category[r["fact_id"]]] += 1
    print(f"keys: {len(seen)}; by category: {dict(sorted(key_cats.items()))}")

    review = [r for r in rows if pool.category[r["fact_id"]] in REVIEW_REASONS]
    with REVIEW_FILE.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["reason", "fact_id", "accession", "ticker", "form", "line_item", "concept",
                    "period_start", "period_end", "value", "unit", "is_comparative",
                    "gold_chunks"])  # fmt: skip
        for r in sorted(review, key=lambda r: (pool.category[r["fact_id"]], r["fact_id"])):
            w.writerow([pool.category[r["fact_id"]], r["fact_id"], r["accession"], r["ticker"],
                        r["form"], r["line_item"], r["concept"], r["period"][0], r["period"][1],
                        r["value"], r["unit"], r["is_comparative"], len(r["gold"])])  # fmt: skip
    reasons = dict(sorted(Counter(pool.category[r["fact_id"]] for r in review).items()))
    print(f"review queue ({REVIEW_FILE.relative_to(REPO_ROOT)}): {len(review)} facts, {reasons}")

    print("\neligible keys and strata per ticker (strata = line item x own-period form):")
    for t in tickers:
        ks = [k for k in pool.eligible if k.ticker == t]
        forms = Counter(k.own_form for k in ks)
        print(f"  {t:5} keys {len(ks):4}  strata {len({k.stratum for k in ks}):3}  "
              f"10-K {forms['10-K']:3}  10-Q {forms['10-Q']:4}")  # fmt: skip

    print("\nline items a filer has facts for but no eligible key, and why (fact categories):")
    has = defaultdict(Counter)
    for r in rows:
        has[(r["ticker"], r["line_item"])][pool.category[r["fact_id"]]] += 1
    for (t, item), c in sorted(has.items()):
        if not c[ELIGIBLE]:
            print(f"  {t:5} {item:24} {dict(sorted(c.items()))}")
    only_c = sorted(k for k, c in has.items() if not c[ELIGIBLE] and set(c) == {NOT_SAMPLED})
    print(f"  emptied by (c) alone: {only_c or 'none'}")

    cfg = eval_sampler()
    print(f"\ndraw: seed {cfg['seed']}, total {cfg['total']}, per ticker {cfg['per_ticker']}")
    try:
        draw = sample(pool.eligible, cfg["seed"], cfg["total"], cfg["per_ticker"])
    except Shortfall as e:
        print(f"SHORTFALL, no draw: {e}")
        sys.exit(1)
    print(f"drawn keys: {len(draw)}; distinct: {len({k.key for k in draw})}")
    dist = Counter(k.stratum for k in draw)
    for t in tickers:
        cells = sorted((item, form, n) for (tt, item, form), n in dist.items() if tt == t)
        print(f"  {t:5} " + ", ".join(f"{item}/{form} {n}" for item, form, n in cells))
    print(f"draw by form: {dict(Counter(k.own_form for k in draw))}; "
          f"distinct line items: {len({k.line_item for k in draw})}")  # fmt: skip


if __name__ == "__main__":
    main()
