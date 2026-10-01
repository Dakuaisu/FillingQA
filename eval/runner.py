"""Eval run scoring and the report (PRD 11.2, 11.4). Pure: no retrieval, no model call.

Every report is stamped with the generation backend; a `claude_cli` run is marked
a development run (F-59) and carries the models actually served per item (F-60).
Metrics are broken out by `source` and aggregated (PRD 11.2).
"""

from __future__ import annotations

from collections import Counter

from api.generate.generator import DEV_BACKENDS
from eval.metrics.abstention import rates, two_by_two
from eval.metrics.numeric import aggregate, score_item
from eval.metrics.retrieval import mrr, ndcg_at_k, precision_at_k, recall_at_k, sufficiency_at_k

SOURCES = ("xbrl_auto", "llm_seeded", "handwritten")
COLUMNS = (*SOURCES, "aggregate")
DEV_BANNER = ("DEVELOPMENT RUN (claude_cli): not a CI baseline, not publishable, not comparable "
              "with anthropic_api runs (F-59)")  # fmt: skip


def _mean(xs: list) -> float | None:
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _slice(items: dict, results: list[dict], k: int) -> dict:
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
    }


def build_report(items: dict, results: list[dict], meta: dict, k: int) -> dict:
    """`items`: item_id -> item; `results`: one per answered item, with retrieved,
    retrieved_post_rerank (or None), answer {text, claims, abstained}, verdict and
    served model; `meta`: backend, run_id, dataset files, retrieval stage."""
    by_source = {s: [r for r in results if items[r["item_id"]]["source"] == s] for s in SOURCES}
    return {
        **meta,
        "development_run": meta["backend"] in DEV_BACKENDS,
        "k": k,
        "served_models": dict(Counter(r["model_served"] for r in results)),
        "columns": {
            **{s: _slice(items, rs, k) if rs else None for s, rs in by_source.items()},
            "aggregate": _slice(items, results, k),
        },
    }


def _fmt(v) -> str:
    return "-" if v is None else f"{v:.3f}" if isinstance(v, float) else str(v)


def format_report(report: dict) -> str:
    k = report["k"]
    lines = [f"run {report['run_id']}  backend: {report['backend']}  "
             f"generation model requested: {report['model_requested']}"]  # fmt: skip
    if report["development_run"]:
        lines.append(DEV_BANNER)
    lines.append(f"served models: {report['served_models']}  retrieval measured on: "
                 f"{report['retrieval_stage']} (F-13)")  # fmt: skip
    rows = [("items", lambda c: c["items"]), ("retrieval items", lambda c: c["retrieval_n"]),
            (f"Sufficiency@{k}", lambda c: c[f"sufficiency@{k}"]),
            (f"Recall@{k}", lambda c: c[f"recall@{k}"]),
            (f"Precision@{k}", lambda c: c[f"precision@{k}"]), ("MRR", lambda c: c["mrr"]),
            (f"nDCG@{k}", lambda c: c[f"ndcg@{k}"]),
            (f"Sufficiency@{k} post-rerank", lambda c: c[f"sufficiency@{k}_post_rerank"]),
            ("Numeric accuracy (gated)", lambda c: c["numeric"]["numeric_accuracy"]),
            ("  numeric items scored", lambda c: c["numeric"]["n"]),
            ("  excluded unit_scale_unknown",
             lambda c: c["numeric"]["excluded"].get("unit_scale_unknown", 0)),
            ("  strict first figure", lambda c: c["numeric"]["strict_first_figure"]),
            ("  within 0.5% (reported)", lambda c: c["numeric"]["tolerant_0_5pct"]),
            ("  comparison values only", lambda c: c["numeric"]["comparison_values_only"]),
            ("  sign agreement", lambda c: c["numeric"]["sign_agreement"]),
            ("  free-text fallback used", lambda c: c["numeric"]["fallback_used"]),
            ("  mean figures per answer", lambda c: c["numeric"]["mean_figure_count"]),
            ("False-answer rate", lambda c: c["abstention"]["false_answer_rate"]),
            ("Over-abstention rate", lambda c: c["abstention"]["over_abstention_rate"]),
            ("Abstention F1", lambda c: c["abstention"]["abstention_f1"])]  # fmt: skip
    cols = report["columns"]
    lines.append(f"{'metric':32}" + "".join(f"{c:>14}" for c in COLUMNS))
    for name, get in rows:
        cells = [_fmt(get(cols[c])) if cols[c] else "-" for c in COLUMNS]
        lines.append(f"{name:32}" + "".join(f"{x:>14}" for x in cells))
    return "\n".join(lines)
