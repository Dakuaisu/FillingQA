"""The LLM-seeding chunk draw (TRADEOFFS, LLM seeding; seeding scale, floor, prompt).

python -m scripts.seed_draw

Key-free: no model call. Writes eval/seeding/draw_v2.json -- per slotted
stratum, `overdraw` x its 1x slots chunk ids in draw order (TRADEOFFS: seeding
overdraw is per stratum),
per-stratum exclusion counts (gold, floor), seeds, freeze versions and the
prompt sha. A re-draw is legitimate only before any model call and only on a
config change recorded in TRADEOFFS.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter

import yaml

from api.chunk.tokens import count_tokens
from api.config import REPO_ROOT, eval_seeding
from api.db import connect
from eval.generate.seeding import draw_chunks, prompt_sha
from scripts.write_freeze import FREEZE_FILE

OUT = REPO_ROOT / "eval" / "seeding" / "draw_v2.json"
PROMPT = REPO_ROOT / "eval" / "generate" / "prompts" / "seed_v1.txt"
CANDIDATES = sorted((REPO_ROOT / "eval" / "candidates").glob("*_candidates.jsonl"))
KINDS = (("table", "table"), ("synthesis", "prose"))


def main() -> None:
    cfg = eval_seeding()
    freeze = yaml.safe_load(FREEZE_FILE.read_text(encoding="utf-8"))
    parsed = [e["accession"] for e in freeze["filings"] if e["status"] == "parsed"]
    with connect() as conn:
        rows = conn.execute(
            "SELECT chunk_id, ticker, form_type, item_code, chunk_type, raw_text FROM chunks "
            "WHERE accession = ANY(%s) ORDER BY chunk_id",
            (parsed,),
        ).fetchall()
    gold = {
        c
        for path in CANDIDATES
        for line in path.read_text(encoding="utf-8").splitlines()
        for s in json.loads(line)["gold_evidence_sets"]
        for c in s
    }
    floor = cfg["synthesis"]["min_body_tokens"]
    template = PROMPT.read_text(encoding="utf-8")
    manifest = {
        "source": "python -m scripts.seed_draw",
        "eval_seeding": cfg,
        "parser_version": freeze["parser_version"],
        "chunker_version": freeze["chunker_version"],
        "prompt_file": str(PROMPT.relative_to(REPO_ROOT)),
        "prompt_sha256": prompt_sha(template),
        "gold_exclusion_source": {
            str(p.relative_to(REPO_ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in CANDIDATES
        },
        "kinds": {},
    }
    for kind, ctype in KINDS:
        c = cfg[kind]
        typed = [r for r in rows if r[4] == ctype]
        excluded_gold = Counter((t, f, i) for cid, t, f, i, _, _ in typed if cid in gold)
        rest = [r for r in typed if r[0] not in gold]
        excluded_floor: Counter = Counter()
        if ctype == "prose":
            short = {r[0] for r in rest if count_tokens(r[5]) < floor}
            excluded_floor = Counter((t, f, i) for cid, t, f, i, _, _ in rest if cid in short)
            rest = [r for r in rest if r[0] not in short]
        eligible = [
            {"chunk_id": cid, "ticker": t, "form": f, "item": i} for cid, t, f, i, _, _ in rest
        ]
        drawn = draw_chunks(eligible, c["per_ticker"], c["overdraw"], c["seed"])
        everything = Counter((r[1], r[2], r[3]) for r in typed)
        manifest["kinds"][kind] = {
            "chunk_type": ctype,
            "eligible": len(eligible),
            "excluded": [
                {"ticker": t, "form": f, "item_code": i, "chunks": n,
                 "gold": excluded_gold[(t, f, i)], "floor": excluded_floor[(t, f, i)]}
                for (t, f, i), n in sorted(everything.items(), key=lambda kv: str(kv[0]))
                if excluded_gold[(t, f, i)] or excluded_floor[(t, f, i)]
            ],
            "per_ticker": drawn,
        }  # fmt: skip
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(manifest, indent=1) + "\n"
    OUT.write_text(text, encoding="utf-8")

    for kind, k in manifest["kinds"].items():
        strata = [(t, s) for t, st in k["per_ticker"].items() for s in st]
        n1 = sum(s["slots_1x"] for _, s in strata)
        target = sum(s["draw_target"] for _, s in strata)
        n2 = sum(len(s["drawn"]) for _, s in strata)
        short = [f"{t} {s['form']} {s['item_code']} ({len(s['drawn'])} of {s['draw_target']})"
                 for t, s in strata if len(s["drawn"]) < s["draw_target"]]  # fmt: skip
        gold_x = sum(e["gold"] for e in k["excluded"])
        floor_x = sum(e["floor"] for e in k["excluded"])
        print(f"{kind}: eligible {k['eligible']}; excluded gold {gold_x}, floor {floor_x}")
        print(f"  slotted strata {len(strata)}; slots 1x {n1}; draw target {target}; drawn {n2}")
        print(f"  strata drawing fewer than their target: {short or 'none'}")
        for t, st in k["per_ticker"].items():
            cells = ", ".join(
                f"{s['form']} {s['item_code']} {s['slots_1x']}/{len(s['drawn'])}" for s in st
            )
            print(f"  {t:5} (1x/drawn) {cells}")
    ids = [c for k in manifest["kinds"].values() for st in k["per_ticker"].values()
           for s in st for c in s["drawn"]]  # fmt: skip
    print(f"distinct drawn chunks: {len(set(ids))} of {len(ids)}; gold among them: "
          f"{len(set(ids) & gold)}")  # fmt: skip
    print(f"prompt sha256 {manifest['prompt_sha256'][:16]}; wrote {OUT.relative_to(REPO_ROOT)} "
          f"sha256 {hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}")  # fmt: skip


if __name__ == "__main__":
    main()
