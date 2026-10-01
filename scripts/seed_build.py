"""Rebuild the seeded items offline from eval/seeding/raw_v1.jsonl. No model call.

python -m scripts.seed_build

Writes eval/seeding/dropped_v1.jsonl (key-free drops with filter, reason and
sign_only) and prints the key-free survivors per stratum in draw order with
counts per filter; with no-context records for every survivor, applies the
no-context stage (drops appended to the same file) and prints its counts per
stratum; then near-duplicate and slot fill, and writes the llm_seeded candidates,
their manifest, the reserve and the review sheet. Never reads the verification file.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import yaml

from api.config import REPO_ROOT, eval_seeded_items, eval_seeding
from api.db import connect
from eval.generate.schema import validate_item
from eval.generate.seed_build import (
    Blocked,
    check_no_context,
    drop_near_duplicates,
    fill_slots,
    key_free,
    no_context_stage,
    redacted_responses,
    stratum_table,
)
from eval.generate.seed_items import (
    accession,
    build_item,
    manifest_entry,
    other_chunks_with_figure,
)
from eval.generate.seeding import near_duplicates, prompt_sha
from scripts.seed_run import DRAW, RAW, TEMPLATES, load_chunk, read_jsonl

DROPPED = REPO_ROOT / "eval" / "seeding" / "dropped_v1.jsonl"
CANDIDATES = sorted(
    p
    for p in (REPO_ROOT / "eval" / "candidates").glob("*_candidates.jsonl")
    if not p.name.startswith("llm_seeded")
)
ITEMS = REPO_ROOT / "eval" / "candidates" / "llm_seeded_candidates.jsonl"
MANIFEST = REPO_ROOT / "eval" / "candidates" / "llm_seeded_manifest.json"
SHEET = REPO_ROOT / "eval" / "candidates" / "llm_seeded_review.md"
RESERVE = REPO_ROOT / "eval" / "seeding" / "reserve_v1.json"
NO_CONTEXT = REPO_ROOT / "eval" / "seeding" / "no_context_v1.jsonl"
NC_PROMPT = REPO_ROOT / "eval" / "generate" / "prompts" / "no_context_v1.txt"


def main() -> None:
    draw = json.loads(DRAW.read_text(encoding="utf-8"))
    raw = read_jsonl(RAW)
    names = yaml.safe_load(TEMPLATES.read_text(encoding="utf-8"))["company_names"]
    company_names = sorted(set(names) | set(names.values()))
    with connect() as conn:
        chunks = {r["chunk_id"]: load_chunk(conn, r["chunk_id"]) for r in raw}
    draw_sha = hashlib.sha256(DRAW.read_bytes()).hexdigest()
    survivors, dropped, counts = key_free(raw, draw, draw_sha, chunks, company_names)
    Path(DROPPED).write_text("".join(json.dumps(d) + "\n" for d in dropped), encoding="utf-8")
    print(f"raw records {len(raw)}; {dict(sorted(counts.items()))}")
    print(f"wrote {DROPPED.relative_to(REPO_ROOT)}: {len(dropped)} drops")
    print(f"model_served: {dict(Counter(r.get('model_served') for r in raw))}")
    print(f"responses redacted (a quote_verbatim drop there is not a filter result): "
          f"{redacted_responses(raw) or 'none'}")  # fmt: skip
    print("slotted strata: survivors / slots_1x / drawn / pending")
    for key, n, slots, drawn, pend in stratum_table(draw, survivors, raw):
        print(f"  {' '.join(key):34} {n:2} / {slots} / {drawn} / {pend}")
    print("key-free survivors in draw order:")
    for key in sorted(survivors):
        ids = [f"{s['chunk_id']}{' [flags]' if s['flags'] else ''}" for s in survivors[key]]
        print(f"  {' '.join(key)}: {ids}")
    if not survivors:
        print("  none")
    nc_sha = prompt_sha(NC_PROMPT.read_text(encoding="utf-8"))
    records = check_no_context(survivors, read_jsonl(NO_CONTEXT), nc_sha)
    try:
        kept, nc_drops, nc_counts = no_context_stage(survivors, records)
    except Blocked as e:
        print(f"stopped after the key-free stage: {e}")
        return
    with Path(DROPPED).open("a", encoding="utf-8") as fh:
        fh.write("".join(json.dumps(d) + "\n" for d in nc_drops))
    print(f"\nno-context stage: {len(nc_drops)} dropped, appended to "
          f"{DROPPED.relative_to(REPO_ROOT)}")  # fmt: skip
    print(
        "slotted strata: survivors / slots_1x / no-context dropped / near-matches / "
        "digits-only / sign-only"
    )
    tot = Counter()
    for key, _, slots, _, _ in stratum_table(draw, survivors, raw):
        c = nc_counts.get(key, Counter())
        tot.update(c)
        n = len(kept.get(key, []))
        print(f"  {' '.join(key):34} {n:2} / {slots} / {c['dropped']} / {c['near']} / "
              f"{c['digits_only']} / {c['sign_only']}")  # fmt: skip
    print(f"  totals: kept {sum(len(v) for v in kept.values())}; {dict(tot)}")
    near_duplicate_and_slots(kept, draw, chunks, {r["chunk_id"]: r for r in raw}, nc_drops)


def near_duplicate_and_slots(
    kept: dict, draw: dict, chunks: dict, raw_by: dict, nc_drops: list
) -> None:
    """Near-duplicate stage (cosine on question embeddings, against the existing
    candidates and earlier seeded questions in draw order), then slot fill. Prints
    counts; writes no candidates or reserve (the llm_seeded item fields are not
    decided)."""
    from api.index.embed import load_model

    threshold = eval_seeding()["near_duplicate_cosine"]
    existing = [(i["item_id"], i["question"]) for p in CANDIDATES for i in read_jsonl(p)]
    seeded = sorted((s for ss in kept.values() for s in ss), key=lambda s: s["draw_index"])
    model, _ = load_model()
    encode = lambda texts: model.encode(texts, normalize_embeddings=True, convert_to_numpy=True)  # noqa: E731
    ex_vecs = list(encode([q for _, q in existing]))
    new_vecs = encode([s["question"]["question"] for s in seeded])
    vectors = {s["chunk_id"]: v for s, v in zip(seeded, new_vecs, strict=True)}
    hits = near_duplicates([vectors[s["chunk_id"]] for s in seeded], ex_vecs, threshold)
    names = [i for i, _ in existing] + [s["chunk_id"] for s in seeded]
    after, nd_drops = drop_near_duplicates(kept, vectors, ex_vecs, threshold)
    with Path(DROPPED).open("a", encoding="utf-8") as fh:
        fh.write("".join(json.dumps(d) + "\n" for d in nd_drops))
    print(f"\nnear-duplicate stage (cosine > {threshold}, question embeddings, against "
          f"{len(existing)} existing candidates and earlier seeded questions): "
          f"{len(nd_drops)} dropped, appended to {DROPPED.relative_to(REPO_ROOT)}")  # fmt: skip
    for s, hit in zip(seeded, hits, strict=True):
        if hit is not None:
            print(f"  {s['chunk_id']} ~ {names[hit[0]]} (cosine {hit[1]:.3f}): "
                  f"{s['question']['question'][:90]}")  # fmt: skip
    best = [max((float(v @ w) for w in ex_vecs), default=0.0) for v in new_vecs]
    print(f"  highest cosine of a seeded question to an existing candidate: max "
          f"{max(best):.3f}, median {sorted(best)[len(best) // 2]:.3f}")  # fmt: skip

    candidates, reserve, short = fill_slots(after, draw)
    n_c = sum(len(v) for v in candidates.values())
    n_r = sum(len(v) for v in reserve.values())
    slots = {k: sum(s["slots_1x"] for st in d["per_ticker"].values() for s in st)
             for k, d in draw["kinds"].items()}  # fmt: skip
    by_kind = Counter(k[0] for k, v in candidates.items() for _ in v)
    print(f"\nslot fill (first survivors in draw order): candidates {n_c} "
          f"({dict(by_kind)} of slots {slots}); reserve {n_r}")  # fmt: skip
    print(f"  short strata ({len(short)}): " + ", ".join(
        f"{' '.join(k)} {got}/{want}" for k, (got, want) in sorted(short.items())))  # fmt: skip
    write_outputs(candidates, reserve, short, chunks, raw_by, nc_drops)


def write_outputs(candidates: dict, reserve: dict, short: dict, chunks: dict, raw_by: dict,
                  nc_drops: list) -> None:  # fmt: skip
    """Candidates and manifest, reserve, review sheet: all from the slot fill."""
    version = eval_seeded_items()["dataset_version"]
    ordered = sorted(((s["draw_index"], k, s) for k, ss in candidates.items() for s in ss),
                     key=lambda x: x[0])  # fmt: skip
    items, entries = [], []
    for n, (_, key, s) in enumerate(ordered, start=1):
        iid = f"seed_{n:04d}"
        items.append(build_item(iid, key, s, chunks[s["chunk_id"]], raw_by[s["chunk_id"]], version))
        entries.append(manifest_entry(iid, key, s, chunks[s["chunk_id"]]))
    failures = {i["item_id"]: e for i in items if (e := validate_item(i))}
    if failures:
        raise SystemExit(f"items fail validate_item: {failures}")
    text = "".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items)
    ITEMS.write_text(text, encoding="utf-8")
    shas = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (RAW, NO_CONTEXT, DRAW, DROPPED)}  # fmt: skip
    manifest = {
        "dataset_version": version,
        "candidates_file": str(ITEMS.relative_to(REPO_ROOT)),
        "candidates_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "source": "python -m scripts.seed_build (rebuilt from the committed raw files)",
        "inputs_sha256": shas,
        "items": len(items),
        "by_type": dict(Counter(i["question_type"] for i in items)),
        "short_slots": {" ".join(k): f"{got}/{want}" for k, (got, want) in sorted(short.items())},
        "reserve_file": str(RESERVE.relative_to(REPO_ROOT)),
        "reviewed": False,
        "entries": entries,
    }
    MANIFEST.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    res = sorted(((s["draw_index"], k, s) for k, ss in reserve.items() for s in ss),
                 key=lambda x: x[0])  # fmt: skip
    RESERVE.write_text(json.dumps({
        "note": "NOT AN EVAL ARTEFACT. Seeded survivors beyond their stratum's slots, in draw "
                "order. Nothing here enters the candidates except through a recorded rebuild.",
        "items": [{**manifest_entry(None, k, s, chunks[s["chunk_id"]]),
                   "question": s["question"]["question"], "answer": s["question"]["answer"]}
                  for _, k, s in res],
    }, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")  # fmt: skip
    write_sheet(items, entries, chunks, nc_drops)
    print(f"\nwrote {ITEMS.relative_to(REPO_ROOT)}: {len(items)} items "
          f"{dict(Counter(i['question_type'] for i in items))}, validation failures 0, "
          f"sha256 {manifest['candidates_sha256'][:16]}")  # fmt: skip
    print(f"wrote {MANIFEST.relative_to(REPO_ROOT)}, {RESERVE.relative_to(REPO_ROOT)} "
          f"({len(res)} reserve), {SHEET.relative_to(REPO_ROOT)}")  # fmt: skip


def write_sheet(items: list, entries: list, chunks: dict, nc_drops: list) -> None:
    accs = sorted({accession(e["chunk_id"]) for e, i in zip(entries, items, strict=True)
                   if i["question_type"] == "table"})  # fmt: skip
    with connect() as conn:
        texts = dict(conn.execute(
            "SELECT chunk_id, raw_text FROM chunks WHERE accession = ANY(%s)", (accs,)
        ).fetchall())  # fmt: skip
    lines = [
        "# llm_seeded review sheet (PRD 11.1 Stage 5: 100% review)", "",
        "OWNER-BLOCKED: nothing here is reviewed. Development-grade: seeded and no-context "
        "checked on `claude_cli` (F-59). For each item: is the question well-formed and "
        "answerable from the chunk, is the answer right, is the gold set right and complete? "
        "Near-match flags may come from figures read inside labels or dates (F-97).", "",
    ]  # fmt: skip
    for item, e in zip(items, entries, strict=True):
        header = chunks[e["chunk_id"]]["text"].split("\n", 1)[0]
        lines += [f"## {item['item_id']} ({item['question_type']}, {' '.join(e['stratum'])})", "",
                  f"- Question: {item['question']}", f"- Answer: {item['reference_answer']}",
                  f"- Supporting quote: {e['supporting_quote']}", f"- Chunk: {e['chunk_id']}",
                  f"- Chunk header: {header}",
                  f"- No-context answer: {e['no_context_answer']!r}",
                  f"- No-context figures extracted: {e['no_context_figures'] or 'none'}; "
                  f"within 5%: {e['no_context_near_figures'] or 'none'}",
                  f"- Flags: {'; '.join(e['flags']) or 'none'}",
                  f"- Tags: {', '.join(item['tags'])}"]  # fmt: skip
        if item["question_type"] == "table":
            others = other_chunks_with_figure(item["reference_answer"], e["chunk_id"], texts)
            lines.append(f"- Other chunks in this filing printing {item['reference_answer']!r} "
                         f"(candidate alternative evidence, not gold): {len(others)}"
                         + (f" -- {', '.join(others[:12])}" + (" ..." if len(others) > 12 else "")
                            if others else ""))  # fmt: skip
        lines.append("")
    lines += [
        "# No-context drops (not candidates)",
        "",
        "The figure that matched within 0.5%, as extracted from the no-context answer.",
        "",
    ]
    for d in nc_drops:
        lines.append(f"- {d['chunk_id']} ({' '.join(d['stratum'])}, {d['filter']}"
                     f"{', sign_only' if d['sign_only'] else ''}): {d['reason']}")  # fmt: skip
    SHEET.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
