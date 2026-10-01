"""LLM seeding runner pieces (TRADEOFFS: LLM seeding; draw_v2). Pure, no model call.

The runner (`scripts/seed_run.py`) calls the model once per drawn chunk and
appends one raw record per call; everything after that is rebuilt offline from
the raw file with `outcome`.
"""

from __future__ import annotations

import json
import re

from eval.generate.seeding import (
    answer_flags,
    attach_scale,
    filter_question,
    mixed_signals,
    parse_response,
)

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
QUESTION_FOR = {"table": "factual", "synthesis": "interpretive"}


def drawn_order(draw: dict) -> list[dict]:
    """Every drawn chunk in manifest order: kind, ticker, stratum, then draw order."""
    out = []
    for kind, k in draw["kinds"].items():
        for ticker, strata in k["per_ticker"].items():
            for s in strata:
                for pos, cid in enumerate(s["drawn"]):
                    out.append({"chunk_id": cid, "kind": kind, "ticker": ticker,
                                "form": s["form"], "item_code": s["item_code"],
                                "position": pos})  # fmt: skip
    return out


def pending(order: list[dict], recorded: set[str]) -> list[dict]:
    """Drawn chunks with no recorded response: a chunk is called at most once."""
    return [d for d in order if d["chunk_id"] not in recorded]


def scrub(record: dict, home: str) -> tuple[dict, list[str]]:
    """Drop every field whose value holds an email address or the home path."""
    dropped = []
    out = {}
    for k, v in record.items():
        text = v if isinstance(v, str) else json.dumps(v)
        if EMAIL.search(text) or (home and home in text):
            dropped.append(k)
            continue
        out[k] = v
    out["scrubbed_fields"] = dropped
    return out, dropped


def outcome(record: dict, chunk: dict, kind: str, company_names: list[str]) -> dict:
    """What Stage 2 (key-free part) makes of one raw record.

    `chunk` has text (as sent), raw_text, unit_scale and span_scales. A table chunk
    yields its factual question, a prose chunk its interpretive one; the other
    question is never promoted.
    """
    if record.get("response") is None:
        return {"status": "dropped", "filter": "call_error", "reason": record.get("error")}
    qs, why = parse_response(record["response"])
    if qs is None:
        return {"status": "dropped", "filter": "parse", "reason": why}
    q = next(x for x in qs if x["kind"] == QUESTION_FOR[kind])
    drop = filter_question(q, chunk["text"], company_names, numeric=kind == "table")
    if drop:
        return {"status": "dropped", "filter": drop.filter, "reason": drop.reason,
                "sign_only": drop.sign_only, "question": q}  # fmt: skip
    flags: list[str] = []
    value = magnitude = None
    if kind == "table":
        mixed = mixed_signals(chunk["raw_text"], chunk["unit_scale"], chunk["span_scales"])
        value, flags = attach_scale(q["answer"], chunk["unit_scale"], mixed)
        paren = answer_flags(q["answer"])
        flags = paren + flags
        if paren:  # the sign is set at review (F-87); code keeps only the magnitude
            value, magnitude = None, abs(value)
    return {"status": "kept", "question": q, "flags": flags,
            "value": None if value is None else str(value),
            "magnitude": None if magnitude is None else str(magnitude)}  # fmt: skip
