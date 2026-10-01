"""Seeding runner pieces: order, resume, scrub, and outcome on real chunk text.

Chunks: tests/fixtures/seed_chunks.json. Responses are inline strings here.
"""

from __future__ import annotations

import json
from pathlib import Path

from eval.generate.seed_runner import drawn_order, outcome, pending, scrub

DOC = json.loads(
    (Path(__file__).resolve().parent.parent / "fixtures" / "seed_chunks.json").read_text(
        encoding="utf-8"
    )
)
CH = {c["chunk_id"]: c for c in DOC["chunks"]}
COST_CF = CH["0000909832-25-000015:68.1:68.1"]
PFE_PROSE = CH["0000078003-24-000039:343.0:344.0"]
JPM_EPS = CH["0000019617-24-000326:1892.0:1892.0"]
NAMES = ["Costco", "COST", "Pfizer", "PFE", "JPMorgan Chase", "JPM"]
Q_CASH = (
    "What was Costco's cash and cash equivalents at the end of the 24 weeks ended "
    "February 16, 2025?"
)
Q_FX = "What was Costco's effect of exchange rates on cash in the first half of fiscal 2025?"
FX_ROW = "| EFFECT OF EXCHANGE RATE CHANGES ON CASH AND CASH EQUIVALENTS | (117) | 15 |"
Q_EPS = (
    "What was JPMorgan Chase's diluted net income per share for the three months ended "
    "March 31, 2024?"
)


def response(factual: dict, interpretive: dict) -> str:
    return json.dumps({"questions": [{"kind": "factual", **factual},
                                     {"kind": "interpretive", **interpretive}]})  # fmt: skip


def test_order_and_resume():
    draw = {"kinds": {"table": {"per_ticker": {"COST": [
        {"form": "10-Q", "item_code": "I.1", "drawn": ["a", "b"]}]}}}}  # fmt: skip
    order = drawn_order(draw)
    assert [(d["chunk_id"], d["position"]) for d in order] == [("a", 0), ("b", 1)]
    assert [d["chunk_id"] for d in pending(order, {"a"})] == ["b"]


def test_scrub_drops_fields_with_an_email_or_the_home_path():
    rec = {"chunk_id": "x", "response": "ok", "error": "at /Users/someone/tmp",
           "note": "mail a.b@example.com"}  # fmt: skip
    clean, dropped = scrub(rec, "/Users/someone")
    assert dropped == ["error", "note"] and clean["response"] == "ok"
    assert clean["scrubbed_fields"] == ["error", "note"]


def test_table_outcome_keeps_the_factual_question_with_scale():
    r = {"response": response(
        {"question": Q_CASH, "answer": "$12,356",
         "supporting_quote": "| CASH AND CASH EQUIVALENTS END OF PERIOD | $12,356 | $9,095 |"},
        {"question": "Why did Costco's cash change?", "answer": "x", "supporting_quote": "y"},
    )}  # fmt: skip
    out = outcome(r, COST_CF, "table", NAMES)
    assert out["status"] == "kept" and out["question"]["kind"] == "factual"
    assert out["value"] == "12356000000" and out["flags"] == []


def test_table_outcome_flags_parentheses_and_mixed_scale():
    r = {"response": response(
        {"question": Q_FX, "answer": "(117)", "supporting_quote": FX_ROW},
        {"question": "q", "answer": "a", "supporting_quote": "s"},
    )}  # fmt: skip
    out = outcome(r, COST_CF, "table", NAMES)
    assert out["status"] == "kept" and out["flags"][0].startswith("parenthesized")
    assert (out["value"], out["magnitude"]) == (None, "117000000")  # sign left to review
    eps = {"response": response(
        {"question": Q_EPS, "answer": "$4.44",
         "supporting_quote": "| Net income per share | $4.44 | $4.10 |"},
        {"question": "q", "answer": "a", "supporting_quote": "s"},
    )}  # fmt: skip
    out = outcome(eps, JPM_EPS, "table", NAMES)
    assert out["value"] == "4.44" and any("mixed table" in f for f in out["flags"])


def test_prose_outcome_uses_the_interpretive_question_and_drops_on_filters():
    quote = (
        "While manufacturing has resumed, the supply of medicines impacted by the tornado "
        "is expected to be affected through 2024."
    )
    good = {"response": response(
        {"question": "q", "answer": "1", "supporting_quote": "nowhere"},
        {"question": "How did Pfizer expect the July 2023 tornado to affect supply in 2024?",
         "answer": "Affected through 2024.", "supporting_quote": quote},
    )}  # fmt: skip
    out = outcome(good, PFE_PROSE, "synthesis", NAMES)
    assert out["status"] == "kept" and out["question"]["kind"] == "interpretive"
    bad = {"response": good["response"].replace("medicines impacted", "drugs affected")}
    assert outcome(bad, PFE_PROSE, "synthesis", NAMES)["filter"] == "quote_verbatim"
    assert outcome({"response": "not json"}, PFE_PROSE, "synthesis", NAMES)["filter"] == "parse"
    assert outcome({"response": None, "error": "boom"}, PFE_PROSE, "synthesis", NAMES)[
        "filter"
    ] == ("call_error")
