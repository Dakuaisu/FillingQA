"""How gold spans print the sign of their fact (F-87). Measurement only.

python -m scripts.sign_display

For every exact-value gold span of every eligible key (F-75), and separately for
the 200 candidates (160 xbrl_numeric, 40 comparison), reads the normalized text
around the span and classifies it: printed in parentheses "(4,388)", with a
minus sign, or plain -- against the sign of the fact's value. A positive fact in
parentheses (a cash outflow line) or a negative fact printed plain is where a
sign-sensitive match against the chunk would disagree with the reference answer.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from api.config import REPO_ROOT
from api.db import connect
from eval.generate.pool import build_pool
from scripts.concept_coverage import classify_facts

CANDIDATES = REPO_ROOT / "eval" / "candidates"
MINUS = ("-", "\u2212", "\u2013")


def printed_sign(text: str, start: int, end: int) -> str:
    """'parens', 'minus' or 'plain', from the characters around text[start:end]."""
    i = start - 1
    while i >= 0 and start - i <= 4 and text[i] in " $\u00a0":
        i -= 1
    left = text[i] if i >= 0 else ""
    j = end
    while j < len(text) and j - end <= 2 and text[j] in " \u00a0":
        j += 1
    right = text[j] if j < len(text) else ""
    if left == "(" and right == ")":
        return "parens"
    if left in MINUS:
        return "minus"
    return "plain"


def sign(value) -> str:
    return "positive" if value > 0 else "negative" if value < 0 else "zero"


def main() -> None:
    _, _, _, rows, _ = classify_facts()
    pool = build_pool(rows)
    wanted: dict[str, list] = defaultdict(list)  # accession -> keys with gold there
    for k in pool.eligible:
        for acc, cs in k.evidence:
            wanted[acc].append((k, set(cs)))
    per_key: dict[tuple, list[tuple[str, str]]] = defaultdict(list)  # key -> [(chunk, display)]
    with connect() as conn:
        paths = dict(conn.execute(
            "SELECT accession, norm_path FROM filings WHERE accession = ANY(%s)", (list(wanted),)
        ).fetchall())  # fmt: skip
        for acc, keys in sorted(wanted.items()):
            text = (REPO_ROOT / paths[acc]).read_text(encoding="utf-8")
            spans = conn.execute(
                "SELECT chunk_id, concept, value, char_start, char_end FROM xbrl_spans "
                "WHERE accession = %s AND chunk_id IS NOT NULL AND concept = ANY(%s)",
                (acc, sorted({k.concept for k, _ in keys})),
            ).fetchall()
            for k, cs in keys:
                for cid, concept, value, a, b in spans:
                    if cid in cs and concept == k.concept and value == k.value:
                        per_key[k.key].append((cid, printed_sign(text, a, b)))

    cells = Counter()
    by_item = defaultdict(Counter)
    for k in pool.eligible:
        for _, shown in per_key[k.key]:
            cells[(sign(k.value), shown)] += 1
            if (sign(k.value), shown) in (("positive", "parens"), ("positive", "minus")):
                by_item[k.line_item]["positive printed negative"] += 1
            if sign(k.value) == "negative" and shown == "plain":
                by_item[k.line_item]["negative printed plain"] += 1
    print(f"exact-value gold spans of the {len(pool.eligible)} eligible keys, "
          f"(fact sign, printed): {dict(sorted(cells.items()))}")  # fmt: skip
    print("  by line item:")
    for item, c in sorted(by_item.items()):
        print(f"    {item:28} {dict(c)}")
    keys_pos_paren = sum(
        1 for k in pool.eligible if k.value > 0 and any(s != "plain" for _, s in per_key[k.key])
    )
    keys_all = sum(
        1 for k in pool.eligible
        if k.value > 0 and per_key[k.key] and all(s != "plain" for _, s in per_key[k.key])
    )  # fmt: skip
    print(f"  positive keys with a gold span printed negative: {keys_pos_paren}; "
          f"with every gold span so printed: {keys_all}")  # fmt: skip

    by_key = {k.key: k for k in pool.eligible}
    cik_of = {(k.concept, k.period_start, k.period_end, str(k.value)): k for k in pool.eligible}
    for name, sides in (("xbrl_numeric", ("",)), ("comparison", ("earlier", "later"))):
        manifest = json.loads(
            Path(CANDIDATES / f"{name}_manifest.json").read_text(encoding="utf-8")
        )
        hit = Counter()
        flagged = []
        for iid, rec in manifest["facts"].items():
            recs = [rec] if sides == ("",) else [rec[s] for s in sides]
            shown = []
            for f in recs:
                k = cik_of[(f["concept"], f["period_start"], f["period_end"], f["value"])]
                assert k.key in by_key
                shown += [(sign(k.value), s) for _, s in per_key[k.key]]
            kinds = {
                "positive printed negative" for v, s in shown if v == "positive" and s != "plain"
            } | {"negative printed plain" for v, s in shown if v == "negative" and s == "plain"}
            for kind in kinds:
                hit[kind] += 1
            if kinds:
                flagged.append(iid)
        print(f"{name} candidates ({len(manifest['facts'])}): items with a gold span whose "
              f"printed sign disagrees with the fact: {dict(hit)}")  # fmt: skip
        print(f"  {len(flagged)} items")
        print(f"  {flagged}")


if __name__ == "__main__":
    main()
