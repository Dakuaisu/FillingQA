"""Run the eval over candidate items and print the report (PRD 11.4).

python -m scripts.eval_run                       # plan only: no retrieval, no model call
python -m scripts.eval_run --run [--limit N]     # retrieve, generate, score, report
python -m scripts.eval_run --run --baseline-out eval/baselines/main.json

Refuses a baseline path for a development backend before any work (F-59). Writes
the run (results and report) to eval/runs/<run_id>.json. Retrieval is the Phase 2
dense top-k (the pre-rerank list, F-13); the generator gets `baseline.top_k` of it.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import uuid
from collections import Counter

from api.config import REPO_ROOT, baseline, eval_run, generation
from api.generate.generator import generate, refuse_dev_baseline
from eval.runner import build_report, format_report

DATASETS = sorted((REPO_ROOT / "eval" / "candidates").glob("*_candidates.jsonl"))
TIER = "tier_small"


def arg(name: str) -> str | None:
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else None


def main() -> None:
    gen, run_cfg = generation(), eval_run()
    baseline_out = arg("--baseline-out")
    if baseline_out:
        refuse_dev_baseline(gen["backend"], baseline_out)
    items = {}
    for p in DATASETS:
        for line in p.read_text(encoding="utf-8").split("\n"):
            if line:
                it = json.loads(line)
                items[it["item_id"]] = it
    order = list(items)
    if arg("--limit"):
        order = order[: int(arg("--limit"))]
    print(f"backend {gen['backend']} ({gen[TIER]}, {TIER}); items {len(order)} "
          f"{dict(Counter(items[i]['source'] for i in order))}; k {run_cfg['k']}")  # fmt: skip
    if "--run" not in sys.argv:
        print("plan only: pass --run to retrieve and generate")
        return

    from api.db import connect
    from api.index.embed import load_model
    from api.query.retrieve import dense_top_k, embed_question

    run_id = uuid.uuid4().hex[:12]
    model, emb = load_model()
    results = []
    with connect() as conn:
        for n, iid in enumerate(order, start=1):
            it = items[iid]
            t0 = time.monotonic()
            chunks, _ = dense_top_k(conn, embed_question(model, emb, it["question"]),
                                    run_cfg["retrieve_depth"])  # fmt: skip
            a = generate(it["question"], chunks[: baseline()["top_k"]], gen, TIER)
            results.append({
                "item_id": iid, "retrieved": [c.chunk_id for c in chunks],
                "retrieved_post_rerank": None,
                "answer": {"text": a.text, "claims": [], "abstained": False},
                "verdict": "PASS", "model_served": a.model, "backend": a.backend,
                "usage": {"input_tokens": a.input_tokens, "output_tokens": a.output_tokens},
                "latency_s": round(time.monotonic() - t0, 2),
            })  # fmt: skip
            print(f"[{n}/{len(order)}] {iid}", flush=True)
    meta = {
        "run_id": run_id, "backend": gen["backend"], "model_requested": gen[TIER],
        "retrieval_stage": "dense top-k (Phase 2 baseline; no fusion, no rerank)",
        "datasets": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in DATASETS},
    }  # fmt: skip
    report = build_report(items, results, meta, run_cfg["k"])
    out = REPO_ROOT / run_cfg["runs_dir"] / f"{run_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"report": report, "results": results}, indent=1) + "\n",
                   encoding="utf-8")  # fmt: skip
    print(format_report(report))
    if baseline_out:
        (REPO_ROOT / baseline_out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
