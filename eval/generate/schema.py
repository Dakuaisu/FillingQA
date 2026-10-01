"""The eval item, field for field as PRD 11.1's item format, and its validator."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields

# PRD 11.1's Type column. PRD 8's eval_items comment lists a different set (F-76).
QUESTION_TYPES = (
    "xbrl_numeric", "table", "comparison", "synthesis",
    "unanswerable", "adversarial", "natural_phrasing",
)  # fmt: skip
SOURCES = ("xbrl_auto", "llm_seeded", "handwritten")
DIFFICULTIES = ("easy", "medium", "hard")


@dataclass
class EvalItem:
    item_id: str
    question: str
    question_type: str
    difficulty: str
    reference_answer: str | None
    gold_evidence_sets: list[list[str]]
    gold_accessions: list[str]
    expected_abstain: bool
    tags: list[str]
    source: str
    xbrl_fact_id: int | None
    reviewed_by_human: bool
    dataset_version: str

    def to_dict(self) -> dict:
        return asdict(self)


FIELDS = tuple(f.name for f in fields(EvalItem))


def _is_str_list(v) -> bool:
    return isinstance(v, list) and all(isinstance(x, str) and x for x in v)


def validate_item(item: dict) -> list[str]:
    """Every way `item` departs from the item format; empty when it conforms."""
    errors = []
    missing, extra = set(FIELDS) - set(item), set(item) - set(FIELDS)
    if missing:
        errors.append(f"missing fields: {sorted(missing)}")
    if extra:
        errors.append(f"unknown fields: {sorted(extra)}")
    if errors:
        return errors
    for name in ("item_id", "question", "dataset_version"):
        if not isinstance(item[name], str) or not item[name].strip():
            errors.append(f"{name} must be a non-empty string")
    for name, allowed in (
        ("question_type", QUESTION_TYPES), ("source", SOURCES), ("difficulty", DIFFICULTIES),
    ):  # fmt: skip
        if item[name] not in allowed:
            errors.append(f"{name} {item[name]!r} not in {allowed}")
    for name in ("expected_abstain", "reviewed_by_human"):
        if not isinstance(item[name], bool):
            errors.append(f"{name} must be a bool")
    sets = item["gold_evidence_sets"]
    if not isinstance(sets, list) or not all(_is_str_list(s) and s for s in sets):
        errors.append("gold_evidence_sets must be a list of non-empty lists of chunk ids")
    for name in ("gold_accessions", "tags"):
        if not _is_str_list(item[name]):
            errors.append(f"{name} must be a list of non-empty strings")
    fact = item["xbrl_fact_id"]
    if fact is not None and (isinstance(fact, bool) or not isinstance(fact, int)):
        errors.append("xbrl_fact_id must be an int or null")
    if errors:
        return errors

    if item["expected_abstain"]:
        if item["reference_answer"] is not None:
            errors.append("an abstain item has reference_answer null (PRD 8)")
    else:
        if not isinstance(item["reference_answer"], str) or not item["reference_answer"].strip():
            errors.append("an answerable item needs a reference_answer")
        if item["question_type"] != "unanswerable" and not sets:
            errors.append("an answerable item needs at least one gold evidence set")
        if sets and not item["gold_accessions"]:
            errors.append("gold evidence without gold_accessions")
    if item["source"] == "xbrl_auto" and fact is None:
        errors.append("an xbrl_auto item names its xbrl_fact_id")
    if item["question_type"] == "natural_phrasing" and item["source"] != "handwritten":
        errors.append("natural_phrasing items are source handwritten (F-11)")
    return errors
