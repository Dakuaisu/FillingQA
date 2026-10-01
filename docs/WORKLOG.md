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
