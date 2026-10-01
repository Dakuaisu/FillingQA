"""Supply for xbrl_auto comparison items (PRD 11.1 comparison row, Stage 3). Measurement only.

python -m scripts.comparison_supply

A pair is two eligible keys (F-75) of one filer and line item, same period kind
and fiscal quarter, one or two fiscal years apart by the own-period filing's dei
label. Reports, by group (kind, gap):
- consecutive-year duration pairs (annual, year-ago quarter, year-to-date);
- whether one chunk holds both exact values (a shared gold chunk);
- the pairs that need two chunks: per-ticker supply without the drawn
  xbrl_numeric keys, evidence-set sizes, edge values;
- untagged co-occurrence: a chunk of the filer whose text prints both sides'
  printed values though neither is tagged there for this pair;
- sides printing at different scales; sides with equal values.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict

from api.config import eval_sampler
from api.db import connect
from eval.generate.pool import build_pool, sample
from eval.generate.xbrl_items import period_info
from scripts.concept_coverage import classify_facts

KINDS = ("annual", "quarter", "ytd")
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def chunks(k) -> set[str]:
    return {c for _, cs in k.evidence for c in cs}


def tokens(text: str) -> set[str]:
    return {m.group(0).rstrip(",") for m in NUMBER.finditer(text)}


def by_group(ps) -> dict[str, int]:
    return {f"{k}/gap{g}": n for (k, g), n in sorted(Counter((p[0], p[1]) for p in ps).items())}


def main() -> None:
    _, tickers, _, rows, _ = classify_facts()
    pool = build_pool(rows)
    cfg = eval_sampler()
    drawn = {k.key for k in sample(pool.eligible, cfg["seed"], cfg["total"], cfg["per_ticker"])}
    printed: dict[tuple, set[str]] = defaultdict(set)
    for r in rows:
        for _, raw in r["exact_spans"]:
            printed[(r["cik"], r["concept"], *r["period"])] |= tokens(raw or "")

    slots: dict[tuple, list] = defaultdict(list)
    for k in pool.eligible:
        slots[(k.cik, k.line_item, period_info(k).kind, k.fiscal_quarter, k.fiscal_year)].append(k)
    dup = sum(1 for v in slots.values() if len(v) > 1)
    print(f"eligible keys: {len(pool.eligible)}; slots holding more than one key: {dup}")

    pairs = []  # (kind, gap, earlier, later)
    for (cik, item, kind, q, fy), ks in sorted(slots.items(), key=lambda s: str(s[0])):
        for gap in (1, 2):
            prev = slots.get((cik, item, kind, q, fy - gap))
            if prev and len(ks) == 1 and len(prev) == 1:
                pairs.append((kind, gap, prev[0], ks[0]))
    shared = lambda p: bool(chunks(p[2]) & chunks(p[3]))  # noqa: E731
    groups = Counter((kind, gap) for kind, gap, _, _ in pairs)
    single = Counter((kind, gap) for kind, gap, a, b in pairs if shared((kind, gap, a, b)))
    print("\npairs by (kind, gap): total / one chunk holds both exact values")
    for g in sorted(groups):
        print(f"  {g[0]:8} gap {g[1]}: {groups[g]:4} / {single[g]:4}")
    inst = Counter(
        ("year-end" if a.fiscal_quarter is None else "quarter-end", shared(p))
        for p in pairs for kind, gap, a, b in [p] if kind == "instant" and gap == 1
    )  # fmt: skip
    print(
        f"  instant gap 1 by (year-end or quarter-end, shared chunk): {dict(sorted(inst.items()))}"
    )
    consecutive = [p for p in pairs if p[0] in KINDS and p[1] == 1]
    print(f"  consecutive-year duration pairs: {len(consecutive)}; "
          f"with a shared chunk: {sum(map(shared, consecutive))}")  # fmt: skip

    two = [p for p in pairs if not shared(p)]
    print(f"\npairs needing two chunks (no shared gold chunk): {len(two)} {by_group(two)}")
    free = [p for p in two if p[2].key not in drawn and p[3].key not in drawn]
    print(f"  of which neither side is a drawn xbrl_numeric key: {len(free)}")
    per = defaultdict(Counter)
    for kind, _, a, _ in free:
        per[a.ticker][kind] += 1
    print("  per ticker, no drawn key (quarter / ytd / instant / total / line items):")
    for t in tickers:
        c = per[t]
        items = len({a.line_item for _, _, a, _ in free if a.ticker == t})
        row = f"{c['quarter']:4} {c['ytd']:4} {c['instant']:4} {sum(c.values()):5} {items:4}"
        print(f"    {t:5} {row}")
    sets = Counter(len(chunks(a)) * len(chunks(b)) for _, _, a, b in free)
    print(f"  evidence sets per pair, every (a, b) combination: {dict(sorted(sets.items()))}")
    zero = sum(1 for *_, a, b in free if a.value == 0 or b.value == 0)
    neg = sum(1 for *_, a, b in free if a.value < 0 or b.value < 0)
    flip = sum(1 for *_, a, b in free if a.value * b.value < 0)
    print(f"  edge values: zero side {zero}; negative side {neg}; sign flip {flip}")
    equal = [p for p in free if p[2].value == p[3].value]
    print(f"  equal values: {len(equal)}")
    for _, _, a, b in equal:
        print(f"    {a.ticker} {a.line_item} {a.period_end} / {b.period_end}: {a.value}")
    mismatch = [
        p for p in free
        if p[2].unit == "USD" and (len(set(p[2].own_scales) | set(p[3].own_scales)) > 1)
    ]  # fmt: skip
    print(f"  sides printing at different (or several) scales, USD: {len(mismatch)}")
    for _, _, a, b in mismatch:
        print(f"    {a.ticker} {a.line_item} {a.period_end} {a.own_scales} / "
              f"{b.period_end} {b.own_scales}")  # fmt: skip

    ciks = sorted({p[2].cik for p in free})
    index: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    with connect() as conn:
        for cik, cid, raw in conn.execute(
            "SELECT cik, chunk_id, raw_text FROM chunks WHERE cik = ANY(%s)", (ciks,)
        ):
            for tok in tokens(raw):
                index[cik][tok].add(cid)
    co = []
    for p in free:
        a, b = p[2], p[3]
        hits_a = set().union(*(index[a.cik].get(t, set()) for t in printed[a.key]))
        hits_b = set().union(*(index[b.cik].get(t, set()) for t in printed[b.key]))
        both = hits_a & hits_b
        if both:
            co.append((p, both))
    print(f"\nuntagged co-occurrence: pairs with a chunk printing both sides' values: {len(co)} "
          f"of {len(free)}; by group {by_group([p for p, _ in co])}")  # fmt: skip
    print(f"  chunks per such pair: {dict(sorted(Counter(len(c) for _, c in co).items()))}")
    for (kind, gap, a, b), cs in co:
        print(f"    {a.ticker} {a.line_item} {kind}/gap{gap} "
              f"{a.period_end} ({sorted(printed[a.key])}) / "
              f"{b.period_end} ({sorted(printed[b.key])}): {sorted(cs)[:3]}")  # fmt: skip


if __name__ == "__main__":
    main()
