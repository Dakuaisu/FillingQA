"""What LLM seeding (PRD 11.1 Stage 1: 50 table, 40 synthesis items) would draw on.

python -m scripts.seed_supply

Measurement only: no model call, no item. Chunks of the frozen 90 parsed
accessions by PRD 11.1's strata (ticker, form_type, item_code, chunk_type), and
how many are already gold for a candidate (eval/candidates/*.jsonl).
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict

import yaml

from api.config import REPO_ROOT
from api.db import connect
from scripts.write_freeze import FREEZE_FILE

CANDIDATES = sorted((REPO_ROOT / "eval" / "candidates").glob("*_candidates.jsonl"))


def quantiles(xs: list[int]) -> str:
    xs = sorted(xs)
    q = lambda f: xs[min(len(xs) - 1, int(f * len(xs)))]  # noqa: E731
    return f"min {xs[0]}, p25 {q(0.25)}, median {q(0.5)}, p75 {q(0.75)}, max {xs[-1]}"


def main() -> None:
    record = yaml.safe_load(FREEZE_FILE.read_text(encoding="utf-8"))
    parsed = [e["accession"] for e in record["filings"] if e["status"] == "parsed"]
    with connect() as conn:
        rows = conn.execute(
            "SELECT chunk_id, ticker, form_type, item_code, chunk_type, token_count "
            "FROM chunks WHERE accession = ANY(%s)",
            (parsed,),
        ).fetchall()
    gold: dict[str, set[str]] = defaultdict(set)  # chunk -> candidate files using it
    for path in CANDIDATES:
        for line in path.read_text(encoding="utf-8").splitlines():
            for s in json.loads(line)["gold_evidence_sets"]:
                for c in s:
                    gold[c].add(path.stem)
    print(f"parsed accessions: {len(parsed)}; chunks: {len(rows)}; "
          f"candidate files: {[p.name for p in CANDIDATES]}")  # fmt: skip

    print("\nchunks by (chunk_type, form): count, gold for a candidate, tokens")
    by_tf = defaultdict(list)
    for cid, _, form, _, ctype, tok in rows:
        by_tf[(ctype, form)].append((cid, tok))
    for key in sorted(by_tf):
        xs = by_tf[key]
        g = sum(1 for c, _ in xs if c in gold)
        toks = quantiles([t for _, t in xs])
        print(f"  {key[0]:5} {key[1]:4} {len(xs):6} gold {g:4}  tokens {toks}")
    per_file = dict(Counter(f for fs in gold.values() for f in fs))
    print(f"  gold chunks by candidate file: {per_file}; distinct {len(gold)}")

    strata = Counter((t, f, i, c) for _, t, f, i, c, _ in rows)
    print(f"\nstrata (ticker, form_type, item_code, chunk_type): {len(strata)} non-empty")
    for ctype in ("table", "prose"):
        sizes = [n for k, n in strata.items() if k[3] == ctype]
        print(f"  {ctype}: {len(sizes)} strata; chunks per stratum {quantiles(sizes)}")

    print("\nchunks by (form, item_code) x chunk_type: table (gold) / prose (gold)")
    fi = defaultdict(Counter)
    for cid, _, form, item, ctype, _ in rows:
        fi[(form, item)][ctype] += 1
        fi[(form, item)][f"{ctype}_gold"] += cid in gold
    for (form, item), c in sorted(fi.items(), key=lambda kv: (kv[0][0], -sum(
            v for k, v in kv[1].items() if not k.endswith("_gold")))):  # fmt: skip
        print(f"  {form:4} {item or '-':6} table {c['table']:5} ({c['table_gold']:3})   "
              f"prose {c['prose']:5} ({c['prose_gold']:3})")  # fmt: skip

    print("\nper ticker: table (10-K / 10-Q) and prose (10-K / 10-Q); not gold for any candidate")
    tk = defaultdict(Counter)
    for cid, t, form, _, ctype, _ in rows:
        tk[t][(ctype, form)] += 1
        tk[t][(ctype, form, "free")] += cid not in gold
    for t in dict.fromkeys(r[1] for r in rows):
        c = tk[t]
        cells = [
            f"{ct} {c[(ct, '10-K')]:5} / {c[(ct, '10-Q')]:5} "
            f"(free {c[(ct, '10-K', 'free')]} / {c[(ct, '10-Q', 'free')]})"
            for ct in ("table", "prose")
        ]
        print(f"  {t:5} " + "   ".join(cells))


if __name__ == "__main__":
    main()
