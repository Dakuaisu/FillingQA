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
from eval.pipeline import depth_disagreements

SOURCES = ("xbrl_auto", "llm_seeded", "handwritten")
COLUMNS = (*SOURCES, "aggregate")
NOTE_F110 = ("F-110: llm_seeded retrieval numbers reflect lexical overlap between seeded questions "
             "and their source chunk")  # fmt: skip
NOTE_F118 = ("F-118: retrieval numbers on this filtered run come from candidate questions that "
             "name their company and period; the router's job here is easier than on real "
             "questions")  # fmt: skip
DEV_BANNER = ("DEVELOPMENT RUN (claude_cli): not a CI baseline, not publishable, not comparable "
              "with anthropic_api runs (F-59)")  # fmt: skip


def _mean(xs: list) -> float | None:
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


PENDING_NLI = "pending NLI threshold (F-125)"


def _generation(results: list[dict], nli_threshold) -> dict:
    """Claim metrics; every one pending while claims exist and the NLI threshold
    is not set (TRADEOFFS: first full run scored before the threshold)."""
    has_claims = any(r.get("claims_pre") or r.get("claims_post") for r in results)
    if has_claims and nli_threshold is None:
        return {"status": PENDING_NLI}
    return generation_metrics(results, nli_threshold if nli_threshold is not None else 0.0)


def _abstention(rows: list[tuple[bool, str]]) -> dict:
    """The 2x2 rates; all pending while any verdict in the column waits on the NLI
    threshold, since the pending items are exactly those with prose claims."""
    if any(v == "PENDING_NLI" for _, v in rows):
        keys = ("partial_rate", "false_answer_rate", "over_abstention_rate",
                "abstention_precision", "abstention_recall", "abstention_f1")  # fmt: skip
        return dict.fromkeys(keys, PENDING_NLI)
    return rates(two_by_two(rows))


def xbrl_summary(results: list[dict]) -> dict | None:
    """Every contradiction with its synonym, figure and facts; claims matched per
    synonym; status counts. None when no result has claims."""
    claims = [(r["item_id"], c) for r in results for c in r.get("claims_pre") or []]
    if not claims:
        return None
    status, per_syn, contra = {}, {}, []
    for iid, c in claims:
        x = (c.get("checks") or {}).get("xbrl")
        if not x:
            continue
        status[x["status"]] = status.get(x["status"], 0) + 1
        if x.get("synonym"):
            per_syn[x["synonym"]] = per_syn.get(x["synonym"], 0) + 1
        if x["status"] == "contradiction":
            contra.append({"item_id": iid, "claim_id": c["claim_id"], "synonym": x["synonym"],
                           "tags": x["tags"], "figure": c["figure"],
                           "period_ends": x["period_ends"], "cited_facts": x["cited_facts"],
                           "period_ok": x["period_ok"]})  # fmt: skip
    return {"status_counts": status, "matched_per_synonym": dict(sorted(per_syn.items())),
            "contradictions": contra}  # fmt: skip


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


def floor_empty(r: dict) -> bool:
    """The score floor emptied the post-rerank list (abstained, no generator call).
    Records written before the `abstain_reason` tag carry it as an empty post-rerank
    list without an RRF fallback, the only path that produces one."""
    if r.get("abstain_reason") == "score_floor":
        return True
    return r.get("retrieved_post_rerank") == [] and not r.get("rerank_fell_back")


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
        "floor_empties": sum(floor_empty(r) for r in results),
        "filtered": sum(bool(r.get("filters")) for r in results),
        "filter_zero_recall": sum(bool(r.get("filter_zero_recall")) for r in results),
        "declined_unsupported": sum(r.get("abstain_reason") == "unsupported" for r in results),
        "pending_nli": sum(r.get("verdict") == "PENDING_NLI" for r in results),
        "rerank_fell_back": sum(bool(r.get("rerank_fell_back")) for r in results),
        "numeric": aggregate(scores),
        "abstention": _abstention(abst),
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
        "intent_matrix": intent_matrix(items, results),
        "xbrl": xbrl_summary(results),
        "meta_disagreements": depth_disagreements(meta, results, items)
        if "retrieve_depth" in meta and "generator_top_k" in meta
        else None,
        "rerank_fell_back": sum(bool(r.get("rerank_fell_back")) for r in results),
        "columns": {
            **{
                s: _slice(items, rs, k, nli_threshold) if rs else None
                for s, rs in by_source.items()
            },
            "aggregate": _slice(items, results, k, nli_threshold),
        },
    }


def intent_matrix(items: dict, results: list[dict]) -> dict | None:
    """{source: {question_type: {intent: n}}} for routed runs, else None."""
    if not any("intent" in r for r in results):
        return None
    out: dict = {}
    for r in results:
        it = items[r["item_id"]]
        row = out.setdefault(it["source"], {}).setdefault(it["question_type"], {})
        row[r.get("intent")] = row.get(r.get("intent"), 0) + 1
    return out


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
    return g["status"] if g["status"] in (NA, PENDING_NLI) else g[key]


def _faith(g: dict):
    """faithfulness_pre is never printed without the answer rate (F-09)."""
    if g["status"] in (NA, PENDING_NLI):
        return g["status"]
    return f"{_fmt(g['faithfulness_pre'])} [{_fmt(g['answer_rate'])}]"


def _fmt(v) -> str:
    return "-" if v is None else f"{v:.3f}" if isinstance(v, float) else str(v)


def format_report(report: dict) -> str:
    k = report["k"]
    lines = [f"run {report['run_id']}  backend: {report['backend']}  "
             f"generation model requested: {report['model_requested']}"]  # fmt: skip
    if report["development_run"]:
        lines.append(DEV_BANNER)
    lines.append(NOTE_F110)
    if report.get("pipeline") == "config_4_routed":
        lines.append(NOTE_F118)
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
            ("  floor_empties (abstain, score_floor; F-112)", lambda c: c.get("floor_empties", 0)),
            ("  rerank fell back to RRF order", lambda c: c.get("rerank_fell_back", 0)),
            ("  router filters applied", lambda c: c.get("filtered", 0)),
            ("  filter_zero_recall (fell back)", lambda c: c.get("filter_zero_recall", 0)),
            ("  declined: intent unsupported", lambda c: c.get("declined_unsupported", 0)),
            ("verdict pending NLI (F-125)", lambda c: c.get("pending_nli", 0)),
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
            ("  checkable only (F-126)",
             lambda c: _gen(c["generation"], "period_accuracy_checkable")),
            ("  uncheckable (in denominator)",
             lambda c: _gen(c["generation"], "period_uncheckable")),
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
    if report.get("intent_matrix"):
        lines.append("router intent by question type (per source):")
        for src, rows in report["intent_matrix"].items():
            for qt, cnt in sorted(rows.items()):
                lines.append(f"  {src:12} {qt:14} {dict(sorted(cnt.items(), key=str))}")
    xs = report.get("xbrl")
    if xs:
        lines.append(f"XBRL check status (claims): {xs['status_counts']}")
        lines.append(f"claims matched per synonym: {xs['matched_per_synonym']}")
        lines.append(f"XBRL contradictions: {len(xs['contradictions'])}")
        for x in xs["contradictions"]:
            lines.append(f"  {x['item_id']} {x['claim_id']}: synonym {x['synonym']!r} -> "
                         f"{x['tags']}; figure {x['figure']}; period ends {x['period_ends']}; "
                         f"cited facts {x['cited_facts']}; period_ok {x['period_ok']}")  # fmt: skip
    lines.append(f"anomalies: {report['anomalies']}")
    md = report.get("meta_disagreements")
    if md is not None:
        lines.append(f"meta: retrieve_depth {report['retrieve_depth']}, generator_top_k "
                     f"{report['generator_top_k']}; items whose stored lists disagree: "
                     f"{len(md)}{' ' + str(md[:10]) if md else ''}")  # fmt: skip
    return "\n".join(lines)
