"""The 160 xbrl_numeric candidates, their manifest and the spot-check sheet.

python -m scripts.xbrl_candidates

Writes eval/candidates/ (never a golden_* file): xbrl_numeric_candidates.jsonl,
xbrl_numeric_manifest.json, xbrl_numeric_spot_check.md. Nothing is marked
reviewed; the spot-check is the owner's (PRD 11.1, OPEN).
"""

from __future__ import annotations

import hashlib
import json
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


def render(items: list[dict]) -> str:
    return "".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items)


def main() -> None:
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
    spot = spot_check_ids(items, cfg["seed"], cfg["spot_check_n"])
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
    }
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")

    by_id = {i["item_id"]: i for i in items}
    chunk_ids = sorted({c for i in spot for s in by_id[i]["gold_evidence_sets"] for c in s})
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
        i = by_id[iid]
        lines += [f"## {iid}", "", f"- Question: {i['question']}",
                  f"- Reference answer: {i['reference_answer']}",
                  f"- Accessions: {', '.join(i['gold_accessions'])}",
                  f"- xbrl_fact_id: {i['xbrl_fact_id']}",
                  f"- tags: {', '.join(i['tags'])}", ""]  # fmt: skip
        for s in i["gold_evidence_sets"]:
            lines += [f"### {s[0]}", "", "```", texts[s[0]].rstrip(), "```", ""]
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
    filing_scoped = [i for i in items if tag(i, "template:").endswith("_filing")]
    print(f"filing-scoped items: {len(filing_scoped)}, all single-accession: "
          f"{all(len(i['gold_accessions']) == 1 for i in filing_scoped)}")  # fmt: skip
    print(f"spot-check ({SHEET_FILE.relative_to(REPO_ROOT)}): {len(spot)} items, "
          f"{len(chunk_ids)} gold chunks")  # fmt: skip
    print(f"wrote {ITEMS_FILE.relative_to(REPO_ROOT)} sha256 {manifest['candidates_sha256'][:16]}")


if __name__ == "__main__":
    main()
