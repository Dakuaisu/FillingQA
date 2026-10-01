"""Baseline generation path, without the network: prompt shape and the loud
failure when no key is configured."""

from __future__ import annotations

import pytest

from api import config
from api.config import ConfigError, generation
from api.generate.generator import build_prompt, generate
from api.query.retrieve import Retrieved

CHUNKS = [
    Retrieved(
        "0000320193-25-000079:456.0:456.0", 0.197, "[Apple Inc. (AAPL) | 10-K | FY2025]\nrow"
    ),
    Retrieved(
        "0000320193-25-000079:305.0:318.0", 0.193, "[Apple Inc. (AAPL) | 10-K | FY2025]\ntext"
    ),
]


def test_prompt_carries_question_and_every_chunk_with_its_id():
    prompt = build_prompt("What were total net sales?", CHUNKS)
    assert prompt.startswith("Question: What were total net sales?")
    for c in CHUNKS:
        assert f"[chunk {c.chunk_id}]\n{c.text}" in prompt


def test_missing_key_fails_at_the_call_site(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "ENV_FILE", tmp_path / "absent.env")
    monkeypatch.setattr(config, "_loaded", False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY is not set"):
        generate("q", CHUNKS, generation(), "tier_small")


def test_generation_config_has_what_the_call_reads():
    cfg = generation()
    assert cfg["tier_small"] and cfg["tier_large"]
    assert cfg["max_tokens"] > 0
    assert "temperature" not in cfg  # not sendable at the pinned SDK (F-60)
