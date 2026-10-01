"""What LLM seeding (PRD 11.1 Stage 1: 50 table, 40 synthesis items) would draw on.

python -m scripts.seed_supply
python -m scripts.seed_supply --write-fixture  # real chunks for tests/unit/test_seeding.py

Measurement only: no model call, no item, no draw. Chunks of the frozen 90
parsed accessions by PRD 11.1's strata (ticker, form_type, item_code,
chunk_type); how many are already gold for a candidate (eval/candidates/*.jsonl)
and so excluded; prose body tokens (header excluded) around the proposed
minimum; and the proportional allocation per ticker (TRADEOFFS, LLM seeding) at
1x, with each slotted stratum's draw (`overdraw` x its slots, as scripts.seed_draw).
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from itertools import pairwise

import yaml

from api.chunk.tokens import count_tokens
from api.config import REPO_ROOT, eval_seeding
from api.db import connect
from eval.generate.seeding import (
    PER_SHARE_EXCEPTION,
    SCALE_EXCEPTION,
    allocate,
    mixed_signals,
    pick_extra,
)
from scripts.write_freeze import FREEZE_FILE

MDNA = {("10-K", "II.7"), ("10-Q", "I.2")}
FIXTURE_FILE = REPO_ROOT / "tests" / "fixtures" / "seed_chunks.json"
# Real chunks for tests/unit/test_seeding.py: a millions table, two NULL-scale
# tables (percentages, per-share), two prose chunks, two sharing a sentence.
FIXTURE_CHUNKS = (
    "0000909832-25-000015:68.1:68.1",
    "0000320193-23-000106:327.0:327.0",
    "0000320193-23-000106:458.0:458.0",
    "0000078003-24-000039:343.0:344.0",
    "0000027419-23-000052:273.0:274.0",
    "0001045810-24-000029:742.0:746.0",
    "0001045810-24-000029:748.0:752.0",
    "0000019617-24-000326:1892.0:1892.0",  # JPM Note 18, EPS, unit_scale millions (F-90)
)
# The gold exclusion is the 200 auto candidates' chunks; seeded items are not part of it.
CANDIDATES = sorted(
    p
    for p in (REPO_ROOT / "eval" / "candidates").glob("*_candidates.jsonl")
    if not p.name.startswith("llm_seeded")
)


def quantiles(xs: list[int]) -> str:
    xs = sorted(xs)
    q = lambda f: xs[min(len(xs) - 1, int(f * len(xs)))]  # noqa: E731
    return f"min {xs[0]}, p25 {q(0.25)}, median {q(0.5)}, p75 {q(0.75)}, max {xs[-1]}"


def span_scales(conn, chunk_ids: list[str]) -> dict[str, list[int | None]]:
    """chunk_id -> the ix scale of every tagged span resolved into it, in span order."""
    out: dict[str, list[int | None]] = defaultdict(list)
    for cid, scale in conn.execute(
        "SELECT chunk_id, scale FROM xbrl_spans WHERE chunk_id = ANY(%s) ORDER BY span_id",
        (chunk_ids,),
    ):
        out[cid].append(scale)
    return out


def write_fixture() -> None:
    record = yaml.safe_load(FREEZE_FILE.read_text(encoding="utf-8"))
    with connect() as conn:
        rows = conn.execute(
            "SELECT chunk_id, ticker, form_type, item_code, chunk_type, unit_scale, text, raw_text "
            "FROM chunks WHERE chunk_id = ANY(%s) ORDER BY chunk_id",
            (list(FIXTURE_CHUNKS),),
        ).fetchall()
        spans = span_scales(conn, list(FIXTURE_CHUNKS))
    keys = ("chunk_id", "ticker", "form_type", "item_code", "chunk_type", "unit_scale", "text",
            "raw_text")  # fmt: skip
    doc = {
        "source": "python -m scripts.seed_supply --write-fixture",
        "parser_version": record["parser_version"],
        "chunker_version": record["chunker_version"],
        "chunks": [
            {
                **dict(zip(keys, r, strict=True)),
                "body_tokens": count_tokens(r[7]),
                "span_scales": spans.get(r[0], []),
            }
            for r in rows
        ],
    }
    FIXTURE_FILE.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(rows)} chunks to {FIXTURE_FILE.relative_to(REPO_ROOT)}")


def main() -> None:
    if "--write-fixture" in sys.argv:
        write_fixture()
        return
    record = yaml.safe_load(FREEZE_FILE.read_text(encoding="utf-8"))
    parsed = [e["accession"] for e in record["filings"] if e["status"] == "parsed"]
    with connect() as conn:
        rows = conn.execute(
            "SELECT chunk_id, ticker, form_type, item_code, chunk_type, token_count, raw_text, "
            "unit_scale, accession, char_start FROM chunks WHERE accession = ANY(%s) "
            "ORDER BY chunk_id",
            (parsed,),
        ).fetchall()
        scaled = [r[0] for r in rows if r[4] == "table" and r[7] is not None]
        spans = span_scales(conn, scaled)
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
    body = {r[0]: count_tokens(r[6]) for r in rows if r[4] == "prose"}
    text = {r[0]: r[6] for r in rows}
    unit = {r[0]: r[7] for r in rows}
    order = sorted(rows, key=lambda r: (r[8], r[9] if r[9] is not None else -1, r[0]))
    next_type = {a[0]: b[4] for a, b in pairwise(order) if a[8] == b[8]}
    rows = [r[:6] for r in rows]
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

    cfg = eval_seeding()
    tickers = list(dict.fromkeys(r[1] for r in rows))
    print("\nconfig allocation:")
    for kind in ("table", "synthesis"):
        c = cfg[kind]
        print(f"  {kind}: total {c['total']}, sum {sum(c['per_ticker'].values())}, "
              f"overdraw {c['overdraw']}, per_ticker {c['per_ticker']}")  # fmt: skip
    extra = pick_extra(tickers, cfg["table"]["seed"], 2)
    above = sorted(t for t, n in cfg["table"]["per_ticker"].items() if n == 7)
    print(f"  table extra slots: pick_extra(seed {cfg['table']['seed']}) = {extra}; "
          f"config gives 7 to {above}; {'match' if extra == above else 'MISMATCH'}")  # fmt: skip

    excluded = Counter((t, f, i, c) for cid, t, f, i, c, _ in rows if cid in gold)
    print(f"\nexcluded as already gold, by stratum (ticker, form, item_code, chunk_type): "
          f"{sum(excluded.values())} in {len(excluded)} strata")  # fmt: skip
    for k, n in sorted(excluded.items()):
        print(f"  {' '.join(x or '-' for x in k)}: {n}")

    prose = sorted((body[cid], cid) for cid, _, _, _, c, _ in rows if c == "prose")
    edges = [0, 10, 20, 30, 40, 50, 60, 80, 100, 150, 200, 501]
    names = [f"{a}-{b - 1}" for a, b in pairwise(edges)]
    bands = Counter(
        next(name for (a, b), name in zip(pairwise(edges), names, strict=True) if a <= n < b)
        for n, _ in prose
    )
    print(f"\nprose body tokens (header excluded), {len(prose)} chunks: "
          f"{ {name: bands[name] for name in names} }")  # fmt: skip
    cut = cfg["synthesis"]["min_body_tokens"]
    below = [x for x in prose if x[0] < cut]
    above = len(prose) - len(below)
    print(f"  below min_body_tokens {cut} (config): {len(below)}; at or above: {above}")
    print(
        "  per ticker: prose / below the floor (share) / of which one-line headings / "
        "headings followed by a table chunk"
    )
    for t in tickers:
        mine = [cid for cid, tk, _, _, c, _ in rows if tk == t and c == "prose"]
        low = [cid for cid in mine if body[cid] < cut]
        heads = [cid for cid in low if text[cid].strip().count("\n") == 0
                 and not re.search(r"[.:;?!]$", text[cid].strip())]  # fmt: skip
        then_table = sum(1 for cid in heads if next_type.get(cid) == "table")
        print(f"    {t:5} {len(mine):5} {len(low):4} ({len(low) / len(mine):.0%}) "
              f"{len(heads):4} {then_table:4}")  # fmt: skip
    for label, band in (("just below", [x for x in prose if cut - 5 <= x[0] < cut]),
                        ("just above", [x for x in prose if cut <= x[0] < cut + 5])):  # fmt: skip
        print(f"  {label} the cut ({len(band)} chunks; every {max(1, len(band) // 6)}th shown):")
        for n, cid in band[:: max(1, len(band) // 6)][:6]:
            print(f"    {n:3} {cid}: {text[cid][:150]!r}")

    print(f"\nscale signals (F-90), table chunks with a unit_scale: {len(scaled)}")
    print(
        "  per ticker: 'except ... per share' / scale-exception clause / tagged span at "
        "another ix scale / union"
    )
    tot = Counter()
    for t in tickers:
        mine = [cid for cid, tk, *_ in rows if tk == t and cid in set(scaled)]
        a = {c for c in mine if PER_SHARE_EXCEPTION.search(text[c])}
        b = {c for c in mine if SCALE_EXCEPTION.search(text[c])}
        m = {
            c
            for c in mine
            if any("tagged spans" in r for r in mixed_signals("", unit[c], spans.get(c, [])))
        }
        u = a | b | m
        tot.update({"a": len(a), "b": len(b), "m": len(m), "u": len(u), "n": len(mine)})
        print(f"    {t:5} {len(mine):5}: {len(a):4} {len(b):4} {len(m):5} {len(u):5}")
    print(f"    total {tot['n']:5}: {tot['a']:4} {tot['b']:4} {tot['m']:5} {tot['u']:5}")

    eligible = [r for r in rows if r[0] not in gold]
    for kind, ctype in (("table", "table"), ("synthesis", "prose")):
        c = cfg[kind]
        floors = [None] if ctype == "table" else [cut]
        for floor in floors:
            pool = [r for r in eligible if r[4] == ctype and (floor is None or body[r[0]] >= floor)]
            title = f"{kind} ({ctype} chunks, gold excluded" + (
                f", body tokens >= {floor})" if floor else ")")  # fmt: skip
            print(
                f"\nallocation, {title}: {len(pool)} chunks; per stratum 1x slots / "
                f"draw (overdraw {c['overdraw']} x slots, capped at the stratum's chunks)"
            )
            no_mdna = []
            for t in tickers:
                counts = Counter((r[2], r[3]) for r in pool if r[1] == t)
                slots = allocate(counts, c["per_ticker"][t])
                cells = ", ".join(
                    f"{f} {i} {n}/{min(n * c['overdraw'], counts[(f, i)])}"
                    for (f, i), n in slots.items()
                )
                print(
                    f"  {t:5} ({sum(slots.values()):2} slots of {sum(counts.values()):5}): {cells}"
                )
                if not any(k in MDNA for k in slots):
                    no_mdna.append(t)
            print(f"  tickers with zero MD&A slots: {no_mdna or 'none'}")


if __name__ == "__main__":
    main()
