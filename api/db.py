"""Postgres connection and migration runner.

Migrations are plain .sql files in infra/migrations/, applied in filename order.
Each is applied once, inside a transaction, and recorded in schema_migrations --
so a partial failure leaves no half-applied file behind and re-running is a no-op.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import psycopg

from api.config import MIGRATIONS_DIR, dsn

_SCHEMA_MIGRATIONS_DDL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename    TEXT PRIMARY KEY,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""


def connect() -> psycopg.Connection:
    return psycopg.connect(dsn())


def migration_files() -> list[Path]:
    """Migrations in filename order. The numeric prefix is the ordering."""
    return sorted(MIGRATIONS_DIR.glob("*.sql"))


def applied(conn: psycopg.Connection) -> set[str]:
    with conn.cursor() as cur:
        cur.execute(_SCHEMA_MIGRATIONS_DDL)
        cur.execute("SELECT filename FROM schema_migrations")
        return {row[0] for row in cur.fetchall()}


def migrate(conn: psycopg.Connection) -> Iterator[str]:
    """Apply pending migrations in order. Yields the filename of each one applied."""
    done = applied(conn)
    conn.commit()

    for path in migration_files():
        if path.name in done:
            continue
        sql = path.read_text(encoding="utf-8")
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "INSERT INTO schema_migrations (filename) VALUES (%s)",
                (path.name,),
            )
        conn.commit()
        yield path.name


def main() -> None:
    with connect() as conn:
        pending = list(migrate(conn))

    if pending:
        for name in pending:
            print(f"applied {name}")
    else:
        print("no pending migrations")


if __name__ == "__main__":
    main()
