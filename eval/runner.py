"""Eval run scoring and the report (PRD 11.2, 11.4). Pure: no retrieval, no model call.

Every report is stamped with the generation backend; a `claude_cli` run is marked
a development run (F-59) and carries the models actually served per item (F-60).
Metrics are broken out by `source` and aggregated (PRD 11.2).
"""

from __future__ import annotations

from collections import Counter

from api.generate.generator import DEV_BACKENDS
from eval.metrics.abstention import rates, two_by_two
from eval.metrics.generation import NA, generation_metrics
from eval.metrics.numeric import aggregate, score_item
from eval.metrics.retrieval import mrr, ndcg_at_k, precision_at_k, recall_at_k, sufficiency_at_k

SOURCES = ("xbrl_auto", "llm_seeded", "handwritten")
COLUMNS = (*SOURCES, "aggregate")
DEV_BANNER = ("DEVELOPMENT RUN (claude_cli): not a CI baseline, not publishable, not comparable "
              "with anthropic_api runs (F-59)")  # fmt: skip


def _mean(xs: list) -> float | None:
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _generation(results: list[dict], nli_threshold) -> dict:
    has_claims = any(r.get("claims_pre") or r.get("claims_post") for r in results)
    if has_claims and nli_threshold is None:
        raise ValueError("claims present but eval_run.nli_threshold is not set (PRD 7.5)")
    return generation_metrics(results, nli_threshold if nli_threshold is not None else 0.0)


def retrieval_slice(items: dict, results: list[dict], k: int, field: str = "retrieved") -> dict:
    """Retrieval metrics at k on one stored list per item (`field`)."""
    cols = {"sufficiency": sufficiency_at_k, "recall": recall_at_k, "precision": precision_at_k}
    out = {"items": len(results)}
    for name, f in cols.items():
        out[f"{name}@{k}"] = _mean([f(r[field], items[r["item_id"]]["gold_evidence_sets"], k)
                                    for r in results])  # fmt: skip
    out["mrr"] = _mean([mrr(r[field], items[r["item_id"]]["gold_evidence_sets"]) for r in results])
    out[f"ndcg@{k}"] = _mean([ndcg_at_k(r[field], items[r["item_id"]]["gold_evidence_sets"], k)
                              for r in results])  # fmt: skip
    return out


def _slice(items: dict, results: list[dict], k: int, nli_threshold=None) -> dict:
    ret = {"sufficiency": [], "recall": [], "precision": [], "mrr": [], "ndcg": [],
           "sufficiency_post_rerank": []}  # fmt: skip
    scores, abst = [], []
    for r in results:
        it = items[r["item_id"]]
        sets, got = it["gold_evidence_sets"], r["retrieved"]
        ret["sufficiency"].append(sufficiency_at_k(got, sets, k))
        ret["recall"].append(recall_at_k(got, sets, k))
        ret["precision"].append(precision_at_k(got, sets, k))
        ret["mrr"].append(mrr(got, sets))
        ret["ndcg"].append(ndcg_at_k(got, sets, k))
        post = r.get("retrieved_post_rerank")
        ret["sufficiency_post_rerank"].append(
            sufficiency_at_k(post, sets, k) if post is not None else None
        )
        scores.append(score_item(it, r["answer"]))
        abst.append((it["expected_abstain"], r["verdict"]))
    n_ret = sum(x is not None for x in ret["sufficiency"])
    return {
        "items": len(results),
        "retrieval_n": n_ret,
        f"sufficiency@{k}": _mean(ret["sufficiency"]),
        f"recall@{k}": _mean(ret["recall"]),
        f"precision@{k}": _mean(ret["precision"]),
        "mrr": _mean(ret["mrr"]),
        f"ndcg@{k}": _mean(ret["ndcg"]),
        f"sufficiency@{k}_post_rerank": _mean(ret["sufficiency_post_rerank"]),
        "numeric": aggregate(scores),
        "abstention": rates(two_by_two(abst)),
        "generation": _generation(results, nli_threshold),
    }


def build_report(items: dict, results: list[dict], meta: dict, k: int, nli_threshold=None) -> dict:
    """`items`: item_id -> item; `results`: one per answered item, with retrieved,
    retrieved_post_rerank (or None), answer {text, claims, abstained}, verdict and
    served model; `meta`: backend, run_id, dataset files, retrieval stage."""
    by_source = {s: [r for r in results if items[r["item_id"]]["source"] == s] for s in SOURCES}
    return {
        **meta,
        "development_run": meta["backend"] in DEV_BACKENDS,
        "k": k,
        "served_models": dict(Counter(r["model_served"] for r in results)),
        "anomalies": anomalies(results),
        "rerank_fell_back": sum(bool(r.get("rerank_fell_back")) for r in results),
        "columns": {
            **{
                s: _slice(items, rs, k, nli_threshold) if rs else None
                for s, rs in by_source.items()
            },
            "aggregate": _slice(items, results, k, nli_threshold),
        },
    }


def anomalies(results: list[dict]) -> dict:
    """Things that look off, reported as findings: empty retrieval or answer, slow items."""
    lat = sorted(r["latency_s"] for r in results if r.get("latency_s") is not None)
    p50 = lat[len(lat) // 2] if lat else None
    return {
        "empty_retrieval": [r["item_id"] for r in results if not r["retrieved"]],
        "empty_answer": [r["item_id"] for r in results if not (r["answer"]["text"] or "").strip()],
        "latency_s": {
            "p50": p50,
            "p95": lat[int(0.95 * (len(lat) - 1))] if lat else None,
            "max": lat[-1] if lat else None,
        },
        "slow_items_over_3x_p50": [
            (r["item_id"], r["latency_s"])
            for r in results
            if p50 and r.get("latency_s") is not None and r["latency_s"] > 3 * p50
        ],
    }


def _gen(g: dict, key: str):
    return NA if g["status"] == NA else g[key]


def _faith(g: dict):
    """faithfulness_pre is never printed without the answer rate (F-09)."""
    if g["status"] == NA:
        return NA
    return f"{_fmt(g['faithfulness_pre'])} [{_fmt(g['answer_rate'])}]"


def _fmt(v) -> str:
    return "-" if v is None else f"{v:.3f}" if isinstance(v, float) else str(v)


def format_report(report: dict) -> str:
    k = report["k"]
    lines = [f"run {report['run_id']}  backend: {report['backend']}  "
             f"generation model requested: {report['model_requested']}"]  # fmt: skip
    if report["development_run"]:
        lines.append(DEV_BANNER)
    lines.append(f"pipeline: {report.get('pipeline', 'config_1_dense')}  served models: "
                 f"{report['served_models']}  retrieval measured on: "
                 f"{report['retrieval_stage']} (F-13)")  # fmt: skip
    if report.get("rerank"):
        rr = report["rerank"]
        lines.append(f"rerank: {rr['model']}@{rr['revision'][:12]} on {rr['device']}; top-n "
                     f"{rr['top_n']} ({rr['top_n_synthesis']} synthesis); floor "
                     f"{rr['score_floor']} ({rr['floor_calibration']}); timeout "
                     f"{rr['timeout_ms']} ms; fell back to RRF order: "
                     f"{report.get('rerank_fell_back', 0)}")  # fmt: skip
    rows = [("items", lambda c: c["items"]), ("retrieval items", lambda c: c["retrieval_n"]),
            (f"Sufficiency@{k}", lambda c: c[f"sufficiency@{k}"]),
            (f"Recall@{k}", lambda c: c[f"recall@{k}"]),
            (f"Precision@{k}", lambda c: c[f"precision@{k}"]), ("MRR", lambda c: c["mrr"]),
            (f"nDCG@{k}", lambda c: c[f"ndcg@{k}"]),
            ("Sufficiency post-rerank (top-n)", lambda c: c[f"sufficiency@{k}_post_rerank"]),
            ("Numeric accuracy (gated)", lambda c: c["numeric"]["numeric_accuracy"]),
            ("  numeric items scored", lambda c: c["numeric"]["n"]),
            ("  excluded unit_scale_unknown",
             lambda c: c["numeric"]["excluded"].get("unit_scale_unknown", 0)),
            ("  strict first figure", lambda c: c["numeric"]["strict_first_figure"]),
            ("  within 0.5% (reported)", lambda c: c["numeric"]["tolerant_0_5pct"]),
            ("  comparison values only", lambda c: c["numeric"]["comparison_values_only"]),
            ("  sign agreement", lambda c: c["numeric"]["sign_agreement"]),
            ("  abstained (in denominator)", lambda c: c["numeric"]["abstained"]),
            ("  free-text fallback used", lambda c: c["numeric"]["fallback_used"]),
            ("  mean figures per answer", lambda c: c["numeric"]["mean_figure_count"]),
            ("Faithfulness (pre) [answer rate]", lambda c: _faith(c["generation"])),
            ("Faithfulness (post)", lambda c: _gen(c["generation"], "faithfulness_post")),
            ("Verifier lift", lambda c: _gen(c["generation"], "verifier_lift")),
            ("Claim retention", lambda c: _gen(c["generation"], "claim_retention")),
            ("Citation coverage", lambda c: _gen(c["generation"], "citation_coverage")),
            ("Citation precision", lambda c: _gen(c["generation"], "citation_precision")),
            ("Unit-scale accuracy", lambda c: _gen(c["generation"], "unit_scale_accuracy")),
            ("Period accuracy", lambda c: _gen(c["generation"], "period_accuracy")),
            ("XBRL contradiction rate", lambda c: _gen(c["generation"], "xbrl_contradiction_rate")),
            ("PARTIAL rate", lambda c: c["abstention"]["partial_rate"]),
            ("False-answer rate", lambda c: c["abstention"]["false_answer_rate"]),
            ("Over-abstention rate", lambda c: c["abstention"]["over_abstention_rate"]),
            ("Abstention F1", lambda c: c["abstention"]["abstention_f1"])]  # fmt: skip
    cols = report["columns"]
    lines.append(f"{'metric':32}" + "".join(f"{c:>17}" for c in COLUMNS))
    for name, get in rows:
        cells = [_fmt(get(cols[c])) if cols[c] else "-" for c in COLUMNS]
        lines.append(f"{name:32}" + "".join(f"{x:>17}" for x in cells))
    agg = cols["aggregate"]["numeric"]
    lines.append(f"figures per numeric answer (aggregate): {agg['figure_count_distribution']}")
    lines.append(f"excluded from numeric accuracy (aggregate): {agg['excluded']}")
    lines.append(f"anomalies: {report['anomalies']}")
    return "\n".join(lines)
