"""LLM seeding allocation and key-free Stage 2 filters (TRADEOFFS, LLM seeding).

Chunk text is real: tests/fixtures/seed_chunks.json, written by
`python -m scripts.seed_supply --write-fixture`. Question and answer strings are
inline here, never under eval/.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
import yaml

from api.config import eval_seeding
from eval.generate.seeding import (
    allocate,
    attach_scale,
    figures,
    filter_question,
    near_duplicates,
    parse_response,
    pick_extra,
    quote_elsewhere,
    quote_in_chunk,
    same_number_elsewhere,
    unanchored_pronoun,
)
from scripts.write_freeze import FREEZE_FILE

DOC = json.loads(
    (Path(__file__).resolve().parent.parent / "fixtures" / "seed_chunks.json").read_text(
        encoding="utf-8"
    )
)
CH = {c["chunk_id"]: c for c in DOC["chunks"]}
COST_CF = CH["0000909832-25-000015:68.1:68.1"]  # cash flows, in millions
AAPL_GM = CH["0000320193-23-000106:327.0:327.0"]  # gross margin %, unit_scale NULL
AAPL_EPS = CH["0000320193-23-000106:458.0:458.0"]  # per-share note, unit_scale NULL
PFE_PROSE = CH["0000078003-24-000039:343.0:344.0"]
NVDA_A, NVDA_B = CH["0001045810-24-000029:742.0:746.0"], CH["0001045810-24-000029:748.0:752.0"]
NAMES = ["Costco", "COST", "Apple", "AAPL", "Pfizer", "PFE"]


def test_fixture_is_stamped_with_the_freeze_versions():
    record = yaml.safe_load(FREEZE_FILE.read_text(encoding="utf-8"))
    assert (DOC["parser_version"], DOC["chunker_version"]) == (
        record["parser_version"], record["chunker_version"],
    )  # fmt: skip


def test_allocation_is_largest_remainder_and_capped():
    # Arithmetic only, no row involved: 6 slots over 50/30/15/5 -> quotas 3, 1.8, 0.9, 0.3.
    assert allocate({"a": 50, "b": 30, "c": 15, "d": 5}, 6) == {"a": 3, "b": 2, "c": 1}
    # Equal remainders go to the larger stratum.
    assert allocate({"big": 3, "small": 1}, 1) == {"big": 1}
    with pytest.raises(ValueError):
        allocate({"a": 1}, 2)


def test_extra_table_tickers_match_config():
    cfg = eval_seeding()["table"]
    picked = pick_extra(sorted(cfg["per_ticker"]), cfg["seed"], 2)
    assert picked == sorted(t for t, n in cfg["per_ticker"].items() if n == 7)
    assert sum(cfg["per_ticker"].values()) == cfg["total"] == 50


def test_verbatim_normalizes_whitespace_and_pipes_only():
    quote = "CASH AND CASH EQUIVALENTS END OF PERIOD   $12,356  $9,095"
    assert quote_in_chunk(quote, COST_CF["text"])
    assert quote_in_chunk("| CASH AND CASH EQUIVALENTS END OF PERIOD | $12,356 |", COST_CF["text"])
    assert not quote_in_chunk("Cash and cash equivalents end of period $12,356", COST_CF["text"])
    assert not quote_in_chunk("CASH AND CASH EQUIVALENTS END OF PERIOD $12,357", COST_CF["text"])


def test_figures_use_the_existing_number_normalization():
    found = figures("| EFFECT OF EXCHANGE RATE CHANGES | (117) | 15 | and $12,356 and 44.1%")
    assert Decimal("-117") in found and Decimal("12356") in found and Decimal("44.1") in found


def factual(question, answer, quote):
    return {"kind": "factual", "question": question, "answer": answer, "supporting_quote": quote}


def test_numeric_answer_must_be_in_the_quote_and_not_in_the_question():
    quote = "| CASH AND CASH EQUIVALENTS END OF PERIOD | $12,356 | $9,095 |"
    q = (
        "What was Costco's cash and cash equivalents at the end of the 24 weeks ended "
        "February 16, 2025?"
    )
    assert filter_question(factual(q, "12,356", quote), COST_CF["text"], NAMES, True) is None
    drop = filter_question(factual(q, "13,700", quote), COST_CF["text"], NAMES, True)
    assert drop.filter == "answer_in_quote"
    leak = "Did Costco end the 24 weeks ended February 16, 2025 with 12,356 in cash?"
    assert filter_question(factual(leak, "12,356", quote), COST_CF["text"], NAMES, True).filter == (
        "question_leaks_answer"
    )
    # Exact after normalization: "(117)" is -117, so an answer of 117 is not in the quote.
    fx = "| EFFECT OF EXCHANGE RATE CHANGES ON CASH AND CASH EQUIVALENTS | (117) | 15 |"
    q2 = "What was the effect of exchange rates on Costco's cash in the first half of fiscal 2025?"
    assert filter_question(factual(q2, "117", fx), COST_CF["text"], NAMES, True).filter == (
        "answer_in_quote"
    )
    assert filter_question(factual(q2, "(117)", fx), COST_CF["text"], NAMES, True) is None
    assert filter_question(
        factual(q, "about twelve", quote), COST_CF["text"], NAMES, True
    ).filter == ("answer_figure")


def test_scale_comes_from_the_chunk_and_null_is_flagged():
    assert attach_scale("12,356", COST_CF["unit_scale"]) == (Decimal("12356000000"), None)
    assert attach_scale("44.1%", AAPL_GM["unit_scale"]) == (Decimal("44.1"), None)
    # The per-share note prints net income in millions but carries no unit_scale.
    value, flag = attach_scale("96,995", AAPL_EPS["unit_scale"])
    assert value == Decimal("96995") and flag.startswith("scale unknown")


def test_unanchored_pronoun_rule():
    assert unanchored_pronoun("How did it change in fiscal 2023?", NAMES)
    assert unanchored_pronoun("What does this table show for Apple in fiscal 2023?", NAMES)
    assert unanchored_pronoun("What did they disclose about Pfizer's tornado damage?", NAMES)
    assert (
        unanchored_pronoun(
            "What did Pfizer say about its Rocky Mount facility in fiscal 2023?", NAMES
        )
        is None
    )
    assert unanchored_pronoun("What gross margin did Apple report for fiscal 2023?", NAMES) is None


def test_interpretive_question_on_real_prose():
    quote = (
        "While manufacturing has resumed, the supply of medicines impacted by the tornado "
        "is expected to be affected through 2024."
    )
    q = {
        "kind": "interpretive",
        "question": "How did Pfizer expect the July 2023 tornado to affect supply?",
        "answer": "Supply of affected medicines was expected to be affected through 2024.",
        "supporting_quote": quote,
    }
    assert filter_question(q, PFE_PROSE["text"], NAMES, False) is None
    para = {
        **q,
        "supporting_quote": "Manufacturing resumed but supply stays affected through 2024.",
    }
    assert filter_question(para, PFE_PROSE["text"], NAMES, False).filter == "quote_verbatim"
    nameless = {**q, "question": "How was supply expected to be affected by the tornado?"}
    assert filter_question(nameless, PFE_PROSE["text"], NAMES, False).filter == "names_company"


def test_parse_response_is_strict():
    good = {"questions": [
        {"kind": "factual", "question": "q1", "answer": "a1", "supporting_quote": "s1"},
        {"kind": "interpretive", "question": "q2", "answer": "a2", "supporting_quote": "s2"},
    ]}  # fmt: skip
    assert parse_response(json.dumps(good))[0] is not None
    assert parse_response("```json\n" + json.dumps(good) + "\n```")[0] is not None
    assert parse_response("Here you go: " + json.dumps(good))[0] is None
    two_factual = {"questions": [dict(good["questions"][0]), dict(good["questions"][0])]}
    assert (
        parse_response(json.dumps(two_factual))[1]
        == "need one factual and one interpretive question"
    )
    extra = {"questions": [{**good["questions"][0], "note": "x"}, good["questions"][1]]}
    assert parse_response(json.dumps(extra))[0] is None


def test_near_duplicates_keep_the_first_in_draw_order():
    # Cosine arithmetic on plain vectors; no chunk text involved.
    existing = [[1.0, 0.0, 0.0]]
    new = [[0.99, 0.1, 0.0], [0.0, 1.0, 0.0], [0.0, 0.99, 0.05]]
    out = near_duplicates(new, existing, 0.92)
    assert out[0][0] == 0 and out[1] is None and out[2][0] == 2  # 2 = the second new vector


def test_review_aids_on_real_chunks():
    texts = {c["chunk_id"]: c["text"] for c in DOC["chunks"]}
    tagged = {COST_CF["chunk_id"]: {Decimal("12356")}}
    t, bare = same_number_elsewhere(Decimal("12356"), texts, tagged)
    assert t == [COST_CF["chunk_id"]] and bare == []
    t, bare = same_number_elsewhere(Decimal("96995"), texts, {})
    assert t == [] and bare == [AAPL_EPS["chunk_id"]]
    hits = quote_elsewhere(
        "See accompanying notes to the consolidated financial statements.", texts
    )
    assert hits == [NVDA_A["chunk_id"], NVDA_B["chunk_id"]]
