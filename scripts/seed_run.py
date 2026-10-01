"""The LLM-seeding runner: one model call per drawn chunk (TRADEOFFS: LLM seeding).

python -m scripts.seed_run                  # status only, no call
python -m scripts.seed_run --verify CHUNK   # one call on a chunk outside the draw and gold
python -m scripts.seed_run --show-verify    # outcome of the verify records, offline
python -m scripts.seed_run --run            # every pending drawn chunk, in draw order

Each response is appended to eval/seeding/raw_v1.jsonl as it arrives, so a crash
resumes; a chunk with a recorded response is never called again, an error
included. Only transport errors (timeout, exit without output) are retried. A
`--verify` record goes to eval/seeding/verify_v1.jsonl and never into the raw
file or the candidates.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import yaml

from api.config import REPO_ROOT, generation
from api.db import connect
from api.generate import claude_cli
from api.generate.generator import complete
from eval.generate.seed_runner import drawn_order, outcome, pending, scrub
from eval.generate.seeding import prompt_sha, render_prompt

SEEDING = REPO_ROOT / "eval" / "seeding"
DRAW = SEEDING / "draw_v2.json"
RAW = SEEDING / "raw_v1.jsonl"
VERIFY = SEEDING / "verify_v1.jsonl"
PROMPT = REPO_ROOT / "eval" / "generate" / "prompts" / "seed_v1.txt"
TEMPLATES = REPO_ROOT / "eval" / "templates.yaml"
CANDIDATES = sorted((REPO_ROOT / "eval" / "candidates").glob("*_candidates.jsonl"))
TIER = "tier_large"
TRANSPORT_RETRIES = 3


def load_chunk(conn, chunk_id: str) -> dict:
    row = conn.execute(
        "SELECT chunk_id, ticker, chunk_type, text, raw_text, unit_scale FROM chunks "
        "WHERE chunk_id = %s",
        (chunk_id,),
    ).fetchone()
    if row is None:
        raise SystemExit(f"no chunk {chunk_id}")
    scales = [
        s for (s,) in conn.execute(
            "SELECT scale FROM xbrl_spans WHERE chunk_id = %s ORDER BY span_id", (chunk_id,)
        )
    ]  # fmt: skip
    keys = ("chunk_id", "ticker", "chunk_type", "text", "raw_text", "unit_scale")
    return {**dict(zip(keys, row, strict=True)), "span_scales": scales}


def call(chunk: dict, meta: dict, cfg: dict, template: str, shas: dict, cli_version) -> dict:
    prompt = render_prompt(template, chunk["text"])
    record = {**meta, "backend": cfg["backend"], "model_requested": cfg[TIER], **shas,
              "cli_version": cli_version}  # fmt: skip
    for attempt in range(1, TRANSPORT_RETRIES + 1):
        try:
            a = complete(prompt, cfg, TIER)
        except claude_cli.TransportError as e:
            if attempt == TRANSPORT_RETRIES:
                return {**record, "model_served": None, "usage": None, "response": None,
                        "error": f"transport, {attempt} attempts: {e}"}  # fmt: skip
            continue
        except claude_cli.CliError as e:
            return {**record, "model_served": None, "usage": None, "response": None,
                    "error": str(e)}  # fmt: skip
        return {**record, "model_served": a.model,
                "usage": {"input_tokens": a.input_tokens, "output_tokens": a.output_tokens,
                          "cache_read_tokens": a.cache_read_tokens,
                          "cache_creation_tokens": a.cache_creation_tokens},
                "response": a.text, "error": None}  # fmt: skip
    raise AssertionError("unreachable")


def append(path: Path, record: dict) -> list[str]:
    clean, dropped = scrub(record, os.path.expanduser("~"))
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(clean, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    return dropped


def recorded(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {json.loads(line)["chunk_id"] for line in path.read_text(encoding="utf-8").splitlines()}


def main() -> None:
    cfg = generation()
    draw = json.loads(DRAW.read_text(encoding="utf-8"))
    template = PROMPT.read_text(encoding="utf-8")
    shas = {
        "prompt_sha256": prompt_sha(template),
        "draw_sha256": hashlib.sha256(DRAW.read_bytes()).hexdigest(),
    }
    if shas["prompt_sha256"] != draw["prompt_sha256"]:
        raise SystemExit("prompt file changed since the draw manifest was written")
    order = drawn_order(draw)
    todo = pending(order, recorded(RAW))
    print(f"backend {cfg['backend']}, model {cfg[TIER]} ({TIER}); "
          f"prompt {shas['prompt_sha256'][:16]}, draw {shas['draw_sha256'][:16]}")  # fmt: skip
    print(f"drawn chunks {len(order)}; recorded {len(order) - len(todo)}; pending {len(todo)}")
    names = yaml.safe_load(TEMPLATES.read_text(encoding="utf-8"))["company_names"]
    company_names = sorted(set(names) | set(names.values()))
    cli_version = claude_cli.version() if cfg["backend"] == "claude_cli" else None

    if "--verify" in sys.argv:
        cid = sys.argv[sys.argv.index("--verify") + 1]
        gold = {
            c for p in CANDIDATES for line in p.read_text(encoding="utf-8").splitlines()
            for s in json.loads(line)["gold_evidence_sets"] for c in s
        }  # fmt: skip
        assert cid not in {d["chunk_id"] for d in order}, f"{cid} is in the draw"
        assert cid not in gold, f"{cid} is gold for a candidate"
        with connect() as conn:
            chunk = load_chunk(conn, cid)
        kind = "table" if chunk["chunk_type"] == "table" else "synthesis"
        meta = {"chunk_id": cid, "kind": kind, "ticker": chunk["ticker"], "verification": True}
        record = call(chunk, meta, cfg, template, shas, cli_version)
        dropped = append(VERIFY, record)
        print(f"verify {cid}: in draw_v2 False, gold False; scrubbed fields {dropped}")
        print(json.dumps(scrub(record, os.path.expanduser("~"))[0], indent=1, ensure_ascii=False))
        print("outcome:", json.dumps(outcome(record, chunk, kind, company_names), indent=1,
                                     ensure_ascii=False))  # fmt: skip
        return

    if "--show-verify" in sys.argv:
        with connect() as conn:
            for line in VERIFY.read_text(encoding="utf-8").splitlines():
                rec = json.loads(line)
                chunk = load_chunk(conn, rec["chunk_id"])
                print(f"{rec['chunk_id']} (offline, from {VERIFY.relative_to(REPO_ROOT)}):")
                print(json.dumps(outcome(rec, chunk, rec["kind"], company_names), indent=1,
                                 ensure_ascii=False))  # fmt: skip
        return

    if "--run" not in sys.argv:
        return
    with connect() as conn:
        for i, d in enumerate(todo, start=1):
            chunk = load_chunk(conn, d["chunk_id"])
            record = call(chunk, d, cfg, template, shas, cli_version)
            dropped = append(RAW, record)
            print(f"[{i}/{len(todo)}] {d['kind']} {d['chunk_id']}: "
                  f"{'error ' + record['error'] if record['error'] else 'ok'}"
                  f"{'; scrubbed ' + str(dropped) if dropped else ''}", flush=True)  # fmt: skip


if __name__ == "__main__":
    main()
