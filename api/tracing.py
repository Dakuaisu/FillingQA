"""Tracing (PRD 14 Phase 5: LangFuse with cost). A no-op without keys.

One trace per `POST /query` and per eval item (callers open it with `trace()`),
spans for router, retrieval, rerank, generation and gate (`span()` in
api/pipeline.py). Model spans carry token counts, and cost from eval/pricing.yaml
when the backend is `anthropic_api`; on `claude_cli` the cost is "n/a (dev
backend)". Question and chunk text leave the process only when
`tracing.include_content` is true (default false).

Export: OTLP/HTTP JSON to LangFuse's `/api/public/otel/v1/traces` with
`langfuse.*` attributes (LangFuse docs, read 2026-10-02), basic auth from
LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY, host LANGFUSE_HOST. Without both keys
nothing is created or sent. Decisions in TRADEOFFS ("tracing").
"""

from __future__ import annotations

import base64
import json
import logging
import os
import secrets
import time
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field

import yaml

from api.config import CORPUS_FILE, REPO_ROOT

log = logging.getLogger(__name__)
DEV_COST = "n/a (dev backend)"
DEFAULT_HOST = "https://cloud.langfuse.com"


@dataclass
class Span:
    name: str
    kind: str = "span"  # langfuse.observation.type: span | generation
    span_id: str = field(default_factory=lambda: secrets.token_hex(8))
    parent_id: str | None = None
    start_ns: int = field(default_factory=time.time_ns)
    end_ns: int | None = None
    attrs: dict = field(default_factory=dict)

    def set(self, **attrs) -> None:
        self.attrs.update({k: v for k, v in attrs.items() if v is not None})

    def content(self, key: str, text: str | None) -> None:
        """Question or chunk text: recorded only when tracing.include_content is true."""
        if text is not None and include_content():
            self.attrs[key] = text

    def model_call(self, model: str | None, usage: dict | None, backend: str) -> None:
        """Token counts on every model span; cost from eval/pricing.yaml on the API backend."""
        from eval.metrics.cost import call_cost

        u = usage or {}
        details = {"input": u.get("input_tokens") or 0, "output": u.get("output_tokens") or 0,
                   "cache_read_input_tokens": u.get("cache_read_tokens") or 0,
                   "cache_creation_input_tokens": u.get("cache_creation_tokens") or 0}  # fmt: skip
        self.set(model=model, usage_details=details, backend=backend)
        if backend == "anthropic_api":
            cost, why = call_cost(model, usage, _prices())
            self.set(cost_details={"total": cost} if why is None else None, cost_note=why)
        else:
            self.set(cost_note=DEV_COST)


class _NullSpan(Span):
    def set(self, **attrs) -> None:
        pass

    def content(self, key: str, text: str | None) -> None:
        pass

    def model_call(self, model, usage, backend) -> None:
        pass


@dataclass
class Trace:
    name: str
    trace_id: str = field(default_factory=lambda: secrets.token_hex(16))
    spans: list[Span] = field(default_factory=list)


_trace: ContextVar[Trace | None] = ContextVar("trace", default=None)
_stack: ContextVar[tuple[str, ...]] = ContextVar("span_stack", default=())
_exporter = None
_exporter_set = False


def set_exporter(exporter) -> None:
    """Tests install a fake exporter; None restores the key-based default."""
    global _exporter, _exporter_set
    _exporter, _exporter_set = exporter, exporter is not None


def exporter():
    if _exporter_set:
        return _exporter
    pk, sk = os.environ.get("LANGFUSE_PUBLIC_KEY", ""), os.environ.get("LANGFUSE_SECRET_KEY", "")
    if not (pk.strip() and sk.strip()):
        return None
    return LangfuseExporter(os.environ.get("LANGFUSE_HOST", DEFAULT_HOST), pk.strip(), sk.strip())


def status() -> str:
    return "enabled" if exporter() is not None else "disabled"


def include_content(path=CORPUS_FILE) -> bool:
    cfg = yaml.safe_load(path.read_text(encoding="utf-8")).get("tracing") or {}
    return bool(cfg.get("include_content", False))


_PRICES = None


def _prices() -> dict:
    global _PRICES
    if _PRICES is None:
        doc = (REPO_ROOT / "eval" / "pricing.yaml").read_text(encoding="utf-8")
        _PRICES = yaml.safe_load(doc)["models"]
    return _PRICES


@contextmanager
def trace(name: str, **attrs):
    """One trace (a root span named `name`); exported when it ends. No-op without keys."""
    exp = exporter()
    if exp is None:
        yield None
        return
    t = Trace(name)
    root = Span(name)
    root.set(**attrs)
    t.spans.append(root)
    tok_t, tok_s = _trace.set(t), _stack.set((root.span_id,))
    try:
        yield root
    finally:
        root.end_ns = time.time_ns()
        _trace.reset(tok_t)
        _stack.reset(tok_s)
        try:
            exp.export(t)
        except Exception as e:  # tracing never breaks an answer
            log.warning("trace export failed: %s", e)


@contextmanager
def span(name: str, kind: str = "span", **attrs):
    t = _trace.get()
    if t is None:
        yield _NullSpan(name)
        return
    stack = _stack.get()
    s = Span(name, kind=kind, parent_id=stack[-1] if stack else None)
    s.set(**attrs)
    t.spans.append(s)
    tok = _stack.set((*stack, s.span_id))
    try:
        yield s
    finally:
        s.end_ns = time.time_ns()
        _stack.reset(tok)


def _value(v) -> dict:
    if isinstance(v, bool):
        return {"boolValue": v}
    if isinstance(v, int):
        return {"intValue": str(v)}
    if isinstance(v, float):
        return {"doubleValue": v}
    return {"stringValue": v if isinstance(v, str) else json.dumps(v)}


def otlp(t: Trace) -> dict:
    """The trace as an OTLP/HTTP JSON body with LangFuse attributes."""
    spans = []
    for i, s in enumerate(t.spans):
        a = {"langfuse.observation.type": s.kind}
        if i == 0:
            a["langfuse.trace.name"] = t.name
        for k, v in s.attrs.items():
            if k == "model":
                a["langfuse.observation.model.name"] = v
            elif k in ("usage_details", "cost_details"):
                a[f"langfuse.observation.{k}"] = json.dumps(v)
            elif k in ("question", "input"):
                a["langfuse.observation.input"] = v
            else:
                a[f"langfuse.observation.metadata.{k}"] = v
        attributes = [{"key": k, "value": _value(v)} for k, v in a.items()]
        parent = {"parentSpanId": s.parent_id} if s.parent_id else {}
        spans.append({"traceId": t.trace_id, "spanId": s.span_id, **parent, "name": s.name,
                      "kind": 1, "startTimeUnixNano": str(s.start_ns),
                      "endTimeUnixNano": str(s.end_ns or s.start_ns),
                      "attributes": attributes})  # fmt: skip
    resource = {"attributes": [{"key": "service.name", "value": {"stringValue": "filingqa"}}]}
    scope = {"scope": {"name": "filingqa"}, "spans": spans}
    return {"resourceSpans": [{"resource": resource, "scopeSpans": [scope]}]}


class LangfuseExporter:
    def __init__(self, host: str, public_key: str, secret_key: str):
        self.url = host.rstrip("/") + "/api/public/otel/v1/traces"
        token = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
        self.headers = {"Authorization": f"Basic {token}", "Content-Type": "application/json",
                        "x-langfuse-ingestion-version": "4"}  # fmt: skip

    def export(self, t: Trace) -> None:
        import httpx

        httpx.post(self.url, json=otlp(t), headers=self.headers, timeout=10).raise_for_status()
