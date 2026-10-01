"""`make eval` (Phase 3 exit, PRD 14): freeze check, then the runner with --run."""

from __future__ import annotations

import subprocess

from api.config import REPO_ROOT


def test_make_eval_checks_the_freeze_then_runs_the_eval():
    out = subprocess.run(["make", "-n", "eval"], cwd=REPO_ROOT, capture_output=True,
                         text=True, check=True).stdout.splitlines()  # fmt: skip
    assert out == ["python -m scripts.verify_freeze", "python -m scripts.eval_run --run"]
