"""Per-claim checks to a verdict (PRD 7.5). Pure.

`supported` is PRD 7.5's, with citation validity on the figure branch too
(F-10); eval/metrics/generation.py imports it, so the faithfulness metrics and
the gate share one definition.
"""

from __future__ import annotations

PASS, PARTIAL, ABSTAIN = "PASS", "PARTIAL", "ABSTAIN"


def check(claim: dict, name: str):
    checks = claim.get("checks") or {}
    if name not in checks:
        raise ValueError(f"claim {claim.get('claim_id')!r} has no {name!r} check")
    return checks[name]


def is_figure(claim: dict) -> bool:
    return bool(claim.get("figure"))


def supported(claim: dict, nli_threshold: float) -> bool:
    """PRD 7.5 aggregation, with citation validity on both branches (F-10)."""
    if not check(claim, "citation_valid") or not check(claim, "entity_ok"):
        return False
    if is_figure(claim):
        return bool(
            check(claim, "numbers_grounded")
            and check(claim, "unit_ok")
            and check(claim, "period_stated")
            and not check(claim, "xbrl_contradiction")
        )
    return check(claim, "entail") >= nli_threshold


def verdict(claims: list[dict], nli_threshold: float | None) -> tuple[str | None, list | None]:
    """(verdict, claims_post). Pending (None, None) while a prose claim needs an
    NLI threshold that is not set."""
    if not claims:
        return ABSTAIN, []
    if nli_threshold is None and any(not is_figure(c) for c in claims):
        return None, None
    threshold = nli_threshold if nli_threshold is not None else 0.0
    post = [c for c in claims if supported(c, threshold)]
    if any(check(c, "xbrl_contradiction") for c in claims):
        return ABSTAIN, post  # hard stop: the answer contradicted the SEC's own data
    ratio = len(post) / len(claims)
    if ratio >= 0.9:
        return PASS, post
    if ratio >= 0.6:
        return PARTIAL, post
    return ABSTAIN, post


PENDING = "PENDING_NLI"


def item_verdict(model_abstained: bool, gate_verdict: str | None,
                 claims_pre: list[dict]) -> tuple[str, str | None]:  # fmt: skip
    """(item verdict, abstain_reason): the model's own abstention stands; else the
    gate's verdict, PENDING_NLI while it waits on the NLI threshold."""
    if model_abstained:
        return ABSTAIN, "insufficient_evidence"
    if gate_verdict is None:
        return PENDING, None
    if gate_verdict == ABSTAIN:
        hard = any(c["checks"]["xbrl_contradiction"] for c in claims_pre)
        return ABSTAIN, "xbrl_contradiction" if hard else "verifier"
    return gate_verdict, None


def rescore_claims(claims_pre: list[dict], nli_threshold: float) -> list[dict]:
    """Stored claims with each prose claim's `citations_supporting` set from its
    stored per-chunk entail at the threshold; figure claims untouched."""
    import copy

    out = copy.deepcopy(claims_pre)
    for c in out:
        if is_figure(c):
            continue
        by_chunk = c["checks"].get("entail_by_chunk") or []
        c["checks"]["citations_supporting"] = [
            x["chunk_id"] for x in by_chunk if x["entail"] >= nli_threshold
        ]
    return out
