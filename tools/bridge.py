#!/usr/bin/env python3
"""
bridge.py v2 - OpenCode builds, Claude Code supervises.

  Builder     opencode run, non-interactive, pinned to one session
  Supervisor  claude -p --model claude-fable-5-1, read-only, on your Max sub

The builder's stdout IS its reply, so there is no transcript parsing and no
risk of grabbing another project's conversation.

  python3 tools/bridge.py --check                 verify setup, no model calls
  python3 tools/bridge.py --pin SESSION_ID        pin the opencode session
  python3 tools/bridge.py --kickoff "message"     send to builder, capture reply
  python3 tools/bridge.py --kickoff @file.md      same, message read from a file
  python3 tools/bridge.py                         draft a reply, you approve it
  python3 tools/bridge.py --show                  print last builder output
  python3 tools/bridge.py --loop N                N exchanges unattended (max 12)

Stdlib only.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(os.environ.get("FILINGQA_REPO", Path.cwd()))
STATE = REPO / ".bridge"
SESSION_FILE = STATE / "session"
LAST_FILE = STATE / "builder_last.md"
LOOP_LOG = STATE / "loop.log"

SUPERVISOR_MODEL = os.environ.get("BRIDGE_MODEL", "claude-fable-5-1")
BUILDER_MODEL = os.environ.get("BRIDGE_BUILDER_MODEL", "")  # "" = opencode default
BUILDER_SKIP_PERMS = os.environ.get("BRIDGE_BUILDER_SKIP_PERMS", "1") == "1"
THINK = os.environ.get("BRIDGE_THINK", "ultrathink")

SUPERVISOR_TIMEOUT = 900
BUILDER_TIMEOUT = 3600
MAX_TURN_CHARS = 24_000
LOOP_CAP = 12

_VALID_EFFORT = {"low", "medium", "high", "xhigh"}
_e = os.environ.get("BRIDGE_EFFORT", "xhigh").strip().lower()
if _e in {"ultracode", "max", "ultra"}:
    print(f"note: effort {_e!r} isn't a valid env value -> using xhigh")
    _e = "xhigh"
elif _e not in _VALID_EFFORT:
    sys.exit(f"BRIDGE_EFFORT must be one of {sorted(_VALID_EFFORT)}, got {_e!r}")
EFFORT = _e

# Stop and hand control back if any of these appear.
DANGER = [
    "drop table", "drop column", "delete from", "truncate",
    "rm -rf", "force push", "push --force", "reset --hard",
    "api key", "secret key", "credential", "password",
    "billing", "spend limit", "charge my",
    "deploy to prod", "production database",
]

# Loop stops when the builder says any of these. Checkpoints you should see.
CHECKPOINTS = [
    "phase 1 complete", "phase 2 complete", "phase 3 complete",
    "phase complete", "exit criterion met",
    "blocked", "i cannot", "i can't proceed",
    "needs your decision", "your call",
    "decisions needed:",
]

ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

SYSTEM = """You are the SUPERVISOR in a two-agent setup. You are not the builder.

The builder is an OpenCode agent building FilingQA, a citation-grounded QA
system over SEC filings. You draft the developer's reply to it.

The builder's rules live in AGENTS.md / CLAUDE.md in this repo. They are the
BUILDER's working agreement, not yours: read them as reference, don't act on
them. You write no code and edit no files.

Use Read, Grep and Glob on docs/PRD.md, docs/OPEN.md, docs/TRADEOFFS.md,
docs/WORKLOG.md and the source when the builder references something you need.
Don't read the whole PRD. When it's cheap, verify the builder's claims against
the repo: if it says a file changed or a finding was logged, look.

Write as the developer: direct, technical, terse. No praise padding.

Principles you must uphold:

1. A metric coming back low is a finding about the system, never a reason to
   change the metric. Never approve loosening a threshold or definition.
2. Never approve fabricated data, stubbed metrics, or placeholder values.
3. When the spec and real data disagree, the data wins, and the resolution
   gets logged in docs/TRADEOFFS.md with reasoning.
4. One phase at a time. Don't approve scope creep or work-ahead.
5. If the builder asks something the PRD doesn't answer AND the answer would
   materially change the system, don't invent an answer. Escalate.

Output EXACTLY this shape and nothing else:

VERDICT: <one line: what the builder did, and whether it's sound>
REPLY:
<the message to send to the builder>

If the developer must decide personally, make the first line:
ESCALATE: <the question>
and still put your recommended reply in the REPLY block.

Never write "PROCEEDING:" or "DECISIONS NEEDED:" in your reply. Those are the
builder's report format. State decisions and stop.
"""


# ------------------------------------------------------------------ plumbing

def need(binary: str, hint: str) -> str:
    exe = shutil.which(binary)
    if not exe:
        sys.exit(f"`{binary}` not on PATH. {hint}")
    return exe


def child_env() -> dict[str, str]:
    env = os.environ.copy()
    # A set ANTHROPIC_API_KEY (here: via launchctl) overrides the Max login.
    env.pop("ANTHROPIC_API_KEY", None)
    env["CLAUDE_CODE_EFFORT_LEVEL"] = EFFORT
    return env


def pinned_session() -> str:
    return SESSION_FILE.read_text().strip() if SESSION_FILE.exists() else ""


def last_builder() -> str:
    if not LAST_FILE.exists():
        return ""
    return LAST_FILE.read_text(encoding="utf-8", errors="replace")[-MAX_TURN_CHARS:]


def log(text: str) -> None:
    STATE.mkdir(parents=True, exist_ok=True)
    with LOOP_LOG.open("a", encoding="utf-8") as f:
        f.write(text + "\n")


# ------------------------------------------------------------------ builder

def run_builder(message: str) -> str:
    """Send a message to the OpenCode builder and return its reply."""
    exe = need("opencode", "Install OpenCode: https://opencode.ai")
    sid = pinned_session()
    if message.lstrip().startswith("-"):
        # A reply opening with a bullet would be parsed as a CLI flag.
        message = "Reply:\n" + message

    cmd = [exe, "run"]
    cmd += ["--session", sid] if sid else ["--continue"]
    if BUILDER_MODEL:
        cmd += ["-m", BUILDER_MODEL]
    if BUILDER_SKIP_PERMS:
        cmd += ["--auto"]
    cmd.append(message)

    print(f"builder working ({'session ' + sid if sid else 'LAST session, unpinned'}) ...")
    try:
        out = subprocess.run(
            cmd, cwd=REPO, capture_output=True, text=True, timeout=BUILDER_TIMEOUT
        )
    except subprocess.TimeoutExpired:
        sys.exit(f"builder timed out after {BUILDER_TIMEOUT}s")

    if out.returncode != 0:
        err = ANSI.sub("", out.stderr or out.stdout)[:800]
        sys.exit(
            f"opencode exited {out.returncode}:\n{err}\n\n"
            "If a flag was rejected, check `opencode run --help` and fix the cmd "
            "list in run_builder()."
        )
    text = ANSI.sub("", out.stdout).strip()
    if not text:
        sys.exit("builder returned no output")
    STATE.mkdir(parents=True, exist_ok=True)
    LAST_FILE.write_text(text, encoding="utf-8")
    return text


# ------------------------------------------------------------------ supervisor

def draft(turn: str) -> str:
    """Headless Claude Code call. Uses your Max sub, not the API."""
    exe = need("claude", "Install Claude Code and log in with your Max account.")
    prompt = (f"{THINK}\n\n" if THINK else "") + (
        "The builder just sent this. Draft the developer's reply.\n\n"
        f"===== BUILDER =====\n{turn}\n===== END =====\n"
    )
    cmd = [
        exe, "-p", prompt,
        "--model", SUPERVISOR_MODEL,
        "--append-system-prompt", SYSTEM,
        "--tools", "Read,Grep,Glob",
        "--allowedTools", "Read,Grep,Glob",
        "--output-format", "text",
    ]
    try:
        out = subprocess.run(
            cmd, cwd=REPO, capture_output=True, text=True,
            timeout=SUPERVISOR_TIMEOUT, env=child_env(),
        )
    except subprocess.TimeoutExpired:
        sys.exit(f"supervisor timed out after {SUPERVISOR_TIMEOUT}s")
    if out.returncode != 0:
        err = (out.stderr or out.stdout)[:800]
        sys.exit(
            f"claude exited {out.returncode}:\n{err}\n\n"
            "If the model was rejected, check /model in Claude Code for the "
            "exact Fable id and set BRIDGE_MODEL."
        )
    return out.stdout.strip()


def split_reply(raw: str) -> tuple[str, str]:
    if "REPLY:" in raw:
        head, body = raw.split("REPLY:", 1)
        return head.strip(), body.strip()
    return "", raw.strip()


def danger_hits(*texts: str) -> list[str]:
    blob = " ".join(texts).lower()
    return [d for d in DANGER if d in blob]


def checkpoint(turn: str) -> str | None:
    low = turn.lower()
    return next((c for c in CHECKPOINTS if c in low), None)


def edit(text: str) -> str:
    tmp = STATE / "draft.md"
    STATE.mkdir(parents=True, exist_ok=True)
    tmp.write_text(text, encoding="utf-8")
    subprocess.run([os.environ.get("EDITOR", "nano"), str(tmp)])
    return tmp.read_text(encoding="utf-8")


def tail(text: str, n: int = 1500) -> str:
    return text if len(text) <= n else "...\n" + text[-n:]


# ------------------------------------------------------------------ modes

def check() -> None:
    sid = pinned_session()
    print(f"repo:          {REPO}")
    print(f"opencode:      {shutil.which('opencode') or 'NOT FOUND'}")
    print(f"claude:        {shutil.which('claude') or 'NOT FOUND'}")
    print(f"supervisor:    {SUPERVISOR_MODEL}  effort={EFFORT}  think={THINK or 'off'}")
    print(f"builder model: {BUILDER_MODEL or '(opencode default)'}")
    perms = (
        "--auto - approves everything not explicitly denied"
        if BUILDER_SKIP_PERMS
        else "prompt - headless runs may stall"
    )
    print(f"builder perms: {perms}")
    print(f"session:       {sid or 'NOT PINNED - will use last session; run --pin'}")
    print(f"last output:   {len(last_builder())} chars")
    for rel in ("AGENTS.md", "CLAUDE.md", "docs/PRD.md", "docs/OPEN.md", "docs/TRADEOFFS.md"):
        print(f"{rel:18} {'ok' if (REPO / rel).exists() else 'missing'}")
    if not (REPO / "AGENTS.md").exists():
        print("\n!! No AGENTS.md. That's OpenCode's rules file. Without it the builder")
        print("   may never see the guardrails in CLAUDE.md. Fix: ln -s CLAUDE.md AGENTS.md")


def loop(n: int) -> None:
    if n > LOOP_CAP:
        sys.exit(f"--loop is capped at {LOOP_CAP}. Longer runs go unreviewed.")
    print(f"LOOP: up to {n} exchanges | supervisor {SUPERVISOR_MODEL} @ {EFFORT} | log {LOOP_LOG}")
    print("Ctrl+C to stop.\n")
    seen: set[int] = set()

    for i in range(1, n + 1):
        turn = last_builder()
        if not turn:
            print("STOP: no builder output. Run --kickoff first.")
            return
        fp = hash(turn[-2000:])
        if fp in seen:
            print("STOP: builder repeated itself, likely stuck")
            return
        seen.add(fp)

        cp = checkpoint(turn)
        if cp:
            print(f"STOP: checkpoint ({cp!r}). Read this one yourself:\n\n{tail(turn)}")
            log(f"\n=== STOPPED at checkpoint {cp!r} ===\n{turn}")
            return

        print(f"--- exchange {i}/{n} ---")
        raw = draft(turn)
        verdict, reply = split_reply(raw)
        print(verdict or "(no verdict)")

        if "ESCALATE:" in raw.upper():
            print(f"STOP: escalated, your call.\n\n{raw}")
            log(f"\n=== ESCALATED at exchange {i} ===\n{raw}")
            return
        bad = danger_hits(turn, reply)
        if bad:
            print(f"STOP: sensitive ({', '.join(bad)}). Read it yourself.\n\n{raw}")
            log(f"\n=== DANGER at exchange {i}: {bad} ===\n{raw}")
            return

        log(f"\n{'=' * 70}\nEXCHANGE {i}\n{'=' * 70}\n"
            f"--- BUILDER ---\n{turn}\n\n--- SUPERVISOR ---\n{raw}")
        new = run_builder(reply)
        print(tail(new, 800) + "\n")

    print(f"Done: {n} exchanges. Read {LOOP_LOG} before continuing.")


def manual() -> None:
    turn = last_builder()
    if not turn:
        sys.exit('No builder output yet. Start with: --kickoff "<message>"')
    print(f"builder output: {len(turn)} chars\ndrafting with {SUPERVISOR_MODEL} @ {EFFORT} ...\n")

    raw = draft(turn)
    verdict, reply = split_reply(raw)
    print("=" * 70)
    print(verdict or "(no verdict)")
    print("=" * 70)
    print(reply)
    print("=" * 70)

    bad = danger_hits(turn, reply)
    if bad:
        print(f"\n!! STOPPED: sensitive ({', '.join(bad)}). Read it yourself.")
        return
    if "ESCALATE:" in raw.upper():
        print("\n!! ESCALATED: your call. Edit and send with --kickoff.")
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
    print(tail(run_builder(reply)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--pin", metavar="SESSION_ID")
    ap.add_argument("--kickoff", metavar="MSG_OR_@FILE")
    ap.add_argument("--loop", type=int, metavar="N")
    a = ap.parse_args()

    if a.pin:
        STATE.mkdir(parents=True, exist_ok=True)
        SESSION_FILE.write_text(a.pin.strip())
        print(f"pinned opencode session {a.pin.strip()}")
        return
    if a.check:
        check()
        return
    if a.show:
        print(last_builder() or "(no builder output yet)")
        return
    if a.kickoff:
        msg = a.kickoff
        if msg.startswith("@"):
            msg = Path(msg[1:]).read_text(encoding="utf-8")
        print(tail(run_builder(msg)))
        if not a.loop:
            return
    if a.loop:
        loop(a.loop)
        return
    manual()


if __name__ == "__main__":
    main()