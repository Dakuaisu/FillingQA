"""GET /api/v1/metrics: the eval dashboard's data, from committed run files only.

- `gate`: `eval/compare.py`'s per-metric table for the latest gated (non-
  development) eval run against `eval/thresholds.yaml` and the fast baseline;
  with no gated run, every row pending for that reason.
- `retrieval_runs`: model-free retrieval-only runs (`*.retrieval.json`) with their
  per-source hybrid Sufficiency@10, labelled Config 3 on unreviewed candidates.
- `development_runs`: run ids and files only, with the banner; no value from a
  development run reaches the payload (enforced here, tested).
- `owner_blocked`: from `eval/dashboard.yaml`.
OWNER DECISION, dev generator (TRADEOFFS): the dashboard rule.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

from api.config import REPO_ROOT
from api.generate.generator import DEV_BACKENDS
from eval import compare

RUNS = REPO_ROOT / "eval" / "runs"
DASHBOARD = REPO_ROOT / "eval" / "dashboard.yaml"
THRESHOLDS = REPO_ROOT / "eval" / "thresholds.yaml"
BASELINE = REPO_ROOT / "eval" / "baselines" / "main_fast.json"
BANNER = "development run on `claude_cli`, not a result"
F110 = "inflated by lexical overlap with the source chunk (F-110)"
SOURCES = ("xbrl_auto", "llm_seeded", "handwritten", "aggregate")
RUN_ID = re.compile(r"^([0-9a-f]{12})\.(.+)$")


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def is_development(doc: dict) -> bool:
    """A report, meta or filter/smoke document produced on a development backend."""
    if doc.get("development_run"):
        return True
    backend = doc.get("backend") or (doc.get("meta") or {}).get("backend")
    return backend in DEV_BACKENDS


def classify(runs: Path) -> tuple[dict[str, list[str]], list[str], list[str]]:
    """(development run id -> files, gated eval run ids, retrieval run ids)."""
    files: dict[str, list[str]] = {}
    for p in sorted(runs.iterdir()):
        m = RUN_ID.match(p.name)
        if m:
            files.setdefault(m.group(1), []).append(p.name)
    dev, gated, retrieval = {}, [], []
    for rid, names in files.items():
        if f"{rid}.retrieval.json" in names:
            retrieval.append(rid)
            continue
        docs = [_load(runs / n) for n in names if n.endswith(".json")]
        meta = runs / f"{rid}.meta.json"
        if meta.exists() and not any(is_development(d) for d in docs):
            gated.append(rid)
        elif any(is_development(d) for d in docs) or any(
            n.endswith((".smoke.json", ".filter.json")) for n in names):  # fmt: skip
            dev[rid] = sorted(names)
    return dev, gated, retrieval


def retrieval_entry(runs: Path, rid: str, current: str, thresholds: dict) -> dict:
    report = _load(runs / f"{rid}.retrieval.json")["report"]
    cols = report["columns"]["hybrid"]
    by_source = thresholds.get("by_source") or {}
    minimum = (thresholds.get("absolute_minimums") or {}).get("sufficiency_at_10")
    suff = {}
    for s in SOURCES:
        col = cols.get(s)
        t = minimum if s == "aggregate" else (by_source.get(s) or {}).get("sufficiency_at_10")
        suff[s] = {"value": col["sufficiency@10"] if col else None, "threshold": t}
    recorded = (report.get("retrieval") or {}).get("sparse") or {}
    sparse = report.get("sparse_backend") or recorded
    sparse = sparse if isinstance(sparse, str) else sparse.get("backend") or "not recorded"
    dense = report.get("dense_search") or "hnsw (before F-136; not recorded)"
    return {"run_id": rid, "current": rid == current, "config": "Config 3 (PRD 11.6)",
            "label": "model-free hybrid retrieval, unreviewed candidates",
            "dense_search": dense, "sparse": sparse,
            "sufficiency_at_10": suff,
            "notes": {"llm_seeded": F110}}  # fmt: skip


def build(runs: Path = RUNS, dashboard: Path = DASHBOARD, thresholds_path: Path = THRESHOLDS,
          baseline_path: Path = BASELINE) -> dict:  # fmt: skip
    cfg = yaml.safe_load(dashboard.read_text(encoding="utf-8"))
    thresholds = yaml.safe_load(thresholds_path.read_text(encoding="utf-8"))
    dev, gated, retrieval = classify(runs)
    head = None
    by_age = sorted(gated, key=lambda r: (runs / f"{r}.meta.json").stat().st_mtime)
    for rid in reversed(by_age):
        if (runs / f"{rid}.json").exists():
            head = rid
            break
    report = _load(runs / f"{head}.json") if head else None
    baseline = _load(baseline_path) if baseline_path.exists() else None
    table = compare.rows(report, thresholds, baseline)
    return {
        "gate": {"passed": compare.passed(table), "run_id": head,
                 "reason": None if head else "no gated run exists (F-59)", "rows": table},
        "retrieval_runs": [retrieval_entry(runs, r, cfg["current_retrieval_run"], thresholds)
                           for r in retrieval],
        "gated_runs": gated,
        "development_runs": [{"run_id": r, "files": [f"eval/runs/{f}" for f in fs],
                              "banner": BANNER} for r, fs in sorted(dev.items())],
        "pending_even_with_a_gated_run": cfg["pending_even_with_a_gated_run"],
        "owner_blocked": cfg["owner_blocked"],
    }  # fmt: skip
