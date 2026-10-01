"""F-100 diagnostic, read-only over a run file. No gold change.

python -m scripts.f100_check RUN_ID

For each xbrl_auto item numerically correct without a sufficient gold set in the
top 10, does a retrieved non-gold chunk print the reference figure (by
magnitude, at the reference's printed precision)? Comparison items: both values
(the difference is printed in no chunk). Writes eval/candidates/f100_<run>.json
with the two groups; the spot-check scripts flag the first group.
"""

from __future__ import annotations

import json
import sys
from decimal import Decimal

from api.config import REPO_ROOT
from api.db import connect
from api.numbers import NumberFormatError, parse_number
from eval.metrics.numeric import FIGURE, mask, score_item
from eval.metrics.retrieval import sufficiency_at_k

CAND = REPO_ROOT / "eval" / "candidates"
RULE = ("reference figure printed (magnitude, reference precision) in a retrieved non-gold "
        "top-10 chunk; comparison items: both values")  # fmt: skip


def printed_values(text: str) -> set[Decimal]:
    out = set()
    for m in FIGURE.finditer(mask(text)):
        try:
            out.add(abs(parse_number(m.group("num"))))
        except NumberFormatError:
            continue
    return out


def read_jsonl(path) -> list[dict]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").split("\n") if x]


def main() -> None:
    run_id = sys.argv[1]
    items = {
        it["item_id"]: it
        for f in ("xbrl_numeric", "comparison")
        for it in read_jsonl(CAND / f"{f}_candidates.jsonl")
    }
    results = read_jsonl(REPO_ROOT / "eval" / "runs" / f"{run_id}.results.jsonl")

    def wanted(r: dict) -> bool:
        it = items.get(r["item_id"])
        if it is None or not score_item(it, r["answer"]).correct:
            return False
        return not sufficiency_at_k(r["retrieved"], it["gold_evidence_sets"], 10)

    picked = [r for r in results if wanted(r)]
    chunk_ids = sorted({c for r in picked for c in r["retrieved"][:10]})
    with connect() as conn:
        texts = dict(
            conn.execute(
                "SELECT chunk_id, raw_text FROM chunks WHERE chunk_id = ANY(%s)", (chunk_ids,)
            ).fetchall()
        )
    present, absent = {}, []
    for r in picked:
        it = items[r["item_id"]]
        gold = {c for s in it["gold_evidence_sets"] for c in s}
        matches = FIGURE.finditer(mask(it["reference_answer"]))
        need = [abs(parse_number(m.group("num"))) for m in matches]
        need = need[:2] if it["question_type"] == "comparison" else need[:1]
        found = {}
        for v in need:
            top = r["retrieved"][:10]
            hits = [c for c in top if c not in gold and v in printed_values(texts[c])]
            if hits:
                found[str(v)] = hits
        if len(found) == len(need):
            present[r["item_id"]] = found
        else:
            absent.append(r["item_id"])
    out = CAND / f"f100_{run_id}.json"
    doc = {"run_id": run_id, "rule": RULE, "figure_in_retrieved_non_gold_chunk": present,
           "figure_in_no_retrieved_chunk": absent}  # fmt: skip
    out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    print(f"items correct without a sufficient gold set: {len(picked)}")
    print(f"  figure present in a retrieved non-gold chunk: {len(present)} {sorted(present)}")
    print(f"  figure in no retrieved chunk: {len(absent)} {sorted(absent)}")
    print(f"wrote {out.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
