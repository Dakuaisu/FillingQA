"""Review decisions as an overlay (PRD 11.1 Stage 5). Inline items and decisions."""

from __future__ import annotations

import copy

from eval.review import effective, records, sheet_item_ids, worksheet

CHUNK, OTHER = "0000909832-25-000015:68.1:68.1", "0000909832-25-000015:61.1:61.1"
ACC = "0000909832-25-000015"
ITEMS = [
    {"item_id": iid, "gold_evidence_sets": [[CHUNK]], "gold_accessions": [ACC],
     "reviewed_by_human": False}
    for iid in ("xbrl_0001", "xbrl_0002", "seed_0001")
]  # fmt: skip
BY_ID = {i["item_id"]: i for i in ITEMS}


def rec(iid, decision, sets=None, who="owner"):
    return {"item_id": iid, "decision": decision, "evidence_sets": sets, "reviewer": who}


def test_overlay_never_touches_the_candidates():
    before = copy.deepcopy(ITEMS)
    out, changes = effective(ITEMS, [
        rec("xbrl_0001", "accept"), rec("xbrl_0002", "reject"),
        rec("seed_0001", "edit_evidence", [[CHUNK], [OTHER]]),
    ])  # fmt: skip
    assert before == ITEMS  # nothing edited in place
    assert [i["item_id"] for i in out] == ["xbrl_0001", "seed_0001"]  # rejected left out
    assert all(i["reviewed_by_human"] for i in out)
    assert out[1]["gold_evidence_sets"] == [[CHUNK], [OTHER]]
    assert len(changes) == 3
    assert changes[1] == "xbrl_0002: rejected (owner)"


def test_only_decisions_set_reviewed_and_the_latest_wins():
    out, _ = effective(ITEMS, [])
    assert not any(i["reviewed_by_human"] for i in out)
    out, _ = effective(ITEMS, [rec("xbrl_0001", "reject"), rec("xbrl_0001", "accept")])
    assert out[0]["item_id"] == "xbrl_0001" and out[0]["reviewed_by_human"]


def test_import_validates_everything_or_appends_nothing():
    ws = worksheet("s.md", ["xbrl_0001", "xbrl_0002", "seed_0001"])
    ws["decisions"][0]["decision"] = "accept"
    ws["decisions"][1]["decision"] = "edit_evidence"
    ws["decisions"][1]["evidence_sets"] = [["no-such-chunk"]]
    recs, errors = records(ws, "owner", "t", BY_ID, {CHUNK, OTHER})
    assert recs == [] and errors == ["xbrl_0002: chunk no-such-chunk is not in the frozen corpus"]
    ws["decisions"][1]["evidence_sets"] = [[OTHER]]
    recs, errors = records(ws, "owner", "t", BY_ID, {CHUNK, OTHER})
    assert errors == [] and [r["item_id"] for r in recs] == [
        "xbrl_0001",
        "xbrl_0002",
    ]  # null skipped
    assert records(ws, " ", "t", BY_ID, {CHUNK})[1] == ["a reviewer name is required"]
    ws["decisions"][0]["decision"] = "maybe"
    assert "decision 'maybe'" in records(ws, "owner", "t", BY_ID, {CHUNK, OTHER})[1][0]


def test_sheet_ids_are_read_from_headings():
    text = (
        "# Sheet\n\n## xbrl_0002\n\n### chunk\n\n## seed_0001 (table, x)\n\n## xbrl_0002\n## nope\n"
    )
    assert sheet_item_ids(text, set(BY_ID)) == ["xbrl_0002", "seed_0001"]
