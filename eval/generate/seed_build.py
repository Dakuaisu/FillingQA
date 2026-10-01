"""Offline rebuild of the seeded items from the raw file (TRADEOFFS: seeding runner
halts on a call with no response; rebuild before the run). Pure.

Stage 2 order, fixed before any drawn chunk is called: key-free filters, then
no-context, then near-duplicate, then slot fill per stratum in draw order, then
reserve. Nothing past the key-free stage runs while any key-free survivor lacks
a no-context record, and no provisional candidates file is written.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict

from eval.generate.seed_runner import drawn_order, outcome
from eval.generate.seeding import near_duplicates

# F-92 flag rule, written before the run: a kept question is flagged when it
# carries a quarter label (Q1-Q4, "first ... fourth quarter") and also states a
# span longer than one quarter (6/9/12 months, 16 to 53 weeks, first half,
# year to date). Example: "for the 24 weeks ended February 16, 2025 (Q2 FY2025)".
QUARTER_LABEL = re.compile(r"\bQ[1-4]\b|\b(first|second|third|fourth) quarter\b", re.I)
MULTI_PERIOD = re.compile(
    r"\b(six|nine|twelve|6|9|12)[\s-]months?\b|\b(1[6-9]|[2-4]\d|5[0-3])[\s-]weeks?\b"
    r"|\bfirst half\b|\byear[\s-]to[\s-]date\b|\bYTD\b",
    re.I,
)
QUARTER_ON_SPAN = "quarter label next to a multi-period span (F-92)"


class Blocked(RuntimeError):
    """A later Stage 2 step cannot run yet; nothing is written."""


def quarter_label_on_span(question: str) -> bool:
    return bool(QUARTER_LABEL.search(question) and MULTI_PERIOD.search(question))


def stratum_of(d: dict) -> tuple[str, str, str, str]:
    return (d["kind"], d["ticker"], d["form"], d["item_code"])


def key_free(raw: list[dict], draw: dict, chunks: dict[str, dict], company_names: list[str]):
    """Key-free stage over every drawn chunk with a recorded response.

    Returns (survivors per stratum in draw order, dropped records, counts).
    """
    if any(r.get("verification") for r in raw):
        raise ValueError("a verification record is in the raw file")
    by_chunk = {r["chunk_id"]: r for r in raw}
    survivors: dict[tuple, list[dict]] = defaultdict(list)
    dropped, counts = [], Counter()
    for index, d in enumerate(drawn_order(draw)):
        rec = by_chunk.get(d["chunk_id"])
        if rec is None:
            counts["pending"] += 1
            continue
        o = outcome(rec, chunks[d["chunk_id"]], d["kind"], company_names)
        if o["status"] == "dropped":
            counts[f"dropped:{o['filter']}"] += 1
            counts["dropped:sign_only"] += bool(o.get("sign_only"))
            dropped.append({
                "chunk_id": d["chunk_id"], "stratum": list(stratum_of(d)),
                "position": d["position"], "filter": o["filter"], "reason": o["reason"],
                "sign_only": bool(o.get("sign_only")),
            })  # fmt: skip
            continue
        flags = list(o["flags"])
        if quarter_label_on_span(o["question"]["question"]):
            flags.append(QUARTER_ON_SPAN)
            counts["flagged:quarter_label_on_span"] += 1
        counts["kept"] += 1
        survivors[stratum_of(d)].append({
            **o, "flags": flags, "chunk_id": d["chunk_id"],
            "position": d["position"], "draw_index": index,
        })  # fmt: skip
    return dict(survivors), dropped, counts


def require_no_context(survivors: dict, no_context: dict[str, dict]) -> None:
    missing = [s["chunk_id"] for ss in survivors.values() for s in ss
               if s["chunk_id"] not in no_context]  # fmt: skip
    if missing:
        raise Blocked(f"{len(missing)} key-free survivors lack a no-context record; "
                      "no candidates or reserve written")  # fmt: skip


def drop_near_duplicates(survivors: dict, vectors: dict[str, list], existing: list,
                         threshold: float) -> tuple[dict, list[dict]]:  # fmt: skip
    """Near-duplicate stage in manifest draw order across all strata (first survives)."""
    order = sorted(((s["draw_index"], k, s) for k, ss in survivors.items() for s in ss),
                   key=lambda x: x[0])  # fmt: skip
    hits = near_duplicates([vectors[s["chunk_id"]] for _, _, s in order], existing, threshold)
    kept: dict[tuple, list[dict]] = defaultdict(list)
    dropped = []
    for (_, k, s), hit in zip(order, hits, strict=True):
        if hit is None:
            kept[k].append(s)
        else:
            why = f"cosine {hit[1]:.3f} > {threshold}"
            dropped.append({"chunk_id": s["chunk_id"], "stratum": list(k),
                            "filter": "near_duplicate", "reason": why})  # fmt: skip
    return {k: sorted(v, key=lambda s: s["position"]) for k, v in kept.items()}, dropped


def fill_slots(survivors: dict, draw: dict) -> tuple[dict, dict, dict]:
    """(candidates, reserve, shortfalls) per stratum: the first survivors in draw
    order fill the stratum's 1x slots; the rest are reserve. No backfill."""
    candidates, reserve, short = {}, {}, {}
    for kind, k in draw["kinds"].items():
        for ticker, strata in k["per_ticker"].items():
            for s in strata:
                key = (kind, ticker, s["form"], s["item_code"])
                got = sorted(survivors.get(key, []), key=lambda x: x["position"])
                candidates[key] = got[: s["slots_1x"]]
                reserve[key] = got[s["slots_1x"] :]
                if len(got) < s["slots_1x"]:
                    short[key] = (len(got), s["slots_1x"])
    return candidates, reserve, short
