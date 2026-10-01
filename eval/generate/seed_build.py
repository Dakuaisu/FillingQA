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


def check_raw(raw: list[dict], draw: dict, draw_sha: str) -> dict[str, dict]:
    """chunk_id -> record, after refusing anything the rebuild must not mix in."""
    drawn = {d["chunk_id"] for d in drawn_order(draw)}
    by_chunk: dict[str, dict] = {}
    for r in raw:
        cid = r["chunk_id"]
        if r.get("verification"):
            raise ValueError(f"a verification record is in the raw file: {cid}")
        if cid in by_chunk:
            raise ValueError(f"duplicate raw record for {cid}")
        if cid not in drawn:
            raise ValueError(f"raw record for {cid}, which is not in the draw")
        if r.get("draw_sha256") != draw_sha:
            raise ValueError(f"{cid}: draw_sha256 {r.get('draw_sha256')} is not the draw file's")
        if r.get("prompt_sha256") != draw["prompt_sha256"]:
            raise ValueError(f"{cid}: prompt_sha256 differs from the draw manifest's")
        by_chunk[cid] = r
    return by_chunk


def key_free(raw: list[dict], draw: dict, draw_sha: str, chunks: dict[str, dict],
             company_names: list[str]):  # fmt: skip
    """Key-free stage over every drawn chunk with a recorded response.

    Returns (survivors per stratum in draw order, dropped records, counts).
    """
    by_chunk = check_raw(raw, draw, draw_sha)
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


def stratum_table(draw: dict, survivors: dict, raw: list[dict]) -> list[tuple]:
    """Every slotted stratum: (key, survivors, slots_1x, drawn, pending)."""
    have = {r["chunk_id"] for r in raw}
    rows = []
    for kind, k in draw["kinds"].items():
        for ticker, strata in k["per_ticker"].items():
            for s in strata:
                key = (kind, ticker, s["form"], s["item_code"])
                pend = sum(1 for c in s["drawn"] if c not in have)
                rows.append(
                    (key, len(survivors.get(key, [])), s["slots_1x"], len(s["drawn"]), pend)
                )
    return rows


def redacted_responses(raw: list[dict]) -> list[str]:
    """Records whose response was redacted: a redacted quote fails quote_verbatim,
    which must not be read as a filter drop."""
    return [r["chunk_id"] for r in raw if "response" in r.get("scrubbed_fields", [])]


def check_no_context(survivors: dict, records: list[dict], prompt_sha: str) -> dict[str, dict]:
    """chunk_id -> no-context record, after refusing duplicates, records for chunks
    that are not key-free survivors, and records under another prompt."""
    ids = {s["chunk_id"] for ss in survivors.values() for s in ss}
    out: dict[str, dict] = {}
    for r in records:
        cid = r["chunk_id"]
        if cid in out:
            raise ValueError(f"duplicate no-context record for {cid}")
        if cid not in ids:
            raise ValueError(f"no-context record for {cid}, which is not a key-free survivor")
        if r.get("no_context_prompt_sha256") != prompt_sha:
            raise ValueError(f"{cid}: no-context prompt sha differs from the prompt file's")
        out[cid] = r
    return out


def no_context_stage(survivors: dict, records: dict[str, dict]):
    """(kept per stratum, drops, per-stratum counts). Table items: `no_context.match`
    against the item's figure; a digits-only comparison when the scale is unknown or
    the table is mixed. Interpretive items are kept with their no-context answer."""
    from decimal import Decimal

    from eval.generate.no_context import match
    from eval.generate.seeding import parse_figure

    require_no_context(survivors, records)
    kept: dict[tuple, list[dict]] = defaultdict(list)
    drops, counts = [], defaultdict(Counter)
    for key, ss in survivors.items():
        for s in ss:
            answer = records[s["chunk_id"]]["response"]
            item = {**s, "no_context_answer": answer}
            if key[0] != "table":
                kept[key].append(item)
                continue
            unscaled = any(f.startswith(("scale unknown", "scale not applied")) for f in s["flags"])
            value = None
            if not unscaled:
                value = Decimal(s["value"] if s["value"] is not None else s["magnitude"])
            m = match(answer, parse_figure(s["question"]["answer"]), value)
            counts[key]["near"] += m.near
            counts[key]["sign_only"] += m.sign_only
            if m.dropped:
                counts[key]["dropped"] += 1
                counts[key]["digits_only"] += m.digits_only
                figure = s["question"]["answer"]
                why = f"no-context answer {m.matched_text!r} within 0.5% of {figure!r}"
                drops.append({"chunk_id": s["chunk_id"], "stratum": list(key),
                              "filter": "no_context:digits_only" if m.digits_only else "no_context",
                              "reason": why, "sign_only": m.sign_only})  # fmt: skip
                continue
            flags = list(s["flags"]) + (["no-context near-match (within 5%)"] if m.near else [])
            kept[key].append({**item, "flags": flags})
    return dict(kept), drops, counts
