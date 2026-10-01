"""Offline rebuild: key-free stage, the no-context gate, near-duplicates, slot fill.

Chunks are real (tests/fixtures/seed_chunks.json); responses are inline.
"""

from __future__ import annotations

import pytest

from eval.generate.seed_build import (
    QUARTER_ON_SPAN,
    Blocked,
    drop_near_duplicates,
    fill_slots,
    key_free,
    quarter_label_on_span,
    redacted_responses,
    require_no_context,
    stratum_table,
)
from tests.unit.test_seed_runner import COST_CF, FX_ROW, NAMES, PFE_PROSE, Q_CASH, Q_FX, response

JPM = "0000019617-24-000326:1892.0:1892.0"
DRAW_SHA = "d" * 64
DRAW = {"prompt_sha256": "p" * 64, "kinds": {
    "table": {"per_ticker": {"COST": [
        {"form": "10-Q", "item_code": "I.1", "slots_1x": 1, "draw_target": 2,
         "drawn": [COST_CF["chunk_id"], JPM]}]}},
    "synthesis": {"per_ticker": {"PFE": [
        {"form": "10-K", "item_code": "I.1A", "slots_1x": 1, "draw_target": 2,
         "drawn": [PFE_PROSE["chunk_id"], "pending-chunk"]}]}},
}}  # fmt: skip
CASH_ROW = "| CASH AND CASH EQUIVALENTS END OF PERIOD | $12,356 | $9,095 |"
TORNADO = (
    "While manufacturing has resumed, the supply of medicines impacted by the tornado "
    "is expected to be affected through 2024."
)
OTHER = {"question": "q", "answer": "a", "supporting_quote": "s"}


SHAS = {"draw_sha256": DRAW_SHA, "prompt_sha256": "p" * 64}


def raw():
    return [{**r, **SHAS} for r in _raw()]


def _raw():
    return [
        {"chunk_id": COST_CF["chunk_id"], "response": response(
            {"question": Q_CASH, "answer": "$12,356", "supporting_quote": CASH_ROW}, OTHER)},
        {"chunk_id": JPM, "response": response(
            {"question": Q_FX, "answer": "117", "supporting_quote": FX_ROW}, OTHER)},
        {"chunk_id": PFE_PROSE["chunk_id"], "response": response(OTHER, {
            "question": "How did Pfizer expect the 2023 tornado to affect supply in 2024?",
            "answer": "Affected through 2024.", "supporting_quote": TORNADO})},
    ]  # fmt: skip


def chunks():
    import tests.unit.test_seed_runner as t

    return {c: t.CH[c] for c in (COST_CF["chunk_id"], JPM, PFE_PROSE["chunk_id"])}


def test_key_free_stage_in_draw_order():
    survivors, dropped, counts = key_free(raw(), DRAW, DRAW_SHA, chunks(), NAMES)
    assert [s["chunk_id"] for s in survivors[("table", "COST", "10-Q", "I.1")]] == [
        COST_CF["chunk_id"]
    ]
    assert [s["chunk_id"] for s in survivors[("synthesis", "PFE", "10-K", "I.1A")]] == [
        PFE_PROSE["chunk_id"]
    ]
    (d,) = dropped  # the JPM record's quote is not in the JPM chunk
    assert (d["chunk_id"], d["filter"], d["position"]) == (JPM, "quote_verbatim", 1)
    assert counts["pending"] == 1 and counts["kept"] == 2
    assert counts["dropped:quote_verbatim"] == 1


def test_verification_records_never_enter():
    with pytest.raises(ValueError, match="verification"):
        key_free([{**raw()[0], "verification": True}], DRAW, DRAW_SHA, chunks(), NAMES)


def test_quarter_label_rule():
    verified = ("What was Costco Wholesale Corp's net cash used in financing activities for the "
                "24 weeks ended February 16, 2025 (Q2 FY2025)?")  # fmt: skip
    assert quarter_label_on_span(verified)
    assert quarter_label_on_span("Apple's revenue for the six months ended March 30, 2024 (Q2)?")
    assert not quarter_label_on_span("Apple's revenue for the second quarter of fiscal 2024?")
    assert not quarter_label_on_span("Costco's sales for the 12 weeks ended November 26, 2023?")
    assert not quarter_label_on_span("Apple's revenue for the nine months ended June 29, 2024?")
    flagged = {**raw()[0], "response": raw()[0]["response"].replace(Q_CASH, verified)}
    survivors, _, counts = key_free([flagged], DRAW, DRAW_SHA, chunks(), NAMES)
    (s,) = survivors[("table", "COST", "10-Q", "I.1")]
    assert QUARTER_ON_SPAN in s["flags"] and counts["flagged:quarter_label_on_span"] == 1


def test_no_candidates_without_no_context_records():
    survivors, _, _ = key_free(raw(), DRAW, DRAW_SHA, chunks(), NAMES)
    with pytest.raises(Blocked, match="1 key-free survivors lack a no-context record"):
        require_no_context(survivors, {COST_CF["chunk_id"]: {}})
    require_no_context(survivors, {s["chunk_id"]: {} for ss in survivors.values() for s in ss})


def test_near_duplicates_then_slot_fill():
    survivors, _, _ = key_free(raw(), DRAW, DRAW_SHA, chunks(), NAMES)
    vectors = {COST_CF["chunk_id"]: [1.0, 0.0], PFE_PROSE["chunk_id"]: [0.999, 0.04]}
    kept, dropped = drop_near_duplicates(survivors, vectors, [], 0.92)
    assert [d["chunk_id"] for d in dropped] == [PFE_PROSE["chunk_id"]]  # later in draw order
    candidates, reserve, short = fill_slots(kept, DRAW)
    assert [s["chunk_id"] for s in candidates[("table", "COST", "10-Q", "I.1")]] == [
        COST_CF["chunk_id"]
    ]
    assert short == {("synthesis", "PFE", "10-K", "I.1A"): (0, 1)}
    assert all(v == [] for v in reserve.values())


@pytest.mark.parametrize(
    ("records", "match"),
    [(lambda r: [*r, r[0]], "duplicate"),
     (lambda r: [*r, {**r[0], "chunk_id": "not-drawn"}], "not in the draw"),
     (lambda r: [{**r[0], "draw_sha256": "e" * 64}], "draw_sha256"),
     (lambda r: [{**r[0], "prompt_sha256": "q" * 64}], "prompt_sha256")],
)  # fmt: skip
def test_rebuild_refuses_mixed_or_stale_records(records, match):
    with pytest.raises(ValueError, match=match):
        key_free(records(raw()), DRAW, DRAW_SHA, chunks(), NAMES)


def test_every_slotted_stratum_is_listed_even_with_no_survivor():
    survivors, _, _ = key_free(raw()[1:2], DRAW, DRAW_SHA, chunks(), NAMES)  # JPM: dropped
    rows = {k: rest for k, *rest in stratum_table(DRAW, survivors, raw()[1:2])}
    assert rows[("table", "COST", "10-Q", "I.1")] == [0, 1, 2, 1]
    assert rows[("synthesis", "PFE", "10-K", "I.1A")] == [0, 1, 2, 2]


def test_redacted_responses_are_listed():
    recs = [{**raw()[0], "scrubbed_fields": ["response"]}, {**raw()[2], "scrubbed_fields": []}]
    assert redacted_responses(recs) == [COST_CF["chunk_id"]]
