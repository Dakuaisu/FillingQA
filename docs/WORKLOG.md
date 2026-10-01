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

## 2026-10-01 — F-45 monetary veto

Step 5 committed as `368f781` (F-49 filed Non-blocking: 0 linked facts have null
or Q4 `fp`; all 618 null and 601 Q4 are unlinked).

`parse_units` resolves each `xbrli:unit`'s measures through the element's nsmap,
like contexts. `Unit.is_monetary`: one iso4217 measure, no denominator.
`ixbrl_scale` takes (scale, is_monetary) pairs and returns (scale, conflict); a
currency figure off the chosen magnitude gives (None, True), logged and stored as
`Table.scale_conflict`.

Re-measured (`ix{..}` = iXBRL-fallback tables by raw scale set; `capt_offscale$`
= captioned tables holding a currency figure at another scale, for information):

    ticker accession              form  data capt ixbrl ix{6} ix{0,6} ix{-2,6} ixother veto miss noscl capt_offscale$
    AAPL   0000320193-25-000079   10-K    43   35     3     3       0        0       0    0    1     5              0
    AAPL   0000320193-26-000006   10-Q    23   21     1     1       0        0       0    0    1     1              0
    AAPL   0000320193-26-000013   10-Q    25   22     2     2       0        0       0    0    1     1              0
    AAPL   0000320193-26-000020   10-Q    26   23     2     2       0        0       0    0    1     1              0
    COST   0000909832-25-000101   10-K    44    8    22    19       0        2       1    0    2    14              0
    COST   0000909832-25-000169   10-Q    27    6    11     9       0        1       1    0    2    10              0
    COST   0000909832-26-000029   10-Q    28    7    11     9       0        1       1    0    2    10              0
    COST   0000909832-26-000051   10-Q    28    7    11     9       0        1       1    0    2    10              0
    TGT    0000027419-25-000126   10-Q    34   25     0     0       0        0       0    0    0     9              0
    TGT    0000027419-26-000016   10-K    64   48     2     0       0        0       2    0    0    14              0
    TGT    0000027419-26-000022   10-Q    30   22     0     0       0        0       0    0    0     8              0
    TGT    0000027419-26-000042   10-Q    32   23     0     0       0        0       0    0    0     9              0

Veto fired 0 times; no fallback table flipped. Caption-less {0,6}: 0, {-2,6}: 5.
`ixother` is {0,3} (RSU/PSU unit tables). F-47 moved to Blocking Phase 5; the
`restatements.sql` header now speaks of rows, not restatements. `make test`: 139
passed, 3 snapshots passed.

## 2026-10-01 — Step 6: parser validation suite and parse-quality score

Monetary veto committed as `411cb47`.

`api/parse/validate.py`: `measure` (quantities the parser already produces),
`check` (assertions; any failure quarantines), `score` (tracked, never gates).
The runner parses every filing, writes normalized text to `data/norm/`, and
updates `filings`: `parse_status`, `parse_error`, `parse_score`,
`parser_version`, `norm_path`, `fiscal_year`, `fiscal_quarter` -- the last four
written for the first time. Bounds read from `api/config.yaml` `parser:`.

`python -m api.parse.validate` (`scale`/`uncol`/`spans`/`items` are score
components; alpha_in_bounds is 1 for all):

    parser_version bfe5929c604b
    ticker accession              form   FY fp sect miss data alpha scale uncol spans items score  status
    AAPL   0000320193-25-000079   10-K 2025 FY   23    0   43 0.765 0.974 1.000 0.995 1.000 0.994  parsed
    AAPL   0000320193-26-000006   10-Q 2026 Q1   11    0   23 0.722 0.957 1.000 0.993 1.000 0.990  parsed
    AAPL   0000320193-26-000013   10-Q 2026 Q2   11    0   25 0.733 0.960 1.000 0.995 1.000 0.991  parsed
    AAPL   0000320193-26-000020   10-Q 2026 Q3   11    0   26 0.728 0.962 1.000 0.995 1.000 0.991  parsed
    COST   0000909832-25-000101   10-K 2025 FY   23    0   44 0.779 0.938 1.000 0.994 1.000 0.986  parsed
    COST   0000909832-25-000169   10-Q 2026 Q1   11    0   27 0.756 0.895 1.000 0.988 1.000 0.976  parsed
    COST   0000909832-26-000029   10-Q 2026 Q2   11    0   28 0.738 0.900 1.000 0.991 1.000 0.978  parsed
    COST   0000909832-26-000051   10-Q 2026 Q3   11    0   28 0.737 0.900 1.000 0.991 1.000 0.978  parsed
    TGT    0000027419-25-000126   10-Q 2025 Q3   11    0   34 0.720 1.000 1.000 0.983 1.000 0.997  parsed
    TGT    0000027419-26-000016   10-K 2025 FY   23    0   64 0.774 1.000 1.000 0.987 1.000 0.997  parsed
    TGT    0000027419-26-000022   10-Q 2026 Q1   11    0   30 0.736 1.000 1.000 0.980 1.000 0.996  parsed
    TGT    0000027419-26-000042   10-Q 2026 Q2   11    0   32 0.720 1.000 1.000 0.979 1.000 0.996  parsed

Second run identical. `validate.py` itself is excluded from the version hash --
it measures parser output and does not produce it. DB: 12 `parsed`, 1 parser_version, 12 norm_paths, 12
fiscal years. Spot checks: AAPL 10-K scale 38/39 (the miss is the mixed EPS
note); COST 10-K 30/32; TGT's 2025-11-01 10-Q is its own Q3 FY2025.

Nothing quarantined on the slice, so every assertion is exercised in
`tests/unit/test_validate.py` by moving one measured quantity across its bound
(24 tests; baseline record = the AAPL 10-K as measured, checked against the
fixture).

## 2026-10-01 — xbrl_spans written; Phase 1 exit check

Step 6 committed as `35ff6e7`.

**xbrl_spans.** `span_rows(doc, accession)` (pure) builds rows from numeric spans
with a parsed value; `validate_filing` deletes and rewrites them by accession in
the same transaction as the `filings` update, after writing `norm_path`. The
runner commits its initial read so each filing's `conn.transaction()` is a real
transaction, not a savepoint. A quarantined filing gets its spans deleted and
none written -- shown by forcing `min_sections: 99` on COST 0000909832-26-000051:
`('quarantined', '11 sections < 99', 0)`, then re-validating restored
`('parsed', None, 570)`. Re-run: 7,877 rows before and after.

`python -m api.parse.validate` (`rows` = spans written, `skip` = word-form spans
without a value, F-33):

    parser_version bfe5929c604b
    ticker accession              form   FY fp sect miss data alpha scale uncol spans items score  rows skip  status
    AAPL   0000320193-25-000079   10-K 2025 FY   23    0   43 0.765 0.974 1.000 0.995 1.000 0.994   962    5  parsed
    AAPL   0000320193-26-000006   10-Q 2026 Q1   11    0   23 0.722 0.957 1.000 0.993 1.000 0.990   554    4  parsed
    AAPL   0000320193-26-000013   10-Q 2026 Q2   11    0   25 0.733 0.960 1.000 0.995 1.000 0.991   750    4  parsed
    AAPL   0000320193-26-000020   10-Q 2026 Q3   11    0   26 0.728 0.962 1.000 0.995 1.000 0.991   756    4  parsed
    COST   0000909832-25-000101   10-K 2025 FY   23    0   44 0.779 0.938 1.000 0.994 1.000 0.986   818    5  parsed
    COST   0000909832-25-000169   10-Q 2026 Q1   11    0   27 0.756 0.895 1.000 0.988 1.000 0.976   395    5  parsed
    COST   0000909832-26-000029   10-Q 2026 Q2   11    0   28 0.738 0.900 1.000 0.991 1.000 0.978   571    5  parsed
    COST   0000909832-26-000051   10-Q 2026 Q3   11    0   28 0.737 0.900 1.000 0.991 1.000 0.978   570    5  parsed
    TGT    0000027419-25-000126   10-Q 2025 Q3   11    0   34 0.720 1.000 1.000 0.983 1.000 0.997   576   10  parsed
    TGT    0000027419-26-000016   10-K 2025 FY   23    0   64 0.774 1.000 1.000 0.987 1.000 0.997   977   13  parsed
    TGT    0000027419-26-000022   10-Q 2026 Q1   11    0   30 0.736 1.000 1.000 0.980 1.000 0.996   401    8  parsed
    TGT    0000027419-26-000042   10-Q 2026 Q2   11    0   32 0.720 1.000 1.000 0.979 1.000 0.996   547   12  parsed

### Exit check 1 -- offsets on stored rows

`python -m scripts.check_stored_spans` reads every row back from Postgres and
slices the file at `norm_path`:

    ticker accession               rows mismatch out_of_range
    AAPL   0000320193-25-000079     962        0            0
    AAPL   0000320193-26-000006     554        0            0
    AAPL   0000320193-26-000013     750        0            0
    AAPL   0000320193-26-000020     756        0            0
    COST   0000909832-25-000101     818        0            0
    COST   0000909832-25-000169     395        0            0
    COST   0000909832-26-000029     571        0            0
    COST   0000909832-26-000051     570        0            0
    TGT    0000027419-25-000126     576        0            0
    TGT    0000027419-26-000016     977        0            0
    TGT    0000027419-26-000022     401        0            0
    TGT    0000027419-26-000042     547        0            0
    total rows 7877, mismatches 0

### Exit check 2 -- PRD 6.5.2 restatement query, as written

        cik     |                                    concept                                    | period_end | variants 
    ------------+-------------------------------------------------------------------------------+------------+----------
     0000027419 | us-gaap:AntidilutiveSecuritiesExcludedFromComputationOfEarningsPerShareAmount | 2025-08-02 |        2
     0000027419 | us-gaap:AntidilutiveSecuritiesExcludedFromComputationOfEarningsPerShareAmount | 2026-08-01 |        2
     0000027419 | us-gaap:ChangeInUnrealizedGainLossOnFairValueHedgingInstruments1              | 2024-11-02 |        2
     0000027419 | us-gaap:ChangeInUnrealizedGainLossOnFairValueHedgingInstruments1              | 2025-08-02 |        2
     0000027419 | us-gaap:ChangeInUnrealizedGainLossOnFairValueHedgingInstruments1              | 2025-11-01 |        2
    (5 rows)

It returns rows. As written it has no `period_start`, so its first rows are
quarter-vs-YTD pairs ending on one date; `scripts/restatements.sql` is the
corrected form. No restatement count is stated (F-47).

### Exit check 3 -- hand inspection, all 12 filings

Per filing: the first financial-statement data table, one more chosen with a
seed of the accession, and three stored spans sampled the same way, each with
the text around its offset (`DIM` = dimensional context). Done by the builder;
the owner should repeat it on these samples against the printed filings.

    === AAPL 0000320193-25-000079 10-K
      TABLE 'CONSOLIDATED STATEMENTS OF OPERATIONS' [Item 8] scale=millions source=caption
        header: ['', 'Years ended September 27, 2025', 'Years ended September 28, 2024', 'Years ended September 30, 2023']
        row1:   ['Net sales:', '', '', '']
      TABLE None [Item 7] scale=millions source=caption
        header: ['', '', '', '']
        row1:   ['Gross margin percentage:', '', '', '']
      SPAN [164695:164701] slice='78,328' value=78328000000 scale=6 us-gaap:LongTermDebtNoncurrent 2025-09-27
        ...(12,350) (10,912) Total non-current portion of term debt $ 78,328 $ 85,750 To m
      SPAN [144057:144058] slice='—' value=0 scale=6 us-gaap:AvailableForSaleDebtSecuritiesAccumulatedGrossUnrealizedGainBeforeTax 2025-09-27 DIM
        ...82) 15,848 1,190 3,712 10,946 U.S. agency securities 5,269 — (149) 5,120 25
      SPAN [161057:161062] slice='1,033' value=1033000000 scale=6 us-gaap:FinanceLeaseRightOfUseAsset 2025-09-27
        ...$ 10,234 Finance leases Property, plant and equipment, net 1,033 1,069 Total r
    === AAPL 0000320193-26-000006 10-Q
      TABLE 'CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS (Unaudited)' [Part I, Item 1] scale=millions source=caption
        header: ['', 'Three Months Ended December 27, 2025', 'Three Months Ended December 28, 2024']
        row1:   ['Net sales:', '', '']
      TABLE 'Operating Expenses' [Part I, Item 2] scale=millions source=caption
        header: ['', 'Three Months Ended December 27, 2025', 'Three Months Ended December 28, 2024', 'Three Months Ended Change']
        row1:   ['Research and development', '$10,887', '$8,268', '32%']
      SPAN [7175:7181] slice='88,190' value=88190000000 scale=6 us-gaap:StockholdersEquity 2025-12-27
        ...prehensive loss (4,854) (5,571) Total shareholders’ equity 88,190 73,733 Total
      SPAN [14505:14508] slice='195' value=195000000 scale=6 aapl:EquitySecuritiesFVNIAccumulatedGrossUnrealizedGainBeforeTax 2025-12-27 DIM
        ...9 — — Mutual funds 792 195 (2) 985 — 985 — Subtotal 6,751 195 (2) 6,944 5,95
      SPAN [15824:15826] slice='13' value=13000000 scale=6 us-gaap:MarketableSecuritiesNoncurrent 2025-09-27 DIM
        ...Certificates of deposit and time deposits 917 — — 917 904 — 13 Commercial pa
    === AAPL 0000320193-26-000013 10-Q
      TABLE 'CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS (Unaudited)' [Part I, Item 1] scale=millions source=caption
        header: ['', 'Three Months Ended March 28, 2026', 'Three Months Ended March 29, 2025', 'Six Months Ended March 28, 2026', 'Six Months Ended March 29, 2025']
        row1:   ['Net sales:', '', '', '', '']
      TABLE None [Part I, Item 1] scale=millions source=caption
        header: ['', 'March 28, 2026', 'September 27, 2025']
        row1:   ['Derivative instruments designated as accounting hedges:', '', '']
      SPAN [6770:6776] slice='21,334' value=21334000000 scale=6 aapl:IntangibleAssetsNetExcludingGoodwillNoncurrent 2026-03-28
        ...nt and equipment, net 50,116 49,834 Intangible assets, net 21,334 11,093 Other
      SPAN [17377:17380] slice='119' value=119000000 scale=6 us-gaap:MarketableSecuritiesCurrent 2025-09-27 DIM
        ...6,560 — 10,623 35,937 Municipal securities 207 — (2) 205 — 119 86 Mortgage-
      SPAN [7299:7306] slice='119,877' value=119877000000 scale=6 us-gaap:LiabilitiesNoncurrent 2025-09-27
        ...lities 55,546 41,549 Total non-current liabilities 129,950 119,877 Total liabili
    === AAPL 0000320193-26-000020 10-Q
      TABLE 'CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS (Unaudited)' [Part I, Item 1] scale=millions source=caption
        header: ['', 'Three Months Ended June 27, 2026', 'Three Months Ended June 28, 2025', 'Nine Months Ended June 27, 2026', 'Nine Months Ended June 28, 2025']
        row1:   ['Net sales:', '', '', '', '']
      TABLE 'March 29, 2026 to May 2, 2026:' [Part II, Item 2] scale=millions source=caption
        header: ['Periods Open market and privately negotiated purchases', 'Total Number of Shares Purchased —', '', 'Average Price Paid Per Share $—', 'Total Number of Shares Purchased as Part of Publicly Announced Plans or Programs —', '', 'Approximate
        row1:   ['May 3, 2026 to May 30, 2026:', '', '', '', '', '', '']
      SPAN [29424:29430] slice='13,995' value=13995000000 scale=6 us-gaap:OperatingIncomeLoss 2025-09-28..2026-06-27 DIM
        ...erating income/(loss) $ 65,027 $ 44,285 $ 28,387 $ 11,456 $ 13,995 $ (40,718) $ 1
      SPAN [17230:17233] slice='100' value=100000000 scale=6 us-gaap:AvailableForSaleDebtSecuritiesAmortizedCostBasis 2025-09-27 DIM
        ...it and time deposits 917 — — 917 904 — 13 Commercial paper 100 — — 100 50 50
      SPAN [10039:10044] slice='1,223' value=-1223000000 scale=6 us-gaap:IncreaseDecreaseInInventories 2024-09-29..2025-06-28
        ...dor non-trade receivables 5,671 13,555 Inventories (5,461) 1,223 Other current
    === COST 0000909832-25-000101 10-K
      TABLE None [Item 1] scale=thousands source=caption
        header: ['', '2025', '2024', '2023']
        row1:   ['Gold Star', '68,300', '63,700', '58,800']
      TABLE 'Gross Margin' [Item 7] scale=None source=None
        header: ['', '2025', '2024', '2023']
        row1:   ['Net sales', '$269,912', '$249,625', '$237,710']
      SPAN [172299:172302] slice='135' value=135000000 scale=6 us-gaap:FinanceLeaseLiabilityPaymentsDueYearThree 2025-08-31
        ...(1) Finance Leases 2026 $ 267 $ 133 2027 250 132 2028 235 135 2029 204 122
      SPAN [172884:172886] slice='15' value=15 scale=0 us-gaap:CommonStockDividendsPerShareDeclared 2023-09-04..2024-09-01 DIM
        ...in 2024. Dividends in 2024 included a special dividend of $15 per share, res
      SPAN [127624:127629] slice='2,426' value=2426000000 scale=6 us-gaap:DepreciationDepletionAndAmortization 2024-09-02..2025-08-31
        ...ided by operating activities: Depreciation and amortization 2,426 2,237 2,077 N
    === COST 0000909832-25-000169 10-Q
      TABLE 'CONDENSED CONSOLIDATED STATEMENTS OF INCOME' [Part I, Item 1] scale=millions source=caption
        header: ['', '12 Weeks Ended November 23, 2025', '12 Weeks Ended November 24, 2024']
        row1:   ['REVENUE', '', '']
      TABLE 'Disaggregated Revenue' [Part I, Item 1] scale=millions source=ixbrl
        header: ['', '12 Weeks Ended November 23, 2025', '12 Weeks Ended November 24, 2024']
        row1:   ['Foods and Sundries', '$26,943', '$25,062']
      SPAN [31916:31919] slice='163' value=163000000 scale=6 us-gaap:SegmentExpenditureAdditionToLongLivedAssets 2024-09-02..2024-11-24 DIM
        ...tization $ 84 $ 75 Additions to property and equipment 160 163 Total Deprec
      SPAN [3794:3800] slice='60,985' value=60985000000 scale=6 us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax 2024-09-02..2024-11-24 DIM
        ...er 23, 2025 November 24, 2024 REVENUE Net sales $ 65,978 $ 60,985 Membership fe
      SPAN [30981:30986] slice='8,481' value=8481000000 scale=6 us-gaap:CostOfGoodsAndServicesSold 2025-09-01..2025-11-23 DIM
        ...rnational Total revenue $ 9,665 $ 8,659 Merchandise costs 8,481 7,620 Selling
    === COST 0000909832-26-000029 10-Q
      TABLE 'CONDENSED CONSOLIDATED STATEMENTS OF INCOME' [Part I, Item 1] scale=millions source=caption
        header: ['', '12 Weeks Ended February 15, 2026', '12 Weeks Ended February 16, 2025', '24 Weeks Ended February 15, 2026', '24 Weeks Ended February 16, 2025']
        row1:   ['REVENUE', '', '', '', '']
      TABLE None [Part I, Item 1] scale=millions source=ixbrl
        header: ['', 'Available-For-Sale Cost Basis', 'Available-For-Sale Fair Value', 'Held-To-Maturity']
        row1:   ['Due in one year or less', '$102', '$102', '$56']
      SPAN [10311:10314] slice='137' value=137000000 scale=6 cost:OperatingandFinancingLeaseRightofUseAssetAmortization 2024-09-02..2025-02-16
        ...on and amortization 1,194 1,100 Non-cash lease expense 149 137 Stock-based c
      SPAN [36262:36267] slice='3,206' value=3206000000 scale=6 us-gaap:PropertyPlantAndEquipmentNet 2026-02-15 DIM
        ...assets 60,142 54,862 Canada Property and equipment, net $ 3,206 $ 2,930 Total
      SPAN [35905:35908] slice='552' value=552000000 scale=6 us-gaap:DepreciationDepletionAndAmortization 2024-11-25..2025-02-16
        ...1 133 281 296 Total Depreciation and amortization $ 597 $ 552 $ 1,194 $ 1,10
    === COST 0000909832-26-000051 10-Q
      TABLE 'CONDENSED CONSOLIDATED STATEMENTS OF INCOME' [Part I, Item 1] scale=millions source=caption
        header: ['', '12 Weeks Ended May 10, 2026', '12 Weeks Ended May 11, 2025', '36 Weeks Ended May 10, 2026', '36 Weeks Ended May 11, 2025']
        row1:   ['REVENUE', '', '', '', '']
      TABLE 'Note 4—Debt' [Part I, Item 1] scale=millions source=ixbrl
        header: ['', 'May 10, 2026', 'August 31, 2025']
        row1:   ['3.000% Senior Notes due May 2027', '$1,000', '$1,000']
      SPAN [7215:7220] slice='2,192' value=2192000000 scale=6 us-gaap:NetIncomeLoss 2026-02-16..2026-05-10
        ...8,570 $ (1,606) $ 25,121 $ 32,087 Net income — — — — 2,192 2,192 Foreign-curre
      SPAN [9579:9582] slice='658' value=658000 scale=3 us-gaap:StockRepurchasedAndRetiredDuringPeriodShares 2024-09-02..2025-05-11 DIM
        ...fects 1,051 — (392) — — (392) Repurchases of common stock (658) — (12) — (611
      SPAN [35567:35573] slice='63,205' value=63205000000 scale=6 us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax 2025-02-17..2025-05-11
        ...436 $ 367 $ 1,344 $ 1,101 Total Total revenue $ 70,527 $ 63,205 $ 207,431 $ 18
    === TGT 0000027419-25-000126 10-Q
      TABLE 'Consolidated Statements of Operations' [Part I, Item 1] scale=millions source=caption
        header: ['', 'Three Months Ended November 1, 2025', 'Three Months Ended November 2, 2024', 'Nine Months Ended November 1, 2025', 'Nine Months Ended November 2, 2024']
        row1:   ['Net sales', '$25,270', '$25,668', '$74,327', '$75,651']
      TABLE 'Comparable Sales by Channel' [Part I, Item 2] scale=None source=None
        header: ['Comparable Sales by Channel', 'Three Months Ended November 1, 2025', 'Three Months Ended November 2, 2024', 'Nine Months Ended November 1, 2025', 'Nine Months Ended November 2, 2024']
        row1:   ['Stores originated comparable sales change', '(3.8)%', '(1.9)%', '(4.2)%', '(2.0)%']
      SPAN [25826:25828] slice='19' value=19000000 scale=6 us-gaap:DefinedBenefitPlanServiceCost 2024-08-04..2024-11-02
        ...r 2, 2024 Service cost benefits earned SG&A Expenses $ 18 $ 19 $ 55 $ 58 Int
      SPAN [5520:5525] slice='3,822' value=3822000000 scale=6 us-gaap:CashCashEquivalentsAndShortTermInvestments 2025-11-01
        ..., 2025 November 2, 2024 Assets Cash and cash equivalents $ 3,822 $ 4,762 $ 3,43
      SPAN [4150:4153] slice='115' value=115000000 scale=6 us-gaap:InterestExpenseNonoperating 2025-08-03..2025-11-01
        ...perating income 948 1,168 3,737 4,099 Net interest expense 115 105 346 321 N
    === TGT 0000027419-26-000016 10-K
      TABLE 'Net Sales' [Item 1] scale=billions source=caption
        header: ['2023 (53 weeks)', '2024 (52 weeks)', '2025 (52 weeks)']
        row1:   ['$107.4', '$106.6', '$104.8']
      TABLE 'Effect of Hedges on Debt' [Item 8] scale=millions source=caption
        header: ['Effect of Hedges on Debt (millions)', 'January 31, 2026', 'February 1, 2025']
        row1:   ['Long-term debt and other borrowings', '', '']
      SPAN [194862:194865] slice='231' value=231000000 scale=6 us-gaap:DeferredTaxLiabilitiesOther 2026-01-31
        ...eased assets (1,374) (1,425) Inventory (591) (484) Other (231) (203) Total
      SPAN [193732:193734] slice='43' value=43000000 scale=6 us-gaap:DeferredStateAndLocalIncomeTaxExpenseBenefit 2023-01-29..2024-02-03
        ...17 1,350 861 Deferred: Federal (72) (184) 256 State 11 2 43 International
      SPAN [196366:196369] slice='352' value=352000000 scale=6 us-gaap:UnrecognizedTaxBenefits 2024-02-03
        ...ements (1) (23) (4) Balance at end of period $ 436 $ 433 $ 352 If we were to
    === TGT 0000027419-26-000022 10-Q
      TABLE 'Consolidated Statements of Operations' [Part I, Item 1] scale=millions source=caption
        header: ['', 'Three Months Ended May 2, 2026', 'Three Months Ended May 3, 2025']
        row1:   ['Net sales', '$25,443', '$23,846']
      TABLE 'Merchandise Sales by Product Category' [Part I, Item 2] scale=None source=None
        header: ['Merchandise Sales by Product Category', 'Three Months Ended May 2, 2026', 'Three Months Ended May 3, 2025']
        row1:   ['Apparel & accessories', '16%', '16%']
      SPAN [13000:13003] slice='173' value=173000000 scale=6 us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax 2026-02-01..2026-05-02 DIM
        ...revenue 246 163 Credit card profit sharing 130 141 Other 173 137 Net sales
      SPAN [12772:12777] slice='3,522' value=3522000000 scale=6 us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax 2026-02-01..2026-05-02 DIM
        ...1 Food & beverage (c) 6,263 5,902 Hardlines (Fun 101) (d) 3,522 3,074 Home fu
      SPAN [4014:4017] slice='116' value=116000000 scale=6 us-gaap:InterestExpenseNonoperating 2025-02-02..2025-05-03
        ...655 Operating income 1,135 1,472 Net interest expense 117 116 Net other inc
    === TGT 0000027419-26-000042 10-Q
      TABLE 'Consolidated Statements of Operations' [Part I, Item 1] scale=millions source=caption
        header: ['', 'Three Months Ended August 1, 2026', 'Three Months Ended August 2, 2025', 'Six Months Ended August 1, 2026', 'Six Months Ended August 2, 2025']
        row1:   ['Net sales', '$26,539', '$25,211', '$51,982', '$49,057']
      TABLE 'Analysis of Results of Operations' [Part I, Item 2] scale=millions source=caption
        header: ['Summary of Operating Income', 'Three Months Ended August 1, 2026', 'Three Months Ended August 2, 2025', 'Change', 'Six Months Ended August 1, 2026', 'Six Months Ended August 2, 2025', 'Change']
        row1:   ['Net sales', '$26,539', '$25,211', '5.3%', '$51,982', '$49,057', '6.0%']
      SPAN [9392:9395] slice='529' value=529000000 scale=6 us-gaap:DividendsCommonStock 2025-05-04..2025-08-02
        ...(6) (6) Dividends declared, $1.14 per share — — — (529) — (529) Share-based
      SPAN [27180:27183] slice='835' value=835000000 scale=6 us-gaap:IncomeTaxExpenseBenefit 2026-02-01..2026-08-01 DIM
        ...2,459 1,218 3,493 2,600 Provision for income taxes 582 283 835 629 Net earni
      SPAN [10717:10720] slice='539' value=539000000 scale=6 us-gaap:DividendsCommonStock 2026-05-03..2026-08-01 DIM
        ...ome — — — — 1 1 Dividends declared, $1.16 per share — — — (539) — (539) Shar

Read against the surrounding text, every span's slice, value and scale agree,
including signs (AAPL `IncreaseDecreaseInInventories` prints 1,223 and stores
-1,223,000,000: a decrease is a positive cash adjustment, XBRL-negative).
Implausible, now in OPEN.md:
- F-50: AAPL 10-K "Gross margin percentage:" table has no column labels -- a
  continuation, faithful to the HTML -- and carries "in millions" from the
  preceding table's caption although it holds only percentages. Measured: 11 of
  404 data tables header-less, 4 all-percentage tables scaled.
- F-51: AAPL 10-Q 0000320193-26-000020 share-repurchase table took its dash-only
  first data row as a header. 1 table.
- F-52: TGT 10-K "Net Sales" chart table has no label column; "2023 (53 weeks)"
  drops out of `fiscal_periods`. 1 table.
Not implausible: COST 10-K "Gross Margin" (MD&A) with no scale is the known F-45
residual.

### Exit check 4

    $ make test
    --------------------------- snapshot report summary ----------------------------
    3 snapshots passed.
    166 passed in 6.61s
    $ make lint
    ruff check .
    All checks passed!
    ruff format --check .
    32 files already formatted

## 2026-10-01 — F-50, F-51 fixed before chunking

Phase 1 exit accepted at `8f9faed`.

`_caption_window_start`: the caption window begins no earlier than the end of the
nearest preceding table. `_first_body_row`: a row whose cells right of the label
column are all dashes (`—`, `$—`, `—%`) is a body row.

Before/after over all 404 data tables on the 12 filings:
- `text_sha256`: unchanged on all 12.
- `parser_version`: bfe5929c604b -> 671106d02317.
- Header rows changed: **1** (AAPL 0000320193-26-000020 share repurchases).
- Scale changed: 17 -- 8 percentage tables millions -> None (AAPL gross margin
  percentage x4, TGT Rate Analysis x3, TGT Assumptions), 5 AAPL continuations
  caption -> iXBRL (still millions), 4 TGT ROIC "Denominator" tables
  millions -> None. My F-50 prevalence count had found only the 4 AAPL tables.

Re-validated: all 12 `parsed`, 7,877 spans, every row on 671106d02317.
`python -m scripts.check_stored_spans`:

    ticker accession               rows mismatch out_of_range
    AAPL   0000320193-25-000079     962        0            0
    AAPL   0000320193-26-000006     554        0            0
    AAPL   0000320193-26-000013     750        0            0
    AAPL   0000320193-26-000020     756        0            0
    COST   0000909832-25-000101     818        0            0
    COST   0000909832-25-000169     395        0            0
    COST   0000909832-26-000029     571        0            0
    COST   0000909832-26-000051     570        0            0
    TGT    0000027419-25-000126     576        0            0
    TGT    0000027419-26-000016     977        0            0
    TGT    0000027419-26-000022     401        0            0
    TGT    0000027419-26-000042     547        0            0
    total rows 7877, mismatches 0

The 8 tables now unscaled, as the chunker will see them:

    0000320193-25-000079 scale=None source=None
        [Table | Apple Inc. | FY2025 10-K | Item 7]
        |  |  |  |  |
        |---|---|---|---|
        | Gross margin percentage: |  |  |  |
        | Products | 36.8% | 37.2% | 36.5% |
    0000320193-26-000006 scale=None source=None
        [Table | Apple Inc. | Q1 FY2026 10-Q | Part I, Item 2]
        |  |  |  |
        |---|---|---|
        | Gross margin percentage: |  |  |
        | Products | 40.7% | 39.3% |
    0000320193-26-000013 scale=None source=None
        [Table | Apple Inc. | Q2 FY2026 10-Q | Part I, Item 2]
        |  |  |  |  |  |
        |---|---|---|---|---|
        | Gross margin percentage: |  |  |  |  |
        | Products | 38.7% | 35.9% | 39.9% | 37.9% |
    0000320193-26-000020 scale=None source=None
        [Table | Apple Inc. | Q3 FY2026 10-Q | Part I, Item 2]
        |  |  |  |  |  |
        |---|---|---|---|---|
        | Gross margin percentage: |  |  |  |  |
        | Products | 40.1% | 34.5% | 39.9% | 36.9% |
    0000027419-25-000126 scale=None source=None
        [Table: Rate Analysis | TARGET CORPORATION | Q3 FY2025 10-Q | Part I, Item 2]
        | Rate Analysis | Three Months Ended November 1, 2025 | Three Months Ended November 2, 2024 | Nine Months Ended November 1, 2025 | Nine Months Ended November 2, 2024 |
        |---|---|---|---|---|
        | Gross margin rate (a) | 28.2% | 28.3% | 28.5% | 29.0% |
        | SG&A expense rate (a)(b) | 21.9 | 21.3 | 20.8 | 21.1 |
    0000027419-26-000016 scale=None source=None
        [Table: Rate Analysis | TARGET CORPORATION | FY2025 10-K | Item 7]
        | Rate Analysis | 2025 | 2024 | 2023(a) |
        |---|---|---|---|
        | Gross margin rate | 27.9% | 28.2% | 27.5% |
        | SG&A expense rate | 20.6 | 20.6 | 20.0 |
    0000027419-26-000016 scale=None source=None
        [Table: Assumptions | TARGET CORPORATION | FY2025 10-K | Item 8]
        | Benefit Obligation Weighted Average Assumptions | 2025 | 2024 |
        |---|---|---|
        | Discount rate | 5.56% | 5.68% |
        | Average assumed rate of compensation increase | 3.00 | 3.00 |
    0000027419-26-000022 scale=None source=None
        [Table: Rate Analysis | TARGET CORPORATION | Q1 FY2026 10-Q | Part I, Item 2]
        | Rate Analysis | Three Months Ended May 2, 2026 | Three Months Ended May 3, 2025 |
        |---|---|---|
        | Gross margin rate | 29.0% | 28.2% |
        | SG&A expense rate | 21.9 | 19.3 |
    0000027419-26-000042 scale=None source=None
        [Table: Rate Analysis | TARGET CORPORATION | Q2 FY2026 10-Q | Part I, Item 2]
        | Rate Analysis | Three Months Ended August 1, 2026 | Three Months Ended August 2, 2025 | Six Months Ended August 1, 2026 | Six Months Ended August 2, 2025 |
        |---|---|---|---|---|
        | Gross margin rate (a) | 33.7% | 29.0% | 31.4% | 28.6% |
        | SG&A expense rate | 21.6 | 21.3 | 21.7 | 20.3 |

The header-less AAPL tables still serialize an empty column-label line; the
chunker drops it (F-50 residual).

Snapshots: the 3 syrupy snapshots pass unchanged -- `parse_summary` holds no
table fields -- so nothing was re-blessed. Four hand-written expectations moved,
each traced to a row of the diff: scale-source counts AAPL 10-K 35/3 -> 32/5,
AAPL 10-Q 22/2 -> 20/3, TGT 10-K 48/2 -> 45/2; the validation baseline's
scale counts 35/3/39 -> 32/5/38. New tests: F-50 on the AAPL 10-K fixture's
percentage table; F-51 on cells copied from 0000320193-26-000020 (not a fixture,
and no fixture has the shape), plus a fixture invariant that no column label
carries a dash. `make test`: 173 passed, 3 snapshots passed.

## 2026-10-01 — Phase 2 step 1: structure-aware chunker (stopped for review)

F-50/F-51 committed as `690a685`.

`api/chunk/context.py` (chunk header, table lines) and `api/chunk/chunker.py`
(`chunk_document`). Outside `api/parse/`, so `parser_version` is unchanged.
Config `chunking:` in `api/config.yaml`; `target_tokens: 700` is PRD's value and
not decided (F-53). Not persisted: no `chunks` migration, no `chunk_id` on spans,
no embeddings or indexes.

Run over the 12 filings. **The counter is whitespace words, not tokens** -- no
tokenizer is installed. `tsplit` tables split by row groups, `furn` furniture
blocks dropped, `layP` layout tables kept as prose, `nohdr` header-less table
chunks, `psplit` paragraphs split at sentences, `preItem` blocks before Item 1:

    COUNTER = whitespace words (not tokens); target=700 overlap=0.15
    ticker accession              prose table tsplit furn layP nohdr psplit preItem  p50w  maxw >512w uniq
    AAPL   0000320193-25-000079      84    45      2   58    7     3      0      47   169   700    30   ok
    AAPL   0000320193-26-000006      34    23      0   22    2     2      0      34   126   671     2   ok
    AAPL   0000320193-26-000013      40    25      0   26    2     2      0      34   181   696     9   ok
    AAPL   0000320193-26-000020      40    26      0   26    2     2      0      34   181   699     5   ok
    COST   0000909832-25-000101      90    44      0  146    6     1      0      45   143   700    36   ok
    COST   0000909832-25-000169      42    27      0   55    2     0      0      29    99   700     9   ok
    COST   0000909832-26-000029      43    28      0   62    2     0      0      29   113   700     9   ok
    COST   0000909832-26-000051      43    28      0   62    2     0      0      29   113   700     9   ok
    TGT    0000027419-25-000126      36    34      0   46   16     0      0      35   133   638     4   ok
    TGT    0000027419-26-000016     105    64      0  132   47     1      2      43   146   699    28   ok
    TGT    0000027419-26-000022      33    30      0   38   21     0      0      35   125   657     3   ok
    TGT    0000027419-26-000042      34    32      0   43   16     0      0      35   152   691     3   ok

Even in words, 2-36 chunks per filing exceed 512 -- the embedding model's limit
(F-53). Samples checked by eye: AAPL 10-Q Part II Item 1A prose chunk; its
statement of operations as one table chunk with Part I, Item 1 and "in millions,
USD"; the AAPL 10-K header-less gross-margin-percentage table with no label line
and no scale; the two split exhibit-index tables repeating context line and
labels in every part. TGT keeps 10-26 nav fragments in prose (F-54).

Tests: `tests/unit/test_chunker.py` (30, on the 3 fixtures, word counter
injected). `make test`: 203 passed, 3 snapshots passed.

## 2026-10-01 — Chunker: real tokens, 500-token budget, split-table offsets

**Tokenizer.** `tokenizers` 0.23.2 added to `pyproject.toml` (installed with uv;
it brings `huggingface-hub` and `tqdm` as its own dependencies). Vendored
`api/chunk/bge-base-en-v1.5.tokenizer.json` from
`https://huggingface.co/BAAI/bge-base-en-v1.5/resolve/a5beb1e3e68b9ab74eb54cfd186867f64f240e1a/tokenizer.json`,
711,396 bytes, sha256
`d241a60d5e8f04cc1b2b3e9ef7a4921b27bf526d9f6050ab90f9267a1f9e5c66` -- pinned in
`embedding:` and checked on every load. The file sets no truncation or padding;
`api/chunk/tokens.py` switches both off anyway. `sentence_bert_config.json` at
that revision: `max_seq_length: 512`.

**Row offsets.** `Cell` carries a trimmed `(char_start, char_end)`;
`Table.body_offsets` holds one range per body row. Checked on all 3,557 body rows
of the 12 filings: 0 outside their table, 0 out of order, 0 with a cell's text
missing from the row slice. A first pass found 306 rows overshooting by one
whitespace character (untrimmed cell ranges), fixed by trimming. `text_sha256`
and all 404 tables' columns, scales, titles and first rows unchanged;
`parser_version` 671106d02317 -> f1090fb5f594; re-validated, 7,877 spans,
`check_stored_spans` 0 mismatches.

**Run with real tokens** (`navres` = "Table of Contents" fragments left in prose,
F-54; `parts` = chunks from split tables; `partOverlap` must be 0):

    COUNTER = BAAI/bge-base-en-v1.5@a5beb1e3e68b tokenizer; target_tokens=500 max_seq_length=512 overlap=0.15
    ticker accession              prose table tsplit parts furn navres layP nohdr psplit preItem  p50  max >512 partOverlap
    AAPL   0000320193-25-000079     118    56      9    22   58      0    7     3      1      47  308  499    0           0
    AAPL   0000320193-26-000006      41    28      5    10   22      0    2     2      0      34  223  500    0           0
    AAPL   0000320193-26-000013      54    33      8    16   26      0    2     2      1      34  292  500    0           0
    AAPL   0000320193-26-000020      52    34      8    16   26      0    2     2      1      34  304  500    0           0
    COST   0000909832-25-000101     129    50      5    11  146      0    6     1      1      45  293  500    0           0
    COST   0000909832-25-000169      51    30      3     6   55      0    2     0      1      29  184  500    0           0
    COST   0000909832-26-000029      55    34      6    12   62      0    2     0      2      29  240  490    0           0
    COST   0000909832-26-000051      56    34      6    12   62      0    2     0      2      29  236  499    0           0
    TGT    0000027419-25-000126      45    38      4     8   46     13   16     0      0      35  227  498    0           0
    TGT    0000027419-26-000016     147    67      3     6  132     29   47     1      3      43  251  992    2           0
    TGT    0000027419-26-000022      39    33      3     6   38     17   21     0      0      35  200  499    0           0
    TGT    0000027419-26-000042      42    35      3     6   43     12   16     0      0      35  227  500    0           0

`>512` is 0 except TGT's 10-K: two units of its exhibit index (648 and 992
tokens) that the sentence splitter cannot break (F-56). Every split table's parts
tile it with no overlap. `make test`: 209 passed, 3 snapshots passed.

## 2026-10-01 — Migration 0005, chunks written; Phase 2 step 2: span -> chunk resolution

Chunker committed as `2a2addb`.

`0005_chunks.sql`: `chunks` exactly as PRD 8 (nullable `embedding VECTOR(768)`,
generated `tsv`, `chunks_meta`); HNSW and GIN deferred to step 4.
`xbrl_spans.chunk_id TEXT REFERENCES chunks(chunk_id) ON DELETE SET NULL`.
Applied; second `make migrate` printed `no pending migrations`.

`python -m api.chunk.store` (one transaction per filing: delete, insert; refuses a
stale parse):

    chunker_version 40eaec61b7a0  parser_version f1090fb5f594
    ticker accession              chunks prose table >512
    AAPL   0000320193-25-000079      174   118    56    0
    AAPL   0000320193-26-000006       69    41    28    0
    AAPL   0000320193-26-000013       87    54    33    0
    AAPL   0000320193-26-000020       86    52    34    0
    COST   0000909832-25-000101      179   129    50    0
    COST   0000909832-25-000169       81    51    30    0
    COST   0000909832-26-000029       89    55    34    0
    COST   0000909832-26-000051       90    56    34    0
    TGT    0000027419-25-000126       83    45    38    0
    TGT    0000027419-26-000016      214   147    67    2
    TGT    0000027419-26-000022       72    39    33    0
    TGT    0000027419-26-000042       77    42    35    0

Second run identical; `resolve.py` excluded from the version hash and both
re-run, giving the version above. DB: 1,301 chunks, 12 filings, 1 `chunker_version`,
`max(token_count)` 992, 2 over 512 (F-56), `tsv` on all 1,301, 0 embeddings.

`python -m api.chunk.resolve`:

    ticker accession              spans preItem unique overlap splitPara unresInItem   rate inItems
    AAPL   0000320193-25-000079     962       2    960       0         0           0  0.998   1.000
    AAPL   0000320193-26-000006     554       1    553       0         0           0  0.998   1.000
    AAPL   0000320193-26-000013     750       1    749       0         0           0  0.999   1.000
    AAPL   0000320193-26-000020     756       1    755       0         0           0  0.999   1.000
    COST   0000909832-25-000101     818       2    814       2         0           0  0.998   1.000
    COST   0000909832-25-000169     395       1    394       0         0           0  0.997   1.000
    COST   0000909832-26-000029     571       1    570       0         0           0  0.998   1.000
    COST   0000909832-26-000051     570       1    569       0         0           0  0.998   1.000
    TGT    0000027419-25-000126     576       1    573       2         0           0  0.998   1.000
    TGT    0000027419-26-000016     977       2    973       2         0           0  0.998   1.000
    TGT    0000027419-26-000022     401       1    400       0         0           0  0.998   1.000
    TGT    0000027419-26-000042     547       1    546       0         0           0  0.998   1.000
    total spans 7877, resolved 7862 (0.998; 1.000 within Items), before first Item 15

The 15 unresolved spans are all before Item 1, all `dei` cover facts --
`EntityCommonStockSharesOutstanding` x12, `EntityPublicFloat` x3. 0 unresolved
inside an Item. Spans landing in a split paragraph: 0. Check on stored rows: all
7,862 resolved spans have their `raw_text` inside their chunk's `raw_text`; 7,278
of them are in table chunks.

Tests: `tests/unit/test_resolve.py` (categories on plain ranges; the AAPL 10-K
fixture end to end: 962 spans, 2 before Item 1, 960 resolved, every one inside its
chunk's text). `make test`: 212 passed, 3 snapshots passed.

## 2026-10-01 — F-56: sentence splitter breaks before a digit

Checkpoint committed as `b385063`.

`ChunkStats.paragraph_pieces` added first (measurement only) so before and after
use the same instrument. Then `_SENTENCE_END`'s lookahead gained `0-9`.
`chunker_version` 40eaec61b7a0 -> 2f9df055b70a; store and resolve re-run.

Before:

    COUNTER = BAAI/bge-base-en-v1.5@a5beb1e3e68b tokenizer; target_tokens=500 max_seq_length=512 overlap=0.15
    ticker accession              prose table tsplit parts furn navres layP nohdr psplit pieces preItem  p50  max >512 partOverlap
    AAPL   0000320193-25-000079     118    56      9    22   58      0    7     3      1      2      47  308  499    0           0
    AAPL   0000320193-26-000006      41    28      5    10   22      0    2     2      0      0      34  223  500    0           0
    AAPL   0000320193-26-000013      54    33      8    16   26      0    2     2      1      2      34  292  500    0           0
    AAPL   0000320193-26-000020      52    34      8    16   26      0    2     2      1      2      34  304  500    0           0
    COST   0000909832-25-000101     129    50      5    11  146      0    6     1      1      2      45  293  500    0           0
    COST   0000909832-25-000169      51    30      3     6   55      0    2     0      1      2      29  184  500    0           0
    COST   0000909832-26-000029      55    34      6    12   62      0    2     0      2      4      29  240  490    0           0
    COST   0000909832-26-000051      56    34      6    12   62      0    2     0      2      4      29  236  499    0           0
    TGT    0000027419-25-000126      45    38      4     8   46     13   16     0      0      0      35  227  498    0           0
    TGT    0000027419-26-000016     147    67      3     6  132     29   47     1      3      7      43  251  992    2           0
    TGT    0000027419-26-000022      39    33      3     6   38     17   21     0      0      0      35  200  499    0           0
    TGT    0000027419-26-000042      42    35      3     6   43     12   16     0      0      0      35  227  500    0           0

After:

    COUNTER = BAAI/bge-base-en-v1.5@a5beb1e3e68b tokenizer; target_tokens=500 max_seq_length=512 overlap=0.15
    ticker accession              prose table tsplit parts furn navres layP nohdr psplit pieces preItem  p50  max >512 partOverlap
    AAPL   0000320193-25-000079     118    56      9    22   58      0    7     3      1      2      47  308  499    0           0
    AAPL   0000320193-26-000006      41    28      5    10   22      0    2     2      0      0      34  223  500    0           0
    AAPL   0000320193-26-000013      54    33      8    16   26      0    2     2      1      2      34  292  500    0           0
    AAPL   0000320193-26-000020      52    34      8    16   26      0    2     2      1      2      34  304  500    0           0
    COST   0000909832-25-000101     129    50      5    11  146      0    6     1      1      2      45  293  500    0           0
    COST   0000909832-25-000169      51    30      3     6   55      0    2     0      1      2      29  184  500    0           0
    COST   0000909832-26-000029      55    34      6    12   62      0    2     0      2      4      29  240  490    0           0
    COST   0000909832-26-000051      56    34      6    12   62      0    2     0      2      4      29  236  499    0           0
    TGT    0000027419-25-000126      45    38      4     8   46     13   16     0      0      0      35  227  498    0           0
    TGT    0000027419-26-000016     150    67      3     6  132     29   47     1      3      8      43  252  500    0           0
    TGT    0000027419-26-000022      39    33      3     6   38     17   21     0      0      0      35  200  499    0           0
    TGT    0000027419-26-000042      42    35      3     6   43     12   16     0      0      0      35  227  500    0           0

Only TGT's 10-K moves: prose 147 -> 150, pieces 7 -> 8, max 992 -> 500, `>512`
2 -> 0. `partOverlap` 0 throughout.

Resolve table before and after is identical:

    ticker accession              spans preItem unique overlap splitPara unresInItem   rate inItems
    AAPL   0000320193-25-000079     962       2    960       0         0           0  0.998   1.000
    AAPL   0000320193-26-000006     554       1    553       0         0           0  0.998   1.000
    AAPL   0000320193-26-000013     750       1    749       0         0           0  0.999   1.000
    AAPL   0000320193-26-000020     756       1    755       0         0           0  0.999   1.000
    COST   0000909832-25-000101     818       2    814       2         0           0  0.998   1.000
    COST   0000909832-25-000169     395       1    394       0         0           0  0.997   1.000
    COST   0000909832-26-000029     571       1    570       0         0           0  0.998   1.000
    COST   0000909832-26-000051     570       1    569       0         0           0  0.998   1.000
    TGT    0000027419-25-000126     576       1    573       2         0           0  0.998   1.000
    TGT    0000027419-26-000016     977       2    973       2         0           0  0.998   1.000
    TGT    0000027419-26-000022     401       1    400       0         0           0  0.998   1.000
    TGT    0000027419-26-000042     547       1    546       0         0           0  0.998   1.000
    total spans 7877, resolved 7862 (0.998; 1.000 within Items), before first Item 15

`content_hash` diff by chunk_id: TGT 10-K 214 -> 217 chunks, 4 changed, 1
removed, 4 added; the other 11 filings 0 changed, 0 removed, 0 added. `make test`:
213 passed, 3 snapshots passed.

## 2026-10-01 — F-54 measured (not fixed); Phase 2 step 3: embedding pipeline

F-56 committed as `1f10f6a`.

**F-54.** The block-level rule ("a leaf block made entirely of in-document
anchors is navigation") was checked against the raw HTML before building it.
TGT's nav tables per filing: 30 / 80 / 28 / 28; entirely anchors: 1 per filing;
mixed (a plain-text section label such as "RISK FACTORS" beside the two links):
29 / 79 / 27 / 27. AAPL and COST: none. The rule would reclassify one block per
TGT filing and leave the residual, so the fix needs a block-model change (anchor
ranges per block plus a rule for mixed blocks). Stopped there as instructed;
F-54 rewritten to say exactly that, and now states it blocks the Phase 2 exit.

**Dependencies.** `sentence-transformers==6.1.0` and `torch==2.14.1` pinned in
`pyproject.toml` (installed with uv; also brought `transformers` 5.18.0, numpy,
scipy, scikit-learn and others). `tokenizers` stays 0.23.2.

**Migration 0006** `embedding_cache (content_hash, model, revision)` -> vector.
Applied; second `make migrate` printed `no pending migrations`.

**`api/index/embed.py`.** Loads the model named in config at the pinned revision.
Before any write: model dimension == `embedding.dim`, `max_seq_length` ==
`embedding.max_seq_length`, and the model's own tokenizer with truncation off
reproduces every stored `token_count`; any chunk over the limit fails the run.
Per filing: fill from the cache, encode the misses (normalized, batch 64, `text`
with header, no instruction prefix), write them to the cache, fill again.

Run 1 (wall time 47.8 s total on MPS):

    model BAAI/bge-base-en-v1.5@a5beb1e3e68b device mps:0
    checks: {'dim': 768, 'max_seq_length': 512, 'chunks_checked': 1304, 'token_count_mismatches': 0, 'over_max_seq_length': 0}
    ticker accession              embedded cache skipped seconds
    AAPL   0000320193-25-000079        174     0       0     6.8
    AAPL   0000320193-26-000006         69     0       0     3.0
    AAPL   0000320193-26-000013         87     0       0     2.8
    AAPL   0000320193-26-000020         86     0       0     2.9
    COST   0000909832-25-000101        179     0       0     5.9
    COST   0000909832-25-000169         81     0       0     2.9
    COST   0000909832-26-000029         89     0       0     3.1
    COST   0000909832-26-000051         90     0       0     3.3
    TGT    0000027419-25-000126         83     0       0     3.0
    TGT    0000027419-26-000016        217     0       0     7.6
    TGT    0000027419-26-000022         72     0       0     3.1
    TGT    0000027419-26-000042         77     0       0     3.4
    chunks with embedding IS NULL: 0

Run 2, resume:

    checks: {'dim': 768, 'max_seq_length': 512, 'chunks_checked': 1304, 'token_count_mismatches': 0, 'over_max_seq_length': 0}
    ticker accession              embedded cache skipped seconds
    AAPL   0000320193-25-000079          0     0     174     0.0
    AAPL   0000320193-26-000006          0     0      69     0.0
    AAPL   0000320193-26-000013          0     0      87     0.0
    AAPL   0000320193-26-000020          0     0      86     0.0
    COST   0000909832-25-000101          0     0     179     0.0
    COST   0000909832-25-000169          0     0      81     0.0
    COST   0000909832-26-000029          0     0      89     0.0
    COST   0000909832-26-000051          0     0      90     0.0
    TGT    0000027419-25-000126          0     0      83     0.0
    TGT    0000027419-26-000016          0     0     217     0.0
    TGT    0000027419-26-000022          0     0      72     0.0
    TGT    0000027419-26-000042          0     0      77     0.0
    chunks with embedding IS NULL: 0

Then `python -m api.chunk.store` re-chunked every filing (delete + insert: 1,304
of 1,304 rows with `embedding IS NULL`), and run 3:

    checks: {'dim': 768, 'max_seq_length': 512, 'chunks_checked': 1304, 'token_count_mismatches': 0, 'over_max_seq_length': 0}
    ticker accession              embedded cache skipped seconds
    AAPL   0000320193-25-000079          0   174       0     0.0
    AAPL   0000320193-26-000006          0    69       0     0.0
    AAPL   0000320193-26-000013          0    87       0     0.0
    AAPL   0000320193-26-000020          0    86       0     0.0
    COST   0000909832-25-000101          0   179       0     0.0
    COST   0000909832-25-000169          0    81       0     0.0
    COST   0000909832-26-000029          0    89       0     0.0
    COST   0000909832-26-000051          0    90       0     0.0
    TGT    0000027419-25-000126          0    83       0     0.0
    TGT    0000027419-26-000016          0   217       0     0.0
    TGT    0000027419-26-000022          0    72       0     0.0
    TGT    0000027419-26-000042          0    77       0     0.0
    chunks with embedding IS NULL: 0

The re-chunk nulled `xbrl_spans.chunk_id` (ON DELETE SET NULL); `resolve`
re-run: 7,862 of 7,877, unchanged. Cache: 1,296 rows for 1,304 chunks -- 8 chunks
share their exact text with another. All vector norms 1.000000. Stored vs fresh
encode on 5 chunks: cosine 1.000000 each. No HNSW or GIN index yet (step 4).

Tests: `tests/unit/test_embed.py` (5; stand-in model on the vendored tokenizer,
no network). `make test`: 218 passed, 3 snapshots passed.

## 2026-10-01 — F-54: navigation by repeated anchor targets

Step 3 committed as `60227fe` (with `check_lengths` returning computed counts).

**Parser.** The walker records each `<a href="#...">` as `Anchor(char_start,
char_end, target)` and attaches it to its leaf block (`Block.anchors`). Text
unchanged: `text_sha256` identical on all 12, all 404 tables identical, the 3
syrupy snapshots unchanged -- `parse_summary` holds no block fields, so the new
field does not appear in them either. `parser_version` f1090fb5f594 -> 0e417d5495e4;
re-validated, `check_stored_spans` 7,877 rows, 0 mismatches.

**Anchor-target sets** (blocks per set; the last 8 characters of each target;
sets reaching `furniture_min_repeats` marked) -- TGT's running headers share one
two-target set on 30/80/28/28 blocks, so the rule's assumption holds:

    === AAPL 0000320193-25-000079: anchors attached 102, all inside their block True, blocks with anchors 3, distinct target sets 2
         2 blocks  ['88eba90a_181', '88eba90a_184', '88eba90a_187', '88eba90a_190', '88eba90a_193', '88eba90a_196', '88eba90a_241']
         1 blocks  ['d88eba90a_10', 'd88eba90a_13', '88eba90a_172', '88eba90a_175', '88eba90a_244', '88eba90a_247', '88eba90a_250', '88eba90a_259', '88eba90a_262', '88eba90a_265', '88eba90a_268', '88eba90a_271', '88eba90a_274', '88eba90a_277', '88eba90a_280', '88eba90a_283', '88eba90a_286', 'd88eba90a_52', 'd88eba90a_70', 'd88eba90a_73', 'd88eba90a_76', 'd88eba90a_79', 'd88eba90a_82', 'd88eba90a_85', 'd88eba90a_88', 'd88eba90a_91', 'd88eba90a_94']
    === AAPL 0000320193-26-000006: anchors attached 35, all inside their block True, blocks with anchors 1, distinct target sets 1
         1 blocks  ['3dde0a849_10', '3dde0a849_13', 'dde0a849_148', 'dde0a849_151', 'dde0a849_154', 'dde0a849_157', 'dde0a849_160', 'dde0a849_163', 'dde0a849_166', 'dde0a849_169', 'dde0a849_172', 'dde0a849_178', '3dde0a849_67']
    === AAPL 0000320193-26-000013: anchors attached 35, all inside their block True, blocks with anchors 1, distinct target sets 1
         1 blocks  ['9d5386f45_10', '9d5386f45_13', 'd5386f45_148', 'd5386f45_151', 'd5386f45_154', 'd5386f45_157', 'd5386f45_160', 'd5386f45_163', 'd5386f45_166', 'd5386f45_169', 'd5386f45_172', 'd5386f45_178', '9d5386f45_67']
    === AAPL 0000320193-26-000020: anchors attached 35, all inside their block True, blocks with anchors 1, distinct target sets 1
         1 blocks  ['a987f6c2a_10', 'a987f6c2a_13', '987f6c2a_148', '987f6c2a_151', '987f6c2a_154', '987f6c2a_157', '987f6c2a_160', '987f6c2a_163', '987f6c2a_166', '987f6c2a_169', '987f6c2a_172', '987f6c2a_181', 'a987f6c2a_67']
    === COST 0000909832-25-000101: anchors attached 160, all inside their block True, blocks with anchors 90, distinct target sets 13
        69 blocks  ['07ac97c984_7']   >= furniture_min_repeats
         7 blocks  ['ac97c984_109']   >= furniture_min_repeats
         3 blocks  ['ac97c984_142']
         2 blocks  ['ac97c984_130']
         1 blocks  ['7ac97c984_13', 'ac97c984_145', 'ac97c984_148', 'ac97c984_151', 'ac97c984_154', 'ac97c984_157', '7ac97c984_16', 'ac97c984_160', 'ac97c984_163', 'ac97c984_166', 'ac97c984_169', 'ac97c984_172', 'ac97c984_175', 'ac97c984_178', 'ac97c984_181', 'ac97c984_184', '7ac97c984_19', '7ac97c984_22', '7ac97c984_25', '7ac97c984_28', '7ac97c984_31', '7ac97c984_34', '7ac97c984_37', '7ac97c984_40', '7ac97c984_46', '7ac97c984_49', '7ac97c984_76', '7ac97c984_79']
         1 blocks  ['ac97c984_139']
    === COST 0000909832-25-000169: anchors attached 69, all inside their block True, blocks with anchors 32, distinct target sets 5
        27 blocks  ['da66d10f26_7']   >= furniture_min_repeats
         2 blocks  ['a66d10f26_37']
         1 blocks  ['a66d10f26_10', '66d10f26_100', '66d10f26_103', '66d10f26_106', '66d10f26_109', '66d10f26_112', '66d10f26_115', '66d10f26_118', '66d10f26_121', '66d10f26_124', '66d10f26_127', 'a66d10f26_13', 'a66d10f26_16', 'a66d10f26_19', 'a66d10f26_22', 'a66d10f26_28', 'a66d10f26_31', 'a66d10f26_34', 'a66d10f26_67', 'a66d10f26_97']
         1 blocks  ['a66d10f26_64']
         1 blocks  ['a66d10f26_61']
    === COST 0000909832-26-000029: anchors attached 72, all inside their block True, blocks with anchors 35, distinct target sets 5
        30 blocks  ['849fd823e0_7']   >= furniture_min_repeats
         2 blocks  ['49fd823e0_37']
         1 blocks  ['49fd823e0_10', '9fd823e0_106', '9fd823e0_109', '9fd823e0_112', '9fd823e0_115', '9fd823e0_118', '9fd823e0_121', '9fd823e0_124', '9fd823e0_127', '49fd823e0_13', '9fd823e0_130', '9fd823e0_133', '9fd823e0_136', '49fd823e0_16', '49fd823e0_19', '49fd823e0_22', '49fd823e0_28', '49fd823e0_31', '49fd823e0_34', '49fd823e0_70']
         1 blocks  ['49fd823e0_64']
         1 blocks  ['49fd823e0_61']
    === COST 0000909832-26-000051: anchors attached 72, all inside their block True, blocks with anchors 35, distinct target sets 5
        30 blocks  ['b65bca5a26_7']   >= furniture_min_repeats
         2 blocks  ['65bca5a26_37']
         1 blocks  ['65bca5a26_10', '5bca5a26_106', '5bca5a26_109', '5bca5a26_112', '5bca5a26_115', '5bca5a26_118', '5bca5a26_121', '5bca5a26_124', '5bca5a26_127', '65bca5a26_13', '5bca5a26_130', '5bca5a26_133', '5bca5a26_136', '65bca5a26_16', '65bca5a26_19', '65bca5a26_22', '65bca5a26_28', '65bca5a26_31', '65bca5a26_34', '65bca5a26_70']
         1 blocks  ['65bca5a26_64']
         1 blocks  ['65bca5a26_61']
    === TGT 0000027419-25-000126: anchors attached 180, all inside their block True, blocks with anchors 52, distinct target sets 15
        30 blocks  ['1a1ce788d_31', '91a1ce788d_7']   >= furniture_min_repeats
         5 blocks  ['1a1ce788d_31']   >= furniture_min_repeats
         3 blocks  ['1ce788d_1331', '1a1ce788d_46']
         2 blocks  ['1ce788d_1331']
         2 blocks  ['1a1ce788d_58']
         1 blocks  ['1a1ce788d_10', '1a1ce788d_13', 'a1ce788d_130', 'a1ce788d_133', 'a1ce788d_136', 'a1ce788d_139', 'a1ce788d_142', 'a1ce788d_145', 'a1ce788d_148', 'a1ce788d_151', 'a1ce788d_154', 'a1ce788d_157', '1a1ce788d_16', 'a1ce788d_160', '1a1ce788d_19', '1a1ce788d_22', '1a1ce788d_25', '1a1ce788d_28', '1a1ce788d_34', '1a1ce788d_82']
    === TGT 0000027419-26-000016: anchors attached 405, all inside their block True, blocks with anchors 138, distinct target sets 41
        80 blocks  ['f8f59e72_139', 'c0f8f59e72_7']   >= furniture_min_repeats
         8 blocks  ['f8f59e72_181']   >= furniture_min_repeats
         3 blocks  ['f8f59e72_190']
         3 blocks  ['8f59e72_2598']
         2 blocks  ['f8f59e72_178']
         2 blocks  ['0f8f59e72_94']
    === TGT 0000027419-26-000022: anchors attached 159, all inside their block True, blocks with anchors 47, distinct target sets 11
        28 blocks  ['37a8dbd04_31', 'e37a8dbd04_7']   >= furniture_min_repeats
         5 blocks  ['37a8dbd04_31']   >= furniture_min_repeats
         4 blocks  ['37a8dbd04_46']
         2 blocks  ['7a8dbd04_115']
         2 blocks  ['37a8dbd04_61']
         1 blocks  ['37a8dbd04_10', '37a8dbd04_13', '7a8dbd04_136', '7a8dbd04_139', '7a8dbd04_142', '7a8dbd04_145', '7a8dbd04_148', '7a8dbd04_151', '7a8dbd04_154', '7a8dbd04_157', '37a8dbd04_16', '7a8dbd04_160', '7a8dbd04_163', '7a8dbd04_166', '37a8dbd04_19', '37a8dbd04_22', '37a8dbd04_25', '37a8dbd04_28', '37a8dbd04_34', '37a8dbd04_85']
    === TGT 0000027419-26-000042: anchors attached 172, all inside their block True, blocks with anchors 51, distinct target sets 15
        28 blocks  ['137393f08_31', '9137393f08_7']   >= furniture_min_repeats
         5 blocks  ['137393f08_31']   >= furniture_min_repeats
         3 blocks  ['137393f08_46']
         2 blocks  ['7393f08_1328']
         2 blocks  ['37393f08_115']
         2 blocks  ['137393f08_61']

**Chunker.** `navigation_blocks` beside `furniture_keys`; `nav_samples` beside
`furniture_samples`. `chunker_version` 2f9df055b70a -> abe01d8d9b7b.

Before:

    COUNTER = BAAI/bge-base-en-v1.5@a5beb1e3e68b tokenizer; target_tokens=500 max_seq_length=512 overlap=0.15
    ticker accession              prose table tsplit parts furn navres layP nohdr psplit pieces preItem  p50  max >512 partOverlap
    AAPL   0000320193-25-000079     118    56      9    22   58      0    7     3      1      2      47  308  499    0           0
    AAPL   0000320193-26-000006      41    28      5    10   22      0    2     2      0      0      34  223  500    0           0
    AAPL   0000320193-26-000013      54    33      8    16   26      0    2     2      1      2      34  292  500    0           0
    AAPL   0000320193-26-000020      52    34      8    16   26      0    2     2      1      2      34  304  500    0           0
    COST   0000909832-25-000101     129    50      5    11  146      0    6     1      1      2      45  293  500    0           0
    COST   0000909832-25-000169      51    30      3     6   55      0    2     0      1      2      29  184  500    0           0
    COST   0000909832-26-000029      55    34      6    12   62      0    2     0      2      4      29  240  490    0           0
    COST   0000909832-26-000051      56    34      6    12   62      0    2     0      2      4      29  236  499    0           0
    TGT    0000027419-25-000126      45    38      4     8   46     13   16     0      0      0      35  227  498    0           0
    TGT    0000027419-26-000016     150    67      3     6  132     29   47     1      3      8      43  252  500    0           0
    TGT    0000027419-26-000022      39    33      3     6   38     17   21     0      0      0      35  200  499    0           0
    TGT    0000027419-26-000042      42    35      3     6   43     12   16     0      0      0      35  227  500    0           0

After (`nav` = blocks dropped as navigation):

    COUNTER = BAAI/bge-base-en-v1.5@a5beb1e3e68b tokenizer; target_tokens=500 max_seq_length=512 overlap=0.15
    ticker accession              prose table tsplit parts furn  nav navres layP nohdr psplit pieces preItem  p50  max >512 partOverlap
    AAPL   0000320193-25-000079     118    56      9    22   58    0      0    7     3      1      2      47  308  499    0           0
    AAPL   0000320193-26-000006      41    28      5    10   22    0      0    2     2      0      0      34  223  500    0           0
    AAPL   0000320193-26-000013      54    33      8    16   26    0      0    2     2      1      2      34  292  500    0           0
    AAPL   0000320193-26-000020      52    34      8    16   26    0      0    2     2      1      2      34  304  500    0           0
    COST   0000909832-25-000101     129    50      5    11  146    0      0    6     1      1      2      45  293  500    0           0
    COST   0000909832-25-000169      51    30      3     6   55    0      0    2     0      1      2      29  184  500    0           0
    COST   0000909832-26-000029      55    34      6    12   62    0      0    2     0      2      4      29  240  490    0           0
    COST   0000909832-26-000051      56    34      6    12   62    0      0    2     0      2      4      29  236  499    0           0
    TGT    0000027419-25-000126      45    38      4     8   46   11      0    5     0      0      0      35  227  498    0           0
    TGT    0000027419-26-000016     150    67      3     6  132   26      0   22     1      3      8      43  252  500    0           0
    TGT    0000027419-26-000022      39    33      3     6   38   15      0    6     0      0      0      35  200  499    0           0
    TGT    0000027419-26-000042      41    35      3     6   43   10      0    6     0      0      0      35  225  500    0           0

Chunk diff by `content_hash`, and dropped blocks (furniture + navigation)
overlapping any stored xbrl_span:

    ticker accession                 chunks hashChanged removed added droppedBlocks spanOverlaps
    AAPL   0000320193-25-000079    174->174            0       0     0            58            0
    AAPL   0000320193-26-000006     69->69             0       0     0            22            0
    AAPL   0000320193-26-000013     87->87             0       0     0            26            0
    AAPL   0000320193-26-000020     86->86             0       0     0            26            0
    COST   0000909832-25-000101    179->179            0       0     0           151            0
    COST   0000909832-25-000169     81->81             0       0     0            61            0
    COST   0000909832-26-000029     89->89             0       0     0            68            0
    COST   0000909832-26-000051     90->90             0       0     0            68            0
    TGT    0000027419-25-000126     83->83             7       5     5            59            0
    TGT    0000027419-26-000016    217->217           18      12    12           161            0
    TGT    0000027419-26-000022     72->72            11       4     4            55            0
    TGT    0000027419-26-000042     77->76             7       5     4            55            0

Embed after re-chunk:

    checks: {'dim': 768, 'max_seq_length': 512, 'chunks_checked': 1303, 'token_count_mismatches': 0, 'over_max_seq_length': 0}
    ticker accession              embedded cache skipped seconds
    AAPL   0000320193-25-000079          0   174       0     0.0
    AAPL   0000320193-26-000006          0    69       0     0.0
    AAPL   0000320193-26-000013          0    87       0     0.0
    AAPL   0000320193-26-000020          0    86       0     0.0
    COST   0000909832-25-000101          0   179       0     0.0
    COST   0000909832-25-000169          0    81       0     0.0
    COST   0000909832-26-000029          0    89       0     0.0
    COST   0000909832-26-000051          0    90       0     0.0
    TGT    0000027419-25-000126         12    71       0     1.0
    TGT    0000027419-26-000016         30   187       0     1.4
    TGT    0000027419-26-000022         15    57       0     0.6
    TGT    0000027419-26-000042         11    65       0     0.5
    chunks with embedding IS NULL: 0

Resolve:

    ticker accession              spans preItem unique overlap splitPara unresInItem   rate inItems
    AAPL   0000320193-25-000079     962       2    960       0         0           0  0.998   1.000
    AAPL   0000320193-26-000006     554       1    553       0         0           0  0.998   1.000
    AAPL   0000320193-26-000013     750       1    749       0         0           0  0.999   1.000
    AAPL   0000320193-26-000020     756       1    755       0         0           0  0.999   1.000
    COST   0000909832-25-000101     818       2    814       2         0           0  0.998   1.000
    COST   0000909832-25-000169     395       1    394       0         0           0  0.997   1.000
    COST   0000909832-26-000029     571       1    570       0         0           0  0.998   1.000
    COST   0000909832-26-000051     570       1    569       0         0           0  0.998   1.000
    TGT    0000027419-25-000126     576       1    573       2         0           0  0.998   1.000
    TGT    0000027419-26-000016     977       2    973       2         0           0  0.998   1.000
    TGT    0000027419-26-000022     401       1    400       0         0           0  0.998   1.000
    TGT    0000027419-26-000042     547       1    546       0         0           0  0.998   1.000
    total spans 7877, resolved 7862 (0.998; 1.000 within Items), before first Item 15

`navres` 0 everywhere; AAPL and COST unchanged; resolve unchanged; 0 overlaps.
One content block dropped, TGT 10-K block 826 (F-58). `make test`: 222 passed, 3
snapshots passed.

## 2026-10-01 — Phase 2 step 4: HNSW and full-text indexes

F-54 committed as `2244ebf`.

`0007_chunk_indexes.sql`: `chunks_hnsw` (hnsw, `embedding vector_cosine_ops`,
`m = 16, ef_construction = 64`) and `chunks_tsv` (gin on `tsv`), exactly as PRD 8
writes them, built after the load. Applied; second `make migrate` printed `no
pending migrations`. `pg_indexes` on chunks: chunks_hnsw, chunks_meta,
chunks_pkey, chunks_tsv.

`python -m scripts.check_indexes` (session `enable_seqscan = off`: 1,303 rows
would not otherwise push the planner off a sequential scan; the 768-float query
vector is elided in the plan):

    EXPLAIN <=> ORDER BY LIMIT:
        Limit  (cost=840.74..858.42 rows=5 width=40)
          ->  Index Scan using chunks_hnsw on chunks  (cost=840.74..5450.06 rows=1303 width=40)
                Order By: (embedding <=> '[...]'::vector)
    EXPLAIN @@:
        Bitmap Heap Scan on chunks  (cost=21.52..29.24 rows=2 width=32)
          Recheck Cond: (tsv @@ '''inventori'' & ''valuat'''::tsquery)
          ->  Bitmap Index Scan on chunks_tsv  (cost=0.00..21.52 rows=2 width=0)
                Index Cond: (tsv @@ '''inventori'' & ''valuat'''::tsquery)
        rows matching 'inventory valuation': 6
    self-retrieval through chunks_hnsw (20 chunks):
        0000027419-25-000126:102.0:102.0         top-1 distance 0.00e+00  distance-0 results 1  self found
        0000027419-25-000126:40.0:40.0           top-1 distance 0.00e+00  distance-0 results 1  self found
        0000027419-26-000016:272.0:272.0         top-1 distance 0.00e+00  distance-0 results 1  self found
        0000027419-26-000016:548.0:554.0         top-1 distance 0.00e+00  distance-0 results 1  self found
        0000027419-26-000016:724.0:724.0         top-1 distance 0.00e+00  distance-0 results 1  self found
        0000027419-26-000022:179.0:179.0         top-1 distance 0.00e+00  distance-0 results 1  self found
        0000027419-26-000042:164.0:164.0         top-1 distance 0.00e+00  distance-0 results 1  self found
        0000320193-25-000079:122.0:126.0         top-1 distance 0.00e+00  distance-0 results 1  self found
        0000320193-25-000079:396.0:396.0         top-1 distance 0.00e+00  distance-0 results 1  self found
        0000320193-25-000079:594.0:594.0         top-1 distance 0.00e+00  distance-0 results 1  self found
        0000320193-26-000006:222.0:226.0         top-1 distance 0.00e+00  distance-0 results 1  self found
        0000320193-26-000013:181.0:193.0         top-1 distance 0.00e+00  distance-0 results 1  self found
        0000320193-26-000020:110.0:110.0         top-1 distance 0.00e+00  distance-0 results 1  self found
        0000320193-26-000020:51.0:55.0           top-1 distance 0.00e+00  distance-0 results 1  self found
        0000909832-25-000101:308.0:313.0         top-1 distance 0.00e+00  distance-0 results 1  self found
        0000909832-25-000101:597.0:599.0         top-1 distance 0.00e+00  distance-0 results 1  self found
        0000909832-25-000101:89.0:89.0           top-1 distance 0.00e+00  distance-0 results 1  self found
        0000909832-25-000169:40.0:40.0           top-1 distance 0.00e+00  distance-0 results 1  self found
        0000909832-26-000029:247.0:247.0         top-1 distance 0.00e+00  distance-0 results 1  self found
        0000909832-26-000051:173.0:173.0         top-1 distance 0.00e+00  distance-0 results 1  self found
    self found at distance 0: 20 of 20

Both query shapes are served by their index; 20 of 20 sampled chunks return
themselves at cosine distance 0 through chunks_hnsw, and none of the 20 has an
identical-text twin.

## 2026-10-01 — Phase 2 step 5: naive baseline (retrieval verified; generation owner-blocked)

Step 4 committed as `e96fbf8` (docstring row count dropped).

`api/query/retrieve.py` (question embedding + dense top-k), `api/generate/
generator.py` (plain prompt, free text, `usage` kept), `api/query/baseline.py`
(CLI). Config: `baseline.top_k: 5`; `generation:` tier_small / tier_large /
max_tokens. `anthropic==1.11.0` pinned. `.env.example` gains `ANTHROPIC_API_KEY=`.

Key: `.env` has no `*_API_KEY` line. The shell environment did carry an
`ANTHROPIC_API_KEY`, so the exit call was attempted once. First attempt failed
before any request: `Messages.create() got an unexpected keyword argument
'temperature'` -- the pinned SDK has no sampling parameters (F-60); temperature
removed. Second attempt reached the API and was rejected:

    anthropic.AuthenticationError: Error code: 401 - {'type': 'error', 'error': {'type': 'authentication_error', 'message': 'invalid x-api-key'}, 'request_id': 'req_011CfbYkv3BmDectYSJKfAn6'}

Not retried. Generation is unexercised (F-59, owner-blocked).

Retrieval half, real output of
`python -m api.query.baseline --retrieve-only "What were Apple's total net sales in fiscal 2025?"`
(cosine distance, chunk id, context header):

    question: What were Apple's total net sales in fiscal 2025?
    plan: ->  Index Scan using chunks_hnsw on chunks  (cost=840.74..5450.06 rows=1303 width=375)
      0.1934  0000320193-25-000079:305.0:318.0  [Apple Inc. (AAPL) | 10-K | FY2025 | Item 7: Management’s Discussion and Analysis of Financial Condition and Results of Operations]
      0.1970  0000320193-25-000079:456.0:456.0  [Apple Inc. (AAPL) | 10-K | FY2025 | Item 8: Financial Statements and Supplementary Data]
      0.1974  0000320193-26-000013:181.0:193.0  [Apple Inc. (AAPL) | 10-Q | Q2 FY2026 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations]
      0.2021  0000320193-25-000079:291.0:303.0  [Apple Inc. (AAPL) | 10-K | FY2025 | Item 7: Management’s Discussion and Analysis of Financial Condition and Results of Operations]
      0.2057  0000320193-25-000079:595.0:595.0  [Apple Inc. (AAPL) | 10-K | FY2025 | Item 8: Financial Statements and Supplementary Data]

Served by chunks_hnsw. All five are AAPL; four from the FY2025 10-K's Items 7 and
8, one from the Q2 FY2026 10-Q's MD&A.

Tests: `tests/unit/test_generator.py` (prompt carries every chunk id; missing key
fails at the call site with a clear message; tiers read from config). `make test`:
225 passed, 3 snapshots passed.

## 2026-10-01 — F-42: corpus accession list materialized (not committed: F-62)

Step 5 committed as `aed3475` (`test_generation_config_has_what_the_call_reads`
replaced the literal-id assertion; F-60 resolution path in OPEN and TRADEOFFS).

`python -m scripts.materialize_corpus --as-of 2026-10-01`: window start
2023-10-01, 85 filings, 0 skipped for missing reportDate. Per ticker: COST, TGT,
JPM, BAC, AAPL, NVDA, PFE 12 each (3 10-K, 9 10-Q); XOM 1. The first run stopped
on JPM -- `filings.recent only reaches back to 2025-10-01 ... 70 older file(s)`
-- the F-28 guard doing its job; pagination added, see TRADEOFFS.

Dev slice: 12 of 12 accessions in the list.

**Fiscal-year coverage** -- issuer labels from companyfacts `fy`/`fp` on each
accession's facts (submissions carry none, finding #5). `COMPLETE` = 10-K plus
Q1, Q2, Q3. `XOM*` is what the predecessor CIK would give (F-62):

    dev slice: 12 accessions, 12 in the corpus list, outside: []
    XOM under predecessor CIK 0000034088: 12 filings
    
    ticker cik         fiscal years: 10-K + Q1 Q2 Q3 present (from companyfacts fy/fp)
    COST   0000909832  FY2023:FY  FY2024:FY+Q1+Q2+Q3 COMPLETE  FY2025:FY+Q1+Q2+Q3 COMPLETE  FY2026:Q1+Q2+Q3
    TGT    0000027419  FY2023:FY+Q3  FY2024:FY+Q1+Q2+Q3 COMPLETE  FY2025:FY+Q1+Q2+Q3 COMPLETE  FY2026:Q1+Q2
    JPM    0000019617  FY2023:FY+Q3  FY2024:FY+Q1+Q2+Q3 COMPLETE  FY2025:FY+Q1+Q2+Q3 COMPLETE  FY2026:Q1+Q2
    BAC    0000070858  FY2023:FY+Q3  FY2024:FY+Q1+Q2+Q3 COMPLETE  FY2025:FY+Q1+Q2+Q3 COMPLETE  FY2026:Q1+Q2
    AAPL   0000320193  FY2023:FY  FY2024:FY+Q1+Q2+Q3 COMPLETE  FY2025:FY+Q1+Q2+Q3 COMPLETE  FY2026:Q1+Q2+Q3
    NVDA   0001045810  FY2024:FY+Q3  FY2025:FY+Q1+Q2+Q3 COMPLETE  FY2026:FY+Q1+Q2+Q3 COMPLETE  FY2027:Q1+Q2
    XOM    0002115436  FY2026:Q2
    PFE    0000078003  FY2023:FY+Q3  FY2024:FY+Q1+Q2+Q3 COMPLETE  FY2025:FY+Q1+Q2+Q3 COMPLETE  FY2026:Q1+Q2
    XOM*   0000034088  FY2023:FY+Q3  FY2024:FY+Q1+Q2+Q3 COMPLETE  FY2025:FY+Q1+Q2+Q3 COMPLETE  FY2026:Q1  unlabelled: ['0000034088-26-000093']

Two complete fiscal years per company, partials at both ends, as F-29 predicted.
NVDA's labels run a year ahead of the calendar (its fiscal 2026 ended January
2026). The predecessor's 2026-08-03 10-Q is unlabelled under 0000034088 because
its facts are filed under the successor CIK.

Guard refined: a remaining paginated file whose `filingTo` ends before the window
no longer counts as a gap; the list is byte-identical before and after.
`tests/unit/test_filings.py` gains merge and page-selection tests. `make test`:
227 passed, 3 snapshots passed.

## 2026-10-01 — F-62: pinned CIKs, XOM from its predecessor; full corpus ingested

Paging support and materializer committed as `d68e1a5`.

Config: `cik` pinned on all 8 companies (quoted -- unquoted, YAML reads
`0000909832` as an integer); XOM `companyfacts_ciks: [0000034088, 0002115436]`.
`corpus.as_of: 2026-10-01` and `corpus.filings` (96 entries); `years_back` and
`form_types` gone. `ingest_company`, `window_start` (moved into the
materializer), `sectors()`, the CLI's `--tickers/--years` and
`assert_recent_covers_window` removed -- nothing read them after the switch. CLI
modes: `--corpus`, `--dev-slice`.

Materializer re-run: `# XOM: pinned cik 0000034088, SEC's ticker map now says
0002115436`; 96 filings, 12 per company, uniqueness asserted.

First corpus ingest stopped on JPM: `accession(s) ['0000019617-23-000524'] not
found` -- page 020 is listed with `filingTo: 2023-10-31` and holds that
2023-11-01 filing. Paging now follows the data (TRADEOFFS F-62); the list is
unchanged. The same run showed COST/TGT facts double-stored across the linked
and unlinked tables; promotion added.

`python -m api.ingest.cli --corpus`:

    COST  cik=0000909832 discovered=12 inserted=0 already_present=12 downloaded=0.0MB
    COST  companyfacts=0000909832 facts=24426 linked_inserted=0 linked_present=3856 linked_accessions=12 unlinked_inserted=0 unlinked_present=20570 promoted=2569
    TGT   cik=0000027419 discovered=12 inserted=0 already_present=12 downloaded=0.0MB
    TGT   companyfacts=0000027419 facts=25319 linked_inserted=0 linked_present=4239 linked_accessions=12 unlinked_inserted=0 unlinked_present=21080 promoted=2831
    JPM   cik=0000019617 discovered=12 inserted=12 already_present=0 downloaded=131.1MB
    JPM   companyfacts=0000019617 facts=53931 linked_inserted=9490 linked_present=0 linked_accessions=12 unlinked_inserted=44441 unlinked_present=0 promoted=0
    BAC   cik=0000070858 discovered=12 inserted=12 already_present=0 downloaded=126.3MB
    BAC   companyfacts=0000070858 facts=45832 linked_inserted=7260 linked_present=0 linked_accessions=12 unlinked_inserted=38572 unlinked_present=0 promoted=0
    AAPL  cik=0000320193 discovered=12 inserted=8 already_present=4 downloaded=7.7MB
    AAPL  companyfacts=0000320193 facts=25135 linked_inserted=2273 linked_present=1186 linked_accessions=12 unlinked_inserted=0 unlinked_present=21676 promoted=2273
    NVDA  cik=0001045810 discovered=12 inserted=12 already_present=0 downloaded=17.4MB
    NVDA  companyfacts=0001045810 facts=27281 linked_inserted=5005 linked_present=0 linked_accessions=12 unlinked_inserted=22276 unlinked_present=0 promoted=0
    XOM   cik=0000034088 discovered=12 inserted=12 already_present=0 downloaded=31.7MB
    XOM   companyfacts=0000034088 facts=20629 linked_inserted=3402 linked_present=0 linked_accessions=11 unlinked_inserted=17227 unlinked_present=0 promoted=0
    XOM   companyfacts=0002115436 facts=280 linked_inserted=269 linked_present=0 linked_accessions=1 unlinked_inserted=11 unlinked_present=0 promoted=0
    PFE   cik=0000078003 discovered=12 inserted=12 already_present=0 downloaded=38.3MB
    PFE   companyfacts=0000078003 facts=33186 linked_inserted=6142 linked_present=0 linked_accessions=12 unlinked_inserted=27044 unlinked_present=0 promoted=0

Second run: no inserts, no promotions. Checks: 96 filings; companies
AAPL..XOM with XOM = 0000034088; 0000034088-26-000093 FY2026 Q2, 269 facts in
`xbrl_facts`, 0 in `_unlinked`; XOM 12 linked accessions; 0 unlinked rows for any
registered filing. JPM and BAC primary documents run to ~130 MB each.

Coverage, from the stored facts:

    corpus: 96 filings, 96 unique; dev slice 12 of 12 in the list
    ticker cik         fiscal years: 10-K + Q1 Q2 Q3 present (companyfacts fy/fp per accession)
    COST   0000909832  FY2023:FY  FY2024:FY+Q1+Q2+Q3 COMPLETE  FY2025:FY+Q1+Q2+Q3 COMPLETE  FY2026:Q1+Q2+Q3
    TGT    0000027419  FY2023:FY+Q3  FY2024:FY+Q1+Q2+Q3 COMPLETE  FY2025:FY+Q1+Q2+Q3 COMPLETE  FY2026:Q1+Q2
    JPM    0000019617  FY2023:FY+Q3  FY2024:FY+Q1+Q2+Q3 COMPLETE  FY2025:FY+Q1+Q2+Q3 COMPLETE  FY2026:Q1+Q2
    BAC    0000070858  FY2023:FY+Q3  FY2024:FY+Q1+Q2+Q3 COMPLETE  FY2025:FY+Q1+Q2+Q3 COMPLETE  FY2026:Q1+Q2
    AAPL   0000320193  FY2023:FY  FY2024:FY+Q1+Q2+Q3 COMPLETE  FY2025:FY+Q1+Q2+Q3 COMPLETE  FY2026:Q1+Q2+Q3
    NVDA   0001045810  FY2024:FY+Q3  FY2025:FY+Q1+Q2+Q3 COMPLETE  FY2026:FY+Q1+Q2+Q3 COMPLETE  FY2027:Q1+Q2
    XOM    0000034088  FY2023:FY+Q3  FY2024:FY+Q1+Q2+Q3 COMPLETE  FY2025:FY+Q1+Q2+Q3 COMPLETE  FY2026:Q1+Q2
    PFE    0000078003  FY2023:FY+Q3  FY2024:FY+Q1+Q2+Q3 COMPLETE  FY2025:FY+Q1+Q2+Q3 COMPLETE  FY2026:Q1+Q2

`make test`: 225 passed (4 guard tests removed, pinned-CIK, list and mislabelled-
page tests added), 3 snapshots passed.

## 2026-10-01 — Corpus parse: 45 of 96 quarantined; freeze not written

F-62 and the list committed as `b87dc0b`.

`python -m api.parse.validate` on all 96 (2 min 12 s):

    parser_version 0e417d5495e4
    ticker accession              form   FY fp sect miss data alpha scale uncol spans items score  rows skip  status
    AAPL   0000320193-23-000106   10-K 2023 FY   23    0   46 0.762 0.976 1.000 0.994 1.000 0.994   983    6  parsed
    AAPL   0000320193-24-000006   10-Q 2024 Q1   11    0   24 0.724 0.957 1.000 0.996 1.000 0.991   522    2  parsed
    AAPL   0000320193-24-000069   10-Q 2024 Q2   11    0   24 0.704 0.957 1.000 0.997 1.000 0.991   676    2  parsed
    AAPL   0000320193-24-000081   10-Q 2024 Q3   11    0   24 0.698 0.957 1.000 0.996 1.000 0.990   678    3  parsed
    AAPL   0000320193-24-000123   10-K 2024 FY   23    0   44 0.765 0.974 1.000 0.996 1.000 0.994   957    4  parsed
    AAPL   0000320193-25-000008   10-Q 2025 Q1   11    0   23 0.736 0.955 1.000 0.994 1.000 0.990   520    3  parsed
    AAPL   0000320193-25-000057   10-Q 2025 Q2   11    0   23 0.725 0.955 1.000 0.997 1.000 0.990   670    2  parsed
    AAPL   0000320193-25-000073   10-Q 2025 Q3   11    0   25 0.701 0.957 1.000 0.996 1.000 0.990   680    3  parsed
    AAPL   0000320193-25-000079   10-K 2025 FY   23    0   43 0.765 0.974 1.000 0.995 1.000 0.994   962    5  parsed
    AAPL   0000320193-26-000006   10-Q 2026 Q1   11    0   23 0.722 0.955 1.000 0.993 1.000 0.989   554    4  parsed
    AAPL   0000320193-26-000013   10-Q 2026 Q2   11    0   25 0.733 0.958 1.000 0.995 1.000 0.991   750    4  parsed
    AAPL   0000320193-26-000020   10-Q 2026 Q3   11    0   26 0.728 0.960 1.000 0.995 1.000 0.991   756    4  parsed
    BAC    0000070858-23-000272   10-Q 2023 Q3    9    1  129 0.689 1.000 0.992 0.999 0.500 0.898     0   10  quarantined: required Items missing: ['I.2']
    BAC    0000070858-24-000122   10-K 2023 FY   21    2  159 0.748 1.000 0.969 0.997 0.600 0.913     0   21  quarantined: required Items missing: ['7', '8']
    BAC    0000070858-24-000156   10-Q 2024 Q1    9    1  119 0.701 1.000 0.992 0.998 0.500 0.898     0    9  quarantined: required Items missing: ['I.2']
    BAC    0000070858-24-000208   10-Q 2024 Q2    9    1  127 0.683 1.000 0.992 0.999 0.500 0.898     0    6  quarantined: required Items missing: ['I.2']
    BAC    0000070858-24-000280   10-Q 2024 Q3    9    1  126 0.685 1.000 0.992 0.999 0.500 0.898     0    8  quarantined: required Items missing: ['I.2']
    BAC    0000070858-25-000139   10-K 2024 FY   21    2  158 0.746 1.000 0.975 0.998 0.600 0.914     0   19  quarantined: required Items missing: ['7', '8']
    BAC    0000070858-25-000200   10-Q 2025 Q1    9    1  118 0.701 1.000 1.000 0.999 0.500 0.900     0    6  quarantined: required Items missing: ['I.2']
    BAC    0000070858-25-000268   10-Q 2025 Q2    9    1  123 0.685 1.000 0.992 0.999 0.500 0.898     0    6  quarantined: required Items missing: ['I.2']
    BAC    0000070858-25-000405   10-Q 2025 Q3    9    1  122 0.686 1.000 0.992 0.999 0.500 0.898     0    7  quarantined: required Items missing: ['I.2']
    BAC    0000070858-26-000157   10-K 2025 FY   21    2  157 0.746 1.000 0.968 0.998 0.600 0.913     0   19  quarantined: required Items missing: ['7', '8']
    BAC    0000070858-26-000249   10-Q 2026 Q1    9    1  117 0.700 1.000 1.000 0.999 0.500 0.900     0    8  quarantined: required Items missing: ['I.2']
    BAC    0000070858-26-000394   10-Q 2026 Q2    9    1  123 0.681 1.000 0.992 0.999 0.500 0.898     0    8  quarantined: required Items missing: ['I.2']
    COST   0000909832-23-000042   10-K 2023 FY   22    0   44 0.775 0.938 1.000 0.995 1.000 0.987   833    4  parsed
    COST   0000909832-23-000065   10-Q 2024 Q1   11    0   25 0.755 0.882 1.000 0.990 1.000 0.974   392    4  parsed
    COST   0000909832-24-000017   10-Q 2024 Q2   11    0   26 0.739 0.889 1.000 0.993 1.000 0.976   569    4  parsed
    COST   0000909832-24-000029   10-Q 2024 Q3   11    0   26 0.738 0.889 1.000 0.993 1.000 0.976   566    4  parsed
    COST   0000909832-24-000049   10-K 2024 FY   23    0   44 0.776 0.938 1.000 0.995 1.000 0.987   837    4  parsed
    COST   0000909832-24-000079   10-Q 2025 Q1   11    0   25 0.758 0.882 1.000 0.989 1.000 0.974   357    4  parsed
    COST   0000909832-25-000015   10-Q 2025 Q2   11    0   26 0.743 0.889 1.000 0.992 1.000 0.976   495    4  parsed
    COST   0000909832-25-000033   10-Q 2025 Q3   11    0   26 0.740 0.889 1.000 0.992 1.000 0.976   490    4  parsed
    COST   0000909832-25-000101   10-K 2025 FY   23    0   44 0.779 0.938 1.000 0.994 1.000 0.986   818    5  parsed
    COST   0000909832-25-000169   10-Q 2026 Q1   11    0   27 0.756 0.895 1.000 0.988 1.000 0.976   395    5  parsed
    COST   0000909832-26-000029   10-Q 2026 Q2   11    0   28 0.738 0.900 1.000 0.991 1.000 0.978   571    5  parsed
    COST   0000909832-26-000051   10-Q 2026 Q3   11    0   28 0.737 0.900 1.000 0.991 1.000 0.978   570    5  parsed
    JPM    0000019617-23-000524   10-Q 2023 Q3    9    2  243 0.701 1.000 0.984 0.995 0.000 0.796     0   36  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0000019617-24-000225   10-K 2023 FY   22    0  268 0.754 1.000 0.993 0.997 1.000 0.998  7776   27  parsed
    JPM    0000019617-24-000326   10-Q 2024 Q1    9    2  218 0.716 1.000 1.000 0.994 0.000 0.799     0   33  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0000019617-24-000453   10-Q 2024 Q2    9    2  232 0.700 1.000 0.983 0.996 0.000 0.796     0   31  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0000019617-24-000611   10-Q 2024 Q3    9    2  232 0.701 1.000 0.983 0.995 0.000 0.796     0   37  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0000019617-25-000270   10-K 2024 FY   22    0  267 0.755 1.000 0.993 0.996 1.000 0.998  7805   34  parsed
    JPM    0000019617-25-000421   10-Q 2025 Q1    9    2  219 0.713 1.000 1.000 0.997 0.000 0.799     0   20  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0000019617-25-000615   10-Q 2025 Q2    9    2  234 0.694 1.000 0.983 0.996 0.000 0.796     0   27  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0001628280-25-048859   10-Q 2025 Q3    9    2  233 0.697 1.000 0.983 0.996 0.000 0.796     0   33  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0001628280-26-008131   10-K 2025 FY   22    0  272 0.752 1.000 0.993 0.995 1.000 0.998  7921   38  parsed
    JPM    0001628280-26-029344   10-Q 2026 Q1    9    2  219 0.714 1.000 1.000 0.997 0.000 0.799     0   16  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0001628280-26-054343   10-Q 2026 Q2    9    2  228 0.695 1.000 0.982 0.997 0.000 0.796     0   20  quarantined: required Items missing: ['I.1', 'I.2']
    NVDA   0001045810-23-000227   10-Q 2024 Q3    9    0   41 0.762 1.000 1.000 0.998 1.000 1.000   964    2  parsed
    NVDA   0001045810-24-000029   10-K 2024 FY   23    0   53 0.790 1.000 1.000 0.993 1.000 0.999  1207    9  parsed
    NVDA   0001045810-24-000124   10-Q 2025 Q1    9    0   43 0.766 1.000 1.000 0.993 1.000 0.999   746    5  parsed
    NVDA   0001045810-24-000264   10-Q 2025 Q2    9    0   45 0.755 1.000 1.000 0.995 1.000 0.999   988    5  parsed
    NVDA   0001045810-24-000316   10-Q 2025 Q3    9    0   44 0.754 1.000 1.000 0.996 1.000 0.999   984    4  parsed
    NVDA   0001045810-25-000023   10-K 2025 FY   23    0   56 0.789 1.000 1.000 0.993 1.000 0.999  1220    9  parsed
    NVDA   0001045810-25-000116   10-Q 2026 Q1    9    0   40 0.768 1.000 1.000 0.994 1.000 0.999   721    4  parsed
    NVDA   0001045810-25-000209   10-Q 2026 Q2    9    0   39 0.752 1.000 1.000 0.994 1.000 0.999   940    6  parsed
    NVDA   0001045810-25-000230   10-Q 2026 Q3    9    0   38 0.761 1.000 1.000 0.992 1.000 0.998   943    8  parsed
    NVDA   0001045810-26-000021   10-K 2026 FY   23    0   49 0.790 1.000 1.000 0.991 1.000 0.998  1117   10  parsed
    NVDA   0001045810-26-000052   10-Q 2027 Q1    9    0   37 0.769 1.000 1.000 0.994 1.000 0.999   699    4  parsed
    NVDA   0001045810-26-000075   10-Q 2027 Q2    9    0   41 0.753 1.000 1.000 0.996 1.000 0.999   996    4  parsed
    PFE    0000078003-23-000115   10-Q 2023 Q3    9    2   46 0.760 1.000 1.000 0.989 0.000 0.798     0   20  quarantined: required Items missing: ['I.1', 'I.2']
    PFE    0000078003-24-000039   10-K 2023 FY    0    5   78 0.784 1.000 1.000 0.988 0.000 0.798     0   37  quarantined: 0 sections < 5; required Items missing: ['1', '1A', '7', '7A', '8']; 10-K has no Item 1A
    PFE    0000078003-24-000107   10-Q 2024 Q1    9    2   44 0.773 1.000 1.000 0.982 0.000 0.796     0   22  quarantined: required Items missing: ['I.1', 'I.2']
    PFE    0000078003-24-000166   10-Q 2024 Q2    9    2   50 0.758 1.000 1.000 0.988 0.000 0.798     0   22  quarantined: required Items missing: ['I.1', 'I.2']
    PFE    0000078003-24-000191   10-Q 2024 Q3    9    2   50 0.758 1.000 1.000 0.985 0.000 0.797     0   27  quarantined: required Items missing: ['I.1', 'I.2']
    PFE    0000078003-25-000054   10-K 2024 FY    0    5   86 0.783 1.000 1.000 0.984 0.000 0.797     0   47  quarantined: 0 sections < 5; required Items missing: ['1', '1A', '7', '7A', '8']; 10-K has no Item 1A
    PFE    0000078003-25-000114   10-Q 2025 Q1    9    2   41 0.774 1.000 1.000 0.974 0.000 0.795     0   30  quarantined: required Items missing: ['I.1', 'I.2']
    PFE    0000078003-25-000138   10-Q 2025 Q2    9    2   50 0.757 1.000 1.000 0.984 0.000 0.797     0   27  quarantined: required Items missing: ['I.1', 'I.2']
    PFE    0000078003-25-000150   10-Q 2025 Q3    9    2   50 0.760 1.000 1.000 0.986 0.000 0.797     0   24  quarantined: required Items missing: ['I.1', 'I.2']
    PFE    0000078003-26-000026   10-K 2025 FY    0    5   82 0.785 1.000 1.000 0.986 0.000 0.797     0   40  quarantined: 0 sections < 5; required Items missing: ['1', '1A', '7', '7A', '8']; 10-K has no Item 1A
    PFE    0000078003-26-000054   10-Q 2026 Q1    9    2   40 0.773 1.000 1.000 0.984 0.000 0.797     0   20  quarantined: required Items missing: ['I.1', 'I.2']
    PFE    0000078003-26-000095   10-Q 2026 Q2    9    2   48 0.757 1.000 1.000 0.989 0.000 0.798     0   20  quarantined: required Items missing: ['I.1', 'I.2']
    TGT    0000027419-23-000052   10-Q 2023 Q3   11    0   29 0.716 1.000 1.000 0.980 1.000 0.996   553   11  parsed
    TGT    0000027419-24-000032   10-K 2023 FY   23    0   60 0.768 0.977 1.000 0.986 1.000 0.993   984   14  parsed
    TGT    0000027419-24-000129   10-Q 2024 Q1   11    0   28 0.730 1.000 1.000 0.982 1.000 0.996   385    7  parsed
    TGT    0000027419-24-000152   10-Q 2024 Q2   11    0   30 0.710 1.000 1.000 0.985 1.000 0.997   517    8  parsed
    TGT    0000027419-24-000179   10-Q 2024 Q3   11    0   30 0.711 1.000 1.000 0.982 1.000 0.996   532   10  parsed
    TGT    0000027419-25-000018   10-K 2024 FY   23    0   62 0.773 1.000 1.000 0.988 1.000 0.998   973   12  parsed
    TGT    0000027419-25-000101   10-Q 2025 Q1   11    0   30 0.734 1.000 1.000 0.981 1.000 0.996   406    8  parsed
    TGT    0000027419-25-000118   10-Q 2025 Q2   11    0   33 0.718 1.000 1.000 0.986 1.000 0.997   546    8  parsed
    TGT    0000027419-25-000126   10-Q 2025 Q3   11    0   34 0.720 1.000 1.000 0.983 1.000 0.997   576   10  parsed
    TGT    0000027419-26-000016   10-K 2025 FY   23    0   64 0.774 1.000 1.000 0.987 1.000 0.997   977   13  parsed
    TGT    0000027419-26-000022   10-Q 2026 Q1   11    0   30 0.736 1.000 1.000 0.980 1.000 0.996   401    8  parsed
    TGT    0000027419-26-000042   10-Q 2026 Q2   11    0   32 0.720 1.000 1.000 0.979 1.000 0.996   547   12  parsed
    XOM    0000034088-23-000056   10-Q 2023 Q3    7    1   36 0.715 1.000 1.000 1.000 0.500 0.900     0    0  quarantined: required Items missing: ['I.1']
    XOM    0000034088-24-000018   10-K 2023 FY    0    5  113 0.738 1.000 0.982 1.000 0.000 0.796     0    1  quarantined: 0 sections < 5; required Items missing: ['1', '1A', '7', '7A', '8']; 10-K has no Item 1A
    XOM    0000034088-24-000029   10-Q 2024 Q1    7    1   35 0.740 1.000 1.000 1.000 0.500 0.900     0    0  quarantined: required Items missing: ['I.1']
    XOM    0000034088-24-000050   10-Q 2024 Q2    7    1   40 0.715 1.000 1.000 1.000 0.500 0.900     0    0  quarantined: required Items missing: ['I.1']
    XOM    0000034088-24-000068   10-Q 2024 Q3    7    1   40 0.714 1.000 1.000 1.000 0.500 0.900     0    0  quarantined: required Items missing: ['I.1']
    XOM    0000034088-25-000010   10-K 2024 FY    0    5  118 0.739 1.000 0.958 1.000 0.000 0.791     0    1  quarantined: 0 sections < 5; required Items missing: ['1', '1A', '7', '7A', '8']; 10-K has no Item 1A
    XOM    0000034088-25-000024   10-Q 2025 Q1    7    1   38 0.730 1.000 0.947 1.000 0.500 0.889     0    0  quarantined: required Items missing: ['I.1']
    XOM    0000034088-25-000042   10-Q 2025 Q2    7    1   44 0.695 1.000 0.909 1.000 0.500 0.882     0    0  quarantined: required Items missing: ['I.1']
    XOM    0000034088-25-000061   10-Q 2025 Q3    7    1   44 0.697 1.000 0.909 1.000 0.500 0.882     0    0  quarantined: required Items missing: ['I.1']
    XOM    0000034088-26-000045   10-K 2025 FY    0    5  116 0.739 1.000 0.983 0.999 0.000 0.796     0    2  quarantined: 0 sections < 5; required Items missing: ['1', '1A', '7', '7A', '8']; 10-K has no Item 1A
    XOM    0000034088-26-000067   10-Q 2026 Q1    8    1   34 0.732 1.000 0.941 0.999 0.500 0.888     0    1  quarantined: required Items missing: ['I.1']
    XOM    0000034088-26-000093   10-Q 2026 Q2    8    1   36 0.703 1.000 0.889 0.999 0.500 0.878     0    2  quarantined: required Items missing: ['I.1']

Parsed: all 48 AAPL, COST, NVDA, TGT filings, and JPM's three 10-Ks.
Quarantined: BAC 12/12, JPM 9/12 (every 10-Q), PFE 12/12, XOM 12/12. Not
patched, by instruction.

Diagnosis, from the blocks that start with "Item n" or "Part":
- Headings as single-cell layout tables, invisible to section detection (F-63):
  PFE and XOM 10-Ks (every Item), BAC 10-K Items 7 and 8, XOM 10-Q Item 1, PFE
  10-Q Part headings.
- BAC 10-Qs: MD&A before Item 1 with a Part II block between, so Items 2-4 are
  tagged Part II (F-64).
- JPM 10-Qs: no Part I Item 1/2 headings at all; a cross-reference index stands
  in for them (F-65).
- JPM 10-Ks pass but are mis-sectioned: Items 7 and 8 are 395- and 368-char
  cross-reference stubs, 1,008,217 of 1,208,667 chars land under Item 15, and
  Items 1-14 are all Part I (F-66).

Chunk, embed, resolve on the 51 parsed filings: 8,868 chunks; 4 over 512 tokens
(F-67), so `python -m api.index.embed` refused the run at its pre-write check --
`EmbeddingCheckError: 4 chunks exceed max_seq_length, e.g.
[('0000019617-25-000270:2228.0:2228.0', 747), ...]` -- and nothing was embedded.
The re-chunk nulled the 12 dev filings' embeddings; their vectors are in
`embedding_cache` and refill once the check passes. Resolve: 57,959 of 58,025
spans (0.999; 1.000 within Items), 66 before the first Item; JPM 10-Ks ~7,800
spans each, all resolved -- under F-66's wrong Item labels.

No freeze record is written: 45 quarantined filings and 3 mis-sectioned ones would
be frozen into the corpus. Phase 3 stays closed.

## 2026-10-01 — Content check on required Items (before any parser fix)

Findings committed as `d3d3bc6`.

Required-Item lengths across the 48 clean filings (AAPL, COST, NVDA, TGT):

    48 clean filings (AAPL, COST, NVDA, TGT)
    form  item    n     min     p10  median     max  smallest (ticker accession)
    10-K  1      12   15096   15699   19475   54801  AAPL 0000320193-23-000106
    10-K  1A     12   33805   40040   67872  114868  TGT 0000027419-24-000032
    10-K  7      12   15352   15499   34192   40282  AAPL 0000320193-24-000123
    10-K  7A     12    2746    2786    3295    4474  TGT 0000027419-24-000032
    10-K  8      12     206     206   75077   87036  NVDA 0001045810-24-000029
    10-Q  I.1    36   18054   20723   29406   58378  TGT 0000027419-24-000129
    10-Q  I.2    36   15310   17444   28685   38455  AAPL 0000320193-24-000006

Each floor in `parser.min_required_item_chars` is the measured minimum, as is.
Item 8's 206 is NVDA: its Item 8 points to Item 15, a legal layout (F-68), so the
Item 8 floor cannot catch stubs; Items 7 and 7A do.

`check` now quarantines any required Item shorter than its floor. Re-validated on
96 (`validate.py` is outside the parser hash, so `parser_version` stays
0e417d5495e4): 48 parsed -- every clean filing still passes -- and all three JPM
10-Ks now quarantine: `required Item too short: Item 7 is 395 chars < 15352;
Item 7A is 269 chars < 2746`. `make test`: 227 passed, 3 snapshots passed.

## 2026-10-01 — F-63: heading tables

Content check committed as `b911278`.

`is_heading_table`: a short table whose first non-empty row is its only row
matching an Item or Part heading; read without in-document link text. Measured
first: the 48 clean filings contain no heading-like table at all; PFE and XOM
heading tables are one row (PFE splits "ITEM 1." | "BUSINESS"), BAC's 10-K Items
7 and 8 are 3- and 2-row (title row and a "Table of Contents" link), BAC's 10-Q
Part II index is 6 rows.

Section lists, previous detector (`git show HEAD`) vs new, all 96:

    BAC   0000070858-24-000122 10-K: ['I.1', 'I.1A', 'I.1B', 'I.1C', 'I.2', 'I.3', 'I.4', 'II.5', 'II.6', 'II.7A', 'II.9', 'II.9A', 'II.9B', 'II.9C', 'III.10', 'III.11', 'III.12', 'III.13', 'III.14', 'IV.15', 'IV.16'] -> ['I.1', 'I.1A', 'I.1B', 'I.1C', 'I.2', 'I.3', 'I.4', 'II.5', 'II.6', 'II.7', 'II.7A', 'II.8', 'II.9', 'II.9A', 'II.9B', 'II.9C', 'III.10', 'III.11', 'III.12', 'III.13', 'III.14', 'IV.15', 'IV.16']
    BAC   0000070858-25-000139 10-K: ['I.1', 'I.1A', 'I.1B', 'I.1C', 'I.2', 'I.3', 'I.4', 'II.5', 'II.6', 'II.7A', 'II.9', 'II.9A', 'II.9B', 'II.9C', 'III.10', 'III.11', 'III.12', 'III.13', 'III.14', 'IV.15', 'IV.16'] -> ['I.1', 'I.1A', 'I.1B', 'I.1C', 'I.2', 'I.3', 'I.4', 'II.5', 'II.6', 'II.7', 'II.7A', 'II.8', 'II.9', 'II.9A', 'II.9B', 'II.9C', 'III.10', 'III.11', 'III.12', 'III.13', 'III.14', 'IV.15', 'IV.16']
    BAC   0000070858-26-000157 10-K: ['I.1', 'I.1A', 'I.1B', 'I.1C', 'I.2', 'I.3', 'I.4', 'II.5', 'II.6', 'II.7A', 'II.9', 'II.9A', 'II.9B', 'II.9C', 'III.10', 'III.11', 'III.12', 'III.13', 'III.14', 'IV.15', 'IV.16'] -> ['I.1', 'I.1A', 'I.1B', 'I.1C', 'I.2', 'I.3', 'I.4', 'II.5', 'II.6', 'II.7', 'II.7A', 'II.8', 'II.9', 'II.9A', 'II.9B', 'II.9C', 'III.10', 'III.11', 'III.12', 'III.13', 'III.14', 'IV.15', 'IV.16']
    PFE   0000078003-23-000115 10-Q: ['1', '2', '3', '4', '1', '1A', '2', '5', '6'] -> ['I.1', 'I.2', 'I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6']
    PFE   0000078003-24-000039 10-K: [] -> ['I.1', 'I.1A', 'I.1C', 'I.2', 'I.3', 'II.5', 'II.6', 'II.7', 'II.7A', 'II.8', 'II.9', 'II.9A', 'II.9B', 'III.10', 'III.11', 'III.12', 'III.13', 'III.14', 'IV.15', 'IV.16']
    PFE   0000078003-24-000107 10-Q: ['1', '2', '3', '4', '1', '1A', '2', '5', '6'] -> ['I.1', 'I.2', 'I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6']
    PFE   0000078003-24-000166 10-Q: ['1', '2', '3', '4', '1', '1A', '2', '5', '6'] -> ['I.1', 'I.2', 'I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6']
    PFE   0000078003-24-000191 10-Q: ['1', '2', '3', '4', '1', '1A', '2', '5', '6'] -> ['I.1', 'I.2', 'I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6']
    PFE   0000078003-25-000054 10-K: [] -> ['I.1', 'I.1A', 'I.1C', 'I.2', 'I.3', 'II.5', 'II.6', 'II.7', 'II.7A', 'II.8', 'II.9', 'II.9A', 'II.9B', 'III.10', 'III.11', 'III.12', 'III.13', 'III.14', 'IV.15', 'IV.16']
    PFE   0000078003-25-000114 10-Q: ['1', '2', '3', '4', '1', '1A', '2', '5', '6'] -> ['I.1', 'I.2', 'I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6']
    PFE   0000078003-25-000138 10-Q: ['1', '2', '3', '4', '1', '1A', '2', '5', '6'] -> ['I.1', 'I.2', 'I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6']
    PFE   0000078003-25-000150 10-Q: ['1', '2', '3', '4', '1', '1A', '2', '5', '6'] -> ['I.1', 'I.2', 'I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6']
    PFE   0000078003-26-000026 10-K: [] -> ['I.1', 'I.1A', 'I.1C', 'I.2', 'I.3', 'II.5', 'II.6', 'II.7', 'II.7A', 'II.8', 'II.9', 'II.9A', 'II.9B', 'III.10', 'III.11', 'III.12', 'III.13', 'III.14', 'IV.15', 'IV.16']
    PFE   0000078003-26-000054 10-Q: ['1', '2', '3', '4', '1', '1A', '2', '5', '6'] -> ['I.1', 'I.2', 'I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6']
    PFE   0000078003-26-000095 10-Q: ['1', '2', '3', '4', '1', '1A', '2', '5', '6'] -> ['I.1', 'I.2', 'I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6']
    XOM   0000034088-23-000056 10-Q: ['I.2', 'I.3', 'I.4', 'II.1', 'II.2', 'II.5', 'II.6'] -> ['I.1', 'I.2', 'I.3', 'I.4', 'II.1', 'II.2', 'II.5', 'II.6']
    XOM   0000034088-24-000018 10-K: [] -> ['I.1', 'I.1A', 'I.1B', 'I.1C', 'I.2', 'I.3', 'I.4', 'II.5', 'II.7', 'II.7A', 'II.8', 'II.9', 'II.9A', 'II.9B', 'II.9C', 'III.10', 'III.11', 'III.12', 'III.13', 'III.14', 'IV.15', 'IV.16']
    XOM   0000034088-24-000029 10-Q: ['I.2', 'I.3', 'I.4', 'II.1', 'II.2', 'II.5', 'II.6'] -> ['I.1', 'I.2', 'I.3', 'I.4', 'II.1', 'II.2', 'II.5', 'II.6']
    XOM   0000034088-24-000050 10-Q: ['I.2', 'I.3', 'I.4', 'II.1', 'II.2', 'II.5', 'II.6'] -> ['I.1', 'I.2', 'I.3', 'I.4', 'II.1', 'II.2', 'II.5', 'II.6']
    XOM   0000034088-24-000068 10-Q: ['I.2', 'I.3', 'I.4', 'II.1', 'II.2', 'II.5', 'II.6'] -> ['I.1', 'I.2', 'I.3', 'I.4', 'II.1', 'II.2', 'II.5', 'II.6']
    XOM   0000034088-25-000010 10-K: [] -> ['I.1', 'I.1A', 'I.1B', 'I.1C', 'I.2', 'I.3', 'I.4', 'II.5', 'II.7', 'II.7A', 'II.8', 'II.9', 'II.9A', 'II.9B', 'II.9C', 'III.10', 'III.11', 'III.12', 'III.13', 'III.14', 'IV.15', 'IV.16']
    XOM   0000034088-25-000024 10-Q: ['I.2', 'I.3', 'I.4', 'II.1', 'II.2', 'II.5', 'II.6'] -> ['I.1', 'I.2', 'I.3', 'I.4', 'II.1', 'II.2', 'II.5', 'II.6']
    XOM   0000034088-25-000042 10-Q: ['I.2', 'I.3', 'I.4', 'II.1', 'II.2', 'II.5', 'II.6'] -> ['I.1', 'I.2', 'I.3', 'I.4', 'II.1', 'II.2', 'II.5', 'II.6']
    XOM   0000034088-25-000061 10-Q: ['I.2', 'I.3', 'I.4', 'II.1', 'II.2', 'II.5', 'II.6'] -> ['I.1', 'I.2', 'I.3', 'I.4', 'II.1', 'II.2', 'II.5', 'II.6']
    XOM   0000034088-26-000045 10-K: [] -> ['I.1', 'I.1A', 'I.1B', 'I.1C', 'I.2', 'I.3', 'I.4', 'II.5', 'II.7', 'II.7A', 'II.8', 'II.9', 'II.9A', 'II.9B', 'II.9C', 'III.10', 'III.11', 'III.12', 'III.13', 'III.14', 'IV.15', 'IV.16']
    XOM   0000034088-26-000067 10-Q: ['I.2', 'I.3', 'I.7A', 'I.4', 'II.1', 'II.2', 'II.5', 'II.6'] -> ['I.1', 'I.2', 'I.3', 'I.7A', 'I.4', 'II.1', 'II.2', 'II.5', 'II.6']
    XOM   0000034088-26-000093 10-Q: ['I.2', 'I.3', 'I.7A', 'I.4', 'II.1', 'II.2', 'II.5', 'II.6'] -> ['I.1', 'I.2', 'I.3', 'I.7A', 'I.4', 'II.1', 'II.2', 'II.5', 'II.6']
    identical section lists: 69 of 96; clean filings changed: 0

`python -m api.parse.validate` (`parser_version` c04582d899a9):

    parser_version c04582d899a9
    ticker accession              form   FY fp sect miss data alpha scale uncol spans items score  rows skip  status
    AAPL   0000320193-23-000106   10-K 2023 FY   23    0   46 0.762 0.976 1.000 0.994 1.000 0.994   983    6  parsed
    AAPL   0000320193-24-000006   10-Q 2024 Q1   11    0   24 0.724 0.957 1.000 0.996 1.000 0.991   522    2  parsed
    AAPL   0000320193-24-000069   10-Q 2024 Q2   11    0   24 0.704 0.957 1.000 0.997 1.000 0.991   676    2  parsed
    AAPL   0000320193-24-000081   10-Q 2024 Q3   11    0   24 0.698 0.957 1.000 0.996 1.000 0.990   678    3  parsed
    AAPL   0000320193-24-000123   10-K 2024 FY   23    0   44 0.765 0.974 1.000 0.996 1.000 0.994   957    4  parsed
    AAPL   0000320193-25-000008   10-Q 2025 Q1   11    0   23 0.736 0.955 1.000 0.994 1.000 0.990   520    3  parsed
    AAPL   0000320193-25-000057   10-Q 2025 Q2   11    0   23 0.725 0.955 1.000 0.997 1.000 0.990   670    2  parsed
    AAPL   0000320193-25-000073   10-Q 2025 Q3   11    0   25 0.701 0.957 1.000 0.996 1.000 0.990   680    3  parsed
    AAPL   0000320193-25-000079   10-K 2025 FY   23    0   43 0.765 0.974 1.000 0.995 1.000 0.994   962    5  parsed
    AAPL   0000320193-26-000006   10-Q 2026 Q1   11    0   23 0.722 0.955 1.000 0.993 1.000 0.989   554    4  parsed
    AAPL   0000320193-26-000013   10-Q 2026 Q2   11    0   25 0.733 0.958 1.000 0.995 1.000 0.991   750    4  parsed
    AAPL   0000320193-26-000020   10-Q 2026 Q3   11    0   26 0.728 0.960 1.000 0.995 1.000 0.991   756    4  parsed
    BAC    0000070858-23-000272   10-Q 2023 Q3    9    1  129 0.689 1.000 0.992 0.999 0.500 0.898     0   10  quarantined: required Items missing: ['I.2']
    BAC    0000070858-24-000122   10-K 2023 FY   23    0  159 0.748 1.000 0.969 0.997 1.000 0.993     0   21  quarantined: required Item too short: Item 7A is 217 chars < 2746
    BAC    0000070858-24-000156   10-Q 2024 Q1    9    1  119 0.701 1.000 0.992 0.998 0.500 0.898     0    9  quarantined: required Items missing: ['I.2']
    BAC    0000070858-24-000208   10-Q 2024 Q2    9    1  127 0.683 1.000 0.992 0.999 0.500 0.898     0    6  quarantined: required Items missing: ['I.2']
    BAC    0000070858-24-000280   10-Q 2024 Q3    9    1  126 0.685 1.000 0.992 0.999 0.500 0.898     0    8  quarantined: required Items missing: ['I.2']
    BAC    0000070858-25-000139   10-K 2024 FY   23    0  158 0.746 1.000 0.975 0.998 1.000 0.994     0   19  quarantined: required Item too short: Item 7A is 217 chars < 2746
    BAC    0000070858-25-000200   10-Q 2025 Q1    9    1  118 0.701 1.000 1.000 0.999 0.500 0.900     0    6  quarantined: required Items missing: ['I.2']
    BAC    0000070858-25-000268   10-Q 2025 Q2    9    1  123 0.685 1.000 0.992 0.999 0.500 0.898     0    6  quarantined: required Items missing: ['I.2']
    BAC    0000070858-25-000405   10-Q 2025 Q3    9    1  122 0.686 1.000 0.992 0.999 0.500 0.898     0    7  quarantined: required Items missing: ['I.2']
    BAC    0000070858-26-000157   10-K 2025 FY   23    0  157 0.746 1.000 0.968 0.998 1.000 0.993     0   19  quarantined: required Item too short: Item 7A is 217 chars < 2746
    BAC    0000070858-26-000249   10-Q 2026 Q1    9    1  117 0.700 1.000 1.000 0.999 0.500 0.900     0    8  quarantined: required Items missing: ['I.2']
    BAC    0000070858-26-000394   10-Q 2026 Q2    9    1  123 0.681 1.000 0.992 0.999 0.500 0.898     0    8  quarantined: required Items missing: ['I.2']
    COST   0000909832-23-000042   10-K 2023 FY   22    0   44 0.775 0.938 1.000 0.995 1.000 0.987   833    4  parsed
    COST   0000909832-23-000065   10-Q 2024 Q1   11    0   25 0.755 0.882 1.000 0.990 1.000 0.974   392    4  parsed
    COST   0000909832-24-000017   10-Q 2024 Q2   11    0   26 0.739 0.889 1.000 0.993 1.000 0.976   569    4  parsed
    COST   0000909832-24-000029   10-Q 2024 Q3   11    0   26 0.738 0.889 1.000 0.993 1.000 0.976   566    4  parsed
    COST   0000909832-24-000049   10-K 2024 FY   23    0   44 0.776 0.938 1.000 0.995 1.000 0.987   837    4  parsed
    COST   0000909832-24-000079   10-Q 2025 Q1   11    0   25 0.758 0.882 1.000 0.989 1.000 0.974   357    4  parsed
    COST   0000909832-25-000015   10-Q 2025 Q2   11    0   26 0.743 0.889 1.000 0.992 1.000 0.976   495    4  parsed
    COST   0000909832-25-000033   10-Q 2025 Q3   11    0   26 0.740 0.889 1.000 0.992 1.000 0.976   490    4  parsed
    COST   0000909832-25-000101   10-K 2025 FY   23    0   44 0.779 0.938 1.000 0.994 1.000 0.986   818    5  parsed
    COST   0000909832-25-000169   10-Q 2026 Q1   11    0   27 0.756 0.895 1.000 0.988 1.000 0.976   395    5  parsed
    COST   0000909832-26-000029   10-Q 2026 Q2   11    0   28 0.738 0.900 1.000 0.991 1.000 0.978   571    5  parsed
    COST   0000909832-26-000051   10-Q 2026 Q3   11    0   28 0.737 0.900 1.000 0.991 1.000 0.978   570    5  parsed
    JPM    0000019617-23-000524   10-Q 2023 Q3    9    2  243 0.701 1.000 0.984 0.995 0.000 0.796     0   36  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0000019617-24-000225   10-K 2023 FY   22    0  268 0.754 1.000 0.993 0.997 1.000 0.998     0   27  quarantined: required Item too short: Item 7 is 395 chars < 15352; Item 7A is 269 chars < 2746
    JPM    0000019617-24-000326   10-Q 2024 Q1    9    2  218 0.716 1.000 1.000 0.994 0.000 0.799     0   33  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0000019617-24-000453   10-Q 2024 Q2    9    2  232 0.700 1.000 0.983 0.996 0.000 0.796     0   31  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0000019617-24-000611   10-Q 2024 Q3    9    2  232 0.701 1.000 0.983 0.995 0.000 0.796     0   37  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0000019617-25-000270   10-K 2024 FY   22    0  267 0.755 1.000 0.993 0.996 1.000 0.998     0   34  quarantined: required Item too short: Item 7 is 395 chars < 15352; Item 7A is 269 chars < 2746
    JPM    0000019617-25-000421   10-Q 2025 Q1    9    2  219 0.713 1.000 1.000 0.997 0.000 0.799     0   20  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0000019617-25-000615   10-Q 2025 Q2    9    2  234 0.694 1.000 0.983 0.996 0.000 0.796     0   27  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0001628280-25-048859   10-Q 2025 Q3    9    2  233 0.697 1.000 0.983 0.996 0.000 0.796     0   33  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0001628280-26-008131   10-K 2025 FY   22    0  272 0.752 1.000 0.993 0.995 1.000 0.998     0   38  quarantined: required Item too short: Item 7 is 395 chars < 15352; Item 7A is 269 chars < 2746
    JPM    0001628280-26-029344   10-Q 2026 Q1    9    2  219 0.714 1.000 1.000 0.997 0.000 0.799     0   16  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0001628280-26-054343   10-Q 2026 Q2    9    2  228 0.695 1.000 0.982 0.997 0.000 0.796     0   20  quarantined: required Items missing: ['I.1', 'I.2']
    NVDA   0001045810-23-000227   10-Q 2024 Q3    9    0   41 0.762 1.000 1.000 0.998 1.000 1.000   964    2  parsed
    NVDA   0001045810-24-000029   10-K 2024 FY   23    0   53 0.790 1.000 1.000 0.993 1.000 0.999  1207    9  parsed
    NVDA   0001045810-24-000124   10-Q 2025 Q1    9    0   43 0.766 1.000 1.000 0.993 1.000 0.999   746    5  parsed
    NVDA   0001045810-24-000264   10-Q 2025 Q2    9    0   45 0.755 1.000 1.000 0.995 1.000 0.999   988    5  parsed
    NVDA   0001045810-24-000316   10-Q 2025 Q3    9    0   44 0.754 1.000 1.000 0.996 1.000 0.999   984    4  parsed
    NVDA   0001045810-25-000023   10-K 2025 FY   23    0   56 0.789 1.000 1.000 0.993 1.000 0.999  1220    9  parsed
    NVDA   0001045810-25-000116   10-Q 2026 Q1    9    0   40 0.768 1.000 1.000 0.994 1.000 0.999   721    4  parsed
    NVDA   0001045810-25-000209   10-Q 2026 Q2    9    0   39 0.752 1.000 1.000 0.994 1.000 0.999   940    6  parsed
    NVDA   0001045810-25-000230   10-Q 2026 Q3    9    0   38 0.761 1.000 1.000 0.992 1.000 0.998   943    8  parsed
    NVDA   0001045810-26-000021   10-K 2026 FY   23    0   49 0.790 1.000 1.000 0.991 1.000 0.998  1117   10  parsed
    NVDA   0001045810-26-000052   10-Q 2027 Q1    9    0   37 0.769 1.000 1.000 0.994 1.000 0.999   699    4  parsed
    NVDA   0001045810-26-000075   10-Q 2027 Q2    9    0   41 0.753 1.000 1.000 0.996 1.000 0.999   996    4  parsed
    PFE    0000078003-23-000115   10-Q 2023 Q3    9    0   46 0.760 1.000 1.000 0.989 1.000 0.998  1856   20  parsed
    PFE    0000078003-24-000039   10-K 2023 FY   20    0   78 0.784 1.000 1.000 0.988 1.000 0.998     0   37  quarantined: required Item too short: Item 7A is 289 chars < 2746
    PFE    0000078003-24-000107   10-Q 2024 Q1    9    0   44 0.773 1.000 1.000 0.982 1.000 0.996  1194   22  parsed
    PFE    0000078003-24-000166   10-Q 2024 Q2    9    0   50 0.758 1.000 1.000 0.988 1.000 0.998  1775   22  parsed
    PFE    0000078003-24-000191   10-Q 2024 Q3    9    0   50 0.758 1.000 1.000 0.985 1.000 0.997  1797   27  parsed
    PFE    0000078003-25-000054   10-K 2024 FY   20    0   86 0.783 1.000 1.000 0.984 1.000 0.997     0   47  quarantined: required Item too short: Item 7A is 289 chars < 2746
    PFE    0000078003-25-000114   10-Q 2025 Q1    9    0   41 0.774 1.000 1.000 0.974 1.000 0.995  1112   30  parsed
    PFE    0000078003-25-000138   10-Q 2025 Q2    9    0   50 0.757 1.000 1.000 0.984 1.000 0.997  1662   27  parsed
    PFE    0000078003-25-000150   10-Q 2025 Q3    9    0   50 0.760 1.000 1.000 0.986 1.000 0.997  1724   24  parsed
    PFE    0000078003-26-000026   10-K 2025 FY   20    0   82 0.785 1.000 1.000 0.986 1.000 0.997     0   40  quarantined: required Item too short: Item 7A is 289 chars < 2746
    PFE    0000078003-26-000054   10-Q 2026 Q1    9    0   40 0.773 1.000 1.000 0.984 1.000 0.997  1207   20  parsed
    PFE    0000078003-26-000095   10-Q 2026 Q2    9    0   48 0.757 1.000 1.000 0.989 1.000 0.998  1789   20  parsed
    TGT    0000027419-23-000052   10-Q 2023 Q3   11    0   29 0.716 1.000 1.000 0.980 1.000 0.996   553   11  parsed
    TGT    0000027419-24-000032   10-K 2023 FY   23    0   60 0.768 0.977 1.000 0.986 1.000 0.993   984   14  parsed
    TGT    0000027419-24-000129   10-Q 2024 Q1   11    0   28 0.730 1.000 1.000 0.982 1.000 0.996   385    7  parsed
    TGT    0000027419-24-000152   10-Q 2024 Q2   11    0   30 0.710 1.000 1.000 0.985 1.000 0.997   517    8  parsed
    TGT    0000027419-24-000179   10-Q 2024 Q3   11    0   30 0.711 1.000 1.000 0.982 1.000 0.996   532   10  parsed
    TGT    0000027419-25-000018   10-K 2024 FY   23    0   62 0.773 1.000 1.000 0.988 1.000 0.998   973   12  parsed
    TGT    0000027419-25-000101   10-Q 2025 Q1   11    0   30 0.734 1.000 1.000 0.981 1.000 0.996   406    8  parsed
    TGT    0000027419-25-000118   10-Q 2025 Q2   11    0   33 0.718 1.000 1.000 0.986 1.000 0.997   546    8  parsed
    TGT    0000027419-25-000126   10-Q 2025 Q3   11    0   34 0.720 1.000 1.000 0.983 1.000 0.997   576   10  parsed
    TGT    0000027419-26-000016   10-K 2025 FY   23    0   64 0.774 1.000 1.000 0.987 1.000 0.997   977   13  parsed
    TGT    0000027419-26-000022   10-Q 2026 Q1   11    0   30 0.736 1.000 1.000 0.980 1.000 0.996   401    8  parsed
    TGT    0000027419-26-000042   10-Q 2026 Q2   11    0   32 0.720 1.000 1.000 0.979 1.000 0.996   547   12  parsed
    XOM    0000034088-23-000056   10-Q 2023 Q3    8    0   36 0.715 1.000 1.000 1.000 1.000 1.000   883    0  parsed
    XOM    0000034088-24-000018   10-K 2023 FY   22    0  113 0.738 1.000 0.982 1.000 1.000 0.996     0    1  quarantined: required Item too short: Item 1 is 7380 chars < 15096; Item 1A is 29659 chars < 33805; Item 7 is 265 chars < 15352; Item 7A is 409 chars < 2746
    XOM    0000034088-24-000029   10-Q 2024 Q1    8    0   35 0.740 1.000 1.000 1.000 1.000 1.000   550    0  parsed
    XOM    0000034088-24-000050   10-Q 2024 Q2    8    0   40 0.715 1.000 1.000 1.000 1.000 1.000   915    0  parsed
    XOM    0000034088-24-000068   10-Q 2024 Q3    8    0   40 0.714 1.000 1.000 1.000 1.000 1.000   917    0  parsed
    XOM    0000034088-25-000010   10-K 2024 FY   22    0  118 0.739 1.000 0.958 1.000 1.000 0.991     0    1  quarantined: required Item too short: Item 1 is 7193 chars < 15096; Item 1A is 32305 chars < 33805; Item 7 is 264 chars < 15352; Item 7A is 409 chars < 2746
    XOM    0000034088-25-000024   10-Q 2025 Q1    8    0   38 0.730 1.000 0.947 1.000 1.000 0.989   903    0  parsed
    XOM    0000034088-25-000042   10-Q 2025 Q2    8    0   44 0.695 1.000 0.909 1.000 1.000 0.982  1533    0  parsed
    XOM    0000034088-25-000061   10-Q 2025 Q3    8    0   44 0.697 1.000 0.909 1.000 1.000 0.982  1526    0  parsed
    XOM    0000034088-26-000045   10-K 2025 FY   22    0  116 0.739 1.000 0.983 0.999 1.000 0.996     0    2  quarantined: required Item too short: Item 1 is 6636 chars < 15096; Item 7 is 264 chars < 15352; Item 7A is 456 chars < 2746
    XOM    0000034088-26-000067   10-Q 2026 Q1    9    0   34 0.732 1.000 0.941 0.999 1.000 0.988   851    1  parsed
    XOM    0000034088-26-000093   10-Q 2026 Q2    9    0   36 0.703 1.000 0.889 0.999 1.000 0.978  1467    2  parsed

Parsed 48 -> 66 (PFE and XOM 10-Qs). The remaining 10-K quarantines are the
content floors (F-69) and JPM/BAC's other findings. XOM's 2026 10-Qs carry an
`I.7A` section that the previous detector also produced -- noted, not changed.

Chunks: `store.py` now deletes chunks of filings no longer `parsed` (it kept the
three JPM 10-Ks' 3,092 chunks after the content check quarantined them). Chunk
diff vs before: clean filings 0 changed, 18 filings newly chunked, 66 chunked.
19 chunks over 512 (NVDA 1, PFE 15, XOM 3) -- F-67's class, fixed in its turn.
Resolve: 58,106 of 58,184 (0.999; 1.000 within Items). Snapshots: 3 passed.
`make test`: 231 passed.

## 2026-10-01 — F-64: Part tracking without Item order

F-63 committed as `43a50b6`.

BAC's 10-Q, block by block: "Part I." and "Part II." are paragraph headings of
the index, each followed by an index table ("Item 1. Legal Proceedings 96 ...");
MD&A then starts with no Part heading of its own and inherited "Part II".
Rules: a Part heading whose next block is a table listing two or more Items is
an index entry; an Item before any effective Part heading is Part I.

Section lists, previous detector vs new:

    BAC   0000070858-23-000272 10-Q: ['II.2', 'II.3', 'II.4', 'I.1', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6'] -> ['I.2', 'I.3', 'I.4', 'I.1', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6']
    BAC   0000070858-24-000156 10-Q: ['II.2', 'II.3', 'II.4', 'I.1', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6'] -> ['I.2', 'I.3', 'I.4', 'I.1', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6']
    BAC   0000070858-24-000208 10-Q: ['II.2', 'II.3', 'II.4', 'I.1', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6'] -> ['I.2', 'I.3', 'I.4', 'I.1', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6']
    BAC   0000070858-24-000280 10-Q: ['II.2', 'II.3', 'II.4', 'I.1', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6'] -> ['I.2', 'I.3', 'I.4', 'I.1', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6']
    BAC   0000070858-25-000200 10-Q: ['II.2', 'II.3', 'II.4', 'I.1', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6'] -> ['I.2', 'I.3', 'I.4', 'I.1', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6']
    BAC   0000070858-25-000268 10-Q: ['II.2', 'II.3', 'II.4', 'I.1', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6'] -> ['I.2', 'I.3', 'I.4', 'I.1', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6']
    BAC   0000070858-25-000405 10-Q: ['II.2', 'II.3', 'II.4', 'I.1', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6'] -> ['I.2', 'I.3', 'I.4', 'I.1', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6']
    BAC   0000070858-26-000249 10-Q: ['II.2', 'II.3', 'II.4', 'I.1', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6'] -> ['I.2', 'I.3', 'I.4', 'I.1', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6']
    BAC   0000070858-26-000394 10-Q: ['II.2', 'II.3', 'II.4', 'I.1', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6'] -> ['I.2', 'I.3', 'I.4', 'I.1', 'II.1', 'II.1A', 'II.2', 'II.5', 'II.6']
    JPM   0000019617-23-000524 10-Q: ['3', '4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6'] -> ['I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6']
    JPM   0000019617-24-000326 10-Q: ['3', '4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6'] -> ['I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6']
    JPM   0000019617-24-000453 10-Q: ['3', '4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6'] -> ['I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6']
    JPM   0000019617-24-000611 10-Q: ['3', '4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6'] -> ['I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6']
    JPM   0000019617-25-000421 10-Q: ['3', '4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6'] -> ['I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6']
    JPM   0000019617-25-000615 10-Q: ['3', '4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6'] -> ['I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6']
    JPM   0001628280-25-048859 10-Q: ['3', '4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6'] -> ['I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6']
    JPM   0001628280-26-029344 10-Q: ['3', '4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6'] -> ['I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6']
    JPM   0001628280-26-054343 10-Q: ['3', '4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6'] -> ['I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6']
    identical section lists: 78 of 96; clean filings changed: 0

`python -m api.parse.validate` (`parser_version` 2b3d5591e4c0):

    parser_version 2b3d5591e4c0
    ticker accession              form   FY fp sect miss data alpha scale uncol spans items score  rows skip  status
    AAPL   0000320193-23-000106   10-K 2023 FY   23    0   46 0.762 0.976 1.000 0.994 1.000 0.994   983    6  parsed
    AAPL   0000320193-24-000006   10-Q 2024 Q1   11    0   24 0.724 0.957 1.000 0.996 1.000 0.991   522    2  parsed
    AAPL   0000320193-24-000069   10-Q 2024 Q2   11    0   24 0.704 0.957 1.000 0.997 1.000 0.991   676    2  parsed
    AAPL   0000320193-24-000081   10-Q 2024 Q3   11    0   24 0.698 0.957 1.000 0.996 1.000 0.990   678    3  parsed
    AAPL   0000320193-24-000123   10-K 2024 FY   23    0   44 0.765 0.974 1.000 0.996 1.000 0.994   957    4  parsed
    AAPL   0000320193-25-000008   10-Q 2025 Q1   11    0   23 0.736 0.955 1.000 0.994 1.000 0.990   520    3  parsed
    AAPL   0000320193-25-000057   10-Q 2025 Q2   11    0   23 0.725 0.955 1.000 0.997 1.000 0.990   670    2  parsed
    AAPL   0000320193-25-000073   10-Q 2025 Q3   11    0   25 0.701 0.957 1.000 0.996 1.000 0.990   680    3  parsed
    AAPL   0000320193-25-000079   10-K 2025 FY   23    0   43 0.765 0.974 1.000 0.995 1.000 0.994   962    5  parsed
    AAPL   0000320193-26-000006   10-Q 2026 Q1   11    0   23 0.722 0.955 1.000 0.993 1.000 0.989   554    4  parsed
    AAPL   0000320193-26-000013   10-Q 2026 Q2   11    0   25 0.733 0.958 1.000 0.995 1.000 0.991   750    4  parsed
    AAPL   0000320193-26-000020   10-Q 2026 Q3   11    0   26 0.728 0.960 1.000 0.995 1.000 0.991   756    4  parsed
    BAC    0000070858-23-000272   10-Q 2023 Q3    9    0  129 0.689 1.000 0.992 0.999 1.000 0.998  6826   10  parsed
    BAC    0000070858-24-000122   10-K 2023 FY   23    0  159 0.748 1.000 0.969 0.997 1.000 0.993     0   21  quarantined: required Item too short: Item 7A is 217 chars < 2746
    BAC    0000070858-24-000156   10-Q 2024 Q1    9    0  119 0.701 1.000 0.992 0.998 1.000 0.998  5402    9  parsed
    BAC    0000070858-24-000208   10-Q 2024 Q2    9    0  127 0.683 1.000 0.992 0.999 1.000 0.998  6856    6  parsed
    BAC    0000070858-24-000280   10-Q 2024 Q3    9    0  126 0.685 1.000 0.992 0.999 1.000 0.998  6898    8  parsed
    BAC    0000070858-25-000139   10-K 2024 FY   23    0  158 0.746 1.000 0.975 0.998 1.000 0.994     0   19  quarantined: required Item too short: Item 7A is 217 chars < 2746
    BAC    0000070858-25-000200   10-Q 2025 Q1    9    0  118 0.701 1.000 1.000 0.999 1.000 1.000  5408    6  parsed
    BAC    0000070858-25-000268   10-Q 2025 Q2    9    0  123 0.685 1.000 0.992 0.999 1.000 0.998  6834    6  parsed
    BAC    0000070858-25-000405   10-Q 2025 Q3    9    0  122 0.686 1.000 0.992 0.999 1.000 0.998  6876    7  parsed
    BAC    0000070858-26-000157   10-K 2025 FY   23    0  157 0.746 1.000 0.968 0.998 1.000 0.993     0   19  quarantined: required Item too short: Item 7A is 217 chars < 2746
    BAC    0000070858-26-000249   10-Q 2026 Q1    9    0  117 0.700 1.000 1.000 0.999 1.000 1.000  5396    8  parsed
    BAC    0000070858-26-000394   10-Q 2026 Q2    9    0  123 0.681 1.000 0.992 0.999 1.000 0.998  6817    8  parsed
    COST   0000909832-23-000042   10-K 2023 FY   22    0   44 0.775 0.938 1.000 0.995 1.000 0.987   833    4  parsed
    COST   0000909832-23-000065   10-Q 2024 Q1   11    0   25 0.755 0.882 1.000 0.990 1.000 0.974   392    4  parsed
    COST   0000909832-24-000017   10-Q 2024 Q2   11    0   26 0.739 0.889 1.000 0.993 1.000 0.976   569    4  parsed
    COST   0000909832-24-000029   10-Q 2024 Q3   11    0   26 0.738 0.889 1.000 0.993 1.000 0.976   566    4  parsed
    COST   0000909832-24-000049   10-K 2024 FY   23    0   44 0.776 0.938 1.000 0.995 1.000 0.987   837    4  parsed
    COST   0000909832-24-000079   10-Q 2025 Q1   11    0   25 0.758 0.882 1.000 0.989 1.000 0.974   357    4  parsed
    COST   0000909832-25-000015   10-Q 2025 Q2   11    0   26 0.743 0.889 1.000 0.992 1.000 0.976   495    4  parsed
    COST   0000909832-25-000033   10-Q 2025 Q3   11    0   26 0.740 0.889 1.000 0.992 1.000 0.976   490    4  parsed
    COST   0000909832-25-000101   10-K 2025 FY   23    0   44 0.779 0.938 1.000 0.994 1.000 0.986   818    5  parsed
    COST   0000909832-25-000169   10-Q 2026 Q1   11    0   27 0.756 0.895 1.000 0.988 1.000 0.976   395    5  parsed
    COST   0000909832-26-000029   10-Q 2026 Q2   11    0   28 0.738 0.900 1.000 0.991 1.000 0.978   571    5  parsed
    COST   0000909832-26-000051   10-Q 2026 Q3   11    0   28 0.737 0.900 1.000 0.991 1.000 0.978   570    5  parsed
    JPM    0000019617-23-000524   10-Q 2023 Q3    9    2  243 0.701 1.000 0.984 0.995 0.000 0.796     0   36  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0000019617-24-000225   10-K 2023 FY   22    0  268 0.754 1.000 0.993 0.997 1.000 0.998     0   27  quarantined: required Item too short: Item 7 is 395 chars < 15352; Item 7A is 269 chars < 2746
    JPM    0000019617-24-000326   10-Q 2024 Q1    9    2  218 0.716 1.000 1.000 0.994 0.000 0.799     0   33  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0000019617-24-000453   10-Q 2024 Q2    9    2  232 0.700 1.000 0.983 0.996 0.000 0.796     0   31  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0000019617-24-000611   10-Q 2024 Q3    9    2  232 0.701 1.000 0.983 0.995 0.000 0.796     0   37  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0000019617-25-000270   10-K 2024 FY   22    0  267 0.755 1.000 0.993 0.996 1.000 0.998     0   34  quarantined: required Item too short: Item 7 is 395 chars < 15352; Item 7A is 269 chars < 2746
    JPM    0000019617-25-000421   10-Q 2025 Q1    9    2  219 0.713 1.000 1.000 0.997 0.000 0.799     0   20  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0000019617-25-000615   10-Q 2025 Q2    9    2  234 0.694 1.000 0.983 0.996 0.000 0.796     0   27  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0001628280-25-048859   10-Q 2025 Q3    9    2  233 0.697 1.000 0.983 0.996 0.000 0.796     0   33  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0001628280-26-008131   10-K 2025 FY   22    0  272 0.752 1.000 0.993 0.995 1.000 0.998     0   38  quarantined: required Item too short: Item 7 is 395 chars < 15352; Item 7A is 269 chars < 2746
    JPM    0001628280-26-029344   10-Q 2026 Q1    9    2  219 0.714 1.000 1.000 0.997 0.000 0.799     0   16  quarantined: required Items missing: ['I.1', 'I.2']
    JPM    0001628280-26-054343   10-Q 2026 Q2    9    2  228 0.695 1.000 0.982 0.997 0.000 0.796     0   20  quarantined: required Items missing: ['I.1', 'I.2']
    NVDA   0001045810-23-000227   10-Q 2024 Q3    9    0   41 0.762 1.000 1.000 0.998 1.000 1.000   964    2  parsed
    NVDA   0001045810-24-000029   10-K 2024 FY   23    0   53 0.790 1.000 1.000 0.993 1.000 0.999  1207    9  parsed
    NVDA   0001045810-24-000124   10-Q 2025 Q1    9    0   43 0.766 1.000 1.000 0.993 1.000 0.999   746    5  parsed
    NVDA   0001045810-24-000264   10-Q 2025 Q2    9    0   45 0.755 1.000 1.000 0.995 1.000 0.999   988    5  parsed
    NVDA   0001045810-24-000316   10-Q 2025 Q3    9    0   44 0.754 1.000 1.000 0.996 1.000 0.999   984    4  parsed
    NVDA   0001045810-25-000023   10-K 2025 FY   23    0   56 0.789 1.000 1.000 0.993 1.000 0.999  1220    9  parsed
    NVDA   0001045810-25-000116   10-Q 2026 Q1    9    0   40 0.768 1.000 1.000 0.994 1.000 0.999   721    4  parsed
    NVDA   0001045810-25-000209   10-Q 2026 Q2    9    0   39 0.752 1.000 1.000 0.994 1.000 0.999   940    6  parsed
    NVDA   0001045810-25-000230   10-Q 2026 Q3    9    0   38 0.761 1.000 1.000 0.992 1.000 0.998   943    8  parsed
    NVDA   0001045810-26-000021   10-K 2026 FY   23    0   49 0.790 1.000 1.000 0.991 1.000 0.998  1117   10  parsed
    NVDA   0001045810-26-000052   10-Q 2027 Q1    9    0   37 0.769 1.000 1.000 0.994 1.000 0.999   699    4  parsed
    NVDA   0001045810-26-000075   10-Q 2027 Q2    9    0   41 0.753 1.000 1.000 0.996 1.000 0.999   996    4  parsed
    PFE    0000078003-23-000115   10-Q 2023 Q3    9    0   46 0.760 1.000 1.000 0.989 1.000 0.998  1856   20  parsed
    PFE    0000078003-24-000039   10-K 2023 FY   20    0   78 0.784 1.000 1.000 0.988 1.000 0.998     0   37  quarantined: required Item too short: Item 7A is 289 chars < 2746
    PFE    0000078003-24-000107   10-Q 2024 Q1    9    0   44 0.773 1.000 1.000 0.982 1.000 0.996  1194   22  parsed
    PFE    0000078003-24-000166   10-Q 2024 Q2    9    0   50 0.758 1.000 1.000 0.988 1.000 0.998  1775   22  parsed
    PFE    0000078003-24-000191   10-Q 2024 Q3    9    0   50 0.758 1.000 1.000 0.985 1.000 0.997  1797   27  parsed
    PFE    0000078003-25-000054   10-K 2024 FY   20    0   86 0.783 1.000 1.000 0.984 1.000 0.997     0   47  quarantined: required Item too short: Item 7A is 289 chars < 2746
    PFE    0000078003-25-000114   10-Q 2025 Q1    9    0   41 0.774 1.000 1.000 0.974 1.000 0.995  1112   30  parsed
    PFE    0000078003-25-000138   10-Q 2025 Q2    9    0   50 0.757 1.000 1.000 0.984 1.000 0.997  1662   27  parsed
    PFE    0000078003-25-000150   10-Q 2025 Q3    9    0   50 0.760 1.000 1.000 0.986 1.000 0.997  1724   24  parsed
    PFE    0000078003-26-000026   10-K 2025 FY   20    0   82 0.785 1.000 1.000 0.986 1.000 0.997     0   40  quarantined: required Item too short: Item 7A is 289 chars < 2746
    PFE    0000078003-26-000054   10-Q 2026 Q1    9    0   40 0.773 1.000 1.000 0.984 1.000 0.997  1207   20  parsed
    PFE    0000078003-26-000095   10-Q 2026 Q2    9    0   48 0.757 1.000 1.000 0.989 1.000 0.998  1789   20  parsed
    TGT    0000027419-23-000052   10-Q 2023 Q3   11    0   29 0.716 1.000 1.000 0.980 1.000 0.996   553   11  parsed
    TGT    0000027419-24-000032   10-K 2023 FY   23    0   60 0.768 0.977 1.000 0.986 1.000 0.993   984   14  parsed
    TGT    0000027419-24-000129   10-Q 2024 Q1   11    0   28 0.730 1.000 1.000 0.982 1.000 0.996   385    7  parsed
    TGT    0000027419-24-000152   10-Q 2024 Q2   11    0   30 0.710 1.000 1.000 0.985 1.000 0.997   517    8  parsed
    TGT    0000027419-24-000179   10-Q 2024 Q3   11    0   30 0.711 1.000 1.000 0.982 1.000 0.996   532   10  parsed
    TGT    0000027419-25-000018   10-K 2024 FY   23    0   62 0.773 1.000 1.000 0.988 1.000 0.998   973   12  parsed
    TGT    0000027419-25-000101   10-Q 2025 Q1   11    0   30 0.734 1.000 1.000 0.981 1.000 0.996   406    8  parsed
    TGT    0000027419-25-000118   10-Q 2025 Q2   11    0   33 0.718 1.000 1.000 0.986 1.000 0.997   546    8  parsed
    TGT    0000027419-25-000126   10-Q 2025 Q3   11    0   34 0.720 1.000 1.000 0.983 1.000 0.997   576   10  parsed
    TGT    0000027419-26-000016   10-K 2025 FY   23    0   64 0.774 1.000 1.000 0.987 1.000 0.997   977   13  parsed
    TGT    0000027419-26-000022   10-Q 2026 Q1   11    0   30 0.736 1.000 1.000 0.980 1.000 0.996   401    8  parsed
    TGT    0000027419-26-000042   10-Q 2026 Q2   11    0   32 0.720 1.000 1.000 0.979 1.000 0.996   547   12  parsed
    XOM    0000034088-23-000056   10-Q 2023 Q3    8    0   36 0.715 1.000 1.000 1.000 1.000 1.000   883    0  parsed
    XOM    0000034088-24-000018   10-K 2023 FY   22    0  113 0.738 1.000 0.982 1.000 1.000 0.996     0    1  quarantined: required Item too short: Item 1 is 7380 chars < 15096; Item 1A is 29659 chars < 33805; Item 7 is 265 chars < 15352; Item 7A is 409 chars < 2746
    XOM    0000034088-24-000029   10-Q 2024 Q1    8    0   35 0.740 1.000 1.000 1.000 1.000 1.000   550    0  parsed
    XOM    0000034088-24-000050   10-Q 2024 Q2    8    0   40 0.715 1.000 1.000 1.000 1.000 1.000   915    0  parsed
    XOM    0000034088-24-000068   10-Q 2024 Q3    8    0   40 0.714 1.000 1.000 1.000 1.000 1.000   917    0  parsed
    XOM    0000034088-25-000010   10-K 2024 FY   22    0  118 0.739 1.000 0.958 1.000 1.000 0.991     0    1  quarantined: required Item too short: Item 1 is 7193 chars < 15096; Item 1A is 32305 chars < 33805; Item 7 is 264 chars < 15352; Item 7A is 409 chars < 2746
    XOM    0000034088-25-000024   10-Q 2025 Q1    8    0   38 0.730 1.000 0.947 1.000 1.000 0.989   903    0  parsed
    XOM    0000034088-25-000042   10-Q 2025 Q2    8    0   44 0.695 1.000 0.909 1.000 1.000 0.982  1533    0  parsed
    XOM    0000034088-25-000061   10-Q 2025 Q3    8    0   44 0.697 1.000 0.909 1.000 1.000 0.982  1526    0  parsed
    XOM    0000034088-26-000045   10-K 2025 FY   22    0  116 0.739 1.000 0.983 0.999 1.000 0.996     0    2  quarantined: required Item too short: Item 1 is 6636 chars < 15096; Item 7 is 264 chars < 15352; Item 7A is 456 chars < 2746
    XOM    0000034088-26-000067   10-Q 2026 Q1    9    0   34 0.732 1.000 0.941 0.999 1.000 0.988   851    1  parsed
    XOM    0000034088-26-000093   10-Q 2026 Q2    9    0   36 0.703 1.000 0.889 0.999 1.000 0.978  1467    2  parsed

Parsed 66 -> 75 (all 9 BAC 10-Qs). Chunks: no previously chunked filing changed;
9 BAC 10-Qs newly chunked (3,986 chunks); 28 over 512 (F-67). Resolve: 115,410 of
115,497 (0.999; 1.000 within Items). Snapshots 3 passed; `make test` 233 passed.

## 2026-10-01 — F-65/F-66: table-of-contents-anchor fallback

F-64 committed as `af7a620`.

Stop check first: JPM's index rows carry hrefs (10-Q: "Item 1. | Financial
Statements" -> `..._163`, resolving to "Consolidated statements of income"; 10-K:
"Part II", "Item 7." etc. each linked). The 10-K's Item 7/8 rows link to the
in-body stubs; the stubs name Annual Report pages with no link, so the 10-K MD&A
is not relocated (stop condition, F-55).

Walker: `anchor_targets` (offset where each `id`/`name` element begins).
`text_sha256` identical on all 96, tables identical; `parser_version`
2b3d5591e4c0 -> 5a01b13efe34 for the walker, d58d26e08e5a with the sections change.

Two corrections while building, both found on data:
- the newer JPM 10-Qs split the index over two tables, the first holding only
  Item 1, so "a table listing two or more Items" missed Item 1; any non-heading
  table's linked Item rows now count;
- JPM's FY2025 10-K came out `III.15`: a "Part IV" running header begins four
  blocks after Item 15's heading, and index Part links only filled Parts the body
  lacked. Index and primary Part markers now combine, earliest position wins.

Section lists, previous detector vs new (only JPM changes):

    JPM   0000019617-23-000524 10-Q: ['I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6'] -> ['I.2', 'I.1', 'I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6']
    JPM   0000019617-24-000225 10-K: ['I.1', 'I.1A', 'I.1B', 'I.1C', 'I.2', 'I.3', 'I.4', 'I.5', 'I.6', 'I.7', 'I.7A', 'I.8', 'I.9', 'I.9A', 'I.9B', 'I.9C', 'I.10', 'I.11', 'I.12', 'I.13', 'I.14', 'IV.15'] -> ['I.1', 'I.1A', 'I.1B', 'I.1C', 'I.2', 'I.3', 'I.4', 'II.5', 'II.6', 'II.7', 'II.7A', 'II.8', 'II.9', 'II.9A', 'II.9B', 'II.9C', 'III.10', 'III.11', 'III.12', 'III.13', 'III.14', 'IV.15']
    JPM   0000019617-24-000326 10-Q: ['I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6'] -> ['I.2', 'I.1', 'I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6']
    JPM   0000019617-24-000453 10-Q: ['I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6'] -> ['I.2', 'I.1', 'I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6']
    JPM   0000019617-24-000611 10-Q: ['I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6'] -> ['I.2', 'I.1', 'I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6']
    JPM   0000019617-25-000270 10-K: ['I.1', 'I.1A', 'I.1B', 'I.1C', 'I.2', 'I.3', 'I.4', 'I.5', 'I.6', 'I.7', 'I.7A', 'I.8', 'I.9', 'I.9A', 'I.9B', 'I.9C', 'I.10', 'I.11', 'I.12', 'I.13', 'I.14', 'IV.15'] -> ['I.1', 'I.1A', 'I.1B', 'I.1C', 'I.2', 'I.3', 'I.4', 'II.5', 'II.6', 'II.7', 'II.7A', 'II.8', 'II.9', 'II.9A', 'II.9B', 'II.9C', 'III.10', 'III.11', 'III.12', 'III.13', 'III.14', 'IV.15']
    JPM   0000019617-25-000421 10-Q: ['I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6'] -> ['I.2', 'I.1', 'I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6']
    JPM   0000019617-25-000615 10-Q: ['I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6'] -> ['I.2', 'I.1', 'I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6']
    JPM   0001628280-25-048859 10-Q: ['I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6'] -> ['I.2', 'I.1', 'I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6']
    JPM   0001628280-26-008131 10-K: ['I.1', 'I.1A', 'I.1B', 'I.1C', 'I.2', 'I.3', 'I.4', 'I.5', 'I.6', 'I.7', 'I.7A', 'I.8', 'I.9', 'I.9A', 'I.9B', 'I.9C', 'I.10', 'I.11', 'I.12', 'I.13', 'I.14', 'I.15'] -> ['I.1', 'I.1A', 'I.1B', 'I.1C', 'I.2', 'I.3', 'I.4', 'II.5', 'II.6', 'II.7', 'II.7A', 'II.8', 'II.9', 'II.9A', 'II.9B', 'II.9C', 'III.10', 'III.11', 'III.12', 'III.13', 'III.14', 'IV.15']
    JPM   0001628280-26-029344 10-Q: ['I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6'] -> ['I.2', 'I.1', 'I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6']
    JPM   0001628280-26-054343 10-Q: ['I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6'] -> ['I.2', 'I.1', 'I.3', 'I.4', 'II.1', 'II.1A', 'II.2', 'II.3', 'II.4', 'II.5', 'II.6']
    identical section lists: 84 of 96; clean filings changed: 0

10-K code shape across companies (detected, all 10-Ks):

    10-K detected qualified codes not in AAPL's set: {'AAPL': [], 'BAC': [], 'COST': [], 'JPM': [], 'NVDA': [], 'PFE': [], 'TGT': [], 'XOM': []}

`python -m api.parse.validate` (`parser_version` d58d26e08e5a):

    parser_version d58d26e08e5a
    ticker accession              form   FY fp sect miss data alpha scale uncol spans items score  rows skip  status
    AAPL   0000320193-23-000106   10-K 2023 FY   23    0   46 0.762 0.976 1.000 0.994 1.000 0.994   983    6  parsed
    AAPL   0000320193-24-000006   10-Q 2024 Q1   11    0   24 0.724 0.957 1.000 0.996 1.000 0.991   522    2  parsed
    AAPL   0000320193-24-000069   10-Q 2024 Q2   11    0   24 0.704 0.957 1.000 0.997 1.000 0.991   676    2  parsed
    AAPL   0000320193-24-000081   10-Q 2024 Q3   11    0   24 0.698 0.957 1.000 0.996 1.000 0.990   678    3  parsed
    AAPL   0000320193-24-000123   10-K 2024 FY   23    0   44 0.765 0.974 1.000 0.996 1.000 0.994   957    4  parsed
    AAPL   0000320193-25-000008   10-Q 2025 Q1   11    0   23 0.736 0.955 1.000 0.994 1.000 0.990   520    3  parsed
    AAPL   0000320193-25-000057   10-Q 2025 Q2   11    0   23 0.725 0.955 1.000 0.997 1.000 0.990   670    2  parsed
    AAPL   0000320193-25-000073   10-Q 2025 Q3   11    0   25 0.701 0.957 1.000 0.996 1.000 0.990   680    3  parsed
    AAPL   0000320193-25-000079   10-K 2025 FY   23    0   43 0.765 0.974 1.000 0.995 1.000 0.994   962    5  parsed
    AAPL   0000320193-26-000006   10-Q 2026 Q1   11    0   23 0.722 0.955 1.000 0.993 1.000 0.989   554    4  parsed
    AAPL   0000320193-26-000013   10-Q 2026 Q2   11    0   25 0.733 0.958 1.000 0.995 1.000 0.991   750    4  parsed
    AAPL   0000320193-26-000020   10-Q 2026 Q3   11    0   26 0.728 0.960 1.000 0.995 1.000 0.991   756    4  parsed
    BAC    0000070858-23-000272   10-Q 2023 Q3    9    0  129 0.689 1.000 0.992 0.999 1.000 0.998  6826   10  parsed
    BAC    0000070858-24-000122   10-K 2023 FY   23    0  159 0.748 1.000 0.969 0.997 1.000 0.993     0   21  quarantined: required Item too short: Item 7A is 217 chars < 2746
    BAC    0000070858-24-000156   10-Q 2024 Q1    9    0  119 0.701 1.000 0.992 0.998 1.000 0.998  5402    9  parsed
    BAC    0000070858-24-000208   10-Q 2024 Q2    9    0  127 0.683 1.000 0.992 0.999 1.000 0.998  6856    6  parsed
    BAC    0000070858-24-000280   10-Q 2024 Q3    9    0  126 0.685 1.000 0.992 0.999 1.000 0.998  6898    8  parsed
    BAC    0000070858-25-000139   10-K 2024 FY   23    0  158 0.746 1.000 0.975 0.998 1.000 0.994     0   19  quarantined: required Item too short: Item 7A is 217 chars < 2746
    BAC    0000070858-25-000200   10-Q 2025 Q1    9    0  118 0.701 1.000 1.000 0.999 1.000 1.000  5408    6  parsed
    BAC    0000070858-25-000268   10-Q 2025 Q2    9    0  123 0.685 1.000 0.992 0.999 1.000 0.998  6834    6  parsed
    BAC    0000070858-25-000405   10-Q 2025 Q3    9    0  122 0.686 1.000 0.992 0.999 1.000 0.998  6876    7  parsed
    BAC    0000070858-26-000157   10-K 2025 FY   23    0  157 0.746 1.000 0.968 0.998 1.000 0.993     0   19  quarantined: required Item too short: Item 7A is 217 chars < 2746
    BAC    0000070858-26-000249   10-Q 2026 Q1    9    0  117 0.700 1.000 1.000 0.999 1.000 1.000  5396    8  parsed
    BAC    0000070858-26-000394   10-Q 2026 Q2    9    0  123 0.681 1.000 0.992 0.999 1.000 0.998  6817    8  parsed
    COST   0000909832-23-000042   10-K 2023 FY   22    0   44 0.775 0.938 1.000 0.995 1.000 0.987   833    4  parsed
    COST   0000909832-23-000065   10-Q 2024 Q1   11    0   25 0.755 0.882 1.000 0.990 1.000 0.974   392    4  parsed
    COST   0000909832-24-000017   10-Q 2024 Q2   11    0   26 0.739 0.889 1.000 0.993 1.000 0.976   569    4  parsed
    COST   0000909832-24-000029   10-Q 2024 Q3   11    0   26 0.738 0.889 1.000 0.993 1.000 0.976   566    4  parsed
    COST   0000909832-24-000049   10-K 2024 FY   23    0   44 0.776 0.938 1.000 0.995 1.000 0.987   837    4  parsed
    COST   0000909832-24-000079   10-Q 2025 Q1   11    0   25 0.758 0.882 1.000 0.989 1.000 0.974   357    4  parsed
    COST   0000909832-25-000015   10-Q 2025 Q2   11    0   26 0.743 0.889 1.000 0.992 1.000 0.976   495    4  parsed
    COST   0000909832-25-000033   10-Q 2025 Q3   11    0   26 0.740 0.889 1.000 0.992 1.000 0.976   490    4  parsed
    COST   0000909832-25-000101   10-K 2025 FY   23    0   44 0.779 0.938 1.000 0.994 1.000 0.986   818    5  parsed
    COST   0000909832-25-000169   10-Q 2026 Q1   11    0   27 0.756 0.895 1.000 0.988 1.000 0.976   395    5  parsed
    COST   0000909832-26-000029   10-Q 2026 Q2   11    0   28 0.738 0.900 1.000 0.991 1.000 0.978   571    5  parsed
    COST   0000909832-26-000051   10-Q 2026 Q3   11    0   28 0.737 0.900 1.000 0.991 1.000 0.978   570    5  parsed
    JPM    0000019617-23-000524   10-Q 2023 Q3   11    0  243 0.701 1.000 0.984 0.995 1.000 0.996  7819   36  parsed
    JPM    0000019617-24-000225   10-K 2023 FY   22    0  268 0.754 1.000 0.993 0.997 1.000 0.998     0   27  quarantined: required Item too short: Item 7 is 395 chars < 15352; Item 7A is 269 chars < 2746
    JPM    0000019617-24-000326   10-Q 2024 Q1   11    0  218 0.716 1.000 1.000 0.994 1.000 0.999  5755   33  parsed
    JPM    0000019617-24-000453   10-Q 2024 Q2   11    0  232 0.700 1.000 0.983 0.996 1.000 0.996  7386   31  parsed
    JPM    0000019617-24-000611   10-Q 2024 Q3   11    0  232 0.701 1.000 0.983 0.995 1.000 0.996  7373   37  parsed
    JPM    0000019617-25-000270   10-K 2024 FY   22    0  267 0.755 1.000 0.993 0.996 1.000 0.998     0   34  quarantined: required Item too short: Item 7 is 395 chars < 15352; Item 7A is 269 chars < 2746
    JPM    0000019617-25-000421   10-Q 2025 Q1   11    0  219 0.713 1.000 1.000 0.997 1.000 0.999  5717   20  parsed
    JPM    0000019617-25-000615   10-Q 2025 Q2   11    0  234 0.694 1.000 0.983 0.996 1.000 0.996  7338   27  parsed
    JPM    0001628280-25-048859   10-Q 2025 Q3   11    0  233 0.697 1.000 0.983 0.996 1.000 0.996  7354   33  parsed
    JPM    0001628280-26-008131   10-K 2025 FY   22    0  272 0.752 1.000 0.993 0.995 1.000 0.998     0   38  quarantined: required Item too short: Item 7 is 395 chars < 15352; Item 7A is 269 chars < 2746
    JPM    0001628280-26-029344   10-Q 2026 Q1   11    0  219 0.714 1.000 1.000 0.997 1.000 0.999  5650   16  parsed
    JPM    0001628280-26-054343   10-Q 2026 Q2   11    0  228 0.695 1.000 0.982 0.997 1.000 0.996  7351   20  parsed
    NVDA   0001045810-23-000227   10-Q 2024 Q3    9    0   41 0.762 1.000 1.000 0.998 1.000 1.000   964    2  parsed
    NVDA   0001045810-24-000029   10-K 2024 FY   23    0   53 0.790 1.000 1.000 0.993 1.000 0.999  1207    9  parsed
    NVDA   0001045810-24-000124   10-Q 2025 Q1    9    0   43 0.766 1.000 1.000 0.993 1.000 0.999   746    5  parsed
    NVDA   0001045810-24-000264   10-Q 2025 Q2    9    0   45 0.755 1.000 1.000 0.995 1.000 0.999   988    5  parsed
    NVDA   0001045810-24-000316   10-Q 2025 Q3    9    0   44 0.754 1.000 1.000 0.996 1.000 0.999   984    4  parsed
    NVDA   0001045810-25-000023   10-K 2025 FY   23    0   56 0.789 1.000 1.000 0.993 1.000 0.999  1220    9  parsed
    NVDA   0001045810-25-000116   10-Q 2026 Q1    9    0   40 0.768 1.000 1.000 0.994 1.000 0.999   721    4  parsed
    NVDA   0001045810-25-000209   10-Q 2026 Q2    9    0   39 0.752 1.000 1.000 0.994 1.000 0.999   940    6  parsed
    NVDA   0001045810-25-000230   10-Q 2026 Q3    9    0   38 0.761 1.000 1.000 0.992 1.000 0.998   943    8  parsed
    NVDA   0001045810-26-000021   10-K 2026 FY   23    0   49 0.790 1.000 1.000 0.991 1.000 0.998  1117   10  parsed
    NVDA   0001045810-26-000052   10-Q 2027 Q1    9    0   37 0.769 1.000 1.000 0.994 1.000 0.999   699    4  parsed
    NVDA   0001045810-26-000075   10-Q 2027 Q2    9    0   41 0.753 1.000 1.000 0.996 1.000 0.999   996    4  parsed
    PFE    0000078003-23-000115   10-Q 2023 Q3    9    0   46 0.760 1.000 1.000 0.989 1.000 0.998  1856   20  parsed
    PFE    0000078003-24-000039   10-K 2023 FY   20    0   78 0.784 1.000 1.000 0.988 1.000 0.998     0   37  quarantined: required Item too short: Item 7A is 289 chars < 2746
    PFE    0000078003-24-000107   10-Q 2024 Q1    9    0   44 0.773 1.000 1.000 0.982 1.000 0.996  1194   22  parsed
    PFE    0000078003-24-000166   10-Q 2024 Q2    9    0   50 0.758 1.000 1.000 0.988 1.000 0.998  1775   22  parsed
    PFE    0000078003-24-000191   10-Q 2024 Q3    9    0   50 0.758 1.000 1.000 0.985 1.000 0.997  1797   27  parsed
    PFE    0000078003-25-000054   10-K 2024 FY   20    0   86 0.783 1.000 1.000 0.984 1.000 0.997     0   47  quarantined: required Item too short: Item 7A is 289 chars < 2746
    PFE    0000078003-25-000114   10-Q 2025 Q1    9    0   41 0.774 1.000 1.000 0.974 1.000 0.995  1112   30  parsed
    PFE    0000078003-25-000138   10-Q 2025 Q2    9    0   50 0.757 1.000 1.000 0.984 1.000 0.997  1662   27  parsed
    PFE    0000078003-25-000150   10-Q 2025 Q3    9    0   50 0.760 1.000 1.000 0.986 1.000 0.997  1724   24  parsed
    PFE    0000078003-26-000026   10-K 2025 FY   20    0   82 0.785 1.000 1.000 0.986 1.000 0.997     0   40  quarantined: required Item too short: Item 7A is 289 chars < 2746
    PFE    0000078003-26-000054   10-Q 2026 Q1    9    0   40 0.773 1.000 1.000 0.984 1.000 0.997  1207   20  parsed
    PFE    0000078003-26-000095   10-Q 2026 Q2    9    0   48 0.757 1.000 1.000 0.989 1.000 0.998  1789   20  parsed
    TGT    0000027419-23-000052   10-Q 2023 Q3   11    0   29 0.716 1.000 1.000 0.980 1.000 0.996   553   11  parsed
    TGT    0000027419-24-000032   10-K 2023 FY   23    0   60 0.768 0.977 1.000 0.986 1.000 0.993   984   14  parsed
    TGT    0000027419-24-000129   10-Q 2024 Q1   11    0   28 0.730 1.000 1.000 0.982 1.000 0.996   385    7  parsed
    TGT    0000027419-24-000152   10-Q 2024 Q2   11    0   30 0.710 1.000 1.000 0.985 1.000 0.997   517    8  parsed
    TGT    0000027419-24-000179   10-Q 2024 Q3   11    0   30 0.711 1.000 1.000 0.982 1.000 0.996   532   10  parsed
    TGT    0000027419-25-000018   10-K 2024 FY   23    0   62 0.773 1.000 1.000 0.988 1.000 0.998   973   12  parsed
    TGT    0000027419-25-000101   10-Q 2025 Q1   11    0   30 0.734 1.000 1.000 0.981 1.000 0.996   406    8  parsed
    TGT    0000027419-25-000118   10-Q 2025 Q2   11    0   33 0.718 1.000 1.000 0.986 1.000 0.997   546    8  parsed
    TGT    0000027419-25-000126   10-Q 2025 Q3   11    0   34 0.720 1.000 1.000 0.983 1.000 0.997   576   10  parsed
    TGT    0000027419-26-000016   10-K 2025 FY   23    0   64 0.774 1.000 1.000 0.987 1.000 0.997   977   13  parsed
    TGT    0000027419-26-000022   10-Q 2026 Q1   11    0   30 0.736 1.000 1.000 0.980 1.000 0.996   401    8  parsed
    TGT    0000027419-26-000042   10-Q 2026 Q2   11    0   32 0.720 1.000 1.000 0.979 1.000 0.996   547   12  parsed
    XOM    0000034088-23-000056   10-Q 2023 Q3    8    0   36 0.715 1.000 1.000 1.000 1.000 1.000   883    0  parsed
    XOM    0000034088-24-000018   10-K 2023 FY   22    0  113 0.738 1.000 0.982 1.000 1.000 0.996     0    1  quarantined: required Item too short: Item 1 is 7380 chars < 15096; Item 1A is 29659 chars < 33805; Item 7 is 265 chars < 15352; Item 7A is 409 chars < 2746
    XOM    0000034088-24-000029   10-Q 2024 Q1    8    0   35 0.740 1.000 1.000 1.000 1.000 1.000   550    0  parsed
    XOM    0000034088-24-000050   10-Q 2024 Q2    8    0   40 0.715 1.000 1.000 1.000 1.000 1.000   915    0  parsed
    XOM    0000034088-24-000068   10-Q 2024 Q3    8    0   40 0.714 1.000 1.000 1.000 1.000 1.000   917    0  parsed
    XOM    0000034088-25-000010   10-K 2024 FY   22    0  118 0.739 1.000 0.958 1.000 1.000 0.991     0    1  quarantined: required Item too short: Item 1 is 7193 chars < 15096; Item 1A is 32305 chars < 33805; Item 7 is 264 chars < 15352; Item 7A is 409 chars < 2746
    XOM    0000034088-25-000024   10-Q 2025 Q1    8    0   38 0.730 1.000 0.947 1.000 1.000 0.989   903    0  parsed
    XOM    0000034088-25-000042   10-Q 2025 Q2    8    0   44 0.695 1.000 0.909 1.000 1.000 0.982  1533    0  parsed
    XOM    0000034088-25-000061   10-Q 2025 Q3    8    0   44 0.697 1.000 0.909 1.000 1.000 0.982  1526    0  parsed
    XOM    0000034088-26-000045   10-K 2025 FY   22    0  116 0.739 1.000 0.983 0.999 1.000 0.996     0    2  quarantined: required Item too short: Item 1 is 6636 chars < 15096; Item 7 is 264 chars < 15352; Item 7A is 456 chars < 2746
    XOM    0000034088-26-000067   10-Q 2026 Q1    9    0   34 0.732 1.000 0.941 0.999 1.000 0.988   851    1  parsed
    XOM    0000034088-26-000093   10-Q 2026 Q2    9    0   36 0.703 1.000 0.889 0.999 1.000 0.978  1467    2  parsed

Parsed 75 -> 84 (all JPM 10-Qs). JPM 10-Ks quarantined by the content check.
Chunks: no previously chunked filing changed; 9 newly chunked; 18,779 chunks, 28
over 512 (F-67). Resolve: 177,144 of 177,240 (0.999; 1.000 within Items).
Snapshots 3 passed; `make test` 236 passed.

## 2026-10-01 — F-67: split at rows, then clauses; embedding runs

F-65/F-66 committed as `d8f85b1`.

Over-512 chunks after F-65, classified by source block: 16 layout tables chunked
as prose (rows 9-38, longest row 98 tokens), 12 paragraphs each a single
over-budget sentence (BAC 9, XOM 3). See TRADEOFFS F-67.

An interruption left the whitespace-window counter declared but not incremented;
a summary run in that state printed `ws 0` from an unwritten field. Caught before
use, wired, and re-run -- the 0 below is counted.

Chunk summary, 84 parsed filings, totals:

    before: prose 10181, table 8598, psplit 109, pieces 206, >512 28, partOverlap 0, max 990
    after:  prose 10190, table 8598, psplit 73, pieces 146, ltsplit 36, ws 0, >512 0, partOverlap 0, max 500

`content_hash` diff by filing (`chunker_version` abe01d8d9b7b -> 964f77f6f9cb):

    accession              before  after changed removed added
    0000019617-23-000524      784    784       1       1     1
    0000019617-24-000326      647    647       1       1     1
    0000019617-24-000453      730    730       1       1     1
    0000019617-24-000611      731    731       1       1     1
    0000027419-24-000032      197    197       3       5     5
    0000027419-25-000018      208    209       4       6     7
    0000027419-26-000016      217    218       3       6     7
    0000034088-25-000024      100    101       1       1     2
    0000034088-25-000042      119    120       1       1     2
    0000034088-25-000061      119    120       1       1     2
    0000070858-23-000272      482    482       1       3     3
    0000070858-24-000156      406    406       1       3     3
    0000070858-24-000208      467    467       1       3     3
    0000070858-24-000280      467    467       1       3     3
    0000070858-25-000200      403    403       1       1     1
    0000070858-25-000268      459    460       1       1     2
    0000070858-25-000405      454    455       1       3     4
    0000070858-26-000249      399    400       1       1     2
    0000070858-26-000394      449    449       1       2     2
    0000078003-23-000115      219    219       2       5     5
    0000078003-24-000107      184    184       2       4     4
    0000078003-24-000166      213    215       2       4     6
    0000078003-24-000191      210    212       1       7     9
    0000078003-25-000114      173    173       2       4     4
    0000078003-25-000138      203    203       2       6     6
    0000078003-25-000150      210    209       1      11    10
    0000078003-26-000095      201    200       0       3     2
    0000909832-23-000042      179    179       1       1     1
    0000909832-24-000049      184    184       1       1     1
    0001045810-26-000021      253    253       1       1     1
    0001628280-25-048859      718    717       0       3     2
    0001628280-26-029344      641    641       1       1     1
    0001628280-26-054343      713    713       1       1     1
    filings with chunk changes: 33 of 84

Attribution, every changed, added or removed chunk:

    0000019617-23-000524: changed/added/removed 3, spanning a large layout table: 3, other: 0 []
    0000019617-24-000326: changed/added/removed 3, spanning a large layout table: 3, other: 0 []
    0000019617-24-000453: changed/added/removed 3, spanning a large layout table: 3, other: 0 []
    0000019617-24-000611: changed/added/removed 3, spanning a large layout table: 3, other: 0 []
    0000027419-24-000032: changed/added/removed 13, spanning a large layout table: 13, other: 0 []
    0000027419-25-000018: changed/added/removed 17, spanning a large layout table: 16, other: 1 ['0000027419-25-000018:813.0:814.0']
    0000027419-26-000016: changed/added/removed 16, spanning a large layout table: 15, other: 1 ['0000027419-26-000016:841.0:849.0']
    0000034088-25-000024: changed/added/removed 4, spanning a large layout table: 0, other: 4 ['0000034088-25-000024:259.0:259.0', '0000034088-25-000024:259.1:260.0', '0000034088-25-000024:259.1:264.0', '0000034088-25-000024:263.0:264.0']
    0000034088-25-000042: changed/added/removed 4, spanning a large layout table: 0, other: 4 ['0000034088-25-000042:317.0:317.0', '0000034088-25-000042:317.1:318.0', '0000034088-25-000042:317.1:322.0', '0000034088-25-000042:321.0:322.0']
    0000034088-25-000061: changed/added/removed 4, spanning a large layout table: 0, other: 4 ['0000034088-25-000061:323.0:323.0', '0000034088-25-000061:323.1:324.0', '0000034088-25-000061:323.1:326.0', '0000034088-25-000061:325.0:326.0']
    0000070858-23-000272: changed/added/removed 7, spanning a large layout table: 0, other: 7 ['0000070858-23-000272:54.0:54.0', '0000070858-23-000272:54.1:60.0', '0000070858-23-000272:56.0:61.0', '0000070858-23-000272:59.0:62.0']
    0000070858-24-000156: changed/added/removed 7, spanning a large layout table: 0, other: 7 ['0000070858-24-000156:54.0:54.0', '0000070858-24-000156:54.1:60.0', '0000070858-24-000156:56.0:61.0', '0000070858-24-000156:59.0:62.0']
    0000070858-24-000208: changed/added/removed 7, spanning a large layout table: 0, other: 7 ['0000070858-24-000208:54.0:54.0', '0000070858-24-000208:54.1:60.0', '0000070858-24-000208:56.0:61.0', '0000070858-24-000208:59.0:63.0']
    0000070858-24-000280: changed/added/removed 7, spanning a large layout table: 0, other: 7 ['0000070858-24-000280:54.0:54.0', '0000070858-24-000280:54.1:60.0', '0000070858-24-000280:56.0:61.0', '0000070858-24-000280:59.0:63.0']
    0000070858-25-000200: changed/added/removed 3, spanning a large layout table: 0, other: 3 ['0000070858-25-000200:54.0:54.0', '0000070858-25-000200:54.1:60.0', '0000070858-25-000200:56.0:60.0']
    0000070858-25-000268: changed/added/removed 4, spanning a large layout table: 0, other: 4 ['0000070858-25-000268:54.0:54.0', '0000070858-25-000268:54.1:57.0', '0000070858-25-000268:56.0:60.0', '0000070858-25-000268:57.0:60.0']
    0000070858-25-000405: changed/added/removed 8, spanning a large layout table: 0, other: 8 ['0000070858-25-000405:54.0:54.0', '0000070858-25-000405:54.1:57.0', '0000070858-25-000405:56.0:60.0', '0000070858-25-000405:57.0:61.0']
    0000070858-26-000249: changed/added/removed 4, spanning a large layout table: 0, other: 4 ['0000070858-26-000249:54.0:54.0', '0000070858-26-000249:54.1:57.0', '0000070858-26-000249:56.0:60.0', '0000070858-26-000249:57.0:60.0']
    0000070858-26-000394: changed/added/removed 5, spanning a large layout table: 0, other: 5 ['0000070858-26-000394:54.0:54.0', '0000070858-26-000394:54.1:57.0', '0000070858-26-000394:56.0:60.0', '0000070858-26-000394:57.0:61.0']
    0000078003-23-000115: changed/added/removed 12, spanning a large layout table: 7, other: 5 ['0000078003-23-000115:658.0:662.0', '0000078003-23-000115:664.0:672.0', '0000078003-23-000115:667.0:672.0', '0000078003-23-000115:674.0:683.0']
    0000078003-24-000107: changed/added/removed 10, spanning a large layout table: 8, other: 2 ['0000078003-24-000107:603.0:609.0', '0000078003-24-000107:608.0:609.0']
    0000078003-24-000166: changed/added/removed 12, spanning a large layout table: 9, other: 3 ['0000078003-24-000166:652.0:653.0', '0000078003-24-000166:675.0:685.0', '0000078003-24-000166:680.0:688.0']
    0000078003-24-000191: changed/added/removed 17, spanning a large layout table: 7, other: 10 ['0000078003-24-000191:653.0:655.0', '0000078003-24-000191:658.0:667.0', '0000078003-24-000191:661.0:671.0', '0000078003-24-000191:666.0:671.0']
    0000078003-25-000114: changed/added/removed 10, spanning a large layout table: 7, other: 3 ['0000078003-25-000114:542.0:544.0', '0000078003-25-000114:560.0:565.0', '0000078003-25-000114:562.0:566.0']
    0000078003-25-000138: changed/added/removed 14, spanning a large layout table: 8, other: 6 ['0000078003-25-000138:571.0:576.0', '0000078003-25-000138:574.0:576.0', '0000078003-25-000138:578.0:589.0', '0000078003-25-000138:579.0:589.0']
    0000078003-25-000150: changed/added/removed 22, spanning a large layout table: 9, other: 13 ['0000078003-25-000150:597.0:603.0', '0000078003-25-000150:601.0:603.0', '0000078003-25-000150:605.0:610.0', '0000078003-25-000150:607.0:613.0']
    0000078003-26-000095: changed/added/removed 5, spanning a large layout table: 3, other: 2 ['0000078003-26-000095:562.0:562.0', '0000078003-26-000095:564.0:569.0']
    0000909832-23-000042: changed/added/removed 3, spanning a large layout table: 3, other: 0 []
    0000909832-24-000049: changed/added/removed 3, spanning a large layout table: 3, other: 0 []
    0001045810-26-000021: changed/added/removed 3, spanning a large layout table: 2, other: 1 ['0001045810-26-000021:1177.0:1182.0']
    0001628280-25-048859: changed/added/removed 5, spanning a large layout table: 4, other: 1 ['0001628280-25-048859:1147.0:1149.0']
    0001628280-26-029344: changed/added/removed 3, spanning a large layout table: 3, other: 0 []
    0001628280-26-054343: changed/added/removed 3, spanning a large layout table: 3, other: 0 []
    chunk changes (changed+added+removed) across 33 filings: 244; with a split source in the chunk or earlier in its prose run: 232; unexplained: 12
    with the prose run searched both ways: 244 of 244 explained; unexplained: []

The six clean filings that moved (COST 10-K x2, TGT 10-K x3, NVDA FY2026 10-K)
each contain layout tables over the prose budget that were sentence-split before
and are row-split now; the chunks around them in the same prose run re-pack.

`python -m api.index.embed` (9 min 25 s, MPS):

    checks: {'dim': 768, 'max_seq_length': 512, 'chunks_checked': 18788, 'token_count_mismatches': 0, 'over_max_seq_length': 0}
    embedded 17494, from cache 1294, skipped 0
    chunks with embedding IS NULL: 0

Resolve: 177,144 of 177,240 (0.999; 1.000 within Items), unchanged. `make test`:
241 passed, 3 snapshots passed.

## 2026-10-01 — After F-63..F-67: full corpus, final pass (freeze not written)

F-67 committed as `7b8fc9a`. Validate, chunk, embed, resolve on all 96, in order.

`python -m api.parse.validate` (`parser_version` d58d26e08e5a):

    parser_version d58d26e08e5a
    ticker accession              form   FY fp sect miss data alpha scale uncol spans items score  rows skip  status
    AAPL   0000320193-23-000106   10-K 2023 FY   23    0   46 0.762 0.976 1.000 0.994 1.000 0.994   983    6  parsed
    AAPL   0000320193-24-000006   10-Q 2024 Q1   11    0   24 0.724 0.957 1.000 0.996 1.000 0.991   522    2  parsed
    AAPL   0000320193-24-000069   10-Q 2024 Q2   11    0   24 0.704 0.957 1.000 0.997 1.000 0.991   676    2  parsed
    AAPL   0000320193-24-000081   10-Q 2024 Q3   11    0   24 0.698 0.957 1.000 0.996 1.000 0.990   678    3  parsed
    AAPL   0000320193-24-000123   10-K 2024 FY   23    0   44 0.765 0.974 1.000 0.996 1.000 0.994   957    4  parsed
    AAPL   0000320193-25-000008   10-Q 2025 Q1   11    0   23 0.736 0.955 1.000 0.994 1.000 0.990   520    3  parsed
    AAPL   0000320193-25-000057   10-Q 2025 Q2   11    0   23 0.725 0.955 1.000 0.997 1.000 0.990   670    2  parsed
    AAPL   0000320193-25-000073   10-Q 2025 Q3   11    0   25 0.701 0.957 1.000 0.996 1.000 0.990   680    3  parsed
    AAPL   0000320193-25-000079   10-K 2025 FY   23    0   43 0.765 0.974 1.000 0.995 1.000 0.994   962    5  parsed
    AAPL   0000320193-26-000006   10-Q 2026 Q1   11    0   23 0.722 0.955 1.000 0.993 1.000 0.989   554    4  parsed
    AAPL   0000320193-26-000013   10-Q 2026 Q2   11    0   25 0.733 0.958 1.000 0.995 1.000 0.991   750    4  parsed
    AAPL   0000320193-26-000020   10-Q 2026 Q3   11    0   26 0.728 0.960 1.000 0.995 1.000 0.991   756    4  parsed
    BAC    0000070858-23-000272   10-Q 2023 Q3    9    0  129 0.689 1.000 0.992 0.999 1.000 0.998  6826   10  parsed
    BAC    0000070858-24-000122   10-K 2023 FY   23    0  159 0.748 1.000 0.969 0.997 1.000 0.993     0   21  quarantined: required Item too short: Item 7A is 217 chars < 2746
    BAC    0000070858-24-000156   10-Q 2024 Q1    9    0  119 0.701 1.000 0.992 0.998 1.000 0.998  5402    9  parsed
    BAC    0000070858-24-000208   10-Q 2024 Q2    9    0  127 0.683 1.000 0.992 0.999 1.000 0.998  6856    6  parsed
    BAC    0000070858-24-000280   10-Q 2024 Q3    9    0  126 0.685 1.000 0.992 0.999 1.000 0.998  6898    8  parsed
    BAC    0000070858-25-000139   10-K 2024 FY   23    0  158 0.746 1.000 0.975 0.998 1.000 0.994     0   19  quarantined: required Item too short: Item 7A is 217 chars < 2746
    BAC    0000070858-25-000200   10-Q 2025 Q1    9    0  118 0.701 1.000 1.000 0.999 1.000 1.000  5408    6  parsed
    BAC    0000070858-25-000268   10-Q 2025 Q2    9    0  123 0.685 1.000 0.992 0.999 1.000 0.998  6834    6  parsed
    BAC    0000070858-25-000405   10-Q 2025 Q3    9    0  122 0.686 1.000 0.992 0.999 1.000 0.998  6876    7  parsed
    BAC    0000070858-26-000157   10-K 2025 FY   23    0  157 0.746 1.000 0.968 0.998 1.000 0.993     0   19  quarantined: required Item too short: Item 7A is 217 chars < 2746
    BAC    0000070858-26-000249   10-Q 2026 Q1    9    0  117 0.700 1.000 1.000 0.999 1.000 1.000  5396    8  parsed
    BAC    0000070858-26-000394   10-Q 2026 Q2    9    0  123 0.681 1.000 0.992 0.999 1.000 0.998  6817    8  parsed
    COST   0000909832-23-000042   10-K 2023 FY   22    0   44 0.775 0.938 1.000 0.995 1.000 0.987   833    4  parsed
    COST   0000909832-23-000065   10-Q 2024 Q1   11    0   25 0.755 0.882 1.000 0.990 1.000 0.974   392    4  parsed
    COST   0000909832-24-000017   10-Q 2024 Q2   11    0   26 0.739 0.889 1.000 0.993 1.000 0.976   569    4  parsed
    COST   0000909832-24-000029   10-Q 2024 Q3   11    0   26 0.738 0.889 1.000 0.993 1.000 0.976   566    4  parsed
    COST   0000909832-24-000049   10-K 2024 FY   23    0   44 0.776 0.938 1.000 0.995 1.000 0.987   837    4  parsed
    COST   0000909832-24-000079   10-Q 2025 Q1   11    0   25 0.758 0.882 1.000 0.989 1.000 0.974   357    4  parsed
    COST   0000909832-25-000015   10-Q 2025 Q2   11    0   26 0.743 0.889 1.000 0.992 1.000 0.976   495    4  parsed
    COST   0000909832-25-000033   10-Q 2025 Q3   11    0   26 0.740 0.889 1.000 0.992 1.000 0.976   490    4  parsed
    COST   0000909832-25-000101   10-K 2025 FY   23    0   44 0.779 0.938 1.000 0.994 1.000 0.986   818    5  parsed
    COST   0000909832-25-000169   10-Q 2026 Q1   11    0   27 0.756 0.895 1.000 0.988 1.000 0.976   395    5  parsed
    COST   0000909832-26-000029   10-Q 2026 Q2   11    0   28 0.738 0.900 1.000 0.991 1.000 0.978   571    5  parsed
    COST   0000909832-26-000051   10-Q 2026 Q3   11    0   28 0.737 0.900 1.000 0.991 1.000 0.978   570    5  parsed
    JPM    0000019617-23-000524   10-Q 2023 Q3   11    0  243 0.701 1.000 0.984 0.995 1.000 0.996  7819   36  parsed
    JPM    0000019617-24-000225   10-K 2023 FY   22    0  268 0.754 1.000 0.993 0.997 1.000 0.998     0   27  quarantined: required Item too short: Item 7 is 395 chars < 15352; Item 7A is 269 chars < 2746
    JPM    0000019617-24-000326   10-Q 2024 Q1   11    0  218 0.716 1.000 1.000 0.994 1.000 0.999  5755   33  parsed
    JPM    0000019617-24-000453   10-Q 2024 Q2   11    0  232 0.700 1.000 0.983 0.996 1.000 0.996  7386   31  parsed
    JPM    0000019617-24-000611   10-Q 2024 Q3   11    0  232 0.701 1.000 0.983 0.995 1.000 0.996  7373   37  parsed
    JPM    0000019617-25-000270   10-K 2024 FY   22    0  267 0.755 1.000 0.993 0.996 1.000 0.998     0   34  quarantined: required Item too short: Item 7 is 395 chars < 15352; Item 7A is 269 chars < 2746
    JPM    0000019617-25-000421   10-Q 2025 Q1   11    0  219 0.713 1.000 1.000 0.997 1.000 0.999  5717   20  parsed
    JPM    0000019617-25-000615   10-Q 2025 Q2   11    0  234 0.694 1.000 0.983 0.996 1.000 0.996  7338   27  parsed
    JPM    0001628280-25-048859   10-Q 2025 Q3   11    0  233 0.697 1.000 0.983 0.996 1.000 0.996  7354   33  parsed
    JPM    0001628280-26-008131   10-K 2025 FY   22    0  272 0.752 1.000 0.993 0.995 1.000 0.998     0   38  quarantined: required Item too short: Item 7 is 395 chars < 15352; Item 7A is 269 chars < 2746
    JPM    0001628280-26-029344   10-Q 2026 Q1   11    0  219 0.714 1.000 1.000 0.997 1.000 0.999  5650   16  parsed
    JPM    0001628280-26-054343   10-Q 2026 Q2   11    0  228 0.695 1.000 0.982 0.997 1.000 0.996  7351   20  parsed
    NVDA   0001045810-23-000227   10-Q 2024 Q3    9    0   41 0.762 1.000 1.000 0.998 1.000 1.000   964    2  parsed
    NVDA   0001045810-24-000029   10-K 2024 FY   23    0   53 0.790 1.000 1.000 0.993 1.000 0.999  1207    9  parsed
    NVDA   0001045810-24-000124   10-Q 2025 Q1    9    0   43 0.766 1.000 1.000 0.993 1.000 0.999   746    5  parsed
    NVDA   0001045810-24-000264   10-Q 2025 Q2    9    0   45 0.755 1.000 1.000 0.995 1.000 0.999   988    5  parsed
    NVDA   0001045810-24-000316   10-Q 2025 Q3    9    0   44 0.754 1.000 1.000 0.996 1.000 0.999   984    4  parsed
    NVDA   0001045810-25-000023   10-K 2025 FY   23    0   56 0.789 1.000 1.000 0.993 1.000 0.999  1220    9  parsed
    NVDA   0001045810-25-000116   10-Q 2026 Q1    9    0   40 0.768 1.000 1.000 0.994 1.000 0.999   721    4  parsed
    NVDA   0001045810-25-000209   10-Q 2026 Q2    9    0   39 0.752 1.000 1.000 0.994 1.000 0.999   940    6  parsed
    NVDA   0001045810-25-000230   10-Q 2026 Q3    9    0   38 0.761 1.000 1.000 0.992 1.000 0.998   943    8  parsed
    NVDA   0001045810-26-000021   10-K 2026 FY   23    0   49 0.790 1.000 1.000 0.991 1.000 0.998  1117   10  parsed
    NVDA   0001045810-26-000052   10-Q 2027 Q1    9    0   37 0.769 1.000 1.000 0.994 1.000 0.999   699    4  parsed
    NVDA   0001045810-26-000075   10-Q 2027 Q2    9    0   41 0.753 1.000 1.000 0.996 1.000 0.999   996    4  parsed
    PFE    0000078003-23-000115   10-Q 2023 Q3    9    0   46 0.760 1.000 1.000 0.989 1.000 0.998  1856   20  parsed
    PFE    0000078003-24-000039   10-K 2023 FY   20    0   78 0.784 1.000 1.000 0.988 1.000 0.998     0   37  quarantined: required Item too short: Item 7A is 289 chars < 2746
    PFE    0000078003-24-000107   10-Q 2024 Q1    9    0   44 0.773 1.000 1.000 0.982 1.000 0.996  1194   22  parsed
    PFE    0000078003-24-000166   10-Q 2024 Q2    9    0   50 0.758 1.000 1.000 0.988 1.000 0.998  1775   22  parsed
    PFE    0000078003-24-000191   10-Q 2024 Q3    9    0   50 0.758 1.000 1.000 0.985 1.000 0.997  1797   27  parsed
    PFE    0000078003-25-000054   10-K 2024 FY   20    0   86 0.783 1.000 1.000 0.984 1.000 0.997     0   47  quarantined: required Item too short: Item 7A is 289 chars < 2746
    PFE    0000078003-25-000114   10-Q 2025 Q1    9    0   41 0.774 1.000 1.000 0.974 1.000 0.995  1112   30  parsed
    PFE    0000078003-25-000138   10-Q 2025 Q2    9    0   50 0.757 1.000 1.000 0.984 1.000 0.997  1662   27  parsed
    PFE    0000078003-25-000150   10-Q 2025 Q3    9    0   50 0.760 1.000 1.000 0.986 1.000 0.997  1724   24  parsed
    PFE    0000078003-26-000026   10-K 2025 FY   20    0   82 0.785 1.000 1.000 0.986 1.000 0.997     0   40  quarantined: required Item too short: Item 7A is 289 chars < 2746
    PFE    0000078003-26-000054   10-Q 2026 Q1    9    0   40 0.773 1.000 1.000 0.984 1.000 0.997  1207   20  parsed
    PFE    0000078003-26-000095   10-Q 2026 Q2    9    0   48 0.757 1.000 1.000 0.989 1.000 0.998  1789   20  parsed
    TGT    0000027419-23-000052   10-Q 2023 Q3   11    0   29 0.716 1.000 1.000 0.980 1.000 0.996   553   11  parsed
    TGT    0000027419-24-000032   10-K 2023 FY   23    0   60 0.768 0.977 1.000 0.986 1.000 0.993   984   14  parsed
    TGT    0000027419-24-000129   10-Q 2024 Q1   11    0   28 0.730 1.000 1.000 0.982 1.000 0.996   385    7  parsed
    TGT    0000027419-24-000152   10-Q 2024 Q2   11    0   30 0.710 1.000 1.000 0.985 1.000 0.997   517    8  parsed
    TGT    0000027419-24-000179   10-Q 2024 Q3   11    0   30 0.711 1.000 1.000 0.982 1.000 0.996   532   10  parsed
    TGT    0000027419-25-000018   10-K 2024 FY   23    0   62 0.773 1.000 1.000 0.988 1.000 0.998   973   12  parsed
    TGT    0000027419-25-000101   10-Q 2025 Q1   11    0   30 0.734 1.000 1.000 0.981 1.000 0.996   406    8  parsed
    TGT    0000027419-25-000118   10-Q 2025 Q2   11    0   33 0.718 1.000 1.000 0.986 1.000 0.997   546    8  parsed
    TGT    0000027419-25-000126   10-Q 2025 Q3   11    0   34 0.720 1.000 1.000 0.983 1.000 0.997   576   10  parsed
    TGT    0000027419-26-000016   10-K 2025 FY   23    0   64 0.774 1.000 1.000 0.987 1.000 0.997   977   13  parsed
    TGT    0000027419-26-000022   10-Q 2026 Q1   11    0   30 0.736 1.000 1.000 0.980 1.000 0.996   401    8  parsed
    TGT    0000027419-26-000042   10-Q 2026 Q2   11    0   32 0.720 1.000 1.000 0.979 1.000 0.996   547   12  parsed
    XOM    0000034088-23-000056   10-Q 2023 Q3    8    0   36 0.715 1.000 1.000 1.000 1.000 1.000   883    0  parsed
    XOM    0000034088-24-000018   10-K 2023 FY   22    0  113 0.738 1.000 0.982 1.000 1.000 0.996     0    1  quarantined: required Item too short: Item 1 is 7380 chars < 15096; Item 1A is 29659 chars < 33805; Item 7 is 265 chars < 15352; Item 7A is 409 chars < 2746
    XOM    0000034088-24-000029   10-Q 2024 Q1    8    0   35 0.740 1.000 1.000 1.000 1.000 1.000   550    0  parsed
    XOM    0000034088-24-000050   10-Q 2024 Q2    8    0   40 0.715 1.000 1.000 1.000 1.000 1.000   915    0  parsed
    XOM    0000034088-24-000068   10-Q 2024 Q3    8    0   40 0.714 1.000 1.000 1.000 1.000 1.000   917    0  parsed
    XOM    0000034088-25-000010   10-K 2024 FY   22    0  118 0.739 1.000 0.958 1.000 1.000 0.991     0    1  quarantined: required Item too short: Item 1 is 7193 chars < 15096; Item 1A is 32305 chars < 33805; Item 7 is 264 chars < 15352; Item 7A is 409 chars < 2746
    XOM    0000034088-25-000024   10-Q 2025 Q1    8    0   38 0.730 1.000 0.947 1.000 1.000 0.989   903    0  parsed
    XOM    0000034088-25-000042   10-Q 2025 Q2    8    0   44 0.695 1.000 0.909 1.000 1.000 0.982  1533    0  parsed
    XOM    0000034088-25-000061   10-Q 2025 Q3    8    0   44 0.697 1.000 0.909 1.000 1.000 0.982  1526    0  parsed
    XOM    0000034088-26-000045   10-K 2025 FY   22    0  116 0.739 1.000 0.983 0.999 1.000 0.996     0    2  quarantined: required Item too short: Item 1 is 6636 chars < 15096; Item 7 is 264 chars < 15352; Item 7A is 456 chars < 2746
    XOM    0000034088-26-000067   10-Q 2026 Q1    9    0   34 0.732 1.000 0.941 0.999 1.000 0.988   851    1  parsed
    XOM    0000034088-26-000093   10-Q 2026 Q2    9    0   36 0.703 1.000 0.889 0.999 1.000 0.978  1467    2  parsed

84 parsed, 12 quarantined -- all 10-Ks:
- JPM x3: Items 7 and 7A are cross-reference stubs (395 / 269 chars); the
  Annual Report holding MD&A and statements is reached only by page reference
  (F-66; no page mechanism, F-55).
- BAC x3: Item 7A is a 217-char cross-reference to MD&A (F-69).
- PFE x3: Item 7A is a 289-char cross-reference to MD&A (F-69).
- XOM x3: Items 1 and 1A shorter than the four-filer floors, Item 7 a 264-char
  stub (MD&A in an appended Financial Section), Item 7A a 409-456-char
  cross-reference (F-69).

`check_stored_spans`: `total rows 177240, mismatches 0`. Chunks: 18,788, 0 over
512 (`chunker_version` 964f77f6f9cb). Embed: checks passed on 18,788 chunks, 0
embedded, 18,788 from cache, 0 without an embedding. Resolve: 177,144 of 177,240
(0.999; 1.000 within Items), 96 before the first Item. `make test`: 241 passed, 3
snapshots passed.

The freeze is the owner's call on these numbers.

## 2026-10-01 — F-69: the stub check replaces the content floors

Final pass committed as `dd6b63a`.

Every required Item's length on all 96 filings; each under 5,000 chars quoted
in full (264 Items measured):

    AAPL  0000320193-23-000106 10-K Item 7A: 3022 chars
          'Item 7A. Quantitative and Qualitative Disclosures About Market Risk The Company is exposed to economic risk from interest rates and foreign exchange rates. The Company uses various strategies to manage these risks; however, they may still impact the Company’s consolidated financial statements. Interest Rate Risk The Company is primarily exposed to fluctuations in U.S. interest rates and their impact on the Company’s investment portfolio and term debt. Increases in interest rates will negatively affect the fair value of the Company’s investment portfolio and increase the interest expense on the Company’s term debt. To protect against interest rate risk, the Company may use derivative instruments, offset interest rate–sensitive assets and liabilities, or control duration of the investment and term debt portfolios. The following table sets forth potential impacts on the Company’s investment portfolio and term debt, including the effects of any associated derivatives, that would result from a hypothetical increase in relevant interest rates as of September 30, 2023 and September 24, 2022 (dollars in millions): Interest Rate Sensitive Instrument Hypothetical Interest Rate Increase Potential Impact 2023 2022 Investment portfolio 100 basis points, all tenors Decline in fair value $ 3,089 $ 4,022 Term debt 100 basis points, all tenors Increase in annual interest expense $ 194 $ 201 Foreign Exchange Rate Risk The Company’s exposure to foreign exchange rate risk relates primarily to the Company being a net receiver of currencies other than the U.S. dollar. Changes in exchange rates, and in particular a strengthening of the U.S. dollar, will negatively affect the Company’s net sales and gross margins as expressed in U.S. dollars. Fluctuations in exchange rates may also affect the fair values of certain of the Company’s assets and liabilities. To protect against foreign exchange rate risk, the Company may use derivative instruments, offset exposures, or adjust local currency pricing of its products and services. However, the Company may choose to not hedge certain foreign currency exposures for a variety of reasons, including accounting considerations or prohibitive cost. The Company applied a value-at-risk (“VAR”) model to its foreign currency derivative positions to assess the potential impact of fluctuations in exchange rates. The VAR model used a Monte Carlo simulation. The VAR is the maximum expected loss in fair value, for a given confidence interval, to the Company’s foreign currency derivative positions due to adverse movements in rates. Based on the results of the model, the Company estimates, with 95% confidence, a maximum one-day loss in fair value of $669 million and $1.0 billion as of September 30, 2023 and September 24, 2022, respectively. Changes in the Company’s underlying foreign currency exposures, which were excluded from the assessment, generally offset changes in the fair values of the Company’s foreign currency derivatives. Apple Inc. | 2023 Form 10-K | 26'
    AAPL  0000320193-24-000123 10-K Item 7A: 3022 chars
          'Item 7A. Quantitative and Qualitative Disclosures About Market Risk The Company is exposed to economic risk from interest rates and foreign exchange rates. The Company uses various strategies to manage these risks; however, they may still impact the Company’s consolidated financial statements. Interest Rate Risk The Company is primarily exposed to fluctuations in U.S. interest rates and their impact on the Company’s investment portfolio and term debt. Increases in interest rates will negatively affect the fair value of the Company’s investment portfolio and increase the interest expense on the Company’s term debt. To protect against interest rate risk, the Company may use derivative instruments, offset interest rate–sensitive assets and liabilities, or control duration of the investment and term debt portfolios. The following table sets forth potential impacts on the Company’s investment portfolio and term debt, including the effects of any associated derivatives, that would result from a hypothetical increase in relevant interest rates as of September 28, 2024 and September 30, 2023 (dollars in millions): Interest Rate Sensitive Instrument Hypothetical Interest Rate Increase Potential Impact 2024 2023 Investment portfolio 100 basis points, all tenors Decline in fair value $ 2,755 $ 3,089 Term debt 100 basis points, all tenors Increase in annual interest expense $ 139 $ 194 Foreign Exchange Rate Risk The Company’s exposure to foreign exchange rate risk relates primarily to the Company being a net receiver of currencies other than the U.S. dollar. Changes in exchange rates, and in particular a strengthening of the U.S. dollar, will negatively affect the Company’s net sales and gross margins as expressed in U.S. dollars. Fluctuations in exchange rates may also affect the fair values of certain of the Company’s assets and liabilities. To protect against foreign exchange rate risk, the Company may use derivative instruments, offset exposures, or adjust local currency pricing of its products and services. However, the Company may choose to not hedge certain foreign currency exposures for a variety of reasons, including accounting considerations or prohibitive cost. The Company applied a value-at-risk (“VAR”) model to its foreign currency derivative positions to assess the potential impact of fluctuations in exchange rates. The VAR model used a Monte Carlo simulation. The VAR is the maximum expected loss in fair value, for a given confidence interval, to the Company’s foreign currency derivative positions due to adverse movements in rates. Based on the results of the model, the Company estimates, with 95% confidence, a maximum one-day loss in fair value of $538 million and $669 million as of September 28, 2024 and September 30, 2023, respectively. Changes in the Company’s underlying foreign currency exposures, which were excluded from the assessment, generally offset changes in the fair values of the Company’s foreign currency derivatives. Apple Inc. | 2024 Form 10-K | 27'
    AAPL  0000320193-25-000079 10-K Item 7A: 3023 chars
          'Item 7A. Quantitative and Qualitative Disclosures About Market Risk The Company is exposed to economic risk from interest rates and foreign exchange rates. The Company uses various strategies to manage these risks; however, they may still impact the Company’s consolidated financial statements. Interest Rate Risk The Company is primarily exposed to fluctuations in U.S. interest rates and their impact on the Company’s investment portfolio and term debt. Increases in interest rates will negatively affect the fair value of the Company’s investment portfolio and increase the interest expense on the Company’s term debt. To protect against interest rate risk, the Company may use derivative instruments, offset interest rate–sensitive assets and liabilities, or control duration of the investment and term debt portfolios. The following table sets forth potential impacts on the Company’s investment portfolio and term debt, including the effects of any associated derivatives, that would result from a hypothetical increase in relevant interest rates as of September 27, 2025 and September 28, 2024 (dollars in millions): Interest Rate Sensitive Instrument Hypothetical Interest Rate Increase Potential Impact 2025 2024 Investment portfolio 100 basis points, all tenors Decline in fair value $ 2,416 $ 2,755 Term debt 100 basis points, all tenors Increase in annual interest expense $ 129 $ 139 Foreign Exchange Rate Risk The Company’s exposure to foreign exchange rate risk relates primarily to the Company being a net receiver of currencies other than the U.S. dollar. Changes in exchange rates, and in particular a strengthening of the U.S. dollar, will negatively affect the Company’s net sales and gross margins as expressed in U.S. dollars. Fluctuations in exchange rates may also affect the fair values of certain of the Company’s assets and liabilities. To protect against foreign exchange rate risk, the Company may use derivative instruments, offset exposures, or adjust local currency pricing of its products and services. However, the Company may choose to not hedge certain foreign currency exposures for a variety of reasons, including accounting considerations or prohibitive cost. The Company applied a value-at-risk (“VAR”) model to its foreign currency derivative positions to assess the potential impact of fluctuations in exchange rates. The VAR model used a Monte Carlo simulation. The VAR is the maximum expected loss in fair value, for a given confidence interval, to the Company’s foreign currency derivative positions due to adverse movements in rates. Based on the results of the model, the Company estimates, with 95% confidence, a maximum one-day loss in fair value of $590 million and $538 million as of September 27, 2025 and September 28, 2024, respectively. Changes in the Company’s underlying foreign currency exposures, which were excluded from the assessment, generally offset changes in the fair values of the Company’s foreign currency derivatives. Apple Inc. | 2025 Form 10-K | 27'
    BAC   0000070858-24-000122 10-K Item 7A: 217 chars
          'Item 7A. Quantitative and Qualitative Disclosures about Market Risk See Market Risk Management on page 73 in the MD&A and the sections referenced therein for Quantitative and Qualitative Disclosures about Market Risk.'
    BAC   0000070858-25-000139 10-K Item 7A: 217 chars
          'Item 7A. Quantitative and Qualitative Disclosures about Market Risk See Market Risk Management on page 74 in the MD&A and the sections referenced therein for Quantitative and Qualitative Disclosures about Market Risk.'
    BAC   0000070858-26-000157 10-K Item 7A: 217 chars
          'Item 7A. Quantitative and Qualitative Disclosures about Market Risk See Market Risk Management on page 75 in the MD&A and the sections referenced therein for Quantitative and Qualitative Disclosures about Market Risk.'
    COST  0000909832-23-000042 10-K Item 7A: 4460 chars
          "Item 7A—Quantitative and Qualitative Disclosures About Market Risk (amounts in millions) Our exposure to financial market risk results from fluctuations in interest rates and foreign currency exchange rates. We do not engage in speculative or leveraged transactions or hold or issue financial instruments for trading purposes. Interest Rate Risk Our exposure to market risk for changes in interest rates relates primarily to our investment holdings that are diversified among various instruments considered to be cash equivalents, as defined in Note 1 to the consolidated financial statements included in Item 8 of this Report, as well as short-term investments in government and agency securities with effective maturities of generally three months to five years at the date of purchase. The primary objective of our investment activities is to preserve principal and secondarily to generate yields. The majority of our short-term investments are in fixed interest-rate securities. These securities are subject to changes in fair value due to interest rate fluctuations. Our policy limits investments in the U.S. to direct U.S. government and government agency obligations, repurchase agreements collateralized by U.S. government and government agency obligations, U.S. government and government agency money market funds, and insured bank balances. Our wholly-owned captive insurance subsidiary invests in U.S. government and government agency obligations and U.S. government and government agency money market funds. Our Canadian and Other International subsidiaries’ investments are primarily in money market funds, bankers’ acceptances, and bank certificates of deposit, generally denominated in local currencies. A 100 basis point change in interest rates as of the end of 2023 would have had an immaterial incremental change in fair market value. For those investments that are classified as available-for-sale, the unrealized gains or losses related to fluctuations in market volatility and interest rates are reflected within stockholders’ equity in accumulated other comprehensive income in the consolidated balance sheets. The nature and amount of our long-term debt may vary as a result of business requirements, market conditions, and other factors. As of the end of 2023, long-term debt with fixed interest rates was $6,484. Fluctuations in interest rates may affect the fair value of the fixed-rate debt. See Note 4 to the consolidated financial statements included in Item 8 of this Report for more information on our long-term debt. Foreign Currency Risk Our foreign subsidiaries conduct certain transactions in non-functional currencies, which exposes us to fluctuations in exchange rates. We manage these fluctuations, in part, through the use of forward foreign-exchange contracts, seeking to economically hedge the impact of these fluctuations on known future expenditures denominated in a non-functional foreign-currency. The contracts are intended primarily to economically hedge exposure to U.S. dollar merchandise inventory expenditures made by our 28 Table of Contents international subsidiaries. We seek to mitigate risk with the use of these contracts and do not intend to engage in speculative transactions. For additional information related to the Company's forward foreign-exchange contracts, see Notes 1 and 3 to the consolidated financial statements included in Item 8 of this Report. A hypothetical 10% strengthening of the functional currency compared to the non-functional currency exchange rates at September 3, 2023, would have decreased the fair value of the contracts by $109 and resulted in an unrealized loss in the consolidated statements of income for the same amount. Commodity Price Risk We are exposed to fluctuations in prices for energy, particularly electricity and natural gas, and other commodities used in retail and manufacturing operations, which we seek to partially mitigate through fixed-price contracts for certain of our warehouses and other facilities, predominantly in the U.S. and Canada. We also enter into variable-priced contracts for some purchases of electricity and natural gas, in addition to some of the fuel for our gas stations, on an index basis. These contracts meet the characteristics of derivative instruments, but generally qualify for the “normal purchases and normal sales” exception under authoritative guidance and require no mark-to-market adjustment. 29 Table of Contents"
    COST  0000909832-24-000049 10-K Item 7A: 4474 chars
          "Item 7A—Quantitative and Qualitative Disclosures About Market Risk (amounts in millions) Our exposure to financial market risk results from fluctuations in interest rates and foreign currency exchange rates. We do not engage in speculative or leveraged transactions or hold or issue financial instruments for trading purposes. Interest Rate Risk Our exposure to market risk for changes in interest rates relates primarily to our investment holdings that are diversified among various instruments considered to be cash equivalents, as defined in Note 1 to the consolidated financial statements included in Item 8 of this Report, as well as short-term investments in government and agency securities with effective maturities of generally three months to five years at the date of purchase. The primary objective of our investment activities is to preserve principal and secondarily to generate yields. The majority of our short-term investments are in fixed interest-rate securities. These securities are subject to changes in fair value due to interest rate fluctuations. Our policy limits investments in the U.S. to direct U.S. government and government agency obligations, repurchase agreements collateralized by U.S. government and government agency obligations, U.S. government and government agency money market funds, and insured bank balances. Our wholly-owned captive insurance subsidiary invests in U.S. government and government agency obligations and U.S. government and government agency money market funds. Our Canadian and Other International subsidiaries’ investments are primarily in money market funds, bankers’ acceptances, and bank certificates of deposit, generally denominated in local currencies. A 100 basis point change in interest rates as of the end of 2024 would have had an immaterial incremental change in fair market value. For those investments that are classified as available-for-sale, the unrealized gains or losses related to fluctuations in market volatility and interest rates are reflected 30 Table of Contents within stockholders’ equity in accumulated other comprehensive income in the consolidated balance sheets. The nature and amount of our long-term debt may vary as a result of business requirements, market conditions, and other factors. As of the end of 2024, long-term debt with fixed interest rates was $5,919. Fluctuations in interest rates may affect the fair value of the fixed-rate debt. See Note 4 to the consolidated financial statements included in Item 8 of this Report for more information on our long-term debt. Foreign Currency Risk Our foreign subsidiaries conduct certain transactions in non-functional currencies, which exposes us to fluctuations in exchange rates. We manage these fluctuations, in part, through the use of forward foreign-exchange contracts, seeking to economically hedge the impact of these fluctuations on known future expenditures denominated in a non-functional foreign-currency. The contracts are intended primarily to economically hedge exposure to U.S. dollar merchandise inventory expenditures made by our international subsidiaries. We seek to mitigate risk with the use of these contracts and do not intend to engage in speculative transactions. For additional information related to the Company's forward foreign-exchange contracts, see Notes 1 and 3 to the consolidated financial statements included in Item 8 of this Report. A hypothetical 10% strengthening of the functional currencies compared to the non-functional currency exchange rates at September 1, 2024, would have decreased the fair value of the contracts by approximately $120 and resulted in an unrealized loss in the consolidated statements of income for the same amount. Commodity Price Risk We are exposed to fluctuations in prices for energy, particularly electricity and natural gas, and other commodities used in retail and manufacturing operations, which we seek to partially mitigate through fixed-price contracts for certain of our warehouses and other facilities, predominantly in the U.S. and Canada. We also enter into variable-priced contracts for some purchases of electricity and natural gas, in addition to some of the fuel for our gas stations, on an index basis. These contracts meet the characteristics of derivative instruments, but generally qualify for the “normal purchases and normal sales” exception under authoritative guidance and require no mark-to-market adjustment. 31 Table of Contents"
    COST  0000909832-25-000101 10-K Item 7A: 4474 chars
          "Item 7A—Quantitative and Qualitative Disclosures About Market Risk (amounts in millions) Our exposure to financial market risk results from fluctuations in interest rates and foreign-currency exchange rates. We do not engage in speculative or leveraged transactions or hold or issue financial instruments for trading purposes. Interest Rate Risk Our exposure to market risk for changes in interest rates relates primarily to our investment holdings, which are diversified among various instruments considered to be cash equivalents, as defined in Note 1 to the consolidated financial statements included in Item 8 of this Report, as well as short-term investments in government and agency securities with effective maturities of generally three months to five years at the date of purchase. The primary objective of our investment activities is to preserve principal and secondarily to generate yields. The majority of our short-term investments are in fixed interest-rate securities. These securities are subject to changes in fair value due to interest rate fluctuations. Our policy limits investments in the U.S. to direct U.S. government and government agency obligations, repurchase agreements collateralized by U.S. government and government agency obligations, U.S. government and government agency money market funds, and insured bank balances. Our wholly-owned captive insurance subsidiary invests in U.S. government and government agency obligations and U.S. government and government agency money market funds. Our Canadian and Other International subsidiaries’ investments are primarily in money market funds, bankers’ acceptances, and bank certificates of deposit, generally denominated in local currencies. A 100 basis point change in interest rates as of the end of 2025 would have had an immaterial incremental change in fair market value. For those investments that are classified as available-for-sale, the unrealized gains or losses related to fluctuations in market volatility and interest rates are reflected within stockholders’ equity in accumulated other comprehensive income in the consolidated balance sheets. The nature and amount of our long-term debt may vary as a result of business requirements, market conditions, and other factors. As of the end of 2025, long-term debt with fixed interest rates was $5,805. Fluctuations in interest rates may affect the fair value of the fixed-rate debt. See Note 4 to the consolidated financial statements included in Item 8 of this Report for more information on our long-term debt. Foreign-Currency Risk Our foreign subsidiaries conduct certain transactions in non-functional currencies, which exposes us to fluctuations in exchange rates. We manage these fluctuations, in part, through the use of forward foreign-exchange contracts, seeking to economically hedge the impact of these fluctuations on known future expenditures denominated in a non-functional foreign-currency. The contracts are intended primarily to economically hedge exposure to U.S. dollar merchandise inventory expenditures made by our international subsidiaries. We seek to mitigate risk with the use of these contracts and do not intend to engage in speculative transactions. For additional information related to the Company's forward foreign-exchange contracts, see Notes 1 and 3 to the consolidated financial statements included in Item 8 of this 31 Table of Contents Report. A hypothetical 10% strengthening of the functional currencies compared to the non-functional currency exchange rates at August 31, 2025, would have decreased the fair value of the contracts by approximately $117 and resulted in an unrealized loss in the consolidated statements of income for the same amount. Commodity Price Risk We are exposed to fluctuations in prices for energy, particularly electricity and natural gas, and other commodities used in retail and manufacturing operations. We seek to partially mitigate these through fixed-price contracts for certain of our warehouses and other facilities, predominantly in the U.S. and Canada. We also enter into variable-priced contracts for some purchases of electricity and natural gas, in addition to some of the fuel for our gas stations, on an index basis. These contracts meet the characteristics of derivative instruments, but generally qualify for the “normal purchases and normal sales” exception under authoritative guidance and require no mark-to-market adjustment. 32 Table of Contents"
    JPM   0000019617-24-000225 10-K Item 7: 395 chars
          'Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations. Management’s discussion and analysis of financial condition and results of operations, entitled “Management’s discussion and analysis,” appears on pages 48–161. Such information should be read in conjunction with the Consolidated Financial Statements and Notes thereto, which appear on pages 166–309.'
    JPM   0000019617-24-000225 10-K Item 7A: 269 chars
          'Item 7A. Quantitative and Qualitative Disclosures About Market Risk. Refer to the Market Risk Management section of Management’s discussion and analysis on pages 135–143 for a discussion of quantitative and qualitative disclosures about market risk. 35 Parts II and III'
    JPM   0000019617-24-000225 10-K Item 8: 368 chars
          'Item 8. Financial Statements and Supplementary Data. The Consolidated Financial Statements, together with the Notes thereto and the report thereon dated February 16, 2024, of PricewaterhouseCoopers LLP, the Firm’s independent registered public accounting firm (PCAOB ID 238), appear on pages 163–309. The “Glossary of Terms and Acronyms’’ is included on pages 315-321.'
    JPM   0000019617-25-000270 10-K Item 7: 395 chars
          'Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations. Management’s discussion and analysis of financial condition and results of operations, entitled “Management’s discussion and analysis,” appears on pages 52–167. Such information should be read in conjunction with the Consolidated Financial Statements and Notes thereto, which appear on pages 172–321.'
    JPM   0000019617-25-000270 10-K Item 7A: 269 chars
          'Item 7A. Quantitative and Qualitative Disclosures About Market Risk. Refer to the Market Risk Management section of Management’s discussion and analysis on pages 141–149 for a discussion of quantitative and qualitative disclosures about market risk. 39 Parts II and III'
    JPM   0000019617-25-000270 10-K Item 8: 368 chars
          'Item 8. Financial Statements and Supplementary Data. The Consolidated Financial Statements, together with the Notes thereto and the report thereon dated February 14, 2025, of PricewaterhouseCoopers LLP, the Firm’s independent registered public accounting firm (PCAOB ID 238), appear on pages 169–321. The “Glossary of Terms and Acronyms’’ is included on pages 327–333.'
    JPM   0001628280-26-008131 10-K Item 7: 395 chars
          'Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations. Management’s discussion and analysis of financial condition and results of operations, entitled “Management’s discussion and analysis,” appears on pages 46–160. Such information should be read in conjunction with the Consolidated Financial Statements and Notes thereto, which appear on pages 165–314.'
    JPM   0001628280-26-008131 10-K Item 7A: 269 chars
          'Item 7A. Quantitative and Qualitative Disclosures About Market Risk. Refer to the Market Risk Management section of Management’s discussion and analysis on pages 133-142 for a discussion of quantitative and qualitative disclosures about market risk. 33 Parts II and III'
    JPM   0001628280-26-008131 10-K Item 8: 368 chars
          'Item 8. Financial Statements and Supplementary Data. The Consolidated Financial Statements, together with the Notes thereto and the report thereon dated February 13, 2026, of PricewaterhouseCoopers LLP, the Firm’s independent registered public accounting firm (PCAOB ID 238), appear on pages 162–314. The “Glossary of Terms and Acronyms’’ is included on pages 320–327.'
    NVDA  0001045810-24-000029 10-K Item 7A: 3295 chars
          'Item 7A. Quantitative and Qualitative Disclosures about Market Risk Investment and Interest Rate Risk We are exposed to interest rate risk related to our fixed-rate investment portfolio and outstanding debt. The investment portfolio is managed consistent with our overall liquidity strategy in support of both working capital needs and growth of our businesses. As of the end of fiscal year 2024, we performed a sensitivity analysis on our investment portfolio. According to our analysis, parallel shifts in the yield curve of plus or minus 0.5% would result in a change in fair value for these investments of $93 million. As of the end of fiscal year 2024, we had $9.7 billion of senior Notes net outstanding. We carry the Notes at face value less unamortized discount on our Consolidated Balance Sheets. As the Notes bear interest at a fixed rate, we have no 43 Table of Contents financial statement risk associated with changes in interest rates. Refer to Note 12 of the Notes to the Consolidated Financial Statements in Part IV, Item 15 of this Annual Report on Form 10-K for additional information. Foreign Exchange Rate Risk We consider our direct exposure to foreign exchange rate fluctuations to be minimal as our sales are in United States dollars and foreign currency forward contracts are used to offset movements of foreign currency exchange rate movements. Gains or losses from foreign currency remeasurement are included in other income or expenses. The impact of foreign currency transaction gain or loss included in determining net income was not significant for fiscal years 2024 and 2023. Sales and arrangements with third-party manufacturers provide for pricing and payment in United States dollars, and, therefore, are not subject to exchange rate fluctuations. Increases in the value of the United States’ dollar relative to other currencies would make our products more expensive, which could negatively impact our ability to compete. Conversely, decreases in the value of the United States’ dollar relative to other currencies could result in our suppliers raising their manufacturing costs. If the U.S. dollar strengthened by 10% as of January 28, 2024 and January 29, 2023, the amount recorded in accumulated other comprehensive income (loss) related to our foreign exchange contracts before tax effect would have been $116 million and $112 million lower, respectively. Change in value recorded in accumulated other comprehensive income (loss) would be expected to offset a corresponding change in hedged forecasted foreign currency expenses when recognized. If an adverse 10% foreign exchange rate change was applied to our balance sheet hedging contracts, it would have resulted in an adverse impact on income before taxes of $60 million and $36 million as of January 28, 2024 and January 29, 2023, respectively. These changes in fair values would be offset in other income (expense), net by corresponding change in fair values of the foreign currency denominated monetary assets and liabilities, assuming the hedge contracts fully cover the foreign currency denominated monetary assets and liabilities balances. Refer to Note 11 of the Notes to the Consolidated Financial Statements in Part IV, Item 15 of this Annual Report on Form 10-K for additional information.'
    NVDA  0001045810-24-000029 10-K Item 8: 206 chars
          'Item 8. Financial Statements and Supplementary Data The information required by this Item is set forth in our Consolidated Financial Statements and Notes thereto included in this Annual Report on Form 10-K.'
    NVDA  0001045810-25-000023 10-K Item 7A: 3305 chars
          'Item 7A. Quantitative and Qualitative Disclosures about Market Risk Investment and Interest Rate Risk We are exposed to interest rate risk related to our fixed-rate investment portfolio and outstanding debt. The investment portfolio is managed consistent with our overall liquidity strategy in support of both working capital needs and growth of our businesses. As of the end of fiscal year 2025, we performed a sensitivity analysis on our investment portfolio. According to our analysis, parallel shifts in the yield curve of plus or minus 0.5% would result in a change in fair value for these investments of $238 million. As of the end of fiscal year 2025, we had $8.5 billion of senior Notes outstanding. We carry the Notes at face value less unamortized discount on our Consolidated Balance Sheets. As the Notes bear interest at a fixed rate, we have no financial statement risk associated with changes in interest rates. Refer to Note 11 of the Notes to the Consolidated Financial Statements in Part IV, Item 15 of this Annual Report on Form 10-K for additional information. Foreign Exchange Rate Risk We consider our direct exposure to foreign exchange rate fluctuations to be minimal as substantially all of our sales are in United States dollars and foreign currency forward contracts are used to offset movements of foreign currency exchange rates. Gains or losses from foreign currency remeasurement are included in other income or expenses. The impact of foreign currency transaction gain or loss included in determining net income was not significant for fiscal years 2025 and 2024. Sales and arrangements with third-party manufacturers provide for pricing and payment in United States dollars, and, therefore, are not subject to exchange rate fluctuations. Increases in the value of the United States’ dollar relative to other currencies would make our products more expensive, which could negatively impact our ability to compete. Conversely, decreases in the value of the United States’ dollar relative to other currencies could result in our suppliers raising their manufacturing costs. If the U.S. dollar strengthened by 10% as of January 26, 2025 and January 28, 2024, the amount recorded in accumulated other comprehensive income (loss) related to our foreign exchange contracts before tax effect would have been $136 million and $116 million lower, respectively. Change in value recorded in accumulated other comprehensive income (loss) would be expected to offset a corresponding change in hedged forecasted foreign currency expenses when recognized. If an adverse 10% foreign exchange rate change was applied to our balance sheet hedging contracts, it would have resulted in an adverse impact on income before taxes of $129 million and $60 million as of January 26, 2025 and January 28, 2024, respectively. These changes in fair values would be offset in other income (expense), net by 45 Table of Contents corresponding change in fair values of the foreign currency denominated monetary assets and liabilities, assuming the hedge contracts fully cover the foreign currency denominated monetary assets and liabilities balances. Refer to Note 10 of the Notes to the Consolidated Financial Statements in Part IV, Item 15 of this Annual Report on Form 10-K for additional information.'
    NVDA  0001045810-25-000023 10-K Item 8: 206 chars
          'Item 8. Financial Statements and Supplementary Data The information required by this Item is set forth in our Consolidated Financial Statements and Notes thereto included in this Annual Report on Form 10-K.'
    NVDA  0001045810-26-000021 10-K Item 7A: 4255 chars
          'Item 7A. Quantitative and Qualitative Disclosures about Market Risk Investment and Interest Rate Risk We are exposed to interest rate risk related to our fixed-rate investment portfolio and outstanding debt. The investment portfolio is managed consistent with our overall liquidity strategy in support of both working capital needs and growth of our businesses. According to our sensitivity analysis on our investment portfolio, a decrease in the yield curve of 0.5% as of the end of fiscal year 2026 and 2025 would decrease the fair value for these investments by approximately $0.2 billion. As of the end of fiscal year 2026, we had $8.5 billion of senior Notes outstanding. We carry the Notes at face value less unamortized discount on our Consolidated Balance Sheets. As the Notes bear interest at a fixed rate, we have no financial statement risk associated with changes in interest rates. Refer to Note 11 of the Notes to the Consolidated Financial Statements in Part IV, Item 15 of this Annual Report on Form 10-K for additional information. 44 Table of Contents Publicly-held equity securities are subject to market price volatility. A hypothetical 10% decrease in our publicly-held equity securities would decrease the fair value of the publicly-held equity securities balance by $1.8 billion and an insignificant amount as of January 25, 2026 and January 26, 2025, respectively. Non-marketable equity securities are measured based on cost minus impairment, if any, and are adjusted for observable price changes in orderly transactions for an identical or similar investment in the same issuer. Valuations of our non-marketable equity securities are inherently complex due to the lack of readily available market data and observable transactions, and impact of macroeconomic factors. For a description of our equity investments, refer to Notes 7 and 8 of the Notes to Condensed Consolidated Financial Statements in Part IV, Item 15 of this Annual Report on Form 10-K for additional information. Foreign Exchange Rate Risk We consider our direct exposure to foreign exchange rate fluctuations to be minimal as substantially all of our sales are in United States dollars and foreign currency forward contracts are used to offset movements of foreign currency exchange rates. Gains or losses from foreign currency remeasurement are included in other income or expenses. The impact of foreign currency transaction gain or loss included in determining net income was not significant for fiscal years 2026 and 2025. Sales and arrangements with third-party manufacturers provide for pricing and payment in United States dollars, and, therefore, are not subject to exchange rate fluctuations. Increases in the value of the United States’ dollar relative to other currencies would make our products more expensive, which could negatively impact our ability to compete. Conversely, decreases in the value of the United States’ dollar relative to other currencies could result in our suppliers raising their manufacturing costs. If the U.S. dollar strengthened by 10% as of January 25, 2026 and January 26, 2025, the amount recorded in Accumulated other comprehensive income (loss) related to our foreign exchange contracts before tax effect would have been an adverse impact of $180 million and $136 million, respectively. Change in value of our foreign exchange contracts recorded in Accumulated other comprehensive income (loss) would be expected to offset a corresponding change in hedged forecasted foreign currency expenses when recognized. If an adverse 10% foreign exchange rate change was applied to our balance sheet hedging contracts, it would have resulted in an adverse impact on income before taxes of $124 million and $129 million as of January 25, 2026 and January 26, 2025, respectively. These changes in fair values would be offset in Total other income, net, by corresponding change in fair values of the foreign currency denominated monetary assets and liabilities, assuming the hedge contracts fully cover the foreign currency denominated monetary assets and liabilities balances. Refer to Note 10 of the Notes to the Consolidated Financial Statements in Part IV, Item 15 of this Annual Report on Form 10-K for additional information.'
    NVDA  0001045810-26-000021 10-K Item 8: 206 chars
          'Item 8. Financial Statements and Supplementary Data The information required by this Item is set forth in our Consolidated Financial Statements and Notes thereto included in this Annual Report on Form 10-K.'
    PFE   0000078003-24-000039 10-K Item 7A: 289 chars
          'ITEM 7A. QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK The information required by this Item is incorporated by reference to the discussion in the Analysis of Financial Condition, Liquidity, Capital Resources and Market Risk section within MD&A. Pfizer Inc. 2023 Form 10-K 49'
    PFE   0000078003-25-000054 10-K Item 7A: 289 chars
          'ITEM 7A. QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK The information required by this Item is incorporated by reference to the discussion in the Analysis of Financial Condition, Liquidity, Capital Resources and Market Risk section within MD&A. Pfizer Inc. 2024 Form 10-K 48'
    PFE   0000078003-26-000026 10-K Item 7A: 289 chars
          'ITEM 7A. QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK The information required by this Item is incorporated by reference to the discussion in the Analysis of Financial Condition, Liquidity, Capital Resources and Market Risk section within MD&A. Pfizer Inc. 2025 Form 10-K 49'
    TGT   0000027419-24-000032 10-K Item 7A: 2746 chars
          "Item 7A. Quantitative and Qualitative Disclosures About Market Risk As of February 3, 2024, our exposure to market risk was primarily from interest rate changes on our debt obligations and short-term investments, some of which are at a Secured Overnight Financing Rate (SOFR). Our interest rate exposure is primarily due to differences between our floating rate debt obligations compared to our floating rate short-term investments. As of February 3, 2024, our floating rate short-term investments exceeded our floating rate debt by approximately $450 million. Based on our balance sheet position as of February 3, 2024, the annualized effect of a 1 percentage point increase in floating interest rates on our floating rate short-term investments, net of our floating rate debt obligations, would increase our earnings before income taxes by $5 million. In general, we expect our floating rate debt to exceed our floating rate short-term investments over time, but that may vary in different interest rate and economic environments. See further description of our debt and derivative instruments in Notes 16 and 17 to the Financial Statements. We record our general liability and workers' compensation liabilities at net present value; therefore, these liabilities fluctuate with changes in interest rates. Based on our balance sheet position as of February 3, 2024, the annualized effect of a 0.5 percentage point increase/(decrease) in interest rates would increase/(decrease) earnings before income taxes by $7 million. In addition, we are exposed to market return fluctuations on our qualified defined benefit pension plan. The value of our pension liabilities is inversely related to changes in interest rates. A 1 percentage point decrease in the weighted average discount rate would increase annual expense by $36 million. To protect against declines in interest rates, we hold high-quality, long-duration bonds and derivative instruments in our pension plan trust. As of February 3, 2024, we had hedged 70 percent of the interest rate exposure of our plan liabilities. As more fully described in Note 23 to the Financial Statements, we are exposed to market returns on accumulated team member balances in our nonqualified, unfunded deferred compensation plans. We control the risk of offering the nonqualified plans by making investments in life insurance contracts and prepaid forward contracts on our own common stock that substantially offset our economic exposure to the returns on these plans. There have been no other material changes in our primary risk exposures or management of market risks since the prior year. TARGET CORPORATION 2023 Form 10-K 35 FINANCIAL STATEMENTS Table of Contents INDEX Index to Financial Statements"
    TGT   0000027419-25-000018 10-K Item 7A: 2786 chars
          "Item 7A. Quantitative and Qualitative Disclosures About Market Risk As of February 1, 2025, our exposure to market risk was primarily from interest rate changes on our debt obligations and short-term investments. Our interest rate exposure is primarily due to differences between our floating rate debt obligations, including fixed rate debt hedged using floating rate interest rate swaps, compared to our floating rate short-term investments. As of February 1, 2025, our floating rate short-term investments exceeded our floating rate debt obligations by approximately $1.7 billion. Based on our financial position as of February 1, 2025, the annualized effect of a 1 percentage point increase in floating interest rates on our floating rate short-term investments, net of our floating rate debt obligations, would increase our earnings before income taxes by $17 million. In general, we expect our floating rate debt obligations to be in line with our floating rate short-term investments over time, but that may vary in different interest rate and economic environments. See further description of our debt and derivative instruments in Notes 15 and 16 to the Financial Statements. We record our general liability and workers' compensation liabilities at net present value; therefore, these liabilities fluctuate with changes in interest rates. Based on our balance sheet position as of February 1, 2025, the annualized effect of a 1 percentage point increase/(decrease) in interest rates would increase/(decrease) earnings before income taxes by $17 million. In addition, we are exposed to market return fluctuations on our qualified defined benefit pension plan. The value of our pension liabilities is inversely related to changes in interest rates. A 1 percentage point decrease in the weighted average discount rate would increase annual expense by $33 million. To protect against declines in interest rates, we hold high-quality, long-duration bonds and derivative instruments in our pension plan trust. As of February 1, 2025, we had hedged 70 percent of the interest rate exposure of our plan liabilities. As more fully described in Note 22 to the Financial Statements, we are exposed to market returns on accumulated team member balances in our nonqualified, unfunded deferred compensation plans. We control the risk of offering the nonqualified plans by making investments in life insurance contracts and prepaid forward contracts on our own common stock that substantially offset our economic exposure to the returns on these plans. There have been no other material changes in our primary risk exposures or management of market risks since the prior year. TARGET CORPORATION 2024 Form 10-K 37 FINANCIAL STATEMENTS Table of Contents INDEX Index to Financial Statements"
    TGT   0000027419-26-000016 10-K Item 7A: 2786 chars
          "Item 7A. Quantitative and Qualitative Disclosures About Market Risk As of January 31, 2026, our exposure to market risk was primarily from interest rate changes on our debt obligations and short-term investments. Our interest rate exposure is primarily due to differences between our floating rate debt obligations, including fixed rate debt hedged using floating rate interest rate swaps, compared to our floating rate short-term investments. As of January 31, 2026, our floating rate short-term investments exceeded our floating rate debt obligations by approximately $2.4 billion. Based on our financial position as of January 31, 2026, the annualized effect of a 1 percentage point increase in floating interest rates on our floating rate short-term investments, net of our floating rate debt obligations, would increase our earnings before income taxes by $24 million. In general, we expect our floating rate debt obligations to be in line with our floating rate short-term investments over time, but that may vary in different interest rate and economic environments. See further description of our debt and derivative instruments in Notes 17 and 18 to the Financial Statements. We record our general liability and workers' compensation liabilities at net present value; therefore, these liabilities fluctuate with changes in interest rates. Based on our balance sheet position as of January 31, 2026, the annualized effect of a 1 percentage point increase/(decrease) in interest rates would increase/(decrease) earnings before income taxes by $20 million. In addition, we are exposed to market return fluctuations on our qualified defined benefit pension plan. The value of our pension liabilities is inversely related to changes in interest rates. A 1 percentage point decrease in the weighted average discount rate would increase annual expense by $38 million. To protect against declines in interest rates, we hold high-quality, long-duration bonds and derivative instruments in our pension plan trust. As of January 31, 2026, we had hedged 75 percent of the interest rate exposure of our plan liabilities. As more fully described in Note 24 to the Financial Statements, we are exposed to market returns on accumulated team member balances in our nonqualified, unfunded deferred compensation plans. We control the risk of offering the nonqualified plans by making investments in life insurance contracts and prepaid forward contracts on our own common stock that substantially offset our economic exposure to the returns on these plans. There have been no other material changes in our primary risk exposures or management of market risks since the prior year. TARGET CORPORATION 2025 Form 10-K 40 FINANCIAL STATEMENTS Table of Contents INDEX Index to Financial Statements"
    XOM   0000034088-24-000018 10-K Item 7: 265 chars
          "ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS Reference is made to the section entitled “Management’s Discussion and Analysis of Financial Condition and Results of Operations” in the Financial Section of this report."
    XOM   0000034088-24-000018 10-K Item 7A: 409 chars
          'ITEM 7A. QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK Reference is made to the section entitled “Market Risks” in the Financial Section of this report. All statements, other than historical information incorporated in this Item 7A, are forward-looking statements. The actual impact of future market changes could differ materially due to, among other things, factors discussed in this report. 30'
    XOM   0000034088-24-000018 10-K Item 8: 733 chars
          'ITEM 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA Reference is made to the following in the Financial Section of this report: •Consolidated financial statements, together with the report thereon of PricewaterhouseCoopers LLP (PCAOB ID 238) dated February 28, 2024, beginning with the section entitled “Report of Independent Registered Public Accounting Firm” and continuing through “Note 21: Mergers and Acquisitions”; •“Supplemental Information on Oil and Gas Exploration and Production Activities” (unaudited); and •“Frequently Used Terms” (unaudited). Financial Statement Schedules have been omitted because they are not applicable or the required information is shown in the consolidated financial statements or notes thereto.'
    XOM   0000034088-25-000010 10-K Item 7: 264 chars
          "ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS Reference is made to the section entitled “Management’s Discussion and Analysis of Financial Condition and Results of Operations” in the Financial Section of this report."
    XOM   0000034088-25-000010 10-K Item 7A: 409 chars
          'ITEM 7A. QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK Reference is made to the section entitled “Market Risks” in the Financial Section of this report. All statements, other than historical information incorporated in this Item 7A, are forward-looking statements. The actual impact of future market changes could differ materially due to, among other things, factors discussed in this report. 27'
    XOM   0000034088-25-000010 10-K Item 8: 706 chars
          'ITEM 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA Reference is made to the following in the Financial Section of this report: • Consolidated financial statements, together with the report thereon of PricewaterhouseCoopers LLP (PCAOB ID 238) dated February 19, 2025, beginning with the section entitled “Report of Independent Registered Public Accounting Firm” and continuing through Note 21; •“Supplemental Information on Oil and Gas Exploration and Production Activities” (unaudited); and •“Frequently Used Terms” (unaudited). Financial Statement Schedules have been omitted because they are not applicable or the required information is shown in the consolidated financial statements or notes thereto.'
    XOM   0000034088-26-000045 10-K Item 7: 264 chars
          "ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS Reference is made to the section entitled “Management’s Discussion and Analysis of Financial Condition and Results of Operations” in the Financial Section of this report."
    XOM   0000034088-26-000045 10-K Item 7A: 456 chars
          'ITEM 7A. QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK Reference is made to the section entitled “Market Risks” in the Financial Section of this report. All statements, other than historical information incorporated in this Item 7A, are forward-looking statements. The actual impact of future market changes could differ materially due to, among other things, factors discussed in this report. 24 Table of Contents Financial Table of Contents'
    XOM   0000034088-26-000045 10-K Item 8: 706 chars
          'ITEM 8. FINANCIAL STATEMENTS AND SUPPLEMENTARY DATA Reference is made to the following in the Financial Section of this report: • Consolidated financial statements, together with the report thereon of PricewaterhouseCoopers LLP (PCAOB ID 238) dated February 18, 2026, beginning with the section entitled “Report of Independent Registered Public Accounting Firm” and continuing through Note 20; •“Supplemental Information on Oil and Gas Exploration and Production Activities” (unaudited); and •“Frequently Used Terms” (unaudited). Financial Statement Schedules have been omitted because they are not applicable or the required information is shown in the consolidated financial statements or notes thereto.'
    
    required Items measured: 264 on 96 filings
    must-not-be-stub Items (1, 1A, 7, I.1, I.2) between 500 and 5,000 chars: none
    must-not-be-stub Items at or below 1,000: [('JPM', '0000019617-24-000225', '7', 395), ('JPM', '0000019617-25-000270', '7', 395), ('JPM', '0001628280-26-008131', '7', 395), ('XOM', '0000034088-24-000018', '7', 265), ('XOM', '0000034088-25-000010', '7', 264), ('XOM', '0000034088-26-000045', '7', 264)]

No Item 1, 1A, 7, I.1 or I.2 lies between 500 and 5,000 chars, so
`stub_max_chars: 1000` (config comment rewritten). `min_required_item_chars` is
gone. `check` quarantines a must-not-be-stub Item at or below the bound; the
runner lists every filing's stub Items.

`python -m api.parse.validate` (`parser_version` d58d26e08e5a, unchanged --
`validate.py` is outside the parser hash):

    parser_version d58d26e08e5a
    ticker accession              form   FY fp sect miss data alpha scale uncol spans items score  rows skip  status
    AAPL   0000320193-23-000106   10-K 2023 FY   23    0   46 0.762 0.976 1.000 0.994 1.000 0.994   983    6  parsed
    AAPL   0000320193-24-000006   10-Q 2024 Q1   11    0   24 0.724 0.957 1.000 0.996 1.000 0.991   522    2  parsed
    AAPL   0000320193-24-000069   10-Q 2024 Q2   11    0   24 0.704 0.957 1.000 0.997 1.000 0.991   676    2  parsed
    AAPL   0000320193-24-000081   10-Q 2024 Q3   11    0   24 0.698 0.957 1.000 0.996 1.000 0.990   678    3  parsed
    AAPL   0000320193-24-000123   10-K 2024 FY   23    0   44 0.765 0.974 1.000 0.996 1.000 0.994   957    4  parsed
    AAPL   0000320193-25-000008   10-Q 2025 Q1   11    0   23 0.736 0.955 1.000 0.994 1.000 0.990   520    3  parsed
    AAPL   0000320193-25-000057   10-Q 2025 Q2   11    0   23 0.725 0.955 1.000 0.997 1.000 0.990   670    2  parsed
    AAPL   0000320193-25-000073   10-Q 2025 Q3   11    0   25 0.701 0.957 1.000 0.996 1.000 0.990   680    3  parsed
    AAPL   0000320193-25-000079   10-K 2025 FY   23    0   43 0.765 0.974 1.000 0.995 1.000 0.994   962    5  parsed
    AAPL   0000320193-26-000006   10-Q 2026 Q1   11    0   23 0.722 0.955 1.000 0.993 1.000 0.989   554    4  parsed
    AAPL   0000320193-26-000013   10-Q 2026 Q2   11    0   25 0.733 0.958 1.000 0.995 1.000 0.991   750    4  parsed
    AAPL   0000320193-26-000020   10-Q 2026 Q3   11    0   26 0.728 0.960 1.000 0.995 1.000 0.991   756    4  parsed
    BAC    0000070858-23-000272   10-Q 2023 Q3    9    0  129 0.689 1.000 0.992 0.999 1.000 0.998  6826   10  parsed
    BAC    0000070858-24-000122   10-K 2023 FY   23    0  159 0.748 1.000 0.969 0.997 1.000 0.993  7848   21  parsed  stubs: 7A
    BAC    0000070858-24-000156   10-Q 2024 Q1    9    0  119 0.701 1.000 0.992 0.998 1.000 0.998  5402    9  parsed
    BAC    0000070858-24-000208   10-Q 2024 Q2    9    0  127 0.683 1.000 0.992 0.999 1.000 0.998  6856    6  parsed
    BAC    0000070858-24-000280   10-Q 2024 Q3    9    0  126 0.685 1.000 0.992 0.999 1.000 0.998  6898    8  parsed
    BAC    0000070858-25-000139   10-K 2024 FY   23    0  158 0.746 1.000 0.975 0.998 1.000 0.994  7853   19  parsed  stubs: 7A
    BAC    0000070858-25-000200   10-Q 2025 Q1    9    0  118 0.701 1.000 1.000 0.999 1.000 1.000  5408    6  parsed
    BAC    0000070858-25-000268   10-Q 2025 Q2    9    0  123 0.685 1.000 0.992 0.999 1.000 0.998  6834    6  parsed
    BAC    0000070858-25-000405   10-Q 2025 Q3    9    0  122 0.686 1.000 0.992 0.999 1.000 0.998  6876    7  parsed
    BAC    0000070858-26-000157   10-K 2025 FY   23    0  157 0.746 1.000 0.968 0.998 1.000 0.993  7872   19  parsed  stubs: 7A
    BAC    0000070858-26-000249   10-Q 2026 Q1    9    0  117 0.700 1.000 1.000 0.999 1.000 1.000  5396    8  parsed
    BAC    0000070858-26-000394   10-Q 2026 Q2    9    0  123 0.681 1.000 0.992 0.999 1.000 0.998  6817    8  parsed
    COST   0000909832-23-000042   10-K 2023 FY   22    0   44 0.775 0.938 1.000 0.995 1.000 0.987   833    4  parsed
    COST   0000909832-23-000065   10-Q 2024 Q1   11    0   25 0.755 0.882 1.000 0.990 1.000 0.974   392    4  parsed
    COST   0000909832-24-000017   10-Q 2024 Q2   11    0   26 0.739 0.889 1.000 0.993 1.000 0.976   569    4  parsed
    COST   0000909832-24-000029   10-Q 2024 Q3   11    0   26 0.738 0.889 1.000 0.993 1.000 0.976   566    4  parsed
    COST   0000909832-24-000049   10-K 2024 FY   23    0   44 0.776 0.938 1.000 0.995 1.000 0.987   837    4  parsed
    COST   0000909832-24-000079   10-Q 2025 Q1   11    0   25 0.758 0.882 1.000 0.989 1.000 0.974   357    4  parsed
    COST   0000909832-25-000015   10-Q 2025 Q2   11    0   26 0.743 0.889 1.000 0.992 1.000 0.976   495    4  parsed
    COST   0000909832-25-000033   10-Q 2025 Q3   11    0   26 0.740 0.889 1.000 0.992 1.000 0.976   490    4  parsed
    COST   0000909832-25-000101   10-K 2025 FY   23    0   44 0.779 0.938 1.000 0.994 1.000 0.986   818    5  parsed
    COST   0000909832-25-000169   10-Q 2026 Q1   11    0   27 0.756 0.895 1.000 0.988 1.000 0.976   395    5  parsed
    COST   0000909832-26-000029   10-Q 2026 Q2   11    0   28 0.738 0.900 1.000 0.991 1.000 0.978   571    5  parsed
    COST   0000909832-26-000051   10-Q 2026 Q3   11    0   28 0.737 0.900 1.000 0.991 1.000 0.978   570    5  parsed
    JPM    0000019617-23-000524   10-Q 2023 Q3   11    0  243 0.701 1.000 0.984 0.995 1.000 0.996  7819   36  parsed
    JPM    0000019617-24-000225   10-K 2023 FY   22    0  268 0.754 1.000 0.993 0.997 1.000 0.998     0   27  quarantined: required Item is a cross-reference stub: Item 7 is 395 chars <= 1000  stubs: 7,7A,8
    JPM    0000019617-24-000326   10-Q 2024 Q1   11    0  218 0.716 1.000 1.000 0.994 1.000 0.999  5755   33  parsed
    JPM    0000019617-24-000453   10-Q 2024 Q2   11    0  232 0.700 1.000 0.983 0.996 1.000 0.996  7386   31  parsed
    JPM    0000019617-24-000611   10-Q 2024 Q3   11    0  232 0.701 1.000 0.983 0.995 1.000 0.996  7373   37  parsed
    JPM    0000019617-25-000270   10-K 2024 FY   22    0  267 0.755 1.000 0.993 0.996 1.000 0.998     0   34  quarantined: required Item is a cross-reference stub: Item 7 is 395 chars <= 1000  stubs: 7,7A,8
    JPM    0000019617-25-000421   10-Q 2025 Q1   11    0  219 0.713 1.000 1.000 0.997 1.000 0.999  5717   20  parsed
    JPM    0000019617-25-000615   10-Q 2025 Q2   11    0  234 0.694 1.000 0.983 0.996 1.000 0.996  7338   27  parsed
    JPM    0001628280-25-048859   10-Q 2025 Q3   11    0  233 0.697 1.000 0.983 0.996 1.000 0.996  7354   33  parsed
    JPM    0001628280-26-008131   10-K 2025 FY   22    0  272 0.752 1.000 0.993 0.995 1.000 0.998     0   38  quarantined: required Item is a cross-reference stub: Item 7 is 395 chars <= 1000  stubs: 7,7A,8
    JPM    0001628280-26-029344   10-Q 2026 Q1   11    0  219 0.714 1.000 1.000 0.997 1.000 0.999  5650   16  parsed
    JPM    0001628280-26-054343   10-Q 2026 Q2   11    0  228 0.695 1.000 0.982 0.997 1.000 0.996  7351   20  parsed
    NVDA   0001045810-23-000227   10-Q 2024 Q3    9    0   41 0.762 1.000 1.000 0.998 1.000 1.000   964    2  parsed
    NVDA   0001045810-24-000029   10-K 2024 FY   23    0   53 0.790 1.000 1.000 0.993 1.000 0.999  1207    9  parsed  stubs: 8
    NVDA   0001045810-24-000124   10-Q 2025 Q1    9    0   43 0.766 1.000 1.000 0.993 1.000 0.999   746    5  parsed
    NVDA   0001045810-24-000264   10-Q 2025 Q2    9    0   45 0.755 1.000 1.000 0.995 1.000 0.999   988    5  parsed
    NVDA   0001045810-24-000316   10-Q 2025 Q3    9    0   44 0.754 1.000 1.000 0.996 1.000 0.999   984    4  parsed
    NVDA   0001045810-25-000023   10-K 2025 FY   23    0   56 0.789 1.000 1.000 0.993 1.000 0.999  1220    9  parsed  stubs: 8
    NVDA   0001045810-25-000116   10-Q 2026 Q1    9    0   40 0.768 1.000 1.000 0.994 1.000 0.999   721    4  parsed
    NVDA   0001045810-25-000209   10-Q 2026 Q2    9    0   39 0.752 1.000 1.000 0.994 1.000 0.999   940    6  parsed
    NVDA   0001045810-25-000230   10-Q 2026 Q3    9    0   38 0.761 1.000 1.000 0.992 1.000 0.998   943    8  parsed
    NVDA   0001045810-26-000021   10-K 2026 FY   23    0   49 0.790 1.000 1.000 0.991 1.000 0.998  1117   10  parsed  stubs: 8
    NVDA   0001045810-26-000052   10-Q 2027 Q1    9    0   37 0.769 1.000 1.000 0.994 1.000 0.999   699    4  parsed
    NVDA   0001045810-26-000075   10-Q 2027 Q2    9    0   41 0.753 1.000 1.000 0.996 1.000 0.999   996    4  parsed
    PFE    0000078003-23-000115   10-Q 2023 Q3    9    0   46 0.760 1.000 1.000 0.989 1.000 0.998  1856   20  parsed
    PFE    0000078003-24-000039   10-K 2023 FY   20    0   78 0.784 1.000 1.000 0.988 1.000 0.998  2979   37  parsed  stubs: 7A
    PFE    0000078003-24-000107   10-Q 2024 Q1    9    0   44 0.773 1.000 1.000 0.982 1.000 0.996  1194   22  parsed
    PFE    0000078003-24-000166   10-Q 2024 Q2    9    0   50 0.758 1.000 1.000 0.988 1.000 0.998  1775   22  parsed
    PFE    0000078003-24-000191   10-Q 2024 Q3    9    0   50 0.758 1.000 1.000 0.985 1.000 0.997  1797   27  parsed
    PFE    0000078003-25-000054   10-K 2024 FY   20    0   86 0.783 1.000 1.000 0.984 1.000 0.997  2905   47  parsed  stubs: 7A
    PFE    0000078003-25-000114   10-Q 2025 Q1    9    0   41 0.774 1.000 1.000 0.974 1.000 0.995  1112   30  parsed
    PFE    0000078003-25-000138   10-Q 2025 Q2    9    0   50 0.757 1.000 1.000 0.984 1.000 0.997  1662   27  parsed
    PFE    0000078003-25-000150   10-Q 2025 Q3    9    0   50 0.760 1.000 1.000 0.986 1.000 0.997  1724   24  parsed
    PFE    0000078003-26-000026   10-K 2025 FY   20    0   82 0.785 1.000 1.000 0.986 1.000 0.997  2911   40  parsed  stubs: 7A
    PFE    0000078003-26-000054   10-Q 2026 Q1    9    0   40 0.773 1.000 1.000 0.984 1.000 0.997  1207   20  parsed
    PFE    0000078003-26-000095   10-Q 2026 Q2    9    0   48 0.757 1.000 1.000 0.989 1.000 0.998  1789   20  parsed
    TGT    0000027419-23-000052   10-Q 2023 Q3   11    0   29 0.716 1.000 1.000 0.980 1.000 0.996   553   11  parsed
    TGT    0000027419-24-000032   10-K 2023 FY   23    0   60 0.768 0.977 1.000 0.986 1.000 0.993   984   14  parsed
    TGT    0000027419-24-000129   10-Q 2024 Q1   11    0   28 0.730 1.000 1.000 0.982 1.000 0.996   385    7  parsed
    TGT    0000027419-24-000152   10-Q 2024 Q2   11    0   30 0.710 1.000 1.000 0.985 1.000 0.997   517    8  parsed
    TGT    0000027419-24-000179   10-Q 2024 Q3   11    0   30 0.711 1.000 1.000 0.982 1.000 0.996   532   10  parsed
    TGT    0000027419-25-000018   10-K 2024 FY   23    0   62 0.773 1.000 1.000 0.988 1.000 0.998   973   12  parsed
    TGT    0000027419-25-000101   10-Q 2025 Q1   11    0   30 0.734 1.000 1.000 0.981 1.000 0.996   406    8  parsed
    TGT    0000027419-25-000118   10-Q 2025 Q2   11    0   33 0.718 1.000 1.000 0.986 1.000 0.997   546    8  parsed
    TGT    0000027419-25-000126   10-Q 2025 Q3   11    0   34 0.720 1.000 1.000 0.983 1.000 0.997   576   10  parsed
    TGT    0000027419-26-000016   10-K 2025 FY   23    0   64 0.774 1.000 1.000 0.987 1.000 0.997   977   13  parsed
    TGT    0000027419-26-000022   10-Q 2026 Q1   11    0   30 0.736 1.000 1.000 0.980 1.000 0.996   401    8  parsed
    TGT    0000027419-26-000042   10-Q 2026 Q2   11    0   32 0.720 1.000 1.000 0.979 1.000 0.996   547   12  parsed
    XOM    0000034088-23-000056   10-Q 2023 Q3    8    0   36 0.715 1.000 1.000 1.000 1.000 1.000   883    0  parsed
    XOM    0000034088-24-000018   10-K 2023 FY   22    0  113 0.738 1.000 0.982 1.000 1.000 0.996     0    1  quarantined: required Item is a cross-reference stub: Item 7 is 265 chars <= 1000  stubs: 7,7A,8
    XOM    0000034088-24-000029   10-Q 2024 Q1    8    0   35 0.740 1.000 1.000 1.000 1.000 1.000   550    0  parsed
    XOM    0000034088-24-000050   10-Q 2024 Q2    8    0   40 0.715 1.000 1.000 1.000 1.000 1.000   915    0  parsed
    XOM    0000034088-24-000068   10-Q 2024 Q3    8    0   40 0.714 1.000 1.000 1.000 1.000 1.000   917    0  parsed
    XOM    0000034088-25-000010   10-K 2024 FY   22    0  118 0.739 1.000 0.958 1.000 1.000 0.991     0    1  quarantined: required Item is a cross-reference stub: Item 7 is 264 chars <= 1000  stubs: 7,7A,8
    XOM    0000034088-25-000024   10-Q 2025 Q1    8    0   38 0.730 1.000 0.947 1.000 1.000 0.989   903    0  parsed
    XOM    0000034088-25-000042   10-Q 2025 Q2    8    0   44 0.695 1.000 0.909 1.000 1.000 0.982  1533    0  parsed
    XOM    0000034088-25-000061   10-Q 2025 Q3    8    0   44 0.697 1.000 0.909 1.000 1.000 0.982  1526    0  parsed
    XOM    0000034088-26-000045   10-K 2025 FY   22    0  116 0.739 1.000 0.983 0.999 1.000 0.996     0    2  quarantined: required Item is a cross-reference stub: Item 7 is 264 chars <= 1000  stubs: 7,7A,8
    XOM    0000034088-26-000067   10-Q 2026 Q1    9    0   34 0.732 1.000 0.941 0.999 1.000 0.988   851    1  parsed
    XOM    0000034088-26-000093   10-Q 2026 Q2    9    0   36 0.703 1.000 0.889 0.999 1.000 0.978  1467    2  parsed

90 parsed, 6 quarantined: JPM x3 and XOM x3, on Item 7 alone -- the fixed
expected result. Stub listings: BAC and PFE 10-Ks `7A`, NVDA 10-Ks `8`, JPM and
XOM 10-Ks `7,7A,8`.

`python -m api.chunk.store` and the chunk diff:

    previously chunked filings: 84 | whose chunks changed: none
    newly chunked: 6 ['0000070858-24-000122', '0000070858-25-000139', '0000070858-26-000157', '0000078003-24-000039', '0000078003-25-000054', '0000078003-26-000026'] chunks: {'0000070858-24-000122': 739, '0000070858-25-000139': 722, '0000070858-26-000157': 731, '0000078003-24-000039': 464, '0000078003-25-000054': 451, '0000078003-26-000026': 459}

`make test`: 246 passed, 3 snapshots passed.

## 2026-10-01 — Phase 1 exit inspection of the six admitted 10-Ks; corpus frozen

Stub check committed as `33ae09d`. Embed after admitting the six: checks passed
on 22,354 chunks, 3,566 embedded, 18,788 from cache, 0 without an embedding.
Resolve: 209,500 of 209,608 (0.999; 1.000 within Items); the six resolve 1.000
within Items; PFE's three 10-Ks have 16-23 spans in split paragraphs.

**Inspection** -- sections with lengths, where the cross-referenced market-risk
section sits, statements under Item 8, sample tables, spans, chunk sizes,
resolve:

    === BAC 0000070858-24-000122
      sections: I.1=39555, I.1A=116434, I.1B=39, I.1C=146, I.2=1714, I.3=191, I.4=89, II.5=2795, II.6=37, II.7=302403, II.7A=217, II.8=391853, II.9=97, II.9A=1455, II.9B=2387, II.9C=146, III.10=5805, III.11=366, III.12=1433, III.13=302, III.14=339, IV.15=16856, IV
      Item 7 [169538:471941]; Item 7A stub: 'Item 7A. Quantitative and Qualitative Disclosures about Market Risk See Market Risk Management on page 73 in the MD&A and the sections referenced ther'
        market-risk heading @397512: 'Market Risk Management' -> inside Item 7
        market-risk heading @472010: 'See Market Risk Management on page 73 in the MD&A and the sections referenced th' -> inside II.7A
      Item 8 [472160:864013] (391853 chars); statement tables:
        'Consolidated Statement of Income' @489478 -> II.8; scale=millions (caption); header=['2023', '2022', '2021']
        'Consolidated Balance Sheet' @491605 -> II.8; scale=millions (caption); header=['', 'December 31 2023', 'December 31 2022']
        'Consolidated Statement of Cash Flows' @497901 -> II.8; scale=millions (caption); header=['2023', '2022', '2021']
        sample table 'Diversity Metrics as of December 31, 2023' -> I.1; scale=None (None); header=['', 'Total Employees', 'Top Three Management Levels', 'Managers at All Levels']; row1=['Global employees', '', '']
        sample table None -> II.5; scale=millions (caption); header=['', 'Total Common Shares Purchased (1,2)', 'Weighted-Average Per Share Price', 'Total Shares Purchased as Part of Publicly Announced Programs (2)']; row1=['October 1 - 31, 2023', '10,251', '$26.8
      spans 7848, mismatches 0; chunks 739, max tokens 500, over 512 0; resolved 7846/7848 (1.000)
    === BAC 0000070858-25-000139
      sections: I.1=37553, I.1A=116995, I.1B=39, I.1C=146, I.2=1714, I.3=191, I.4=108, II.5=2392, II.6=37, II.7=292585, II.7A=217, II.8=385743, II.9=97, II.9A=1455, II.9B=2539, II.9C=146, III.10=6045, III.11=366, III.12=1433, III.13=302, III.14=339, IV.15=17148, I
      Item 7 [167714:460299]; Item 7A stub: 'Item 7A. Quantitative and Qualitative Disclosures about Market Risk See Market Risk Management on page 74 in the MD&A and the sections referenced ther'
        market-risk heading @389301: 'Market Risk Management' -> inside Item 7
        market-risk heading @460368: 'See Market Risk Management on page 74 in the MD&A and the sections referenced th' -> inside II.7A
      Item 8 [460518:846261] (385743 chars); statement tables:
        'Consolidated Statement of Income' @477837 -> II.8; scale=millions (caption); header=['2024', '2023', '2022']
        'Consolidated Balance Sheet' @479957 -> II.8; scale=millions (caption); header=['', 'December 31 December 31 2024', 'December 31 December 31 2023']
        'Consolidated Statement of Cash Flows' @486242 -> II.8; scale=millions (caption); header=['2024', '2023', '2022']
        sample table 'Workforce data as of December 31, 2024' -> I.1; scale=None (None); header=['', 'Total Employees', 'Top Three Management Levels', 'Managers at All Levels']; row1=['Global employees', '', '']
        sample table None -> II.5; scale=millions (caption); header=['', 'Total Common Shares Purchased (1,2)', 'Weighted-Average Per Share Price', 'Total Shares Purchased as Part of Publicly Announced Programs (2)']; row1=['October 1 - 31, 2024', '22,058', '$42.8
      spans 7853, mismatches 0; chunks 722, max tokens 500, over 512 0; resolved 7851/7853 (1.000)
    === BAC 0000070858-26-000157
      sections: I.1=37968, I.1A=116929, I.1B=39, I.1C=146, I.2=1714, I.3=191, I.4=108, II.5=2482, II.6=37, II.7=294340, II.7A=217, II.8=385688, II.9=97, II.9A=1455, II.9B=2420, II.9C=146, III.10=5370, III.11=366, III.12=1433, III.13=302, III.14=339, IV.15=17751, I
      Item 7 [168153:462493]; Item 7A stub: 'Item 7A. Quantitative and Qualitative Disclosures about Market Risk See Market Risk Management on page 75 in the MD&A and the sections referenced ther'
        market-risk heading @394089: 'Market Risk Management' -> inside Item 7
        market-risk heading @462562: 'See Market Risk Management on page 75 in the MD&A and the sections referenced th' -> inside II.7A
      Item 8 [462712:848400] (385688 chars); statement tables:
        'Consolidated Statement of Income' @477575 -> II.8; scale=millions (caption); header=['2025', '2024', '2023']
        'Consolidated Balance Sheet' @479673 -> II.8; scale=millions (caption); header=['', 'December 31 2025', 'December 31 2024']
        'Consolidated Statement of Cash Flows' @485975 -> II.8; scale=millions (caption); header=['2025', '2024', '2023']
        sample table 'Workforce data as of December 31, 2025' -> I.1; scale=None (None); header=['', 'Total Employees', 'Top Three Management Levels', 'Managers at All Levels']; row1=['Global employees', '', '']
        sample table None -> II.5; scale=millions (caption); header=['', 'Total Common Shares Purchased (1,2)', 'Weighted-Average Per Share Price', 'Total Shares Purchased as Part of Publicly Announced Programs (2)']; row1=['October 1 - 31, 2025', '30,775', '$52.2
      spans 7872, mismatches 0; chunks 731, max tokens 500, over 512 0; resolved 7870/7872 (1.000)
    === PFE 0000078003-24-000039
      sections: I.1=92316, I.1A=83042, I.1C=6697, I.2=1429, I.3=5523, II.5=2102, II.6=49, II.7=100731, II.7A=289, II.8=293582, II.9=98, II.9A=9972, II.9B=273, III.10=1491, III.11=397, III.12=334, III.13=581, III.14=883, IV.15=19748, IV.16=2156
      Item 7 [228051:328782]; Item 7A stub: 'ITEM 7A. QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK The information required by this Item is incorporated by reference to the discussi'
        market-risk heading @328851: 'The information required by this Item is incorporated by reference to the discus' -> inside II.7A
      Item 8 [329073:622655] (293582 chars); statement tables:
        'The following provides: (i) an analysis of the changes in ou' @513530 -> II.8; scale=millions (caption); header=['Pension Plans U.S. Year Ended December 31, 2023', 'Pension Plans U.S. Year Ended December 31, 2022', 'Pension Plans International Year Ended 
        'For operating leases, the ROU assets and liabilities in our ' @544326 -> II.8; scale=millions (caption); header=['Balance Sheet Classification', 'As of December 31, 2023', 'As of December 31, 2022']
        sample table 'Product Inlyta Xeljanz' -> I.1; scale=None (None); header=['Product Inlyta Xeljanz', 'U.S. Basic Product Patent Expiration Year(1) 2025 2025', 'Major Europe Basic Product Patent Expiration Year(1) 2025 2028(2)', 'Japan Basic Product Patent Ex
        sample table 'Period' -> II.5; scale=None (None); header=['Period', 'Total Number of Shares Purchased(b)', 'Average Price Paid per Share(b)', 'Total Number of Shares Purchased as Part of Publicly Announced Plan']; row1=['October 2 through October 29, 2023'
      spans 2979, mismatches 0; chunks 464, max tokens 500, over 512 0; resolved 2977/2979 (0.999)
    === PFE 0000078003-25-000054
      sections: I.1=88408, I.1A=78992, I.1C=6991, I.2=1594, I.3=5164, II.5=2103, II.6=49, II.7=105158, II.7A=289, II.8=284850, II.9=98, II.9A=8637, II.9B=273, III.10=1607, III.11=397, III.12=334, III.13=581, III.14=883, IV.15=19512, IV.16=2297
      Item 7 [220848:326006]; Item 7A stub: 'ITEM 7A. QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK The information required by this Item is incorporated by reference to the discussi'
        market-risk heading @326075: 'The information required by this Item is incorporated by reference to the discus' -> inside II.7A
      Item 8 [326297:611147] (284850 chars); statement tables:
        'ANALYSIS OF THE CONSOLIDATED STATEMENTS OF CASH FLOWS' @313383 -> II.7; scale=millions (caption); header=['Year Ended December 31, 2024', 'Year Ended December 31, 2023', 'Year Ended December 31, 2022']
        'The following provides: (i) an analysis of the changes in ou' @499141 -> II.8; scale=millions (caption); header=['Pension Plans U.S. Year Ended December 31, 2024', 'Pension Plans U.S. Year Ended December 31, 2023', 'Pension Plans International Year Ended 
        'For operating leases, the ROU assets and liabilities in our ' @529727 -> II.8; scale=millions (caption); header=['Balance Sheet Classification', 'As of December 31, 2024', 'As of December 31, 2023']
        sample table 'Product Inlyta Xeljanz' -> I.1; scale=None (None); header=['Product Inlyta Xeljanz', 'U.S. Basic Product Patent Expiration Year(1) 2025 2026', 'Major Europe Basic Product Patent Expiration Year(1) 2025 2028(2)', 'Japan Basic Product Patent Ex
        sample table None -> I.1; scale=None (None); header=['']; row1=['Product U.S. Basic Product Patent Expiration Year(1) Major Europe Basic Product Patent Expiration Year(1) Japan Basic Product Patent Expiration Year(1)']
      spans 2905, mismatches 0; chunks 451, max tokens 500, over 512 0; resolved 2903/2905 (0.999)
    === PFE 0000078003-26-000026
      sections: I.1=91826, I.1A=87396, I.1C=6997, I.2=1616, I.3=4811, II.5=2102, II.6=49, II.7=105392, II.7A=289, II.8=262601, II.9=130, II.9A=8629, II.9B=273, III.10=1607, III.11=397, III.12=334, III.13=581, III.14=883, IV.15=18700, IV.16=2236
      Item 7 [235820:341212]; Item 7A stub: 'ITEM 7A. QUANTITATIVE AND QUALITATIVE DISCLOSURES ABOUT MARKET RISK The information required by this Item is incorporated by reference to the discussi'
        market-risk heading @341281: 'The information required by this Item is incorporated by reference to the discus' -> inside II.7A
      Item 8 [341503:604104] (262601 chars); statement tables:
        'ANALYSIS OF THE CONSOLIDATED STATEMENTS OF CASH FLOWS' @328028 -> II.7; scale=millions (caption); header=['Year Ended December 31, 2025', 'Year Ended December 31, 2024', 'Year Ended December 31, 2023']
        'The following provides: (i) an analysis of the changes in ou' @505071 -> II.8; scale=millions (caption); header=['Pension Plans U.S. Year Ended December 31, 2025', 'Pension Plans U.S. Year Ended December 31, 2024', 'Pension Plans International Year Ended 
        'For operating leases, the ROU assets and liabilities in our ' @534037 -> II.8; scale=millions (caption); header=['Balance Sheet Classification', 'As of December 31, 2025', 'As of December 31, 2024']
        sample table 'Product Xeljanz' -> I.1; scale=None (None); header=['Product Xeljanz', 'U.S. Basic Product Patent Expiration Year(1) 2026', 'Major Europe Basic Product Patent Expiration Year(1) 2028(2)', 'Japan Basic Product Patent Expiration Year(1) 2025'];
        sample table 'Product' -> I.1; scale=None (None); header=['Product', 'U.S. Basic Product Patent Expiration Year(1)', 'Major Europe Basic Product Patent Expiration Year(1)', 'Japan Basic Product Patent Expiration Year(1)']; row1=['Braftovi(11)', '2030 (2031
      spans 2911, mismatches 0; chunks 459, max tokens 500, over 512 0; resolved 2909/2911 (0.999)

PFE's market-risk section and statement titles, found by their exact headings
(the first pass searched "Market Risk" and "Statements of Income", which PFE
words differently):

    === PFE 0000078003-24-000039
      heading 'ANALYSIS OF FINANCIAL CONDITION, LIQUIDITY, CAPITAL RESOURCES AND MARKET RISK' @316575 -> II.7
      'Consolidated Statements of Income' heading @342302 -> II.8; next data table @342373 -> II.8, scale=millions (caption), header=['Year Ended December 31, 2023', 'Year Ended December 31, 2022', 'Year Ended December 31, 2021'], row
      'Consolidated Balance Sheets' heading @346018 -> II.8; next data table @346083 -> II.8, scale=millions (caption), header=['As of December 31, 2023', 'As of December 31, 2022'], row1=['Assets', '', '']
      'Consolidated Statements of Cash Flows' heading @349991 -> II.8; next data table @350066 -> II.8, scale=millions (caption), header=['Year Ended December 31, 2023', 'Year Ended December 31, 2022', 'Year Ended December 31, 2021'],
    === PFE 0000078003-25-000054
      heading 'ANALYSIS OF FINANCIAL CONDITION, LIQUIDITY, CAPITAL RESOURCES AND MARKET RISK' @314487 -> II.7
      'Consolidated Balance Sheets' heading @343829 -> II.8; next data table @343894 -> II.8, scale=millions (caption), header=['As of December 31, 2024', 'As of December 31, 2023'], row1=['Assets', '', '']
      'Consolidated Statements of Cash Flows' heading @347641 -> II.8; next data table @347716 -> II.8, scale=millions (caption), header=['Year Ended December 31, 2024', 'Year Ended December 31, 2023', 'Year Ended December 31, 2022'],
    === PFE 0000078003-26-000026
      heading 'ANALYSIS OF FINANCIAL CONDITION, LIQUIDITY, CAPITAL RESOURCES AND MARKET RISK' @329151 -> II.7
      'Consolidated Balance Sheets' heading @355118 -> II.8; next data table @355183 -> II.8, scale=millions (caption), header=['As of December 31, 2025', 'As of December 31, 2024'], row1=['Assets', '', '']
      'Consolidated Statements of Cash Flows' heading @358824 -> II.8; next data table @358899 -> II.8, scale=millions (caption), header=['Year Ended December 31, 2025', 'Year Ended December 31, 2024', 'Year Ended December 31, 2023'],
    === PFE 0000078003-25-000054: Item 8 headings starting 'Consolidated Statement(s) of' in its first 30,000 chars:
      'Consolidated Statements of Operations' @340121 (II.8); next table scale=millions (caption) header=['Year Ended December 31, 2024', 'Year Ended December 31, 2023'] row1=['Revenues:', '']
      'Consolidated Statements of Comprehensive Income' @342143 (II.8); next table scale=millions (caption) header=['Year Ended December 31, 2024', 'Year Ended December 31, 2023'] row1=['Net income before allocation to noncontrolling 
      'Consolidated Statements of Equity' @345852 (II.8); next table scale=millions (caption) header=['PFIZER INC. SHAREHOLDERS Common Stock Shares', 'PFIZER INC. SHAREHOLDERS Common Stock Par Value'] row1=['Balance, January 1, 2022',
      'Consolidated Statements of Cash Flows' @347641 (II.8); next table scale=millions (caption) header=['Year Ended December 31, 2024', 'Year Ended December 31, 2023'] row1=['Operating Activities', '']
      'Consolidated Statements of Cash Flows' @350883 (II.8); next table scale=millions (ixbrl) header=['Year Ended December 31, 2024', 'Year Ended December 31, 2023'] row1=['Supplemental Cash Flow Information', '']
    === PFE 0000078003-26-000026: Item 8 headings starting 'Consolidated Statement(s) of' in its first 30,000 chars:
      'Consolidated Statements of Operations' @351449 (II.8); next table scale=millions (caption) header=['Year Ended December 31, 2025', 'Year Ended December 31, 2024'] row1=['Revenues:', '']
      'Consolidated Statements of Comprehensive Income' @353452 (II.8); next table scale=millions (caption) header=['Year Ended December 31, 2025', 'Year Ended December 31, 2024'] row1=['Net income before allocation to noncontrolling 
      'Consolidated Statements of Equity' @357102 (II.8); next table scale=millions (caption) header=['PFIZER INC. SHAREHOLDERS Common Stock Shares', 'PFIZER INC. SHAREHOLDERS Common Stock Par Value'] row1=['Balance, January 1, 2023',
      'Consolidated Statements of Cash Flows' @358824 (II.8); next table scale=millions (caption) header=['Year Ended December 31, 2025', 'Year Ended December 31, 2024'] row1=['Operating Activities', '']
      'Consolidated Statements of Cash Flows' @361956 (II.8); next table scale=millions (ixbrl) header=['Year Ended December 31, 2025', 'Year Ended December 31, 2024'] row1=['Supplemental Cash Flow Information', '']

All six pass: the market-risk section each 7A points to is inside Item 7 (BAC
"Market Risk Management"; PFE "Analysis of Financial Condition, Liquidity,
Capital Resources and Market Risk"); every primary statement is under Item 8
with scale and period headers; 0 span mismatches; 0 chunks over 512, max 500.

**F-70, where XOM's Financial Section lands:**

    === XOM 0000034088-24-000018: text 415479 chars; last sections: [('III.14', 276), ('IV.15', 205), ('IV.16', 302621)]
      'MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULT' @244307 -> IV.16 (302621 chars)
      'MARKET RISKS' @220556 -> IV.16 (302621 chars)
      'REPORT OF INDEPENDENT REGISTERED PUBLIC ACCOUNTING FIRM' @257893 -> IV.16 (302621 chars)
      'CONSOLIDATED STATEMENT OF INCOME' @261942 -> IV.16 (302621 chars)
    === XOM 0000034088-25-000010: text 440229 chars; last sections: [('III.14', 276), ('IV.15', 205), ('IV.16', 324704)]
      'MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULT' @256051 -> IV.16 (324704 chars)
      'MARKET RISKS' @227388 -> IV.16 (324704 chars)
      'REPORT OF INDEPENDENT REGISTERED PUBLIC ACCOUNTING FIRM' @272952 -> IV.16 (324704 chars)
      'CONSOLIDATED STATEMENT OF INCOME' @274426 -> IV.16 (324704 chars)
    === XOM 0000034088-26-000045: text 420541 chars; last sections: [('III.14', 276), ('IV.15', 205), ('IV.16', 317816)]
      'MANAGEMENT’S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULT' @239059 -> IV.16 (317816 chars)
      'MARKET RISKS' @213909 -> IV.16 (317816 chars)
      'REPORT OF INDEPENDENT REGISTERED PUBLIC ACCOUNTING FIRM' @251495 -> IV.16 (317816 chars)
      'CONSOLIDATED STATEMENT OF INCOME' @255988 -> IV.16 (317816 chars)

**Freeze.** `python -m scripts.write_freeze` -> `api/corpus_freeze.yaml`:

    {'frozen_on': '2026-10-01', 'corpus_as_of': '2026-10-01', 'parser_version': 'd58d26e08e5a', 'chunker_version': '964f77f6f9cb', 'totals': {'listed': 96, 'parsed': 90, 'quarantined': 6}}
      COST  10-K parsed 3 quarantined 0 | 10-Q parsed 9 quarantined 0
      TGT   10-K parsed 3 quarantined 0 | 10-Q parsed 9 quarantined 0
      JPM   10-K parsed 0 quarantined 3 | 10-Q parsed 9 quarantined 0
      BAC   10-K parsed 3 quarantined 0 | 10-Q parsed 9 quarantined 0
      AAPL  10-K parsed 3 quarantined 0 | 10-Q parsed 9 quarantined 0
      NVDA  10-K parsed 3 quarantined 0 | 10-Q parsed 9 quarantined 0
      XOM   10-K parsed 0 quarantined 3 | 10-Q parsed 9 quarantined 0
      PFE   10-K parsed 3 quarantined 0 | 10-Q parsed 9 quarantined 0
    [('0000019617-24-000225', 'F-66'), ('0000019617-25-000270', 'F-66'), ('0001628280-26-008131', 'F-66'), ('0000034088-24-000018', 'F-70'), ('0000034088-25-000010', 'F-70'), ('0000034088-26-000045', 'F-70')]

`python -m scripts.verify_freeze`: `verified 96 frozen accessions; mismatches 0`,
exit 0. With one frozen hash altered (file backed up and restored byte for
byte): `MISMATCH 0000909832-23-000042 ...`, `mismatches 1`, exit 1.

**Retrieval half of the baseline on the frozen corpus:**

    question: How does Bank of America describe its market risk management in its annual report?
    plan: ->  Index Scan using chunks_hnsw on chunks  (cost=1181.91..81867.08 rows=22354 width=407)
      0.2050  0000070858-25-000200:532.0:542.0  [Bank of America Corporation (BAC) | 10-Q | Q1 FY2025 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations]
      0.2053  0000070858-26-000249:525.0:535.0  [Bank of America Corporation (BAC) | 10-Q | Q1 FY2026 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations]
      0.2069  0000070858-24-000156:546.0:556.0  [Bank of America Corporation (BAC) | 10-Q | Q1 FY2024 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations]
      0.2097  0000070858-26-000157:1011.0:1018.0  [Bank of America Corporation (BAC) | 10-K | FY2025 | Item 7: Bank of America Corporation and Subsidiaries Management's Discussion and Analysis of Financial Condition and Results of Operations Table of Contents]
      0.2105  0000070858-24-000208:585.0:592.0  [Bank of America Corporation (BAC) | 10-Q | Q2 FY2024 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations]

The fourth result is BAC's FY2025 10-K, Item 7 (`II.7`). Its context header ends
"Table of Contents" -- a non-link cell in BAC's heading table kept in the section
title (F-71). Generation stays F-59.

## 2026-10-01 — Phase 2 close-out: F-71 scope, freeze notes, chunker check in the verifier

Freeze committed as `a21ab6c`.

**F-71 scope** -- every stored chunk of the 90 whose `section_title` contains
"Table of Contents":

     ticker |      accession       | form_type | item_code | chunks |                                                                    section_title                                                                     
    --------+----------------------+-----------+-----------+--------+------------------------------------------------------------------------------------------------------------------------------------------------------
     BAC    | 0000070858-24-000122 | 10-K      | II.7      |    245 | Bank of America Corporation and Subsidiaries Management's Discussion and Analysis of Financial Condition and Results of Operations Table of Contents
     BAC    | 0000070858-24-000122 | 10-K      | II.8      |    370 | Financial Statements and Supplementary Data Table of Contents
     BAC    | 0000070858-25-000139 | 10-K      | II.7      |    242 | Bank of America Corporation and Subsidiaries Management's Discussion and Analysis of Financial Condition and Results of Operations Table of Contents
     BAC    | 0000070858-25-000139 | 10-K      | II.8      |    358 | Financial Statements and Supplementary Data Table of Contents
     BAC    | 0000070858-26-000157 | 10-K      | II.7      |    242 | Bank of America Corporation and Subsidiaries Management's Discussion and Analysis of Financial Condition and Results of Operations Table of Contents
     BAC    | 0000070858-26-000157 | 10-K      | II.8      |    365 | Financial Statements and Supplementary Data Table of Contents
    (6 rows)

Only BAC 10-K Items 7 and 8: 3 filings, 1,822 chunks. Left as a known residual
(TRADEOFFS F-71).

**Freeze notes.** `scripts/write_freeze.py` names F-71 beside F-58; re-run.
`git diff api/corpus_freeze.yaml` changes the `notes` value only (3 insertions,
1 deletion, all inside it).

**Verifier.** `verify_freeze` now compares `chunker_version()` with the record
and requires every stored chunk of every parsed filing to carry the frozen value.
Passing run (exit 0):

    verified 96 frozen accessions; mismatches 0
    chunks of 90 parsed filings: 22354; not on chunker_version 964f77f6f9cb: 0; filings with no chunks: 0

Failing run, `chunking.target_tokens` temporarily 499, no re-chunk (exit 1;
`api/config.yaml` reverted, `git diff` empty):

    verified 96 frozen accessions; mismatches 0
    chunker_version 89d4e49a7f45 != frozen 964f77f6f9cb
    chunks of 90 parsed filings: 22354; not on chunker_version 964f77f6f9cb: 0; filings with no chunks: 0

**Phase 2 owes nothing except F-59**, OWNER-BLOCKED: no valid `ANTHROPIC_API_KEY`,
so the generation call is unexercised. No mocked or canned answer stands in for
it; the Phase 2 exit's "plausible answer out" waits on the key.

## 2026-10-01 — Phase 3 step 1: concept coverage on the frozen corpus (measurement only)

Phase 2 close-out committed as `fb871fa`.

Bank candidates were chosen from the concepts both JPM and BAC tag in nearly
every frozen filing (`us-gaap` only, ≥6 filings each): net interest income,
noninterest income and expense, loan interest income, the credit-loss allowance,
gross loans, pre-tax income, income tax; plus `Deposits` and the loan-loss
provision to probe.

`python -m scripts.concept_coverage` -- facts from the freeze record's 90 parsed
accessions; gold chunks = distinct chunks with a span of the same accession,
concept and period on a non-dimensional context:

    frozen parsed accessions: 90; linked facts in them: 38709; with no visible non-dimensional span (F-48): 476
    human-label queue (eval/human_label_queue.csv): 0 facts (Counter())
    
    facts of these concepts: 4899; bucket changes if gold kept only spans whose value equals the fact's (F-72): none; gold set smaller: 68; left with no exact-value gold: 0
    
    cell = facts as 0 / 1-3 / >3 gold chunks; '-' = no linked fact
    group   concept                                      form          COST           TGT           JPM           BAC          AAPL          NVDA           XOM           PFE
    named   Revenues                                     10-K     0/  9/  0             -             -     0/  9/  0             -     0/  3/  6             -     0/  0/  9
    named   Revenues                                     10-Q     0/ 32/  0             -             -     0/ 30/  0             -     0/ 14/ 16     0/ 30/  0     0/  0/ 30
    named   CostOfRevenue                                10-K             -             -             -             -             -     0/  9/  0             -             -
    named   CostOfRevenue                                10-Q             -             -             -             -             -     0/ 30/  0             -             -
    named   GrossProfit                                  10-K             -             -             -             -     0/  9/  0     0/  9/  0             -             -
    named   GrossProfit                                  10-Q             -             -             -             -     0/ 30/  0     0/ 30/  0             -             -
    named   OperatingIncomeLoss                          10-K     0/  9/  0     0/  9/  0             -             -     0/  9/  0     0/  9/  0             -             -
    named   OperatingIncomeLoss                          10-Q     0/ 36/  0     0/ 30/  0             -             -     0/ 30/  0     0/ 30/  0             -             -
    named   NetIncomeLoss                                10-K     0/  6/  3     0/  0/  9             -     0/  0/  9     0/  0/  9     0/  0/  9             -     0/  9/  0
    named   NetIncomeLoss                                10-Q     0/  8/ 22     0/ 60/  6     0/  0/ 30     0/  0/ 30     0/ 12/ 18     0/  0/ 30     0/ 30/  0     0/ 30/  0
    named   ResearchAndDevelopmentExpense                10-K             -             -             -             -     0/  9/  0     0/  9/  0             -             -
    named   ResearchAndDevelopmentExpense                10-Q             -             -             -             -     0/ 30/  0     0/ 30/  0             -             -
    named   SellingGeneralAndAdministrativeExpense       10-K     0/  9/  0     0/  9/  0             -             -     0/  9/  0     0/  9/  0             -     0/  9/  0
    named   SellingGeneralAndAdministrativeExpense       10-Q     0/ 30/  0     0/ 30/  0             -             -     0/ 30/  0     0/ 30/  0     0/ 30/  0     0/ 30/  0
    named   EarningsPerShareDiluted                      10-K     0/  9/  0     0/  9/  0             -     0/  9/  0     0/  9/  0     0/  9/  0             -     0/  9/  0
    named   EarningsPerShareDiluted                      10-Q     0/ 30/  0     0/ 30/  0     0/ 30/  0     0/ 30/  0     0/ 30/  0     0/ 30/  0     0/ 30/  0     0/ 30/  0
    named   Assets                                       10-K     0/  9/  0     0/  6/  0             -     0/  4/  2     0/  6/  0     0/  6/  0             -     0/  6/  0
    named   Assets                                       10-Q     0/ 18/  0     0/ 27/  0     0/ 27/  0     0/ 24/  3     0/ 18/  0     0/ 18/  0     0/ 18/  0     0/ 18/  0
    named   AssetsCurrent                                10-K     0/  6/  0     0/  6/  0             -             -     0/  6/  0     0/  6/  0             -     0/  6/  0
    named   AssetsCurrent                                10-Q     0/ 18/  0     0/ 27/  0             -             -     0/ 18/  0     0/ 18/  0     0/ 18/  0     0/ 18/  0
    named   Liabilities                                  10-K     0/  6/  0             -             -     0/  6/  0     0/  6/  0     0/  6/  0             -     0/  6/  0
    named   Liabilities                                  10-Q     0/ 18/  0             -     0/ 18/  0     0/ 18/  0     0/ 18/  0     0/ 18/  0     0/ 18/  0     0/ 18/  0
    named   StockholdersEquity                           10-K     0/  6/  0     0/ 12/  0             -     0/ 12/  0     0/ 12/  0     0/ 12/  0             -     0/  6/  0
    named   StockholdersEquity                           10-Q     0/ 38/  0     0/ 63/  0     0/ 27/  0     0/ 48/  0     0/ 48/  0     0/ 48/  0     0/ 18/  0     0/ 18/  0
    named   CashAndCashEquivalentsAtCarryingValue        10-K     0/  6/  0             -             -             -     0/  6/  0     0/  6/  0             -     0/  6/  0
    named   CashAndCashEquivalentsAtCarryingValue        10-Q     0/ 18/  0             -             -             -     0/ 18/  0     0/ 19/  0     0/ 18/  0     0/ 18/  0
    named   InventoryNet                                 10-K     0/  6/  0     0/  6/  0             -             -     0/  6/  0     0/  6/  0             -     0/  6/  0
    named   InventoryNet                                 10-Q     0/ 18/  0     0/ 27/  0             -             -     0/ 18/  0     0/ 18/  0             -     0/ 18/  0
    named   AccountsReceivableNetCurrent                 10-K             -             -             -             -     0/  6/  0     0/  6/  0             -     0/  6/  0
    named   AccountsReceivableNetCurrent                 10-Q             -             -             -             -     0/ 18/  0     0/ 18/  0             -     0/ 18/  0
    named   LongTermDebtNoncurrent                       10-K     0/  6/  0             -             -             -     0/  6/  0     0/  6/  0             -     0/  6/  0
    named   LongTermDebtNoncurrent                       10-Q     0/ 18/  0             -             -             -     0/ 18/  0     0/ 18/  0             -     0/ 18/  0
    named   NetCashProvidedByUsedInOperatingActivities   10-K     0/  9/  0     0/  9/  0             -     0/  9/  0     0/  9/  0     0/  9/  0             -     0/  9/  0
    named   NetCashProvidedByUsedInOperatingActivities   10-Q     0/ 18/  0     0/ 18/  0     0/ 18/  0     0/ 18/  0     0/ 18/  0     0/ 18/  0     0/ 18/  0     0/ 18/  0
    named   PaymentsToAcquirePropertyPlantAndEquipment   10-K     0/  9/  0     0/  9/  0             -             -     0/  9/  0             -             -     0/  9/  0
    named   PaymentsToAcquirePropertyPlantAndEquipment   10-Q     0/ 18/  0     0/ 18/  0             -             -     0/ 18/  0             -     0/ 18/  0     0/ 18/  0
    named   PaymentsForRepurchaseOfCommonStock           10-K     0/  9/  0     0/  9/  0             -     0/  9/  0     0/  9/  0     0/  9/  0             -     0/  6/  0
    named   PaymentsForRepurchaseOfCommonStock           10-Q     0/ 18/  0     0/ 16/  0     0/ 18/  0     0/ 18/  0     0/ 18/  0     0/ 18/  0     0/ 18/  0     0/  2/  0
    bank    InterestIncomeExpenseNet                     10-K             -             -             -     0/  9/  0             -             -             -             -
    bank    InterestIncomeExpenseNet                     10-Q             -             -     0/ 30/  0     0/ 30/  0             -             -             -             -
    bank    NoninterestIncome                            10-K             -             -             -     0/  0/  9             -             -             -             -
    bank    NoninterestIncome                            10-Q             -             -     0/ 30/  0     0/  0/ 30             -             -             -             -
    bank    NoninterestExpense                           10-K             -             -             -     0/  9/  0             -             -             -             -
    bank    NoninterestExpense                           10-Q             -             -     0/ 30/  0     0/ 30/  0             -             -             -             -
    bank    InterestAndFeeIncomeLoansAndLeases           10-K             -             -             -     0/  9/  0             -             -             -             -
    bank    InterestAndFeeIncomeLoansAndLeases           10-Q             -             -     0/ 30/  0     0/ 30/  0             -             -             -             -
    bank    ProvisionForLoanLeaseAndOtherLosses          10-K             -             -             -             -             -             -             -             -
    bank    ProvisionForLoanLeaseAndOtherLosses          10-Q             -             -     0/ 12/ 18             -             -             -             -             -
    bank    FinancingReceivableAllowanceForCreditLossExc 10-K             -             -             -     0/ 12/  0             -             -             -             -
    bank    FinancingReceivableAllowanceForCreditLossExc 10-Q             -             -     0/ 36/  0     0/ 48/  0             -             -             -             -
    bank    FinancingReceivableExcludingAccruedInterestB 10-K             -             -             -     0/  6/  0             -             -             -             -
    bank    FinancingReceivableExcludingAccruedInterestB 10-Q             -             -     0/ 27/  0     0/ 18/  0             -             -             -             -
    bank    Deposits                                     10-K             -             -             -     0/  6/  0             -             -             -             -
    bank    Deposits                                     10-Q             -             -     0/ 18/  0     0/ 18/  0             -             -             -             -
    bank    IncomeLossFromContinuingOperationsBeforeInco 10-K     0/  9/  0     0/  9/  0             -     0/  9/  0     0/  9/  0     0/  9/  0             -     0/  9/  0
    bank    IncomeLossFromContinuingOperationsBeforeInco 10-Q     0/ 10/  0     0/ 30/  0     0/ 30/  0     0/ 30/  0     0/ 30/  0     0/ 30/  0     0/ 30/  0     0/ 30/  0
    bank    IncomeTaxExpenseBenefit                      10-K     0/  9/  0     0/  9/  0             -     0/  9/  0     0/  9/  0     0/  9/  0             -     0/  8/  1
    bank    IncomeTaxExpenseBenefit                      10-Q     0/ 30/  0     0/ 30/  0     0/ 30/  0     0/ 30/  0     0/ 30/  0     0/ 30/  0     0/ 30/  0     0/ 30/  0
    variant RevenueFromContractWithCustomerExcludingAsse 10-K     0/  9/  0     0/  9/  0             -             -     0/  6/  3             -             -     0/  3/  0
    variant RevenueFromContractWithCustomerExcludingAsse 10-Q     0/ 30/  0     0/ 30/  0             -             -     0/ 30/  0             -             -             -
    variant CostOfGoodsAndServicesSold                   10-K     0/  9/  0     0/  9/  0             -             -     0/  9/  0             -             -     0/  9/  0
    variant CostOfGoodsAndServicesSold                   10-Q     0/ 30/  0     0/ 30/  0             -             -     0/ 30/  0             -             -     0/ 30/  0
    variant LongTermDebt                                 10-K             -     0/  6/  0             -     0/  6/  0     0/  6/  0     0/  6/  0             -             -
    variant LongTermDebt                                 10-Q             -             -             -     0/ 18/  0     0/ 18/  0     0/ 18/  0             -             -
    variant EarningsPerShareBasic                        10-K     0/  9/  0     0/  9/  0             -     0/  9/  0     0/  9/  0     0/  9/  0             -     0/  9/  0
    variant EarningsPerShareBasic                        10-Q     0/ 30/  0     0/ 30/  0     0/ 30/  0     0/ 30/  0     0/ 30/  0     0/ 30/  0     0/ 30/  0     0/ 30/  0

Spot check of 8 random facts (span value vs fact value, printed text inside the
gold chunk):

    BAC 0000070858-26-000249 StockholdersEquity None..2025-03-31 value=293949000000 USD: 1 gold chunks
        0000070858-26-000249:603.0:603.0 span '293,949' span value=293949000000 | span value == fact value: True | printed text in chunk: True
    TGT 0000027419-23-000052 EarningsPerShareDiluted 2023-01-29..2023-10-28 value=5.96 USD/shares: 1 gold chunks
        0000027419-23-000052:36.0:36.0 span '5.96' span value=5.96 | span value == fact value: True | printed text in chunk: True
    AAPL 0000320193-24-000123 StockholdersEquity None..2023-09-30 value=62146000000 USD: 3 gold chunks
        0000320193-24-000123:416.1:416.1 span '62,146' span value=62146000000 | span value == fact value: True | printed text in chunk: True
        0000320193-24-000123:422.0:422.0 span '62,146' span value=62146000000 | span value == fact value: True | printed text in chunk: True
        0000320193-24-000123:422.1:422.1 span '62,146' span value=62146000000 | span value == fact value: True | printed text in chunk: True
    COST 0000909832-25-000101 OperatingIncomeLoss 2024-09-02..2025-08-31 value=10383000000 USD: 2 gold chunks
        0000909832-25-000101:439.0:439.0 span '10,383' span value=10383000000 | span value == fact value: True | printed text in chunk: True
        0000909832-25-000101:722.0:722.0 span '10,383' span value=10383000000 | span value == fact value: True | printed text in chunk: True
    TGT 0000027419-26-000042 NetIncomeLoss 2025-02-02..2025-05-03 value=1036000000 USD: 1 gold chunks
        0000027419-26-000042:54.0:54.0 span '1,036' span value=1036000000 | span value == fact value: True | printed text in chunk: True
    PFE 0000078003-26-000095 Assets None..2026-06-28 value=201131000000 USD: 2 gold chunks
        0000078003-26-000095:410.0:414.0 span '201' span value=201000000000 | span value == fact value: False | printed text in chunk: True
        0000078003-26-000095:65.0:65.0 span '201,131' span value=201131000000 | span value == fact value: True | printed text in chunk: True
    COST 0000909832-25-000015 EarningsPerShareBasic 2023-11-27..2024-02-18 value=3.93 USD/shares: 1 gold chunks
        0000909832-25-000015:33.0:33.0 span '3.93' span value=3.93 | span value == fact value: True | printed text in chunk: True
    AAPL 0000320193-25-000057 Liabilities None..2024-09-28 value=308030000000 USD: 1 gold chunks
        0000320193-25-000057:50.0:50.0 span '308,030' span value=308030000000 | span value == fact value: True | printed text in chunk: True

F-48 across all linked facts of the 90:

    F-48 facts with no visible non-dimensional span: 476 across 33 concepts; in the coverage candidates: 0
        69 us-gaap:PreferredStockSharesIssued
        63 us-gaap:PreferredStockSharesOutstanding
        37 us-gaap:NumberOfReportableSegments
        36 us-gaap:NumberOfOperatingSegments
        30 us-gaap:GoodwillImpairmentLoss
        30 us-gaap:DebtSecuritiesHeldToMaturityAccruedInterestWriteoff
        30 us-gaap:DebtSecuritiesAvailableForSaleAccruedInterestWriteoff
        24 us-gaap:CommonStockSharesOutstanding
        18 us-gaap:FairValueOptionLoansHeldAsAssetsAggregateDifference
        16 us-gaap:CommonStockParOrStatedValuePerShare
        16 us-gaap:CommonStockSharesAuthorized
        16 us-gaap:PreferredStockParOrStatedValuePerShare

**Proposed list, 26 concepts, by coverage alone** (no retrieval run):

    concept (truncated as in the table)            group   tickers K/Q  facts   0   1-3    >3
    Revenues                                       named           4/5    188   0   127    61
    RevenueFromContractWithCustomerExcludingAsse   variant         4/3    120   0   117     3
    CostOfGoodsAndServicesSold                     variant         4/4    156   0   156     0
    GrossProfit                                    named           2/2     78   0    78     0
    OperatingIncomeLoss                            named           4/4    162   0   162     0
    NetIncomeLoss                                  named           6/8    330   0   155   175
    ResearchAndDevelopmentExpense                  named           2/2     78   0    78     0
    SellingGeneralAndAdministrativeExpense         named           5/6    225   0   225     0
    IncomeLossFromContinuingOperationsBeforeInco   bank            6/8    274   0   274     0
    IncomeTaxExpenseBenefit                        bank            6/8    294   0   293     1
    EarningsPerShareDiluted                        named           6/8    294   0   294     0
    EarningsPerShareBasic                          variant         6/8    294   0   294     0
    Assets                                         named           6/8    210   0   205     5
    AssetsCurrent                                  named           5/6    147   0   147     0
    Liabilities                                    named           5/7    156   0   156     0
    StockholdersEquity                             named           6/8    368   0   368     0
    CashAndCashEquivalentsAtCarryingValue          named           4/5    115   0   115     0
    InventoryNet                                   named           5/5    129   0   129     0
    NetCashProvidedByUsedInOperatingActivities     named           6/8    198   0   198     0
    PaymentsToAcquirePropertyPlantAndEquipment     named           4/5    126   0   126     0
    PaymentsForRepurchaseOfCommonStock             named           6/8    177   0   177     0
    InterestIncomeExpenseNet                       bank            1/2     69   0    69     0
    NoninterestIncome                              bank            1/2     69   0    30    39
    NoninterestExpense                             bank            1/2     69   0    69     0
    FinancingReceivableAllowanceForCreditLossExc   bank            1/2     96   0    96     0
    Deposits                                       bank            1/2     42   0    42     0
    TOTAL (26 concepts)                                                  4464   0  4180   284
    
    facts per ticker in the proposal (10-K / 10-Q): {'COST': '156/470', 'TGT': '138/502', 'JPM': '0/402', 'BAC': '141/465', 'AAPL': '168/522', 'NVDA': '150/475', 'XOM': '0/354', 'PFE': '135/386'}
    not proposed: ['CostOfRevenue', 'AccountsReceivableNetCurrent', 'LongTermDebtNoncurrent', 'InterestAndFeeIncomeLoansAndLeases', 'ProvisionForLoanLeaseAndOtherLosses', 'FinancingReceivableExcludingAccruedInterestB', 'LongTermDebt']

Facts include comparatives (prior periods restated in later filings), so the
item count will be far below 4,464 once items are keyed by company and period --
the item schema's step. JPM and XOM contribute 10-Q facts only (their 10-Ks are
quarantined). Not proposed: `CostOfRevenue` (NVDA only), `AccountsReceivableNetCurrent`
(3 filers, no retail), the two long-term-debt tags (split across filers), the
loan-loss provision (JPM only), loan interest income and gross loans (bank lines
overlapping net interest income and the allowance).

Stopped here, as instructed: no eval item, no item schema, F-11 untouched.

## 2026-10-01 — Concept list fixed (F-15); exact-value gold (F-72)

The proposal of the previous entry was not adopted: it dropped PRD-named
concepts, fed both revenue tags to one question and added basic EPS. The list
is `eval/concepts.yaml` (26 line items, 28 tags; TRADEOFFS). Every number below
is the output of `python -m scripts.concept_coverage`, which reads that file:

    list: 26 line items, 28 tags (eval/concepts.yaml)
    frozen parsed accessions: 90; listed facts: 4335
    buckets on exact-value gold: 0 0, 1-3 4051, >3 284
    human-label queue (eval/human_label_queue.csv): 0
    F-72, exact-value gold vs PRD 6.5.3 context key: {'gold smaller under exact value': 68}
    
    cell = tag (N named / V variant) and facts as 0 / 1-3 / >3 gold chunks; '-' = none
    line item                  form            COST             TGT             JPM             BAC            AAPL            NVDA             XOM             PFE
    revenue                    10-K   N   0/  9/  0   V   0/  9/  0               -   N   0/  9/  0   V   0/  6/  3   N   0/  3/  6               -   N   0/  0/  9
    revenue                    10-Q   N   0/ 32/  0   V   0/ 30/  0               -   N   0/ 30/  0   V   0/ 30/  0   N   0/ 14/ 16   N   0/ 30/  0   N   0/  0/ 30
    cost_of_revenue            10-K   V   0/  9/  0   V   0/  9/  0               -               -   V   0/  9/  0   N   0/  9/  0               -   V   0/  9/  0
    cost_of_revenue            10-Q   V   0/ 30/  0   V   0/ 30/  0               -               -   V   0/ 30/  0   N   0/ 30/  0               -   V   0/ 30/  0
    gross_profit               10-K               -               -               -               -   N   0/  9/  0   N   0/  9/  0               -               -
    gross_profit               10-Q               -               -               -               -   N   0/ 30/  0   N   0/ 30/  0               -               -
    operating_income           10-K   N   0/  9/  0   N   0/  9/  0               -               -   N   0/  9/  0   N   0/  9/  0               -               -
    operating_income           10-Q   N   0/ 36/  0   N   0/ 30/  0               -               -   N   0/ 30/  0   N   0/ 30/  0               -               -
    net_income                 10-K   N   0/  6/  3   N   0/  0/  9               -   N   0/  0/  9   N   0/  0/  9   N   0/  0/  9               -   N   0/  9/  0
    net_income                 10-Q   N   0/  8/ 22   N   0/ 60/  6   N   0/  0/ 30   N   0/  0/ 30   N   0/ 12/ 18   N   0/  0/ 30   N   0/ 30/  0   N   0/ 30/  0
    research_and_development   10-K               -               -               -               -   N   0/  9/  0   N   0/  9/  0               -               -
    research_and_development   10-Q               -               -               -               -   N   0/ 30/  0   N   0/ 30/  0               -               -
    sga                        10-K   N   0/  9/  0   N   0/  9/  0               -               -   N   0/  9/  0   N   0/  9/  0               -   N   0/  9/  0
    sga                        10-Q   N   0/ 30/  0   N   0/ 30/  0               -               -   N   0/ 30/  0   N   0/ 30/  0   N   0/ 30/  0   N   0/ 30/  0
    eps_diluted                10-K   N   0/  9/  0   N   0/  9/  0               -   N   0/  9/  0   N   0/  9/  0   N   0/  9/  0               -   N   0/  9/  0
    eps_diluted                10-Q   N   0/ 30/  0   N   0/ 30/  0   N   0/ 30/  0   N   0/ 30/  0   N   0/ 30/  0   N   0/ 30/  0   N   0/ 30/  0   N   0/ 30/  0
    total_assets               10-K   N   0/  9/  0   N   0/  6/  0               -   N   0/  4/  2   N   0/  6/  0   N   0/  6/  0               -   N   0/  6/  0
    total_assets               10-Q   N   0/ 18/  0   N   0/ 27/  0   N   0/ 27/  0   N   0/ 24/  3   N   0/ 18/  0   N   0/ 18/  0   N   0/ 18/  0   N   0/ 18/  0
    current_assets             10-K   N   0/  6/  0   N   0/  6/  0               -               -   N   0/  6/  0   N   0/  6/  0               -   N   0/  6/  0
    current_assets             10-Q   N   0/ 18/  0   N   0/ 27/  0               -               -   N   0/ 18/  0   N   0/ 18/  0   N   0/ 18/  0   N   0/ 18/  0
    total_liabilities          10-K   N   0/  6/  0               -               -   N   0/  6/  0   N   0/  6/  0   N   0/  6/  0               -   N   0/  6/  0
    total_liabilities          10-Q   N   0/ 18/  0               -   N   0/ 18/  0   N   0/ 18/  0   N   0/ 18/  0   N   0/ 18/  0   N   0/ 18/  0   N   0/ 18/  0
    stockholders_equity        10-K   N   0/  6/  0   N   0/ 12/  0               -   N   0/ 12/  0   N   0/ 12/  0   N   0/ 12/  0               -   N   0/  6/  0
    stockholders_equity        10-Q   N   0/ 38/  0   N   0/ 63/  0   N   0/ 27/  0   N   0/ 48/  0   N   0/ 48/  0   N   0/ 48/  0   N   0/ 18/  0   N   0/ 18/  0
    cash_and_equivalents       10-K   N   0/  6/  0               -               -               -   N   0/  6/  0   N   0/  6/  0               -   N   0/  6/  0
    cash_and_equivalents       10-Q   N   0/ 18/  0               -               -               -   N   0/ 18/  0   N   0/ 19/  0   N   0/ 18/  0   N   0/ 18/  0
    inventory                  10-K   N   0/  6/  0   N   0/  6/  0               -               -   N   0/  6/  0   N   0/  6/  0               -   N   0/  6/  0
    inventory                  10-Q   N   0/ 18/  0   N   0/ 27/  0               -               -   N   0/ 18/  0   N   0/ 18/  0               -   N   0/ 18/  0
    accounts_receivable        10-K               -               -               -               -   N   0/  6/  0   N   0/  6/  0               -   N   0/  6/  0
    accounts_receivable        10-Q               -               -               -               -   N   0/ 18/  0   N   0/ 18/  0               -   N   0/ 18/  0
    long_term_debt_noncurrent  10-K   N   0/  6/  0               -               -               -   N   0/  6/  0   N   0/  6/  0               -   N   0/  6/  0
    long_term_debt_noncurrent  10-Q   N   0/ 18/  0               -               -               -   N   0/ 18/  0   N   0/ 18/  0               -   N   0/ 18/  0
    operating_cash_flow        10-K   N   0/  9/  0   N   0/  9/  0               -   N   0/  9/  0   N   0/  9/  0   N   0/  9/  0               -   N   0/  9/  0
    operating_cash_flow        10-Q   N   0/ 18/  0   N   0/ 18/  0   N   0/ 18/  0   N   0/ 18/  0   N   0/ 18/  0   N   0/ 18/  0   N   0/ 18/  0   N   0/ 18/  0
    capex                      10-K   N   0/  9/  0   N   0/  9/  0               -               -   N   0/  9/  0               -               -   N   0/  9/  0
    capex                      10-Q   N   0/ 18/  0   N   0/ 18/  0               -               -   N   0/ 18/  0               -   N   0/ 18/  0   N   0/ 18/  0
    share_repurchases          10-K   N   0/  9/  0   N   0/  9/  0               -   N   0/  9/  0   N   0/  9/  0   N   0/  9/  0               -   N   0/  6/  0
    share_repurchases          10-Q   N   0/ 18/  0   N   0/ 16/  0   N   0/ 18/  0   N   0/ 18/  0   N   0/ 18/  0   N   0/ 18/  0   N   0/ 18/  0   N   0/  2/  0
    net_interest_income        10-K               -               -               -   N   0/  9/  0               -               -               -               -
    net_interest_income        10-Q               -               -   N   0/ 30/  0   N   0/ 30/  0               -               -               -               -
    noninterest_income         10-K               -               -               -   N   0/  0/  9               -               -               -               -
    noninterest_income         10-Q               -               -   N   0/ 30/  0   N   0/  0/ 30               -               -               -               -
    noninterest_expense        10-K               -               -               -   N   0/  9/  0               -               -               -               -
    noninterest_expense        10-Q               -               -   N   0/ 30/  0   N   0/ 30/  0               -               -               -               -
    credit_loss_allowance      10-K               -               -               -   N   0/ 12/  0               -               -               -               -
    credit_loss_allowance      10-Q               -               -   N   0/ 36/  0   N   0/ 48/  0               -               -               -               -
    deposits                   10-K               -               -               -   N   0/  6/  0               -               -               -               -
    deposits                   10-Q               -               -   N   0/ 18/  0   N   0/ 18/  0               -               -               -               -
    pretax_income              10-K   N   0/  9/  0   N   0/  9/  0               -   N   0/  9/  0   N   0/  9/  0   N   0/  9/  0               -   N   0/  9/  0
    pretax_income              10-Q   N   0/ 10/  0   N   0/ 30/  0   N   0/ 30/  0   N   0/ 30/  0   N   0/ 30/  0   N   0/ 30/  0   N   0/ 30/  0   N   0/ 30/  0
    income_tax                 10-K   N   0/  9/  0   N   0/  9/  0               -   N   0/  9/  0   N   0/  9/  0   N   0/  9/  0               -   N   0/  8/  1
    income_tax                 10-Q   N   0/ 30/  0   N   0/ 30/  0   N   0/ 30/  0   N   0/ 30/  0   N   0/ 30/  0   N   0/ 30/  0   N   0/ 30/  0   N   0/ 30/  0
    
    per-ticker supply (facts by bucket 0 / 1-3 / >3):
      COST  10-K      0/141/3   10-Q     0/406/22
      TGT   10-K      0/120/9   10-Q      0/466/6
      JPM   10-K        0/0/0   10-Q     0/342/30
      BAC   10-K     0/112/20   10-Q     0/372/63
      AAPL  10-K     0/159/12   10-Q     0/510/18
      NVDA  10-K     0/147/15   10-Q     0/465/46
      XOM   10-K        0/0/0   10-Q      0/324/0
      PFE   10-K     0/125/10   10-Q     0/362/30
    
    variant resolution:
      revenue: named ['COST', 'BAC', 'NVDA', 'XOM', 'PFE']; variant ['TGT', 'AAPL']
      cost_of_revenue: named ['NVDA']; variant ['COST', 'TGT', 'AAPL', 'PFE']
    
    two-tag check -- filings with facts under both revenue tags for one period:
      COST  0000909832-23-000042 2020-08-31..2021-08-29  Revenues 195929000000  RevenueFromContract... 195929000000  equal
      COST  0000909832-23-000042 2021-08-30..2022-08-28  Revenues 226954000000  RevenueFromContract... 226954000000  equal
      COST  0000909832-23-000042 2022-08-29..2023-09-03  Revenues 242290000000  RevenueFromContract... 242290000000  equal
      COST  0000909832-23-000065 2022-08-29..2022-11-20  Revenues 54437000000  RevenueFromContract... 54437000000  equal
      COST  0000909832-23-000065 2023-09-04..2023-11-26  Revenues 57799000000  RevenueFromContract... 57799000000  equal
      COST  0000909832-24-000017 2022-08-29..2023-02-12  Revenues 109703000000  RevenueFromContract... 109703000000  equal
      COST  0000909832-24-000017 2022-11-21..2023-02-12  Revenues 55266000000  RevenueFromContract... 55266000000  equal
      COST  0000909832-24-000017 2023-09-04..2024-02-18  Revenues 116241000000  RevenueFromContract... 116241000000  equal
      COST  0000909832-24-000017 2023-11-27..2024-02-18  Revenues 58442000000  RevenueFromContract... 58442000000  equal
      COST  0000909832-24-000029 2022-08-29..2023-05-07  Revenues 163351000000  RevenueFromContract... 163351000000  equal
      COST  0000909832-24-000029 2023-02-13..2023-05-07  Revenues 53648000000  RevenueFromContract... 53648000000  equal
      COST  0000909832-24-000029 2023-09-04..2024-05-12  Revenues 174756000000  RevenueFromContract... 174756000000  equal
      COST  0000909832-24-000029 2024-02-19..2024-05-12  Revenues 58515000000  RevenueFromContract... 58515000000  equal
      COST  0000909832-24-000049 2021-08-30..2022-08-28  Revenues 226954000000  RevenueFromContract... 226954000000  equal
      COST  0000909832-24-000049 2022-08-29..2023-09-03  Revenues 242290000000  RevenueFromContract... 242290000000  equal
      COST  0000909832-24-000049 2023-09-04..2024-09-01  Revenues 254453000000  RevenueFromContract... 254453000000  equal
      COST  0000909832-24-000079 2023-09-04..2023-11-26  Revenues 57799000000  RevenueFromContract... 57799000000  equal
      COST  0000909832-24-000079 2024-09-02..2024-11-24  Revenues 62151000000  RevenueFromContract... 62151000000  equal
      COST  0000909832-25-000015 2023-09-04..2024-02-18  Revenues 116241000000  RevenueFromContract... 116241000000  equal
      COST  0000909832-25-000015 2023-11-27..2024-02-18  Revenues 58442000000  RevenueFromContract... 58442000000  equal
      COST  0000909832-25-000015 2024-09-02..2025-02-16  Revenues 125874000000  RevenueFromContract... 125874000000  equal
      COST  0000909832-25-000015 2024-11-25..2025-02-16  Revenues 63723000000  RevenueFromContract... 63723000000  equal
      COST  0000909832-25-000033 2023-09-04..2024-05-12  Revenues 174756000000  RevenueFromContract... 174756000000  equal
      COST  0000909832-25-000033 2024-02-19..2024-05-12  Revenues 58515000000  RevenueFromContract... 58515000000  equal
      COST  0000909832-25-000033 2024-09-02..2025-05-11  Revenues 189079000000  RevenueFromContract... 189079000000  equal
      COST  0000909832-25-000033 2025-02-17..2025-05-11  Revenues 63205000000  RevenueFromContract... 63205000000  equal
      COST  0000909832-25-000101 2022-08-29..2023-09-03  Revenues 242290000000  RevenueFromContract... 242290000000  equal
      COST  0000909832-25-000101 2023-09-04..2024-09-01  Revenues 254453000000  RevenueFromContract... 254453000000  equal
      COST  0000909832-25-000101 2024-09-02..2025-08-31  Revenues 275235000000  RevenueFromContract... 275235000000  equal
      COST  0000909832-25-000169 2024-09-02..2024-11-24  Revenues 62151000000  RevenueFromContract... 62151000000  equal
      COST  0000909832-25-000169 2025-09-01..2025-11-23  Revenues 67307000000  RevenueFromContract... 67307000000  equal
      COST  0000909832-26-000029 2024-09-02..2025-02-16  Revenues 125874000000  RevenueFromContract... 125874000000  equal
      COST  0000909832-26-000029 2024-11-25..2025-02-16  Revenues 63723000000  RevenueFromContract... 63723000000  equal
      COST  0000909832-26-000029 2025-09-01..2026-02-15  Revenues 136904000000  RevenueFromContract... 136904000000  equal
      COST  0000909832-26-000029 2025-11-24..2026-02-15  Revenues 69597000000  RevenueFromContract... 69597000000  equal
      PFE   0000078003-24-000039 2021-01-01..2021-12-31  Revenues 81288000000  RevenueFromContract... 73636000000  DIFFERENT
      PFE   0000078003-24-000039 2022-01-01..2022-12-31  Revenues 100330000000  RevenueFromContract... 91793000000  DIFFERENT
      PFE   0000078003-24-000039 2023-01-01..2023-12-31  Revenues 58496000000  RevenueFromContract... 50914000000  DIFFERENT
    
    variant captions -- one exact-value gold span per variant-only filer:
      AAPL  cost_of_revenue  CostOfGoodsAndServicesSold 0000320193-25-000079 2023-09-30: printed '214,137' in row 'Total cost of sales'
      AAPL  revenue          RevenueFromContractWithCustomerExcludingAssessedTax 0000320193-25-000079 2023-09-30: printed '383,285' in row 'Total net sales'
      COST  cost_of_revenue  CostOfGoodsAndServicesSold 0000909832-25-000101 2023-09-03: printed '212,586' in row 'Merchandise costs'
      PFE   cost_of_revenue  CostOfGoodsAndServicesSold 0000078003-24-000039 2021-12-31: printed '30,821' in row 'Cost of sales(b), (c)'
      TGT   cost_of_revenue  CostOfGoodsAndServicesSold 0000027419-26-000016 2024-02-03: printed '77,828' in row 'Cost of sales'
      TGT   revenue          RevenueFromContractWithCustomerExcludingAssessedTax 0000027419-26-000016 2024-02-03: printed '107,412' in row 'Net sales'

COST's two revenue tags agree on every period; PFE's differ in its FY2023 10-K
(`Revenues` includes revenue outside contracts with customers), which is why a
line item takes one tag per filer. The variant captions are the evidence each
variant is that filer's line: AAPL "Total net sales" / "Total cost of sales",
TGT "Net sales" / "Cost of sales", COST "Merchandise costs", PFE "Cost of
sales".

## 2026-10-01 — Item schema and sampler: measurements (no item generated)

`python -m scripts.item_supply` (reads the same facts as `concept_coverage`
through the shared `classify_facts`; `concept_coverage` output re-run and
byte-identical after the refactor):

    listed facts: 4335; buckets {'1-3': 4051, '>3': 284}
    
    cross-filing duplication:
      distinct (cik, concept, period_start, period_end) keys: 2553
      in more than one parsed accession: 1234 (accessions per such key: {2: 973, 3: 123, 4: 41, 5: 74, 6: 7, 7: 8, 8: 3, 9: 5})
      of those, value differs across accessions: 61
        TGT   CostOfGoodsAndServicesSold 2022-01-30..2023-01-28: [('0000027419-24-000032', Decimal('82229000000')), ('0000027419-25-000018', Decimal('82306000000'))]
        TGT   CostOfGoodsAndServicesSold 2023-01-29..2024-02-03: [('0000027419-24-000032', Decimal('77736000000')), ('0000027419-25-000018', Decimal('77828000000')), ('0000027419-26-000016', Decimal('77828000000'))]
        TGT   CostOfGoodsAndServicesSold 2024-02-04..2024-05-04: [('0000027419-24-000129', Decimal('17449000000')), ('0000027419-25-000101', Decimal('17471000000'))]
        TGT   CostOfGoodsAndServicesSold 2024-02-04..2024-08-03: [('0000027419-24-000152', Decimal('35248000000')), ('0000027419-25-000118', Decimal('35297000000'))]
        TGT   CostOfGoodsAndServicesSold 2024-02-04..2024-11-02: [('0000027419-24-000179', Decimal('53623000000')), ('0000027419-25-000126', Decimal('53700000000'))]
        TGT   CostOfGoodsAndServicesSold 2024-05-05..2024-08-03: [('0000027419-24-000152', Decimal('17799000000')), ('0000027419-25-000118', Decimal('17826000000'))]
        TGT   CostOfGoodsAndServicesSold 2024-08-04..2024-11-02: [('0000027419-24-000179', Decimal('18375000000')), ('0000027419-25-000126', Decimal('18402000000'))]
        TGT   SellingGeneralAndAdministrativeExpense 2022-01-30..2023-01-28: [('0000027419-24-000032', Decimal('20658000000')), ('0000027419-25-000018', Decimal('20581000000'))]
        TGT   SellingGeneralAndAdministrativeExpense 2023-01-29..2024-02-03: [('0000027419-24-000032', Decimal('21554000000')), ('0000027419-25-000018', Decimal('21462000000')), ('0000027419-26-000016', Decimal('21462000000'))]
        TGT   SellingGeneralAndAdministrativeExpense 2024-02-04..2024-05-04: [('0000027419-24-000129', Decimal('5168000000')), ('0000027419-25-000101', Decimal('5146000000'))]
        TGT   SellingGeneralAndAdministrativeExpense 2024-02-04..2024-08-03: [('0000027419-24-000152', Decimal('10560000000')), ('0000027419-25-000118', Decimal('10511000000'))]
        TGT   SellingGeneralAndAdministrativeExpense 2024-02-04..2024-11-02: [('0000027419-24-000179', Decimal('16046000000')), ('0000027419-25-000126', Decimal('15969000000'))]
      keys reported by a filing whose own period it is: 1898; only as a later filing's comparative: 655
      keys by their facts' buckets: {'all 1-3': 2362, 'all >3': 167, 'mixed': 24}
    
    sampler strata (ticker x line item x form, 1-3 bucket only):
      non-empty strata: 231; facts per stratum min 2, median 18, max 63
      distinct keys per stratum: min 2, max 26
      strata per ticker: {'AAPL': 41, 'COST': 36, 'TGT': 29, 'JPM': 13, 'BAC': 26, 'NVDA': 38, 'XOM': 14, 'PFE': 34}
      strata per form: {'10-K': 101, '10-Q': 130}
    
    line items entirely in the >3 bucket for a filer (all its facts, both forms):
      BAC   net_income: 39 facts, all >3
      BAC   noninterest_income: 39 facts, all >3
      JPM   net_income: 30 facts, all >3
      NVDA  net_income: 39 facts, all >3
      PFE   revenue: 39 facts, all >3
    
    review queue (eval/review_queue.csv): 284 facts

The 61 value-differing keys by ticker and concept, and whether any differ
between two filings that each report the period as their own (ad hoc query over
`classify_facts`):

    Counter({('TGT', 'CostOfGoodsAndServicesSold'): 7, ('TGT', 'SellingGeneralAndAdministrativeExpense'): 7, ('BAC', 'Revenues'): 5, ('BAC', 'IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest'): 5, ('BAC', 'IncomeTaxExpenseBenefit'): 5, ('BAC', 'NetIncomeLoss'): 5, ('BAC', 'NoninterestIncome'): 5, ('NVDA', 'EarningsPerShareDiluted'): 5, ('BAC', 'EarningsPerShareDiluted'): 4, ('BAC', 'StockholdersEquity'): 4, ('PFE', 'Revenues'): 4, ('BAC', 'Assets'): 3, ('BAC', 'Liabilities'): 1, ('PFE', 'AccountsReceivableNetCurrent'): 1})
    differing keys with >1 distinct value among non-comparative facts: 0

Every disagreement is a later filing's comparative against the original, never
two originals. Cause not established here. `eval/review_queue.csv` holds the 284
>3 facts (F-73). Line items entirely in >3 for a filer (F-74): JPM, BAC and NVDA
net income, PFE revenue -- as expected -- plus BAC noninterest income.

## 2026-10-01 — One fact loader; period labels checked (F-75)

`scripts/concept_coverage.main()` now consumes `classify_facts` (its rows carry
the PRD-key gold count, the exact-value spans with `raw_text`, and the reporting
filing's dei labels; unresolved facts come back separately for the two-tag
check). Re-run: `concept_coverage` and `item_supply` output both
byte-identical to the previous runs (`diff` empty), `eval/human_label_queue.csv`
unchanged.

`xbrl_facts.fiscal_year` / `fiscal_period` against the reporting filing's dei
labels (`filings.fiscal_year`, `'Q' || fiscal_quarter` or `FY`), parsed filings:

     is_comparative | rows  | fy_equals_filing_fy | fp_equals_filing_fp | both_equal
    ----------------+-------+---------------------+---------------------+------------
     f              | 18522 |               18522 |               18522 |      18522
     t              | 20187 |               20187 |               20187 |      20187

    TGT FY2023 cost of sales (2023-01-29..2024-02-03) in each filing:
          accession       | form_type | filing_fy | filing_q | fact_fy | fact_fp | is_comparative |    value
     0000027419-24-000032 | 10-K      |      2023 |          |    2023 | FY      | f              | 77736000000
     0000027419-25-000018 | 10-K      |      2024 |          |    2024 | FY      | t              | 77828000000
     0000027419-26-000016 | 10-K      |      2025 |          |    2025 | FY      | t              | 77828000000

So a comparative row carries the later filing's label; the period label must
come from the own-period filing. Over `classify_facts` rows: keys by number of
own-period accessions `{0: 655, 1: 1898}`; own-period facts with a NULL filing
fiscal year: 0.

## 2026-10-01 — xbrl_auto pool and sampler as tested code (no item, no dataset)

`eval/generate/schema.py` (PRD 11.1 item format + validator), `eval/generate/pool.py`
(`build_pool`, `sample`; pure), `scripts/xbrl_pool.py` (driver). Sampler config:
`eval_sampler:` in `api/config.yaml`. `scripts/item_supply.py` no longer writes
the review queue; `xbrl_pool` does, with a `reason` column. Its other output is
unchanged (`diff` shows only the removed queue line).

`python -m scripts.xbrl_pool`:

    facts: 4335; by category: {'comparative_only': 801, 'eligible': 3089, 'gt3': 226, 'mixed_key': 63, 'value_differs': 156}; sum 4335
    keys: 2553; by category: {'comparative_only': 602, 'eligible': 1713, 'gt3': 153, 'mixed_key': 24, 'value_differs': 61}
    review queue (eval/review_queue.csv): 445 facts, {'gt3': 226, 'mixed_key': 63, 'value_differs': 156}
    
    eligible keys and strata per ticker (strata = line item x own-period form):
      COST  keys  234  strata  34  10-K  51  10-Q  183
      TGT   keys  209  strata  29  10-K  40  10-Q  169
      JPM   keys  153  strata  13  10-K   0  10-Q  153
      BAC   keys  161  strata  26  10-K  26  10-Q  135
      AAPL  keys  297  strata  40  10-K  57  10-Q  240
      NVDA  keys  268  strata  38  10-K  54  10-Q  214
      XOM   keys  162  strata  14  10-K   0  10-Q  162
      PFE   keys  229  strata  34  10-K  48  10-Q  181
    
    line items a filer has facts for but no eligible key, and why (fact categories):
      BAC   net_income               {'gt3': 28, 'value_differs': 11}
      BAC   noninterest_income       {'gt3': 28, 'value_differs': 11}
      COST  net_income               {'comparative_only': 7, 'gt3': 19, 'mixed_key': 13}
      JPM   net_income               {'gt3': 30}
      NVDA  net_income               {'gt3': 39}
      PFE   revenue                  {'gt3': 30, 'value_differs': 9}
      emptied by (c) alone: none
    
    draw: seed 20261001, total 160, per ticker {'COST': 20, 'TGT': 20, 'JPM': 20, 'BAC': 20, 'AAPL': 20, 'NVDA': 20, 'XOM': 20, 'PFE': 20}
    drawn keys: 160; distinct: 160
      COST  capex/10-K 1, capex/10-Q 1, cost_of_revenue/10-K 1, current_assets/10-K 1, eps_diluted/10-K 1, eps_diluted/10-Q 1, income_tax/10-Q 1, inventory/10-K 1, long_term_debt_noncurrent/10-K 1, long_term_debt_noncurrent/10-Q 1, operating_cash_flow/10-K 1, operating_income/10-Q 1, pretax_income/10-Q 1, revenue/10-K 1, sga/10-K 1, share_repurchases/10-K 1, share_repurchases/10-Q 1, stockholders_equity/10-K 1, total_assets/10-Q 1, total_liabilities/10-K 1
      TGT   capex/10-K 1, capex/10-Q 1, cost_of_revenue/10-K 1, cost_of_revenue/10-Q 1, current_assets/10-Q 1, eps_diluted/10-K 1, eps_diluted/10-Q 1, income_tax/10-K 1, inventory/10-Q 1, net_income/10-Q 1, operating_cash_flow/10-Q 1, operating_income/10-K 1, pretax_income/10-K 1, pretax_income/10-Q 1, revenue/10-K 1, revenue/10-Q 1, sga/10-Q 1, share_repurchases/10-Q 1, stockholders_equity/10-Q 1, total_assets/10-K 1
      JPM   credit_loss_allowance/10-Q 1, deposits/10-Q 2, eps_diluted/10-Q 1, income_tax/10-Q 1, net_interest_income/10-Q 2, noninterest_expense/10-Q 2, noninterest_income/10-Q 2, operating_cash_flow/10-Q 1, pretax_income/10-Q 1, share_repurchases/10-Q 1, stockholders_equity/10-Q 2, total_assets/10-Q 2, total_liabilities/10-Q 2
      BAC   credit_loss_allowance/10-K 1, credit_loss_allowance/10-Q 1, deposits/10-K 1, deposits/10-Q 1, income_tax/10-K 1, income_tax/10-Q 1, net_interest_income/10-K 1, net_interest_income/10-Q 1, noninterest_expense/10-Q 1, operating_cash_flow/10-Q 1, pretax_income/10-K 1, revenue/10-K 1, revenue/10-Q 1, share_repurchases/10-K 1, share_repurchases/10-Q 1, stockholders_equity/10-K 1, stockholders_equity/10-Q 1, total_assets/10-Q 1, total_liabilities/10-K 1, total_liabilities/10-Q 1
      AAPL  accounts_receivable/10-K 1, cash_and_equivalents/10-K 1, cash_and_equivalents/10-Q 1, cost_of_revenue/10-K 1, cost_of_revenue/10-Q 1, current_assets/10-K 1, inventory/10-K 1, long_term_debt_noncurrent/10-K 1, operating_cash_flow/10-K 1, operating_income/10-Q 1, research_and_development/10-K 1, revenue/10-Q 1, sga/10-K 1, sga/10-Q 1, share_repurchases/10-K 1, share_repurchases/10-Q 1, stockholders_equity/10-Q 1, total_assets/10-Q 1, total_liabilities/10-K 1, total_liabilities/10-Q 1
      NVDA  accounts_receivable/10-K 1, cash_and_equivalents/10-K 1, cash_and_equivalents/10-Q 1, current_assets/10-Q 1, gross_profit/10-Q 1, income_tax/10-K 1, inventory/10-Q 1, long_term_debt_noncurrent/10-K 1, operating_cash_flow/10-Q 1, operating_income/10-Q 1, pretax_income/10-Q 1, revenue/10-K 1, revenue/10-Q 1, sga/10-K 1, share_repurchases/10-K 1, share_repurchases/10-Q 1, stockholders_equity/10-K 1, total_assets/10-K 1, total_assets/10-Q 1, total_liabilities/10-Q 1
      XOM   capex/10-Q 1, cash_and_equivalents/10-Q 1, current_assets/10-Q 2, eps_diluted/10-Q 1, income_tax/10-Q 1, net_income/10-Q 2, operating_cash_flow/10-Q 2, pretax_income/10-Q 1, revenue/10-Q 1, sga/10-Q 2, share_repurchases/10-Q 2, stockholders_equity/10-Q 2, total_assets/10-Q 1, total_liabilities/10-Q 1
      PFE   accounts_receivable/10-Q 1, capex/10-K 1, capex/10-Q 1, cost_of_revenue/10-K 1, current_assets/10-K 1, income_tax/10-K 1, income_tax/10-Q 1, inventory/10-K 1, inventory/10-Q 1, long_term_debt_noncurrent/10-K 1, long_term_debt_noncurrent/10-Q 1, net_income/10-K 1, operating_cash_flow/10-Q 1, pretax_income/10-K 1, pretax_income/10-Q 1, sga/10-K 1, share_repurchases/10-K 1, share_repurchases/10-Q 1, stockholders_equity/10-Q 1, total_liabilities/10-K 1
    draw by form: {'10-K': 60, '10-Q': 100}; distinct line items: 26

Ad hoc over `build_pool` on the same rows:

    eligible keys by number of gold evidence sets: {1: 527, 2: 646, 3: 162, 4: 186, 5: 86, 6: 56, 7: 13, 8: 13, 9: 6, 10: 9, 11: 1, 12: 2, 14: 2, 15: 1, 16: 2, 17: 1}
    eligible keys by number of gold accessions: {1: 767, 2: 750, 3: 79, 4: 35, 5: 68, 6: 4, 7: 3, 8: 3, 9: 4}
    eligible keys by own-filing label: {('10-K', 'FY'): 276, ('10-Q', 'Q1'): 364, ('10-Q', 'Q2'): 535, ('10-Q', 'Q3'): 538}

Every fact is 1-3 within its own filing, but 378 eligible keys have more than 3
evidence sets once gold is the union over every accession carrying the key
(question in the report). No ticker is short of its 20.

Tests: `tests/unit/test_pool.py` on `tests/fixtures/xbrl_pool_rows.json` (234
real rows, `python -m scripts.xbrl_pool --write-fixture`, covering all five
categories), `tests/unit/test_item_schema.py` on PRD 11.1's example item.
`make test`: 259 passed.

## 2026-10-01 — Large evidence sets listed; xbrl_numeric candidates generated

The 18 eligible keys with 10 or more evidence sets (ad hoc over `build_pool`;
accession and exact-value chunks per accession):

    eligible keys with >= 10 evidence sets: 18
      TGT   stockholders_equity              ..2024-02-03 own 10-K sets 17: 0000027419-24-000032 2, 0000027419-24-000129 3, 0000027419-24-000152 3, 0000027419-24-000179 3, 0000027419-25-000018 2, 0000027419-25-000101 1, 0000027419-25-000118 1, 0000027419-25-000126 1, 0000027419-26-000016 1
      AAPL  stockholders_equity              ..2023-09-30 own 10-K sets 16: 0000320193-23-000106 2, 0000320193-24-000006 2, 0000320193-24-000069 2, 0000320193-24-000081 2, 0000320193-24-000123 3, 0000320193-25-000008 1, 0000320193-25-000057 1, 0000320193-25-000073 1, 0000320193-25-000079 2
      BAC   credit_loss_allowance            ..2023-12-31 own 10-K sets 16: 0000070858-24-000122 2, 0000070858-24-000156 2, 0000070858-24-000208 2, 0000070858-24-000280 2, 0000070858-25-000139 3, 0000070858-25-000200 1, 0000070858-25-000268 1, 0000070858-25-000405 1, 0000070858-26-000157 2
      TGT   stockholders_equity              ..2025-02-01 own 10-K sets 15: 0000027419-25-000018 2, 0000027419-25-000101 3, 0000027419-25-000118 3, 0000027419-25-000126 3, 0000027419-26-000016 2, 0000027419-26-000022 1, 0000027419-26-000042 1
      AAPL  stockholders_equity              ..2024-09-28 own 10-K sets 14: 0000320193-24-000123 2, 0000320193-25-000008 2, 0000320193-25-000057 2, 0000320193-25-000073 2, 0000320193-25-000079 3, 0000320193-26-000006 1, 0000320193-26-000013 1, 0000320193-26-000020 1
      NVDA  stockholders_equity              ..2024-01-28 own 10-K sets 14: 0001045810-24-000029 2, 0001045810-24-000124 2, 0001045810-24-000264 2, 0001045810-24-000316 2, 0001045810-25-000023 2, 0001045810-25-000116 1, 0001045810-25-000209 1, 0001045810-25-000230 1, 0001045810-26-000021 1
      BAC   credit_loss_allowance            ..2024-12-31 own 10-K sets 12: 0000070858-25-000139 2, 0000070858-25-000200 2, 0000070858-25-000268 2, 0000070858-25-000405 2, 0000070858-26-000157 2, 0000070858-26-000249 1, 0000070858-26-000394 1
      NVDA  stockholders_equity              ..2025-01-26 own 10-K sets 12: 0001045810-25-000023 2, 0001045810-25-000116 2, 0001045810-25-000209 2, 0001045810-25-000230 2, 0001045810-26-000021 2, 0001045810-26-000052 1, 0001045810-26-000075 1
      COST  stockholders_equity              ..2024-09-01 own 10-K sets 11: 0000909832-24-000049 1, 0000909832-24-000079 2, 0000909832-25-000015 2, 0000909832-25-000033 2, 0000909832-25-000101 1, 0000909832-25-000169 1, 0000909832-26-000029 1, 0000909832-26-000051 1
      AAPL  cash_and_equivalents             ..2023-09-30 own 10-K sets 10: 0000320193-23-000106 2, 0000320193-24-000006 2, 0000320193-24-000069 2, 0000320193-24-000081 2, 0000320193-24-000123 2
      AAPL  cash_and_equivalents             ..2024-09-28 own 10-K sets 10: 0000320193-24-000123 2, 0000320193-25-000008 2, 0000320193-25-000057 2, 0000320193-25-000073 2, 0000320193-25-000079 2
      COST  long_term_debt_noncurrent           ..2023-09-03 own 10-K sets 10: 0000909832-23-000042 2, 0000909832-23-000065 2, 0000909832-24-000017 2, 0000909832-24-000029 2, 0000909832-24-000049 2
      COST  long_term_debt_noncurrent           ..2024-09-01 own 10-K sets 10: 0000909832-24-000049 2, 0000909832-24-000079 2, 0000909832-25-000015 2, 0000909832-25-000033 2, 0000909832-25-000101 2
      NVDA  inventory                        ..2024-01-28 own 10-K sets 10: 0001045810-24-000029 2, 0001045810-24-000124 2, 0001045810-24-000264 2, 0001045810-24-000316 2, 0001045810-25-000023 2
      NVDA  inventory                        ..2025-01-26 own 10-K sets 10: 0001045810-25-000023 2, 0001045810-25-000116 2, 0001045810-25-000209 2, 0001045810-25-000230 2, 0001045810-26-000021 2
      NVDA  long_term_debt_noncurrent           ..2024-01-28 own 10-K sets 10: 0001045810-24-000029 2, 0001045810-24-000124 2, 0001045810-24-000264 2, 0001045810-24-000316 2, 0001045810-25-000023 2
      PFE   inventory                        ..2023-12-31 own 10-K sets 10: 0000078003-24-000039 2, 0000078003-24-000107 2, 0000078003-24-000166 2, 0000078003-24-000191 2, 0000078003-25-000054 2
      PFE   inventory                        ..2024-12-31 own 10-K sets 10: 0000078003-25-000054 2, 0000078003-25-000114 2, 0000078003-25-000138 2, 0000078003-25-000150 2, 0000078003-26-000026 2

Gold rule moved to `eval/generate/gold.select_gold`; `classify_facts` keeps
dimensional spans (flagged) and calls it. Re-run: `concept_coverage` and
`xbrl_pool` output byte-identical to the committed runs; both queue files
unchanged. (A first attempt looked spans up by date objects against string keys:
every fact came out 0-gold. Caught by the diff, fixed before anything was
committed.) Facts with a same-value dimensional span in a chunk: 479.

Generator over every eligible key, not only the draw (ad hoc):

    all 1713 eligible keys: period kinds {'annual': 162, 'instant': 557, 'quarter': 547, 'ytd': 447}
    keys the generator would report, not generate: 1 {"value: own filing's exact-value spans print scales [6, 9]": 1}
    units: {'USD': 1583, 'USD/shares': 130} own scales: {(6,): 1582, (0,): 115, (None,): 3, (0, None): 12, (6, 9): 1}

The one key reported (F-80):

    NVDA income_tax 2026-01-26 2026-07-26 0001045810-26-000075 23400000000 [('0001045810-26-000075:45.0:45.0', '23,400'), ('0001045810-26-000075:273.0:281.0', '23.4')] (6, 9)

Two wording gaps found on the way and fixed before the final run: Costco's
12-week quarters (84 / 168 / 252 days) were first rejected as not month-length
and are now worded in weeks; Pfizer's 88- and 179-day periods (fixture rows, not
drawn) needed the month ranges widened. The draw did not change (seed 20261001,
no re-draw).

F-71 residual in the candidates' gold (ad hoc over the candidates and `chunks`):

    distinct gold chunks in the 160 candidates: 326; with an F-71 'Table of Contents' context header: 15
    candidates with at least one such gold chunk: 9; whose every evidence set is one: 5

`xbrl_fact_id`: a rebuild from the freeze was not run. `xbrl_facts.fact_id` is a
serial filled with `ON CONFLICT DO NOTHING`, and the stored ids run 1..58,979
over 43,122 rows (`SELECT min(fact_id), max(fact_id), count(*)`), so a fresh
load would number them differently: F-78, not fixed.

`python -m scripts.xbrl_candidates`:

    items: 160 (drawn 160); not generated: 0
    validation failures: 0
    items per template: {'dur_figure': 27, 'dur_filing': 14, 'dur_how_much': 29, 'dur_record': 8, 'dur_report': 18, 'ins_balance': 16, 'ins_carry': 11, 'ins_figure': 10, 'ins_filing': 12, 'ins_report': 15}
    period kinds: {'annual': 35, 'instant': 64, 'quarter': 29, 'ytd': 32}
    form split per ticker (10-K/10-Q): COST 12/8, TGT 8/12, JPM 0/20, BAC 9/11, AAPL 11/9, NVDA 9/11, XOM 0/20, PFE 11/9
    form split: {'10-K': 60, '10-Q': 100}
    evidence sets per item: {1: 54, 2: 45, 3: 23, 4: 11, 5: 9, 6: 13, 7: 2, 8: 1, 10: 2}
    filing-scoped items: 26, all single-accession: True
    spot-check (eval/candidates/xbrl_numeric_spot_check.md): 16 items, 33 gold chunks
    wrote eval/candidates/xbrl_numeric_candidates.jsonl sha256 19fb355d8134c950

A second run left all three files' sha256 unchanged. `make test`: 272 passed; `make lint` clean.

## 2026-10-01 — Negative and zero candidates; xbrl_fact_id guarded (F-78)

Gold spans of the two zero items, and edge values in the eligible pool (ad hoc
over `build_pool` and `xbrl_spans`):

    xbrl_0116: Pfizer payments for repurchases of common stock, fiscal 2024: what was the figure? | $0 million for the fiscal year ended December 31, 2024.
       0000078003-25-000054:788.2:788.2 raw_text='—' scale=6 value=0
       0000078003-25-000054:788.2:788.2 raw_text='—' scale=6 value=0
    xbrl_0117: According to its 10-Q for the third quarter of fiscal 2023, what figure did Pfizer report for payments for repurchases of common stock in the nine months ended October 1, 2023? | $0 million for the nine months ended October 1, 2023.
       0000078003-23-000115:77.1:77.1 raw_text='—' scale=6 value=0
    eligible keys valued zero: 6 {'share_repurchases': 6}
    eligible keys valued negative: 32 {'eps_diluted': 2, 'income_tax': 10, 'net_income': 2, 'operating_cash_flow': 15, 'pretax_income': 3}
    zero keys by ticker: {'TGT': 3, 'PFE': 3} negative by ticker: {'JPM': 9, 'BAC': 5, 'PFE': 18}

`python -m scripts.xbrl_candidates` (candidates file unchanged: sha256
19fb355d...; manifest gains `flagged` and `facts`; the sheet gains the flagged
section, 16 + 5 items rendered, xbrl_0115 being both seeded and flagged):

    items: 160 (drawn 160); not generated: 0
    validation failures: 0
    items per template: {'dur_figure': 27, 'dur_filing': 14, 'dur_how_much': 29, 'dur_record': 8, 'dur_report': 18, 'ins_balance': 16, 'ins_carry': 11, 'ins_figure': 10, 'ins_filing': 12, 'ins_report': 15}
    period kinds: {'annual': 35, 'instant': 64, 'quarter': 29, 'ytd': 32}
    form split per ticker (10-K/10-Q): COST 12/8, TGT 8/12, JPM 0/20, BAC 9/11, AAPL 11/9, NVDA 9/11, XOM 0/20, PFE 11/9
    form split: {'10-K': 60, '10-Q': 100}
    evidence sets per item: {1: 54, 2: 45, 3: 23, 4: 11, 5: 9, 6: 13, 7: 2, 8: 1, 10: 2}
    filing-scoped items: 26, all single-accession: True
    spot-check (eval/candidates/xbrl_numeric_spot_check.md): 16 seeded items; flagged (value <= 0): ['xbrl_0070', 'xbrl_0113', 'xbrl_0115', 'xbrl_0116', 'xbrl_0117', 'xbrl_0119']; 45 gold chunks shown
    manifest natural keys: 160
    wrote eval/candidates/xbrl_numeric_candidates.jsonl sha256 19fb355d8134c950

A second run left all three files' sha256 unchanged:

    19fb355d8134c9504a654282354c13e92a453c450e67b87c9e9a25a9aaf638e7  eval/candidates/xbrl_numeric_candidates.jsonl
    68b7ac51bd4ee0eb7e04dcb6cb6fa4221d1b906ba40532b7a6a82039309eaabc  eval/candidates/xbrl_numeric_manifest.json
    8d92d2c92b5533918e34f473c80f1da702facbfe730fce7a46aa7b3220831fba  eval/candidates/xbrl_numeric_spot_check.md

`python -m scripts.xbrl_candidates --verify` (exit 0):

    verify: 160 items, 160 fact ids found in xbrl_facts, 0 mismatches

The same check against a copy of the manifest with xbrl_0001's value set to 1
(ad hoc, module constant pointed at the copy):

    verify: 160 items, 160 fact ids found in xbrl_facts, 1 mismatches
      MISMATCH xbrl_0001: fact_id 43544 is {'accession': '0000320193-23-000106', 'concept': 'us-gaap:ResearchAndDevelopmentExpense', 'period_start': '2022-09-25', 'period_end': '2023-09-30', 'unit': 'USD', 'value': '29915000000'}, want {'accession': '0000320193-23-000106', 'concept': 'us-gaap:ResearchAndDevelopmentExpense', 'period_start': '2022-09-25', 'period_end': '2023-09-30', 'unit': 'USD', 'value': '1'}
    tampered manifest (xbrl_0001 value -> 1): verify returns 1

`make test`: 272 passed (zero cases added to `test_format_value`); `make lint` clean.

## 2026-10-01 — Comparison supply measured (no comparison item generated)

`python -m scripts.comparison_supply` (every number below is its output; the
earlier ad hoc figures are folded in):

    eligible keys: 1713; slots holding more than one key: 0
    
    pairs by (kind, gap): total / one chunk holds both exact values
      annual   gap 1:  103 /  103
      annual   gap 2:   49 /   49
      instant  gap 1:  363 /  129
      instant  gap 2:  185 /    3
      quarter  gap 1:  345 /  345
      quarter  gap 2:  178 /    0
      ytd      gap 1:  287 /  287
      ytd      gap 2:  146 /    0
      instant gap 1 by (year-end or quarter-end, shared chunk): {('quarter-end', False): 234, ('quarter-end', True): 56, ('year-end', True): 73}
      consecutive-year duration pairs: 735; with a shared chunk: 735
    
    pairs needing two chunks (no shared gold chunk): 740 {'instant/gap1': 234, 'instant/gap2': 182, 'quarter/gap2': 178, 'ytd/gap2': 146}
      of which neither side is a drawn xbrl_numeric key: 622
      per ticker, no drawn key (quarter / ytd / instant / total / line items):
        COST    19   14   63    96   16
        TGT     18   18   14    50   15
        JPM     17   12   17    46   13
        BAC     17   14   23    54   12
        AAPL    29   23   62   114   21
        NVDA    22   16   64   102   18
        XOM     15   14   32    61   14
        PFE     20   12   67    99   16
      evidence sets per pair, every (a, b) combination: {1: 219, 2: 191, 3: 8, 4: 69, 6: 6, 8: 61, 9: 2, 12: 4, 14: 1, 15: 26, 16: 1, 18: 13, 20: 4, 21: 3, 24: 2, 25: 4, 27: 1, 28: 2, 35: 1, 60: 1, 80: 2, 136: 1}
      edge values: zero side 1; negative side 10; sign flip 5
      equal values: 0
      sides printing at different (or several) scales, USD: 1
        NVDA income_tax 2024-07-28 (6,) / 2026-07-26 (6, 9)
    
    untagged co-occurrence: pairs with a chunk printing both sides' values: 29 of 622; by group {'instant/gap1': 15, 'instant/gap2': 6, 'quarter/gap2': 5, 'ytd/gap2': 3}
      chunks per such pair: {1: 22, 2: 5, 3: 1, 12: 1}
        TGT income_tax ytd/gap2 2024-08-03 (['630']) / 2026-08-01 (['835']): ['0000027419-24-000152:191.0:191.0', '0000027419-24-000152:36.0:36.0']
        TGT share_repurchases ytd/gap2 2024-08-03 (['155']) / 2026-08-01 (['3']): ['0000027419-24-000032:664.0:670.0', '0000027419-24-000152:119.0:119.0', '0000027419-24-000152:214.0:224.0']
        TGT stockholders_equity instant/gap2 2024-05-04 (['13,840']) / 2026-05-02 (['16,395']): ['0000027419-26-000022:210.0:210.0']
        TGT stockholders_equity instant/gap2 2024-08-03 (['14,429']) / 2026-08-01 (['17,843']): ['0000027419-26-000042:222.0:222.0']
        TGT stockholders_equity instant/gap2 2023-10-28 (['12,514']) / 2025-11-01 (['15,501']): ['0000027419-25-000126:235.0:235.0']
        TGT stockholders_equity instant/gap2 2024-02-03 (['13,432']) / 2026-01-31 (['16,165']): ['0000027419-26-000016:370.0:370.0']
        XOM income_tax quarter/gap2 2024-03-31 (['3,803']) / 2026-03-31 (['2,495']): ['0000034088-24-000029:39.0:39.0', '0000034088-25-000024:40.0:40.0']
        BAC credit_loss_allowance instant/gap1 2023-09-30 (['13,287']) / 2024-09-30 (['13,251']): ['0000070858-24-000280:605.1:605.1']
        BAC eps_diluted quarter/gap2 2023-09-30 (['0.90']) / 2025-09-30 (['1.06']): ['0000070858-25-000405:121.2:121.2', '0000070858-26-000157:469.3:469.3', '0000070858-26-000394:115.2:115.2']
        BAC stockholders_equity instant/gap1 2023-09-30 (['287,064']) / 2024-09-30 (['296,512']): ['0000070858-24-000280:683.1:683.1', '0000070858-25-000139:1183.1:1183.1']
        BAC stockholders_equity instant/gap1 2024-09-30 (['296,512']) / 2025-09-30 (['304,152']): ['0000070858-25-000405:655.1:655.1']
        PFE income_tax quarter/gap2 2023-10-01 (['964']) / 2025-09-28 (['216']): ['0000078003-25-000150:180.2:180.2']
        PFE income_tax ytd/gap2 2024-06-30 (['159']) / 2026-06-28 (['54']): ['0000078003-23-000115:499.0:499.0', '0000078003-24-000166:58.0:58.0']
        PFE net_income quarter/gap2 2024-06-30 (['41']) / 2026-06-28 (['248']): ['0000078003-26-000054:462.2:462.2', '0000078003-26-000095:504.5:504.5']
        AAPL cash_and_equivalents instant/gap1 2025-03-29 (['28,162']) / 2026-03-28 (['45,572']): ['0000320193-26-000013:62.1:62.1']
        AAPL cash_and_equivalents instant/gap1 2025-06-28 (['36,269']) / 2026-06-27 (['39,544']): ['0000320193-26-000020:62.1:62.1']
        COST cash_and_equivalents instant/gap1 2023-11-26 (['17,011']) / 2024-11-24 (['10,907']): ['0000909832-24-000079:61.1:61.1']
        COST cash_and_equivalents instant/gap1 2024-11-24 (['10,907']) / 2025-11-23 (['16,217']): ['0000909832-25-000169:61.1:61.1']
        COST cash_and_equivalents instant/gap1 2024-02-18 (['9,095']) / 2025-02-16 (['12,356']): ['0000909832-25-000015:68.1:68.1']
        COST cash_and_equivalents instant/gap1 2025-02-16 (['12,356']) / 2026-02-15 (['17,383']): ['0000909832-26-000029:68.1:68.1']
        COST cash_and_equivalents instant/gap1 2024-05-12 (['10,404']) / 2025-05-11 (['13,836']): ['0000909832-25-000033:68.1:68.1']
        COST cash_and_equivalents instant/gap1 2025-05-11 (['13,836']) / 2026-05-10 (['18,946']): ['0000909832-26-000051:68.1:68.1']
        COST cash_and_equivalents instant/gap2 2023-09-03 (['13,700']) / 2025-08-31 (['14,161']): ['0000909832-25-000101:467.1:467.1']
        COST share_repurchases quarter/gap2 2023-11-26 (['162']) / 2025-11-23 (['210']): ['0000909832-25-000033:126.0:126.0']
        NVDA cash_and_equivalents instant/gap1 2024-04-28 (['7,587']) / 2025-04-27 (['15,234']): ['0001045810-25-000116:70.1:70.1']
        NVDA cash_and_equivalents instant/gap1 2025-04-27 (['15,234']) / 2026-04-26 (['13,237']): ['0001045810-26-000052:71.1:71.1']
        NVDA cash_and_equivalents instant/gap1 2025-07-27 (['11,639']) / 2026-07-26 (['22,443']): ['0001045810-26-000075:78.1:78.1']
        NVDA cash_and_equivalents instant/gap1 2023-10-29 (['5,519']) / 2024-10-27 (['9,107']): ['0001045810-24-000316:78.1:78.1']
        NVDA cash_and_equivalents instant/gap2 2024-01-28 (['7,280']) / 2026-01-25 (['10,605']): ['0001045810-26-000021:778.2:778.2']

Every consecutive-year duration pair (735) has one chunk holding both exact
values: a later filing prints the prior-year column. So PRD Stage 3's "gold set
= both chunk_ids" holds for none of them. The pairs with no shared gold chunk
are 740 in four groups: instant one year apart 234, instant two years 182,
quarter two years 178, year-to-date two years 146. 622 of them have neither
side among the 160 drawn keys; JPM has the fewest (46).

Untagged co-occurrence matches the sides' printed tokens anywhere in the filer's
chunks, so it is an upper bound. Small values ("3", "41") can match by
coincidence. Real cases include 10-Q cash-flow statements, which print the
year-ago quarter-end cash under another tag.

(Correction to the report of this measurement: it summed the two-chunk pool as
324 + 234 = 558 and left out the 182 instant pairs two years apart, and it gave
the per-ticker minimum as 41; it is 46, JPM.)

## 2026-10-01 — 40 comparison candidates (xbrl_auto)

Checked after the supply commit: the untagged co-occurrence of COST cash
12,356 / 9,095 is chunk 0000909832-25-000015:68.1:68.1, the Q2 FY2025 10-Q cash-flow
statement, tagged there as `CashCashEquivalentsRestrictedCash...`, not the pair's
concept.

Pairing, eligibility, co-occurrence, evidence sets and the reference answer are
pure functions in `eval/generate/comparison.py`; `scripts/comparison_supply.py`
now calls them. Its output has the same lines as the committed run; only the
co-occurrence listing is reordered (pairs now sorted by key):
`diff <(sort old) <(sort new)` is empty. `sample` takes pairs as well as keys
(no key in two pairs); the xbrl_numeric outputs are byte-identical after the
change (sha256 unchanged).

`python -m scripts.comparison_candidates`:

    eligible pairs (no shared gold chunk, no drawn xbrl_numeric key): 622
    items: 40 (drawn 40); not generated: 0
    validation failures: 0
    distinct period keys: 80 of 80; overlap with drawn xbrl_numeric keys: 0
    items per template: {'cmp_dur_both': 6, 'cmp_dur_change': 6, 'cmp_dur_compare': 6, 'cmp_dur_diff': 2, 'cmp_dur_versus': 6, 'cmp_ins_both': 4, 'cmp_ins_change': 1, 'cmp_ins_compare': 4, 'cmp_ins_diff': 3, 'cmp_ins_versus': 2}
    kind/gap: {'instant/gap1': 5, 'instant/gap2': 9, 'quarter/gap2': 16, 'ytd/gap2': 10}
      COST  {'instant/gap2': 1, 'ytd/gap2': 4}
      TGT   {'instant/gap2': 2, 'quarter/gap2': 3}
      JPM   {'instant/gap2': 1, 'quarter/gap2': 4}
      BAC   {'instant/gap2': 2, 'quarter/gap2': 2, 'ytd/gap2': 1}
      AAPL  {'instant/gap1': 1, 'quarter/gap2': 2, 'ytd/gap2': 2}
      NVDA  {'instant/gap1': 1, 'instant/gap2': 1, 'quarter/gap2': 2, 'ytd/gap2': 1}
      XOM   {'instant/gap1': 2, 'quarter/gap2': 1, 'ytd/gap2': 2}
      PFE   {'instant/gap1': 1, 'instant/gap2': 2, 'quarter/gap2': 2}
    evidence sets per item: {1: 6, 2: 17, 3: 1, 4: 3, 6: 1, 8: 7, 12: 1, 18: 1, 21: 2, 27: 1}
    flagged: 0
    spot-check (eval/candidates/comparison_spot_check.md): seeded ['cmp_0003', 'cmp_0015', 'cmp_0036', 'cmp_0040']; 12 gold chunks shown
    manifest fact records: 40 (later + earlier)
    wrote eval/candidates/comparison_candidates.jsonl sha256 e8f78af34061ba4f

A second run left all three files' sha256 unchanged:

    e8f78af34061ba4fe05c10facc6f9dcab2d4e30219dcad40806616614dbb0eef  eval/candidates/comparison_candidates.jsonl
    f8f83e418430d6fca74c691be9129d3b64b41a90c8e038e28ede1aad4b262fe1  eval/candidates/comparison_manifest.json
    d3ec2b6eb9a40ec704405bc30a22bfcf0c62718887b007e95c7a88fe40b9a2a6  eval/candidates/comparison_spot_check.md

`python -m scripts.comparison_candidates --verify` (exit 0):

    verify: 40 items, 80 fact ids checked, 80 found in xbrl_facts, 0 mismatches

Against a copy of the manifest with cmp_0001's earlier value set to 1 (ad hoc):

    verify: 40 items, 80 fact ids checked, 80 found in xbrl_facts, 1 mismatches
      MISMATCH cmp_0001 earlier: fact_id 42555 is {'accession': '0000320193-24-000081', 'concept': 'us-gaap:NetIncomeLoss', 'period_start': '2024-03-31', 'period_end': '2024-06-29', 'unit': 'USD', 'value': '21448000000'}, want {'accession': '0000320193-24-000081', 'concept': 'us-gaap:NetIncomeLoss', 'period_start': '2024-03-31', 'period_end': '2024-06-29', 'unit': 'USD', 'value': '1'}
    tampered manifest (cmp_0001 earlier value -> 1): verify returns 1

`make test`: 282 passed; `make lint` clean; `python -m scripts.xbrl_candidates --verify`: 0 mismatches, its three outputs unchanged.

## 2026-10-01 — Review fixes: real scale-mismatch pair, sheet sides, sign display (F-87)

- `tests/fixtures/xbrl_pool_rows.json` regenerated with NVDA income tax added
  to the slice (`--write-fixture`: 384 rows). `test_sides_at_different_scales_are_reported`
  asserts on the real pair (ytd, gap 2, 2024-07-28 (6,) / 2026-07-26 (6, 9)).
- `comparison_spot_check.md` heads each gold chunk `earlier:` / `later:` and lists
  the evidence sets; the manifest gains `distinct_gold_chunks_per_item`. Both
  candidate files are unchanged (sha256 e8f78af3..., 19fb355d...).

`python -m scripts.comparison_candidates`:

    eligible pairs (no shared gold chunk, no drawn xbrl_numeric key): 622
    items: 40 (drawn 40); not generated: 0
    validation failures: 0
    distinct period keys: 80 of 80; overlap with drawn xbrl_numeric keys: 0
    items per template: {'cmp_dur_both': 6, 'cmp_dur_change': 6, 'cmp_dur_compare': 6, 'cmp_dur_diff': 2, 'cmp_dur_versus': 6, 'cmp_ins_both': 4, 'cmp_ins_change': 1, 'cmp_ins_compare': 4, 'cmp_ins_diff': 3, 'cmp_ins_versus': 2}
    kind/gap: {'instant/gap1': 5, 'instant/gap2': 9, 'quarter/gap2': 16, 'ytd/gap2': 10}
      COST  {'instant/gap2': 1, 'ytd/gap2': 4}
      TGT   {'instant/gap2': 2, 'quarter/gap2': 3}
      JPM   {'instant/gap2': 1, 'quarter/gap2': 4}
      BAC   {'instant/gap2': 2, 'quarter/gap2': 2, 'ytd/gap2': 1}
      AAPL  {'instant/gap1': 1, 'quarter/gap2': 2, 'ytd/gap2': 2}
      NVDA  {'instant/gap1': 1, 'instant/gap2': 1, 'quarter/gap2': 2, 'ytd/gap2': 1}
      XOM   {'instant/gap1': 2, 'quarter/gap2': 1, 'ytd/gap2': 2}
      PFE   {'instant/gap1': 1, 'instant/gap2': 2, 'quarter/gap2': 2}
    evidence sets per item: {1: 6, 2: 17, 3: 1, 4: 3, 6: 1, 8: 7, 12: 1, 18: 1, 21: 2, 27: 1}
    distinct gold chunks per item: {2: 6, 3: 17, 4: 4, 5: 1, 6: 7, 7: 1, 9: 1, 10: 2, 12: 1}
    flagged: 0
    spot-check (eval/candidates/comparison_spot_check.md): seeded ['cmp_0003', 'cmp_0015', 'cmp_0036', 'cmp_0040']; 12 gold chunks shown
    manifest fact records: 40 (later + earlier)
    wrote eval/candidates/comparison_candidates.jsonl sha256 e8f78af34061ba4f

`python -m scripts.sign_display`:

    exact-value gold spans of the 1713 eligible keys, (fact sign, printed): {('negative', 'parens'): 66, ('negative', 'plain'): 3, ('positive', 'parens'): 296, ('positive', 'plain'): 3964, ('zero', 'plain'): 13}
      by line item:
        capex                        {'positive printed negative': 99}
        cost_of_revenue              {'positive printed negative': 13}
        credit_loss_allowance        {'positive printed negative': 31}
        income_tax                   {'negative printed plain': 3}
        research_and_development     {'positive printed negative': 26}
        share_repurchases            {'positive printed negative': 127}
      positive keys with a gold span printed negative: 178; with every gold span so printed: 130
    xbrl_numeric candidates (160): items with a gold span whose printed sign disagrees with the fact: {'positive printed negative': 24, 'negative printed plain': 1}
      25 items
      ['xbrl_0001', 'xbrl_0004', 'xbrl_0007', 'xbrl_0020', 'xbrl_0022', 'xbrl_0023', 'xbrl_0029', 'xbrl_0039', 'xbrl_0041', 'xbrl_0050', 'xbrl_0057', 'xbrl_0060', 'xbrl_0068', 'xbrl_0073', 'xbrl_0086', 'xbrl_0093', 'xbrl_0110', 'xbrl_0112', 'xbrl_0119', 'xbrl_0121', 'xbrl_0122', 'xbrl_0127', 'xbrl_0143', 'xbrl_0151', 'xbrl_0157']
    comparison candidates (40): items with a gold span whose printed sign disagrees with the fact: {'positive printed negative': 5}
      5 items
      ['cmp_0002', 'cmp_0003', 'cmp_0007', 'cmp_0015', 'cmp_0035']

Two flagged items checked against the normalized text: xbrl_0001 (AAPL R&D
FY2023) is printed "(29,915)" in a reconciliation table of the FY2025 10-K
(chunk 592.0) and plain on the income statements; xbrl_0119 (PFE income tax
FY2024, -$28 million) is "(28)" on the income statement and "The tax benefit of
$28 million" in prose.

`make test`: 282 passed; `make lint` clean; both `--verify` runs: 0 mismatches.

## 2026-10-01 — LLM seeding supply measured (no model call, no item)

`python -m scripts.seed_supply`:

    parsed accessions: 90; chunks: 22354; candidate files: ['comparison_candidates.jsonl', 'xbrl_numeric_candidates.jsonl']
    
    chunks by (chunk_type, form): count, gold for a candidate, tokens
      prose 10-K   4067 gold    2  tokens min 28, p25 224, median 385, p75 459, max 500
      prose 10-Q   8422 gold    0  tokens min 34, p25 153, median 327, p75 446, max 500
      table 10-K   1973 gold   94  tokens min 72, p25 209, median 331, p75 475, max 500
      table 10-Q   7892 gold  345  tokens min 113, p25 252, median 395, p75 481, max 500
      gold chunks by candidate file: {'comparison_candidates': 162, 'xbrl_numeric_candidates': 326}; distinct 441
    
    strata (ticker, form_type, item_code, chunk_type): 270 non-empty
      table: 55 strata; chunks per stratum min 1, p25 8, median 25, p75 174, max 2101
      prose: 215 strata; chunks per stratum min 2, p25 3, median 9, p75 18, max 1546
    
    chunks by (form, item_code) x chunk_type: table (gold) / prose (gold)
      10-K II.8   table  1198 ( 79)   prose  1436 (  2)
      10-K II.7   table   470 (  0)   prose   837 (  0)
      10-K I.1A   table     0 (  0)   prose   709 (  0)
      10-K IV.15  table   228 ( 15)   prose   298 (  0)
      10-K I.1    table    26 (  0)   prose   354 (  0)
      10-K II.5   table    33 (  0)   prose    39 (  0)
      10-K I.1C   table     0 (  0)   prose    40 (  0)
      10-K II.9A  table     0 (  0)   prose    40 (  0)
      10-K I.2    table    12 (  0)   prose    24 (  0)
      10-K II.7A  table     3 (  0)   prose    30 (  0)
      10-K I.3    table     0 (  0)   prose    30 (  0)
      10-K IV.16  table     0 (  0)   prose    28 (  0)
      10-K III.10 table     0 (  0)   prose    25 (  0)
      10-K III.12 table     3 (  0)   prose    21 (  0)
      10-K II.9B  table     0 (  0)   prose    21 (  0)
      10-K II.6   table     0 (  0)   prose    18 (  0)
      10-K II.9   table     0 (  0)   prose    18 (  0)
      10-K III.11 table     0 (  0)   prose    18 (  0)
      10-K III.13 table     0 (  0)   prose    18 (  0)
      10-K III.14 table     0 (  0)   prose    18 (  0)
      10-K I.1B   table     0 (  0)   prose    15 (  0)
      10-K II.9C  table     0 (  0)   prose    15 (  0)
      10-K I.4    table     0 (  0)   prose    15 (  0)
      10-Q I.1    table  5075 (344)   prose  4042 (  0)
      10-Q I.2    table  2725 (  1)   prose  3468 (  0)
      10-Q II.1A  table     0 (  0)   prose   273 (  0)
      10-Q II.2   table    68 (  0)   prose   136 (  0)
      10-Q II.6   table    24 (  0)   prose   110 (  0)
      10-Q II.1   table     0 (  0)   prose    93 (  0)
      10-Q II.5   table     0 (  0)   prose    82 (  0)
      10-Q I.3    table     0 (  0)   prose    72 (  0)
      10-Q I.4    table     0 (  0)   prose    72 (  0)
      10-Q II.3   table     0 (  0)   prose    36 (  0)
      10-Q II.4   table     0 (  0)   prose    36 (  0)
      10-Q I.7A   table     0 (  0)   prose     2 (  0)
    
    per ticker: table (10-K / 10-Q) and prose (10-K / 10-Q); not gold for any candidate
      AAPL  table   173 /   270 (free 158 / 223)   prose   356 /   396 (free 356 / 396)
      XOM   table     0 /   476 (free 0 / 434)   prose     0 /   463 (free 0 / 463)
      BAC   table   901 /  2151 (free 886 / 2091)   prose  1291 /  1838 (free 1291 / 1838)
      PFE   table   366 /   674 (free 346 / 645)   prose  1008 /  1101 (free 1006 / 1101)
      TGT   table   197 /   309 (free 183 / 268)   prose   427 /   354 (free 427 / 354)
      JPM   table     0 /  3315 (free 0 / 3256)   prose     0 /  2992 (free 0 / 2992)
      COST  table   154 /   283 (free 139 / 247)   prose   388 /   480 (free 388 / 480)
      NVDA  table   182 /   414 (free 167 / 383)   prose   597 /   798 (free 597 / 798)

The candidates' gold sits almost entirely in statement tables (10-Q I.1 344,
10-K II.8 79, 10-K IV.15 15). MD&A tables (10-K II.7 470, 10-Q I.2 2,725) and all
prose but 2 chunks are untouched. JPM and BAC hold 6,367 of the 9,865 table
chunks. JPM and XOM have no 10-K chunks (F-66, F-70). F-59 extended to Stage 1
and the no-context filter and moved under Blocking Phase 3; F-88 records the 90
`llm_seeded` items.

## 2026-10-01 — LLM seeding: allocation measured, key-free filters built (no draw, no model call)

`eval_seeding` config block added (seeds, `per_ticker`, overdraw 2,
`min_body_tokens: null`, `near_duplicate_cosine: 0.92`). The two extra table
slots went to `pick_extra(tickers, 20261003, 2)` = AAPL, XOM, printed by the
script below and asserted by `test_extra_table_tickers_match_config`.

`python -m scripts.seed_supply`:

    parsed accessions: 90; chunks: 22354; candidate files: ['comparison_candidates.jsonl', 'xbrl_numeric_candidates.jsonl']
    
    chunks by (chunk_type, form): count, gold for a candidate, tokens
      prose 10-K   4067 gold    2  tokens min 28, p25 224, median 385, p75 459, max 500
      prose 10-Q   8422 gold    0  tokens min 34, p25 153, median 327, p75 446, max 500
      table 10-K   1973 gold   94  tokens min 72, p25 209, median 331, p75 475, max 500
      table 10-Q   7892 gold  345  tokens min 113, p25 252, median 395, p75 481, max 500
      gold chunks by candidate file: {'comparison_candidates': 162, 'xbrl_numeric_candidates': 326}; distinct 441
    
    strata (ticker, form_type, item_code, chunk_type): 270 non-empty
      table: 55 strata; chunks per stratum min 1, p25 8, median 25, p75 174, max 2101
      prose: 215 strata; chunks per stratum min 2, p25 3, median 9, p75 18, max 1546
    
    chunks by (form, item_code) x chunk_type: table (gold) / prose (gold)
      10-K II.8   table  1198 ( 79)   prose  1436 (  2)
      10-K II.7   table   470 (  0)   prose   837 (  0)
      10-K I.1A   table     0 (  0)   prose   709 (  0)
      10-K IV.15  table   228 ( 15)   prose   298 (  0)
      10-K I.1    table    26 (  0)   prose   354 (  0)
      10-K II.5   table    33 (  0)   prose    39 (  0)
      10-K I.1C   table     0 (  0)   prose    40 (  0)
      10-K II.9A  table     0 (  0)   prose    40 (  0)
      10-K I.2    table    12 (  0)   prose    24 (  0)
      10-K II.7A  table     3 (  0)   prose    30 (  0)
      10-K I.3    table     0 (  0)   prose    30 (  0)
      10-K IV.16  table     0 (  0)   prose    28 (  0)
      10-K III.10 table     0 (  0)   prose    25 (  0)
      10-K III.12 table     3 (  0)   prose    21 (  0)
      10-K II.9B  table     0 (  0)   prose    21 (  0)
      10-K II.6   table     0 (  0)   prose    18 (  0)
      10-K II.9   table     0 (  0)   prose    18 (  0)
      10-K III.11 table     0 (  0)   prose    18 (  0)
      10-K III.13 table     0 (  0)   prose    18 (  0)
      10-K III.14 table     0 (  0)   prose    18 (  0)
      10-K I.1B   table     0 (  0)   prose    15 (  0)
      10-K I.4    table     0 (  0)   prose    15 (  0)
      10-K II.9C  table     0 (  0)   prose    15 (  0)
      10-Q I.1    table  5075 (344)   prose  4042 (  0)
      10-Q I.2    table  2725 (  1)   prose  3468 (  0)
      10-Q II.1A  table     0 (  0)   prose   273 (  0)
      10-Q II.2   table    68 (  0)   prose   136 (  0)
      10-Q II.6   table    24 (  0)   prose   110 (  0)
      10-Q II.1   table     0 (  0)   prose    93 (  0)
      10-Q II.5   table     0 (  0)   prose    82 (  0)
      10-Q I.3    table     0 (  0)   prose    72 (  0)
      10-Q I.4    table     0 (  0)   prose    72 (  0)
      10-Q II.3   table     0 (  0)   prose    36 (  0)
      10-Q II.4   table     0 (  0)   prose    36 (  0)
      10-Q I.7A   table     0 (  0)   prose     2 (  0)
    
    per ticker: table (10-K / 10-Q) and prose (10-K / 10-Q); not gold for any candidate
      JPM   table     0 /  3315 (free 0 / 3256)   prose     0 /  2992 (free 0 / 2992)
      TGT   table   197 /   309 (free 183 / 268)   prose   427 /   354 (free 427 / 354)
      XOM   table     0 /   476 (free 0 / 434)   prose     0 /   463 (free 0 / 463)
      BAC   table   901 /  2151 (free 886 / 2091)   prose  1291 /  1838 (free 1291 / 1838)
      PFE   table   366 /   674 (free 346 / 645)   prose  1008 /  1101 (free 1006 / 1101)
      AAPL  table   173 /   270 (free 158 / 223)   prose   356 /   396 (free 356 / 396)
      COST  table   154 /   283 (free 139 / 247)   prose   388 /   480 (free 388 / 480)
      NVDA  table   182 /   414 (free 167 / 383)   prose   597 /   798 (free 597 / 798)
    
    config allocation:
      table: total 50, sum 50, overdraw 2, per_ticker {'COST': 6, 'TGT': 6, 'JPM': 6, 'BAC': 6, 'AAPL': 7, 'NVDA': 6, 'XOM': 7, 'PFE': 6}
      synthesis: total 40, sum 40, overdraw 2, per_ticker {'COST': 5, 'TGT': 5, 'JPM': 5, 'BAC': 5, 'AAPL': 5, 'NVDA': 5, 'XOM': 5, 'PFE': 5}
      table extra slots: pick_extra(seed 20261003) = ['AAPL', 'XOM']; config gives 7 to ['AAPL', 'XOM']; match
    
    excluded as already gold, by stratum (ticker, form, item_code, chunk_type): 441 in 16 strata
      AAPL 10-K II.8 table: 15
      AAPL 10-Q I.1 table: 47
      BAC 10-K II.8 table: 15
      BAC 10-Q I.1 table: 60
      COST 10-K II.8 table: 15
      COST 10-Q I.1 table: 36
      JPM 10-Q I.1 table: 59
      NVDA 10-K IV.15 table: 15
      NVDA 10-Q I.1 table: 31
      PFE 10-K II.8 prose: 2
      PFE 10-K II.8 table: 20
      PFE 10-Q I.1 table: 29
      TGT 10-K II.8 table: 14
      TGT 10-Q I.1 table: 41
      XOM 10-Q I.1 table: 41
      XOM 10-Q I.2 table: 1
    
    prose body tokens (header excluded), 12489 chunks: {'0-9': 315, '10-19': 380, '20-29': 239, '30-39': 299, '40-49': 254, '50-59': 230, '60-79': 421, '80-99': 352, '100-149': 950, '150-199': 775, '200-500': 8274}
      below the proposed 40: 1233; at or above: 11256
      just below the cut (141 chunks; every 23th shown):
         35 0000019617-23-000524:328.0:330.0: '(a)Predominantly recognized in CIB, CB and Corporate.\nThe following table provides information on net interest income, net yield, and noninterest reve'
         36 0000019617-24-000453:1267.0:1270.0: 'The Notes to Consolidated Financial Statements (unaudited) are an integral part of these statements.\nJPMorgan Chase & Co.\nConsolidated statements of c'
         36 0000078003-24-000039:699.0:700.0: '(k)January 2024 filing date refers to application for conversion from accelerated to full approval.\nThe following provides information about additiona'
         36 0000909832-25-000101:728.0:729.0: 'Disaggregated Revenue\nThe following table summarizes net sales by merchandise category; sales from e-commerce sites and business centers have been all'
         37 0000070858-24-000122:1651.0:1651.0: 'The table below presents the December 31, 2022 and 2021 carrying value for consumer real estate loans that were modified in a TDR during 2022 and 2021'
         38 0001628280-26-054343:1548.0:1549.0: 'Contractual maturities and yields\nThe following table presents the amortized cost and estimated fair value at June 30, 2026, of JPMorganChase’s invest'
      just above the cut (142 chunks; every 23th shown):
         40 0000019617-23-000524:1392.0:1395.0: 'The Notes to Consolidated Financial Statements (unaudited) are an integral part of these statements.\nJPMorgan Chase & Co.\nConsolidated statements of c'
         40 0000078003-25-000114:154.0:155.0: '(a)Taxes are not provided for foreign currency translation adjustments relating to investments in international subsidiaries that are expected to be h'
         40 0001045810-24-000029:892.0:893.0: 'Stock-based compensation capitalized in inventories was not significant during fiscal years 2024, 2023, and 2022.\nThe following is a summary of equity'
         42 0000027419-23-000052:273.0:274.0: 'Item 1A. Risk Factors\nThere have been no material changes to the risk factors described in Part I, Item 1A, Risk Factors of our Form 10-K for the fisc'
         43 0000027419-23-000052:271.0:272.0: 'Item 1. Legal Proceedings\nFor the quarterly period ended October 28, 2023, no response is required under Item 103 of Regulation S-K, nor have there be'
         43 0000070858-26-000157:1961.0:1962.0: '(1) Income is related to the tax jurisdiction of the legal entity’s principal place of business.\nThe components of income tax expense for 2025, 2024 a'
    
    allocation, table (table chunks, gold excluded): 9426 chunks
      JPM   x1 ( 6 of  3256): 10-Q I.1 4, 10-Q I.2 2
      JPM   x2 (12 of  3256): 10-Q I.1 8, 10-Q I.2 4
      TGT   x1 ( 6 of   451): 10-K II.8 2, 10-Q I.1 2, 10-Q I.2 2
      TGT   x2 (12 of   451): 10-K II.7 1, 10-K II.8 3, 10-Q I.1 4, 10-Q I.2 4
      XOM   x1 ( 7 of   434): 10-Q I.1 4, 10-Q I.2 3
      XOM   x2 (14 of   434): 10-Q I.1 9, 10-Q I.2 5
      BAC   x1 ( 6 of  2977): 10-K II.7 1, 10-K II.8 1, 10-Q I.1 2, 10-Q I.2 2
      BAC   x2 (12 of  2977): 10-K II.7 1, 10-K II.8 2, 10-Q I.1 5, 10-Q I.2 4
      PFE   x1 ( 6 of   991): 10-K II.8 2, 10-Q I.1 3, 10-Q I.2 1
      PFE   x2 (12 of   991): 10-K II.7 1, 10-K II.8 3, 10-Q I.1 5, 10-Q I.2 3
      AAPL  x1 ( 7 of   381): 10-K II.8 2, 10-K IV.15 1, 10-Q I.1 3, 10-Q I.2 1
      AAPL  x2 (14 of   381): 10-K II.7 1, 10-K II.8 4, 10-K IV.15 1, 10-Q I.1 6, 10-Q I.2 2
      COST  x1 ( 6 of   386): 10-K II.8 2, 10-Q I.1 3, 10-Q I.2 1
      COST  x2 (12 of   386): 10-K I.1 1, 10-K II.7 1, 10-K II.8 3, 10-Q I.1 5, 10-Q I.2 2
      NVDA  x1 ( 6 of   550): 10-K IV.15 2, 10-Q I.1 3, 10-Q I.2 1
      NVDA  x2 (12 of   550): 10-K II.7 1, 10-K IV.15 3, 10-Q I.1 6, 10-Q I.2 2
      tickers with zero MD&A slots at x1: none
      tickers with zero MD&A slots at x2: none
    
    allocation, synthesis (prose chunks, gold excluded): 12487 chunks
      JPM   x1 ( 5 of  2992): 10-Q I.1 3, 10-Q I.2 2
      JPM   x2 (10 of  2992): 10-Q I.1 5, 10-Q I.2 5
      TGT   x1 ( 5 of   781): 10-K I.1A 1, 10-K II.7 1, 10-K II.8 1, 10-Q I.1 1, 10-Q I.2 1
      TGT   x2 (10 of   781): 10-K I.1 1, 10-K I.1A 1, 10-K II.7 1, 10-K II.8 2, 10-K IV.15 1, 10-Q I.1 2, 10-Q I.2 2
      XOM   x1 ( 5 of   463): 10-Q I.1 2, 10-Q I.2 3
      XOM   x2 (10 of   463): 10-Q I.1 4, 10-Q I.2 5, 10-Q II.2 1
      BAC   x1 ( 5 of  3129): 10-K II.7 1, 10-K II.8 1, 10-Q I.1 2, 10-Q I.2 1
      BAC   x2 (10 of  3129): 10-K I.1A 1, 10-K II.7 1, 10-K II.8 2, 10-Q I.1 3, 10-Q I.2 3
      PFE   x1 ( 5 of  2107): 10-K II.7 1, 10-K II.8 1, 10-Q I.1 2, 10-Q I.2 1
      PFE   x2 (10 of  2107): 10-K I.1 1, 10-K I.1A 1, 10-K II.7 1, 10-K II.8 2, 10-Q I.1 3, 10-Q I.2 2
      AAPL  x1 ( 5 of   752): 10-K I.1A 1, 10-K II.8 1, 10-Q I.1 1, 10-Q I.2 1, 10-Q II.1A 1
      AAPL  x2 (10 of   752): 10-K I.1A 1, 10-K II.7 1, 10-K II.8 2, 10-Q I.1 2, 10-Q I.2 2, 10-Q II.1 1, 10-Q II.1A 1
      COST  x1 ( 5 of   868): 10-K I.1A 1, 10-K II.7 1, 10-K II.8 1, 10-Q I.1 1, 10-Q I.2 1
      COST  x2 (10 of   868): 10-K I.1 1, 10-K I.1A 1, 10-K II.7 1, 10-K II.8 2, 10-Q I.1 3, 10-Q I.2 2
      NVDA  x1 ( 5 of  1395): 10-K I.1A 1, 10-K IV.15 1, 10-Q I.1 1, 10-Q I.2 1, 10-Q II.1A 1
      NVDA  x2 (10 of  1395): 10-K I.1 1, 10-K I.1A 1, 10-K II.7 1, 10-K IV.15 2, 10-Q I.1 3, 10-Q I.2 1, 10-Q II.1A 1
      tickers with zero MD&A slots at x1: none
      tickers with zero MD&A slots at x2: none
    
    allocation, synthesis (prose chunks, gold excluded, body tokens >= 40): 11254 chunks
      JPM   x1 ( 5 of  2779): 10-Q I.1 3, 10-Q I.2 2
      JPM   x2 (10 of  2779): 10-Q I.1 5, 10-Q I.2 5
      TGT   x1 ( 5 of   651): 10-K I.1A 1, 10-K II.7 1, 10-K II.8 1, 10-Q I.1 1, 10-Q I.2 1
      TGT   x2 (10 of   651): 10-K I.1 1, 10-K I.1A 1, 10-K II.7 1, 10-K II.8 2, 10-K IV.15 1, 10-Q I.1 1, 10-Q I.2 2, 10-Q II.6 1
      XOM   x1 ( 5 of   322): 10-Q I.1 2, 10-Q I.2 3
      XOM   x2 (10 of   322): 10-Q I.1 3, 10-Q I.2 6, 10-Q II.6 1
      BAC   x1 ( 5 of  2976): 10-K II.7 1, 10-K II.8 1, 10-Q I.1 1, 10-Q I.2 2
      BAC   x2 (10 of  2976): 10-K I.1A 1, 10-K II.7 1, 10-K II.8 2, 10-Q I.1 3, 10-Q I.2 3
      PFE   x1 ( 5 of  1944): 10-K I.1 1, 10-K II.7 1, 10-K II.8 1, 10-Q I.1 1, 10-Q I.2 1
      PFE   x2 (10 of  1944): 10-K I.1 1, 10-K I.1A 1, 10-K II.7 1, 10-K II.8 2, 10-Q I.1 3, 10-Q I.2 2
      AAPL  x1 ( 5 of   629): 10-K I.1A 1, 10-K II.8 1, 10-Q I.1 1, 10-Q I.2 1, 10-Q II.1A 1
      AAPL  x2 (10 of   629): 10-K I.1A 2, 10-K II.7 1, 10-K II.8 2, 10-Q I.1 2, 10-Q I.2 2, 10-Q II.1A 1
      COST  x1 ( 5 of   706): 10-K I.1A 1, 10-K II.7 1, 10-K II.8 1, 10-Q I.1 1, 10-Q I.2 1
      COST  x2 (10 of   706): 10-K I.1 1, 10-K I.1A 1, 10-K II.7 1, 10-K II.8 2, 10-Q I.1 2, 10-Q I.2 3
      NVDA  x1 ( 5 of  1247): 10-K I.1A 1, 10-K IV.15 1, 10-Q I.1 1, 10-Q I.2 1, 10-Q II.1A 1
      NVDA  x2 (10 of  1247): 10-K I.1 1, 10-K I.1A 2, 10-K II.7 1, 10-K IV.15 1, 10-Q I.1 2, 10-Q I.2 1, 10-Q II.1A 2
      tickers with zero MD&A slots at x1: none
      tickers with zero MD&A slots at x2: none

`eval/generate/seeding.py`: `allocate`, `pick_extra`, and the key-free Stage 2
filters and review aids. They are tested in `tests/unit/test_seeding.py` (12
tests) on 7 real chunks in `tests/fixtures/seed_chunks.json` (`python -m
scripts.seed_supply --write-fixture`, stamped with the freeze's parser and
chunker versions). `make test`: 294 passed; `make lint` clean.

F-90, found while checking the scale rule (psql over `chunks`, table chunks with
a non-NULL `unit_scale`): 153 of 9,221 contain "except ... per share" in their
text, 0 have "except" in the header line; JPM's Note 18 Earnings per share table
(0000019617-24-000326:1892.0:1892.0) has `unit_scale = millions`. Logged, not fixed.

## 2026-10-01 — Seeding: scale, floor, prompt applied (no draw yet)

`mixed_signals` / `attach_scale` (F-90), `min_body_tokens: 40` in config (the
script reads it; its constant is gone), `sign_only` on `answer_in_quote` drops,
`answer_flags`, `eval/generate/prompts/seed_v1.txt` with `render_prompt` and
`prompt_sha`. Fixture regenerated with JPM Note 18 and each chunk's span scales
(8 chunks). F-90's counts are now printed by the script, replacing the ad hoc
psql figures of the previous entry ("except ... per share" is 153 by both). The
heading counts replace an ad hoc run that used a looser one-line rule.

`python -m scripts.seed_supply`:

    parsed accessions: 90; chunks: 22354; candidate files: ['comparison_candidates.jsonl', 'xbrl_numeric_candidates.jsonl']
    
    chunks by (chunk_type, form): count, gold for a candidate, tokens
      prose 10-K   4067 gold    2  tokens min 28, p25 224, median 385, p75 459, max 500
      prose 10-Q   8422 gold    0  tokens min 34, p25 153, median 327, p75 446, max 500
      table 10-K   1973 gold   94  tokens min 72, p25 209, median 331, p75 475, max 500
      table 10-Q   7892 gold  345  tokens min 113, p25 252, median 395, p75 481, max 500
      gold chunks by candidate file: {'comparison_candidates': 162, 'xbrl_numeric_candidates': 326}; distinct 441
    
    strata (ticker, form_type, item_code, chunk_type): 270 non-empty
      table: 55 strata; chunks per stratum min 1, p25 8, median 25, p75 174, max 2101
      prose: 215 strata; chunks per stratum min 2, p25 3, median 9, p75 18, max 1546
    
    chunks by (form, item_code) x chunk_type: table (gold) / prose (gold)
      10-K II.8   table  1198 ( 79)   prose  1436 (  2)
      10-K II.7   table   470 (  0)   prose   837 (  0)
      10-K I.1A   table     0 (  0)   prose   709 (  0)
      10-K IV.15  table   228 ( 15)   prose   298 (  0)
      10-K I.1    table    26 (  0)   prose   354 (  0)
      10-K II.5   table    33 (  0)   prose    39 (  0)
      10-K I.1C   table     0 (  0)   prose    40 (  0)
      10-K II.9A  table     0 (  0)   prose    40 (  0)
      10-K I.2    table    12 (  0)   prose    24 (  0)
      10-K II.7A  table     3 (  0)   prose    30 (  0)
      10-K I.3    table     0 (  0)   prose    30 (  0)
      10-K IV.16  table     0 (  0)   prose    28 (  0)
      10-K III.10 table     0 (  0)   prose    25 (  0)
      10-K III.12 table     3 (  0)   prose    21 (  0)
      10-K II.9B  table     0 (  0)   prose    21 (  0)
      10-K II.6   table     0 (  0)   prose    18 (  0)
      10-K II.9   table     0 (  0)   prose    18 (  0)
      10-K III.11 table     0 (  0)   prose    18 (  0)
      10-K III.13 table     0 (  0)   prose    18 (  0)
      10-K III.14 table     0 (  0)   prose    18 (  0)
      10-K I.1B   table     0 (  0)   prose    15 (  0)
      10-K I.4    table     0 (  0)   prose    15 (  0)
      10-K II.9C  table     0 (  0)   prose    15 (  0)
      10-Q I.1    table  5075 (344)   prose  4042 (  0)
      10-Q I.2    table  2725 (  1)   prose  3468 (  0)
      10-Q II.1A  table     0 (  0)   prose   273 (  0)
      10-Q II.2   table    68 (  0)   prose   136 (  0)
      10-Q II.6   table    24 (  0)   prose   110 (  0)
      10-Q II.1   table     0 (  0)   prose    93 (  0)
      10-Q II.5   table     0 (  0)   prose    82 (  0)
      10-Q I.3    table     0 (  0)   prose    72 (  0)
      10-Q I.4    table     0 (  0)   prose    72 (  0)
      10-Q II.3   table     0 (  0)   prose    36 (  0)
      10-Q II.4   table     0 (  0)   prose    36 (  0)
      10-Q I.7A   table     0 (  0)   prose     2 (  0)
    
    per ticker: table (10-K / 10-Q) and prose (10-K / 10-Q); not gold for any candidate
      JPM   table     0 /  3315 (free 0 / 3256)   prose     0 /  2992 (free 0 / 2992)
      TGT   table   197 /   309 (free 183 / 268)   prose   427 /   354 (free 427 / 354)
      XOM   table     0 /   476 (free 0 / 434)   prose     0 /   463 (free 0 / 463)
      BAC   table   901 /  2151 (free 886 / 2091)   prose  1291 /  1838 (free 1291 / 1838)
      PFE   table   366 /   674 (free 346 / 645)   prose  1008 /  1101 (free 1006 / 1101)
      AAPL  table   173 /   270 (free 158 / 223)   prose   356 /   396 (free 356 / 396)
      COST  table   154 /   283 (free 139 / 247)   prose   388 /   480 (free 388 / 480)
      NVDA  table   182 /   414 (free 167 / 383)   prose   597 /   798 (free 597 / 798)
    
    config allocation:
      table: total 50, sum 50, overdraw 2, per_ticker {'COST': 6, 'TGT': 6, 'JPM': 6, 'BAC': 6, 'AAPL': 7, 'NVDA': 6, 'XOM': 7, 'PFE': 6}
      synthesis: total 40, sum 40, overdraw 2, per_ticker {'COST': 5, 'TGT': 5, 'JPM': 5, 'BAC': 5, 'AAPL': 5, 'NVDA': 5, 'XOM': 5, 'PFE': 5}
      table extra slots: pick_extra(seed 20261003) = ['AAPL', 'XOM']; config gives 7 to ['AAPL', 'XOM']; match
    
    excluded as already gold, by stratum (ticker, form, item_code, chunk_type): 441 in 16 strata
      AAPL 10-K II.8 table: 15
      AAPL 10-Q I.1 table: 47
      BAC 10-K II.8 table: 15
      BAC 10-Q I.1 table: 60
      COST 10-K II.8 table: 15
      COST 10-Q I.1 table: 36
      JPM 10-Q I.1 table: 59
      NVDA 10-K IV.15 table: 15
      NVDA 10-Q I.1 table: 31
      PFE 10-K II.8 prose: 2
      PFE 10-K II.8 table: 20
      PFE 10-Q I.1 table: 29
      TGT 10-K II.8 table: 14
      TGT 10-Q I.1 table: 41
      XOM 10-Q I.1 table: 41
      XOM 10-Q I.2 table: 1
    
    prose body tokens (header excluded), 12489 chunks: {'0-9': 315, '10-19': 380, '20-29': 239, '30-39': 299, '40-49': 254, '50-59': 230, '60-79': 421, '80-99': 352, '100-149': 950, '150-199': 775, '200-500': 8274}
      below min_body_tokens 40 (config): 1233; at or above: 11256
      per ticker: prose / below the floor (share) / of which one-line headings / headings followed by a table chunk
        JPM    2992  213 (7%)    0    0
        TGT     781  130 (17%)   32   29
        XOM     463  141 (30%)  102  101
        BAC    3129  153 (5%)   22   19
        PFE    2109  163 (8%)   34   31
        AAPL    752  123 (16%)   17   12
        COST    868  162 (19%)    3    0
        NVDA   1395  148 (11%)   20   17
      just below the cut (141 chunks; every 23th shown):
         35 0000019617-23-000524:328.0:330.0: '(a)Predominantly recognized in CIB, CB and Corporate.\nThe following table provides information on net interest income, net yield, and noninterest reve'
         36 0000019617-24-000453:1267.0:1270.0: 'The Notes to Consolidated Financial Statements (unaudited) are an integral part of these statements.\nJPMorgan Chase & Co.\nConsolidated statements of c'
         36 0000078003-24-000039:699.0:700.0: '(k)January 2024 filing date refers to application for conversion from accelerated to full approval.\nThe following provides information about additiona'
         36 0000909832-25-000101:728.0:729.0: 'Disaggregated Revenue\nThe following table summarizes net sales by merchandise category; sales from e-commerce sites and business centers have been all'
         37 0000070858-24-000122:1651.0:1651.0: 'The table below presents the December 31, 2022 and 2021 carrying value for consumer real estate loans that were modified in a TDR during 2022 and 2021'
         38 0001628280-26-054343:1548.0:1549.0: 'Contractual maturities and yields\nThe following table presents the amortized cost and estimated fair value at June 30, 2026, of JPMorganChase’s invest'
      just above the cut (142 chunks; every 23th shown):
         40 0000019617-23-000524:1392.0:1395.0: 'The Notes to Consolidated Financial Statements (unaudited) are an integral part of these statements.\nJPMorgan Chase & Co.\nConsolidated statements of c'
         40 0000078003-25-000114:154.0:155.0: '(a)Taxes are not provided for foreign currency translation adjustments relating to investments in international subsidiaries that are expected to be h'
         40 0001045810-24-000029:892.0:893.0: 'Stock-based compensation capitalized in inventories was not significant during fiscal years 2024, 2023, and 2022.\nThe following is a summary of equity'
         42 0000027419-23-000052:273.0:274.0: 'Item 1A. Risk Factors\nThere have been no material changes to the risk factors described in Part I, Item 1A, Risk Factors of our Form 10-K for the fisc'
         43 0000027419-23-000052:271.0:272.0: 'Item 1. Legal Proceedings\nFor the quarterly period ended October 28, 2023, no response is required under Item 103 of Regulation S-K, nor have there be'
         43 0000070858-26-000157:1961.0:1962.0: '(1) Income is related to the tax jurisdiction of the legal entity’s principal place of business.\nThe components of income tax expense for 2025, 2024 a'
    
    scale signals (F-90), table chunks with a unit_scale: 9221
      per ticker: 'except ... per share' / scale-exception clause / tagged span at another ix scale / union
        JPM    3240:   19  260   407   575
        TGT     356:    3    3    51    51
        XOM     476:    0    0    26    26
        BAC    2929:    0    0   270   270
        PFE     977:   75   75   112   183
        AAPL    387:    0    0    57    57
        COST    302:    0    0   100   100
        NVDA    554:   56   62   112   124
        total  9221:  153  400  1135  1386
    
    allocation, table (table chunks, gold excluded): 9426 chunks
      JPM   x1 ( 6 of  3256): 10-Q I.1 4, 10-Q I.2 2
      JPM   x2 (12 of  3256): 10-Q I.1 8, 10-Q I.2 4
      TGT   x1 ( 6 of   451): 10-K II.8 2, 10-Q I.1 2, 10-Q I.2 2
      TGT   x2 (12 of   451): 10-K II.7 1, 10-K II.8 3, 10-Q I.1 4, 10-Q I.2 4
      XOM   x1 ( 7 of   434): 10-Q I.1 4, 10-Q I.2 3
      XOM   x2 (14 of   434): 10-Q I.1 9, 10-Q I.2 5
      BAC   x1 ( 6 of  2977): 10-K II.7 1, 10-K II.8 1, 10-Q I.1 2, 10-Q I.2 2
      BAC   x2 (12 of  2977): 10-K II.7 1, 10-K II.8 2, 10-Q I.1 5, 10-Q I.2 4
      PFE   x1 ( 6 of   991): 10-K II.8 2, 10-Q I.1 3, 10-Q I.2 1
      PFE   x2 (12 of   991): 10-K II.7 1, 10-K II.8 3, 10-Q I.1 5, 10-Q I.2 3
      AAPL  x1 ( 7 of   381): 10-K II.8 2, 10-K IV.15 1, 10-Q I.1 3, 10-Q I.2 1
      AAPL  x2 (14 of   381): 10-K II.7 1, 10-K II.8 4, 10-K IV.15 1, 10-Q I.1 6, 10-Q I.2 2
      COST  x1 ( 6 of   386): 10-K II.8 2, 10-Q I.1 3, 10-Q I.2 1
      COST  x2 (12 of   386): 10-K I.1 1, 10-K II.7 1, 10-K II.8 3, 10-Q I.1 5, 10-Q I.2 2
      NVDA  x1 ( 6 of   550): 10-K IV.15 2, 10-Q I.1 3, 10-Q I.2 1
      NVDA  x2 (12 of   550): 10-K II.7 1, 10-K IV.15 3, 10-Q I.1 6, 10-Q I.2 2
      tickers with zero MD&A slots at x1: none
      tickers with zero MD&A slots at x2: none
    
    allocation, synthesis (prose chunks, gold excluded, body tokens >= 40): 11254 chunks
      JPM   x1 ( 5 of  2779): 10-Q I.1 3, 10-Q I.2 2
      JPM   x2 (10 of  2779): 10-Q I.1 5, 10-Q I.2 5
      TGT   x1 ( 5 of   651): 10-K I.1A 1, 10-K II.7 1, 10-K II.8 1, 10-Q I.1 1, 10-Q I.2 1
      TGT   x2 (10 of   651): 10-K I.1 1, 10-K I.1A 1, 10-K II.7 1, 10-K II.8 2, 10-K IV.15 1, 10-Q I.1 1, 10-Q I.2 2, 10-Q II.6 1
      XOM   x1 ( 5 of   322): 10-Q I.1 2, 10-Q I.2 3
      XOM   x2 (10 of   322): 10-Q I.1 3, 10-Q I.2 6, 10-Q II.6 1
      BAC   x1 ( 5 of  2976): 10-K II.7 1, 10-K II.8 1, 10-Q I.1 1, 10-Q I.2 2
      BAC   x2 (10 of  2976): 10-K I.1A 1, 10-K II.7 1, 10-K II.8 2, 10-Q I.1 3, 10-Q I.2 3
      PFE   x1 ( 5 of  1944): 10-K I.1 1, 10-K II.7 1, 10-K II.8 1, 10-Q I.1 1, 10-Q I.2 1
      PFE   x2 (10 of  1944): 10-K I.1 1, 10-K I.1A 1, 10-K II.7 1, 10-K II.8 2, 10-Q I.1 3, 10-Q I.2 2
      AAPL  x1 ( 5 of   629): 10-K I.1A 1, 10-K II.8 1, 10-Q I.1 1, 10-Q I.2 1, 10-Q II.1A 1
      AAPL  x2 (10 of   629): 10-K I.1A 2, 10-K II.7 1, 10-K II.8 2, 10-Q I.1 2, 10-Q I.2 2, 10-Q II.1A 1
      COST  x1 ( 5 of   706): 10-K I.1A 1, 10-K II.7 1, 10-K II.8 1, 10-Q I.1 1, 10-Q I.2 1
      COST  x2 (10 of   706): 10-K I.1 1, 10-K I.1A 1, 10-K II.7 1, 10-K II.8 2, 10-Q I.1 2, 10-Q I.2 3
      NVDA  x1 ( 5 of  1247): 10-K I.1A 1, 10-K IV.15 1, 10-Q I.1 1, 10-Q I.2 1, 10-Q II.1A 1
      NVDA  x2 (10 of  1247): 10-K I.1 1, 10-K I.1A 2, 10-K II.7 1, 10-K IV.15 1, 10-Q I.1 2, 10-Q I.2 1, 10-Q II.1A 2
      tickers with zero MD&A slots at x1: none
      tickers with zero MD&A slots at x2: none

`make test`: 297 passed; `make lint` clean.

## 2026-10-01 — OWNER DECISION: claude_cli dev backend; Phase 2 exit met on it (dev run)

`api/generate/claude_cli.py`, `generation.backend: claude_cli` (default) and
`cli_system_prompt` in config; `generate` dispatches, `generate_api` is the
unchanged `anthropic_api` path; `Answer.backend` is printed by the baseline.
`tests/unit/test_claude_cli.py` checks the command, the child environment and
parsing against `tests/fixtures/claude_cli_response.json`, one real response
(prompt "Reply with the single word: ready", `claude-haiku-4-5-20251001`,
`usage` 465 in / 41 out, 34 of them thinking tokens; no email in it). No live
call in pytest. `make test`: 303 passed.

Live smoke run, the Phase 2 exit question
(`python -m api.query.baseline "What were Apple's total net sales in fiscal 2025?"`,
14.8 s wall):

    question: What were Apple's total net sales in fiscal 2025?
    plan: ->  Index Scan using chunks_hnsw on chunks  (cost=1181.91..81867.08 rows=22354 width=407)
      0.1714  0000320193-25-000057:176.0:188.0  [Apple Inc. (AAPL) | 10-Q | Q2 FY2025 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations]
      0.1794  0000320193-25-000008:174.0:186.0  [Apple Inc. (AAPL) | 10-Q | Q1 FY2025 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations]
      0.1934  0000320193-25-000079:305.0:318.0  [Apple Inc. (AAPL) | 10-K | FY2025 | Item 7: Management’s Discussion and Analysis of Financial Condition and Results of Operations]
      0.1970  0000320193-25-000079:456.0:456.0  [Apple Inc. (AAPL) | 10-K | FY2025 | Item 8: Financial Statements and Supplementary Data]
      0.1974  0000320193-26-000013:181.0:193.0  [Apple Inc. (AAPL) | 10-Q | Q2 FY2026 | Part I, Item 2: Management’s Discussion and Analysis of Financial Condition and Results of Operations]
    backend: claude_cli
    model: claude-haiku-4-5-20251001
    usage: input_tokens=2124 output_tokens=328
    answer:
    # Apple's Total Net Sales in Fiscal 2025
    
    According to Apple's 10-K filing for fiscal 2025, **Apple's total net sales in fiscal 2025 were $416,161 million ($416.161 billion)**.
    
    This represents an increase from fiscal 2024's total net sales of $391,035 million.
    
    The breakdown by product category was:
    - **iPhone**: $209,586 million
    - **Services**: $109,158 million
    - **Wearables, Home and Accessories**: $35,686 million
    - **Mac**: $33,708 million
    - **iPad**: $28,023 million

The headline figure matches `xbrl_facts` (AAPL
`RevenueFromContractWithCustomerExcludingAssessedTax`, 2024-09-29..2025-09-27,
0000320193-25-000079: 416161000000); the product breakdown was not checked. This
is a development run on `claude_cli`: not a baseline, not publishable (F-59 stays
open for `anthropic_api`).

## 2026-10-01 — Seeding chunk draw (key-free, no model call)

`draw_chunks` (pure, `eval/generate/seeding.py`): per ticker, slots at 1x and at
the configured 2x by largest remainder over (form, item_code); within a stratum
a shuffle of the sorted ids seeded by (seed, ticker, form, item). Tested on the
fixture chunks. `python -m scripts.seed_draw`:

    table: eligible 9426; excluded gold 439, floor 0; slots 1x 50; drawn 100
      strata with fewer draws than 1x slots: none
      strata with no spare draw (drawn == 1x slots): 2 ['AAPL 10-K IV.15', 'BAC 10-K II.7']
      AAPL  (1x/drawn) 10-K II.7 0/1, 10-K II.8 2/4, 10-K IV.15 1/1, 10-Q I.1 3/6, 10-Q I.2 1/2
      BAC   (1x/drawn) 10-K II.7 1/1, 10-K II.8 1/2, 10-Q I.1 2/5, 10-Q I.2 2/4
      COST  (1x/drawn) 10-K I.1 0/1, 10-K II.7 0/1, 10-K II.8 2/3, 10-Q I.1 3/5, 10-Q I.2 1/2
      JPM   (1x/drawn) 10-Q I.1 4/8, 10-Q I.2 2/4
      NVDA  (1x/drawn) 10-K II.7 0/1, 10-K IV.15 2/3, 10-Q I.1 3/6, 10-Q I.2 1/2
      PFE   (1x/drawn) 10-K II.7 0/1, 10-K II.8 2/3, 10-Q I.1 3/5, 10-Q I.2 1/3
      TGT   (1x/drawn) 10-K II.7 0/1, 10-K II.8 2/3, 10-Q I.1 2/4, 10-Q I.2 2/4
      XOM   (1x/drawn) 10-Q I.1 4/9, 10-Q I.2 3/5
    synthesis: eligible 11254; excluded gold 2, floor 1233; slots 1x 40; drawn 80
      strata with fewer draws than 1x slots: none
      strata with no spare draw (drawn == 1x slots): 11 ['AAPL 10-Q II.1A', 'BAC 10-K II.7', 'COST 10-K I.1A', 'COST 10-K II.7', 'NVDA 10-K IV.15', 'NVDA 10-Q I.2', 'PFE 10-K I.1', 'PFE 10-K II.7', 'TGT 10-K I.1A', 'TGT 10-K II.7', 'TGT 10-Q I.1']
      AAPL  (1x/drawn) 10-K I.1A 1/2, 10-K II.7 0/1, 10-K II.8 1/2, 10-Q I.1 1/2, 10-Q I.2 1/2, 10-Q II.1A 1/1
      BAC   (1x/drawn) 10-K I.1A 0/1, 10-K II.7 1/1, 10-K II.8 1/2, 10-Q I.1 1/3, 10-Q I.2 2/3
      COST  (1x/drawn) 10-K I.1 0/1, 10-K I.1A 1/1, 10-K II.7 1/1, 10-K II.8 1/2, 10-Q I.1 1/2, 10-Q I.2 1/3
      JPM   (1x/drawn) 10-Q I.1 3/5, 10-Q I.2 2/5
      NVDA  (1x/drawn) 10-K I.1 0/1, 10-K I.1A 1/2, 10-K II.7 0/1, 10-K IV.15 1/1, 10-Q I.1 1/2, 10-Q I.2 1/1, 10-Q II.1A 1/2
      PFE   (1x/drawn) 10-K I.1 1/1, 10-K I.1A 0/1, 10-K II.7 1/1, 10-K II.8 1/2, 10-Q I.1 1/3, 10-Q I.2 1/2
      TGT   (1x/drawn) 10-K I.1 0/1, 10-K I.1A 1/1, 10-K II.7 1/1, 10-K II.8 1/2, 10-K IV.15 0/1, 10-Q I.1 1/1, 10-Q I.2 1/2, 10-Q II.6 0/1
      XOM   (1x/drawn) 10-Q I.1 2/3, 10-Q I.2 3/6, 10-Q II.6 0/1
    distinct drawn chunks: 180 of 180; gold among them: 0
    prompt sha256 0dac2295c1cd2a20; wrote eval/seeding/draw_v1.json sha256 25e1bfc1d21eeef0

A second run left `eval/seeding/draw_v1.json` byte-identical (sha256
25e1bfc1...). The 2x is allocated per ticker, so 13 strata hold exactly their 1x
slots: one drop there is a `Shortfall` (question in the report). `make test`: 304
passed; `make lint` clean.

## 2026-10-01 — Seeding re-draw: overdraw per stratum (draw_v2)

From `draw_v1.json` (read before removal):

    draw_v1 table: draws in strata with zero 1x slots 6 (strata 6); slotted strata with no spare 2; total drawn 100
    draw_v1 synthesis: draws in strata with zero 1x slots 10 (strata 10); slotted strata with no spare 11; total drawn 80

`python -m scripts.seed_draw`:

    table: eligible 9426; excluded gold 439, floor 0
      slotted strata 24; slots 1x 50; draw target 100; drawn 100
      strata drawing fewer than their target: none
      AAPL  (1x/drawn) 10-K II.8 2/4, 10-K IV.15 1/2, 10-Q I.1 3/6, 10-Q I.2 1/2
      BAC   (1x/drawn) 10-K II.7 1/2, 10-K II.8 1/2, 10-Q I.1 2/4, 10-Q I.2 2/4
      COST  (1x/drawn) 10-K II.8 2/4, 10-Q I.1 3/6, 10-Q I.2 1/2
      JPM   (1x/drawn) 10-Q I.1 4/8, 10-Q I.2 2/4
      NVDA  (1x/drawn) 10-K IV.15 2/4, 10-Q I.1 3/6, 10-Q I.2 1/2
      PFE   (1x/drawn) 10-K II.8 2/4, 10-Q I.1 3/6, 10-Q I.2 1/2
      TGT   (1x/drawn) 10-K II.8 2/4, 10-Q I.1 2/4, 10-Q I.2 2/4
      XOM   (1x/drawn) 10-Q I.1 4/8, 10-Q I.2 3/6
    synthesis: eligible 11254; excluded gold 2, floor 1233
      slotted strata 33; slots 1x 40; draw target 80; drawn 80
      strata drawing fewer than their target: none
      AAPL  (1x/drawn) 10-K I.1A 1/2, 10-K II.8 1/2, 10-Q I.1 1/2, 10-Q I.2 1/2, 10-Q II.1A 1/2
      BAC   (1x/drawn) 10-K II.7 1/2, 10-K II.8 1/2, 10-Q I.1 1/2, 10-Q I.2 2/4
      COST  (1x/drawn) 10-K I.1A 1/2, 10-K II.7 1/2, 10-K II.8 1/2, 10-Q I.1 1/2, 10-Q I.2 1/2
      JPM   (1x/drawn) 10-Q I.1 3/6, 10-Q I.2 2/4
      NVDA  (1x/drawn) 10-K I.1A 1/2, 10-K IV.15 1/2, 10-Q I.1 1/2, 10-Q I.2 1/2, 10-Q II.1A 1/2
      PFE   (1x/drawn) 10-K I.1 1/2, 10-K II.7 1/2, 10-K II.8 1/2, 10-Q I.1 1/2, 10-Q I.2 1/2
      TGT   (1x/drawn) 10-K I.1A 1/2, 10-K II.7 1/2, 10-K II.8 1/2, 10-Q I.1 1/2, 10-Q I.2 1/2
      XOM   (1x/drawn) 10-Q I.1 2/4, 10-Q I.2 3/6
    distinct drawn chunks: 180 of 180; gold among them: 0
    prompt sha256 0dac2295c1cd2a20; wrote eval/seeding/draw_v2.json sha256 1c23e9f6511a554e

A second run left `draw_v2.json` byte-identical:

    1c23e9f6511a554eebab64a25e07117d3e2c099cd504ad1948239d46c4028313  eval/seeding/draw_v2.json

Order check against `draw_v1` (ad hoc, both files in the tree before removal):

    strata in draw_v2 whose order agrees with draw_v1 on the common prefix: 57; disagree: 0

`draw_v1.json` (sha256 25e1bfc1d21eeef0353d281e19ebeb9ccaa4830ac69634b48bc791e37176b147,
commit 8e6854d) removed. `scripts.seed_supply` now prints 1x slots and each
stratum's draw (`overdraw` x slots), the rule `seed_draw` applies; its 2x
largest-remainder lines are gone.

## 2026-10-01 — Seeding runner; one verification call outside the draw

`api.generate.generator.complete` (backend-neutral; the `anthropic_api` request
is the same code), `claude_cli.TransportError`, `claude_cli.version`,
`refuse_dev_baseline` (F-59), `eval/generate/seed_runner.py` (order, resume,
scrub, outcome), `scripts/seed_run.py`. Tests: `test_seed_runner.py` (5), one more
in `test_generator.py`; `make test` 310 passed, `make lint` clean.

`python -m scripts.seed_run --verify 0000909832-25-000015:68.1:68.1` (Costco Q2
FY2025 cash-flow table; asserted in neither draw_v2 nor gold; 5.1 s wall):

    backend claude_cli, model claude-sonnet-5-5 (tier_large); prompt 0dac2295c1cd2a20, draw 1c23e9f6511a554e
    drawn chunks 180; recorded 0; pending 180
    verify 0000909832-25-000015:68.1:68.1: in draw_v2 False, gold False; scrubbed fields []
    {
     "chunk_id": "0000909832-25-000015:68.1:68.1",
     "kind": "table",
     "ticker": "COST",
     "verification": true,
     "backend": "claude_cli",
     "model_requested": "claude-sonnet-5-5",
     "prompt_sha256": "0dac2295c1cd2a201df6efaac17917d8be07fda4e48156833b163759341d03f6",
     "draw_sha256": "1c23e9f6511a554eebab64a25e07117d3e2c099cd504ad1948239d46c4028313",
     "cli_version": "2.1.286 (Claude Code)",
     "model_served": "claude-sonnet-5-5",
     "usage": {
      "input_tokens": 2,
      "output_tokens": 364
     },
     "response": "{\"questions\": [{\"kind\": \"factual\", \"question\": \"What was Costco Wholesale Corp's net cash used in financing activities for the 24 weeks ended February 16, 2025 (Q2 FY2025)?\", \"answer\": \"(1,434)\", \"supporting_quote\": \"| Net cash used in financing activities | (1,434) | (8,250) |\"}, {\"kind\": \"interpretive\", \"question\": \"How did Costco Wholesale Corp's net change in cash and cash equivalents for the 24 weeks ended February 16, 2025 (Q2 FY2025) compare with the prior-year 24-week period, and what does that indicate about the direction of its cash position?\", \"answer\": \"Costco's cash position increased by 2,450 million in the 24 weeks ended February 16, 2025, versus a decrease of (4,605) million in the prior-year period, a reversal from cash decline to cash growth, with cash and cash equivalents ending at $12,356 compared with $9,095.\", \"supporting_quote\": \"| Net change in cash and cash equivalents | 2,450 | (4,605) |\"}]}",
     "error": null,
     "scrubbed_fields": []
    }
    outcome: {
     "status": "kept",
     "question": {
      "kind": "factual",
      "question": "What was Costco Wholesale Corp's net cash used in financing activities for the 24 weeks ended February 16, 2025 (Q2 FY2025)?",
      "answer": "(1,434)",
      "supporting_quote": "| Net cash used in financing activities | (1,434) | (8,250) |"
     },
     "flags": [
      "parenthesized figure: sign wording set at review (F-87)"
     ],
     "value": "-1434000000"
    }

Two defects that output exposed, fixed after the call and before any drawn chunk
was called: `value` came out signed (-1434000000), i.e. code decided the sign of
"(1,434)"; and `input_tokens: 2` because the CLI counts cached input apart. The
record on disk predates the cache-token fix (no re-call). Rebuilt offline:
`python -m scripts.seed_run --show-verify`:

    backend claude_cli, model claude-sonnet-5-5 (tier_large); prompt 0dac2295c1cd2a20, draw 1c23e9f6511a554e
    drawn chunks 180; recorded 0; pending 180
    0000909832-25-000015:68.1:68.1 (offline, from eval/seeding/verify_v1.jsonl):
    {
     "status": "kept",
     "question": {
      "kind": "factual",
      "question": "What was Costco Wholesale Corp's net cash used in financing activities for the 24 weeks ended February 16, 2025 (Q2 FY2025)?",
      "answer": "(1,434)",
      "supporting_quote": "| Net cash used in financing activities | (1,434) | (8,250) |"
     },
     "flags": [
      "parenthesized figure: sign wording set at review (F-87)"
     ],
     "value": null,
     "magnitude": "1434000000"
    }

`eval/seeding/verify_v1.jsonl` checked before commit: no email address, no home
path, no "/Users/".

## 2026-10-01 — Seeding: halt path, in-place redaction, offline rebuild (before the run)

`scripts/seed_run.py`: `call` returns a record with a response or raises
`CallFailed` with every attempt; `run_pending` writes one record per halt to
`call_errors_v1.jsonl`, leaves the chunk pending and exits 1, and refuses (exit
2) a chunk that halted 3 runs. Records carry `called_at` (UTC). `scrub` redacts
in place. `eval/generate/seed_build.py` (key-free stage, no-context gate,
near-duplicate, slot fill, F-92 flag) and `scripts/seed_build.py`. Tests:
`test_seed_run.py` (4, patched `complete`, no model call), `test_seed_build.py`
(5), the redaction test in `test_seed_runner.py`. `make test`: 319 passed; `make
lint`: 88 files already formatted.

`python -m scripts.seed_run` (status; exit 0):

    backend claude_cli, model claude-sonnet-5-5 (tier_large); prompt 0dac2295c1cd2a20, draw 1c23e9f6511a554e
    drawn chunks 180; recorded 0; pending 180

`python -m scripts.seed_build` on an empty raw file (exit 0; the empty
`dropped_v1.jsonl` it wrote was removed, it is rebuilt after the run):

    raw records 0; {'pending': 180}
    wrote eval/seeding/dropped_v1.jsonl: 0 drops
    key-free survivors per stratum, in draw order:
      none
    no survivors: no candidates or reserve to write

No drawn chunk has been called.

## 2026-10-01 — Seeding: pre-run fixes (served model, malformed result, JSONL, rebuild integrity, --limit)

`claude_cli.parse_output` raises `CliError` on a non-object document, missing or
non-integer usage, or a missing, non-string or empty result; `call` halts on a
served model other than `tier_large` (kind `wrong_model`, text kept); `read_jsonl`
splits on "\n" only (the candidates and verify readers use it too); the rebuild
refuses duplicates, undrawn chunks and stale shas and prints every slotted
stratum, `model_served` and redacted responses; `--limit N` on `--run`. Tests
added for each. `make test`: 334 passed; `make lint`: 88 files already formatted.

## 2026-10-01 — Prose verification outside the draw

Target, per the run protocol (ad hoc, eligibility recomputed as `seed_draw` does):

    largest synthesis stratum by eligible: JPM 10-Q I.1 (1421 eligible, 6 drawn)
    recomputed eligible: 1421 (manifest 1421)
    lowest chunk_id not drawn and not gold: 0000019617-23-000524:1390.0:1390.0

`python -m scripts.seed_run --verify 0000019617-23-000524:1390.0:1390.0` (exit 0):

    backend claude_cli, model claude-sonnet-5-5 (tier_large); prompt 0dac2295c1cd2a20, draw 1c23e9f6511a554e
    drawn chunks 180; recorded 0; pending 180
    verify 0000019617-23-000524:1390.0:1390.0: in draw_v2 False, gold False; scrubbed fields []
    {
     "chunk_id": "0000019617-23-000524:1390.0:1390.0",
     "kind": "synthesis",
     "ticker": "JPM",
     "verification": true,
     "called_at": "2026-10-01T18:40:01+00:00",
     "backend": "claude_cli",
     "model_requested": "claude-sonnet-5-5",
     "model_served": "claude-sonnet-5-5",
     "prompt_sha256": "0dac2295c1cd2a201df6efaac17917d8be07fda4e48156833b163759341d03f6",
     "draw_sha256": "1c23e9f6511a554eebab64a25e07117d3e2c099cd504ad1948239d46c4028313",
     "cli_version": "2.1.286 (Claude Code)",
     "usage": {
      "input_tokens": 2,
      "output_tokens": 635,
      "cache_read_tokens": 0,
      "cache_creation_tokens": 969
     },
     "response": "{\"questions\": [{\"kind\": \"factual\", \"question\": \"In JPMorgan Chase & Co's 10-Q for Q3 FY2023, as of which two dates does the table present information on assets and liabilities related to consolidated VIEs?\", \"answer\": \"September 30, 2023 and December 31, 2022\", \"supporting_quote\": \"The following table presents information on assets and liabilities related to VIEs that are consolidated by the Firm at September 30, 2023 and December 31, 2022.\"}, {\"kind\": \"interpretive\", \"question\": \"In JPMorgan Chase & Co's Q3 FY2023 10-Q, what do the disclosures imply about whether JPMorgan Chase's general credit backs the liabilities of its consolidated VIEs, and what are the VIE assets used for?\", \"answer\": \"The VIE assets are used to settle the VIEs' liabilities, and holders of the beneficial interests generally have no recourse to JPMorgan Chase's general credit, so the firm's general credit does not generally back those liabilities.\", \"supporting_quote\": \"The assets of the consolidated VIEs are used to settle the liabilities of those entities. The holders of the beneficial interests generally do not have recourse to the general credit of JPMorgan Chase.\"}]}",
     "scrubbed_fields": []
    }
    outcome: {
     "status": "kept",
     "question": {
      "kind": "interpretive",
      "question": "In JPMorgan Chase & Co's Q3 FY2023 10-Q, what do the disclosures imply about whether JPMorgan Chase's general credit backs the liabilities of its consolidated VIEs, and what are the VIE assets used for?",
      "answer": "The VIE assets are used to settle the VIEs' liabilities, and holders of the beneficial interests generally have no recourse to JPMorgan Chase's general credit, so the firm's general credit does not generally back those liabilities.",
      "supporting_quote": "The assets of the consolidated VIEs are used to settle the liabilities of those entities. The holders of the beneficial interests generally do not have recourse to the general credit of JPMorgan Chase."
     },
     "flags": [],
     "value": null,
     "magnitude": null
    }

Kept. Both questions name the filing and its quarter ("In JPMorgan Chase & Co's
10-Q for Q3 FY2023"), copied from the header: the same tendency as F-92, here
on a prose item. `verify_v1.jsonl`: no email address, no "/Users/".

## 2026-10-01 — Seeding run complete: 180 calls, pending 0

Ten batches, one process at a time (`--run --limit 5`, then `seed_build`, then
`--limit 20` x 8 and a final 15), 18:40:20Z to about 18:58Z UTC. `raw_v1.jsonl`
committed after each batch; no halts, `call_errors_v1.jsonl` was never created;
no run killed. After every batch: all responses started with "{" or a code fence
(no CLI/API error text), every record served by `claude-sonnet-5-5`, no email
address and no "/Users/" in the raw file.

`python -m scripts.seed_run`:

    backend claude_cli, model claude-sonnet-5-5 (tier_large); prompt 0dac2295c1cd2a20, draw 1c23e9f6511a554e
    drawn chunks 180; recorded 180; pending 0

`python -m scripts.seed_build`:

    raw records 180; {'dropped:names_company': 5, 'dropped:sign_only': 0, 'dropped:unanchored_pronoun': 17, 'flagged:quarter_label_on_span': 13, 'kept': 158}
    wrote eval/seeding/dropped_v1.jsonl: 22 drops
    model_served: {'claude-sonnet-5-5': 180}
    responses redacted (a quote_verbatim drop there is not a filter result): none
    slotted strata: survivors / slots_1x / drawn / pending
      table AAPL 10-K II.8                4 / 2 / 4 / 0
      table AAPL 10-K IV.15               2 / 1 / 2 / 0
      table AAPL 10-Q I.1                 6 / 3 / 6 / 0
      table AAPL 10-Q I.2                 2 / 1 / 2 / 0
      table BAC 10-K II.7                 2 / 1 / 2 / 0
      table BAC 10-K II.8                 2 / 1 / 2 / 0
      table BAC 10-Q I.1                  4 / 2 / 4 / 0
      table BAC 10-Q I.2                  4 / 2 / 4 / 0
      table COST 10-K II.8                4 / 2 / 4 / 0
      table COST 10-Q I.1                 6 / 3 / 6 / 0
      table COST 10-Q I.2                 2 / 1 / 2 / 0
      table JPM 10-Q I.1                  8 / 4 / 8 / 0
      table JPM 10-Q I.2                  4 / 2 / 4 / 0
      table NVDA 10-K IV.15               4 / 2 / 4 / 0
      table NVDA 10-Q I.1                 6 / 3 / 6 / 0
      table NVDA 10-Q I.2                 2 / 1 / 2 / 0
      table PFE 10-K II.8                 4 / 2 / 4 / 0
      table PFE 10-Q I.1                  6 / 3 / 6 / 0
      table PFE 10-Q I.2                  2 / 1 / 2 / 0
      table TGT 10-K II.8                 4 / 2 / 4 / 0
      table TGT 10-Q I.1                  4 / 2 / 4 / 0
      table TGT 10-Q I.2                  4 / 2 / 4 / 0
      table XOM 10-Q I.1                  5 / 4 / 8 / 0
      table XOM 10-Q I.2                  6 / 3 / 6 / 0
      synthesis AAPL 10-K I.1A            0 / 1 / 2 / 0
      synthesis AAPL 10-K II.8            1 / 1 / 2 / 0
      synthesis AAPL 10-Q I.1             2 / 1 / 2 / 0
      synthesis AAPL 10-Q I.2             1 / 1 / 2 / 0
      synthesis AAPL 10-Q II.1A           1 / 1 / 2 / 0
      synthesis BAC 10-K II.7             2 / 1 / 2 / 0
      synthesis BAC 10-K II.8             2 / 1 / 2 / 0
      synthesis BAC 10-Q I.1              2 / 1 / 2 / 0
      synthesis BAC 10-Q I.2              4 / 2 / 4 / 0
      synthesis COST 10-K I.1A            0 / 1 / 2 / 0
      synthesis COST 10-K II.7            2 / 1 / 2 / 0
      synthesis COST 10-K II.8            2 / 1 / 2 / 0
      synthesis COST 10-Q I.1             2 / 1 / 2 / 0
      synthesis COST 10-Q I.2             2 / 1 / 2 / 0
      synthesis JPM 10-Q I.1              6 / 3 / 6 / 0
      synthesis JPM 10-Q I.2              4 / 2 / 4 / 0
      synthesis NVDA 10-K I.1A            0 / 1 / 2 / 0
      synthesis NVDA 10-K IV.15           2 / 1 / 2 / 0
      synthesis NVDA 10-Q I.1             2 / 1 / 2 / 0
      synthesis NVDA 10-Q I.2             1 / 1 / 2 / 0
      synthesis NVDA 10-Q II.1A           1 / 1 / 2 / 0
      synthesis PFE 10-K I.1              2 / 1 / 2 / 0
      synthesis PFE 10-K II.7             1 / 1 / 2 / 0
      synthesis PFE 10-K II.8             2 / 1 / 2 / 0
      synthesis PFE 10-Q I.1              2 / 1 / 2 / 0
      synthesis PFE 10-Q I.2              2 / 1 / 2 / 0
      synthesis TGT 10-K I.1A             0 / 1 / 2 / 0
      synthesis TGT 10-K II.7             1 / 1 / 2 / 0
      synthesis TGT 10-K II.8             2 / 1 / 2 / 0
      synthesis TGT 10-Q I.1              2 / 1 / 2 / 0
      synthesis TGT 10-Q I.2              2 / 1 / 2 / 0
      synthesis XOM 10-Q I.1              2 / 2 / 4 / 0
      synthesis XOM 10-Q I.2              4 / 3 / 6 / 0
    key-free survivors in draw order:
      synthesis AAPL 10-K II.8: ['0000320193-25-000079:478.0:485.0']
      synthesis AAPL 10-Q I.1: ['0000320193-24-000069:105.0:112.0', '0000320193-24-000081:81.0:84.0 [flags]']
      synthesis AAPL 10-Q I.2: ['0000320193-25-000008:189.0:196.0']
      synthesis AAPL 10-Q II.1A: ['0000320193-26-000013:270.0:272.0']
      synthesis BAC 10-K II.7: ['0000070858-24-000122:1193.0:1195.0', '0000070858-24-000122:831.0:835.0']
      synthesis BAC 10-K II.8: ['0000070858-24-000122:1445.0:1453.0', '0000070858-26-000157:1268.0:1273.0']
      synthesis BAC 10-Q I.1: ['0000070858-25-000268:991.0:993.0', '0000070858-24-000208:1135.0:1138.0']
      synthesis BAC 10-Q I.2: ['0000070858-25-000405:253.0:260.0', '0000070858-25-000200:433.0:438.0', '0000070858-25-000405:328.0:331.0', '0000070858-23-000272:397.0:400.0']
      synthesis COST 10-K II.7: ['0000909832-24-000049:271.0:273.0', '0000909832-23-000042:283.0:285.0']
      synthesis COST 10-K II.8: ['0000909832-24-000049:704.0:704.0', '0000909832-24-000049:512.0:514.0']
      synthesis COST 10-Q I.1: ['0000909832-23-000065:143.0:146.0', '0000909832-25-000033:152.0:156.0']
      synthesis COST 10-Q I.2: ['0000909832-26-000051:204.0:215.0', '0000909832-25-000033:221.0:227.0']
      synthesis JPM 10-Q I.1: ['0000019617-24-000611:2453.0:2461.0', '0000019617-24-000611:1673.0:1678.0', '0001628280-25-048859:1284.0:1301.0', '0000019617-23-000524:2434.0:2440.0', '0000019617-23-000524:2571.0:2595.0', '0000019617-23-000524:2284.0:2285.0']
      synthesis JPM 10-Q I.2: ['0001628280-26-029344:908.0:908.0', '0001628280-26-054343:948.0:953.0', '0000019617-23-000524:864.0:871.0', '0000019617-25-000615:813.0:821.0']
      synthesis NVDA 10-K IV.15: ['0001045810-25-000023:1199.0:1205.0', '0001045810-24-000029:1063.0:1066.0']
      synthesis NVDA 10-Q I.1: ['0001045810-25-000230:188.0:191.0', '0001045810-24-000316:197.0:198.0']
      synthesis NVDA 10-Q I.2: ['0001045810-25-000230:354.0:360.0']
      synthesis NVDA 10-Q II.1A: ['0001045810-25-000209:462.0:465.0']
      synthesis PFE 10-K I.1: ['0000078003-24-000039:239.0:246.0', '0000078003-26-000026:197.0:201.0']
      synthesis PFE 10-K II.7: ['0000078003-24-000039:743.0:746.0']
      synthesis PFE 10-K II.8: ['0000078003-26-000026:1365.0:1366.0', '0000078003-26-000026:1225.0:1233.0']
      synthesis PFE 10-Q I.1: ['0000078003-26-000095:107.0:110.0', '0000078003-24-000191:396.0:398.0']
      synthesis PFE 10-Q I.2: ['0000078003-25-000114:498.0:503.0', '0000078003-26-000095:646.0:651.0']
      synthesis TGT 10-K II.7: ['0000027419-24-000032:392.0:395.0']
      synthesis TGT 10-K II.8: ['0000027419-25-000018:704.0:708.0', '0000027419-24-000032:664.0:670.0']
      synthesis TGT 10-Q I.1: ['0000027419-26-000022:131.0:131.0', '0000027419-25-000101:45.0:47.0']
      synthesis TGT 10-Q I.2: ['0000027419-24-000179:214.0:224.0 [flags]', '0000027419-25-000118:174.0:195.0 [flags]']
      synthesis XOM 10-Q I.1: ['0000034088-23-000056:75.0:77.0', '0000034088-26-000093:147.0:168.0']
      synthesis XOM 10-Q I.2: ['0000034088-23-000056:132.0:133.0', '0000034088-24-000029:168.0:177.0', '0000034088-26-000067:231.0:253.0', '0000034088-25-000042:247.0:259.0 [flags]']
      table AAPL 10-K II.8: ['0000320193-24-000123:512.0:512.0', '0000320193-24-000123:416.1:416.1 [flags]', '0000320193-25-000079:462.0:462.0 [flags]', '0000320193-24-000123:410.0:410.0']
      table AAPL 10-K IV.15: ['0000320193-23-000106:682.1:682.1', '0000320193-25-000079:680.0:680.0']
      table AAPL 10-Q I.1: ['0000320193-25-000073:112.0:112.0', '0000320193-24-000006:62.0:62.0', '0000320193-26-000013:38.1:38.1 [flags]', '0000320193-26-000013:85.0:85.0', '0000320193-26-000006:56.0:56.0 [flags]', '0000320193-25-000008:73.0:73.0']
      table AAPL 10-Q I.2: ['0000320193-24-000081:194.0:194.0', '0000320193-25-000057:175.0:175.0']
      table BAC 10-K II.7: ['0000070858-26-000157:580.0:580.0', '0000070858-24-000122:508.2:508.2']
      table BAC 10-K II.8: ['0000070858-26-000157:2172.3:2172.3', '0000070858-25-000139:1474.1:1474.1']
      table BAC 10-Q I.1: ['0000070858-24-000208:1148.1:1148.1 [flags]', '0000070858-25-000200:750.2:750.2 [flags]', '0000070858-24-000156:646.2:646.2', '0000070858-25-000405:710.2:710.2']
      table BAC 10-Q I.2: ['0000070858-24-000280:570.0:570.0', '0000070858-24-000156:288.1:288.1', '0000070858-25-000268:138.4:138.4 [flags]', '0000070858-25-000200:546.1:546.1']
      table COST 10-K II.8: ['0000909832-25-000101:686.0:686.0', '0000909832-23-000042:411.0:411.0 [flags]', '0000909832-23-000042:504.0:504.0', '0000909832-24-000049:511.0:511.0']
      table COST 10-Q I.1: ['0000909832-26-000029:174.0:174.0', '0000909832-24-000017:33.1:33.1 [flags]', '0000909832-24-000079:95.0:95.0', '0000909832-24-000029:61.0:61.0 [flags]', '0000909832-26-000029:177.0:177.0', '0000909832-23-000065:104.0:104.0 [flags]']
      table COST 10-Q I.2: ['0000909832-23-000065:211.0:211.0 [flags]', '0000909832-24-000079:210.0:210.0 [flags]']
      table JPM 10-Q I.1: ['0000019617-25-000615:1344.0:1344.0', '0000019617-24-000611:1549.0:1549.0 [flags]', '0000019617-25-000615:1270.0:1270.0 [flags]', '0001628280-26-054343:1819.1:1819.1', '0000019617-25-000615:1706.0:1706.0 [flags]', '0000019617-24-000326:1130.1:1130.1 [flags]', '0001628280-26-054343:1228.0:1228.0 [flags]', '0001628280-26-029344:1299.0:1299.0 [flags]']
      table JPM 10-Q I.2: ['0000019617-25-000421:752.0:752.0', '0000019617-24-000453:415.1:415.1', '0001628280-25-048859:475.0:475.0', '0001628280-26-029344:535.0:535.0']
      table NVDA 10-K IV.15: ['0001045810-26-000021:1010.0:1010.0', '0001045810-25-000023:1122.0:1122.0', '0001045810-26-000021:778.0:778.0', '0001045810-24-000029:963.0:963.0']
      table NVDA 10-Q I.1: ['0001045810-24-000124:178.0:178.0', '0001045810-24-000316:43.1:43.1 [flags]', '0001045810-24-000264:117.0:117.0', '0001045810-24-000316:71.1:71.1 [flags]', '0001045810-24-000316:192.0:192.0', '0001045810-26-000052:116.0:116.0']
      table NVDA 10-Q I.2: ['0001045810-24-000316:327.0:327.0 [flags]', '0001045810-26-000075:378.0:378.0']
      table PFE 10-K II.8: ['0000078003-26-000026:1124.0:1124.0 [flags]', '0000078003-26-000026:1261.0:1261.0', '0000078003-26-000026:1261.1:1261.1', '0000078003-25-000054:1174.1:1174.1 [flags]']
      table PFE 10-Q I.1: ['0000078003-26-000054:236.0:236.0', '0000078003-26-000054:209.1:209.1', '0000078003-25-000138:70.1:70.1 [flags]', '0000078003-25-000114:153.0:153.0 [flags]', '0000078003-25-000150:70.0:70.0 [flags]', '0000078003-24-000166:203.0:203.0 [flags]']
      table PFE 10-Q I.2: ['0000078003-23-000115:586.3:586.3', '0000078003-24-000166:593.3:593.3']
      table TGT 10-K II.8: ['0000027419-24-000032:480.0:480.0', '0000027419-26-000016:688.0:688.0 [flags]', '0000027419-25-000018:716.0:716.0', '0000027419-25-000018:605.0:605.0']
      table TGT 10-Q I.1: ['0000027419-24-000129:75.0:75.0', '0000027419-23-000052:128.0:128.0 [flags]', '0000027419-25-000118:123.0:123.0 [flags]', '0000027419-24-000152:50.0:50.0 [flags]']
      table TGT 10-Q I.2: ['0000027419-26-000042:213.0:213.0', '0000027419-25-000101:169.0:169.0', '0000027419-25-000101:203.0:203.0', '0000027419-25-000118:158.0:158.0']
      table XOM 10-Q I.1: ['0000034088-25-000042:83.0:83.0', '0000034088-24-000050:122.0:122.0', '0000034088-24-000050:117.2:117.2', '0000034088-26-000067:104.0:104.0', '0000034088-24-000068:97.1:97.1']
      table XOM 10-Q I.2: ['0000034088-24-000050:154.0:154.0 [flags]', '0000034088-25-000061:180.1:180.1 [flags]', '0000034088-25-000061:266.0:266.0', '0000034088-24-000029:190.0:190.0', '0000034088-24-000068:224.0:224.0', '0000034088-24-000068:242.0:242.0']
    stopped after the key-free stage: 158 key-free survivors lack a no-context record; no candidates or reserve written

The drops (ad hoc over `dropped_v1.jsonl` and the raw file, question shown):

    drops by (kind, filter): {('table', 'names_company'): 3, ('synthesis', 'unanchored_pronoun'): 17, ('synthesis', 'names_company'): 2}
    drops by stratum: {'table XOM 10-Q I.1': 3, 'synthesis AAPL 10-K I.1A': 2, 'synthesis AAPL 10-K II.8': 1, 'synthesis AAPL 10-Q I.2': 1, 'synthesis AAPL 10-Q II.1A': 1, 'synthesis COST 10-K I.1A': 2, 'synthesis NVDA 10-K I.1A': 2, 'synthesis NVDA 10-Q I.2': 1, 'synthesis NVDA 10-Q II.1A': 1, 'synthesis PFE 10-K II.7': 1, 'synthesis TGT 10-K I.1A': 2, 'synthesis TGT 10-K II.7': 1, 'synthesis XOM 10-Q I.1': 2, 'synthesis XOM 10-Q I.2': 2}
    - table XOM 10-Q I.1 names_company: question names no company or ticker | What was ExxonMobil Holdings Corporation's net benefit cost for pension and other postretirement benefits for the three months ended June 30, 2026 (Q2
    - table XOM 10-Q I.1 names_company: question names no company or ticker | What was ExxonMobil Holdings Corporation's net cash used in financing activities for the six months ended June 30, 2026 (Q2 FY2026)?
    - table XOM 10-Q I.1 names_company: question names no company or ticker | In ExxonMobil Holdings Corporation's 10-Q for Q2 FY2026, what Segment Total was reported for Sales and other operating revenue for the six months ende
    - synthesis AAPL 10-K I.1A unanchored_pronoun: pronoun 'its' before any company name | In its FY2025 10-K risk factors, what does Apple Inc. say could happen to the Company if its effective tax rates increase or if the final determinatio
    - synthesis AAPL 10-K I.1A unanchored_pronoun: pronoun 'its' before any company name | In its FY2025 10-K risk factors, what competitor pricing behavior does Apple Inc. cite as making competition particularly intense?
    - synthesis AAPL 10-K II.8 unanchored_pronoun: deictic reference 'that period' | Based on the figures reported for Apple Inc. for fiscal years 2022 through 2024, how did depreciation expense on property, plant and equipment trend o
    - synthesis AAPL 10-Q I.2 unanchored_pronoun: deictic reference 'that period' | In its Q1 FY2026 Form 10-Q, what example does Apple Inc. give of a forward-looking statement, and what does this suggest about the uncertainties manag
    - synthesis AAPL 10-Q II.1A unanchored_pronoun: pronoun 'its' before any company name | In its Q2 FY2025 10-Q risk factors, why does Apple Inc. suggest that its reliance on a single product could make quarterly net sales volatile?
    - synthesis COST 10-K I.1A unanchored_pronoun: pronoun 'its' before any company name | In its FY2024 10-K, how does Costco Wholesale Corp say its own actions can shape the effect that tariff-related cost increases have on its net sales a
    - synthesis COST 10-K I.1A unanchored_pronoun: pronoun 'its' before any company name | In its fiscal year 2024 10-K risk factors, what does Costco Wholesale Corp imply about the limits of employee security training as a defense against c
    - synthesis NVDA 10-K I.1A unanchored_pronoun: pronoun 'its' before any company name | In its FY2026 10-K risk factors, what does NVIDIA Corp's list of operational disruption factors suggest about the range of risks it considers, in term
    - synthesis NVDA 10-K I.1A unanchored_pronoun: pronoun 'its' before any company name | In its fiscal year 2025 10-K risk factors, under what circumstances does NVIDIA Corp indicate it could incur inventory provisions or impairments as it
    - synthesis NVDA 10-Q I.2 unanchored_pronoun: pronoun 'its' before any company name | In its 10-Q for Q3 FY2024, how does NVIDIA Corp (NVDA) characterize the risk that further changes in U.S. government export controls pose to its busin
    - synthesis NVDA 10-Q II.1A unanchored_pronoun: pronoun 'its' before any company name | In its Q2 fiscal year 2027 10-Q, how does NVIDIA Corp characterize its ability to pass the tariff on H200 products shipped under the USG licensing pro
    - synthesis PFE 10-K II.7 unanchored_pronoun: pronoun 'its' before any company name | In its FY2023 10-K, why does Pfizer Inc acknowledge that major non-acquisition-related cost-reduction programs, though excluded from adjusted income a
    - synthesis TGT 10-K I.1A unanchored_pronoun: pronoun 'its' before any company name | In its FY2025 10-K risk factors, why does Target Corporation say it expects to keep incurring significant interchange and other processing fee costs, 
    - synthesis TGT 10-K I.1A unanchored_pronoun: pronoun 'its' before any company name | In its FY2025 10-K, why does Target Corporation say that its own resilience goals and initiatives, not just external climate events, could harm its bu
    - synthesis TGT 10-K II.7 unanchored_pronoun: pronoun 'its' before any company name | In its fiscal year 2024 10-K, why does Target Corporation believe the risk of inventory obsolescence is largely mitigated?
    - synthesis XOM 10-Q I.1 unanchored_pronoun: pronoun 'its' before any company name | In its Q1 FY2026 10-Q, how does Exxon Mobil Corporation characterize the likelihood that the ultimate outcomes of the climate change and Louisiana coa
    - synthesis XOM 10-Q I.1 unanchored_pronoun: pronoun 'its' before any company name | In its Q1 FY2025 10-Q, how does Exxon Mobil Corporation characterize the climate change lawsuits filed by state and local governments, and what does i
    - synthesis XOM 10-Q I.2 names_company: question names no company or ticker | According to ExxonMobil Holdings Corporation's disclosure for the first six months of fiscal 2026, what factors explained the increase in Corporate an
    - synthesis XOM 10-Q I.2 names_company: question names no company or ticker | How did ExxonMobil Holdings Corporation characterize global industry refining margins in Q2 FY2026 relative to historical norms, and what reason did i

Findings, not filter changes (the filters are frozen from the first drawn call):
15 of the 17 `unanchored_pronoun` drops are a cataphoric "In its FY2025 10-K
..., what does Apple Inc. say ..." (F-94); all 5 `names_company` drops name
"ExxonMobil Holdings Corporation", which the names list does not hold (F-93). At
the key-free stage four synthesis strata have no survivor: 10-K I.1A for AAPL,
COST, NVDA and TGT, 0 of 1 slot each (F-95). F-92's count, 13, is a lower bound.

## 2026-10-01 — No-context filter built (before any no-context call)

`eval/generate/no_context.py` (extractor, 0.5% rule, near-match, digits-only,
sign-only), `eval/generate/prompts/no_context_v1.txt`,
`scripts/no_context_run.py` (on `seed_run`'s halt-and-resume loop; `call` now
delegates to `call_prompt`, seeding behaviour unchanged, its tests pass),
`seed_build`'s no-context stage. Tests: `test_no_context.py` (9), three more in
`test_seed_build.py`. `make test`: 346 passed; `make lint`: 91 files already
formatted. `seed_build`'s key-free output is identical to the committed post-run
output (`diff` empty) and `dropped_v1.jsonl` is unchanged.

`python -m scripts.seed_build` with no no-context records:

      table XOM 10-Q I.2: ['0000034088-24-000050:154.0:154.0 [flags]', '0000034088-25-000061:180.1:180.1 [flags]', '0000034088-25-000061:266.0:266.0', '0000034088-24-000029:190.0:190.0', '0000034088-24-000068:224.0:224.0', '0000034088-24-000068:242.0:242.0']
    stopped after the key-free stage: 158 key-free survivors lack a no-context record; no candidates or reserve written

## 2026-10-01 — No-context run complete: 158 calls; no-context stage applied

Batches (`--limit 5`, then 20s, last 13), 19:28:24Z to 19:45Z UTC, one process at
a time, `no_context_v1.jsonl` committed after each; no halts (no errors file), all
158 served by `claude-sonnet-5-5`, no CLI/API error text, no email or "/Users/".
`python -m scripts.no_context_run`: `key-free survivors 158; recorded 158; pending 0`.

`python -m scripts.seed_build` (no-context part; the key-free part is unchanged):

    raw records 180; {'dropped:names_company': 5, 'dropped:sign_only': 0, 'dropped:unanchored_pronoun': 17, 'flagged:quarter_label_on_span': 13, 'kept': 158}
    ...
    no-context stage: 18 dropped, appended to eval/seeding/dropped_v1.jsonl
    slotted strata: survivors / slots_1x / no-context dropped / near-matches / digits-only / sign-only
      table AAPL 10-K II.8                1 / 2 / 3 / 1 / 2 / 1
      table AAPL 10-K IV.15               0 / 1 / 2 / 0 / 0 / 0
      table AAPL 10-Q I.1                 3 / 3 / 3 / 0 / 1 / 0
      table AAPL 10-Q I.2                 0 / 1 / 2 / 0 / 0 / 0
      table BAC 10-K II.7                 2 / 1 / 0 / 0 / 0 / 0
      table BAC 10-K II.8                 2 / 1 / 0 / 0 / 0 / 0
      table BAC 10-Q I.1                  4 / 2 / 0 / 0 / 0 / 0
      table BAC 10-Q I.2                  4 / 2 / 0 / 1 / 0 / 0
      table COST 10-K II.8                3 / 2 / 1 / 0 / 1 / 0
      table COST 10-Q I.1                 5 / 3 / 1 / 0 / 1 / 0
      table COST 10-Q I.2                 2 / 1 / 0 / 0 / 0 / 0
      table JPM 10-Q I.1                  8 / 4 / 0 / 0 / 0 / 0
      table JPM 10-Q I.2                  3 / 2 / 1 / 0 / 0 / 0
      table NVDA 10-K IV.15               4 / 2 / 0 / 0 / 0 / 0
      table NVDA 10-Q I.1                 5 / 3 / 1 / 0 / 1 / 0
      table NVDA 10-Q I.2                 2 / 1 / 0 / 0 / 0 / 0
      table PFE 10-K II.8                 4 / 2 / 0 / 0 / 0 / 0
      table PFE 10-Q I.1                  6 / 3 / 0 / 1 / 0 / 0
      table PFE 10-Q I.2                  1 / 1 / 1 / 0 / 0 / 0
      table TGT 10-K II.8                 3 / 2 / 1 / 0 / 0 / 0
      table TGT 10-Q I.1                  3 / 2 / 1 / 0 / 0 / 0
      table TGT 10-Q I.2                  3 / 2 / 1 / 2 / 0 / 0
      table XOM 10-Q I.1                  5 / 4 / 0 / 2 / 0 / 0
      table XOM 10-Q I.2                  6 / 3 / 0 / 0 / 0 / 0
      synthesis AAPL 10-K I.1A            0 / 1 / 0 / 0 / 0 / 0
      synthesis AAPL 10-K II.8            1 / 1 / 0 / 0 / 0 / 0
      synthesis AAPL 10-Q I.1             2 / 1 / 0 / 0 / 0 / 0
      synthesis AAPL 10-Q I.2             1 / 1 / 0 / 0 / 0 / 0
      synthesis AAPL 10-Q II.1A           1 / 1 / 0 / 0 / 0 / 0
      synthesis BAC 10-K II.7             2 / 1 / 0 / 0 / 0 / 0
      synthesis BAC 10-K II.8             2 / 1 / 0 / 0 / 0 / 0
      synthesis BAC 10-Q I.1              2 / 1 / 0 / 0 / 0 / 0
      synthesis BAC 10-Q I.2              4 / 2 / 0 / 0 / 0 / 0
      synthesis COST 10-K I.1A            0 / 1 / 0 / 0 / 0 / 0
      synthesis COST 10-K II.7            2 / 1 / 0 / 0 / 0 / 0
      synthesis COST 10-K II.8            2 / 1 / 0 / 0 / 0 / 0
      synthesis COST 10-Q I.1             2 / 1 / 0 / 0 / 0 / 0
      synthesis COST 10-Q I.2             2 / 1 / 0 / 0 / 0 / 0
      synthesis JPM 10-Q I.1              6 / 3 / 0 / 0 / 0 / 0
      synthesis JPM 10-Q I.2              4 / 2 / 0 / 0 / 0 / 0
      synthesis NVDA 10-K I.1A            0 / 1 / 0 / 0 / 0 / 0
      synthesis NVDA 10-K IV.15           2 / 1 / 0 / 0 / 0 / 0
      synthesis NVDA 10-Q I.1             2 / 1 / 0 / 0 / 0 / 0
      synthesis NVDA 10-Q I.2             1 / 1 / 0 / 0 / 0 / 0
      synthesis NVDA 10-Q II.1A           1 / 1 / 0 / 0 / 0 / 0
      synthesis PFE 10-K I.1              2 / 1 / 0 / 0 / 0 / 0
      synthesis PFE 10-K II.7             1 / 1 / 0 / 0 / 0 / 0
      synthesis PFE 10-K II.8             2 / 1 / 0 / 0 / 0 / 0
      synthesis PFE 10-Q I.1              2 / 1 / 0 / 0 / 0 / 0
      synthesis PFE 10-Q I.2              2 / 1 / 0 / 0 / 0 / 0
      synthesis TGT 10-K I.1A             0 / 1 / 0 / 0 / 0 / 0
      synthesis TGT 10-K II.7             1 / 1 / 0 / 0 / 0 / 0
      synthesis TGT 10-K II.8             2 / 1 / 0 / 0 / 0 / 0
      synthesis TGT 10-Q I.1              2 / 1 / 0 / 0 / 0 / 0
      synthesis TGT 10-Q I.2              2 / 1 / 0 / 0 / 0 / 0
      synthesis XOM 10-Q I.1              2 / 2 / 0 / 0 / 0 / 0
      synthesis XOM 10-Q I.2              4 / 3 / 0 / 0 / 0 / 0
      totals: kept 140; {'near': 7, 'sign_only': 1, 'dropped': 18, 'digits_only': 6}
    next: near-duplicate stage (not run here); no candidates or reserve written

The 18 no-context drops (ad hoc over `dropped_v1.jsonl` and the no-context raw):

    - table AAPL 10-K II.8 [no_context] no-context answer '$74,834 million' within 0.5% of '$74,834'
        Q: What was Apple Inc.'s total other non-current assets in fiscal year 2024 (FY2024), in millions of USD?
    - table AAPL 10-K II.8 [no_context:digits_only, sign_only] no-context answer '$19,154 million' within 0.5% of '(19,154)'
        Q: What was Apple Inc.'s accumulated deficit as of September 28, 2024, the end of fiscal year 2024?
    - table AAPL 10-K II.8 [no_context:digits_only] no-context answer '$7.46' within 0.5% of '$7.46'
        Q: What was Apple Inc.'s diluted earnings per share for fiscal year 2025?
    - table AAPL 10-K IV.15 [no_context] no-context answer '3.000%' within 0.5% of '3.000%'
        Q: In Apple Inc.'s FY2023 10-K (Item 15 exhibit list), what interest rate applies to the global note due 2027 described in the Officer's Certif
    - table AAPL 10-K IV.15 [no_context] no-context answer '4.750%' within 0.5% of '4.750%'
        Q: In Apple Inc.'s FY2025 10-K (Item 15 exhibit list), what interest rate is stated for the Notes due 2035 in the Officer's Certificate dated a
    - table AAPL 10-Q I.1 [no_context] no-context answer '$39,895 million' within 0.5% of '39,895'
        Q: What was Apple Inc.'s cash generated by operating activities for the three months ended December 30, 2023 (Q1 FY2024)?
    - table AAPL 10-Q I.1 [no_context:digits_only] no-context answer '2' within 0.5% of '$2.01'
        Q: What was Apple Inc.'s diluted earnings per share for the three months ended March 28, 2026 (Q2 FY2026)?
    - table AAPL 10-Q I.1 [no_context] no-context answer '$26.340 billion' within 0.5% of '26,340'
        Q: What was Apple Inc.'s Services net sales for the three months ended December 28, 2024 (Q1 FY2025)?
    - table AAPL 10-Q I.2 [no_context] no-context answer '$39,678 million' within 0.5% of '$39,678'
        Q: What was Apple Inc.'s total gross margin, in millions of USD, for the three months ended June 29, 2024 (Q3 FY2024)?
    - table AAPL 10-Q I.2 [no_context] no-context answer '$26.645 billion' within 0.5% of '$26,645'
        Q: What were Apple Inc.'s Services net sales for the three months ended March 29, 2025 (Q2 FY2025)?
    - table COST 10-K II.8 [no_context:digits_only] no-context answer '$14.16' within 0.5% of '$14.16'
        Q: What was Costco Wholesale Corp's diluted net income per common share attributable to Costco for the 53 weeks ended September 3, 2023 (fiscal
    - table COST 10-Q I.1 [no_context:digits_only] no-context answer '$5,008 million' within 0.5% of '5,013'
        Q: What was Costco Wholesale Corp's net income in the 36 weeks ended May 12, 2024 (Q3 FY2024), as shown in its condensed consolidated statement
    - table JPM 10-Q I.2 [no_context] no-context answer '$8.9 billion' within 0.5% of '$8,944'
        Q: What was JPMorgan Chase & Co's Total Markets total net revenue for the three months ended September 30, 2025 (Q3 FY2025)?
    - table NVDA 10-Q I.1 [no_context:digits_only] no-context answer '$0.78' within 0.5% of '$0.78'
        Q: What was NVIDIA Corp's diluted net income per share for the three months ended Oct 27, 2024 (Q3 FY2025)?
    - table PFE 10-Q I.2 [no_context] no-context answer '$251 million' within 0.5% of '$251'
        Q: What were Pfizer Inc's worldwide Paxlovid revenues for the second quarter of fiscal year 2024 (quarter ended June 30, 2024)?
    - table TGT 10-K II.8 [no_context] no-context answer '$11,886 million' within 0.5% of '11,886'
        Q: What was Target Corporation's inventory balance as of February 3, 2024, the end of fiscal year 2023?
    - table TGT 10-Q I.1 [no_context] no-context answer '$24.5 billion' within 0.5% of '$24,531'
        Q: What was Target Corporation's total revenue for the three months ended May 4, 2024 (Q1 FY2024)?
    - table TGT 10-Q I.2 [no_context] no-context answer '$1,317 million' within 0.5% of '$1,317'
        Q: What was Target Corporation's operating income for the three months ended August 2, 2025 (Q2 FY2025)?

One drop is spurious (F-97): 0000320193-26-000013:38.1:38.1 (AAPL Q2 FY2026
diluted EPS, $2.01). The answer was "Unknown. I don't have a reliable figure
... its Q2 FY2026 earnings release ...", and the extractor read figures from a
date and labels (`['28,', '2026,', '10', '2', '2026']`); "2" is within 0.5% of
2.01. The rule and extractor are frozen from the first no-context call; the drop
stands. The other 17 drops match a figure the answer states.

## 2026-10-01 — Near-duplicate stage and slot fill (no candidates file)

`scripts/seed_build.py` now runs the near-duplicate stage (`drop_near_duplicates`
and `near_duplicates`, written before the run, unchanged): question embeddings
from the local retrieval model, cosine > `near_duplicate_cosine` (0.92) against
the 200 existing candidates' questions and earlier seeded questions in draw
order; then `fill_slots`. It writes no candidates or reserve file. Two runs left
`dropped_v1.jsonl` byte-identical (44 lines). `make test`: 346 passed; `make
lint` clean.

`python -m scripts.seed_build` (near-duplicate part):

    near-duplicate stage (cosine > 0.92, question embeddings, against 200 existing candidates and earlier seeded questions): 4 dropped, appended to eval/seeding/dropped_v1.jsonl
      0001628280-26-054343:1228.0:1228.0 ~ 0000019617-25-000615:1270.0:1270.0 (cosine 0.935): For JPMorgan Chase & Co in the six months ended June 30, 2026 (Q2 FY2026), what was the fa
      0000034088-24-000050:122.0:122.0 ~ 0000034088-25-000042:83.0:83.0 (cosine 0.962): What was Exxon Mobil Corporation's total sales and other operating revenue, in millions of
      0000034088-24-000068:242.0:242.0 ~ 0000034088-24-000068:224.0:224.0 (cosine 0.956): What were Exxon Mobil Corporation's total Specialty Products earnings (U.S. GAAP), in mill
      0001045810-24-000316:197.0:198.0 ~ 0001045810-25-000230:188.0:191.0 (cosine 0.927): In NVIDIA Corp's 10-Q for the third quarter of fiscal year 2025, what types of arrangement
      highest cosine of a seeded question to an existing candidate: max 0.909, median 0.772
    
    slot fill (first survivors in draw order): candidates 83 ({'table': 47, 'synthesis': 36} of slots {'table': 50, 'synthesis': 40}); reserve 53
      short strata (7): synthesis AAPL 10-K I.1A 0/1, synthesis COST 10-K I.1A 0/1, synthesis NVDA 10-K I.1A 0/1, synthesis TGT 10-K I.1A 0/1, table AAPL 10-K II.8 1/2, table AAPL 10-K IV.15 0/1, table AAPL 10-Q I.2 0/1
    no candidates or reserve file written: the llm_seeded item fields are not decided

Correction to F-88 as first written in this commit's predecessor: none of the 4
near-duplicate drops is against an existing candidate. All four partners are
seeded chunks, and the highest cosine of a seeded question to an existing
candidate is 0.909, below 0.92.

## 2026-10-01 — llm_seeded candidates written (83), reserve, review sheet

`eval/generate/seed_items.py` (item fields, manifest entry, scale tag,
same-filing figure search) and the writer in `scripts/seed_build.py`. Tests:
`tests/unit/test_seed_items.py` (4). `make test`: 350 passed; `make lint`: 94
files already formatted. Two rebuilds left every output byte-identical.

`python -m scripts.seed_build` (last lines):

      short strata (7): synthesis AAPL 10-K I.1A 0/1, synthesis COST 10-K I.1A 0/1, synthesis NVDA 10-K I.1A 0/1, synthesis TGT 10-K I.1A 0/1, table AAPL 10-K II.8 1/2, table AAPL 10-K IV.15 0/1, table AAPL 10-Q I.2 0/1
    wrote eval/candidates/llm_seeded_candidates.jsonl: 83 items {'table': 47, 'synthesis': 36}, validation failures 0, sha256 f1b7849ab81e5299
    wrote eval/candidates/llm_seeded_manifest.json, eval/seeding/reserve_v1.json (53 reserve), eval/candidates/llm_seeded_review.md

Tag counts over the 83 (ad hoc): kind:factual 47, kind:interpretive 36,
unit_scale_millions 33, unit_scale_billions 4, unit_scale_unknown 10,
parenthesized 7, quarter_label_on_span 6, no_context:near_match 2,
seed_backend:claude_cli 83, seed_model:claude-sonnet-5-5 83. Other same-filing
chunks printing a table item's figure, items by count: 0: 21, 1: 7, 2: 12, 3: 3,
4: 2, 5: 2. No email address or "/Users/" in any of the four new files.

Gold-exclusion globs in `seed_draw`, `seed_supply` and `seed_run` now take the 200 auto candidates only (the seeded file would otherwise widen the exclusion). `python -m scripts.seed_draw` then reproduces `draw_v2.json` byte-identical (sha256 1c23e9f6...): a reproducibility check, not a re-draw.

## 2026-10-01 — Metrics as pure functions (nothing computed on answers)

`eval/metrics/retrieval.py` (Sufficiency@k, Recall@k, Precision@k, MRR, nDCG@k
per F-77), `eval/metrics/numeric.py` (F-81: new extractor masking dates, period
labels, form names, item numbers, period lengths and bare years; claim figure
objects first; exact at printed precision, magnitude; strict, tolerant, sign,
values-only reported), `eval/metrics/abstention.py` (2x2; PARTIAL raises, F-21).
Tests: `test_metrics_retrieval.py` (7), `test_metrics_numeric.py` (27, including
F-97's "Unknown ... Q2 FY2026 ... March 28, 2026" answer, which yields no figure),
`test_metrics_abstention.py` (3). `make test`: 387 passed.

The reference reader alone, run over the candidates' reference answers (ad hoc;
no answer was scored):

    reference figures parsed: {'xbrl': 160, 'comparison': 40, 'seeded:scored': 37, 'seeded:unit_scale_unknown': 10, 'seeded:not numeric': 36}; disagreements with the manifests: 0

## 2026-10-01 — Eval runner built (not run)

`eval/runner.py`, `scripts/eval_run.py`, config `eval_run` (k 10, retrieve_depth
10, runs_dir). Tests: `tests/unit/test_runner.py` (3). `make test`: 390 passed;
`make lint`: 104 files already formatted.

`python -m scripts.eval_run` (plan only):

    backend claude_cli (claude-haiku-4-5-20251001, tier_small); items 283 {'xbrl_auto': 200, 'llm_seeded': 83}; k 10
    plan only: pass --run to retrieve and generate

`python -m scripts.eval_run --baseline-out eval/baselines/main.json`:

    api.config.ConfigError: refusing to write eval/baselines/main.json: backend claude_cli is development-only (TRADEOFFS, OWNER DECISION - Max subscription as dev generator)

Report shape, rendered from the synthetic items and results of `test_runner.py`
(no candidate was retrieved or answered):

    run r1  backend: claude_cli  generation model requested: m
    DEVELOPMENT RUN (claude_cli): not a CI baseline, not publishable, not comparable with anthropic_api runs (F-59)
    served models: {'claude-haiku-4-5-20251001': 3}  retrieval measured on: dense top-k (F-13)
    metric                               xbrl_auto    llm_seeded   handwritten     aggregate
    items                                        1             2             -             3
    retrieval items                              1             2             -             3
    Sufficiency@10                           1.000         0.500             -         0.667
    Recall@10                                1.000         0.500             -         0.667
    Precision@10                             0.100         0.050             -         0.067
    MRR                                      0.500         0.500             -         0.500
    nDCG@10                                  0.631         0.500             -         0.544
    Sufficiency@10 post-rerank                   -             -             -             -
    Numeric accuracy (gated)                 1.000             -             -         1.000
      numeric items scored                       1             0             -             1
      excluded unit_scale_unknown                0             1             -             1
      strict first figure                    1.000             -             -         1.000
      within 0.5% (reported)                 1.000             -             -         1.000
      comparison values only                     -             -             -             -
      sign agreement                             -             -             -             -
      free-text fallback used                    1             0             -             1
      mean figures per answer                1.000             -             -         1.000
    False-answer rate                            -             -             -             -
    Over-abstention rate                     0.000         0.000             -         0.000
    Abstention F1                                -             -             -             -

## 2026-10-01 — First dev eval run: process killed once (logged per protocol)

Run 19693d4aa874 (`python -m scripts.eval_run --run`) started 20:10:28Z. I ran it in
the foreground by mistake; the tool's 2-minute timeout killed it at about
20:12:36Z with 10 items recorded in `19693d4aa874.results.jsonl` and the 11th call
(cmp_0011) in flight, lost unrecorded. No errors file. Resumed with `--resume
19693d4aa874` in the background; cmp_0011 is asked again.
Second kill, same cause (resumed in the foreground, not backgrounded): started
20:12:46Z, killed at about 20:14:54Z with 19 items recorded (all distinct) and the
20th call (cmp_0020) in flight, lost unrecorded. Resumed again, backgrounded.
Third kill, same cause: started 20:15:00Z, killed at about 20:17:10Z with 25 items
recorded (all distinct), the 26th (cmp_0026) in flight, lost unrecorded. Resumed
detached (`nohup ... &`) so the tool timeout cannot reach it.

## 2026-10-01 — First dev eval run 19693d4aa874: complete

`python -m scripts.verify_freeze` passed first (96 accessions, 0 mismatches;
22,354 chunks on chunker_version 964f77f6f9cb). The detached resume ran from
20:17:18Z to about 20:59Z; in all 283 results, 283 distinct, no errors file, no
traceback. Three in-flight calls were lost to the three kills above and asked
again on resume. Files committed: `eval/runs/19693d4aa874.meta.json`,
`.results.jsonl`, `.json` (report).

Printed report, as printed:

    run 19693d4aa874  backend: claude_cli  generation model requested: claude-haiku-4-5-20251001
    DEVELOPMENT RUN (claude_cli): not a CI baseline, not publishable, not comparable with anthropic_api runs (F-59)
    served models: {'claude-haiku-4-5-20251001': 283}  retrieval measured on: dense top-k (Phase 2 baseline; no fusion, no rerank) (F-13)
    metric                               xbrl_auto    llm_seeded   handwritten     aggregate
    items                                      200            83             -           283
    retrieval items                            200            83             -           283
    Sufficiency@10                           0.285         0.675             -         0.399
    Recall@10                                0.295         0.675             -         0.406
    Precision@10                             0.051         0.067             -         0.056
    MRR                                      0.135         0.477             -         0.235
    nDCG@10                                  0.172         0.524             -         0.275
    Sufficiency@10 post-rerank                   -             -             -             -
    Numeric accuracy (gated)                 0.375         0.757             -         0.435
      numeric items scored                     200            37             -           237
      excluded unit_scale_unknown                0            10             -            10
      strict first figure                    0.330         0.703             -         0.388
      within 0.5% (reported)                 0.415         0.757             -         0.468
      comparison values only                 0.225             -             -         0.225
      sign agreement                         1.000         1.000             -         1.000
      abstained (in denominator)                 0             0             -             0
      free-text fallback used                  200            37             -           237
      mean figures per answer                4.120         4.541             -         4.186
    PARTIAL rate                             0.000         0.000             -         0.000
    False-answer rate                            -             -             -             -
    Over-abstention rate                     0.000         0.000             -         0.000
    Abstention F1                                -             -             -             -
    figures per numeric answer (aggregate): {'0': 32, '1': 28, '2': 26, '3': 34, '4': 27, '5': 20, '6': 15, '7': 21, '8': 8, '9': 9, '10': 4, '11': 2, '12': 3, '13': 1, '14': 4, '16': 1, '17': 1, '20': 1}
    excluded from numeric accuracy (aggregate): {'unit_scale_unknown': 10, 'not numeric': 36}
    anomalies: {'empty_retrieval': [], 'empty_answer': [], 'latency_s': {'p50': 7.88, 'p95': 16.39, 'max': 98.75}, 'slow_items_over_3x_p50': [('cmp_0023', 43.52), ('cmp_0040', 68.95), ('seed_0026', 37.05), ('seed_0047', 24.62), ('xbrl_0064', 98.75), ('xbrl_0135', 60.29), ('xbrl_0136', 25.88), ('xbrl_0141', 50.66)]}

Read-only diagnosis of what looks off (ad hoc over the results; nothing
re-scored or changed):

    numeric answers with no extracted figure: 32 by source {'xbrl_auto': 30, 'llm_seeded': 2}
        cmp_0001 '# Unable to Answer with Provided Excerpts\n\nI cannot provide the specific net income figures for Q3 FY2024 and Q3 FY2026 based on the SEC fil'
        cmp_0012 "I appreciate your question, but I notice there's a mismatch between what you're asking and the documents provided.\n\n**You asked about:** Cos"
        cmp_0013 "# Unable to Answer\n\nI cannot find Costco income tax expense information in the SEC filing excerpts provided. The excerpts you've shared cont"
    answers with decline wording (regex, all items): 106
    xbrl_numeric: 160 items; top-10 holds a chunk from a gold accession: 148
    comparison: 40 items; top-10 holds a chunk from a gold accession: 37
    xbrl_numeric: top-10 holds a chunk of the item's own company (among accessions known from gold): 152
    comparison: top-10 holds a chunk of the item's own company (among accessions known from gold): 37
    numeric accuracy split inside xbrl_auto: xbrl_numeric 66/160; comparison 9/40
    xbrl_auto (sufficient@10, numerically correct): {(False, False): 112, (True, True): 44, (True, False): 13, (False, True): 31}
    correct under any-figure but not strict-first-figure: 11

Findings logged: F-98 (xbrl_auto is the hard slice here), F-99 (the baseline
cannot abstain; declines score as wrong answers), F-100 (numerically correct
without sufficient retrieval), F-101 (gated vs strict numeric gap), F-102
(latency outliers).

## 2026-10-01 — F-100 split (read-only over run 19693d4aa874)

`python -m scripts.f100_check 19693d4aa874`:

    items correct without a sufficient gold set: 31
      figure present in a retrieved non-gold chunk: 29 ['cmp_0006', 'cmp_0009', 'cmp_0010', 'cmp_0016', 'cmp_0018', 'xbrl_0008', 'xbrl_0017', 'xbrl_0029', 'xbrl_0038', 'xbrl_0039', 'xbrl_0048', 'xbrl_0063', 'xbrl_0066', 'xbrl_0069', 'xbrl_0072', 'xbrl_0075', 'xbrl_0079', 'xbrl_0084', 'xbrl_0090', 'xbrl_0096', 'xbrl_0100', 'xbrl_0102', 'xbrl_0104', 'xbrl_0111', 'xbrl_0123', 'xbrl_0124', 'xbrl_0137', 'xbrl_0138', 'xbrl_0145']
      figure in no retrieved chunk: 2 ['xbrl_0049', 'xbrl_0116']
    wrote eval/candidates/f100_19693d4aa874.json

Hits checked by eye: xbrl_0008 (Apple SG&A $6,650) and xbrl_0100 (NVIDIA
operating income $36,010) are printed in the 10-Q MD&A tables, untagged; cmp_0006's
two BAC pre-tax figures likewise. The 29 are flagged in a new section of
`xbrl_numeric_spot_check.md` / `comparison_spot_check.md` (and `flagged_f100` in
both manifests), with the matching non-gold chunk and row. Both candidate files
are byte-identical; both `--verify` runs 0 mismatches. `make test`: 391 passed.

## 2026-10-01 — `make eval`

Target added: `python -m scripts.verify_freeze`, then `python -m scripts.eval_run
--run` (report stamped with the backend; dev banner on claude_cli). `make -n eval`
prints exactly those two commands (`tests/unit/test_make_eval.py`). Not run here.
`make eval-fast` is Phase 4.

## 2026-10-01 — Hand-written authoring kit (no items)

Templates per type under `eval/handwritten/templates/` (fields fixed by the
schema pre-filled; `expected_abstain` true for unanswerable, false for
natural_phrasing, and per adversarial subtype: true for entity_confusion and
investment_advice as PRD 11.1 states, null for false_premise and prompt_injection
so the author must decide); empty item files; config `eval_handwritten`;
`eval/generate/handwritten.py` and `scripts/handwritten_validate.py`. Tests:
`tests/unit/test_handwritten.py` (4). `make test`: 396 passed; `make lint` clean.

`python -m scripts.handwritten_validate` on the empty files (exit 1):

    files: ['eval/handwritten/adversarial.jsonl', 'eval/handwritten/natural_phrasing.jsonl', 'eval/handwritten/unanswerable.jsonl']; items 0
      unanswerable: 0 of 50
      adversarial: 0 of 20
      natural_phrasing: 0 of 30
    problems: 3
      unanswerable: 0 items, PRD 11.1 asks for 50
      adversarial: 0 items, PRD 11.1 asks for 20
      natural_phrasing: 0 items, PRD 11.1 asks for 30

## 2026-10-01 — Hand-written comparisons added to the kit (F-84)

`templates/comparison.json`, empty `comparison.jsonl`, `comparison: 20` in
`eval_handwritten.targets`; comparison checks in `eval/generate/handwritten.py`
(answerable, at least one evidence set, `xbrl_fact_id` null; chunks, accessions
and near-duplicates as for the rest). One-chunk sets are allowed (F-83, F-84).
Tests: `test_comparison_rules` and the good-item case. `make test`: 397 passed.

`python -m scripts.handwritten_validate` on the empty files (exit 1):

    files: ['eval/handwritten/adversarial.jsonl', 'eval/handwritten/comparison.jsonl', 'eval/handwritten/natural_phrasing.jsonl', 'eval/handwritten/unanswerable.jsonl']; items 0
      unanswerable: 0 of 50
      adversarial: 0 of 20
      natural_phrasing: 0 of 30
      comparison: 0 of 20
    problems: 4
      unanswerable: 0 items, PRD 11.1 asks for 50
      adversarial: 0 items, PRD 11.1 asks for 20
      natural_phrasing: 0 items, PRD 11.1 asks for 30
      comparison: 0 items, PRD 11.1 asks for 20

## 2026-10-01 — Review CLI (no decisions)

`eval/review_decisions.py`, `scripts/review.py` (worksheet / import / status),
`eval/review/decisions_v1.jsonl` (empty), worksheets for the three sheets (44, 9
and 83 items). Tests: `tests/unit/test_review.py` (4). `make test`: 401 passed;
`make lint`: 112 files already formatted.

`python -m scripts.review status`:

    decisions on file: 0 (eval/review/decisions_v1.jsonl)
      comparison_candidates.jsonl: 40 items; {'undecided': 40}
      llm_seeded_candidates.jsonl: 83 items; {'undecided': 83}
      xbrl_numeric_candidates.jsonl: 160 items; {'undecided': 160}

## 2026-10-01 — LLM judge tooling (no judge run, no kappa)

`eval/judge/{rubrics,judge,agreement}.py`, `scripts/judge.py`, config
`eval_judge`. `python -m scripts.judge labels` wrote `eval/judge/label_sheet_v1.md`
and `eval/judge/labels_v1.yaml`: "50 pairs {'llm_seeded': 15, 'xbrl_auto': 35}";
`eval/judge/verdicts_v1.jsonl` empty. `python -m scripts.judge run --run`: "labels
0 of 50: the judge runs only on a fully labelled set, with --run"; `python -m
scripts.judge kappa`: "labels 0 of 50, verdicts 0: kappa needs both complete".
Tests: `tests/unit/test_judge.py` (5). `make test`: 406 passed; `make lint`: 119
files already formatted.

## 2026-10-01 — Phase 3 exit, step 1: claim-level metrics (F-10, F-09 resolved)

Inventory of PRD 14's Phase 3 metrics and PRD 11.2's generation metrics in
`eval/metrics/` before this step: present and tested -- Sufficiency@k, Recall@k,
Precision@k, MRR, nDCG@k (`retrieval.py`), numeric accuracy (`numeric.py`), the
abstention 2x2 (`abstention.py`). Missing -- faithfulness_pre/post, verifier
lift, claim retention, citation coverage, citation precision, unit-scale
accuracy, period accuracy, XBRL contradiction rate. Added as pure functions over
`claims_pre`/`claims_post` (PRD 7.4 claim shape plus the verifier's `checks`) in
`eval/metrics/generation.py`, tested on inline claims (`test_metrics_generation.py`,
4); the runner prints them as "n/a: no claims" until Phase 4's structured output
lands, and faithfulness_pre always with the answer rate in brackets.
`eval_run.nli_threshold` is null (PRD 7.5 gives no value; calibrated in Phase 4)
and scoring claims refuses while it is. Still not built, judge- or
model-dependent: answer correctness (needs the validated judge, F-105), context
precision (judge), answer relevance (PRD 11.2's reconstructed-question cosine).
`make test`: 411 passed.

## 2026-10-01 — `make eval` (Phase 3 exit run): f2e616e0a7d7

Run detached (`nohup bash -c 'source .venv/bin/activate && make eval'`) from
21:18:41Z to about 22:06Z; `verify_freeze` passed first (96 accessions, 0
mismatches; 22,354 chunks on 964f77f6f9cb); 283 results, no errors file, no
traceback, not killed. Committed: `eval/runs/f2e616e0a7d7.{meta.json,results.jsonl,json}`
(no email address, no "/Users/").

Printed report, as printed:

    run f2e616e0a7d7  backend: claude_cli  generation model requested: claude-haiku-4-5-20251001
    DEVELOPMENT RUN (claude_cli): not a CI baseline, not publishable, not comparable with anthropic_api runs (F-59)
    served models: {'claude-haiku-4-5-20251001': 283}  retrieval measured on: dense top-k (Phase 2 baseline; no fusion, no rerank) (F-13)
    metric                                  xbrl_auto       llm_seeded      handwritten        aggregate
    items                                         200               83                -              283
    retrieval items                               200               83                -              283
    Sufficiency@10                              0.285            0.675                -            0.399
    Recall@10                                   0.295            0.675                -            0.406
    Precision@10                                0.051            0.067                -            0.056
    MRR                                         0.135            0.477                -            0.235
    nDCG@10                                     0.172            0.524                -            0.275
    Sufficiency@10 post-rerank                      -                -                -                -
    Numeric accuracy (gated)                    0.390            0.757                -            0.447
      numeric items scored                        200               37                -              237
      excluded unit_scale_unknown                   0               10                -               10
      strict first figure                       0.340            0.703                -            0.397
      within 0.5% (reported)                    0.425            0.757                -            0.477
      comparison values only                    0.250                -                -            0.250
      sign agreement                            1.000            1.000                -            1.000
      abstained (in denominator)                    0                0                -                0
      free-text fallback used                     200               37                -              237
      mean figures per answer                   4.020            5.486                -            4.249
    Faithfulness (pre) [answer rate]   n/a: no claims   n/a: no claims                -   n/a: no claims
    Faithfulness (post)                n/a: no claims   n/a: no claims                -   n/a: no claims
    Verifier lift                      n/a: no claims   n/a: no claims                -   n/a: no claims
    Claim retention                    n/a: no claims   n/a: no claims                -   n/a: no claims
    Citation coverage                  n/a: no claims   n/a: no claims                -   n/a: no claims
    Citation precision                 n/a: no claims   n/a: no claims                -   n/a: no claims
    Unit-scale accuracy                n/a: no claims   n/a: no claims                -   n/a: no claims
    Period accuracy                    n/a: no claims   n/a: no claims                -   n/a: no claims
    XBRL contradiction rate            n/a: no claims   n/a: no claims                -   n/a: no claims
    PARTIAL rate                                0.000            0.000                -            0.000
    False-answer rate                               -                -                -                -
    Over-abstention rate                        0.000            0.000                -            0.000
    Abstention F1                                   -                -                -                -
    figures per numeric answer (aggregate): {'0': 41, '1': 24, '2': 26, '3': 28, '4': 28, '5': 18, '6': 18, '7': 13, '8': 9, '9': 9, '10': 5, '11': 6, '12': 1, '13': 4, '14': 2, '15': 2, '16': 1, '17': 1, '22': 1}
    excluded from numeric accuracy (aggregate): {'unit_scale_unknown': 10, 'not numeric': 36}
    anomalies: {'empty_retrieval': [], 'empty_answer': [], 'latency_s': {'p50': 7.56, 'p95': 16.93, 'max': 76.66}, 'slow_items_over_3x_p50': [('cmp_0020', 58.06), ('cmp_0023', 27.5), ('cmp_0040', 38.54), ('seed_0026', 26.8), ('seed_0032', 37.23), ('seed_0047', 35.18), ('xbrl_0064', 76.63), ('xbrl_0125', 76.66), ('xbrl_0135', 26.55), ('xbrl_0141', 36.65)]}

Run-to-run spread against 19693d4aa874 (F-60), `python -m scripts.run_spread
19693d4aa874 f2e616e0a7d7`:

    run A 19693d4aa874 vs run B f2e616e0a7d7; same config: {'backend': True, 'model_requested': True, 'datasets': True, 'parser_version': True, 'chunker_version': True, 'k': True}
    served models A {'claude-haiku-4-5-20251001': 283} B {'claude-haiku-4-5-20251001': 283}
    metric (B - A)                     xbrl_auto    llm_seeded   handwritten     aggregate
    Sufficiency@10                        +0.000        +0.000             -        +0.000
    Recall@10                             +0.000        +0.000             -        +0.000
    MRR                                   +0.000        +0.000             -        +0.000
    nDCG@10                               +0.000        +0.000             -        +0.000
    Numeric accuracy (gated)              +0.015        +0.000             -        +0.013
      strict first figure                 +0.010        +0.000             -        +0.008
      within 0.5%                         +0.010        +0.000             -        +0.008
      comparison values only              +0.025             -             -        +0.025
    items in both runs: 283; identical retrieved list: 283
    numeric correctness flips: correct in A only 1, in B only 4
      A only: ['xbrl_0117']
      B only: ['cmp_0033', 'xbrl_0052', 'xbrl_0131', 'xbrl_0140']

## 2026-10-01 — Phase 3 exit statement

PRD 14's Phase 3 checklist, against the repo:

- **XBRL auto-generation, ~160 numeric items with auto-located evidence sets:**
  done. `eval/candidates/xbrl_numeric_candidates.jsonl` (160), plus 40 auto
  comparisons (`comparison_candidates.jsonl`, F-83).
- **Paraphrase templating, 4-6 surface forms per concept:** done.
  `eval/templates.yaml`: five forms per period type (`duration`, `instant`),
  filled with each line item's label, so every line item has five; five
  `comparison_forms` per type. Used by `eval/generate/xbrl_items.py` and
  `eval/generate/comparison.py`; the form id is a tag on every item.
- **LLM seeding for table/synthesis items + filters (verbatim, no-context,
  dedup):** done, development-grade. 83 `llm_seeded` candidates
  (`llm_seeded_candidates.jsonl`; 7 short slots, F-95), seeded and no-context
  checked on `claude_cli` (F-59, F-14).
- **Hand-write 50 unanswerable, 20 adversarial, 30 natural-phrasing (and the 20
  hand-written comparisons, F-84):** OWNER-BLOCKED, F-103. Kit built: templates,
  empty item files, `scripts.handwritten_validate`.
- **Human review:** OWNER-BLOCKED, F-104. Sheets and worksheets ready;
  `scripts.review`; decisions file empty.
- **Metrics (sufficiency@k over evidence sets, MRR, nDCG, faithfulness_pre/post,
  verifier lift, claim retention, abstention 2x2):** done as tested pure
  functions in `eval/metrics/`; the claim metrics print "n/a: no claims" until
  Phase 4's structured output (F-10, F-09 resolved). Answer relevance not built
  (F-107); answer correctness and context precision wait on the judge (F-105).
- **Per-source breakout for every gated metric:** done; the report has the
  `xbrl_auto`, `llm_seeded`, `handwritten` and aggregate columns.
- **LLM judge + Cohen's kappa against 50 hand labels:** tooling done
  (`eval/judge/`, `scripts.judge`); the 50 labels are OWNER-BLOCKED, F-105; no
  judge run and no kappa.
- **Runner, report generation:** done (`scripts.eval_run`, `make eval`).
  **Freeze `golden_v1`:** OWNER-BLOCKED, F-106 (waits on review and the
  hand-written items).
- **Exit: `make eval` prints a metrics table with four source columns for
  Config 1:** done, run f2e616e0a7d7 (Phase 2 dense baseline on `claude_cli`,
  development banner). *Not circular:* retrieval and numeric accuracy are scored
  against fixed gold, not against anything the system or a verifier produced;
  faithfulness is not computed yet ("n/a: no claims"), so its circularity fix
  (F-09) has nothing to act on. *Not carried by the easy slice:* the handwritten
  column is empty for the owner's reason (F-103), so this is checked on the two
  columns that exist: Sufficiency@10 is 0.285 on `xbrl_auto` and 0.675 on
  `llm_seeded`, aggregate 0.399, and numeric accuracy 0.390 / 0.757 / 0.447.
  The aggregate is not carried by `xbrl_auto`; contrary to PRD 11.2's premise it
  is the hard slice here (F-98). To be re-checked when the owner's items land.

Everything not done is OWNER-BLOCKED (F-103, F-104, F-105, F-106), except
answer relevance (F-107), which is not on the Phase 3 checklist.

## 2026-10-01 — Phase 4 starts: BM25-style sparse retrieval and RRF fusion, measured

`api/query/retrieve.py`: `sparse_top_k`, `rrf_fuse`, `hybrid_top_k`; `dense_top_k`
raises `hnsw.ef_search` to k above 40. Config `retrieval` (k_dense 50, k_sparse
50, rrf_k 60, weights 1.0/1.0). `eval/runner.retrieval_slice`;
`scripts/retrieval_run.py`. Tests: `tests/unit/test_rrf.py` (4). `make test`:
415 passed. No candidate, metric definition or threshold touched.

`python -m scripts.retrieval_run --compare f2e616e0a7d7` (1 min 32 s, no model
call; run file `eval/runs/188304ccaf94.retrieval.json`):

    retrieval run 188304ccaf94: 283 items; k 10; {'k_dense': 50, 'k_sparse': 50, 'rrf_k': 60, 'weights': {'dense': 1.0, 'sparse': 1.0}}
    dense top-10 identical to the stored list of: {'f2e616e0a7d7': 273}
    list / metric                    xbrl_auto    llm_seeded   handwritten     aggregate
    dense sufficiency@10                 0.290         0.675             -         0.403
    dense recall@10                      0.300         0.675             -         0.410
    dense mrr                            0.155         0.487             -         0.252
    dense ndcg@10                        0.174         0.524             -         0.277
    dense precision@10                   0.052         0.067             -         0.057
    sparse sufficiency@10                0.025         0.241             -         0.088
    sparse recall@10                     0.025         0.241             -         0.088
    sparse mrr                           0.012         0.127             -         0.046
    sparse ndcg@10                       0.012         0.151             -         0.053
    sparse precision@10                  0.005         0.024             -         0.010
    hybrid sufficiency@10                0.215         0.687             -         0.353
    hybrid recall@10                     0.217         0.687             -         0.355
    hybrid mrr                           0.119         0.368             -         0.192
    hybrid ndcg@10                       0.128         0.437             -         0.219
    hybrid precision@10                  0.038         0.069             -         0.047

Findings F-108 (the `ts_rank_cd` sparse branch is weak and fusion lowers dense)
and F-109 (dense top-10 depends on `ef_search`). Nothing tuned in response.

## 2026-10-01 — BM25 sparse branch; `ef_search` pinned (F-108, F-109 resolved)

`api/query/bm25.py` (tokenizer, Okapi BM25, cached index), `load_bm25` and
`sparse` in `api/query/retrieve.py`; `dense_top_k` takes `ef_search`; config
`retrieval.hnsw_ef_search: 100`, `retrieval.sparse` (bm25, k1 1.2, b 0.75); eval
run meta records `hnsw_ef_search` and `k_dense`. Tests: `tests/unit/test_bm25.py`
(4). `make test`: 419 passed.

`python -m scripts.exact_nn_check`:

    vectors 22354; questions 283; k 10; hnsw.ef_search 100
    top-10 lists differing from exact search: 0 (order or membership); membership overlap among them: []
      []

`python -m scripts.retrieval_run --compare f2e616e0a7d7` (index built, 37 s;
`eval/runs/01019ff395ec.retrieval.json`):

    retrieval run 01019ff395ec: 283 items; k 10; {'k_dense': 50, 'k_sparse': 50, 'rrf_k': 60, 'weights': {'dense': 1.0, 'sparse': 1.0}, 'hnsw_ef_search': 100, 'sparse': {'backend': 'bm25', 'k1': 1.2, 'b': 0.75}}
    bm25 index key 5a33c360a77f5bdf (rebuilt)
    dense top-10 identical to the stored list of: {'f2e616e0a7d7': 243}
    list / metric                    xbrl_auto    llm_seeded   handwritten     aggregate
    dense sufficiency@10                 0.290         0.699             -         0.410
    dense recall@10                      0.300         0.699             -         0.417
    dense mrr                            0.156         0.511             -         0.260
    dense ndcg@10                        0.174         0.548             -         0.284
    dense precision@10                   0.052         0.070             -         0.058
    sparse sufficiency@10                0.175         0.892             -         0.385
    sparse recall@10                     0.182         0.892             -         0.390
    sparse mrr                           0.071         0.707             -         0.257
    sparse ndcg@10                       0.090         0.746             -         0.282
    sparse precision@10                  0.029         0.089             -         0.046
    hybrid sufficiency@10                0.365         0.892             -         0.519
    hybrid recall@10                     0.375         0.892             -         0.527
    hybrid mrr                           0.178         0.639             -         0.313
    hybrid ndcg@10                       0.213         0.697             -         0.355
    hybrid precision@10                  0.062         0.089             -         0.070

Rerun from the cached index (key 5a33c360...): metrics identical (`diff` empty);
its duplicate run file was deleted. F-110 logged: the llm_seeded gain is BM25's
lexical overlap with seeded questions.

## 2026-10-01 — Cross-encoder reranking, measured post-rerank (F-13, F-111, F-112)

`api/query/rerank.py`, config `rerank` (bge-reranker-base @2cfc18c9, top-n 8 /
10 synthesis, floor 0.30 pending, timeout 800 ms), `scripts/rerank_run.py`.
Tests: `tests/unit/test_rerank.py` (3). `make test`: 422 passed. Model smoke
check: an Apple net-sales sentence scored 0.9995 against a bank-deposits one at
0.00004 for the exit question.

`python -m scripts.rerank_run 01019ff395ec` (detached, about 7 min;
`eval/runs/4aef651ade44.rerank.json`):

    rerank run 4aef651ade44 of retrieval run 01019ff395ec: 283 items; BAAI/bge-reranker-base@2cfc18c9415c; floor 0.3 (pending)
    metric                                 xbrl_auto    llm_seeded   handwritten     aggregate
    items                                        200            83             -           283
    pre_suff@8                                 0.330         0.867             -         0.488
    pre_suff@10                                0.365         0.892             -         0.519
    post_suff@top_n                            0.450         0.831             -         0.562
    post_recall@top_n                          0.465         0.831             -         0.572
    post_mrr                                   0.256         0.523             -         0.334
    post_ndcg@top_n                            0.305         0.597             -         0.390
    post_floor_suff@top_n (pending)            0.450         0.831             -         0.562
    floor_empties (abstain)                        0             0             -             0
    over_timeout                                 200            83             -           283
    latency per item (one pass of up to 50 pairs, this machine): {'p50': 1.403, 'p95': 1.792, 'max': 2.471}

The floor at 0.30 changes nothing; every item is over the 800 ms timeout on this
machine (F-111). The llm_seeded slice drops slightly after reranking, consistent
with F-110 (BM25's lexical advantage on seeded questions).

## 2026-10-01 — Reranker timeout (F-111): device and model measured

`rerank.device` in config; rerank runs record device, torch and machine
(`api.query.rerank.machine`) and exclude one warm-up pass from latency;
`scripts.rerank_run --model/--revision/--device` override config for a
measurement only. Checked: a CrossEncoder with no device lands on `mps:0`, so run
4aef651ade44 was on the GPU, not the CPU as first reported.

Rerank on mps, first attempt (22:30Z): launched inside a tool call that also polled; the call hit its 2-minute timeout and the process group was killed at about 50 of 283 items. Offline measurement, no run file written; relaunched on its own.

`python -m scripts.rerank_run 01019ff395ec` (bge-reranker-base, mps;
`eval/runs/dd372192a070.rerank.json`):

    rerank run dd372192a070 of retrieval run 01019ff395ec: 283 items; BAAI/bge-reranker-base@2cfc18c9415c; floor 0.3 (pending)
    metric                                 xbrl_auto    llm_seeded   handwritten     aggregate
    items                                        200            83             -           283
    pre_suff@8                                 0.330         0.867             -         0.488
    pre_suff@10                                0.365         0.892             -         0.519
    post_suff@top_n                            0.450         0.831             -         0.562
    post_recall@top_n                          0.465         0.831             -         0.572
    post_mrr                                   0.256         0.523             -         0.334
    post_ndcg@top_n                            0.305         0.597             -         0.390
    post_floor_suff@top_n (pending)            0.450         0.831             -         0.562
    floor_empties (abstain)                        0             0             -             0
    over_timeout                                 200            83             -           283
    latency per item (one pass of up to 50 pairs): {'p50': 1.406, 'p95': 1.802, 'max': 2.011}; warm-up pass (not counted) 2.189 s
    device mps; machine {'torch': '2.14.1', 'platform': 'macOS-27.0.1-arm64-arm-64bit', 'cpu': 'Apple M1 Pro', 'gpu': 'Apple M1 Pro (16 GPU cores)', 'ram_gb': 16.0, 'mps_available': True}

`... --model cross-encoder/ms-marco-MiniLM-L-6-v2 --revision 233902d2... --device cpu`
(`45e3ed5c8f13.rerank.json`):

    rerank run 45e3ed5c8f13 of retrieval run 01019ff395ec: 283 items; cross-encoder/ms-marco-MiniLM-L-6-v2@233902d25c44; floor 0.3 (pending)
    metric                                 xbrl_auto    llm_seeded   handwritten     aggregate
    items                                        200            83             -           283
    pre_suff@8                                 0.330         0.867             -         0.488
    pre_suff@10                                0.365         0.892             -         0.519
    post_suff@top_n                            0.270         0.819             -         0.431
    post_recall@top_n                          0.270         0.819             -         0.431
    post_mrr                                   0.118         0.518             -         0.235
    post_ndcg@top_n                            0.155         0.590             -         0.282
    post_floor_suff@top_n (pending)            0.270         0.819             -         0.431
    floor_empties (abstain)                        0             0             -             0
    over_timeout                                  31             3             -            34
    latency per item (one pass of up to 50 pairs): {'p50': 0.756, 'p95': 0.834, 'max': 1.061}; warm-up pass (not counted) 0.808 s

`... --device mps` (`46523deda1c0.rerank.json`):

    rerank run 46523deda1c0 of retrieval run 01019ff395ec: 283 items; cross-encoder/ms-marco-MiniLM-L-6-v2@233902d25c44; floor 0.3 (pending)
    metric                                 xbrl_auto    llm_seeded   handwritten     aggregate
    items                                        200            83             -           283
    pre_suff@8                                 0.330         0.867             -         0.488
    pre_suff@10                                0.365         0.892             -         0.519
    post_suff@top_n                            0.270         0.819             -         0.431
    post_recall@top_n                          0.270         0.819             -         0.431
    post_mrr                                   0.118         0.518             -         0.235
    post_ndcg@top_n                            0.155         0.590             -         0.282
    post_floor_suff@top_n (pending)            0.270         0.819             -         0.431
    floor_empties (abstain)                        0             0             -             0
    over_timeout                                   0             0             -             0
    latency per item (one pass of up to 50 pairs): {'p50': 0.259, 'p95': 0.272, 'max': 0.51}; warm-up pass (not counted) 1.083 s

Adopted: MiniLM on mps (the only one under 800 ms). F-111 resolved; F-113 logged
(MiniLM reranks below the fused order).

## 2026-10-01 — `make eval` on Config 4 (supervisor decision 2)

Commit bf0accd: `eval/pipeline.py` (`context_for`, `PIPELINES`), `eval_run`
stores the pre- and post-rerank lists and `generator_input`; `make test` 430
passed after the fix below, lint clean.

First launch (22:51Z) failed at the first item: `TypeError: answer_one() takes 5
positional arguments but 6 were given`. bf0accd changed `answer_one` but not its
call in `main`; the stubbed smoke test called `answer_one` directly, so it did not
reach the call. Nothing recorded; `eval/runs/b400b99f7086.meta.json` is kept as
the artefact. Fixed in 17a803d; relaunched 22:56Z as run 63cf35c328e2.
