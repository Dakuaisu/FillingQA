"""The LLM-seeding runner: one model call per drawn chunk (TRADEOFFS: LLM seeding).

python -m scripts.seed_run                  # status only, no call
python -m scripts.seed_run --verify CHUNK   # one call on a chunk outside the draw and gold
python -m scripts.seed_run --show-verify    # outcome of the verify records, offline
python -m scripts.seed_run --run [--limit N] # pending drawn chunks, in draw order

Each response is appended to eval/seeding/raw_v1.jsonl as it arrives, so a crash
resumes; a chunk with a recorded response is never called again. A call that
returns no model output (an is_error result, non-JSON output, no modelUsage, or
a transport failure after 3 attempts) is written to call_errors_v1.jsonl with
every attempt, the chunk stays pending and the run halts non-zero. A chunk that
halted 3 runs stops the run. A `--verify` record goes to verify_v1.jsonl and
never into the raw file or the candidates.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

from api.config import REPO_ROOT, generation
from api.db import connect
from api.generate import claude_cli
from api.generate.generator import complete
from eval.generate.seed_runner import drawn_order, halts, outcome, pending, scrub
from eval.generate.seeding import prompt_sha, render_prompt

SEEDING = REPO_ROOT / "eval" / "seeding"
DRAW = SEEDING / "draw_v2.json"
RAW = SEEDING / "raw_v1.jsonl"
ERRORS = SEEDING / "call_errors_v1.jsonl"
VERIFY = SEEDING / "verify_v1.jsonl"
PROMPT = REPO_ROOT / "eval" / "generate" / "prompts" / "seed_v1.txt"
TEMPLATES = REPO_ROOT / "eval" / "templates.yaml"
CANDIDATES = sorted((REPO_ROOT / "eval" / "candidates").glob("*_candidates.jsonl"))
TIER = "tier_large"
TRANSPORT_RETRIES = 3
MAX_HALTS = 3


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


class CallFailed(Exception):
    """A call that returned no model output; the chunk stays pending."""

    def __init__(self, attempts: list[dict]):
        self.attempts = attempts
        super().__init__(attempts[-1]["error"])


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def call(chunk: dict, meta: dict, cfg: dict, template: str, shas: dict, cli_version) -> dict:
    """A record with the model's response, or CallFailed with every failed attempt.

    Transport errors are retried up to TRANSPORT_RETRIES; any other CLI error
    (is_error, non-JSON output, no modelUsage) fails at once.
    """
    prompt = render_prompt(template, chunk["text"])
    attempts = []
    for _ in range(TRANSPORT_RETRIES):
        called_at = now()
        try:
            a = complete(prompt, cfg, TIER)
        except claude_cli.TransportError as e:
            attempts.append({"called_at": called_at, "kind": "transport", "error": str(e)})
            continue
        except claude_cli.CliError as e:
            attempts.append({"called_at": called_at, "kind": "cli", "error": str(e)})
            raise CallFailed(attempts) from e
        if cfg[TIER] not in a.model.split(","):
            attempts.append({"called_at": called_at, "kind": "wrong_model",
                             "error": f"served {a.model}, requested {cfg[TIER]}",
                             "response": a.text})  # fmt: skip
            raise CallFailed(attempts)
        return {**meta, "called_at": called_at, "backend": cfg["backend"],
                "model_requested": cfg[TIER], "model_served": a.model, **shas,
                "cli_version": cli_version,
                "usage": {"input_tokens": a.input_tokens, "output_tokens": a.output_tokens,
                          "cache_read_tokens": a.cache_read_tokens,
                          "cache_creation_tokens": a.cache_creation_tokens},
                "response": a.text}  # fmt: skip
    raise CallFailed(attempts)


def run_pending(todo: list[dict], chunk_of, call_one, raw: Path, errors: Path) -> int:
    """Call each pending chunk in order. Exit status: 0 done, 1 halted on a failed
    call (chunk left pending, error on file), 2 refused a chunk that halted
    MAX_HALTS runs already."""
    past = read_jsonl(errors)
    for i, d in enumerate(todo, start=1):
        n = halts(past, d["chunk_id"])
        if n >= MAX_HALTS:
            print(f"STOP: {d['chunk_id']} halted {n} runs; not called, not skipped")
            return 2
        try:
            record = call_one(chunk_of(d["chunk_id"]), d)
        except CallFailed as e:
            append(errors, {"chunk_id": d["chunk_id"], "kind": d["kind"],
                            "halted_at": now(), "attempts": e.attempts})  # fmt: skip
            print(f"HALT at [{i}/{len(todo)}] {d['chunk_id']}: {e}; chunk stays pending")
            return 1
        scrubbed = append(raw, record)
        print(f"[{i}/{len(todo)}] {d['kind']} {d['chunk_id']}: ok"
              f"{'; redacted ' + str(scrubbed) if scrubbed else ''}", flush=True)  # fmt: skip
    return 0


def limited(todo: list[dict], argv: list[str]) -> list[dict]:
    """`--limit N`: the first N pending chunks in draw order."""
    if "--limit" not in argv:
        return todo
    n = int(argv[argv.index("--limit") + 1])
    if n < 1:
        raise SystemExit("--limit must be at least 1")
    return todo[:n]


def read_jsonl(path: Path) -> list[dict]:
    """One record per "\n"-terminated line. Not splitlines(): it also splits on
    U+2028, U+2029 and U+0085, which ensure_ascii=False leaves raw in a response."""
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line]


def append(path: Path, record: dict) -> list[str]:
    clean, dropped = scrub(record, os.path.expanduser("~"))
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(clean, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    return dropped


def recorded(path: Path) -> set[str]:
    return {r["chunk_id"] for r in read_jsonl(path)}


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
            c for p in CANDIDATES for item in read_jsonl(p)
            for s in item["gold_evidence_sets"] for c in s
        }  # fmt: skip
        assert cid not in {d["chunk_id"] for d in order}, f"{cid} is in the draw"
        assert cid not in gold, f"{cid} is gold for a candidate"
        with connect() as conn:
            chunk = load_chunk(conn, cid)
        kind = "table" if chunk["chunk_type"] == "table" else "synthesis"
        meta = {"chunk_id": cid, "kind": kind, "ticker": chunk["ticker"], "verification": True}
        try:
            record = call(chunk, meta, cfg, template, shas, cli_version)
        except CallFailed as e:
            append(ERRORS, {"chunk_id": cid, "kind": kind, "verification": True,
                            "halted_at": now(), "attempts": e.attempts})  # fmt: skip
            print(f"HALT on verification {cid}: {e}")
            sys.exit(1)
        dropped = append(VERIFY, record)
        print(f"verify {cid}: in draw_v2 False, gold False; scrubbed fields {dropped}")
        print(json.dumps(scrub(record, os.path.expanduser("~"))[0], indent=1, ensure_ascii=False))
        print("outcome:", json.dumps(outcome(record, chunk, kind, company_names), indent=1,
                                     ensure_ascii=False))  # fmt: skip
        return

    if "--show-verify" in sys.argv:
        with connect() as conn:
            for rec in read_jsonl(VERIFY):
                chunk = load_chunk(conn, rec["chunk_id"])
                print(f"{rec['chunk_id']} (offline, from {VERIFY.relative_to(REPO_ROOT)}):")
                print(json.dumps(outcome(rec, chunk, rec["kind"], company_names), indent=1,
                                 ensure_ascii=False))  # fmt: skip
        return

    if "--run" not in sys.argv:
        return
    todo = limited(todo, sys.argv)
    with connect() as conn:
        code = run_pending(
            todo,
            lambda cid: load_chunk(conn, cid),
            lambda chunk, d: call(chunk, d, cfg, template, shas, cli_version),
            RAW,
            ERRORS,
        )
    sys.exit(code)


if __name__ == "__main__":
    main()
