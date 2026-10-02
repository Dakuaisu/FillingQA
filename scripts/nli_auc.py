"""PRD 7.5's NLI gate: 40 owner-labelled (prose claim, cited chunk) pairs, AUC.

python -m scripts.nli_auc --sheet RUN_ID [--seed 20261006]   # draw pairs, write the sheet
python -m scripts.nli_auc --score                            # AUC and threshold from labels

--sheet draws 40 pairs by seed from a run's `claims_pre` (prose claims only,
one cited chunk per pair) and writes eval/nli/label_sheet_v1.md (claim and chunk
text, no score) and eval/nli/labels_v1.yaml (all null). It refuses to overwrite
a sheet. --score refuses while any label is null, then scores every pair with the
pinned NLI model, prints AUC and, at AUC >= 0.75, the Youden threshold, and writes
eval/nli/auc_v1.json. It never writes `nli_threshold` to config: that edit is
made by hand from this file and recorded (TRADEOFFS).
"""

from __future__ import annotations

import json
import random
import sys

import yaml

from api.config import REPO_ROOT
from scripts.eval_run import read_jsonl

PAIRS = 40
AUC_MIN = 0.75
OUT = REPO_ROOT / "eval" / "nli"
SHEET, LABELS, RESULT = OUT / "label_sheet_v1.md", OUT / "labels_v1.yaml", OUT / "auc_v1.json"


def arg(name: str) -> str | None:
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else None


def candidate_pairs(results: list[dict]) -> list[dict]:
    out = []
    for r in results:
        for c in r.get("claims_pre") or []:
            if c.get("figure"):
                continue
            for cid in c["citations"]:
                if cid in (r.get("generator_input") or []):
                    out.append({"item_id": r["item_id"], "claim_id": c["claim_id"],
                                "claim": c["text"], "chunk_id": cid})  # fmt: skip
    return out


def sheet(run_id: str, seed: int) -> None:
    from api.db import connect

    if SHEET.exists() or LABELS.exists():
        raise SystemExit(f"{SHEET} or {LABELS} exists; a drawn sheet is never redrawn")
    results = read_jsonl(REPO_ROOT / "eval" / "runs" / f"{run_id}.results.jsonl")
    pool = candidate_pairs(results)
    if len(pool) < PAIRS:
        raise SystemExit(f"run {run_id} has {len(pool)} prose (claim, chunk) pairs, need {PAIRS}")
    drawn = random.Random(seed).sample(pool, PAIRS)
    with connect() as conn:
        texts = dict(conn.execute("SELECT chunk_id, text FROM chunks WHERE chunk_id = ANY(%s)",
                                  ([p["chunk_id"] for p in drawn],)).fetchall())  # fmt: skip
    OUT.mkdir(parents=True, exist_ok=True)
    lines = [f"# NLI gate label sheet v1 (PRD 7.5)\n\nRun {run_id}, seed {seed}, {PAIRS} pairs "
             f"drawn from {len(pool)} prose (claim, cited chunk) pairs. For each pair: does the "
             "chunk, on its own, support the claim? Label in labels_v1.yaml: true or false. "
             "No score is shown here.\n"]  # fmt: skip
    for i, p in enumerate(drawn, 1):
        p["pair"] = f"p{i:02d}"
        head = f"## {p['pair']} ({p['item_id']} {p['claim_id']}, chunk {p['chunk_id']})"
        body = f"**Claim:** {p['claim']}\n\n**Chunk:**\n\n```\n{texts[p['chunk_id']]}\n```\n"
        lines.append(f"{head}\n\n{body}")
    SHEET.write_text("\n".join(lines), encoding="utf-8")
    LABELS.write_text(yaml.safe_dump({"run_id": run_id, "seed": seed, "pairs": [
        {"pair": p["pair"], "item_id": p["item_id"], "claim_id": p["claim_id"],
         "chunk_id": p["chunk_id"], "claim": p["claim"], "supports": None} for p in drawn]},
        sort_keys=False, allow_unicode=True), encoding="utf-8")  # fmt: skip
    print(f"wrote {SHEET} and {LABELS}: {PAIRS} pairs from {len(pool)}")


def score() -> None:
    from api.db import connect
    from api.verify.nli import REVISION, Nli, auc, youden_threshold

    doc = yaml.safe_load(LABELS.read_text(encoding="utf-8"))
    pending = [p["pair"] for p in doc["pairs"] if p["supports"] is None]
    if pending:
        raise SystemExit(f"{len(pending)} pairs unlabelled ({pending[:5]}...); owner labels first")
    with connect() as conn:
        texts = dict(conn.execute("SELECT chunk_id, text FROM chunks WHERE chunk_id = ANY(%s)",
                                  ([p["chunk_id"] for p in doc["pairs"]],)).fetchall())  # fmt: skip
    scores = Nli().score([(texts[p["chunk_id"]], p["claim"]) for p in doc["pairs"]])
    labels = [bool(p["supports"]) for p in doc["pairs"]]
    a = auc(scores, labels)
    t = youden_threshold(scores, labels) if a >= AUC_MIN else None
    out = {"run_id": doc["run_id"], "seed": doc["seed"], "nli_revision": REVISION, "auc": a,
           "auc_min": AUC_MIN, "nli_kept": a >= AUC_MIN, "threshold_youden": t,
           "pairs": [{**p, "entail": s}
                     for p, s in zip(doc["pairs"], scores, strict=True)]}  # fmt: skip
    RESULT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    verdict = f"keep NLI, threshold {t}" if t is not None else "drop NLI (PRD 7.5 fallback)"
    print(f"AUC {a:.3f} over {len(labels)} pairs ({sum(labels)} supporting): {verdict}")


if __name__ == "__main__":
    if arg("--sheet"):
        sheet(arg("--sheet"), int(arg("--seed") or 20261006))
    elif "--score" in sys.argv:
        score()
    else:
        raise SystemExit(__doc__)
