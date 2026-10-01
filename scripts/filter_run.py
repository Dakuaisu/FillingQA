"""Router + metadata filters, measured retrieval-only against a hybrid run (PRD 7.1).

python -m scripts.filter_run --run --against RETRIEVAL_RUN_ID      # new run
python -m scripts.filter_run --resume RUN_ID --against RETRIEVAL_RUN_ID

One small-tier router call per candidate question, appended to
eval/runs/<run_id>.router.jsonl as it arrives (a call with no usable response
halts the run, eval_run's rule). When every item is routed: filtered hybrid
retrieval (exact dense among the allowed chunks, BM25 restricted to them, RRF),
falling back to unfiltered when the filters return nothing (`filter_zero_recall`)
or when confidence is below the minimum. Prints retrieval metrics per source for
the unfiltered lists of RETRIEVAL_RUN_ID and the filtered lists, with counts of
unfiltered (low confidence or parse failure), filter_zero_recall, and items whose
every gold chunk lies outside the filter. Writes eval/runs/<run_id>.filter.json.
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from collections import Counter
from datetime import UTC, datetime

import yaml

from api.config import REPO_ROOT, eval_run, generation, retrieval
from api.db import connect
from api.generate import claude_cli
from api.generate.generator import complete
from api.query.router import RouterParseError, allowed_chunks, filters, parse, render
from eval.runner import COLUMNS, SOURCES, retrieval_slice
from scripts.eval_run import read_jsonl, run_items

RUNS = REPO_ROOT / "eval" / "runs"
DATASETS = sorted((REPO_ROOT / "eval" / "candidates").glob("*_candidates.jsonl"))
TEMPLATES = REPO_ROOT / "eval" / "templates.yaml"
TIER = "tier_small"


def arg(name: str) -> str | None:
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else None


def route_one(it: dict, gen: dict, companies: dict) -> dict:
    t0 = time.monotonic()
    a = complete(render(it["question"], companies), gen, TIER)
    if gen[TIER] not in a.model.split(","):
        raise claude_cli.CliError(f"served {a.model}, requested {gen[TIER]}")
    return {"item_id": it["item_id"], "response": a.text, "model_served": a.model,
            "backend": a.backend, "latency_s": round(time.monotonic() - t0, 2),
            "routed_at": datetime.now(UTC).isoformat(timespec="seconds")}  # fmt: skip


def main() -> None:
    gen, rc, k = generation(), retrieval(), eval_run()["k"]
    against = arg("--against")
    items = {it["item_id"]: it for p in DATASETS for it in read_jsonl(p)}
    companies = yaml.safe_load(TEMPLATES.read_text(encoding="utf-8"))["company_names"]
    run_id = arg("--resume") or uuid.uuid4().hex[:12]
    if "--run" not in sys.argv and not arg("--resume"):
        raise SystemExit("usage: --run --against ID | --resume RUN_ID --against ID")
    router_path = RUNS / f"{run_id}.router.jsonl"
    done = {r["item_id"] for r in read_jsonl(router_path)}
    todo = [i for i in items if i not in done]
    print(f"filter run {run_id}: backend {gen['backend']} ({gen[TIER]}); routed {len(done)}; "
          f"pending {len(todo)}", flush=True)  # fmt: skip
    if todo:
        code = run_items(todo, lambda iid: route_one(items[iid], gen, companies), router_path,
                         RUNS / f"{run_id}.router_errors.jsonl")  # fmt: skip
        if code:
            print(f"resume with --resume {run_id} --against {against}")
            sys.exit(code)

    from api.index.embed import load_model
    from api.query.retrieve import dense_filtered_top_k, embed_question, load_bm25, rrf_fuse

    base_doc = json.loads((RUNS / f"{against}.retrieval.json").read_text(encoding="utf-8"))
    base = {r["item_id"]: r for r in base_doc["results"]}
    routes = {r["item_id"]: r for r in read_jsonl(router_path)}
    model, emb = load_model()
    out, counts = [], Counter()
    with connect() as conn:
        index, _ = load_bm25(conn, rc["sparse"])
        meta = conn.execute(
            "SELECT chunk_id, ticker, fiscal_year, fiscal_quarter, form_type FROM chunks"
        ).fetchall()
        for iid, it in items.items():
            src = it["source"]
            try:
                route = parse(routes[iid]["response"])
            except RouterParseError:
                route = None
                counts[(src, "router_parse_failure")] += 1
            f = filters(route, set(companies), rc["filter_confidence_min"]) if route else None
            unfiltered = base[iid]["hybrid"]
            fused, event = unfiltered, None
            if route and f is None:
                counts[(src, "unfiltered_low_confidence_or_empty")] += 1
            if f is not None:
                allowed = allowed_chunks(meta, f)
                gold = {c for es in it["gold_evidence_sets"] for c in es}
                if gold and not gold & allowed:
                    counts[(src, "all_gold_outside_filter")] += 1
                vec = embed_question(model, emb, it["question"])
                dense = dense_filtered_top_k(conn, vec, rc["k_dense"], allowed) if allowed else []
                sp = [c for c, _ in index.search(it["question"], rc["k_sparse"], allowed)]
                w = rc["weights"]
                fused = rrf_fuse([dense, sp], [w["dense"], w["sparse"]], rc["rrf_k"])
                if not fused:
                    event = "filter_zero_recall"
                    counts[(src, "filter_zero_recall")] += 1
                    fused = unfiltered
                else:
                    counts[(src, "filtered")] += 1
            out.append({"item_id": iid, "route": route, "filters": f, "event": event,
                        "unfiltered": unfiltered,
                        "filtered": fused[: max(rc["k_dense"], rc["k_sparse"])]})  # fmt: skip
    report = {"run_id": run_id, "against": against, "kind": "router + filters, retrieval-only",
              "router_model": gen[TIER], "backend": gen["backend"],
              "filter_confidence_min": rc["filter_confidence_min"], "retrieval": rc,
              "counts": {f"{s}/{n}": v for (s, n), v in sorted(counts.items())},
              "columns": {}}  # fmt: skip
    for lst in ("unfiltered", "filtered"):
        by = {s: [r for r in out if items[r["item_id"]]["source"] == s] for s in SOURCES}
        report["columns"][lst] = {
            **{s: retrieval_slice(items, rs, k, lst) if rs else None for s, rs in by.items()},
            "aggregate": retrieval_slice(items, out, k, lst),
        }
    (RUNS / f"{run_id}.filter.json").write_text(
        json.dumps({"report": report, "results": out}, indent=1) + "\n", encoding="utf-8"
    )
    print(f"against retrieval run {against}; router {gen[TIER]} on {gen['backend']}; "
          f"confidence min {rc['filter_confidence_min']}")  # fmt: skip
    print(f"{'list / metric':28}" + "".join(f"{c:>14}" for c in COLUMNS))
    for lst in ("unfiltered", "filtered"):
        for m in (f"sufficiency@{k}", f"recall@{k}", "mrr", f"ndcg@{k}"):
            cells = [report["columns"][lst][c][m] if report["columns"][lst][c] else None
                     for c in COLUMNS]  # fmt: skip
            shown = ["-" if v is None else f"{v:.3f}" for v in cells]
            print(f"{lst + ' ' + m:28}" + "".join(f"{x:>14}" for x in shown))
    print("counts per source:")
    for name in ("filtered", "unfiltered_low_confidence_or_empty", "router_parse_failure",
                 "filter_zero_recall", "all_gold_outside_filter"):  # fmt: skip
        row = [counts.get((s, name), 0) for s in SOURCES]
        print(f"  {name:36}" + "".join(f"{x:>14}" for x in [*row, sum(row)]))


if __name__ == "__main__":
    main()
