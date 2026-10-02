"""Structured, citation-carrying answers (PRD 7.4).

The shape is enforced by the backend, not requested in prose: `claude_cli` with
`--json-schema` (the CLI answers through a forced tool call and returns
`structured_output`), `anthropic_api` with a forced tool whose input_schema is
SCHEMA. `contract_violations` records where an answer breaks the contract beyond
what a schema can say (a citation to a chunk it was not given, a number with no
figure object); nothing is repaired or dropped here, that is the verifier's job
(PRD 7.5).
"""

from __future__ import annotations

import re

UNITS = ("ones", "thousands", "millions", "billions", "trillions", "percent")

FIGURE = {
    "type": ["object", "null"],
    "properties": {
        "value": {"type": "number"},
        "unit": {"type": "string", "enum": list(UNITS)},
        "currency": {"type": ["string", "null"]},
        "period": {"type": "string"},
        "concept": {"type": ["string", "null"]},
    },
    "required": ["value", "unit", "currency", "period", "concept"],
    "additionalProperties": False,
}

SCHEMA = {
    "type": "object",
    "properties": {
        "answer_claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim_id": {"type": "string"},
                    "text": {"type": "string"},
                    "citations": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                    "figure": FIGURE,
                },
                "required": ["claim_id", "text", "citations", "figure"],
                "additionalProperties": False,
            },
        },
        "sufficient_evidence": {"type": "boolean"},
        "abstain_reason": {"type": ["string", "null"]},
    },
    "required": ["answer_claims", "sufficient_evidence", "abstain_reason"],
    "additionalProperties": False,
}

TOOL_NAME = "answer"

SYSTEM_PROMPT = """You answer questions about SEC filings using ONLY the numbered evidence
chunks provided. You do not use outside knowledge about these companies.

Rules:
1. Decompose your answer into atomic claims. One fact per claim.
2. Every claim MUST cite at least one chunk_id that directly supports it.
3. Never state a figure whose exact value does not appear in a cited chunk.
4. Always state the fiscal period and unit scale for every figure
   (e.g. "$7,286 million for fiscal 2024"). Unit scale appears in the
   table context line — use it.
5. If the evidence does not support an answer, set sufficient_evidence
   to false and explain what is missing. Do not guess. Do not approximate.
6. If chunks concern a different company than the question asks about,
   treat the evidence as insufficient.
7. Never give investment advice, forecasts, or recommendations.

Every claim that contains a number carries a `figure` object (value as printed in
the chunk, unit scale, currency, fiscal period, concept); other claims set figure
to null."""

NUMBER = re.compile(r"\d")


def render(question: str, chunks: list[tuple[str, str]]) -> str:
    """The user turn: evidence chunks by chunk_id, then the question."""
    body = "\n\n".join(f"[chunk_id: {cid}]\n{text}" for cid, text in chunks)
    return f"Evidence chunks:\n\n{body}\n\nQuestion: {question}"


def contract_violations(doc: dict, given: list[str]) -> list[str]:
    """Breaches the schema cannot express, one string each."""
    out = []
    claims = doc["answer_claims"]
    ids = [c["claim_id"] for c in claims]
    if len(set(ids)) != len(ids):
        out.append("duplicate claim_id")
    if doc["sufficient_evidence"] and not claims:
        out.append("sufficient_evidence true with no claims")
    if not doc["sufficient_evidence"] and not (doc["abstain_reason"] or "").strip():
        out.append("insufficient evidence with no abstain_reason")
    allowed = set(given)
    for c in claims:
        bad = [x for x in c["citations"] if x not in allowed]
        if bad:
            out.append(f"{c['claim_id']}: cites chunks not given {bad}")
        if NUMBER.search(c["text"]) and not c["figure"]:
            out.append(f"{c['claim_id']}: number in text without a figure object")
    return out


def answer_text(doc: dict) -> str:
    """The claims joined as prose, for the free-text numeric fallback and display."""
    if not doc["sufficient_evidence"] and not doc["answer_claims"]:
        return ""
    return " ".join(c["text"].strip() for c in doc["answer_claims"])
