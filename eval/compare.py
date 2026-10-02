"""The CI gate (PRD 11.5): a report against eval/thresholds.yaml and a baseline.

python -m eval.compare --report build/eval_fast.json \
    --baseline eval/baselines/main_fast.json [--thresholds eval/thresholds.yaml] [--md out.md]

`eval/thresholds.yaml` is the only source of threshold numbers (F-07); this file
reads it as it is. Rows (TRADEOFFS, CI gate): `absolute_minimums` and `maximums`
on the aggregate and on the handwritten slice (`by_source.handwritten` overrides
for that slice), the other `by_source` slices on their own keys, and
`regression_tolerance` on the aggregate against a baseline drawn from the same
subset (F-12). A metric that is pending, not measured or missing fails: a gate
that cannot evaluate a gated metric does not pass. A development-backend report
(claude_cli) never passes. Exit status 1 on any failure.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

from api.config import REPO_ROOT

NOT_IN_REPORT = {
    "answer_correctness": "pending: judge answer correctness (F-105)",
    "natural_phrasing_gap": "pending: hand-written natural-phrasing items (F-103)",
    "cost_per_query": "pending: cost per query not measured (F-134)",
}


def _gen(key):
    return lambda c: (c.get("generation") or {}).get(key, (c.get("generation") or {}).get("status"))


def _abst(key):
    return lambda c: (c.get("abstention") or {}).get(key)


METRICS = {
    "sufficiency_at_10": lambda c: c.get("sufficiency@10"),
    "faithfulness_pre": _gen("faithfulness_pre"),
    "claim_retention": _gen("claim_retention"),
    "citation_coverage": _gen("citation_coverage"),
    "xbrl_contradiction": _gen("xbrl_contradiction_rate"),
    "false_answer_rate": _abst("false_answer_rate"),
    "over_abstention_rate": _abst("over_abstention_rate"),
}


def value(report: dict | None, scope: str, metric: str):
    """(number, None) or (None, why it cannot be evaluated)."""
    if metric in NOT_IN_REPORT:
        return None, NOT_IN_REPORT[metric]
    if report is None:
        return None, "pending: no baseline report (F-59)"
    col = report["columns"].get(scope)
    if col is None:
        why = (
            "hand-written items not yet authored (F-103)" if scope == "handwritten" else "no items"
        )
        return None, f"pending: {scope} slice empty, {why}"
    if metric not in METRICS:
        return None, f"unknown metric {metric!r}"
    v = METRICS[metric](col)
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        if isinstance(v, str) and v.startswith("pending"):
            return None, v
        return None, f"pending: {v if isinstance(v, str) else 'not measurable on this report'}"
    return float(v), None


def _row(metric, scope, rule, threshold, v, why, ok, base=None) -> dict:
    status = "pending" if why and why.startswith("pending") else ("pass" if ok else "fail")
    return {"metric": metric, "scope": scope, "rule": rule, "threshold": threshold, "value": v,
            "baseline": base, "status": status, "why": why}  # fmt: skip


def _check(report, metric, scope, rule, t) -> dict:
    v, why = value(report, scope, metric)
    ok = why is None and (v >= t if rule == "min" else v <= t)
    return _row(metric, scope, rule, t, v, why, ok)


def rows(report: dict, thresholds: dict, baseline: dict | None) -> list[dict]:
    """One row per gated (metric, scope); see the module docstring."""
    minimums = thresholds.get("absolute_minimums") or {}
    maximums = thresholds.get("maximums") or {}
    by_source = thresholds.get("by_source") or {}
    hand = by_source.get("handwritten") or {}
    out = []
    for rule, table in (("min", minimums), ("max", maximums)):
        for metric, t in table.items():
            out.append(_check(report, metric, "aggregate", rule, t))
            out.append(_check(report, metric, "handwritten", rule, hand.get(metric, t)))
    out += [
        _check(report, m, "handwritten", "min", t) for m, t in hand.items() if m not in minimums
    ]
    for scope, table in by_source.items():
        if scope != "handwritten":
            out += [_check(report, m, scope, "min", t) for m, t in (table or {}).items()]
    same_subset = baseline is not None and (baseline.get("subset") or {}).get("sha256") == (
        report.get("subset") or {}).get("sha256")  # fmt: skip
    for metric, tol in (thresholds.get("regression_tolerance") or {}).items():
        v, why = value(report, "aggregate", metric)
        b, bwhy = value(baseline, "aggregate", metric)
        why = why or bwhy
        if why is None and not same_subset:
            why = "baseline is not from the same subset (F-12)"
        ok = why is None and ((v - b) >= tol if tol < 0 else (v - b) <= tol)
        out.append(_row(metric, "aggregate", f"delta {tol:+}", tol, v, why, ok, b))
    if report.get("development_run"):
        out.append(_row("backend", "run", "not a development backend", None,
                        report.get("backend"), "development run (claude_cli) cannot pass (F-59)",
                        False))  # fmt: skip
    return out


def passed(table: list[dict]) -> bool:
    return all(r["status"] == "pass" for r in table)


def _f(v) -> str:
    return "-" if v is None else f"{v:.3f}" if isinstance(v, float) else str(v)


def format_table(table: list[dict], markdown: bool = False) -> str:
    head = ["metric", "scope", "rule", "threshold", "value", "baseline", "status", "why"]
    cells = [[r["metric"], r["scope"], r["rule"], _f(r["threshold"]), _f(r["value"]),
              _f(r["baseline"]), r["status"].upper(), r["why"] or ""] for r in table]  # fmt: skip
    verdict = "GATE PASSED" if passed(table) else "GATE FAILED"
    if markdown:
        lines = [f"### Eval gate: {verdict}", "", "| " + " | ".join(head) + " |",
                 "|" + "---|" * len(head)]  # fmt: skip
        lines += ["| " + " | ".join(c) + " |" for c in cells]
        return "\n".join(lines) + "\n"
    widths = [max(len(head[i]), *(len(c[i]) for c in cells)) for i in range(len(head) - 1)]

    def fmt(row):
        return "  ".join(x.ljust(w) for x, w in zip(row, widths, strict=False)) + "  " + row[-1]

    return "\n".join([verdict, fmt(head), *(fmt(c) for c in cells)])


def arg(name: str, default: str | None = None) -> str | None:
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main() -> None:
    report = json.loads(Path(arg("--report")).read_text(encoding="utf-8"))
    thresholds = yaml.safe_load(
        (REPO_ROOT / arg("--thresholds", "eval/thresholds.yaml")).read_text(encoding="utf-8")
    )
    bpath = Path(arg("--baseline")) if arg("--baseline") else None
    baseline = json.loads(bpath.read_text(encoding="utf-8")) if bpath and bpath.exists() else None
    table = rows(report, thresholds, baseline)
    print(format_table(table))
    if arg("--md"):
        Path(arg("--md")).write_text(format_table(table, markdown=True), encoding="utf-8")
    sys.exit(0 if passed(table) else 1)


if __name__ == "__main__":
    main()
