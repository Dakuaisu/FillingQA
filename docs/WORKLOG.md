# WORKLOG

Implementation detail, so it stays out of turn summaries. Newest last.

Findings live in `docs/OPEN.md`; the reasoning behind decisions lives in
`docs/TRADEOFFS.md`.

---

## 2026-08-30 — Phase 1 scaffold

Repo foundation: `pyproject.toml` (httpx, lxml, psycopg[binary], PyYAML; dev:
pytest, syrupy, ruff), `Makefile`, `docker-compose.yml`, `.env.example`,
`.gitignore`, `README.md`, `.github/workflows/ci.yml` (ruff check + ruff format
--check + pytest, network-marked tests excluded).

`ruff format` was found to rewrite Python code blocks inside `docs/PRD.md` --
11 blocks on the first run, including collapsing the aligned comments in the
`Document` dataclass. Added `extend-exclude = ["docs", "data"]` (F-27).

No empty module stubs created; each file is written when its contents are.

## 2026-08-30 — Step 1: migrations

`infra/migrations/0001_companies_filings.sql` — `companies`, `filings`, pgvector
extension. Deviations from PRD 8: `norm_path` (nowhere else to persist the text
that offsets index into) and `parse_error` (PRD 6.2 says quarantine and inspect;
`parse_status` alone cannot say why).

`0002_xbrl.sql` — `xbrl_facts`, `xbrl_facts_unlinked`, `xbrl_spans`. Key is
`UNIQUE NULLS NOT DISTINCT (accession, concept, period_start, period_end,
fiscal_period, unit)`. `xbrl_spans.chunk_id` deliberately omitted; `chunks` does
not exist until Phase 2.

`api/db.py` — migration runner applying `.sql` files in filename order inside a
transaction, tracked in `schema_migrations`. Verified idempotent: runs 2 and 3
both printed `no pending migrations`.

`scripts/key_sanity.sql` and `scripts/restatements.sql` — both read
`xbrl_facts UNION ALL xbrl_facts_unlinked`. Both run clean, 0 rows on an empty
database.

Environment: Postgres 18.6 running inside WSL, port-forwarded by `wslrelay.exe`,
not a Windows install -- so `psql` is reached via `wsl -e bash -lc`. Docker
Desktop would not start; abandoned in favour of the local instance.

## 2026-08-30 — Step 2: EDGAR client

`api/config.py` — single owner of `.env` loading (12 lines, no python-dotenv).
Real environment variables win over `.env`. `sec_user_agent()` raises on missing,
on no email, and on placeholder domains.

`api/ingest/rate_limit.py` — token bucket, 8 req/s. `capacity` defaults to 1
(strict pacing, no burst) and the bucket starts empty, so 20 requests cost
exactly 2.5s. Starting full would give 19 intervals = 2.375s. `clock` and `sleep`
injectable; 12 tests, one against the real clock.

`api/ingest/edgar.py` — retry policy visible in `_request`: retries
`{429, 500, 502, 503, 504}`, exponential 1/2/4/8/16s capped at 60s, `Retry-After`
wins. 403 and 404 never retried; the 403 message names the User-Agent. Disk cache
writes to a `.part` neighbour then `replace()`.

Bug caught by tests: the User-Agent was set on the constructed client, so an
injected client sent `python-httpx/0.28.1`. Now sent per request (F-31).

Live check: 4 companies resolved, `filings.recent` field list captured, cache
proven with 0 HTTP requests on a second run.

## 2026-08-30 — Step 3: filings discovery and storage

`api/ingest/filings.py` — discover, filter, download, register. Idempotent at two
layers: disk cache stops the byte download, `ON CONFLICT (accession) DO NOTHING`
stops the row.

`assert_recent_covers_window` compares the window start against the oldest date
in `filings.recent`, not the entry count. All three dev companies are AT the
~1000 cap with one paginated file each, but `recent` reaches back to 2015--2016,
so a 3-year window has ~9 years of headroom. A count-based check would have
false-alarmed on every company (F-28).

Ingested COST, TGT, AAPL for 1 year: 12 filings, 4 each (1 10-K + 3 10-Q),
12.83 MB, all 12 sha256 verified disk-vs-DB. Re-run: 0 HTTP requests, 0 new rows.

Primary document vs `.txt` bundle, AAPL FY2025 10-K: 1,520,208 bytes vs
9,392,337 bytes -- the bundle is 6.2x larger.

## 2026-08-30 — Step 4a: single-pass iXBRL extraction

`api/numbers.py` — `parse_number` handles `$7,286` / `(7,286)` / unicode minus,
en dash, em dash / non-breaking, thin and narrow no-break spaces as digit
separators. `apply_scale`, `to_base_units`, `detect_unit_scale`.

`api/parse/ixbrl.py` — one traversal emits normalized text while recording each
`ix` element's range in the text being emitted. Whitespace is collapsed as it is
written, never afterwards; collapsing afterwards would shift every offset already
recorded.

Verification built in two layers because the obvious one is nearly tautological:
`verify_spans` compares the slice against `raw_text`, which came from that slice,
so it proves only that nothing mutated the text afterwards. The independent check
re-parses with lxml, looks each element up by `id`, and compares. It initially
reported 35 mismatches, all long `nonNumeric` prose blocks differing only by the
newlines the emitter inserts at block boundaries -- the emitter is the more
faithful side -- so the comparison now ignores whitespace. Result: 0 mismatches
across all 12 filings, 7,957 numeric spans.

Bug caught: `dei:DocumentFiscalYearFocus` sits in `ix:hidden` inside a
`display:none` div, which the walker skips, so the first run reported
`fiscal_year=None`. `harvest_dei` now walks the whole tree independently (F-30).

100% of contextRefs resolve to a period in every filing. 30--56% sit on
dimensional contexts (F-32). 4--5 word-form numbers per filing do not parse and
are recorded with `value=None` rather than dropped (F-33).

Normalized text persisted to `data/norm/` -- 12 files, 1.3 MB, with sha256.

## 2026-08-30 — Step 4b: section detection

`Block` recording added to the same traversal: leaf blocks only, tables always
atomic. Spans re-verified at 0 mismatches afterwards.

`api/parse/sections.py` — detection runs on blocks, not text. PRD 6.2's suggested
`^ITEM` regex over flattened text matches only the table of contents, because
real headings render mid-line (`...employee retention. Item 1B. Unresolved Staff
Comments None. Item 1C. Cybersecurity...`) and cross-references are lexically
identical to headings. Block-based detection: 23 headings, 0 false positives, vs
61 raw text matches (F-34).

Part tracking gives `I.1` (Financial Statements) vs `II.1` (Legal Proceedings) vs
`II.1A` (Risk Factors) on the same 10-Q.

All 12 filings: 23 sections per 10-K, 11 per 10-Q, no required Item missing.
TGT's 10-K has 250 table blocks against AAPL's 54 (F-35).

## 2026-08-30 — Register correction

`docs/OPEN.md`'s summary table read OPEN 14 / RESOLVED 17 / Total 31. The tables
below it hold 22 OPEN and 17 RESOLVED, which matches F-39 as the highest ID with
no gaps. Counts corrected to 22 / 17 / 39. The register is the state file; a
stale header is the kind of number that gets quoted back later.

## 2026-10-01 — Environment moved to macOS

The Windows/WSL machine is gone. New environment: macOS, fresh clone, Docker
Desktop 29.7.2, Postgres in the `pgvector/pgvector:pg18` container (PG 18.6,
vector 0.8.6). System `python3` is 3.9 and cannot run the project; the venv is
`.venv`, Python 3.12.14, created with `uv`.

`make db-up` failed first time: pg18 images reject a volume at
`/var/lib/postgresql/data` (F-40). The compose file had never actually been run.
Mount moved to `/var/lib/postgresql`; the empty volume from the failed attempt
was reused.

`make migrate` applied 0001--0003; a second run printed `no pending migrations`.

`make test` failed collection with `No module named 'tests'` -- bare `pytest`
does not add the repo root to `sys.path`, `python -m pytest` does (F-41). CI
uses bare `pytest`, so CI had the same latent failure. Fixed with
`pythonpath = ["."]`. After the fix: 59 passed, 3 snapshots passed against the
committed baselines, no snapshot files modified.

`data/` does not survive the move (gitignored), so the dev slice must be
re-ingested from EDGAR.

## 2026-10-01 — Dev slice pinned to an accession list; re-ingested

`sec_user_agent()` passes with the `.env` on this machine.

`corpus.dev_slice` in `api/config.yaml` is now 12 explicit `{ticker, accession,
form}` entries instead of `tickers` + `years_back: 1`. `api.config.dev_slice()`
reads it. `api.ingest.filings.select_accessions` picks exactly those accessions
from `filings.recent` and raises on a missing accession (naming any paginated
files not searched), on a form that disagrees with SEC's, and on a missing
`reportDate`. `ingest_accessions` wraps it; the download/insert loop is shared
with `ingest_company` via `_store`. CLI: `python -m api.ingest.cli --dev-slice`,
mutually exclusive with `--tickers/--years`, which is kept for the eval corpus
until F-42. 5 new unit tests.

Ingest: 12 inserted (AAPL 4.1 MB, COST 3.7 MB, TGT 5.0 MB). Second run: 0
inserted, 12 already present, 0.0 MB downloaded.

Fixture comparison, all three MISMATCH on both `filings.content_hash` and the
on-disk sha256; DB and disk agree with each other; the committed `.gz` fixtures
still match the manifest. Each fresh download is exactly 114 bytes longer: SEC's
edge now appends `<script type="text/javascript" src="/jGPwwufxbVNjftpB5QEsfCYc/...">`
before `</body>`. `parse_summary` (the snapshot function) is identical between
fixture and fresh bytes for all three, because `script` is in `SKIP_TAGS`. F-43;
nothing changed.

`make test`: 64 passed, 3 snapshots passed. `make lint`: `ruff check` clean,
`ruff format --check` fails on `tools/bridge.py` only (F-44).

`.serena/` and `.omo/` added to `.gitignore`. Four files under them were already
committed and remain tracked.

F-43 and F-44 resolved by supervisor decision (TRADEOFFS 2026-10-01, AUTONOMOUS
DECISION). `[tool.ruff.format] exclude = ["tools"]` added; `make lint` now
`23 files already formatted`. `git rm -r --cached .omo .serena` removed 4 files
from the index; they remain on disk.
