"""Corpus snapshot for CI (PRD 11.5 "restore-corpus-snapshot"; F-135).

python -m scripts.corpus_snapshot dump [--out build/corpus_snapshot.dump]
python -m scripts.corpus_snapshot restore build/corpus_snapshot.dump

`dump`: `pg_dump --data-only -Fc` of the frozen tables (companies, filings,
chunks with their embeddings, xbrl_facts, xbrl_spans) and records the archive's
sha256, size, tables and the parser/chunker versions it carries under
`snapshot:` in api/corpus_freeze.yaml. `restore`: refuses an archive whose sha256
differs from the record, `pg_restore --data-only` into a migrated, empty
database, rebuilds the HNSW index, then `verify_freeze --snapshot`. The restored
HNSW graph is not the original one, so dense top-50 lists can differ (F-136).
Postgres tools run through PG_EXEC
(default `docker compose exec -T postgres`; CI: `docker exec -i <service id>`), so
the client always matches the server.
"""

from __future__ import annotations

import hashlib
import os
import shlex
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

from api.config import REPO_ROOT
from scripts.write_freeze import FREEZE_FILE

TABLES = ("companies", "filings", "chunks", "xbrl_facts", "xbrl_spans")
DEFAULT_OUT = REPO_ROOT / "build" / "corpus_snapshot.dump"


def pg(tool: str, *args: str) -> list[str]:
    prefix = shlex.split(os.environ.get("PG_EXEC", "docker compose exec -T postgres"))
    return [*prefix, tool, "-U", "filingqa", "-d", os.environ.get("PG_DB", "filingqa"), *args]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def snapshot_block(path: Path, record: dict) -> dict:
    return {"archive": path.name, "sha256": sha256(path), "bytes": path.stat().st_size,
            "tables": list(TABLES), "parser_version": record["parser_version"],
            "chunker_version": record["chunker_version"],
            "dumped_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "hosted": None}  # fmt: skip


def dump(out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    args = ["-Fc", "--data-only", *(x for t in TABLES for x in ("-t", t))]
    with out.open("wb") as fh:
        subprocess.run(pg("pg_dump", *args), stdout=fh, check=True)
    record = yaml.safe_load(FREEZE_FILE.read_text(encoding="utf-8"))
    block = snapshot_block(out, record)
    text = FREEZE_FILE.read_text(encoding="utf-8")
    head = text.split("\nsnapshot:\n", 1)[0].rstrip("\n")
    FREEZE_FILE.write_text(head + "\n" + yaml.safe_dump({"snapshot": block}, sort_keys=False),
                           encoding="utf-8")  # fmt: skip
    print(f"wrote {out} ({block['bytes']} bytes, sha256 {block['sha256']}); recorded in "
          f"{FREEZE_FILE.relative_to(REPO_ROOT)}")  # fmt: skip


def restore(path: Path) -> int:
    record = yaml.safe_load(FREEZE_FILE.read_text(encoding="utf-8"))
    want = (record.get("snapshot") or {}).get("sha256")
    got = sha256(path)
    if got != want:
        print(f"refusing {path}: sha256 {got} != recorded {want}", file=sys.stderr)
        return 1
    with path.open("rb") as fh:
        subprocess.run(pg("pg_restore", "--data-only", "--single-transaction",
                          "--disable-triggers"), stdin=fh, check=True)  # fmt: skip
    # pg_dump carries no index contents; rebuild the HNSW graph in bulk (F-136).
    subprocess.run(pg("psql", "-c", "REINDEX INDEX chunks_hnsw", "-c", "ANALYZE"), check=True)
    return subprocess.run([sys.executable, "-m", "scripts.verify_freeze", "--snapshot"]).returncode


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "dump":
        out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else DEFAULT_OUT
        dump(out)
    elif len(sys.argv) > 2 and sys.argv[1] == "restore":
        sys.exit(restore(Path(sys.argv[2])))
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
