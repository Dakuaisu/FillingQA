"""Rerank a retrieval-only run's fused lists and measure (PRD 7.3; F-13).

python -m scripts.rerank_run RETRIEVAL_RUN_ID

No generation. For each item: the stored hybrid top-50 (the pre-rerank list),
reranked by the cross-encoder in one pass; the post-rerank list is the top-n
(8, or 10 for synthesis). Reports per source column: pre-rerank Sufficiency at 8
and 10, post-rerank sufficiency at the item's top-n without and with the score
floor (calibration pending), the items the floor would empty (abstain), and
latency against the 800 ms timeout. Writes eval/runs/<run_id>.rerank.json.
"""

from __future__ import annotations

import json
import sys
import uuid

from api.config import REPO_ROOT, rerank
from api.db import connect
from api.query.rerank import apply_floor, load_reranker, top_n_for
from api.query.rerank import rerank as rerank_one
from eval.metrics.retrieval import mrr, ndcg_at_k, recall_at_k, sufficiency_at_k
from eval.runner import COLUMNS, SOURCES

RUNS = REPO_ROOT / "eval" / "runs"
DATASETS = sorted((REPO_ROOT / "eval" / "candidates").glob("*_candidates.jsonl"))


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def main() -> None:
    src = sys.argv[1]
    cfg = rerank()
    doc = json.loads((RUNS / f"{src}.retrieval.json").read_text(encoding="utf-8"))
    items = {}
    for p in DATASETS:
        for x in p.read_text(encoding="utf-8").split("\n"):
            if x:
                it = json.loads(x)
                items[it["item_id"]] = it
    ids = sorted({c for r in doc["results"] for c in r["hybrid"]})
    with connect() as conn:
        texts = dict(conn.execute("SELECT chunk_id, text FROM chunks WHERE chunk_id = ANY(%s)",
                                  (ids,)).fetchall())  # fmt: skip
    model = load_reranker(cfg)
    out = []
    for n, r in enumerate(doc["results"], start=1):
        it = items[r["item_id"]]
        ranked, secs = rerank_one(model, it["question"], [(c, texts[c]) for c in r["hybrid"]])
        top = top_n_for(it["question_type"], cfg)
        floored = apply_floor(ranked, cfg["score_floor"])
        out.append({"item_id": r["item_id"], "pre": r["hybrid"], "top_n": top,
                    "post": [c for c, _ in ranked[:top]],
                    "post_floor": [c for c, _ in floored[:top]],
                    "scores": [[c, round(s, 6)] for c, s in ranked],
                    "seconds": round(secs, 3)})  # fmt: skip
        if n % 25 == 0:
            print(f"[{n}/{len(doc['results'])}]", flush=True)
    run_id = uuid.uuid4().hex[:12]

    def col(rs):
        sets = lambda r: items[r["item_id"]]["gold_evidence_sets"]  # noqa: E731
        return {
            "items": len(rs),
            "pre_suff@8": mean([sufficiency_at_k(r["pre"], sets(r), 8) for r in rs]),
            "pre_suff@10": mean([sufficiency_at_k(r["pre"], sets(r), 10) for r in rs]),
            "post_suff@top_n": mean(
                [sufficiency_at_k(r["post"], sets(r), r["top_n"]) for r in rs]
            ),
            "post_recall@top_n": mean([recall_at_k(r["post"], sets(r), r["top_n"]) for r in rs]),
            "post_mrr": mean([mrr(r["post"], sets(r)) for r in rs]),
            "post_ndcg@top_n": mean([ndcg_at_k(r["post"], sets(r), r["top_n"]) for r in rs]),
            "post_floor_suff@top_n (pending)":
                mean([sufficiency_at_k(r["post_floor"], sets(r), r["top_n"]) for r in rs]),
            "floor_empties (abstain)": sum(not r["post_floor"] for r in rs),
            "over_timeout": sum(r["seconds"] * 1000 > cfg["timeout_ms"] for r in rs),
        }  # fmt: skip

    by = {s: [r for r in out if items[r["item_id"]]["source"] == s] for s in SOURCES}
    columns = {**{s: col(rs) if rs else None for s, rs in by.items()}, "aggregate": col(out)}
    lat = sorted(r["seconds"] for r in out)
    report = {"run_id": run_id, "kind": "rerank of a retrieval-only run, no generation",
              "source_run": src, "rerank": cfg, "columns": columns,
              "latency_s": {"p50": lat[len(lat) // 2], "p95": lat[int(0.95 * (len(lat) - 1))],
                            "max": lat[-1]}}  # fmt: skip
    (RUNS / f"{run_id}.rerank.json").write_text(
        json.dumps({"report": report, "results": out}, indent=1) + "\n", encoding="utf-8"
    )
    floor = f"floor {cfg['score_floor']} ({cfg['floor_calibration']})"
    print(f"rerank run {run_id} of retrieval run {src}: {len(out)} items; {cfg['model']}@"
          f"{cfg['revision'][:12]}; {floor}")  # fmt: skip
    print(f"{'metric':34}" + "".join(f"{c:>14}" for c in COLUMNS))
    for m in columns["aggregate"]:
        cells = [columns[c][m] if columns[c] else None for c in COLUMNS]
        shown = ["-" if v is None else f"{v:.3f}" if isinstance(v, float) else str(v)
                 for v in cells]  # fmt: skip
        print(f"{m:34}" + "".join(f"{x:>14}" for x in shown))
    print(f"latency per item (one pass of up to 50 pairs, this machine): {report['latency_s']}")


if __name__ == "__main__":
    main()
