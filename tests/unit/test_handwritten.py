"""Hand-written item checks (PRD 11.1 Stage 4). Inline items; vectors are synthetic."""

from __future__ import annotations

import json

from api.config import REPO_ROOT, eval_handwritten
from eval.generate.handwritten import check
from eval.generate.schema import FIELDS

CHUNK = "0000909832-25-000015:68.1:68.1"  # a real chunk (tests/fixtures/seed_chunks.json)
TARGETS = {"unanswerable": 1, "adversarial": 1, "natural_phrasing": 1}
V = "handwritten_candidates_v1"


def item(iid, qt, abstain, **kw):
    base = {"item_id": iid, "question": f"q {iid}", "question_type": qt, "difficulty": "hard",
            "reference_answer": None if abstain else "$12,356 million",
            "gold_evidence_sets": [] if abstain else [[CHUNK]],
            "gold_accessions": [] if abstain else ["0000909832-25-000015"],
            "expected_abstain": abstain, "tags": [], "source": "handwritten",
            "xbrl_fact_id": None, "reviewed_by_human": False, "dataset_version": V}  # fmt: skip
    return {**base, **kw}


GOOD = [
    item("hw_u_0001", "unanswerable", True, tags=["subtype:company_not_in_corpus"]),
    item("hw_a_0001", "adversarial", True, tags=["subtype:investment_advice"]),
    item("hw_n_0001", "natural_phrasing", False),
]


def run(items, vectors=None, existing=None, ids=frozenset()):
    vectors = vectors or [[1.0, float(i), 0.0] for i in range(len(items))]
    return check(items, targets=TARGETS, dataset_version=V, known_chunks={CHUNK},
                 existing_ids=set(ids), vectors=vectors, existing_vectors=existing or [],
                 threshold=0.92)  # fmt: skip


def test_good_items_pass():
    problems, counts = run(GOOD, vectors=[[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    assert problems == [] and counts == {"unanswerable": 1, "adversarial": 1, "natural_phrasing": 1}


def test_each_rule_reports():
    bad = [
        item("hw_u_0002", "unanswerable", True),  # no subtype tag
        item("hw_a_0002", "adversarial", None, tags=["subtype:false_premise"]),  # undecided
        item("hw_a_0003", "adversarial", False, tags=["subtype:entity_confusion"]),
        item(
            "hw_n_0002",
            "natural_phrasing",
            False,
            gold_evidence_sets=[["no-such-chunk"]],
            gold_accessions=["0000909832-25-000015"],
        ),
        item("hw_n_0003", "natural_phrasing", False, source="llm_seeded"),
        item("xbrl_0001", "natural_phrasing", False, dataset_version="x"),
    ]
    vecs = [[1, 0, 0], [0, 1, 0], [0, 0, 1], [1, 1, 0], [0, 1, 1], [1, 0, 1]]
    problems, _ = run(bad, vectors=vecs, ids={"xbrl_0001"})
    text = "\n".join(problems)
    assert "hw_u_0002: needs a tag subtype:" in text
    assert "hw_a_0002: expected_abstain must be a bool" in text
    assert "hw_a_0003: entity_confusion must expect abstention" in text
    assert "hw_n_0002: cited chunk no-such-chunk is not in the frozen corpus" in text
    assert "hw_n_0003: source must be handwritten" in text
    assert "xbrl_0001: duplicate item_id" in text and "xbrl_0001: dataset_version" in text
    assert "unanswerable: 1 items, PRD 11.1 asks for 1" not in text
    assert "adversarial: 2 items, PRD 11.1 asks for 1" in text


def test_near_duplicates_of_candidates_and_within_the_file():
    problems, _ = run(
        GOOD, vectors=[[1, 0, 0], [0.99, 0.05, 0], [0, 0, 1]], existing=[[0, 0, 0.999]]
    )
    text = "\n".join(problems)
    assert "hw_a_0001: near-duplicate of an earlier hand-written item" in text
    assert "hw_n_0001: near-duplicate of an existing candidate" in text


def test_templates_hold_no_items_and_match_the_schema():
    targets = eval_handwritten()["targets"]
    for t in targets:
        doc = json.loads((REPO_ROOT / f"eval/handwritten/templates/{t}.json").read_text())
        assert doc["target_count"] == targets[t] and tuple(doc["item"]) == FIELDS
        assert doc["item"]["source"] == "handwritten" and doc["item"]["question_type"] == t
        assert (REPO_ROOT / f"eval/handwritten/{t}.jsonl").read_text() == ""
    assert targets == {"unanswerable": 50, "adversarial": 20, "natural_phrasing": 30}
