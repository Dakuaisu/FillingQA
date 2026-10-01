"""Checks on hand-written items (PRD 11.1 Stage 4; authored by the owner). Pure.

`check` returns every problem found; an empty list and full counts mean the
files are ready for review. Embedding vectors and the set of frozen chunk ids
are passed in by the caller.
"""

from __future__ import annotations

from collections import Counter

from eval.generate.schema import validate_item
from eval.generate.seeding import near_duplicates

SUBTYPES = {
    "unanswerable": {"metric_not_disclosed", "company_not_in_corpus", "year_outside_range",
                     "forward_looking", "wrong_form"},
    "adversarial": {"false_premise", "entity_confusion", "investment_advice", "prompt_injection"},
}  # fmt: skip
MUST_ABSTAIN = {"entity_confusion", "investment_advice"}  # PRD 11.1 states these


def subtype(item: dict) -> str | None:
    return next(
        (t.split(":", 1)[1] for t in item.get("tags", []) if t.startswith("subtype:")), None
    )


def check(
    items: list[dict],
    *,
    targets: dict[str, int],
    dataset_version: str,
    known_chunks: set[str],
    existing_ids: set[str],
    vectors: list,
    existing_vectors: list,
    threshold: float,
) -> tuple[list[str], Counter]:
    """(problems, counts per question_type). `vectors` align with `items`."""
    problems = []
    counts = Counter(i.get("question_type") for i in items)
    seen = set()
    for it in items:
        iid = it.get("item_id", "<no item_id>")
        problems += [f"{iid}: {e}" for e in validate_item(it)]
        qt = it.get("question_type")
        if it.get("source") != "handwritten":
            problems.append(f"{iid}: source must be handwritten")
        if qt not in targets:
            problems.append(
                f"{iid}: question_type {qt!r} is not a hand-written type {sorted(targets)}"
            )
        if it.get("dataset_version") != dataset_version:
            problems.append(f"{iid}: dataset_version must be {dataset_version}")
        if iid in seen or iid in existing_ids:
            problems.append(f"{iid}: duplicate item_id")
        seen.add(iid)
        st = subtype(it)
        if qt in SUBTYPES and st not in SUBTYPES[qt]:
            problems.append(f"{iid}: needs a tag subtype:<one of {sorted(SUBTYPES[qt])}>")
        if qt == "unanswerable" and it.get("expected_abstain") is not True:
            problems.append(f"{iid}: unanswerable items expect abstention")
        if qt in ("natural_phrasing", "comparison") and it.get("expected_abstain") is not False:
            problems.append(f"{iid}: {qt} items are answerable")
        if qt == "comparison":
            if not it.get("gold_evidence_sets"):
                problems.append(f"{iid}: a comparison needs at least one evidence set")
            if it.get("xbrl_fact_id") is not None:
                problems.append(f"{iid}: a hand-written comparison has xbrl_fact_id null")
        if st in MUST_ABSTAIN and it.get("expected_abstain") is not True:
            problems.append(f"{iid}: {st} must expect abstention (PRD 11.1)")
        for es in it.get("gold_evidence_sets") or []:
            for c in es:
                if c not in known_chunks:
                    problems.append(f"{iid}: cited chunk {c} is not in the frozen corpus")
        cited = {c.split(":", 1)[0] for es in it.get("gold_evidence_sets") or [] for c in es}
        if cited and cited != set(it.get("gold_accessions") or []):
            problems.append(
                f"{iid}: gold_accessions {it.get('gold_accessions')} != cited {sorted(cited)}"
            )
    hits = near_duplicates(vectors, existing_vectors, threshold)
    n_existing = len(existing_vectors)
    for it, hit in zip(items, hits, strict=True):
        if hit is not None:
            other = (
                "an existing candidate" if hit[0] < n_existing else "an earlier hand-written item"
            )
            problems.append(f"{it.get('item_id')}: near-duplicate of {other} (cosine {hit[1]:.3f})")
    for qt, want in targets.items():
        if counts[qt] != want:
            problems.append(f"{qt}: {counts[qt]} items, PRD 11.1 asks for {want}")
    return problems, counts
