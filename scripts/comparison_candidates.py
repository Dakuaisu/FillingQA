"""The 40 xbrl_auto comparison candidates, their manifest and the spot-check sheet.

python -m scripts.comparison_candidates           # generate
python -m scripts.comparison_candidates --verify  # both facts of every pair still resolve (F-78)

Writes eval/candidates/ (never a golden_* file): comparison_candidates.jsonl,
comparison_manifest.json, comparison_spot_check.md. Nothing is marked reviewed.
Pool: eligible pairs (eval/generate/comparison.py), neither side among the 160
drawn xbrl_numeric keys.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict

import yaml

from api.config import REPO_ROOT, eval_comparison, eval_sampler
from api.db import connect
from eval.generate.comparison import (
    build_comparison_items,
    build_pairs,
    chunks,
    cooccurrence,
    eligible_pairs,
    tokens,
)
from eval.generate.pool import build_pool, sample
from eval.generate.schema import validate_item
from eval.generate.xbrl_items import spot_check_ids
from scripts.concept_coverage import classify_facts
from scripts.write_freeze import FREEZE_FILE
from scripts.xbrl_candidates import (
    FACT_SQL,
    TEMPLATES_FILE,
    f100_flags,
    f100_lines,
    item_lines,
    natural_key,
    render,
)

OUT_DIR = REPO_ROOT / "eval" / "candidates"
ITEMS_FILE = OUT_DIR / "comparison_candidates.jsonl"
MANIFEST_FILE = OUT_DIR / "comparison_manifest.json"
SHEET_FILE = OUT_DIR / "comparison_spot_check.md"


def fact_key(k) -> dict:
    return natural_key(k.own_accession, k.concept, k.period_start, k.period_end, k.unit, k.value)


def verify() -> int:
    """Exit status 1 if either fact of any pair no longer resolves to its natural key."""
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    text = ITEMS_FILE.read_text(encoding="utf-8")
    items = [json.loads(line) for line in text.splitlines()]
    problems = []
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != manifest["candidates_sha256"]:
        problems.append("candidates file sha256 differs from the manifest")
    ids = {}
    for i in items:
        rec = manifest["facts"].get(i["item_id"])
        if rec is None:
            problems.append(f"{i['item_id']}: no facts in the manifest")
            continue
        ids[(i["item_id"], "later")] = (i["xbrl_fact_id"], rec["later"])
        ids[(i["item_id"], "earlier")] = (rec["earlier_fact_id"], rec["earlier"])
    with connect() as conn:
        found = {
            r[0]: natural_key(*r[1:])
            for r in conn.execute(FACT_SQL, ([v[0] for v in ids.values()],)).fetchall()
        }
    for (iid, side), (fid, want) in sorted(ids.items()):
        if found.get(fid) != want:
            problems.append(f"{iid} {side}: fact_id {fid} is {found.get(fid)}, want {want}")
    print(f"verify: {len(items)} items, {len(ids)} fact ids checked, "
          f"{len(found)} found in xbrl_facts, {len(problems)} mismatches")  # fmt: skip
    for p in problems:
        print(f"  MISMATCH {p}")
    return 1 if problems else 0


def main() -> None:
    if "--verify" in sys.argv:
        sys.exit(verify())
    line_items, tickers, _, rows, _ = classify_facts()
    cfg, xcfg = eval_comparison(), eval_sampler()
    templates = yaml.safe_load(TEMPLATES_FILE.read_text(encoding="utf-8"))
    freeze = yaml.safe_load(FREEZE_FILE.read_text(encoding="utf-8"))
    pool = build_pool(rows)
    drawn = {k.key for k in sample(pool.eligible, xcfg["seed"], xcfg["total"], xcfg["per_ticker"])}
    pairs = eligible_pairs(build_pairs(pool.eligible, cfg["gaps"]), drawn)
    draw = sample(pairs, cfg["seed"], cfg["total"], cfg["per_ticker"])
    items, problems = build_comparison_items(
        draw, forms=templates["comparison_forms"],
        labels={i["id"]: i["label"] for i in line_items},
        company_names=templates["company_names"], seed=cfg["seed"],
        dataset_version=cfg["dataset_version"],
    )  # fmt: skip
    failures = {i["item_id"]: e for i in items if (e := validate_item(i))}
    text = render(items)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ITEMS_FILE.write_text(text, encoding="utf-8")

    pair_of = {p.later.xbrl_fact_id: p for p in draw}
    printed: dict[tuple, set[str]] = defaultdict(set)
    for r in rows:
        for _, raw in r["exact_spans"]:
            printed[(r["cik"], r["concept"], *r["period"])] |= tokens(raw or "")
    index: dict = defaultdict(lambda: defaultdict(set))
    with connect() as conn:
        for cik, cid, raw in conn.execute(
            "SELECT cik, chunk_id, raw_text FROM chunks WHERE cik = ANY(%s)",
            (sorted({p.later.cik for p in draw}),),
        ):
            for tok in tokens(raw):
                index[cik][tok].add(cid)
    flagged: dict[str, list[str]] = {}
    for i in items:
        p = pair_of[i["xbrl_fact_id"]]
        reasons = []
        if min(p.earlier.value, p.later.value) <= 0:
            reasons.append("side <= 0")
        if p.earlier.value * p.later.value < 0:
            reasons.append("sign flip")
        co = cooccurrence(p, printed, index)
        if co:
            reasons.append(f"untagged co-occurrence in {sorted(co)}")
        if reasons:
            flagged[i["item_id"]] = reasons

    tag = lambda i, prefix: next(t for t in i["tags"] if t.startswith(prefix))  # noqa: E731
    per_template = Counter(tag(i, "template:").split(":", 1)[1] for i in items)
    groups = Counter(f"{i['tags'][4]}/{i['tags'][5]}" for i in items)
    split = defaultdict(Counter)
    for i in items:
        split[i["tags"][0]][f"{i['tags'][4]}/{i['tags'][5]}"] += 1
    evsets = Counter(len(i["gold_evidence_sets"]) for i in items)
    distinct = Counter(len({c for s in i["gold_evidence_sets"] for c in s}) for i in items)
    spot = spot_check_ids(items, cfg["seed"], cfg["spot_check_n"])
    facts = {
        i["item_id"]: {
            "later": fact_key(p.later),
            "earlier_fact_id": p.earlier.xbrl_fact_id,
            "earlier": fact_key(p.earlier),
        }
        for i in items
        for p in [pair_of[i["xbrl_fact_id"]]]
    }
    manifest = {
        "dataset_version": cfg["dataset_version"],
        "candidates_file": str(ITEMS_FILE.relative_to(REPO_ROOT)),
        "candidates_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "eval_comparison": cfg,
        "excluded_keys": "the 160 drawn xbrl_numeric keys (eval_sampler)",
        "parser_version": freeze["parser_version"],
        "chunker_version": freeze["chunker_version"],
        "eligible_pairs": len(pairs),
        "items": len(items),
        "validation_failures": failures,
        "not_generated": [list(p) for p in problems],
        "items_per_template": dict(sorted(per_template.items())),
        "kind_gap": dict(sorted(groups.items())),
        "kind_gap_per_ticker": {t: dict(sorted(split[t].items())) for t in tickers},
        "evidence_sets_per_item": {str(k): v for k, v in sorted(evsets.items())},
        "distinct_gold_chunks_per_item": {str(k): v for k, v in sorted(distinct.items())},
        "spot_check": {"n": cfg["spot_check_n"], "item_ids": spot, "reviewed": False},
        "flagged": {
            "rule": "side <= 0, sign flip, or untagged co-occurrence",
            "outside_spot_check": True,
            "items": flagged,
        },
        "facts": facts,
    }
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")

    by_id = {i["item_id"]: i for i in items}
    shown = spot + [i for i in flagged if i not in spot]
    f100, f100_runs = f100_flags(set(by_id))
    manifest["flagged_f100"] = {"runs": f100_runs, "item_ids": sorted(f100)}
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    gold_ids = {c for i in shown + sorted(f100) for s in by_id[i]["gold_evidence_sets"] for c in s}
    other_ids = {c for found in f100.values() for cs in found.values() for c in cs}
    chunk_ids = sorted(gold_ids | other_ids)
    with connect() as conn:
        texts = dict(conn.execute(
            "SELECT chunk_id, text FROM chunks WHERE chunk_id = ANY(%s)", (chunk_ids,)
        ).fetchall())  # fmt: skip
    lines = [
        "# xbrl_auto comparison spot-check (PRD 11.1: 10%)", "",
        f"{len(spot)} of {len(items)} candidates, drawn with seed {cfg['seed']} "
        f"(`python -m scripts.comparison_candidates`). OWNER-BLOCKED: nothing here is reviewed.",
        "Each evidence set is two chunks, one earlier and one later; each chunk is shown once,",
        "headed with the side it is gold for.", "",
    ]  # fmt: skip

    def render_item(iid: str) -> list[str]:
        i, p = by_id[iid], pair_of[by_id[iid]["xbrl_fact_id"]]
        side = {c: "earlier" for c in chunks(p.earlier)} | {c: "later" for c in chunks(p.later)}
        head = item_lines({**i, "gold_evidence_sets": []}, texts)
        e, la, sets = p.earlier, p.later, i["gold_evidence_sets"]
        body = [
            f"- Earlier: {e.own_accession} {e.period_start}..{e.period_end}",
            f"- Later: {la.own_accession} {la.period_start}..{la.period_end}",
            f"- Evidence sets ({len(sets)}, each one earlier + one later chunk): "
            + "; ".join(" + ".join(s) for s in sets),
            "",
        ]
        if iid in flagged:
            body += [f"- Flagged: {'; '.join(flagged[iid])}", ""]
        for c in sorted(side, key=lambda c: (side[c] != "earlier", c)):
            body += [f"### {side[c]}: {c}", "", "```", texts[c].rstrip(), "```", ""]
        return head + body

    for iid in spot:
        lines += render_item(iid)
    also = [i for i in flagged if i in spot]
    lines += [
        "# Flagged, outside the seeded 10%", "",
        "Selected by rule (side <= 0, sign flip, or a chunk printing both values untagged),",
        f"not by the seed: {', '.join(flagged) or 'none'}. "
        f"Already shown above: {', '.join(also) or 'none'}.", "",
    ]  # fmt: skip
    for iid in flagged:
        if iid not in spot:
            lines += render_item(iid)
    lines += f100_lines(f100, f100_runs, texts, render_item, set(spot) | set(flagged))
    SHEET_FILE.write_text("\n".join(lines), encoding="utf-8")

    print(f"eligible pairs (no shared gold chunk, no drawn xbrl_numeric key): {len(pairs)}")
    print(f"items: {len(items)} (drawn {len(draw)}); not generated: {len(problems)}")
    for p in problems:
        print(f"  NOT GENERATED {p[0]}: {p[1]}")
    print(f"validation failures: {len(failures)}")
    for iid, errs in failures.items():
        print(f"  {iid}: {errs}")
    keys = [k for p in draw for k in p.members]
    print(f"distinct period keys: {len(set(keys))} of {len(keys)}; "
          f"overlap with drawn xbrl_numeric keys: {len(set(keys) & drawn)}")  # fmt: skip
    print(f"items per template: {dict(sorted(per_template.items()))}")
    print(f"kind/gap: {dict(sorted(groups.items()))}")
    for t in tickers:
        print(f"  {t:5} {dict(sorted(split[t].items()))}")
    print(f"evidence sets per item: {dict(sorted(evsets.items()))}")
    print(f"distinct gold chunks per item: {dict(sorted(distinct.items()))}")
    print(f"flagged: {len(flagged)}")
    for iid, why in flagged.items():
        print(f"  {iid}: {'; '.join(why)}")
    print(f"spot-check ({SHEET_FILE.relative_to(REPO_ROOT)}): seeded {spot}; "
          f"{len(chunk_ids)} gold chunks shown")  # fmt: skip
    print(f"manifest fact records: {len(facts)} (later + earlier)")
    print(f"wrote {ITEMS_FILE.relative_to(REPO_ROOT)} sha256 {manifest['candidates_sha256'][:16]}")


if __name__ == "__main__":
    main()
