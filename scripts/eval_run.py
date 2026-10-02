"""Run the eval over candidate items and print the report (PRD 11.4).

python -m scripts.eval_run                     # plan only: no retrieval, no model call
python -m scripts.eval_run --run [--limit N]   # new run
python -m scripts.eval_run --resume RUN_ID     # continue a run from its results file
python -m scripts.eval_run --report RUN_ID     # rebuild a finished run's report from its saved meta
python -m scripts.eval_run --rescore RUN_ID T   # derived report at nli_threshold T (F-125)
python -m scripts.eval_run --reverify RUN_ID TAG  # model-free checks again: <id>.reverify-TAG.json
python -m scripts.eval_run --smoke SEED        # pipeline check, 12 seeded items: <id>.smoke.json
python -m scripts.eval_run --run --baseline-out eval/baselines/main.json
python -m scripts.eval_run --run --subset eval/fast_subset_v1.yaml --report-out build/eval_fast.json

The pipeline is `eval_run.pipeline` (PRD 11.6 configs: config_1_dense,
config_3_hybrid, config_4_rerank; eval/pipeline.py). Each result stores the
pre-rerank list (`retrieved`), the reranked list, and what the generator received.

Each item's result is appended to eval/runs/<run_id>.results.jsonl as it
completes, so a killed process loses at most the item in flight; --resume skips
recorded items after checking the backend, datasets and freeze versions still
match the run's meta. A call with no usable response halts the run (exit 1) with
the error in <run_id>.errors.jsonl and the item left unrecorded. When no item is
pending, the report is written to <run_id>.json and printed. Refuses a baseline
path for a development backend before any work (F-59).
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

from api import pipeline, tracing
from api.config import REPO_ROOT, baseline, eval_run, generation, rerank, retrieval, router
from api.generate import claude_cli
from api.generate.generator import refuse_dev_baseline
from api.pipeline import TEMPLATES, Context, answer_fields, call_model, texts_for
from eval.pipeline import depths
from eval.runner import build_report, format_report
from scripts.write_freeze import FREEZE_FILE

DATASETS = sorted((REPO_ROOT / "eval" / "candidates").glob("*_candidates.jsonl"))
TIER = "tier_small"


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


STAGES = {
    "config_1_dense": "dense top-k (no fusion, no rerank)",
    "config_3_hybrid": "BM25 + dense, RRF-fused pre-rerank list (no rerank)",
    "config_4_rerank": "BM25 + dense, RRF-fused pre-rerank list; reranked list stored beside it",
    "config_4_routed": "PRD 7.1 router, metadata filters and intent budgets in front of Config 4; "
    "pre-rerank list per query (RRF over a comparison's sub-queries), reranked lists beside",
}


def current_meta(gen: dict, run_cfg: dict) -> dict:
    """Everything a resumed run must match. Names the PRD 11.6 pipeline (F-61)."""
    from api.db import connect
    from api.query.rerank import machine
    from api.query.retrieve import load_bm25

    freeze = yaml.safe_load(FREEZE_FILE.read_text(encoding="utf-8"))
    pipeline, rc = run_cfg["pipeline"], retrieval()
    meta = {
        "backend": gen["backend"], "model_requested": gen[TIER], "tier": TIER,
        "pipeline": pipeline, "retrieval_stage": STAGES[pipeline],
        **depths(pipeline, retrieve_depth=run_cfg["retrieve_depth"], retrieval_cfg=rc,
                 rerank_cfg=rerank(), baseline_top_k=baseline()["top_k"],
                 budgets=router()["budgets"] if pipeline == "config_4_routed" else None),
        "hnsw_ef_search": rc["hnsw_ef_search"], "k_dense": rc["k_dense"],
        "dense_search": rc.get("dense_search", "exact"),
        "parser_version": freeze["parser_version"], "chunker_version": freeze["chunker_version"],
        "datasets": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in DATASETS},
    }  # fmt: skip
    if pipeline != "config_1_dense":
        meta["retrieval"] = rc
        if rc["sparse"]["backend"] == "bm25":
            with connect() as conn:
                meta["bm25_index_key"] = load_bm25(conn, rc["sparse"])[0].key
    if pipeline in ("config_4_rerank", "config_4_routed"):
        from api.query.rerank import resolve_device

        meta["rerank"] = {**rerank(), "device_used": resolve_device(rerank()["device"])}
        meta["machine"] = machine()
    if gen.get("structured"):
        from api.generate import claims

        meta["generation_contract"] = {
            "kind": "PRD 7.4 structured claims, schema enforced by the backend",
            "schema_sha256": hashlib.sha256(
                json.dumps(claims.SCHEMA, sort_keys=True).encode()).hexdigest(),
            "system_prompt_sha256": hashlib.sha256(claims.SYSTEM_PROMPT.encode()).hexdigest(),
        }  # fmt: skip
        from api.config import verification
        from api.verify import nli

        meta["verification"] = {**verification(), "nli_model": nli.MODEL,
                                "nli_revision": nli.REVISION,
                                "nli_threshold": run_cfg["nli_threshold"]}  # fmt: skip
    else:
        meta["generation_contract"] = {"kind": "plain prompt, free text (Phase 2 baseline)"}
    if pipeline == "config_4_routed":
        meta["router"] = router()
        meta["model_requested"] = {t: gen[t] for t in ("tier_small", "tier_large")}
        meta["templates_sha256"] = hashlib.sha256(TEMPLATES.read_bytes()).hexdigest()
    return meta


def answer_one(conn, ctx: Context, it: dict, gen: dict, run_cfg: dict) -> dict:
    from api.query.rerank import rerank as rerank_one
    from api.query.retrieve import Retrieved, dense_search, embed_question, rrf_fuse, sparse
    from eval.pipeline import context_for

    t0 = time.monotonic()
    pipeline, rc = run_cfg["pipeline"], ctx.rcfg
    vec = embed_question(ctx.model, ctx.emb, it["question"])
    d = depths(
        pipeline,
        retrieve_depth=run_cfg["retrieve_depth"],
        retrieval_cfg=rc,
        rerank_cfg=ctx.rrcfg,
        baseline_top_k=baseline()["top_k"],
    )
    k_dense = run_cfg["retrieve_depth"] if pipeline == "config_1_dense" else rc["k_dense"]
    dense = dense_search(conn, vec, k_dense, rc)
    fused, reranked, secs = [], None, None
    if pipeline != "config_1_dense":
        sp = sparse(conn, it["question"], rc["k_sparse"], rc["sparse"], ctx.index)
        w = rc["weights"]
        fused = rrf_fuse([dense, sp], [w["dense"], w["sparse"]], rc["rrf_k"])
        fused = fused[: d["retrieve_depth"]]
    if pipeline == "config_4_rerank":
        texts = texts_for(conn, fused)
        reranked, secs = rerank_one(ctx.reranker, it["question"], [(c, texts[c]) for c in fused])
    c = context_for(pipeline, dense=dense, fused=fused, reranked=reranked, rerank_seconds=secs,
                    rerank_cfg=ctx.rrcfg, question_type=it["question_type"],
                    baseline_top_k=baseline()["top_k"])  # fmt: skip
    record = {
        "item_id": it["item_id"], "pipeline": pipeline, "retrieved": c["retrieved"],
        "retrieved_post_rerank": c["retrieved_post_rerank"],
        "generator_input": c["generator_input"], "rerank_seconds": secs,
        "rerank_fell_back": c["fell_back"], "claims_pre": [], "claims_post": [],
    }  # fmt: skip
    if c["abstain"]:  # every chunk below the score floor: no generator call (PRD 7.3)
        return {**record, "answer": {"text": "", "claims": [], "abstained": True},
                "verdict": "ABSTAIN", "abstain_reason": "score_floor", "model_served": None,
                "backend": gen["backend"], "usage": None,
                "latency_s": round(time.monotonic() - t0, 2),
                "answered_at": datetime.now(UTC).isoformat(timespec="seconds")}  # fmt: skip
    texts = texts_for(conn, c["generator_input"])
    chunks = [Retrieved(cid, 0.0, texts[cid]) for cid in c["generator_input"]]
    a = call_model(chunks, it["question"], gen, TIER)
    return {
        **record, **answer_fields(a, c["generator_input"], ctx, it["question"], texts,
                                  run_cfg["nli_threshold"]),
        "model_served": a.model, "backend": a.backend,
        "usage": {"input_tokens": a.input_tokens, "output_tokens": a.output_tokens,
                  "cache_read_tokens": a.cache_read_tokens,
                  "cache_creation_tokens": a.cache_creation_tokens},
        "latency_s": round(time.monotonic() - t0, 2),
        "answered_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }  # fmt: skip


def answer_routed(conn, ctx: Context, it: dict, gen: dict, run_cfg: dict) -> dict:
    """The eval's call into the served path (api.pipeline.answer_question), one trace per item."""
    with tracing.trace("eval-item", item_id=it["item_id"], pipeline=run_cfg["pipeline"]) as root:
        if root is not None:
            root.content("question", it["question"])
        r = pipeline.answer_question(conn, ctx, it["question"], gen, run_cfg, item_id=it["item_id"])
        if root is not None:
            root.set(verdict=r["verdict"], intent=r.get("intent"), backend=r.get("backend"))
        return r


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


def rescore_results(results: list[dict], nli_threshold: float) -> list[dict]:
    """Pure: each structured result's verdict and claims_post from its stored checks
    at the threshold (TRADEOFFS, re-score derivation). Other fields unchanged."""
    from api.verify.verdict import item_verdict, rescore_claims, verdict

    out = []
    for r in results:
        if r.get("claims_pre") is None:
            out.append(r)
            continue
        pre = rescore_claims(r["claims_pre"], nli_threshold)
        gv, post = verdict(pre, nli_threshold)
        v, why = item_verdict(bool(r["answer"].get("abstained")), gv, pre)
        new = {**r, "claims_pre": pre, "claims_post": post, "gate_verdict": gv, "verdict": v}
        new.pop("abstain_reason", None)
        if why:
            new["abstain_reason"] = why
        out.append(new)
    return out


def rescore_run(items: dict, run_cfg: dict, run_id: str, nli_threshold: float) -> None:
    runs = REPO_ROOT / run_cfg["runs_dir"]
    saved = json.loads((runs / f"{run_id}.meta.json").read_text(encoding="utf-8"))
    results = rescore_results(read_jsonl(runs / f"{run_id}.results.jsonl"), nli_threshold)
    meta = {k: v for k, v in saved.items() if k != "item_order"}
    meta = {**meta, "derived": f"re-score of run {run_id} at nli_threshold {nli_threshold}",
            "source_run": run_id, "nli_threshold": nli_threshold}  # fmt: skip
    report = build_report(items, results, meta, saved["k"], nli_threshold)
    doc = {"report": report, "items": [
        {"item_id": r["item_id"], "verdict": r["verdict"], "gate_verdict": r.get("gate_verdict"),
         "abstain_reason": r.get("abstain_reason"), "claims_post": r.get("claims_post")}
        for r in results]}  # fmt: skip
    path = runs / f"{run_id}.rescore-{nli_threshold}.json"
    path.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(format_report(report))
    print(f"wrote {path}")


def verdict_summary(items: dict, results: list[dict]) -> dict:
    """Counts the re-verification compares: verdicts and abstain reasons per
    source, XBRL statuses, ungrounded and scale-unknown figure claims."""
    from collections import Counter

    def src(r):
        return items[r["item_id"]]["source"]

    figs = [c for r in results for c in r.get("claims_pre") or [] if c.get("figure")]
    verdicts = Counter(f"{src(r)}/{r['verdict']}" for r in results)
    reasons = Counter(f"{src(r)}/{r.get('abstain_reason')}" for r in results
                      if r["verdict"] == "ABSTAIN")  # fmt: skip
    status = Counter(str((c["checks"].get("xbrl") or {}).get("status")) for c in figs)
    return {
        "verdict": dict(sorted(verdicts.items())),
        "abstain_reason": dict(sorted(reasons.items())),
        "xbrl_status": dict(sorted(status.items())),
        "figure_claims": len(figs),
        "figure_ungrounded": sum(not c["checks"]["numbers_grounded"] for c in figs),
        "figure_unit_false": sum(c["checks"]["unit_ok"] is False for c in figs),
        "figure_unit_unknown": sum(c["checks"]["unit_ok"] == "unknown" for c in figs),
    }


def reverify_run(items: dict, run_cfg: dict, run_id: str, tag: str) -> None:
    """Re-run the model-free checks (grounding, XBRL) over a run's stored claims,
    then the verdicts; a derived file, never a new run (TRADEOFFS, F-128)."""
    from api.db import connect
    from api.verify.gate import Gate
    from api.verify.verdict import item_verdict, verdict

    runs = REPO_ROOT / run_cfg["runs_dir"]
    saved = json.loads((runs / f"{run_id}.meta.json").read_text(encoding="utf-8"))
    before = read_jsonl(runs / f"{run_id}.results.jsonl")
    threshold = saved.get("verification", {}).get("nli_threshold")
    names = yaml.safe_load(TEMPLATES.read_text(encoding="utf-8"))["company_names"]
    after = []
    with connect() as conn:
        gate = Gate(conn, names)
        for r in before:
            if r.get("claims_pre") is None:
                after.append(r)
                continue
            texts = texts_for(conn, r["generator_input"])
            pre = gate.recheck(r["claims_pre"], r["generator_input"], texts)
            gv, post = verdict(pre, threshold)
            v, why = item_verdict(bool(r["answer"].get("abstained")), gv, pre)
            new = {**r, "claims_pre": pre, "claims_post": post, "gate_verdict": gv, "verdict": v}
            new.pop("abstain_reason", None)
            if why:
                new["abstain_reason"] = why
            after.append(new)
    meta = {k: v for k, v in saved.items() if k != "item_order"}
    meta = {**meta, "derived": f"re-verification of run {run_id} ({tag}): grounding and XBRL "
                               "checks recomputed over stored claims, no model call",
            "source_run": run_id}  # fmt: skip
    report = build_report(items, after, meta, saved["k"], threshold)
    changed = [
        {"item_id": a["item_id"], "verdict_before": b["verdict"], "verdict_after": a["verdict"]}
        for b, a in zip(before, after, strict=True)
        if a["verdict"] != b["verdict"]
    ]
    doc = {"kind": f"derived: re-verification of {run_id}", "tag": tag, "report": report,
           "summary": {"as_run": verdict_summary(items, before),
                       "reverified": verdict_summary(items, after)},
           "verdict_changes": changed,
           "items": [{"item_id": r["item_id"], "verdict": r["verdict"],
                      "abstain_reason": r.get("abstain_reason"),
                      "claims_pre": r.get("claims_pre"), "claims_post": r.get("claims_post")}
                     for r in after]}  # fmt: skip
    path = runs / f"{run_id}.reverify-{tag}.json"
    path.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(format_report(report))
    for k in doc["summary"]["as_run"]:
        print(f"{k}:\n  as run      {doc['summary']['as_run'][k]}\n  re-verified "
              f"{doc['summary']['reverified'][k]}")  # fmt: skip
    print(f"verdict changes: {len(changed)}")
    for c in changed:
        print(f"  {c['item_id']}: {c['verdict_before']} -> {c['verdict_after']}")
    print(f"wrote {path}")


SMOKE_PER_TYPE = 3
FIGURE_CHECKS = ("citation_valid", "entity_ok", "numbers_grounded", "unit_ok", "period_stated")


def failed_checks(r: dict) -> list[list[str]]:
    """Per claim not kept by the gate, the names of the checks it failed."""
    kept = {c["claim_id"] for c in r.get("claims_post") or []}
    out = []
    for c in r.get("claims_pre") or []:
        if c["claim_id"] in kept or r.get("claims_post") is None:
            continue
        k = c["checks"]
        names = [n for n in FIGURE_CHECKS if not k.get(n)] if c.get("figure") else []
        if k.get("xbrl_contradiction"):
            names.append("xbrl_contradiction")
        out.append([c["claim_id"], *(names or ["entail"])])
    return out


def smoke_items(items: dict, seed: int) -> list[str]:
    """SMOKE_PER_TYPE items per question type, drawn by seed from the sorted ids."""
    import random

    rng, out = random.Random(seed), []
    for qt in sorted({it["question_type"] for it in items.values()}):
        ids = sorted(i for i, it in items.items() if it["question_type"] == qt)
        out += sorted(rng.sample(ids, SMOKE_PER_TYPE))
    return out


def smoke(items: dict, gen: dict, run_cfg: dict, seed: int) -> None:
    """A pipeline check, not a measurement: runs the seeded subset end to end,
    checks the records, builds and formats the report, and stores only what
    broke. No metric is written."""
    from api.db import connect

    runs = REPO_ROOT / run_cfg["runs_dir"]
    run_id, order = uuid.uuid4().hex[:12], smoke_items(items, seed)
    meta = {**current_meta(gen, run_cfg), "run_id": run_id, "k": run_cfg["k"]}
    print(f"smoke {run_id}: {len(order)} items (seed {seed}): {order}", flush=True)
    results, failure = [], None
    with connect() as conn:
        ctx = Context(conn, run_cfg["pipeline"])
        answer = answer_routed if run_cfg["pipeline"] == "config_4_routed" else answer_one
        for n, iid in enumerate(order, start=1):
            try:
                results.append(answer(conn, ctx, items[iid], gen, run_cfg))
            except Exception as e:  # a pipeline check records any failure, then stops
                failure = {"item_id": iid, "error": f"{type(e).__name__}: {e}"}
                print(f"FAIL at {iid}: {failure['error']}")
                break
            r = results[-1]
            print(f"[{n}/{len(order)}] {iid} {r.get('intent')} {r['verdict']} "
                  f"{r.get('latency_s')}s", flush=True)  # fmt: skip
    checks = {"meta_disagreements": [], "report": None}
    if not failure:
        from eval.pipeline import depth_disagreements

        checks["meta_disagreements"] = depth_disagreements(meta, results, items)
        try:
            format_report(build_report(items, results, meta, run_cfg["k"],
                                       run_cfg["nli_threshold"]))  # fmt: skip
            checks["report"] = "built and formatted"
        except ValueError as e:
            refused = run_cfg["nli_threshold"] is None and "nli_threshold" in str(e)
            checks["report"] = ("refused: claims present and nli_threshold null (expected, "
                                "PRD 7.5 gate)" if refused else f"ValueError: {e}")  # fmt: skip
        except Exception as e:
            checks["report"] = f"{type(e).__name__}: {e}"
    ok = (
        not failure
        and not checks["meta_disagreements"]
        and (checks["report"] == "built and formatted" or checks["report"].startswith("refused:"))
    )
    doc = {"kind": "PIPELINE CHECK, not a measurement: no number here goes into a finding "
                   "except a failure", "seed": seed, "item_ids": order, "ok": ok,
           "failure": failure, "checks": checks, "meta": meta,
           "records": [{"item_id": r["item_id"], "keys": sorted(r), "intent": r.get("intent"),
                        "verdict": r["verdict"], "abstain_reason": r.get("abstain_reason"),
                        "contract_violations": r.get("contract_violations"),
                        "failed_checks": failed_checks(r)}
                       for r in results]}  # fmt: skip
    (runs / f"{run_id}.smoke.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"smoke {run_id}: ok {ok}; failure {failure}; checks {checks}")
    sys.exit(0 if ok else 1)


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
    subset = None
    if arg("--subset"):
        path = REPO_ROOT / arg("--subset")
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        subset = [i for ids in doc["items"].values() for i in ids]
        missing = [i for i in subset if i not in items]
        if missing:
            raise SystemExit(f"subset {path.name} names items not in the candidates: {missing[:5]}")
        meta["subset"] = {"file": arg("--subset"), "items": len(subset),
                          "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}  # fmt: skip

    if arg("--reverify"):
        reverify_run(items, run_cfg, arg("--reverify"), sys.argv[sys.argv.index("--reverify") + 2])
        return
    if arg("--rescore"):
        rescore_run(
            items, run_cfg, arg("--rescore"), float(sys.argv[sys.argv.index("--rescore") + 2])
        )
        return
    if arg("--smoke"):
        smoke(items, gen, run_cfg, int(arg("--smoke")))
        return
    if arg("--report"):
        run_id = arg("--report")
        saved = json.loads((runs / f"{run_id}.meta.json").read_text(encoding="utf-8"))
        results = read_jsonl(runs / f"{run_id}.results.jsonl")
        if len(results) != len(saved["item_order"]):
            raise SystemExit(f"run {run_id} has {len(results)} of {len(saved['item_order'])} items")
        report_meta = {k: v for k, v in saved.items() if k != "item_order"}
        report = build_report(items, results, report_meta, saved["k"], run_cfg["nli_threshold"])
        (runs / f"{run_id}.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
        print(format_report(report))
        return
    if arg("--resume"):
        run_id = arg("--resume")
        saved = json.loads((runs / f"{run_id}.meta.json").read_text(encoding="utf-8"))
        diff = {k for k in meta if meta[k] != saved.get(k)}
        if diff:
            raise SystemExit(f"run {run_id} cannot resume: {sorted(diff)} changed since it began")
        order = saved["item_order"]
    elif "--run" in sys.argv:
        run_id = uuid.uuid4().hex[:12]
        order = subset or list(items)
        order = order[: int(arg("--limit"))] if arg("--limit") else order
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

        with connect() as conn:
            ctx = Context(conn, run_cfg["pipeline"])
            answer = answer_routed if run_cfg["pipeline"] == "config_4_routed" else answer_one
            code = run_items(
                todo,
                lambda iid: answer(conn, ctx, items[iid], gen, run_cfg),
                results_path,
                runs / f"{run_id}.errors.jsonl",
            )
        if code:
            print(f"resume with --resume {run_id}")
            sys.exit(code)
    results = read_jsonl(results_path)
    report = build_report(items, results, {**meta, "run_id": run_id}, run_cfg["k"],
                          run_cfg["nli_threshold"])  # fmt: skip
    (runs / f"{run_id}.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(format_report(report))
    if baseline_out:
        (REPO_ROOT / baseline_out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    if arg("--report-out"):
        out = REPO_ROOT / arg("--report-out")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
        out.with_suffix(".md").write_text(
            f"### Eval report, run {run_id}\n\n```\n{format_report(report)}\n```\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
