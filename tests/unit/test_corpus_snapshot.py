"""Corpus snapshot (F-135): restore refuses an archive whose sha256 is not recorded."""

from __future__ import annotations

import hashlib

import scripts.corpus_snapshot as cs


def test_restore_refuses_a_different_archive(tmp_path, monkeypatch):
    archive = tmp_path / "corpus_snapshot.dump"
    archive.write_bytes(b"not the frozen corpus")
    freeze = tmp_path / "freeze.yaml"
    freeze.write_text(
        "parser_version: p\nchunker_version: c\nsnapshot:\n  sha256: " + "0" * 64 + "\n"
    )
    monkeypatch.setattr(cs, "FREEZE_FILE", freeze)
    ran = []
    monkeypatch.setattr(cs.subprocess, "run", lambda *a, **k: ran.append(a))
    assert cs.restore(archive) == 1 and ran == []
    assert cs.sha256(archive) == hashlib.sha256(b"not the frozen corpus").hexdigest()


def test_tools_run_through_pg_exec(monkeypatch):
    monkeypatch.setenv("PG_EXEC", "docker exec -i abc")
    monkeypatch.setenv("PG_DB", "scratch")
    assert cs.pg("pg_restore", "--data-only") == [
        "docker",
        "exec",
        "-i",
        "abc",
        "pg_restore",
        "-U",
        "filingqa",
        "-d",
        "scratch",
        "--data-only",
    ]
