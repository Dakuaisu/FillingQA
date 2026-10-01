# OPEN — findings register

Every finding raised against the PRD or discovered while building, with the phase
it blocks and its current status. Resolved entries stay here with their date so
this file is the complete record rather than a to-do list.

`docs/TRADEOFFS.md` carries the reasoning behind each resolution. This file
carries the state.

**Last updated: 2026-10-01**

| Status | Count |
|---|---|
| OPEN | 49 |
| RESOLVED | 41 |
| **Total** | **90** |

---

## Blocking now

| ID | Finding | Blocks | Status |
|---|---|---|---|
| F-77 | PRD 11.2 defines neither `rel_i` nor IDCG over alternative evidence sets. With union-as-relevant, an item with 8 single-chunk alternatives scores nDCG@10 of about 0.25 (1 / 3.95) for one gold chunk at rank 1 and nothing else; sufficiency gets easier as alternatives grow. Sets per item: xbrl_numeric 1 to 10 (`{1: 54, 2: 45, 3: 23, 4: 11, 5: 9, 6: 13, 7: 2, 8: 1, 10: 2}`), each one chunk; comparison 1 to 27 two-chunk sets (`{1: 6, 2: 17, 3: 1, 4: 3, 6: 1, 8: 7, 12: 1, 18: 1, 21: 2, 27: 1}`) over 2 to 12 distinct gold chunks (`{2: 6, 3: 17, 4: 4, 5: 1, 6: 7, 7: 1, 9: 1, 10: 2, 12: 1}`), printed by `scripts.xbrl_candidates` / `scripts.comparison_candidates`. Settle the definition when metrics are built, before any run; gold is not shaped around it | Phase 3 metrics | OPEN |
| F-81 | PRD 11.2's numeric accuracy ("exact match after unit normalization") does not say how "a benefit of $28 million", "(28)", "net cash used of $691 million", "none" or "—" compare with the reference answers "-$28 million" and "$0 million". Six candidates are negative or zero. Settle before any run, never by rewording gold Also, for comparison items: which of the three figures (two values, difference) numeric accuracy requires, and how an answer giving only the two values, or a correct percent change, is scored. Also the printed sign (F-87): 296 exact-value gold spans of positive facts print in parentheses, so an answer reading the chunk's "(2,815)" as -2,815 disagrees with the reference "$2,815 million". Also seeded numeric answers: percentages, per-share figures and counts, and a figure from a table whose `unit_scale` is NULL (flagged, never guessed) | Phase 3 metrics | OPEN |

## Blocking Phase 2

| ID | Finding | Status |
|---|---|---|

## Owner review (quarantined at the freeze)

| ID | Finding | Status |
|---|---|---|
| F-66 | False pass: JPM's three 10-Ks are `parsed` but mis-sectioned. Items 7 and 8 are cross-reference stubs (395 and 368 chars); the embedded Annual Report -- MD&A and financial statements, 1,008,217 of 1,208,667 chars in FY2024 -- lands under Item 15; no Part heading before Item 15 is recognised, so Items 1-14 are all Part I. The validation suite asserts that required Items exist, not that they hold content, so nothing caught it. Since the content check: all three quarantine (Item 7 395 < 15352, Item 7A 269 < 2746). Their chunks carry Item 15 / Part I labels for MD&A and statement text After F-65: Parts now right (II.5..IV.16 via the index's Part links; shape check passes). Items 7 and 8 stay stubs: the index links them to the stubs, and the stubs give the Annual Report pages with no link -- the stop condition (no page mechanism, F-55). All three stay quarantined Quarantined at the freeze (F-42 record). OWNER REVIEW | OPEN |
| F-70 | XOM's 10-K Items 7, 7A and 8 point to an appended "Financial Section"; its MD&A, "Market Risks", auditor's report and statements land under Item 16 (IV.16, "Form 10-K Summary", 302,621-324,704 chars, ~73-75% of each 10-K). Relocating them needs a section-title mechanism the PRD does not specify; the three 10-Ks are quarantined at the freeze (Item 7 is a 264-265-char stub). OWNER REVIEW | OPEN |

## Blocking Phase 3

| ID | Finding | Status |
|---|---|---|
| F-59 | OWNER-BLOCKED: Phase 2 exit needs ANTHROPIC_API_KEY in .env; retrieval verified, generation call unexercised. `.env` has no `*_API_KEY` line; the key present in the shell environment was rejected by the API (`401 invalid x-api-key`) on the one exit call made, and was not retried. Extended 2026-10-01: also blocks PRD 11.1 Stage 1 (LLM seeding of the 50 `table` and 40 `synthesis` items) and Stage 2's no-context filter ("is the question answerable without the chunk"), both model calls. `.env` still has no key; neither is stubbed | OPEN |
| F-88 | The 90 `llm_seeded` items (PRD 11.1: 50 `table`, 40 `synthesis`) are not built. Decided 2026-10-01 (TRADEOFFS, LLM seeding): 6 per ticker + AAPL, XOM 7 for tables, 5 per ticker for synthesis; the 441 gold chunks excluded; proportional allocation within ticker by (form, item_code), 2x overdraw, one draw; key-free filters built and tested (`eval/generate/seeding.py`). Allocation at 1x/2x printed by `python -m scripts.seed_supply`; every ticker has MD&A slots. Open: the minimum prose length (proposed 40 body tokens), the draw, the runner. Generation is blocked by F-59 | OPEN |
| F-89 | PRD 7.1's `synthesis` intent (summaries, top-10 lists, answers drawn from several chunks) has no eval item behind it: PRD 11.1 Stage 1 seeds `synthesis` items from one chunk each (TRADEOFFS, LLM seeding). No report may call the `synthesis` slice multi-chunk | OPEN |
| F-90 | `attach_scale` takes the scale from `chunks.unit_scale`, but a caption's exception ("in millions, except per share data") survives in neither `unit_scale` nor the chunk header: 0 of 9,221 scaled table chunks have "except" in the header line, while 153 print "except ... per share" in their text (e.g. JPM Note 18, Earnings per share, `unit_scale = millions`). A seeded per-share answer from such a table would be scaled by 10^6 without a flag. Found before any draw; not fixed | OPEN |
| F-11 | `xbrl_auto` is 49% of the eval set, not the 39% §11.2 argues from; `natural_phrasing` has no home in the `source` enum | Decided 2026-10-01 (TRADEOFFS): three `source` values; natural_phrasing is a `question_type` with `source = handwritten`, inside the handwritten gate, also reported as its own row feeding `natural_phrasing_gap`; the share is printed from the frozen dataset. Carve-out from the gate rejected. Stays OPEN until the share is printed from a real dataset | OPEN |
| F-73 | Facts whose period key cannot be an auto item need PRD 6.5.3 review: 445 facts in `eval/review_queue.csv` with a reason -- gt3 226, mixed_key 63, value_differs 156 (the 61 F-75 keys) (`python -m scripts.xbrl_pool`). OWNER-BLOCKED | OPEN |
| F-74 | Line items with facts for a filer but no eligible key, so the sampler cannot draw them (`python -m scripts.xbrl_pool`): JPM and NVDA net income (all gt3); BAC net income and noninterest income, PFE revenue (gt3 + value_differs); COST net income (gt3 + mixed_key + comparative_only). None is emptied by rule (c) alone | OPEN |
| F-76 | PRD 8's `eval_items.question_type` comment lists `lookup\|comparison\|synthesis\|table\|unanswerable\|adversarial`; PRD 11.1's Type column has `xbrl_numeric` and `natural_phrasing` and no `lookup`. `eval/generate/schema.py` follows 11.1; no migration yet. Also: `difficulty` has no assignment rule in the PRD and no metric reads it; xbrl_numeric items take `easy` from PRD 11.1's example; comparison items take `medium`, by the same absence of a rule | OPEN |
| F-78 | `xbrl_fact_id` is a DB serial (`xbrl_facts.fact_id`), filled with `ON CONFLICT DO NOTHING`; the stored ids have gaps (43,122 rows over 1..58,979), so a rebuild from the freeze would not reproduce them. Not verified by a rebuild | Guarded, ids still not reproducible: the candidates manifest records each item's fact by natural key, and `python -m scripts.xbrl_candidates --verify` exits non-zero if an id no longer names it (TRADEOFFS) | OPEN |
| F-79 | PRD 11.1's 10% spot-check of XBRL items: `eval/candidates/xbrl_numeric_spot_check.md`, 16 of 160 candidates (seed 20261001), with each gold chunk's text; plus a "flagged, outside the seeded 10%" section selected by rule (`value <= 0`): xbrl_0070, 0113, 0115 (also seeded), 0116, 0117, 0119. Ids in the manifest. Nothing marked reviewed. OWNER-BLOCKED | OPEN |
| F-80 | NVDA income tax, six months ended 2026-07-26 (0001045810-26-000075): the exact-value spans print "23,400" (scale 6) and "23.4" (scale 9), so `format_value` reports the key instead of picking a scale. The only such key among the 1,713 eligible; not drawn | OPEN |
| F-83 | PRD 11.1 Stage 3's "gold set = both chunk_ids" fails on real data: every consecutive-year duration pair (735) has one chunk holding both exact values, because a later filing prints the prior-year column (`python -m scripts.comparison_supply`). Auto comparison items draw only on pairs with no shared gold chunk (TRADEOFFS) | OPEN |
| F-84 | The 20 hand-written comparison items (PRD 11.1) are now the only plain year-over-year comparisons, the auto pool having excluded them (F-83). Authoring is the owner's; evidence sets are minimal sufficient sets (TRADEOFFS). OWNER-BLOCKED | OPEN |
| F-86 | PRD 11.1's 10% spot-check of the 40 comparison candidates: `eval/candidates/comparison_spot_check.md`, 4 seeded (cmp_0003, cmp_0015, cmp_0036, cmp_0040) with each gold chunk's text, plus a flagged section by rule (side <= 0, sign flip, untagged co-occurrence): none drawn. Nothing marked reviewed. OWNER-BLOCKED | OPEN |
| F-60 | Appendix A's `generation.temperature: 0.0` cannot be applied: `Messages.create` at the pinned `anthropic==1.11.0` takes no sampling parameters. Generation is therefore not pinned to greedy decoding, which matters for PRD 11.4 run-to-run comparability and for the LLM judge's kappa in Phase 3. Resolution path: generation runs without a temperature (nothing else to send; no SDK downgrade, no seed exists). Phase 3's runner records `response.model` per item and repeats the fast subset at least 3 times on identical config, reporting the spread of every gated metric beside its value; kappa on one fixed run against the owner's hand labels. The spread is reported noise, never a reason to widen a threshold; a threshold inside it is an F-07 input. TRADEOFFS, Phase 2 baseline | OPEN |
| F-48 | 101 of 3,881 linked facts (2.6%) are tagged only in `ix:hidden` (shares authorized, par value, segment counts), so they have no span and no gold chunk; PRD 6.5.3 routes them to human labeling Measured on the frozen 90: 476 linked facts with no visible non-dimensional span, across 33 concepts (preferred/common share counts, segment counts, zero write-offs ...), none among the 28 listed tags (`python -m scripts.concept_coverage`: human-label queue 0). Queue: `eval/human_label_queue.csv`. Labeling OWNER-BLOCKED | OPEN |
| F-13 | `sufficiency@10` has no defined measurement point — post-rerank vs post-fusion | OPEN |
| F-07 | All seven gated thresholds have drifted between §11.2 prose and `thresholds.yaml` | OPEN |
| F-08 | `faithfulness_pre` is undefined for Configs 1–4, yet §11.6 plots it there | OPEN |
| F-09 | Abstained items in generation-metric denominators — a third circularity | OPEN |
| F-14 | Judge must be a different model family, but CI carries one provider key | OPEN |
| F-20 | `natural_phrasing_gap` is gated in `thresholds.yaml` but never defined as a metric | OPEN |

## Blocking Phase 4

| ID | Finding | Status |
|---|---|---|
| F-87 | Gold spans print the sign differently from the fact (`python -m scripts.sign_display`): of the eligible keys' exact-value gold spans, 296 positive facts print in parentheses (share repurchases 127, capex 99, credit-loss allowance 31, R&D 26 in reconciliation tables, cost of revenue 13) and 3 negative facts print plain ("tax benefit of $28 million"). PRD 7.5 normalizes "(7,286)" as negative, so a sign-sensitive grounding check would strip a correct claim. Candidates with such a gold span: 25 xbrl_numeric, 5 comparison. Measured only; gold and reference answers unchanged | OPEN |
| F-85 | A comparison item's difference is printed in no chunk, so PRD 7.5's numeric grounding ("every number in the claim appears in a cited chunk") would strip a correct difference claim | OPEN |
| F-82 | Numeric grounding of a zero claim: the correct figure is $0, but the cited chunk prints "—" (PFE share repurchases, xbrl_0116/0117: `raw_text='—'`, value 0, scale 6), so matching the claim's number against the chunk text finds no "0" | OPEN |
| F-10 | `supported()` omits `citation_valid` for figure claims, contradicting §7.5's own table | OPEN |
| F-12 | `eval.compare` compares a fast/CI-corpus run against a full-corpus baseline | OPEN |
| F-16 | Chunk-size and context-header ablations need a full re-embed; budget is ~10× short | OPEN |
| F-61 | PRD 14 calls the Phase 2 baseline "Config 1", but PRD 11.6's Config 1 is fixed 512-char chunks and Config 2 is the structure-aware chunking built in Phase 2 step 1. The baseline runs on the only chunk set that exists. Either the 11.6 chart needs a separate fixed-512-char chunk set and its embeddings, or Configs 1 and 2 collapse | OPEN |
| F-21 | `PARTIAL` verdict has no place in the abstention 2×2 or the API examples | OPEN |
| F-68 | NVDA's 10-K Item 8 is a cross-reference stub (206 chars: the statements are "set forth in Item 15"), a legal SEC layout faithfully parsed: NVDA's financial-statement chunks carry "Item 15" headers. It sets the measured Item 8 floor at 206, so the content check cannot catch Item 8 stubs; JPM is caught on Items 7 and 7A instead. Item-based filtering (PRD 7.1) for "Item 8" would miss NVDA's statements Bites PRD 7.1's Item filter: "Item 8" misses statements filed under Item 15 (NVDA), and validation now lists each filing's stub Items | OPEN |
| F-57 | PRD 11.7's chunk-size ablation lists 256 / 512 / 800 / 1200 tokens; 800 and 1200 exceed bge-base-en-v1.5's 512-token input (F-53), so those points would embed truncated chunks | OPEN |

## Blocking Phase 5

| ID | Finding | Status |
|---|---|---|
| F-47 | No restatement count can be published yet: companyfacts drops iXBRL `decimals`, so a figure printed exactly in one place and rounded in another (AAPL LongTermDebt 90,678M vs 90,700M) diverges like a real restatement (TGT 2016 equity 12,957M -> 12,965M). Phase 1's exit only needs the query to return rows, which it does. No restatement number appears anywhere until this is resolved | OPEN |
| F-55 | `page_hint` is not computed; `chunks.page_hint` is NULL. PRD 6.2 step 5, the 9 API response and the 10 source panel all carry it; PRD 10's source panel consumes it | OPEN |

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
| F-49 | companyfacts `fp` carries `Q4` (601 facts) and null (618), contradicting PRD 6.5.2's `'FY' \| 'Q1' \| 'Q2' \| 'Q3'`; all in `xbrl_facts_unlinked` -- 0 linked facts have either | OPEN |
| F-71 | BAC's 10-K Item 7 and 8 heading tables carry a "Table of Contents" cell that is not an in-document link, so it stays in the section title and every BAC 10-K Item 7/8 chunk's context header ends "... Table of Contents". Found on the frozen corpus's retrieval check; cosmetic, embedded Measured scope over the 90's stored chunks: BAC 10-K Items 7 and 8 only -- 0000070858-24-000122 II.7 245 / II.8 370, -25-000139 II.7 242 / II.8 358, -26-000157 II.7 242 / II.8 365; 1,822 chunks in 3 filings. Item 7's title also keeps the "Bank of America Corporation and Subsidiaries" prefix. Left as a known residual of the freeze, named in its notes; the cheap fix window closes when the first gold evidence set is written (TRADEOFFS) Window closed 2026-10-01 when the first gold was written: 15 of the 326 distinct gold chunks in the 160 candidates carry the header, in 9 candidates, 5 of which have no other evidence set | OPEN |
| F-58 | The F-54 navigation rule drops one content block: TGT 10-K Item 15's list item "•Notes to Consolidated Financial Statements" (block 826), whose only text is a link sharing its target with seven "See accompanying Notes..." sentences, and which has no full stop. No span overlaps it. Measured, not tuned | OPEN |
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
| F-46 | Some `layout` tables carry prose (audit matters, cybersecurity oversight, executive officers), not scaffolding | Every layout table that is not page furniture chunks as prose; no length rule (cell lengths of TOCs, exhibit indexes and prose tables overlap). Verified: AAPL's uncertain-tax-positions audit matter is in a stored prose chunk (test). Furniture residual tracked as F-54 | 2026-10-01 |
| F-56 | TGT's 10-K exhibit index produced two unsplittable units of 648 and 992 tokens, over `max_seq_length`: the sentence splitter never broke before a digit ("...reference). 4.2 Description...") | Digits added to the sentence-start lookahead. 12 filings before/after: >512 2 -> 0 (TGT 10-K max 992 -> 500); content_hash changes only in TGT's 10-K (214 -> 217 chunks: 4 changed, 1 removed, 4 added), 0 in the other 11; resolve table unchanged, 7,862 of 7,877 | 2026-10-01 |
| F-54 | TGT's per-section running headers survived furniture filtering and left nav fragments in prose; blocked the Phase 2 exit (the freeze pins `parser_version`) | `Block.anchors` (in-document links, normalized-text coordinates; text unchanged on all 12, `parser_version` f1090fb5f594 -> 0e417d5495e4) plus a navigation rule keyed on repeated anchor-target sets with the furniture guard. `navres` 13/29/17/12 -> 0 on TGT; navigation blocks dropped 11/26/15/10; AAPL and COST 0 chunk changes; resolve 7,862/7,877 unchanged; 0 dropped blocks overlap an xbrl_span. 1 false positive (F-58). AUTONOMOUS DECISION, TRADEOFFS 2026-10-01 | 2026-10-01 |
| F-62 | XOM's ticker now resolves to the successor ExxonMobil Holdings Corp (CIK 0002115436, 1 window filing); the 3-year history is under the predecessor Exxon Mobil Corp (CIK 0000034088) | Option (a): XOM's company row is cik 0000034088, all 12 filings from it; `companyfacts_ciks` adds the successor as a facts source, stamped with the pinned CIK and linked by accession. All 8 CIKs pinned in config (deviation from PRD 6.1's ticker lookup). Verified: XOM 12 linked accessions; 0000034088-26-000093 FY2026 Q2, 269 facts in `xbrl_facts`, 0 unlinked. AUTONOMOUS DECISION, TRADEOFFS 2026-10-01 | 2026-10-01 |
| F-63 | Item and Part headings rendered as layout tables were invisible to section detection (27 quarantined filings) | A short table (<= `MAX_HEADING_CHARS`) is a heading when its first non-empty row is its only heading-like row; its text is read without in-document link text. An index listing several Items stays excluded. 96 filings: 69 section lists identical, every one of the 48 clean filings among them; PFE 10-Ks 0 -> 20 sections, XOM 10-Ks 0 -> 22, BAC 10-Ks gain Items 7 and 8, PFE 10-Qs Part-qualified, XOM 10-Qs gain I.1. Parsed 48 -> 66; clean-filing chunk changes 0; resolve 0.999 (1.000 within Items). `parser_version` 0e417d5495e4 -> c04582d899a9 | 2026-10-01 |
| F-64 | BAC 10-Qs print MD&A before Item 1; the index's "Part II" heading tagged it Part II, so `I.2` was missing (9 quarantined) | Part tracking reads no Item order: a Part heading followed directly by a table listing several Items heads an index entry and does not set the Part; an Item before any effective Part heading is Part I (both forms open with it). 96 filings: 78 section lists identical, all 48 clean among them; BAC 10-Qs I.2/I.3/I.4, JPM 10-Qs I.3/I.4. Parsed 66 -> 75; no previously chunked filing's chunks changed; resolve 0.999 (1.000 within Items). `parser_version` c04582d899a9 -> 2b3d5591e4c0 | 2026-10-01 |
| F-65 | JPM 10-Qs carry no Part I Item 1/2 headings; their index links stand in for them (9 quarantined) | PRD 6.2 step 2's table-of-contents-anchor fallback: link targets recorded by the walker (`text_sha256` identical on all 96); linked index rows fill only Items primary detection missed; index Part links join the Part markers, earliest position wins. 96 filings: 84 section lists identical, all 48 clean among them; all 9 JPM 10-Qs gain I.1 and I.2. Parsed 75 -> 84; no previously chunked filing changed; resolve 0.999 (1.000 within Items). 10-K code shape: no company detects a code AAPL's set lacks. `parser_version` 2b3d5591e4c0 -> d58d26e08e5a | 2026-10-01 |
| F-67 | Chunks over `max_seq_length`, so the embedder refused the run (4 at first; 28 after F-63..F-65: 16 layout tables chunked as prose, 12 single over-budget sentences) | Layout tables over budget split at row boundaries with the first row repeated; over-budget sentences split at "; " clauses, whitespace windows only as a last resort (0 used). 84 parsed filings: >512 28 -> 0, max 500, part overlaps 0; chunk changes in 33 filings, all 244 traced to a split unit or its prose run; embed check passed on 18,788 chunks, 0 without an embedding; resolve unchanged 177,144 of 177,240. `chunker_version` -> 964f77f6f9cb. AUTONOMOUS DECISION, TRADEOFFS 2026-10-01 | 2026-10-01 |
| F-69 | Content floors measured on four filers quarantined faithful parses: BAC's and PFE's Item 7A point into Item 7 (217 / 289 chars) | The check is redefined by what it is for: `parser.stub_max_chars: 1000`; 10-K Items 1, 1A, 7 and 10-Q I.1, I.2 must not be stubs; 7A and 8 may be, and are listed per filing. Set after measuring all 96: no must-not-be-stub Item between 500 and 5,000 chars. Result: 90 parsed, BAC x3 and PFE x3 admitted, JPM x3 and XOM x3 quarantined on Item 7 alone; the 84 previously chunked filings unchanged. AUTONOMOUS DECISION, TRADEOFFS 2026-10-01 | 2026-10-01 |
| F-42 | The eval corpus was a window relative to the run date; a raw-byte hash is not a filing's identity | Accession list committed as of 2026-10-01 (96 filings, pinned CIKs, F-62); frozen in `api/corpus_freeze.yaml`: 90 parsed with `(accession, text_sha256, parser_version)`, 6 quarantined with reason and finding (F-66, F-70), per-ticker 10-K/10-Q counts, F-58 referenced. `python -m scripts.verify_freeze`: 96 verified, 0 mismatches; exits 1 on any difference (tested by altering one hash) | 2026-10-01 |
| F-15 | `CURATED_CONCEPTS` named in PRD 6.5.3 yields near-zero items for JPM and BAC | `eval/concepts.yaml`: 26 line items, 28 tags -- all 19 named concepts, 7 bank supplements chosen by PRD 6.5.3's analyst-relevance criterion, and two variants used only by filers with no fact under the named tag. On the frozen 90 (`python -m scripts.concept_coverage`): 4,335 facts, 4,051 in the 1-3 bucket, 284 in >3, 0 in 0; every ticker supplied, JPM and XOM by 10-Qs only. AUTONOMOUS DECISION, TRADEOFFS 2026-10-01 | 2026-10-01 |
| F-32 | 30–56% of numeric iXBRL facts sit on dimensional (segmented) contexts, segment/product breakdowns, not company-level figures | Gold excludes dimensional spans in `eval/generate/gold.select_gold`, which the candidate generator goes through; tested on a real AAPL net-income span at the same value on an equity-statement context (`tests/unit/test_gold.py`). 479 facts have such a same-value dimensional span in a chunk | 2026-10-01 |
| F-72 | PRD 6.5.3 keys gold chunks on `(accession, concept, context)`, so a rounded mention of a fact (PFE "$201 billion" for total assets 201,131 million) counted as gold | Gold is exact-value spans only, in `select_gold`, which the candidate generator goes through; tested on the real PFE spans (`tests/unit/test_gold.py`) | 2026-10-01 |
| F-75 | Of 2,553 (cik, concept, period) keys, 1,234 appear in more than one parsed accession and 61 differ in value | One item per key, eligibility (a)-(c), gold over every accession, label from the own-period filing's dei labels: enforced by `build_pool` / `build_items` under test (`test_pool.py`, `test_xbrl_items.py`). The 61 stay in review (F-73) | 2026-10-01 |

---

## Recommendations for the open items

Kept separate from the tables so the tables stay scannable.

**F-32 — dimensional contexts.** Record `is_dimensional` on every context (done)
and require Phase 3's auto-generation to filter on it (done: `select_gold`, tested). A segment revenue line is
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

**F-11 — source taxonomy.** Settled 2026-10-01 (TRADEOFFS): three `source`
values; `natural_phrasing` is a `question_type` with `source = handwritten`,
inside the handwritten gate and also reported as its own row; carving it out of
the gate was rejected. Remaining: print §11.2's share from the frozen dataset.

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

**F-15 — curated concepts.** Done 2026-10-01: `eval/concepts.yaml`, measured by
`scripts/concept_coverage.py`, with bank supplements.

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
Since Phase 2 step 2 the same pattern holds `span_resolution.min_rate` (PRD 14's
80% resolve floor).
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
