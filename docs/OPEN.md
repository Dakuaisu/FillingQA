# OPEN — findings register

Every finding raised against the PRD or discovered while building, with the phase
it blocks and its current status. Resolved entries stay here with their date so
this file is the complete record rather than a to-do list.

`docs/TRADEOFFS.md` carries the reasoning behind each resolution. This file
carries the state.

**Last updated: 2026-10-01**

| Status | Count |
|---|---|
| OPEN | 30 |
| RESOLVED | 27 |
| **Total** | **57** |

---

## Blocking now

| ID | Finding | Blocks | Status |
|---|---|---|---|
| F-32 | 30–56% of numeric iXBRL facts sit on dimensional (segmented) contexts — segment/product breakdowns, not company-level figures | Phase 3 | OPEN |

## Blocking Phase 2

| ID | Finding | Status |
|---|---|---|
| F-42 | The eval corpus is still defined as `years_back: 3`, a window relative to the run date. Must become an explicit accession list before the end-of-Phase-2 freeze (TRADEOFFS 2026-10-01). The freeze record per filing is `(accession, text_sha256, parser_version)`: raw hash differs but `text_sha256` matches is logged, not failed; `text_sha256` differs under the same `parser_version` fails. `filings.parser_version` and `norm_path` are written by the step 6 validation runner (2026-10-01), so the record's inputs exist; the accession list itself is still to do | OPEN |
| F-54 | TGT's per-section running headers ("CYBERSECURITY Table of Contents Index to Financial Statements") repeat fewer than `furniture_min_repeats` times, survive as layout-as-prose, and leave 12-29 nav fragments inside TGT prose chunks per filing (at 500 tokens; `navres` in the chunk summary). 0 in AAPL and COST. Revisit after the full ingest; fix by mechanism (a leaf block made entirely of in-document `<a href="#...">` anchors is navigation), as a parser change with an F-50-style diff -- no phrase rule | OPEN |
| F-56 | TGT's 10-K exhibit index is a layout table kept as prose whose entries run "...by reference). 4.2 Description...": the sentence splitter never breaks before a digit, so two units of 648 and 992 tokens cannot be split and exceed `max_seq_length` | OPEN |

## Blocking Phase 3

| ID | Finding | Status |
|---|---|---|
| F-11 | `xbrl_auto` is 49% of the eval set, not the 39% §11.2 argues from; `natural_phrasing` has no home in the `source` enum | OPEN |
| F-48 | 101 of 3,881 linked facts (2.6%) are tagged only in `ix:hidden` (shares authorized, par value, segment counts), so they have no span and no gold chunk; PRD 6.5.3 routes them to human labeling | OPEN |
| F-13 | `sufficiency@10` has no defined measurement point — post-rerank vs post-fusion | OPEN |
| F-07 | All seven gated thresholds have drifted between §11.2 prose and `thresholds.yaml` | OPEN |
| F-08 | `faithfulness_pre` is undefined for Configs 1–4, yet §11.6 plots it there | OPEN |
| F-09 | Abstained items in generation-metric denominators — a third circularity | OPEN |
| F-14 | Judge must be a different model family, but CI carries one provider key | OPEN |
| F-15 | `CURATED_CONCEPTS` yields near-zero items for JPM and BAC | OPEN |
| F-20 | `natural_phrasing_gap` is gated in `thresholds.yaml` but never defined as a metric | OPEN |

## Blocking Phase 4

| ID | Finding | Status |
|---|---|---|
| F-10 | `supported()` omits `citation_valid` for figure claims, contradicting §7.5's own table | OPEN |
| F-12 | `eval.compare` compares a fast/CI-corpus run against a full-corpus baseline | OPEN |
| F-16 | Chunk-size and context-header ablations need a full re-embed; budget is ~10× short | OPEN |
| F-21 | `PARTIAL` verdict has no place in the abstention 2×2 or the API examples | OPEN |
| F-57 | PRD 11.7's chunk-size ablation lists 256 / 512 / 800 / 1200 tokens; 800 and 1200 exceed bge-base-en-v1.5's 512-token input (F-53), so those points would embed truncated chunks | OPEN |

## Blocking Phase 5

| ID | Finding | Status |
|---|---|---|
| F-47 | No restatement count can be published yet: companyfacts drops iXBRL `decimals`, so a figure printed exactly in one place and rounded in another (AAPL LongTermDebt 90,678M vs 90,700M) diverges like a real restatement (TGT 2016 equity 12,957M -> 12,965M). Phase 1's exit only needs the query to return rows, which it does. No restatement number appears anywhere until this is resolved | OPEN |

## Non-blocking

| ID | Finding | Status |
|---|---|---|
| F-17 | US-4 and `GET /documents/{accession}/content` promise span highlighting that §10 explicitly cut | OPEN |
| F-18 | §2.2 says "20–40 companies is enough"; §4.4 sets 8 and argues why | OPEN |
| F-19 | §4.4's 50k–130k chunk estimate looks 4–10× high | OPEN |
| F-23 | "Threshold" is undefined for CLAUDE.md rule 4 — gate thresholds vs pipeline params | OPEN |
| F-24 | §15's prompt-injection fixture is synthetic corpus data, which CLAUDE.md rule 2 forbids | OPEN |
| F-26 | PRD §4.4 says four sectors but its company table describes PFE as "Pharma" | OPEN |
| F-33 | 4–5 word-form numbers per filing ("one", "two") don't parse | OPEN |
| F-46 | Some `layout` tables carry prose content, not scaffolding: TGT's critical audit matters and cybersecurity-oversight tables, AAPL's audit-matter tables. Phase 2 must chunk layout tables as prose rather than drop them | OPEN |
| F-55 | `page_hint` is not computed; `chunks.page_hint` is NULL. PRD 6.2 step 5, the 9 API response and the 10 source panel all carry it | OPEN |
| F-49 | companyfacts `fp` carries `Q4` (601 facts) and null (618), contradicting PRD 6.5.2's `'FY' \| 'Q1' \| 'Q2' \| 'Q3'`; all in `xbrl_facts_unlinked` -- 0 linked facts have either | OPEN |
| F-52 | A table with no label column (TGT 10-K "Net Sales" chart: `$107.4 | $106.6 | $104.8`) puts its first value column in the label slot, so "2023 (53 weeks)" is missing from `fiscal_periods`. Markdown alignment is still right. 1 of 404 tables (AAPL's exhibit indexes look similar but correctly use exhibit numbers as row labels) | OPEN |

## Resolved

| ID | Finding | Resolution | Date |
|---|---|---|---|
| F-01 | `xbrl_facts` key collides on QTD vs YTD facts in Q2/Q3 10-Qs | `period_start` added to the key; `UNIQUE NULLS NOT DISTINCT` so instant facts still dedupe | 2026-08-30 |
| F-02 | iXBRL offsets and chunk offsets are different coordinate systems; normalized text had nowhere to live | Extraction and flattening made one traversal; `filings.norm_path` added; verified 0 mismatches across 12 filings on an independent lxml check | 2026-08-30 |
| F-03 | `companyfacts` returns accessions outside `filings`, violating the FK | `xbrl_facts_unlinked` staging table, kept for restatement history. Exercised 2026-10-01: 70,999 unlinked facts across 3 companies, restatement query reads both tables | 2026-08-30 |
| F-04 | 10-Q Part I and Part II each have an Item 1 and Item 1A | `Section.part` tracked; `qualified_code` yields `I.1` vs `II.1`. Verified on 8 real 10-Qs | 2026-08-30 |
| F-05 | `fiscal_year` cannot be read from submissions — no such field exists | Migration 0003 makes it nullable; populated at parse time from `dei:DocumentFiscalYearFocus`. Verified: TGT 10-K = FY2025 with `period_end` 2026-01-31 | 2026-08-30 |
| F-06 | Corpus scope contradicted itself across Phases 1/2/3/5 and §11.4's freeze rule | Eval corpus is 8 companies × 3 years, frozen at end of Phase 2; the 3×1 dev slice is parser development only | 2026-08-30 |
| F-22 | Rate limit stated as 10/s in PRD §6.1, 8/s "ceiling" in CLAUDE.md | Built to 8 req/s as the operating point, strict pacing, no burst | 2026-08-30 |
| F-25 | PRD §6.2's iXBRL sample mixes `lxml.etree` namespaces with `lxml.html`'s `text_content()` and cannot run | Treated as pseudocode; real implementation uses `etree` with `itertext()` | 2026-08-30 |
| F-27 | `ruff format` rewrites Python code blocks inside `docs/PRD.md` — a lint job would silently mangle the spec | `extend-exclude = ["docs", "data"]` | 2026-08-30 |
| F-28 | `filings.recent` is at the ~1000 cap for all three dev companies, each with a paginated older file | Cap assertion compares the window start against the oldest date in `recent`, not the entry count — a count-based check would false-alarm on every company | 2026-08-30 |
| F-29 | A 1-year filing-date window gives no company a coherent fiscal year | Logged; dev slice is parser development only. Reinforces F-06 | 2026-08-30 |
| F-30 | `dei` fiscal tags sit in `ix:hidden` inside a `display:none` div, so the walker skipped them and reported `fiscal_year=None` | `harvest_dei` walks the whole tree independently of the text pass | 2026-08-30 |
| F-31 | User-Agent was set on the constructed httpx client, so an injected client sent `python-httpx/0.28.1` | Headers sent explicitly on every request | 2026-08-30 |
| F-34 | Item headings are mid-line and lexically identical to cross-references; `^ITEM` matches only the TOC | Detection moved onto blocks. 23 headings, 0 false positives, vs 61 raw text matches | 2026-08-30 |
| F-36 | `.gitignore` corrupted with UTF-16 bytes by an external tool | Rewritten as clean UTF-8; `.bridge/` kept as a normal entry | 2026-08-30 |
| F-37 | `ixbrl.py` and `sections.py` had no tests and no committed fixtures | 3 real filings gzipped under `tests/fixtures/filings/` (0.31 MB) with a manifest; hash re-checked on every load; snapshot baseline hand-verified against printed figures before blessing | 2026-08-30 |
| F-38 | PRD §6.2's `Document` dataclass has no `full_text`, yet its validation calls `alpha_char_ratio(doc.full_text)` | Normalized text persisted to `data/norm/{accession}.txt` with sha256 | 2026-08-30 |
| F-40 | `docker-compose.yml` mounted the volume at `/var/lib/postgresql/data`; `pgvector/pgvector:pg18` refuses to start with that layout. Never caught because the old machine never ran Docker | Mount moved to `/var/lib/postgresql`. Verified: container healthy, PG 18.6, vector 0.8.6 | 2026-10-01 |
| F-41 | `make test` and CI run bare `pytest`, which does not put the repo root on `sys.path`, so `from tests.conftest import ...` fails collection. Only `python -m pytest` worked | `pythonpath = ["."]` in `[tool.pytest.ini_options]`. Verified: `make test` 59 passed, 3 snapshots passed | 2026-10-01 |
| F-43 | Re-downloaded raw bytes differ from `tests/fixtures/manifest.json` for all 3 fixtures: SEC's edge injects a 114-byte `<script>` before `</body>`. Parser output unaffected | Accession is the identity; `content_hash` stays raw sha256 as provenance; freeze compares `text_sha256` under a fixed `parser_version` (F-42). Manifest unchanged. AUTONOMOUS DECISION, TRADEOFFS 2026-10-01 | 2026-10-01 |
| F-44 | `make lint` failed: `ruff format --check` would reformat `tools/bridge.py` | `[tool.ruff.format] exclude = ["tools"]`; `ruff check` still covers it; file untouched. Verified: `23 files already formatted`. AUTONOMOUS DECISION, TRADEOFFS 2026-10-01 | 2026-10-01 |
| F-35 | TGT's 10-K has 250 table blocks vs AAPL's 54; most are layout scaffolding, not data | `classify()`: data iff some row holds two or more figures. TGT 10-K: 64 data / 186 layout, layout inspected by text (80 page footers, ~70 running headers, cover/signature/TOC). Split for all 12 filings in WORKLOG | 2026-10-01 |
| F-45 | COST states units once per section, so the 500-char caption window found no scale for 13-24 iXBRL-scaled tables per COST filing | Caption, else the single magnitude `scale` on the table's tagged figures, else None; never section inheritance. `scale_source` on Table and Block. Monetary veto: a currency figure off the chosen magnitude gives None plus `scale_conflict`; fired 0 times on the slice, now a fixture invariant. Mixed-magnitude tables stay None (AAPL 1, COST 2 per filing). Residual with no caption and no tagged magnitude, per filing: AAPL 10-K 4, 10-Qs 0/0/0; COST 10-K 12, 10-Qs 8/8/8; TGT 10-K 14, 10-Qs 9/8/9 (mostly genuinely unscaled: counts, percentages). AUTONOMOUS DECISION, TRADEOFFS 2026-10-01 | 2026-10-01 |
| F-39 | `api/config.yaml` sector labels existed but nothing read them; `companies.sector` was NULL | `upsert_company` writes the label via `sector_of`, which raises on an unlabelled ticker. Verified: AAPL tech, COST retail, TGT retail | 2026-10-01 |
| F-50 | Continuation tables with no header row of their own got the preceding table's caption scale: percentage-only tables read "in millions" | Caption window stops at the end of a preceding table; never inherit labels or scale from a neighbour. 8 percentage tables now unscaled, 4 untagged TGT ROIC tables lose a borrowed scale. Residual: 11 header-less data tables on the slice stay header-less -- the chunker must emit no column-label line for them, not an empty one. AUTONOMOUS DECISION, TRADEOFFS 2026-10-01 | 2026-10-01 |
| F-51 | A dash-only first data row was taken as a header row | A row whose cells right of the label column are all dashes is a body row. Header rows changed on exactly 1 of 404 data tables (AAPL 0000320193-26-000020 share repurchases) | 2026-10-01 |
| F-53 | PRD 6.3's 500-800-token chunks (Appendix A: 700) exceed bge-base-en-v1.5's 512-token input and would be silently truncated; no tokenizer was installed | `target_tokens: 500` counted with the pinned model's own vendored tokenizer, header and special tokens included; `max_seq_length: 512` violations counted, never truncated. 12 filings: 0 over 512 except 2 in TGT's 10-K (F-56). Consequence: PRD 11.7's 800 and 1200-token chunk-size ablation points are impossible on bge-base (F-57). AUTONOMOUS DECISION, TRADEOFFS 2026-10-01 | 2026-10-01 |

---

## Recommendations for the open items

Kept separate from the tables so the tables stay scannable.

**F-32 — dimensional contexts.** Record `is_dimensional` on every context (done)
and require Phase 3's auto-generation to filter on it. A segment revenue line is
not "revenue"; templating a question from one produces a wrong answer with a
correct-looking citation.

**F-37 — parser tests.** Commit 2–3 real filings gzipped under
`tests/fixtures/filings/` with a manifest recording accession, CIK, form,
`period_end`, source URL and sha256 (CLAUDE.md rule 2: fixtures must be real
filings). Then snapshot `extract()` and `detect_sections()` output with syrupy.

**F-42 — eval corpus as accession list.** Run the 3-year window once to list
candidates, review them, and commit the resulting accessions under `corpus` in
`api/config.yaml`. Ingest reads the list, never the window.

**F-47 — restatement count.** Phase 5: the README count and the "later
restated" annotation. Separate rounding from restatement first; `decimals` is not
captured now, by decision.

**F-48 — hidden-only facts.** Exclude them from `xbrl_auto` generation or
accept them into the human-labeling queue; at 2.6% either is affordable.

**F-11 — source taxonomy.** Settle before generating any item. Carve
`natural_phrasing` out via `tags`, decide whether it sits inside or outside the
handwritten gate, and recompute §11.2's share from actual generated counts.

**F-13 — sufficiency measurement point.** Store the post-fusion, pre-rerank
ordered list in `eval_results.retrieved` and compute sufficiency / recall / MRR /
nDCG on it; measure reranker quality separately as `sufficiency@8_post_rerank`.

**F-07 — threshold drift.** `thresholds.yaml` is authoritative. Replace §11.2's
"Target" column with `gated` / `reported` labels so the PRD stops carrying copies.

**F-08 — faithfulness across configs.** Plot retrieval metrics from Config 1 and
generation metrics from Config 5, labelled on the chart.

**F-09 — abstention in denominators.** Compute `faithfulness_pre` over answered
items only, and never publish it without `answer_rate` beside it.

**F-14 — judge family.** Decide before computing kappa: add a second provider key
to CI, or accept same-family judging and state it in the README next to the
figure.

**F-15 — curated concepts.** Derive `eval/concepts.yaml` empirically via
`scripts/concept_coverage.py` once companyfacts is loaded, with per-sector
supplements for the banks.

**F-20 — natural_phrasing_gap.** Define the formula in Appendix B — which metric,
against which comparison population — before it can be gated.

**F-10 — `supported()`.** Add `citation_valid` to the figure branch.

**F-12 — baseline comparability.** Add `eval/baselines/main_fast.json` produced by
the same 60-item subset on the same fixture; co-design the fast subset with the CI
fixture.

**F-16 — ablation budget.** Run re-embedding ablations on a reduced slice and
label them as such, or schedule them overnight. Fix the estimate now.

**F-21 — PARTIAL.** Decide where it lands in the 2×2 and what the API returns.

**F-17, F-18, F-19, F-26 — stale or drifted PRD text.** Edit the PRD, or accept
the more specific statement in each case and note it here.

**F-23 — "threshold" definition.** Interpretation in use since step 6
(2026-10-01): parser validation bounds are pipeline parameters and live in
`api/config.yaml` under `parser:` (min sections, min data tables, alpha-ratio
range), following Appendix A; `eval/thresholds.yaml` keeps gate thresholds only.
Still a code constant: the 500-character caption window from PRD 6.2
(`CAPTION_WINDOW`), a candidate for the same block. CLAUDE.md rule 4 not yet
reworded. Original recommendation: `thresholds.yaml` owns eval-gate thresholds;
Appendix A's config owns runtime pipeline parameters, snapshotted into
`eval_runs.config_json`. Needs stating explicitly in CLAUDE.md rule 4.

**F-24 — injection fixture.** Keep the injected chunk in a test-only namespace
that can never be retrieved during a metric run.

**F-33 — word-form numbers.** Leave as `value=None` with the span still recorded.
None are curated concepts. Revisit only if the count grows.

**F-36 — `.gitignore`.** Rewrite the file as clean UTF-8.
