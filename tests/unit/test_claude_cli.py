"""The claude_cli dev backend without a live call: command, environment, parsing.

tests/fixtures/claude_cli_response.json is one real response of the command
below (`claude` 2.1.286, prompt "Reply with the single word: ready").
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from api.generate.claude_cli import CliError, build_command, child_env, parse_output

RAW = (Path(__file__).resolve().parent.parent / "fixtures" / "claude_cli_response.json").read_text(
    encoding="utf-8"
)


def test_command_is_exactly_the_verified_one():
    assert build_command("P", "claude-sonnet-5-5", "S") == [
        "claude", "-p", "P", "--model", "claude-sonnet-5-5", "--system-prompt", "S",
        "--tools", "", "--strict-mcp-config", "--disable-slash-commands",
        "--setting-sources", "", "--no-session-persistence", "--output-format", "json",
    ]  # fmt: skip
    assert "--bare" not in build_command("P", "m", "S")


def test_child_env_drops_the_api_key_only():
    env = child_env({"ANTHROPIC_API_KEY": "bad", "HOME": "/h", "PATH": "/p"})
    assert env == {"HOME": "/h", "PATH": "/p"}


def test_parses_the_recorded_response():
    r = parse_output(RAW)
    assert (r.text, r.model) == ("ready", "claude-haiku-4-5-20251001")
    assert (r.input_tokens, r.output_tokens) == (465, 41)
    assert (r.cache_read_tokens, r.cache_creation_tokens) == (0, 0)


def test_is_error_raises():
    # No real error response is recorded; the real one with is_error set.
    doc = {**json.loads(RAW), "is_error": True, "subtype": "error_during_execution"}
    with pytest.raises(CliError, match="error_during_execution"):
        parse_output(json.dumps(doc))
    with pytest.raises(CliError, match="not JSON"):
        parse_output("Invalid API key")
    with pytest.raises(CliError, match="modelUsage"):
        parse_output(json.dumps({**json.loads(RAW), "modelUsage": {}}))


@pytest.mark.parametrize(
    ("change", "match"),
    [(lambda d: [d], "not an object"),
     (lambda d: {k: v for k, v in d.items() if k != "usage"}, "usage"),
     (lambda d: {**d, "usage": {"input_tokens": "1", "output_tokens": 2}}, "usage"),
     (lambda d: {k: v for k, v in d.items() if k != "result"}, "missing or empty"),
     (lambda d: {**d, "result": 7}, "missing or empty"),
     (lambda d: {**d, "result": "  "}, "missing or empty")],
)  # fmt: skip
def test_malformed_results_raise_cli_error(change, match):
    # The recorded response, each time with one part made malformed.
    with pytest.raises(CliError, match=match):
        parse_output(json.dumps(change(json.loads(RAW))))
