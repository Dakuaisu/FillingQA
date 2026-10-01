"""What the xbrl_auto item schema and sampler would draw on. Measurement only.

python -m scripts.item_supply

No eval item is generated. Reads the same facts as scripts/concept_coverage.py
(`classify_facts`) and reports:
- cross-filing duplication: distinct (cik, concept, period_start, period_end)
  keys, how many appear in more than one parsed accession, how many differ in
  value across accessions;
- sampler strata: ticker x line item x form over the 1-3 bucket only;
- line items entirely in the >3 bucket for a filer.
The review queue is written by scripts/xbrl_pool.py.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from scripts.concept_coverage import classify_facts


def main() -> None:
    _, _, _, rows, _ = classify_facts()
    print(f"listed facts: {len(rows)}; buckets {dict(Counter(r['bucket'] for r in rows))}")

    keys: dict[tuple, list[dict]] = defaultdict(list)
    for r in rows:
        keys[(r["cik"], r["concept"], *r["period"])].append(r)
    multi = {k: v for k, v in keys.items() if len({r["accession"] for r in v}) > 1}
    differ = {k: v for k, v in multi.items() if len({r["value"] for r in v}) > 1}
    print("\ncross-filing duplication:")
    print(f"  distinct (cik, concept, period_start, period_end) keys: {len(keys)}")
    spread = Counter(len({r["accession"] for r in v}) for v in multi.values())
    print(f"  in more than one parsed accession: {len(multi)} "
          f"(accessions per such key: {dict(sorted(spread.items()))})")  # fmt: skip
    print(f"  of those, value differs across accessions: {len(differ)}")
    for k, v in sorted(differ.items())[:12]:
        ticker = v[0]["ticker"]
        vals = sorted({(r["accession"], r["value"]) for r in v})
        print(f"    {ticker:5} {k[1].split(':')[1]} {k[2]}..{k[3]}: {vals}")
    own = sum(1 for v in keys.values() if any(not r["is_comparative"] for r in v))
    only_comp = len(keys) - own
    print(f"  keys reported by a filing whose own period it is: {own}; "
          f"only as a later filing's comparative: {only_comp}")  # fmt: skip
    per_key_bucket = Counter(
        "all 1-3"
        if all(r["bucket"] == "1-3" for r in v)
        else "all >3"
        if all(r["bucket"] == ">3" for r in v)
        else "mixed"
        for v in keys.values()
    )
    print(f"  keys by their facts' buckets: {dict(per_key_bucket)}")

    strata: dict[tuple, int] = Counter(
        (r["ticker"], r["line_item"], r["form"]) for r in rows if r["bucket"] == "1-3"
    )
    key_strata: dict[tuple, set] = defaultdict(set)
    for r in rows:
        if r["bucket"] == "1-3":
            key_strata[(r["ticker"], r["line_item"], r["form"])].add(
                (r["cik"], r["concept"], *r["period"])
            )
    sizes = sorted(strata.values())
    print("\nsampler strata (ticker x line item x form, 1-3 bucket only):")
    print(f"  non-empty strata: {len(strata)}; facts per stratum min {sizes[0]}, "
          f"median {sizes[len(sizes) // 2]}, max {sizes[-1]}")  # fmt: skip
    print(f"  distinct keys per stratum: min {min(len(v) for v in key_strata.values())}, "
          f"max {max(len(v) for v in key_strata.values())}")  # fmt: skip
    per_ticker = Counter(t for (t, _, _) in strata)
    print(f"  strata per ticker: {dict(per_ticker)}")
    per_form = Counter(f for (_, _, f) in strata)
    print(f"  strata per form: {dict(per_form)}")

    print("\nline items entirely in the >3 bucket for a filer (all its facts, both forms):")
    by = defaultdict(Counter)
    for r in rows:
        by[(r["ticker"], r["line_item"])][r["bucket"]] += 1
    for (t, item), c in sorted(by.items()):
        if c[">3"] and not c["1-3"] and not c["0"]:
            print(f"  {t:5} {item}: {c['>3']} facts, all >3")


if __name__ == "__main__":
    main()
