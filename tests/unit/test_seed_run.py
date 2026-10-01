"""The seeding runner's halt path, without a model call: `complete` is patched."""

from __future__ import annotations

import json

import pytest

from api.config import generation
from api.generate.claude_cli import CliError, TransportError
from eval.generate.seed_runner import pending
from scripts import seed_run
from tests.unit.test_seed_runner import COST_CF

DRAWN = [{"chunk_id": COST_CF["chunk_id"], "kind": "table", "ticker": "COST",
          "form": "10-Q", "item_code": "I.1", "position": 0}]  # fmt: skip
SHAS = {"prompt_sha256": "p", "draw_sha256": "d"}


def run_once(tmp_path, monkeypatch, exc):
    calls = []

    def fake_complete(prompt, cfg, tier):
        calls.append(prompt)
        raise exc

    monkeypatch.setattr(seed_run, "complete", fake_complete)
    raw, errors = tmp_path / "raw.jsonl", tmp_path / "errors.jsonl"
    template = seed_run.PROMPT.read_text(encoding="utf-8")
    code = seed_run.run_pending(
        DRAWN, lambda cid: COST_CF,
        lambda chunk, d: seed_run.call(chunk, d, generation(), template, SHAS, "test"),
        raw, errors,
    )  # fmt: skip
    return code, calls, raw, errors


@pytest.mark.parametrize(
    ("exc", "attempts"),
    [(CliError("claude CLI error (error_during_execution): 'usage limit'"), 1),
     (TransportError("claude CLI timed out after 300s"), 3)],
)  # fmt: skip
def test_a_call_without_output_halts_and_leaves_the_chunk_pending(
    tmp_path, monkeypatch, exc, attempts
):
    code, calls, raw, errors = run_once(tmp_path, monkeypatch, exc)
    assert code == 1 and len(calls) == attempts
    assert not raw.exists()  # the raw file is unchanged
    (err,) = [json.loads(line) for line in errors.read_text().splitlines()]
    assert err["chunk_id"] == COST_CF["chunk_id"] and len(err["attempts"]) == attempts
    assert all(a["called_at"] and str(exc) in a["error"] for a in err["attempts"])
    assert pending(DRAWN, seed_run.recorded(raw)) == DRAWN


def test_a_chunk_that_halted_three_runs_stops_the_run(tmp_path, monkeypatch):
    for _ in range(3):
        code, *_ = run_once(tmp_path, monkeypatch, CliError("x"))
        assert code == 1
    code, calls, _, errors = run_once(tmp_path, monkeypatch, CliError("x"))
    assert code == 2 and calls == []  # refused, not called and not skipped
    assert len(errors.read_text().splitlines()) == 3


def test_a_response_is_recorded_with_called_at(tmp_path, monkeypatch):
    from api.generate.generator import Answer

    monkeypatch.setattr(seed_run, "complete", lambda p, c, t: Answer("{}", "m", 1, 2, "claude_cli"))
    raw, errors = tmp_path / "raw.jsonl", tmp_path / "errors.jsonl"
    template = seed_run.PROMPT.read_text(encoding="utf-8")
    code = seed_run.run_pending(
        DRAWN, lambda cid: COST_CF,
        lambda chunk, d: seed_run.call(chunk, d, generation(), template, SHAS, "test"),
        raw, errors,
    )  # fmt: skip
    (rec,) = [json.loads(line) for line in raw.read_text().splitlines()]
    assert code == 0 and not errors.exists()
    assert rec["called_at"].endswith("+00:00") and rec["response"] == "{}"
    assert rec["model_served"] == "m" and rec["draw_sha256"] == "d"
