"""Human review decisions (PRD 11.1 Stage 5). Pure.

Decisions are the only thing that sets `reviewed_by_human = true`. They are an
overlay: `effective` returns new item dicts and never touches a candidates file.
The latest decision for an item wins; earlier ones stay on file.
"""

from __future__ import annotations

import copy
import re

DECISIONS = ("accept", "reject", "edit_evidence")
SHEET_ITEM = re.compile(r"^## (\S+)", re.M)


def sheet_item_ids(sheet_text: str, known_ids: set[str]) -> list[str]:
    """Item ids headed in a review sheet, in order, once each."""
    out = []
    for m in SHEET_ITEM.finditer(sheet_text):
        iid = m.group(1)
        if iid in known_ids and iid not in out:
            out.append(iid)
    return out


def worksheet(sheet: str, item_ids: list[str]) -> dict:
    return {
        "sheet": sheet,
        "instructions": (
            "For each item set decision to accept, reject or edit_evidence. For edit_evidence "
            "give evidence_sets as a list of lists of chunk ids (every alternative sufficient "
            "set, F-84). Leave decision null to skip. Import with "
            "`python -m scripts.review import <this file> --reviewer <name>`."
        ),
        "decisions": [
            {"item_id": i, "decision": None, "evidence_sets": None, "note": ""} for i in item_ids
        ],
    }


def check_entry(entry: dict, items: dict, known_chunks: set[str]) -> list[str]:
    iid, d = entry.get("item_id"), entry.get("decision")
    errors = []
    if iid not in items:
        errors.append(f"{iid}: not a candidate item")
    if d not in DECISIONS:
        errors.append(f"{iid}: decision {d!r} not in {DECISIONS}")
    sets = entry.get("evidence_sets")
    if d == "edit_evidence":
        if not sets or not all(isinstance(s, list) and s for s in sets):
            errors.append(f"{iid}: edit_evidence needs evidence_sets, a list of non-empty lists")
        else:
            errors += [f"{iid}: chunk {c} is not in the frozen corpus"
                       for s in sets for c in s if c not in known_chunks]  # fmt: skip
    elif sets:
        errors.append(f"{iid}: evidence_sets only go with edit_evidence")
    return errors


def records(sheet: dict, reviewer: str, decided_at: str, items: dict, known_chunks: set[str]):
    """(decision records to append, errors). Entries left null are skipped; any error
    means nothing is appended."""
    if not reviewer.strip():
        return [], ["a reviewer name is required"]
    out, errors = [], []
    for e in sheet["decisions"]:
        if e.get("decision") is None:
            continue
        errors += check_entry(e, items, known_chunks)
        out.append({"item_id": e["item_id"], "decision": e["decision"],
                    "evidence_sets": e.get("evidence_sets"), "note": e.get("note", ""),
                    "reviewer": reviewer, "decided_at": decided_at,
                    "sheet": sheet["sheet"]})  # fmt: skip
    return ([], errors) if errors else (out, [])


def effective(items: list[dict], decisions: list[dict]) -> tuple[list[dict], list[str]]:
    """(items as reviewed, changes). Copies only; rejected items are left out."""
    latest = {}
    for d in decisions:
        latest[d["item_id"]] = d
    out, changes = [], []
    for it in items:
        d = latest.get(it["item_id"])
        if d is None:
            out.append(it)
            continue
        if d["decision"] == "reject":
            changes.append(f"{it['item_id']}: rejected ({d['reviewer']})")
            continue
        new = copy.deepcopy(it)
        new["reviewed_by_human"] = True
        if d["decision"] == "edit_evidence":
            new["gold_evidence_sets"] = d["evidence_sets"]
            new["gold_accessions"] = sorted(
                {c.split(":", 1)[0] for s in d["evidence_sets"] for c in s}
            )
            changes.append(f"{it['item_id']}: evidence {it['gold_evidence_sets']} -> "
                           f"{new['gold_evidence_sets']} ({d['reviewer']})")  # fmt: skip
        else:
            changes.append(f"{it['item_id']}: accepted ({d['reviewer']})")
        out.append(new)
    return out, changes
