#!/usr/bin/env python3
"""
bridge.py — drafts your reply to Claude Code, using your Max subscription.

Runs a second, headless `claude` session as a supervisor. It reads the
builder's last message plus the PRD, and drafts your reply. No API key, no
separate billing — it uses the same auth Claude Code already has.

Usage:
    python tools/bridge.py            # draft a reply
    python tools/bridge.py --show     # print last turn only, no model call
    python tools/bridge.py --auto     # send without asking (read warnings)
    python tools/bridge.py --check    # verify setup

Stdlib only. No pip install.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(os.environ.get("FILINGQA_REPO", Path.cwd()))
SUPERVISOR_MODEL = os.environ.get("BRIDGE_MODEL", "opus")
MAX_TURN_CHARS = 24_000
TIMEOUT = 600

# Reasoning effort for BOTH the supervisor and the headless builder.
# Levels: low | medium | high | xhigh. xhigh requires Opus 4.7/4.8; on
# older models Claude Code falls back to the highest supported level.
# The env var has highest precedence, above settings files.
_VALID_EFFORT = {"low", "medium", "high", "xhigh"}
_raw_effort = os.environ.get("BRIDGE_EFFORT", "xhigh").strip().lower()
if _raw_effort in {"ultracode", "max", "ultra"}:
    # CLAUDE_CODE_EFFORT_LEVEL rejects these. Ultracode is a session setting
    # that sends xhigh + workflow orchestration; xhigh is the part an env
    # var can express. Run /ultracode in the interactive session for the rest.
    print(f"note: effort {_raw_effort!r} is not a valid env value -> using xhigh")
    _raw_effort = "xhigh"
elif _raw_effort not in _VALID_EFFORT:
    sys.exit(f"BRIDGE_EFFORT must be one of {sorted(_VALID_EFFORT)}, got {_raw_effort!r}")
EFFORT = _raw_effort

# One-turn thinking nudge, layered on top of EFFORT. Redundant at xhigh,
# so off by default. Set BRIDGE_THINK=ultrathink to re-enable.
THINK = os.environ.get("BRIDGE_THINK", "")


def child_env() -> dict[str, str]:
    """Env for spawned claude processes, with effort pinned."""
    env = os.environ.copy()
    if EFFORT:
        env["CLAUDE_CODE_EFFORT_LEVEL"] = EFFORT
    return env


# Permission mode for the builder when running unattended in --loop.
#   acceptEdits       - file edits auto-approved, bash still prompts (safe,
#                       but a bash prompt will hang a headless loop)
#   bypassPermissions - everything auto-approved (required for a real loop)
BUILDER_PERMS = os.environ.get("BRIDGE_BUILDER_PERMS", "acceptEdits")

LOOP_LOG = REPO / ".bridge" / "loop.log"

# The loop stops when the builder's message contains any of these. Phase and
# step boundaries are checkpoints you should see, not drive past.
CHECKPOINTS = [
    "phase 1 complete",
    "phase 2 complete",
    "phase 3 complete",
    "phase complete",
    "exit criterion met",
    "blocked",
    "i cannot",
    "i can't proceed",
    "needs your decision",
    "your call",
]

# Bridge stops and hands control back if any of these appear.
DANGER = [
    "drop table",
    "drop column",
    "delete from",
    "truncate",
    "rm -rf",
    "force push",
    "push --force",
    "api key",
    "secret key",
    "credential",
    "password",
    "billing",
    "spend limit",
    "charge my",
    "deploy to prod",
    "production database",
]

SYSTEM = """You are the SUPERVISOR in a two-agent setup, not the builder.

Another Claude Code agent is building FilingQA — a citation-grounded QA system
over SEC filings. You are drafting the *developer's reply* to that agent.

IMPORTANT: CLAUDE.md in this repo is the BUILDER's working agreement, not
yours. Read it as reference material describing what the builder was told.
Do not act on it. You write no code and edit no files.

You may use Read, Grep and Glob to look things up in docs/PRD.md,
docs/OPEN.md, docs/TRADEOFFS.md and the source. Do this when the builder
references a section or finding you need context on. Don't read the whole PRD.

Write as the developer: direct, technical, no pleasantries, no praise padding.

Principles you must uphold:

1. A metric coming back low is a finding about the system, never a reason to
   change the metric. Never approve loosening a threshold or definition.
2. Never approve fabricated data, stubbed metrics, or placeholder values.
3. When the spec and real data disagree, the data wins — but the resolution
   gets logged in docs/TRADEOFFS.md with reasoning.
4. One phase at a time. Don't approve scope creep or work-ahead.
5. If the builder asks something the PRD doesn't answer AND the answer would
   materially change the system, do not invent an answer. Escalate.

Output EXACTLY this shape and nothing else:

VERDICT: <one line: what the builder did, and whether it's sound>
REPLY:
<the message to send to the builder>

If the developer needs to decide personally, make the first line:
ESCALATE: <the question>
and still put your recommended reply in the REPLY block so they can edit it.
"""


# ------------------------------------------------------------- transcript


def find_transcript() -> Path | None:
    root = Path.home() / ".claude" / "projects"
    if not root.exists():
        return None
    slug = str(REPO.resolve()).replace("/", "-").replace("_", "-").strip("-")
    hits = list(root.glob(f"*{slug}*/*.jsonl")) or list(root.glob("*/*.jsonl"))
    return max(hits, key=lambda p: p.stat().st_mtime) if hits else None


def last_assistant_turn(path: Path) -> str:
    chunks: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if row.get("type") != "assistant":
            continue
        content = row.get("message", {}).get("content", [])
        text = "".join(
            b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
        )
        if text.strip():
            chunks.append(text)
    return chunks[-1][-MAX_TURN_CHARS:] if chunks else ""


# ------------------------------------------------------------- supervisor


def claude_bin() -> str:
    exe = shutil.which("claude")
    if not exe:
        sys.exit(
            "`claude` not found on PATH.\n"
            "Install Claude Code and log in with your Max account first:\n"
            "  npm install -g @anthropic-ai/claude-code && claude"
        )
    return exe


def draft(turn: str) -> str:
    """One-shot headless claude call. Uses your subscription, not the API."""
    prompt = (f"{THINK}\n\n" if THINK else "") + (
        "The builder agent just sent this message. Draft the developer's "
        "reply.\n\n"
        "===== BUILDER'S MESSAGE =====\n"
        f"{turn}\n"
        "===== END =====\n"
    )
    cmd = [
        claude_bin(),
        "-p",
        prompt,
        "--model",
        SUPERVISOR_MODEL,
        "--append-system-prompt",
        SYSTEM,
        "--allowedTools",
        "Read,Grep,Glob",
        "--output-format",
        "text",
    ]
    try:
        out = subprocess.run(
            cmd,
            cwd=REPO,
            capture_output=True,
            text=True,
            timeout=TIMEOUT,
            env=child_env(),
        )
    except subprocess.TimeoutExpired:
        sys.exit(f"supervisor timed out after {TIMEOUT}s")

    if out.returncode != 0:
        err = (out.stderr or out.stdout)[:600]
        sys.exit(
            f"claude exited {out.returncode}:\n{err}\n\n"
            "If a flag was rejected, run `claude --help` and check the exact\n"
            "spelling for --append-system-prompt / --allowedTools on your\n"
            "version, then edit the cmd list in draft()."
        )
    return out.stdout.strip()


# ------------------------------------------------------------- helpers


def danger_hits(*texts: str) -> list[str]:
    blob = " ".join(texts).lower()
    return [d for d in DANGER if d in blob]


def split_reply(raw: str) -> tuple[str, str]:
    if "REPLY:" in raw:
        head, body = raw.split("REPLY:", 1)
        return head.strip(), body.strip()
    return "", raw.strip()


def edit(text: str) -> str:
    tmp = REPO / ".bridge" / "draft.md"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(text, encoding="utf-8")
    subprocess.run([os.environ.get("EDITOR", "nano"), str(tmp)])
    return tmp.read_text(encoding="utf-8")


def send(reply: str, headless: bool = False) -> None:
    out = REPO / ".bridge" / "reply.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(reply, encoding="utf-8")
    print(f"\nsent (saved to {out})\n")

    cmd = [claude_bin(), "--continue", reply]
    if headless:
        # -p so it returns instead of opening the TUI; permission mode so it
        # doesn't block on an approval prompt nobody is there to answer.
        cmd = [
            claude_bin(),
            "--continue",
            "-p",
            reply,
            "--permission-mode",
            BUILDER_PERMS,
            "--output-format",
            "text",
        ]
        if THINK:
            cmd[3] = f"{THINK}\n\n{reply}"
    subprocess.run(cmd, cwd=REPO, env=child_env())


def log(text: str) -> None:
    LOOP_LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOOP_LOG.open("a", encoding="utf-8") as f:
        f.write(text + "\n")


def hits_checkpoint(turn: str) -> str | None:
    low = turn.lower()
    for c in CHECKPOINTS:
        if c in low:
            return c
    return None


def loop(budget: int) -> None:
    """Run up to `budget` exchanges unattended. Stops at any guardrail."""
    print(f"LOOP: up to {budget} exchanges")
    print(f"      builder perms: {BUILDER_PERMS}")
    print(f"      effort: {EFFORT}")
    print(f"      log: {LOOP_LOG}")
    print("      Ctrl+C to stop at any point.\n")

    seen: set[int] = set()

    for n in range(1, budget + 1):
        tpath = find_transcript()
        if not tpath:
            print("STOP: transcript vanished")
            return
        turn = last_assistant_turn(tpath)
        if not turn:
            print("STOP: no assistant message")
            return

        fingerprint = hash(turn[-2000:])
        if fingerprint in seen:
            print("STOP: builder repeated itself — likely stuck in a loop")
            return
        seen.add(fingerprint)

        cp = hits_checkpoint(turn)
        if cp:
            print(f"STOP: checkpoint reached ({cp!r}) — read this one yourself")
            log(f"\n=== STOPPED at checkpoint: {cp} ===\n{turn[:2000]}")
            return

        print(f"--- exchange {n}/{budget} ---")
        raw = draft(turn)
        verdict, reply = split_reply(raw)
        print(verdict or "(no verdict)")

        if "ESCALATE:" in raw.upper():
            print("STOP: escalated — your decision")
            log(f"\n=== ESCALATED at exchange {n} ===\n{raw}")
            return

        bad = danger_hits(turn, reply)
        if bad:
            print(f"STOP: sensitive topic ({', '.join(bad)})")
            log(f"\n=== DANGER at exchange {n}: {bad} ===\n{raw}")
            return

        log(
            f"\n{'=' * 70}\nEXCHANGE {n}\n{'=' * 70}\n"
            f"--- BUILDER ---\n{turn}\n\n--- SUPERVISOR ---\n{raw}"
        )
        send(reply, headless=True)

    print(f"\nDone: {budget} exchanges. Read {LOOP_LOG} before continuing.")


def check() -> None:
    print(f"repo:       {REPO}")
    print(f"claude:     {shutil.which('claude') or 'NOT FOUND'}")
    t = find_transcript()
    print(f"transcript: {t or 'NOT FOUND'}")
    if t:
        print(f"last turn:  {len(last_assistant_turn(t))} chars")
    for rel in ("CLAUDE.md", "docs/PRD.md", "docs/OPEN.md"):
        print(f"{rel:14} {'ok' if (REPO / rel).exists() else 'missing'}")
    print(f"model:      {SUPERVISOR_MODEL}")
    print(f"effort:     {EFFORT}  (CLAUDE_CODE_EFFORT_LEVEL)")
    print(f"ultrathink: {THINK or 'off'}")
    print(f"loop perms: {BUILDER_PERMS}")


# ------------------------------------------------------------- main


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--auto", action="store_true")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument(
        "--loop", type=int, metavar="N", help="run N exchanges unattended, stopping at guardrails"
    )
    args = ap.parse_args()

    if args.check:
        check()
        return

    if args.loop:
        if args.loop > 12:
            sys.exit("--loop is capped at 12. Longer runs go unreviewed.")
        loop(args.loop)
        return

    tpath = find_transcript()
    if not tpath:
        sys.exit("No Claude Code transcript under ~/.claude/projects/")

    turn = last_assistant_turn(tpath)
    if not turn:
        sys.exit(f"No assistant message in {tpath}")

    if args.show:
        print(turn)
        return

    print(f"transcript: {tpath.name}  ({len(turn)} chars)")
    print("drafting via your Claude subscription...\n")

    raw = draft(turn)
    verdict, reply = split_reply(raw)

    print("=" * 70)
    print(verdict or "(no verdict line)")
    print("=" * 70)
    print(reply)
    print("=" * 70)

    hits = danger_hits(turn, reply)
    if hits:
        print(f"\n!! STOPPED — sensitive: {', '.join(hits)}")
        print("   Read the exchange yourself before replying.")
        return
    if "ESCALATE:" in raw.upper():
        print("\n!! ESCALATED — your call. Edit and send manually.")
        return

    if args.auto:
        send(reply)
        return

    c = input("\n[enter]=send  [e]=edit  [n]=discard > ").strip().lower()
    if c == "n":
        print("discarded")
        return
    if c == "e":
        reply = edit(reply)
        if not reply.strip():
            print("empty, discarded")
            return
    send(reply)


if __name__ == "__main__":
    main()
