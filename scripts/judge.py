"""The LLM judge and its validation (PRD 11.3).

python -m scripts.judge labels          # seeded 50-item label sheet + empty labels worksheet
python -m scripts.judge run --run       # judge the pairs (only once all 50 are labelled)
python -m scripts.judge kappa           # Cohen's kappa (refuses until labels and verdicts exist)

The pairs are (item, answer) from the dev run `eval_judge.label_run`; the owner
labels them 1-5 with the rubric in eval/judge/rubrics.py. A judge whose family
is the generator's is same-family judging (F-14): every output says so.
"""

from __future__ import annotations

import json
import random
import sys
from collections import Counter

import yaml

from api.config import REPO_ROOT, eval_judge, generation
from eval.generate.seeding import allocate
from eval.judge.agreement import RELIABLE, cohens_kappa
from eval.judge.judge import family, judge
from eval.judge.rubrics import RUBRIC

CANDIDATES = sorted((REPO_ROOT / "eval" / "candidates").glob("*_candidates.jsonl"))
JUDGE = REPO_ROOT / "eval" / "judge"
SHEET = JUDGE / "label_sheet_v1.md"
LABELS = JUDGE / "labels_v1.yaml"
VERDICTS = JUDGE / "verdicts_v1.jsonl"


def read_jsonl(path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").split("\n") if x.strip()]


def draw(results: list[dict], items: dict, seed: int, n: int) -> list[str]:
    """Seeded, proportional by source (largest remainder), sorted ids within source."""
    by_source: dict[str, list[str]] = {}
    for r in results:
        by_source.setdefault(items[r["item_id"]]["source"], []).append(r["item_id"])
    slots = allocate({s: len(v) for s, v in by_source.items()}, n)
    rng = random.Random(seed)
    out = []
    for s in sorted(slots):
        out += sorted(rng.sample(sorted(by_source[s]), slots[s]))
    return out


def labelled() -> dict[str, int]:
    if not LABELS.exists():
        return {}
    doc = yaml.safe_load(LABELS.read_text(encoding="utf-8"))
    return {e["item_id"]: e["label"] for e in doc["labels"] if e.get("label") is not None}


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    cfg = eval_judge()
    items = {it["item_id"]: it for p in CANDIDATES for it in read_jsonl(p)}
    run = read_jsonl(REPO_ROOT / "eval" / "runs" / f"{cfg['label_run']}.results.jsonl")
    answers = {r["item_id"]: r for r in run}
    if cmd == "labels":
        if labelled():
            raise SystemExit(f"{LABELS} already holds labels; not redrawn")
        ids = draw(run, items, cfg["label_seed"], cfg["label_n"])
        rubric = "\n".join(f"- {k}: {v}" for k, v in sorted(RUBRIC.items(), reverse=True))
        lines = ["# Judge validation label sheet (PRD 11.3)", "",
                 f"{len(ids)} (item, answer) pairs drawn with seed {cfg['label_seed']} from dev "
                 f"run {cfg['label_run']} (claude_cli, {answers[ids[0]]['model_served']}), "
                 f"proportional by source {dict(Counter(items[i]['source'] for i in ids))}. "
                 "OWNER-BLOCKED: label each 1-5 in eval/judge/labels_v1.yaml, before seeing any "
                 "judge score.", "", "Rubric:", rubric, ""]  # fmt: skip
        for i in ids:
            it, a = items[i], answers[i]["answer"]["text"]
            lines += [f"## {i} ({it['source']}, {it['question_type']})", "",
                      f"- Question: {it['question']}", f"- Reference: {it['reference_answer']}",
                      "- Answer:", "", "```", a.strip(), "```", ""]  # fmt: skip
        SHEET.write_text("\n".join(lines), encoding="utf-8")
        LABELS.write_text(yaml.safe_dump({
            "sheet": SHEET.name, "run": cfg["label_run"], "seed": cfg["label_seed"],
            "labels": [{"item_id": i, "label": None} for i in ids],
        }, sort_keys=False), encoding="utf-8")  # fmt: skip
        print(f"wrote {SHEET.relative_to(REPO_ROOT)} and {LABELS.relative_to(REPO_ROOT)}: "
              f"{len(ids)} pairs {dict(Counter(items[i]['source'] for i in ids))}")  # fmt: skip
        return
    labels = labelled()
    ids = [e["item_id"] for e in yaml.safe_load(LABELS.read_text())["labels"]]
    if cmd == "run":
        if len(labels) < len(ids) or "--run" not in sys.argv:
            raise SystemExit(f"labels {len(labels)} of {len(ids)}: the judge runs only on a "
                             "fully labelled set, with --run")  # fmt: skip
        gen = generation()
        done = {v["item_id"] for v in read_jsonl(VERDICTS)}
        for i in ids:
            if i in done:
                continue
            v = judge(items[i], answers[i]["answer"]["text"], gen, cfg["tier"],
                      answers[i]["model_served"])  # fmt: skip
            with VERDICTS.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(v) + "\n")
        return
    if cmd == "kappa":
        verdicts = {v["item_id"]: v for v in read_jsonl(VERDICTS)}
        if len(labels) < len(ids) or any(i not in verdicts for i in ids):
            raise SystemExit(f"labels {len(labels)} of {len(ids)}, verdicts {len(verdicts)}: "
                             "kappa needs both complete")  # fmt: skip
        k = cohens_kappa([labels[i] for i in ids], [verdicts[i]["score"] for i in ids])
        fams = {verdicts[i]["judge_family"] for i in ids}
        gen_fams = {family(answers[i]["model_served"]) for i in ids}
        same = bool(fams & gen_fams)
        verdict = "reliable" if k is not None and k >= RELIABLE else "UNRELIABLE (< 0.6)"
        tag = " -- SAME FAMILY (F-14)" if same else ""
        print(f"Cohen's kappa {k} on {len(ids)} pairs; judge {sorted(fams)}, generator "
              f"{sorted(gen_fams)}{tag}; {verdict}")  # fmt: skip
        return
    raise SystemExit("usage: labels | run --run | kappa")


if __name__ == "__main__":
    main()
