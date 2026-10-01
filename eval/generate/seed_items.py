"""`llm_seeded` items from the rebuild's slot fill (TRADEOFFS: seeded item fields). Pure.

The item holds PRD 11.1's fields only; the supporting quote, the resolved value
and scale, the no-context answer and its extracted figures, and the stratum go in
the manifest entry.
"""

from __future__ import annotations

from decimal import Decimal

from eval.generate.no_context import NEAR, figures, within
from eval.generate.schema import EvalItem
from eval.generate.seed_build import QUARTER_ON_SPAN
from eval.generate.seeding import parse_figure

QUESTION_TYPE = {"table": "table", "synthesis": "synthesis"}
DIFFICULTY = {"table": "easy", "synthesis": "medium"}  # F-76
UNSCALED = ("scale unknown", "scale not applied")
NEAR_FLAG = "no-context near-match (within 5%)"


def accession(chunk_id: str) -> str:
    return chunk_id.split(":", 1)[0]


def scale_tag(s: dict, unit_scale: str | None) -> str:
    """unit_scale_<caption scale>, or unit_scale_unknown for a NULL or mixed scale and
    for a percent (no caption scale applies); confirmed at review either way (F-90)."""
    if (
        unit_scale is None
        or any(f.startswith(UNSCALED) for f in s["flags"])
        or s["question"]["answer"].strip().endswith("%")
    ):
        return "unit_scale_unknown"
    return f"unit_scale_{unit_scale.strip().lower()}"


def build_item(item_id: str, key: tuple, s: dict, chunk: dict, raw: dict,
               dataset_version: str) -> dict:  # fmt: skip
    kind, ticker, form, item_code = key
    q = s["question"]
    tags = [ticker, form, item_code, f"kind:{q['kind']}"]
    if kind == "table":
        tags.append(scale_tag(s, chunk["unit_scale"]))
    if QUARTER_ON_SPAN in s["flags"]:
        tags.append("quarter_label_on_span")
    if NEAR_FLAG in s["flags"]:
        tags.append("no_context:near_match")
    if any(f.startswith("parenthesized") for f in s["flags"]):
        tags.append("parenthesized")
    tags += [f"seed_backend:{raw['backend']}", f"seed_model:{raw['model_served']}"]
    return EvalItem(
        item_id=item_id,
        question=q["question"],
        question_type=QUESTION_TYPE[kind],
        difficulty=DIFFICULTY[kind],
        reference_answer=q["answer"],
        gold_evidence_sets=[[s["chunk_id"]]],
        gold_accessions=[accession(s["chunk_id"])],
        expected_abstain=False,
        tags=tags,
        source="llm_seeded",
        xbrl_fact_id=None,
        reviewed_by_human=False,
        dataset_version=dataset_version,
    ).to_dict()


def nc_figures(s: dict) -> tuple[list[str], list[str]]:
    """(every figure extracted from the no-context answer, those within 5% of the
    item's figure on the comparison the rule used): what the review sheet prints."""
    figs = figures(s.get("no_context_answer") or "")
    if s["question"]["kind"] != "factual":
        return [f.text for f in figs], []
    unscaled = any(f.startswith(UNSCALED) for f in s["flags"])
    printed = parse_figure(s["question"]["answer"])
    if unscaled:
        target, pick = printed, (lambda f: f.printed)
    else:
        target = Decimal(s["value"] if s["value"] is not None else s["magnitude"])
        pick = lambda f: f.value  # noqa: E731
    near = [f.text for f in figs if within(pick(f), target, NEAR)]
    return [f.text for f in figs], near


def manifest_entry(item_id: str, key: tuple, s: dict, chunk: dict) -> dict:
    extracted, near = nc_figures(s)
    return {
        "item_id": item_id,
        "chunk_id": s["chunk_id"],
        "stratum": list(key),
        "draw_index": s["draw_index"],
        "supporting_quote": s["question"]["supporting_quote"],
        "value": s.get("value"),
        "magnitude": s.get("magnitude"),
        "unit_scale": chunk["unit_scale"],
        "flags": s["flags"],
        "no_context_answer": s.get("no_context_answer"),
        "no_context_figures": extracted,
        "no_context_near_figures": near,
    }


def other_chunks_with_figure(figure: str, chunk_id: str, texts: dict[str, str]) -> list[str]:
    """Chunks of the same filing (other than the seed) printing the item's figure, by
    magnitude: candidate alternative evidence for the owner, never written to gold."""
    want = abs(parse_figure(figure))
    acc = accession(chunk_id)
    hits = []
    for cid, text in sorted(texts.items()):
        if cid == chunk_id or accession(cid) != acc:
            continue
        if any(abs(f.printed) == want for f in figures(text)):
            hits.append(cid)
    return hits
