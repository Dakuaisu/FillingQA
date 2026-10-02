"""GET /metrics (dashboard data): development runs never contribute a value, and the
README status section agrees with the payload. Inline run files for the first."""

from __future__ import annotations

import json
import re
import shutil

import yaml

from api import metrics
from api.config import REPO_ROOT

SENTINEL = 0.123457


def _write(path, doc):
    path.write_text(json.dumps(doc), encoding="utf-8")


def _report(dev: bool):
    col = {"sufficiency@10": SENTINEL if dev else 0.9, "generation": {"status": "ok",
           "faithfulness_pre": SENTINEL if dev else 0.8}, "abstention": {}}  # fmt: skip
    return {"backend": "claude_cli" if dev else "anthropic_api", "development_run": dev,
            "columns": {"aggregate": col, "xbrl_auto": col}}  # fmt: skip


def test_development_runs_are_ids_only_and_never_values(tmp_path):
    runs = tmp_path / "runs"
    runs.mkdir()
    _write(runs / "aaaaaaaaaaaa.meta.json", {"backend": "claude_cli"})
    _write(runs / "aaaaaaaaaaaa.json", _report(dev=True))
    _write(runs / "bbbbbbbbbbbb.filter.json", {"report": {"backend": "claude_cli",
           "columns": {"filtered": {"aggregate": {"sufficiency@10": SENTINEL}}}}})  # fmt: skip
    _write(runs / "cccccccccccc.smoke.json", {"ok": True, "meta": {"backend": "claude_cli"}})
    shutil.copy(REPO_ROOT / "eval" / "runs" / "5b3c3ac13e5e.retrieval.json", runs)
    payload = metrics.build(runs=runs)
    text = json.dumps(payload)
    assert str(SENTINEL) not in text
    assert [d["run_id"] for d in payload["development_runs"]] == [
        "aaaaaaaaaaaa", "bbbbbbbbbbbb", "cccccccccccc"]  # fmt: skip
    assert all(d["banner"] == metrics.BANNER for d in payload["development_runs"])
    assert payload["gate"]["run_id"] is None and not payload["gate"]["passed"]
    assert payload["gate"]["reason"] == "no gated run exists (F-59)"


def test_a_gated_run_feeds_the_gate_by_the_same_rule(tmp_path):
    runs = tmp_path / "runs"
    runs.mkdir()
    _write(runs / "dddddddddddd.meta.json", {"backend": "anthropic_api"})
    _write(runs / "dddddddddddd.json", _report(dev=False))
    _write(runs / "eeeeeeeeeeee.meta.json", {"backend": "claude_cli"})
    _write(runs / "eeeeeeeeeeee.json", _report(dev=True))
    payload = metrics.build(runs=runs)
    assert payload["gate"]["run_id"] == "dddddddddddd" and payload["gated_runs"] == ["dddddddddddd"]
    suff = next(r for r in payload["gate"]["rows"]
                if r["metric"] == "sufficiency_at_10" and r["scope"] == "aggregate")  # fmt: skip
    assert suff["value"] == 0.9 and str(SENTINEL) not in json.dumps(payload)


def cfg_pending():
    cfg = yaml.safe_load((REPO_ROOT / "eval" / "dashboard.yaml").read_text(encoding="utf-8"))
    return cfg["pending_even_with_a_gated_run"]


def test_readme_status_section_agrees_with_metrics():
    """If the README and the dashboard ever disagree, both are wrong."""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    payload = metrics.build()
    cur = next(r for r in payload["retrieval_runs"] if r["current"])
    assert f"`{cur['run_id']}`" in readme
    section = readme.split("### Where the gate stands", 1)[1].split("### What waits", 1)[0]
    for src in ("aggregate", "xbrl_auto", "llm_seeded"):
        v, t = cur["sufficiency_at_10"][src]["value"], cur["sufficiency_at_10"][src]["threshold"]
        assert f"{v:.3f}" in section and f"{t:.2f}" in section, (src, v, t)
    assert "Config\n  3" in section or "Config 3" in section
    assert "**No gated run exists.**" in section and payload["gate"]["reason"].startswith(
        "no gated run exists"
    )
    flat = " ".join(section.split())
    for x in cfg_pending():
        line = f"{x['metrics']} ({x['reason']}, {', '.join(x['findings'])})"
        assert line in flat, line
    rows = re.findall(r"^\| (.+?) \| (F-[\d, F-]+) \|$", readme, re.M)
    cfg = yaml.safe_load((REPO_ROOT / "eval" / "dashboard.yaml").read_text(encoding="utf-8"))
    assert rows == [(o["item"], ", ".join(o["findings"])) for o in cfg["owner_blocked"]]
    assert [o["item"] for o in payload["owner_blocked"]] == [
        o["item"] for o in cfg["owner_blocked"]
    ]
