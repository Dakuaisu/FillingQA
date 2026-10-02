"""F-144: --report must not rewrite a run's files."""

from __future__ import annotations

import json

from scripts import eval_run


def test_rebuild_report_leaves_run_files_byte_identical(tmp_path, monkeypatch):
    run_id = "abc123def456"
    meta = {"run_id": run_id, "k": 10, "item_order": ["x1"], "backend": "claude_cli"}
    files = {
        f"{run_id}.meta.json": json.dumps(meta, indent=1) + "\n",
        f"{run_id}.results.jsonl": json.dumps({"item_id": "x1"}) + "\n",
        f"{run_id}.json": '{\n "older": "report"\n}\n',
    }
    for name, text in files.items():
        (tmp_path / name).write_text(text, encoding="utf-8")
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    monkeypatch.setattr(eval_run, "build_report", lambda *a: {"newer": "fields", "k": a[3]})

    report = eval_run.rebuild_report(tmp_path, run_id, {"x1": {}}, {"nli_threshold": None})

    assert report == {"newer": "fields", "k": 10}
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before
