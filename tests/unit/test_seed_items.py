"""llm_seeded item fields and manifest entries (TRADEOFFS: seeded item fields)."""

from __future__ import annotations

from eval.generate.schema import validate_item
from eval.generate.seed_build import check_no_context, key_free, no_context_stage
from eval.generate.seed_items import (
    build_item,
    manifest_entry,
    other_chunks_with_figure,
    scale_tag,
)
from tests.unit.test_seed_build import DRAW, DRAW_SHA, chunks, nc, raw
from tests.unit.test_seed_runner import COST_CF, JPM_EPS, NAMES, PFE_PROSE

RAW_META = {"backend": "claude_cli", "model_served": "claude-sonnet-5-5"}


def kept():
    survivors, _, _ = key_free(raw(), DRAW, DRAW_SHA, chunks(), NAMES)
    recs = check_no_context(survivors, [
        nc(COST_CF["chunk_id"], "Roughly $12 billion; FY2025."),
        nc(PFE_PROSE["chunk_id"], "Unknown."),
    ], "n")  # fmt: skip
    out, _, _ = no_context_stage(survivors, recs)
    return out


def test_table_and_synthesis_items_carry_the_approved_fields():
    k = kept()
    (t,) = k[("table", "COST", "10-Q", "I.1")]
    (p,) = k[("synthesis", "PFE", "10-K", "I.1A")]
    ti = build_item("seed_0001", ("table", "COST", "10-Q", "I.1"), t, COST_CF, RAW_META, "v")
    pi = build_item("seed_0002", ("synthesis", "PFE", "10-K", "I.1A"), p, PFE_PROSE, RAW_META, "v")
    assert validate_item(ti) == [] and validate_item(pi) == []
    assert (ti["question_type"], ti["difficulty"], pi["difficulty"]) == ("table", "easy", "medium")
    assert ti["reference_answer"] == "$12,356"  # the model's answer, unchanged
    assert ti["gold_evidence_sets"] == [[COST_CF["chunk_id"]]]
    assert ti["gold_accessions"] == ["0000909832-25-000015"]
    assert (ti["source"], ti["xbrl_fact_id"], ti["reviewed_by_human"]) == (
        "llm_seeded",
        None,
        False,
    )
    assert ti["tags"] == ["COST", "10-Q", "I.1", "kind:factual", "unit_scale_millions",
                          "no_context:near_match", "seed_backend:claude_cli",
                          "seed_model:claude-sonnet-5-5"]  # fmt: skip
    assert "kind:interpretive" in pi["tags"] and not any(
        x.startswith("unit_scale") for x in pi["tags"]
    )


def test_manifest_holds_quote_value_and_no_context_figures():
    (t,) = kept()[("table", "COST", "10-Q", "I.1")]
    e = manifest_entry("seed_0001", ("table", "COST", "10-Q", "I.1"), t, COST_CF)
    assert e["supporting_quote"].startswith("| CASH AND CASH EQUIVALENTS")
    assert (e["value"], e["unit_scale"]) == ("12356000000", "millions")
    assert e["no_context_figures"] == ["$12 billion", "2025"]  # "2025" from "FY2025" (F-97)
    assert e["no_context_near_figures"] == ["$12 billion"]


def test_scale_tag_unknown_for_null_mixed_or_percent():
    base = {"flags": [], "question": {"answer": "12,356"}}
    assert scale_tag(base, "millions") == "unit_scale_millions"
    assert scale_tag(base, None) == "unit_scale_unknown"
    mixed = {**base, "flags": ["scale not applied, mixed table: ..."]}
    assert scale_tag(mixed, JPM_EPS["unit_scale"]) == "unit_scale_unknown"
    assert (
        scale_tag({"flags": [], "question": {"answer": "44.1%"}}, "millions")
        == "unit_scale_unknown"
    )


def test_other_chunks_in_the_same_filing_only():
    texts = {COST_CF["chunk_id"]: COST_CF["text"],
             "0000909832-25-000015:1.0:1.0": "Cash ended the period at $12,356 million.",
             "0000909832-25-000016:1.0:1.0": "Cash was 12,356."}  # fmt: skip
    assert other_chunks_with_figure("$12,356", COST_CF["chunk_id"], texts) == [
        "0000909832-25-000015:1.0:1.0"
    ]
