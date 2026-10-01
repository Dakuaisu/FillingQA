"""The 160 xbrl_numeric candidates, their manifest and the spot-check sheet.

python -m scripts.xbrl_candidates           # generate
python -m scripts.xbrl_candidates --verify  # every xbrl_fact_id still names its fact (F-78)

Writes eval/candidates/ (never a golden_* file): xbrl_numeric_candidates.jsonl,
xbrl_numeric_manifest.json, xbrl_numeric_spot_check.md. Nothing is marked
reviewed; the spot-check is the owner's (PRD 11.1, OPEN). The manifest records
each item's fact by natural key, because `xbrl_fact_id` is a DB serial a rebuild
would not reproduce (F-78).
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict

import yaml

from api.config import REPO_ROOT, eval_sampler
from api.db import connect
from eval.generate.pool import build_pool, sample
from eval.generate.schema import validate_item
from eval.generate.xbrl_items import build_items, spot_check_ids
from scripts.concept_coverage import classify_facts
from scripts.write_freeze import FREEZE_FILE

OUT_DIR = REPO_ROOT / "eval" / "candidates"
ITEMS_FILE = OUT_DIR / "xbrl_numeric_candidates.jsonl"
MANIFEST_FILE = OUT_DIR / "xbrl_numeric_manifest.json"
SHEET_FILE = OUT_DIR / "xbrl_numeric_spot_check.md"
TEMPLATES_FILE = REPO_ROOT / "eval" / "templates.yaml"


FLAG_RULE = "value <= 0"
FACT_SQL = (
    "SELECT fact_id, accession, concept, period_start, period_end, unit, value "
    "FROM xbrl_facts WHERE fact_id = ANY(%s)"
)


def render(items: list[dict]) -> str:
    return "".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items)


def natural_key(accession, concept, start, end, unit, value) -> dict:
    return {
        "accession": accession, "concept": concept,
        "period_start": str(start) if start else None, "period_end": str(end),
        "unit": unit, "value": str(value),
    }  # fmt: skip


def item_lines(i: dict, texts: dict[str, str]) -> list[str]:
    lines = [f"## {i['item_id']}", "", f"- Question: {i['question']}",
             f"- Reference answer: {i['reference_answer']}",
             f"- Accessions: {', '.join(i['gold_accessions'])}",
             f"- xbrl_fact_id: {i['xbrl_fact_id']}",
             f"- tags: {', '.join(i['tags'])}", ""]  # fmt: skip
    for s in i["gold_evidence_sets"]:
        lines += [f"### {s[0]}", "", "```", texts[s[0]].rstrip(), "```", ""]
    return lines


def verify() -> int:
    """Exit status 1 if any item's xbrl_fact_id no longer names the recorded fact."""
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    text = ITEMS_FILE.read_text(encoding="utf-8")
    items = [json.loads(line) for line in text.splitlines()]
    problems = []
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != manifest["candidates_sha256"]:
        problems.append("candidates file sha256 differs from the manifest")
    recorded = manifest["facts"]
    with connect() as conn:
        found = {
            r[0]: natural_key(*r[1:])
            for r in conn.execute(FACT_SQL, ([i["xbrl_fact_id"] for i in items],)).fetchall()
        }
    for i in items:
        want, have = recorded.get(i["item_id"]), found.get(i["xbrl_fact_id"])
        if want is None:
            problems.append(f"{i['item_id']}: no natural key in the manifest")
        elif have != want:
            problems.append(f"{i['item_id']}: fact_id {i['xbrl_fact_id']} is {have}, want {want}")
    print(f"verify: {len(items)} items, {len(found)} fact ids found in xbrl_facts, "
          f"{len(problems)} mismatches")  # fmt: skip
    for p in problems:
        print(f"  MISMATCH {p}")
    return 1 if problems else 0


def main() -> None:
    if "--verify" in sys.argv:
        sys.exit(verify())
    line_items, tickers, _, rows, _ = classify_facts()
    cfg = eval_sampler()
    templates = yaml.safe_load(TEMPLATES_FILE.read_text(encoding="utf-8"))
    freeze = yaml.safe_load(FREEZE_FILE.read_text(encoding="utf-8"))
    pool = build_pool(rows)
    draw = sample(pool.eligible, cfg["seed"], cfg["total"], cfg["per_ticker"])
    items, problems = build_items(
        draw, forms=templates["forms"], labels={i["id"]: i["label"] for i in line_items},
        company_names=templates["company_names"], seed=cfg["seed"],
        dataset_version=cfg["dataset_version"],
    )  # fmt: skip
    failures = {i["item_id"]: e for i in items if (e := validate_item(i))}
    text = render(items)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ITEMS_FILE.write_text(text, encoding="utf-8")

    tag = lambda i, prefix: next(t for t in i["tags"] if t.startswith(prefix))  # noqa: E731
    per_template = Counter(tag(i, "template:").split(":", 1)[1] for i in items)
    split = defaultdict(Counter)
    for i in items:
        split[i["tags"][0]][i["tags"][3]] += 1
    kinds = Counter(i["tags"][4] for i in items)
    evsets = Counter(len(i["gold_evidence_sets"]) for i in items)
    distinct = Counter(len({c for s in i["gold_evidence_sets"] for c in s}) for i in items)
    spot = spot_check_ids(items, cfg["seed"], cfg["spot_check_n"])
    key_of = {k.xbrl_fact_id: k for k in draw}
    flagged = [i["item_id"] for i in items if key_of[i["xbrl_fact_id"]].value <= 0]
    facts = {
        i["item_id"]: natural_key(
            k.own_accession, k.concept, k.period_start, k.period_end, k.unit, k.value
        )
        for i in items
        for k in [key_of[i["xbrl_fact_id"]]]
    }
    manifest = {
        "dataset_version": cfg["dataset_version"],
        "candidates_file": str(ITEMS_FILE.relative_to(REPO_ROOT)),
        "candidates_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "eval_sampler": cfg,
        "parser_version": freeze["parser_version"],
        "chunker_version": freeze["chunker_version"],
        "items": len(items),
        "validation_failures": failures,
        "not_generated": [list(p) for p in problems],
        "items_per_template": dict(sorted(per_template.items())),
        "period_kinds": dict(sorted(kinds.items())),
        "form_split_per_ticker": {t: dict(sorted(split[t].items())) for t in tickers},
        "evidence_sets_per_item": {str(k): v for k, v in sorted(evsets.items())},
        "spot_check": {"n": cfg["spot_check_n"], "item_ids": spot, "reviewed": False},
        "flagged": {"rule": FLAG_RULE, "outside_spot_check": True, "item_ids": flagged},
        "facts": facts,
    }
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")

    by_id = {i["item_id"]: i for i in items}
    shown = spot + [i for i in flagged if i not in spot]
    chunk_ids = sorted({c for i in shown for s in by_id[i]["gold_evidence_sets"] for c in s})
    with connect() as conn:
        texts = dict(conn.execute(
            "SELECT chunk_id, text FROM chunks WHERE chunk_id = ANY(%s)", (chunk_ids,)
        ).fetchall())  # fmt: skip
    lines = [
        "# xbrl_numeric spot-check (PRD 11.1: 10% of XBRL items)", "",
        f"{len(spot)} of {len(items)} candidates, drawn with seed {cfg['seed']} "
        f"(`python -m scripts.xbrl_candidates`). OWNER-BLOCKED: nothing here is reviewed.",
        "For each: is the question well-formed, is the answer right, are the gold chunks",
        "right and complete?", "",
    ]  # fmt: skip
    for iid in spot:
        lines += item_lines(by_id[iid], texts)
    also_seeded = [i for i in flagged if i in spot]
    lines += [
        "# Flagged, outside the seeded 10%", "",
        f"Selected by rule ({FLAG_RULE}), not by the seed: {', '.join(flagged)}. A zero may be",
        "printed as a dash; a negative sits under a line whose label reads as positive.",
        f"Already shown above in the seeded 10%: {', '.join(also_seeded) or 'none'}.", "",
    ]  # fmt: skip
    for iid in flagged:
        if iid not in spot:
            lines += item_lines(by_id[iid], texts)
    SHEET_FILE.write_text("\n".join(lines), encoding="utf-8")

    print(f"items: {len(items)} (drawn {len(draw)}); not generated: {len(problems)}")
    for p in problems:
        print(f"  NOT GENERATED {p[0]}: {p[1]}")
    print(f"validation failures: {len(failures)}")
    for iid, errs in failures.items():
        print(f"  {iid}: {errs}")
    print(f"items per template: {dict(sorted(per_template.items()))}")
    print(f"period kinds: {dict(sorted(kinds.items()))}")
    per = ", ".join(f"{t} {split[t]['10-K']}/{split[t]['10-Q']}" for t in tickers)
    print(f"form split per ticker (10-K/10-Q): {per}")
    print(f"form split: {dict(sum(split.values(), Counter()))}")
    print(f"evidence sets per item: {dict(sorted(evsets.items()))}")
    print(f"distinct gold chunks per item: {dict(sorted(distinct.items()))}")
    filing_scoped = [i for i in items if tag(i, "template:").endswith("_filing")]
    print(f"filing-scoped items: {len(filing_scoped)}, all single-accession: "
          f"{all(len(i['gold_accessions']) == 1 for i in filing_scoped)}")  # fmt: skip
    print(f"spot-check ({SHEET_FILE.relative_to(REPO_ROOT)}): {len(spot)} seeded items; "
          f"flagged ({FLAG_RULE}): {flagged}; {len(chunk_ids)} gold chunks shown")  # fmt: skip
    print(f"manifest natural keys: {len(facts)}")
    print(f"wrote {ITEMS_FILE.relative_to(REPO_ROOT)} sha256 {manifest['candidates_sha256'][:16]}")


if __name__ == "__main__":
    main()
