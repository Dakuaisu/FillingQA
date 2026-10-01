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

## 2026-10-01 — Step 4c: table extraction

Committed F-43/F-44/untracking as `e725d13` first; only ` M tools/bridge.py`
remained.

**Walker.** `Block.rows` added: per table, rows of `(char_start, char_end,
colspan, rowspan)` cell ranges into the normalized text. Purely additive -- the
emitted text is unchanged, and the 3 existing snapshots (`text_sha256`, span
counts, sections) pass unmodified. Never ran `--snapshot-update`.

**`api/parse/tables.py`.** Cells placed on the column grid with colspan and
rowspan; `$` / `%` / `)` fragment cells merged into their figure; logical columns
recovered by merging the column ranges of body cells (spacer columns are the
gaps). Classification: `data` if some row holds two or more figures, else
`layout` (F-35). Header rows end at the last row labelling a value column;
label-only rows after it ("ASSETS:", "Net sales:") are body. Column labels join
every header cell above a column, so AAPL's "2025" super-header labels all seven
region columns.

Bugs found against real data, each fixed and covered by a test:
- `$` + `(861)` merged to `$(861)`, which `parse_number` rejected; the cell fell
  into the label column. `parse_number` now strips a leading `$` first.
- Grouping columns on figures only folded AAPL Term Debt's maturity and rate
  columns into the row label and shifted every header. Columns now form from all
  body cells right of the label column.
- AAPL Term Debt's header was still one column left: the HTML uses `rowspan=2`.
  The walker now records rowspan and the grid honours occupied slots.
- Title fallback picked up the previous table's last row; now walks preceding
  *blocks* and stops at a table.

**Unit-scale caption.** `detect_unit_scale` (pure, 10 tests) takes the caption
nearest the table, and the scale before "except". Searches the 500 characters
before the table *plus the table's own header rows*, because TGT prints
"(millions)" inside the table, without "in". Captions naming two scales with no
"except" return None (AAPL "(net income in millions and shares in thousands)").

**12-filing split** (`miss` = iXBRL says the table is scaled, no caption found;
`noscale` also counts legitimately unscaled tables such as store counts):

    ticker accession              form  tables  data layout scale  ixsc agree disagr  miss title noscale
    AAPL   0000320193-25-000079   10-K      54    43     11    35    31    27      0     4    28       8
    AAPL   0000320193-26-000006   10-Q      29    23      6    21    16    14      0     2    19       2
    AAPL   0000320193-26-000013   10-Q      31    25      6    22    18    15      0     3    20       3
    AAPL   0000320193-26-000020   10-Q      32    26      6    23    19    16      0     3    21       3
    COST   0000909832-25-000101   10-K      56    44     12     8    29     5      0    24    27      36
    COST   0000909832-25-000169   10-Q      35    27      8     6    18     5      0    13    15      21
    COST   0000909832-26-000029   10-Q      36    28      8     7    19     6      0    13    16      21
    COST   0000909832-26-000051   10-Q      36    28      8     7    19     6      0    13    16      21
    TGT    0000027419-25-000126   10-Q     102    34     68    25    18    18      0     0    34       9
    TGT    0000027419-26-000016   10-K     250    64    186    48    41    39      0     2    62      16
    TGT    0000027419-26-000022   10-Q      95    30     65    22    16    16      0     0    30       8
    TGT    0000027419-26-000042   10-Q      97    32     65    23    16    16      0     0    32       9

TGT 10-K layout (186) inspected by text: 80 page footers ("TARGET CORPORATION |
2025 Form 10-K | 8"), ~70 running headers ("BUSINESS | Table of Contents"),
cover, signature and TOC tables, and 4 prose-in-table blocks (F-46). No data
table in the slice is scaffolding.

Caption scale vs iXBRL `scale`: **0 disagreements** across all 12 filings. COST
misses 13-24 per filing because it states units once per section (F-45).

**Independent cross-check.** iXBRL tags each figure where it prints, so the
tagged figures inside a table, in document order, must be an ordered subsequence
of the extracted cells. 266 tagged data tables across the 12 filings: all pass
(the one scratch-script miss was a `—%` nil cell the script did not read as a
dash; the committed test handles it). Committed as
`test_every_tagged_figure_survives_extraction_in_order` for the 3 fixtures.

**Tests.** `tests/unit/test_tables.py` (26) and
`tests/snapshot/test_table_extraction.py` (13, expected values written out and
hand-verified by arithmetic, see its docstring). `parse_summary` unchanged, so
no snapshot was re-blessed. `make test`: 103 passed, 3 snapshots passed.

## 2026-10-01 — F-45: iXBRL scale fallback; scale_source

Step 4c committed as `c2c9f51`. Six departures accepted by the supervisor; the
TRADEOFFS heading now carries "AUTONOMOUS DECISION - owner to review".

`ixbrl_scale(scales)` (pure, 10 tests from real scale combinations) returns the
table's scale when its tagged figures carry exactly one magnitude (3/6/9);
0 and -2 do not count. `extract_table` takes the caption first, then that, else
None, and sets `scale_source` on both `Table` and `Block`.

Bug found while hand-checking the fallback tables: AAPL 10-Q segment tables stack
two period blocks, and the mid-table "Six Months Ended March 29, 2025" header
spans every region column, so column grouping merged all seven into one cell.
The iXBRL order check could not see it -- the figures were in order, just in the
same cell. Columns now form from figures and dashes first; a text cell joins
only if it does not bridge two figure columns. Term Debt unaffected. New
invariant test: no value cell holds several figures (0 of 404 data tables in the
slice after the fix). Known limitation: in a stacked table, column labels come
from the first block; the second block's header renders as body rows.

**12-filing table, post-fallback.** `caption`/`ixbrl` = scale source; `miss` =
tagged with a magnitude but no scale (all mixed-magnitude); `noscale` = data
tables with no scale = `mixed` + `untagd` (no caption and no tagged magnitude).

    ticker accession              form  tables  data layout caption ixbrl  ixsc disagr  miss noscale mixed untagd
    AAPL   0000320193-25-000079   10-K      54    43     11      35     3    31      0     1       5     1      4
    AAPL   0000320193-26-000006   10-Q      29    23      6      21     1    16      0     1       1     1      0
    AAPL   0000320193-26-000013   10-Q      31    25      6      22     2    18      0     1       1     1      0
    AAPL   0000320193-26-000020   10-Q      32    26      6      23     2    19      0     1       1     1      0
    COST   0000909832-25-000101   10-K      56    44     12       8    22    29      0     2      14     2     12
    COST   0000909832-25-000169   10-Q      35    27      8       6    11    18      0     2      10     2      8
    COST   0000909832-26-000029   10-Q      36    28      8       7    11    19      0     2      10     2      8
    COST   0000909832-26-000051   10-Q      36    28      8       7    11    19      0     2      10     2      8
    TGT    0000027419-25-000126   10-Q     102    34     68      25     0    18      0     0       9     0      9
    TGT    0000027419-26-000016   10-K     250    64    186      48     2    41      0     0      14     0     14
    TGT    0000027419-26-000022   10-Q      95    30     65      22     0    16      0     0       8     0      8
    TGT    0000027419-26-000042   10-Q      97    32     65      23     0    16      0     0       9     0      9

COST `miss` fell from 24/13/13/13 to 2/2/2/2. Caption vs iXBRL: still 0
disagreements. `parse_summary` unchanged; no snapshot re-blessed. `make test`:
121 passed, 3 snapshots passed.

## 2026-10-01 — Step 5: companyfacts ingestion; sector wiring (F-39)

F-45 committed as `47260a5`.

`api/ingest/xbrl_facts.py`: `flatten` turns companyfacts into one `Fact` per
`facts/{taxonomy}/{concept}/units/{unit}` row, concept written `us-gaap:X` like an
ix `name` so facts and spans join. Values in base units as reported, never
rescaled. `load_companyfacts` raises on any key carrying two values in the
payload, and on any stored fact whose value companyfacts has since changed -- ON
CONFLICT DO NOTHING alone would hide that drift. Linked facts get
`is_comparative = period_end < filing.period_end`. Wired into the ingest CLI after
each company's filings, so facts can link to them.

`EdgarClient.fetch_json(exact=True)` for companyfacts parses decimals as
`Decimal`; plain `json.loads` would have stored 7.46 as a float.

Profiled before loading (AAPL / COST / TGT): 25,135 / 24,426 / 25,319 facts over
72 / 67 / 73 accessions. `fy` is null on 569 / 0 / 49 facts, all from 8-K, DEF
14A, S-3ASR or S-8, none in the slice -> migration 0004 makes
`xbrl_facts_unlinked.fiscal_year` nullable; `xbrl_facts` keeps NOT NULL. `fp`
includes `Q4` (601 COST facts) and null, which the PRD's enumeration does not
list. Taxonomies beyond us-gaap/dei: `srt`, `ecd`, `ffd`. **0 key conflicts**
under the period_start-inclusive key across ~75k facts.

Run 1: linked 1,186 / 1,287 / 1,408 (exactly the per-accession counts profiled:
AAPL 427+203+273+283), unlinked 23,949 / 23,139 / 23,911. Run 2: 0 inserted,
everything present. `companies.sector`: AAPL tech, COST retail, TGT retail;
`sector_of` raises on a ticker with no label rather than writing NULL.

`key_sanity.sql`: 50 rows, periods reported by up to 12 accessions -- only
possible with accession in the key.

`restatements.sql` bug: grouped on `(cik, concept, period_end)` only, so a quarter
and the YTD figure ending the same day were two "values" -- 5,146 rows. Now
groups on unit and period_start too: 1,390 rows. Still not a restatement count
(F-47): TGT 2016 equity 12,957M -> 12,965M from the FY2018 10-K is a real
restatement; AAPL LongTermDebt 90,678M vs 90,700M is one balance printed exactly
and rounded, and companyfacts drops `decimals`.

**Trap 2 cross-check.** For each linked fact, the filing's own non-dimensional
iXBRL span with the same concept and period:

    ticker accession              facts match mismat nospan
    AAPL   0000320193-25-000079     427   427      0      0
    AAPL   0000320193-26-000006     203   203      0      0
    AAPL   0000320193-26-000013     273   273      0      0
    AAPL   0000320193-26-000020     283   283      0      0
    COST   0000909832-25-000101     489   477      0     12
    COST   0000909832-25-000169     225   208      0     17
    COST   0000909832-26-000029     289   272      0     17
    COST   0000909832-26-000051     284   267      0     17
    TGT    0000027419-25-000126     323   314      0      9
    TGT    0000027419-26-000016     533   520      0     13
    TGT    0000027419-26-000022     241   233      0      8
    TGT    0000027419-26-000042     311   303      0      8

3,780 match exactly in base units, 0 mismatch. The 101 `nospan` facts were
checked in the raw XML: tagged only inside `ix:hidden` (shares authorized, par
value, segment counts), which has no rendered position (F-48).

Tests: `tests/unit/test_xbrl_facts.py` (11, real AAPL rows), one Decimal test in
`test_edgar.py`. `make test`: 133 passed, 3 snapshots passed.
