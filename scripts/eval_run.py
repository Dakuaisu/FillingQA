"""Run the eval over candidate items and print the report (PRD 11.4).

python -m scripts.eval_run                     # plan only: no retrieval, no model call
python -m scripts.eval_run --run [--limit N]   # new run
python -m scripts.eval_run --resume RUN_ID     # continue a run from its results file
python -m scripts.eval_run --run --baseline-out eval/baselines/main.json

Each item's result is appended to eval/runs/<run_id>.results.jsonl as it
completes, so a killed process loses at most the item in flight; --resume skips
recorded items after checking the backend, datasets and freeze versions still
match the run's meta. A call with no usable response halts the run (exit 1) with
the error in <run_id>.errors.jsonl and the item left unrecorded. When no item is
pending, the report is written to <run_id>.json and printed. Refuses a baseline
path for a development backend before any work (F-59). Retrieval: the Phase 2
dense top-k at `eval_run.retrieve_depth` (the pre-rerank list, F-13); the
generator gets `baseline.top_k` of it.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import uuid
from collections import Counter
from datetime import UTC, datetime

import yaml

from api.config import REPO_ROOT, baseline, eval_run, generation
from api.generate import claude_cli
from api.generate.generator import generate, refuse_dev_baseline
from eval.runner import build_report, format_report
from scripts.write_freeze import FREEZE_FILE

DATASETS = sorted((REPO_ROOT / "eval" / "candidates").glob("*_candidates.jsonl"))
TIER = "tier_small"
TRANSPORT_RETRIES = 3


def arg(name: str) -> str | None:
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else None


def append(path, record: dict) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def read_jsonl(path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").split("\n") if x]


def current_meta(gen: dict, run_cfg: dict) -> dict:
    freeze = yaml.safe_load(FREEZE_FILE.read_text(encoding="utf-8"))
    return {
        "backend": gen["backend"], "model_requested": gen[TIER], "tier": TIER,
        "retrieval_stage": "dense top-k (Phase 2 baseline; no fusion, no rerank)",
        "retrieve_depth": run_cfg["retrieve_depth"], "generator_top_k": baseline()["top_k"],
        "parser_version": freeze["parser_version"], "chunker_version": freeze["chunker_version"],
        "datasets": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in DATASETS},
    }  # fmt: skip


def answer_one(conn, model, emb, it: dict, gen: dict, depth: int) -> dict:
    from api.query.retrieve import dense_top_k, embed_question

    t0 = time.monotonic()
    chunks, _ = dense_top_k(conn, embed_question(model, emb, it["question"]), depth)
    last = None
    for _ in range(TRANSPORT_RETRIES):
        try:
            a = generate(it["question"], chunks[: baseline()["top_k"]], gen, TIER)
            break
        except claude_cli.TransportError as e:
            last = e
    else:
        raise last
    if gen[TIER] not in a.model.split(","):
        raise claude_cli.CliError(f"served {a.model}, requested {gen[TIER]}")
    return {
        "item_id": it["item_id"], "retrieved": [c.chunk_id for c in chunks],
        "retrieved_post_rerank": None,
        "answer": {"text": a.text, "claims": [], "abstained": False}, "verdict": "PASS",
        "model_served": a.model, "backend": a.backend,
        "usage": {"input_tokens": a.input_tokens, "output_tokens": a.output_tokens,
                  "cache_read_tokens": a.cache_read_tokens,
                  "cache_creation_tokens": a.cache_creation_tokens},
        "latency_s": round(time.monotonic() - t0, 2),
        "answered_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }  # fmt: skip


def run_items(todo: list[str], answer, results_path, errors_path) -> int:
    """Answer each pending item in order, appending each result as it completes.
    0 when done; 1 on a call with no usable response (error filed, item unrecorded)."""
    for n, iid in enumerate(todo, start=1):
        try:
            rec = answer(iid)
        except claude_cli.CliError as e:
            at = datetime.now(UTC).isoformat(timespec="seconds")
            append(errors_path, {"item_id": iid, "error": str(e), "at": at})
            print(f"HALT at {iid}: {e}")
            return 1
        append(results_path, rec)
        print(f"[{n}/{len(todo)}] {iid} {rec.get('latency_s')}s", flush=True)
    return 0


def main() -> None:
    gen, run_cfg = generation(), eval_run()
    baseline_out = arg("--baseline-out")
    if baseline_out:
        refuse_dev_baseline(gen["backend"], baseline_out)
    items = {}
    for p in DATASETS:
        for it in read_jsonl(p):
            items[it["item_id"]] = it
    runs = REPO_ROOT / run_cfg["runs_dir"]
    meta = current_meta(gen, run_cfg)

    if arg("--resume"):
        run_id = arg("--resume")
        saved = json.loads((runs / f"{run_id}.meta.json").read_text(encoding="utf-8"))
        diff = {k for k in meta if meta[k] != saved.get(k)}
        if diff:
            raise SystemExit(f"run {run_id} cannot resume: {sorted(diff)} changed since it began")
        order = saved["item_order"]
    elif "--run" in sys.argv:
        run_id = uuid.uuid4().hex[:12]
        order = list(items)[: int(arg("--limit"))] if arg("--limit") else list(items)
        runs.mkdir(parents=True, exist_ok=True)
        (runs / f"{run_id}.meta.json").write_text(
            json.dumps({**meta, "run_id": run_id, "k": run_cfg["k"], "item_order": order},
                       indent=1) + "\n", encoding="utf-8")  # fmt: skip
    else:
        sources = dict(Counter(i["source"] for i in items.values()))
        print(f"backend {gen['backend']} ({gen[TIER]}, {TIER}); items {len(items)} {sources}; "
              f"k {run_cfg['k']}")  # fmt: skip
        print("plan only: pass --run to retrieve and generate")
        return

    results_path = runs / f"{run_id}.results.jsonl"
    done = {r["item_id"] for r in read_jsonl(results_path)}
    todo = [i for i in order if i not in done]
    print(f"run {run_id}: backend {gen['backend']}; items {len(order)}; recorded {len(done)}; "
          f"pending {len(todo)}", flush=True)  # fmt: skip
    if todo:
        from api.db import connect
        from api.index.embed import load_model

        model, emb = load_model()
        with connect() as conn:
            code = run_items(
                todo,
                lambda iid: answer_one(
                    conn, model, emb, items[iid], gen, run_cfg["retrieve_depth"]
                ),
                results_path,
                runs / f"{run_id}.errors.jsonl",
            )
        if code:
            print(f"resume with --resume {run_id}")
            sys.exit(code)
    results = read_jsonl(results_path)
    report = build_report(items, results, {**meta, "run_id": run_id}, run_cfg["k"])
    (runs / f"{run_id}.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(format_report(report))
    if baseline_out:
        (REPO_ROOT / baseline_out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
