"""Claim-level generation metrics (PRD 11.2, 7.5). Pure.

Claims are PRD 7.4's shape (`claim_id`, `text`, `citations`, optional `figure`)
with the verifier's per-claim results under `checks`:

    citation_valid, numbers_grounded, unit_ok, period_stated, period_ok, entity_ok,
    xbrl_contradiction, entail, citations_supporting

They are exercised for real once Phase 4's structured output and verifier land;
until then results carry no claims and the report prints "n/a: no claims".

Two settled points: `supported()` requires `citation_valid` for figure claims as
well as prose ones (F-10, PRD 7.5's own check table), and `faithfulness_pre` is
computed over answered items only and always returned with `answer_rate` (F-09).
"""

from __future__ import annotations

NA = "n/a: no claims"


def _check(claim: dict, name: str):
    checks = claim.get("checks") or {}
    if name not in checks:
        raise ValueError(f"claim {claim.get('claim_id')!r} has no {name!r} check")
    return checks[name]


def is_figure(claim: dict) -> bool:
    return bool(claim.get("figure"))


def supported(claim: dict, nli_threshold: float) -> bool:
    """PRD 7.5 aggregation, with citation validity on both branches (F-10)."""
    if not _check(claim, "citation_valid") or not _check(claim, "entity_ok"):
        return False
    if is_figure(claim):
        return bool(
            _check(claim, "numbers_grounded")
            and _check(claim, "unit_ok")
            and _check(claim, "period_stated")
            and not _check(claim, "xbrl_contradiction")
        )
    return _check(claim, "entail") >= nli_threshold


def _rate(num: int, den: int):
    return num / den if den else None


def generation_metrics(results: list[dict], nli_threshold: float) -> dict:
    """`results`: one per item, with `claims_pre`, `claims_post` (PRD 7.5) and
    `answer.abstained`. Returns NA for every metric when no result has a claim."""
    pre_all = [c for r in results for c in r.get("claims_pre") or []]
    post_all = [c for r in results for c in r.get("claims_post") or []]
    if not pre_all and not post_all:
        return {"status": NA}
    answered = [r for r in results if not (r.get("answer") or {}).get("abstained")]
    pre = [c for r in answered for c in r.get("claims_pre") or []]
    post = [c for r in answered for c in r.get("claims_post") or []]
    f_pre = _rate(sum(supported(c, nli_threshold) for c in pre), len(pre))
    f_post = _rate(sum(supported(c, nli_threshold) for c in post), len(post))
    figures = [c for c in pre if is_figure(c)]
    cites = sum(len(c.get("citations") or []) for c in pre)
    good_cites = sum(
        len(set(c.get("citations") or []) & set(_check(c, "citations_supporting") or []))
        for c in pre
    )
    return {
        "status": "ok",
        "answer_rate": _rate(len(answered), len(results)),  # always beside faithfulness_pre
        "faithfulness_pre": f_pre,
        "faithfulness_post": f_post,
        "verifier_lift": None if f_pre is None or f_post is None else f_post - f_pre,
        "claim_retention": _rate(len(post), len(pre)),
        "citation_coverage": _rate(sum(bool(c.get("citations")) for c in pre), len(pre)),
        "citation_precision": _rate(good_cites, cites),
        "unit_scale_accuracy": _rate(
            sum(bool(_check(c, "unit_ok")) for c in figures), len(figures)
        ),
        "period_accuracy": _rate(sum(bool(_check(c, "period_ok")) for c in figures), len(figures)),
        "xbrl_contradiction_rate": _rate(
            sum(bool(_check(c, "xbrl_contradiction")) for c in figures), len(figures)
        ),
        "claims_pre": len(pre),
        "claims_post": len(post),
    }
