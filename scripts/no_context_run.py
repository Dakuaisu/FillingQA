"""The no-context filter's model calls (TRADEOFFS: no-context filter rule).

python -m scripts.no_context_run                  # status only, no call
python -m scripts.no_context_run --run [--limit N]

One call per key-free seeding survivor, in draw order, on `tier_large`: the
question alone (eval/generate/prompts/no_context_v1.txt), no chunk. Same rules as
the seeding runner: appended as it arrives, never repeated; a call with no
response goes to no_context_errors_v1.jsonl, the item stays pending and the run
halts non-zero; an item that halted 3 runs stops the run.
"""

from __future__ import annotations

import hashlib
import json
import sys

import yaml

from api.config import REPO_ROOT, generation
from api.db import connect
from api.generate import claude_cli
from eval.generate.no_context import render
from eval.generate.seed_build import key_free
from eval.generate.seeding import prompt_sha
from scripts.seed_run import (
    DRAW,
    RAW,
    TEMPLATES,
    TIER,
    call_prompt,
    limited,
    load_chunk,
    read_jsonl,
    run_pending,
)

NC_PROMPT = REPO_ROOT / "eval" / "generate" / "prompts" / "no_context_v1.txt"
NC_RAW = REPO_ROOT / "eval" / "seeding" / "no_context_v1.jsonl"
NC_ERRORS = REPO_ROOT / "eval" / "seeding" / "no_context_errors_v1.jsonl"


def survivors_in_order() -> list[dict]:
    draw = json.loads(DRAW.read_text(encoding="utf-8"))
    raw = read_jsonl(RAW)
    names = yaml.safe_load(TEMPLATES.read_text(encoding="utf-8"))["company_names"]
    with connect() as conn:
        chunks = {r["chunk_id"]: load_chunk(conn, r["chunk_id"]) for r in raw}
    survivors, _, _ = key_free(raw, draw, hashlib.sha256(DRAW.read_bytes()).hexdigest(), chunks,
                               sorted(set(names) | set(names.values())))  # fmt: skip
    items = [
        {"chunk_id": s["chunk_id"], "kind": key[0], "stratum": list(key),
         "draw_index": s["draw_index"], "question": s["question"]["question"]}
        for key, ss in survivors.items() for s in ss
    ]  # fmt: skip
    return sorted(items, key=lambda d: d["draw_index"])


def main() -> None:
    cfg = generation()
    template = NC_PROMPT.read_text(encoding="utf-8")
    shas = {
        "no_context_prompt_sha256": prompt_sha(template),
        "draw_sha256": hashlib.sha256(DRAW.read_bytes()).hexdigest(),
        "seed_raw_sha256": hashlib.sha256(RAW.read_bytes()).hexdigest(),
    }
    order = survivors_in_order()
    done = {r["chunk_id"] for r in read_jsonl(NC_RAW)}
    todo = [d for d in order if d["chunk_id"] not in done]
    print(f"backend {cfg['backend']}, model {cfg[TIER]} ({TIER}); "
          f"no-context prompt {shas['no_context_prompt_sha256'][:16]}")  # fmt: skip
    print(
        f"key-free survivors {len(order)}; recorded {len(order) - len(todo)}; pending {len(todo)}"
    )
    if "--run" not in sys.argv:
        return
    cli_version = claude_cli.version() if cfg["backend"] == "claude_cli" else None
    code = run_pending(
        limited(todo, sys.argv),
        lambda cid: None,
        lambda _chunk, d: call_prompt(render(template, d["question"]), d, cfg, shas, cli_version),
        NC_RAW,
        NC_ERRORS,
    )
    sys.exit(code)


if __name__ == "__main__":
    main()
