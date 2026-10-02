"""The verification gate (PRD 7.5): every check on every claim, then the verdict.

Figure claims: citation validity, numeric grounding, unit scale, period stated,
entity match, XBRL agreement. Prose claims: citation validity, entity match, NLI
against each cited chunk. `claims_pre` is the generator's list with `checks`
added; `claims_post` the supported claims (PRD 7.5, 11.2).
Decisions in TRADEOFFS (numeric grounding; runtime XBRL validation; NLI; gate).
"""

from __future__ import annotations

import copy
import re
from decimal import Decimal

from api.config import REPO_ROOT, verification
from api.query.router import PERIOD_ENDS_SQL
from api.verify.grounding import figure_value, ground_answer
from api.verify.verdict import verdict
from api.verify.xbrl_check import (
    XbrlIndex,
    claim_kind,
    classify,
    concept_tags,
    load_concepts,
    norm,
    of_kind,
    period_ends_for,
)


def accession_of(chunk_id: str) -> str:
    return chunk_id.split(":", 1)[0]


def targets_in(question: str, names: dict[str, list[str]]) -> set[str]:
    """Tickers whose ticker or a company name appears in the question text."""
    out = set()
    for ticker, ns in names.items():
        for n in [ticker, *ns]:
            if re.search(rf"(?<![A-Za-z]){re.escape(n)}(?![A-Za-z])", question, re.I):
                out.add(ticker)
    return out


class Gate:
    def __init__(self, conn, company_names: dict[str, str], nli=None):
        cfg = verification()
        self.conn, self.nli, self.tol = conn, nli, cfg["xbrl_match_tolerance_pct"]
        self.phrases = load_concepts(REPO_ROOT / "eval" / "concepts.yaml",
                                     REPO_ROOT / cfg["concept_synonyms"])  # fmt: skip
        self.filings = conn.execute(PERIOD_ENDS_SQL).fetchall()
        self.ticker_of = dict(
            conn.execute(
                "SELECT f.accession, c.ticker FROM filings f JOIN companies c USING (cik)"
            ).fetchall()
        )
        full = dict(conn.execute("SELECT ticker, name FROM companies").fetchall())
        self.names = {t: [n for n in (company_names.get(t), full.get(t)) if n] for t in full}
        self.xbrl = XbrlIndex(conn)

    def zero_span_chunks(self, ids: list[str]) -> set[str]:
        rows = self.conn.execute(
            "SELECT DISTINCT chunk_id FROM xbrl_spans WHERE chunk_id = ANY(%s) AND value = 0",
            (ids,)).fetchall()  # fmt: skip
        return {r[0] for r in rows}

    def xbrl_check(self, claim: dict) -> dict:
        f = figure_value(claim.get("figure"))
        kind = claim_kind(claim["figure"], claim["text"]) if f is not None else None
        if f is None or kind is None:
            return {"status": "not_checked", "period_ok": None}
        phrase = norm(claim["figure"].get("concept") or "")
        tags = concept_tags(claim["figure"].get("concept"), self.phrases)
        base = {"synonym": phrase if tags else None, "tags": tags, "kind": kind,
                "claim_value": str(f.value)}  # fmt: skip
        tickers = {self.ticker_of.get(accession_of(c)) for c in claim["citations"]} - {None}
        if len(tickers) != 1 or not tags:
            why = "no concept" if not tags else "citations span companies"
            return {**base, "status": "no_fact", "period_ok": None, "why": why}
        ticker = tickers.pop()
        ends = period_ends_for(claim["figure"].get("period"), ticker, self.filings)
        if not ends:
            return {**base, "status": "no_fact", "period_ok": None, "why": "period unresolved"}
        cited = {accession_of(c) for c in claim["citations"]}
        facts = of_kind(self.xbrl.facts(ticker, tags), kind)
        out = classify(Decimal(f.value), cited, ends, facts, self.tol)
        return {**base, **out, "period_ends": [e.isoformat() for e in ends]}

    def verify(self, question: str, claims: list[dict], given: list[str], texts: dict[str, str],
               nli_threshold: float | None) -> dict:  # fmt: skip
        """claims_pre (with checks), claims_post, verdict, per-claim xbrl results."""
        pre = copy.deepcopy(claims)
        given_texts = {c: texts[c] for c in given if c in texts}
        grounding = ground_answer(pre, given_texts, self.zero_span_chunks(given))
        targets = targets_in(question, self.names)
        for c, g in zip(pre, grounding, strict=True):
            cited_tickers = {self.ticker_of.get(accession_of(x)) for x in c["citations"]}
            checks = {
                "citation_valid": bool(c["citations"]) and set(c["citations"]) <= set(given),
                "entity_ok": not targets or (cited_tickers <= targets),
                "numbers": g["numbers"], "numbers_grounded": g["numbers_grounded"],
                "numbers_derived": g["numbers_derived"], "unit_ok": g["unit_ok"],
                "period_stated": g["period_stated"],
                "xbrl": None, "xbrl_contradiction": False, "period_ok": None,
                "entail": None, "entail_by_chunk": None,
                "citations_supporting": g["citations_supporting"],
            }  # fmt: skip
            if c.get("figure"):
                x = self.xbrl_check(c)
                checks.update({"xbrl": x, "xbrl_contradiction": x["status"] == "contradiction",
                               "period_ok": x["period_ok"]})  # fmt: skip
            elif self.nli is not None:
                cited = [x for x in c["citations"] if x in given_texts]
                scores = self.nli.score([(given_texts[x], c["text"]) for x in cited])
                checks["entail_by_chunk"] = [
                    {"chunk_id": x, "entail": s,
                     "tokens": self.nli.tokens(given_texts[x], c["text"])}
                    for x, s in zip(cited, scores, strict=True)
                ]  # fmt: skip
                checks["entail"] = max(scores) if scores else 0.0
                checks["citations_supporting"] = (
                    [x for x, s in zip(cited, scores, strict=True) if s >= nli_threshold]
                    if nli_threshold is not None else []
                )  # fmt: skip
            c["checks"] = checks
        v, post = verdict(pre, nli_threshold)
        return {"claims_pre": pre, "claims_post": post, "verify_verdict": v}
