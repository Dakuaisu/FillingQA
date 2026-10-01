"""The eval item format (PRD 11.1) and its validator."""

from __future__ import annotations

import copy

from eval.generate.schema import FIELDS, validate_item

# PRD 11.1's example item, verbatim.
PRD_EXAMPLE = {
    "item_id": "gold_0142",
    "question": "What were Apple's total inventories as of the end of fiscal 2024?",
    "question_type": "table",
    "difficulty": "easy",
    "reference_answer": "$7,286 million as of September 28, 2024.",
    "gold_evidence_sets": [["chunk_a1b2c3"], ["chunk_f9e8d7"]],
    "gold_accessions": ["0000320193-24-000123"],
    "expected_abstain": False,
    "tags": ["balance_sheet", "AAPL", "FY2024", "unit_scale_millions"],
    "source": "xbrl_auto",
    "xbrl_fact_id": 88214,
    "reviewed_by_human": False,
    "dataset_version": "v2",
}


def with_(**changes) -> dict:
    item = copy.deepcopy(PRD_EXAMPLE)
    item.update(changes)
    return item


def test_prd_example_conforms_and_fields_match():
    assert validate_item(PRD_EXAMPLE) == []
    assert tuple(PRD_EXAMPLE) == FIELDS


def test_missing_and_unknown_fields():
    item = with_(natural_phrasing=True)
    del item["tags"]
    errors = validate_item(item)
    assert any("missing" in e and "tags" in e for e in errors)
    assert any("unknown" in e and "natural_phrasing" in e for e in errors)


def test_enums():
    assert validate_item(with_(question_type="lookup"))  # PRD 8's value, not 11.1's (F-76)
    assert validate_item(with_(source="natural_phrasing"))
    assert validate_item(with_(difficulty="trivial"))


def test_natural_phrasing_is_handwritten():
    assert validate_item(with_(question_type="natural_phrasing"))
    assert not validate_item(with_(question_type="natural_phrasing", source="handwritten"))


def test_evidence_and_abstain_rules():
    assert validate_item(with_(gold_evidence_sets=[[]]))
    assert validate_item(with_(gold_evidence_sets=[]))
    assert validate_item(with_(xbrl_fact_id=None))
    assert validate_item(with_(xbrl_fact_id=True))
    abstain = with_(question_type="unanswerable", source="handwritten", xbrl_fact_id=None,
                    expected_abstain=True, reference_answer=None, gold_evidence_sets=[],
                    gold_accessions=[])  # fmt: skip
    assert validate_item(abstain) == []
    assert validate_item({**abstain, "reference_answer": "x"})
