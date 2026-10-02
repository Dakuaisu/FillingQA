"""Tracing (PRD 14 Phase 5): the span tree of one answer, token counts and cost on model
spans, and no question or chunk text leaving the process unless enabled. A fake
exporter captures the trace; the pipeline's models and database are stubbed."""

from __future__ import annotations

import json
from datetime import date
from types import SimpleNamespace

import pytest

import api.query.rerank as rerank_mod
import api.query.retrieve as retrieve_mod
from api import pipeline, tracing
from api.generate.generator import Answer

QUESTION = "What were Apple's inventories at fiscal 2024 year end? SECRET-QUESTION-TEXT"
CHUNK_TEXT = "| Inventories | 7,286 | SECRET-CHUNK-TEXT"
CID = "0000320193-24-000123:1.0:1.0"
ROUTE = {"intent": "lookup", "entities": [{"ticker": "AAPL", "company_name": "Apple"}],
         "fiscal_periods": ["FY2024"], "form_types": ["10-K"], "sub_queries": [],
         "confidence": 0.95}  # fmt: skip
DOC = {"answer_claims": [{"claim_id": "c1", "text": "Inventories were $7,286 million.",
                          "citations": [CID], "figure": None}],
       "sufficient_evidence": True, "abstain_reason": None}  # fmt: skip


class Capture:
    def __init__(self):
        self.traces = []

    def export(self, t):
        self.traces.append(t)


class Gate:
    def verify(self, question, claims, given, texts, threshold):
        pre = [{**c, "checks": {}} for c in claims]
        return {"claims_pre": pre, "claims_post": pre, "verify_verdict": "PASS"}


def make_ctx():
    lookup = {"tier": "tier_small", "k": 20, "top_n": 5, "sub_queries": 1}
    budgets = {"lookup": lookup, "unrouted": {**lookup, "k": 50, "top_n": 8}}
    index = SimpleNamespace(search=lambda q, k, allowed=None: [(CID, 1.0)])
    return SimpleNamespace(
        companies={"AAPL": "Apple"}, router={"tier": "tier_small", "budgets": budgets},
        rcfg={"metadata_filter": True, "filter_confidence_min": 0.6, "rrf_k": 60,
              "weights": {"dense": 1, "sparse": 1}, "dense_search": "exact"},
        rrcfg={"timeout_ms": 800, "score_floor": 0.3},
        chunk_meta=[(CID, "AAPL", 2024, None, "10-K")],
        period_ends=[("AAPL", date(2024, 9, 28), 2024, None)],
        model=None, emb=None, reranker=None, gate=Gate(), index=index,
    )  # fmt: skip


def run(monkeypatch, backend: str, include: bool):
    def fake_call(prompt_or_chunks, question, gen, tier):
        if question is None:
            return Answer(json.dumps(ROUTE), "claude-haiku-4-5-20251001", 120, 30, backend)
        return Answer("Inventories were $7,286 million.", "claude-haiku-4-5-20251001", 900, 60,
                      backend, structured=DOC)  # fmt: skip

    monkeypatch.setattr(pipeline, "call_model", fake_call)
    monkeypatch.setattr(pipeline, "texts_for", lambda conn, ids: {c: CHUNK_TEXT for c in ids})
    monkeypatch.setattr(retrieve_mod, "embed_question", lambda m, e, q: "[0]")
    monkeypatch.setattr(retrieve_mod, "dense_filtered_top_k", lambda conn, v, k, allowed: [CID])
    monkeypatch.setattr(rerank_mod, "rerank", lambda m, q, pairs: ([(CID, 0.9)], 0.1))
    monkeypatch.setattr(tracing, "include_content", lambda path=None: include)
    cap = Capture()
    tracing.set_exporter(cap)
    try:
        with tracing.trace("query") as root:
            root.content("question", QUESTION)
            gen = {
                "backend": backend,
                "tier_small": "claude-haiku-4-5-20251001",
                "structured": True,
            }
            r = pipeline.answer_question(None, make_ctx(), QUESTION, gen, {"nli_threshold": 0.5})
    finally:
        tracing.set_exporter(None)
    return r, cap.traces[0]


def test_one_trace_with_router_retrieval_rerank_generation_and_gate_spans(monkeypatch):
    r, t = run(monkeypatch, "claude_cli", include=False)
    assert r["verdict"] == "PASS"
    root, *children = t.spans
    assert root.name == "query" and root.parent_id is None
    assert [s.name for s in children] == ["router", "retrieval", "rerank", "generation", "gate"]
    assert all(s.parent_id == root.span_id for s in children)
    model_spans = [s for s in children if s.kind == "generation"]
    assert [s.name for s in model_spans] == ["router", "generation"]
    assert model_spans[0].attrs["usage_details"]["input"] == 120
    assert model_spans[1].attrs["usage_details"]["output"] == 60
    assert all(s.attrs["cost_note"] == "n/a (dev backend)" for s in model_spans)
    assert children[4].attrs["verdict"] == "PASS"


def test_no_question_or_chunk_text_leaves_the_process_by_default(monkeypatch):
    _, t = run(monkeypatch, "claude_cli", include=False)
    body = json.dumps(tracing.otlp(t))
    assert "SECRET-QUESTION-TEXT" not in body and "SECRET-CHUNK-TEXT" not in body
    _, t = run(monkeypatch, "claude_cli", include=True)
    assert "SECRET-QUESTION-TEXT" in json.dumps(tracing.otlp(t))


def test_api_backend_spans_carry_cost_from_the_pricing_file(monkeypatch):
    _, t = run(monkeypatch, "anthropic_api", include=False)
    gen = next(s for s in t.spans if s.name == "generation")
    # 900 input at $1/M + 60 output at $5/M for claude-haiku-4-5-20251001 (eval/pricing.yaml)
    assert gen.attrs["cost_details"]["total"] == pytest.approx((900 * 1.0 + 60 * 5.0) / 1e6)
    attrs = {a["key"] for s in tracing.otlp(t)["resourceSpans"][0]["scopeSpans"][0]["spans"]
             for a in s["attributes"]}  # fmt: skip
    assert {"langfuse.observation.cost_details", "langfuse.observation.usage_details",
            "langfuse.observation.model.name", "langfuse.trace.name"} <= attrs  # fmt: skip


def test_without_keys_nothing_is_created_and_health_says_disabled(monkeypatch):
    monkeypatch.delenv("LANGFUSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("LANGFUSE_SECRET_KEY", raising=False)
    assert tracing.exporter() is None and tracing.status() == "disabled"
    with tracing.trace("query") as root:
        assert root is None
        with tracing.span("router") as s:
            s.set(x=1)  # a no-op span
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk")
    assert tracing.status() == "enabled"
