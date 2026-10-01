"""Unstructured generation for the Phase 2 naive baseline (PRD 14).

Plain prompt, free-text answer. None of PRD 7.4 -- no structured output, no
claims, no citation contract. Quality is irrelevant by the Phase 2 exit; the
baseline exists to be the number later configs beat.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from api.config import ConfigError, load_env
from api.query.retrieve import Retrieved

BACKENDS = ("claude_cli", "anthropic_api")


@dataclass
class Answer:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    backend: str = "anthropic_api"


def build_prompt(question: str, chunks: list[Retrieved]) -> str:
    context = "\n\n".join(f"[chunk {c.chunk_id}]\n{c.text}" for c in chunks)
    return f"Question: {question}\n\nExcerpts from SEC filings:\n\n{context}\n\nAnswer:"


def generate(question: str, chunks: list[Retrieved], cfg: dict, tier: str) -> Answer:
    """Dispatch on `generation.backend`. `claude_cli` answers are development
    numbers only (TRADEOFFS, OWNER DECISION - Max subscription as dev generator)."""
    backend = cfg["backend"]
    if backend == "claude_cli":
        from api.generate import claude_cli

        r = claude_cli.run(build_prompt(question, chunks), cfg[tier], cfg["cli_system_prompt"])
        return Answer(r.text, r.model, r.input_tokens, r.output_tokens, backend)
    if backend == "anthropic_api":
        return generate_api(question, chunks, cfg, tier)
    raise ConfigError(f"generation.backend {backend!r} not in {BACKENDS}")


def generate_api(question: str, chunks: list[Retrieved], cfg: dict, tier: str) -> Answer:
    load_env()
    if not os.environ.get("ANTHROPIC_API_KEY", "").strip():
        raise ConfigError(
            "ANTHROPIC_API_KEY is not set (environment or .env). The baseline's "
            "generation call needs it; retrieval does not."
        )
    import anthropic  # here, so retrieval and tests never need the client

    model = cfg[tier]
    response = anthropic.Anthropic().messages.create(
        model=model,
        max_tokens=cfg["max_tokens"],
        messages=[{"role": "user", "content": build_prompt(question, chunks)}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return Answer(text, response.model, response.usage.input_tokens, response.usage.output_tokens)
