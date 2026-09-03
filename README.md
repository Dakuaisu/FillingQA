# FilingQA

Citation-grounded question answering over SEC 10-K and 10-Q filings, built around
a CI-gated evaluation harness. The RAG pipeline exists to be measured; the harness
is the point. Full specification in [`docs/PRD.md`](docs/PRD.md).

**Status: Phase 1 (ingestion, parsing, XBRL) — in progress.**

No metrics are reported here yet. Numbers appear in this README only once they
have been produced by a real eval run.

## Local setup

Requires Postgres 18 with the `vector` extension available, and Python 3.11+.

```bash
python -m pip install -e ".[dev]"
cp .env.example .env      # set DATABASE_URL, and SEC_USER_AGENT to a real email
make migrate
```

`make migrate` applies everything in `infra/migrations/` in filename order and
records each file in `schema_migrations`, so re-running it is a no-op.

If you do not have a local Postgres, `make db-up` starts one in Docker
(`pgvector/pgvector:pg18`) matching the default DSN in `.env.example`.

## Development

```bash
make lint
make test
```

## Documents

- [`docs/PRD.md`](docs/PRD.md) — the specification
- [`docs/TRADEOFFS.md`](docs/TRADEOFFS.md) — decisions taken, and deferred PRD
  defects logged against the phase where they have to be resolved
