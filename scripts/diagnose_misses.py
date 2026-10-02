"""Read-only diagnosis of retrieval misses (supervisor decision 3; no tuning).

python -m scripts.diagnose_misses EVAL_RUN RETRIEVAL_RUN [--source xbrl_auto]

For every item of the source not sufficient at 10 in EVAL_RUN's pre-rerank list
(`retrieved`), per gold chunk: rank in that list; rank in RETRIEVAL_RUN's
unfiltered hybrid list; whether it is in the unfiltered dense top-50, BM25
top-50, both or neither; whether EVAL_RUN's metadata filter excluded it;
whether the question's line-item label appears in the chunk text, in its
context lines, and in a table caption; whether the context header names the
chunk's own ticker, form and period; and the best gold rank within the item's
filter for BM25 alone and for exact dense search alone. Each item gets one primary cause, the
first that holds:

  filter_excluded_all_gold  every gold chunk is outside the item's filter
  header_mismatch           a gold chunk's context header names another
                            company, form or period than the chunk's metadata
  neither_branch            no gold chunk in the dense or BM25 top-50
  beyond_query_k            gold in the unfiltered hybrid top-50, absent from
                            the routed list (the intent's k)
  ranked_below_10           gold in the routed list, below rank 10
  other

Writes eval/runs/<EVAL_RUN>.diagnosis.json and prints counts and ids.
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter

import yaml

from api.config import REPO_ROOT, retrieval
from api.db import connect
from api.index.embed import load_model
from api.query.retrieve import embed_question, load_bm25
from api.query.router import allowed_chunks
from scripts.eval_run import DATASETS, read_jsonl

RUNS = REPO_ROOT / "eval" / "runs"
CAUSES = ("filter_excluded_all_gold", "header_mismatch", "neither_branch", "beyond_query_k",
          "ranked_below_10", "other")  # fmt: skip


def sufficient(lst: list[str], sets: list[list[str]], k: int = 10) -> bool:
    top = set(lst[:k])
    return any(set(s) <= top for s in sets)


def rank(lst: list[str], cid: str) -> int | None:
    return lst.index(cid) + 1 if cid in lst else None


EXACT = ("SELECT chunk_id FROM chunks WHERE chunk_id = ANY(%s) "
         "ORDER BY embedding <=> %s::vector, chunk_id")  # fmt: skip


def best(lst: list[str], golds: list[str]) -> int | None:
    pos = {c: i for i, c in enumerate(lst, 1)}
    return min((pos[c] for c in golds if c in pos), default=None)


def _bucket(r: int) -> str:
    for hi in (10, 20, 50, 100):
        if r <= hi:
            return f"<= {hi}"
    return "> 100"


def header_ok(text: str, ticker: str, form: str, fy: int, fq: int | None) -> bool:
    first = text.split("\n", 1)[0]
    period = f"Q{fq} FY{fy}" if fq else f"FY{fy}"
    return f"({ticker})" in first and form in first and period in first


def main() -> None:
    eval_id, ret_id = sys.argv[1], sys.argv[2]
    source = sys.argv[sys.argv.index("--source") + 1] if "--source" in sys.argv else "xbrl_auto"
    items = {it["item_id"]: it for p in DATASETS for it in read_jsonl(p)}
    concepts = yaml.safe_load((REPO_ROOT / "eval" / "concepts.yaml").read_text(encoding="utf-8"))
    labels = {li["id"]: li["label"] for li in concepts["line_items"]}
    ev = {r["item_id"]: r for r in read_jsonl(RUNS / f"{eval_id}.results.jsonl")}
    ret = json.loads((RUNS / f"{ret_id}.retrieval.json").read_text(encoding="utf-8"))
    base = {r["item_id"]: r for r in ret["results"]}
    misses = [i for i, r in ev.items() if items[i]["source"] == source
              and not sufficient(r["retrieved"], items[i]["gold_evidence_sets"])]  # fmt: skip
    gold_ids = sorted({c for i in misses for s in items[i]["gold_evidence_sets"] for c in s})
    with connect() as conn:
        index, _ = load_bm25(conn, retrieval()["sparse"])
        meta = conn.execute(
            "SELECT chunk_id, ticker, fiscal_year, fiscal_quarter, form_type FROM chunks"
        ).fetchall()
        texts = dict(conn.execute("SELECT chunk_id, text FROM chunks WHERE chunk_id = ANY(%s)",
                                  (gold_ids,)).fetchall())  # fmt: skip
    cmeta = {m[0]: m[1:] for m in meta}
    model, emb = load_model()
    out, counts = [], Counter()
    for iid in sorted(misses):
        it, r, b = items[iid], ev[iid], base[iid]
        label = next((labels[t] for t in it["tags"] if t in labels), None)
        allowed = allowed_chunks(meta, r["filters"]) if r.get("filters") else None
        gold = []
        for cid in sorted({c for s in it["gold_evidence_sets"] for c in s}):
            t = texts.get(cid, "")
            context = "\n".join(line for line in t.split("\n") if line.startswith("["))
            caption = next((line for line in t.split("\n") if line.startswith("[Table")), "")
            low = label.lower() if label else None
            tk, fy, fq, form = cmeta[cid]
            gold.append({
                "chunk_id": cid,
                "rank_routed": rank(r["retrieved"], cid),
                "rank_unfiltered_hybrid": rank(b["hybrid"], cid),
                "in_dense50": cid in b["dense"], "in_bm25_50": cid in b["sparse"],
                "filter_excludes": allowed is not None and cid not in allowed,
                "label": label,
                "label_in_text": bool(low and low in t.lower()),
                "label_in_context": bool(low and low in context.lower()),
                "is_table": bool(caption), "label_in_caption": bool(low and low in caption.lower()),
                "header_ok": header_ok(t, tk, form, fy, fq),
                "words_of_label_in_text": (
                    sum(w in t.lower() for w in re.findall(r"[a-z]+", low)) if low else None),
            })  # fmt: skip
        scope = allowed if allowed is not None else {m[0] for m in meta}
        golds = [g["chunk_id"] for g in gold]
        bm = [c for c, _ in index.search(it["question"], len(scope), scope)]
        vec = embed_question(model, emb, it["question"])
        with connect() as conn, conn.transaction():
            conn.execute("SET LOCAL enable_indexscan = off")
            conn.execute("SET LOCAL enable_bitmapscan = off")
            rows = conn.execute(EXACT, (sorted(scope), vec)).fetchall()
        dn = [x[0] for x in rows]
        in_filter = {"scope_size": len(scope), "best_gold_rank_bm25": best(bm, golds),
                     "best_gold_rank_exact_dense": best(dn, golds)}  # fmt: skip
        if allowed is not None and all(g["filter_excludes"] for g in gold):
            cause = "filter_excluded_all_gold"
        elif any(not g["header_ok"] for g in gold):
            cause = "header_mismatch"
        elif not any(g["in_dense50"] or g["in_bm25_50"] or g["rank_routed"] for g in gold):
            cause = "neither_branch"
        elif not any(g["rank_routed"] for g in gold):
            cause = "beyond_query_k"
        elif any(g["rank_routed"] and g["rank_routed"] > 10 for g in gold):
            cause = "ranked_below_10"
        else:
            cause = "other"
        counts[cause] += 1
        out.append({"item_id": iid, "question_type": it["question_type"],
                    "question": it["question"], "intent": r.get("intent"),
                    "filters": r.get("filters"),
                    "routed_list_len": len(r["retrieved"]), "cause": cause,
                    "in_filter": in_filter, "gold": gold})  # fmt: skip
    summary = {
        "eval_run": eval_id, "retrieval_run": ret_id, "source": source,
        "items": sum(1 for i in ev if items[i]["source"] == source), "misses": len(misses),
        "by_cause": {c: counts.get(c, 0) for c in CAUSES},
        "ids_by_cause": {c: [x["item_id"] for x in out if x["cause"] == c] for c in CAUSES},
        "gold_chunks": sum(len(x["gold"]) for x in out),
        "gold_label_in_text": sum(g["label_in_text"] for x in out for g in x["gold"]),
        "gold_tables": sum(g["is_table"] for x in out for g in x["gold"]),
        "gold_tables_label_in_caption": sum(g["label_in_caption"] for x in out for g in x["gold"]),
        "gold_header_ok": sum(g["header_ok"] for x in out for g in x["gold"]),
        "gold_filter_excluded": sum(g["filter_excludes"] for x in out for g in x["gold"]),
        "in_filter_best_gold_rank_min_of_bm25_dense": dict(sorted(Counter(
            _bucket(min(x["in_filter"]["best_gold_rank_bm25"] or 10**6,
                        x["in_filter"]["best_gold_rank_exact_dense"] or 10**6))
            for x in out).items())),
        "gold_dense50_bm25_50": dict(Counter(
            f"dense={g['in_dense50']} bm25={g['in_bm25_50']}" for x in out for g in x["gold"])),
    }  # fmt: skip
    path = RUNS / f"{eval_id}.diagnosis.json"
    path.write_text(json.dumps({"kind": "read-only diagnosis, no tuning", "summary": summary,
                                "items": out}, indent=1) + "\n", encoding="utf-8")  # fmt: skip
    print(json.dumps(summary, indent=1))
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
