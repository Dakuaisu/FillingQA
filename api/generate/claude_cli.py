"""Development generator: the `claude` CLI on the developer's Max subscription.

OWNER DECISION (TRADEOFFS, "Max subscription as dev generator"). Results are
development numbers only: never in the README, never a CI baseline, never
compared with `anthropic_api` runs. No temperature or max-token control (F-60).

The child runs in a fresh empty temp directory (so Claude Code loads no
CLAUDE.md/AGENTS.md) without ANTHROPIC_API_KEY in its environment (the shell key
is invalid and would override the Max login). `--bare` is never used: it accepts
only an API key.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass

TIMEOUT_S = 300


class CliError(RuntimeError):
    """The CLI failed, or reported an error in its JSON result."""


@dataclass(frozen=True)
class CliResult:
    text: str
    model: str  # the model actually served (`modelUsage` keys)
    input_tokens: int
    output_tokens: int


def build_command(prompt: str, model: str, system_prompt: str) -> list[str]:
    return [
        "claude", "-p", prompt,
        "--model", model,
        "--system-prompt", system_prompt,
        "--tools", "",
        "--strict-mcp-config",
        "--disable-slash-commands",
        "--setting-sources", "",
        "--no-session-persistence",
        "--output-format", "json",
    ]  # fmt: skip


def child_env(env: dict[str, str]) -> dict[str, str]:
    return {k: v for k, v in env.items() if k != "ANTHROPIC_API_KEY"}


def parse_output(stdout: str) -> CliResult:
    try:
        doc = json.loads(stdout)
    except json.JSONDecodeError as e:
        raise CliError(f"claude CLI output is not JSON: {e.msg}") from e
    if doc.get("is_error"):
        raise CliError(f"claude CLI error ({doc.get('subtype')}): {doc.get('result')!r}")
    served = sorted(doc.get("modelUsage") or {})
    if not served:
        raise CliError("claude CLI result has no modelUsage")
    usage = doc["usage"]
    return CliResult(
        text=doc["result"],
        model=",".join(served),
        input_tokens=usage["input_tokens"],
        output_tokens=usage["output_tokens"],
    )


def run(prompt: str, model: str, system_prompt: str) -> CliResult:
    with tempfile.TemporaryDirectory(prefix="filingqa-cli-") as cwd:
        proc = subprocess.run(
            build_command(prompt, model, system_prompt),
            cwd=cwd,
            env=child_env(dict(os.environ)),
            capture_output=True,
            text=True,
            timeout=TIMEOUT_S,
            check=False,
        )
    if proc.returncode != 0 and not proc.stdout.strip():
        raise CliError(f"claude CLI exited {proc.returncode}: {proc.stderr.strip()[:500]}")
    return parse_output(proc.stdout)
