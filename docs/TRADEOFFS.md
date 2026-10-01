# TRADEOFFS

Running log of decisions, deferred defects, and their reasoning. Appendix C of the
PRD asks for one paragraph per week; deferred PRD findings are logged here too,
with the phase where they have to be resolved.

---

## 2026-08-30 — PRD review, deferred findings

Ten defects found in a full read of `docs/PRD.md`. All accepted as real; none
fixed yet, by decision. Each is resolved at the start of the phase where it
bites. Two are marked **BLOCKING Phase 3** — Phase 3 cannot start until they are
settled, because they change what the metrics mean.

### #7 — Every gated threshold has drifted between PRD §11.2 and `eval/thresholds.yaml`

**Bites: Phase 3.**

§2.1 says thresholds live in `thresholds.yaml` "and nowhere else". §11.2's tables
restate all seven, and all seven differ: sufficiency@10 0.85/0.82,
faithfulness_pre 0.75/0.72, claim_retention 0.80/0.78, citation_coverage
0.95/0.93, xbrl_contradiction 0.02/0.03, false_answer_rate 0.05/0.07,
over_abstention_rate 0.10/0.15. This is §0a defect 8 recurring inside the very
section that warns about it.

**Recommendation:** `thresholds.yaml` is authoritative (CLAUDE.md rule 4).
Replace §11.2's "Target" column with `gated` / `reported` labels so the PRD stops
carrying copies at all.

### #8 — `faithfulness_pre` is undefined for Configs 1-4

**Bites: Phase 3.**

§11.6 plots `faithfulness_pre` across Configs 1 to 8 and puts that chart above
the fold in the README. Citation-constrained structured generation is not added
until Config 5; Configs 1-4 emit prose with no claims and no citations, so
`supported(claims_pre) / |claims_pre|` has nothing to divide. Phase 3's exit
criterion ("four source columns for Config 1") is unachievable for every
generation metric.

**Recommendation:** plot retrieval metrics from Config 1 and generation metrics
from Config 5, labelled as such on the chart. The alternative — a
claim-decomposition post-processor for unstructured baselines — introduces
another unvalidated instrument that would itself need an agreement check.

### #9 — Abstained items in the generation-metric denominators

**Bites: Phase 3.**

`faithfulness_post = supported(claims_post) / |claims_post|` divides by zero on
any ABSTAIN, since §7.5's `verdict()` returns ABSTAIN when `claims` is empty.
Same for `claim_retention` when the generator emits no claims. The real problem
is not the division: if abstained items are excluded from the denominator, a
system that abstains on everything hard scores near-perfect faithfulness. That is
§16's own test — "could a component in my pipeline force this value?" — answered
yes, for the third time in this document's history.

**Recommendation:** compute `faithfulness_pre` over answered items only, but never
publish it without `answer_rate` beside it — the same pairing discipline as
`verifier_lift` / `claim_retention`.

### #10 — `supported()` omits `citation_valid` for figure claims

**Bites: Phase 4.**

§7.5's figure-claims table lists citation validity as the first check with "strip
claim" as the failure action. The `supported()` function six lines below omits it
from the figure branch and keeps it only in the prose branch. It has teeth:
`numbers_grounded` ("every number appears in a cited chunk") is undefined when the
cited chunk_id is a hallucination, and `supported()` is the faithfulness
predicate.

**Recommendation:** add `citation_valid` to the figure branch.

### #11 — `xbrl_auto` is 49% of the eval set, not 39% — BLOCKING Phase 3

§11.2 argues the per-source breakout from "160 of your 410 items (39%)". But
§11.1's comparison row reads "60 | XBRL pairs across fiscal years (auto) + 20
hand-written", adding 40 more auto items. With only three legal `source` values
those must be `xbrl_auto`: 200/410 = 49%. The entire §11.2 argument is calibrated
on the wrong denominator, and the easy slice is half the set.

Related and equally blocking: the 30 natural-phrasing controls are presumably
`source = 'handwritten'`, which puts them inside the separately-gated handwritten
slice (`sufficiency_at_10: 0.72`) — a slice they are designed to score low on —
while §11.1 also requires reporting them separately. The `source` enum cannot
express both roles.

**Settled 2026-10-01 (AUTONOMOUS DECISION, F-11 entry below):** controls stay inside the
handwritten gate and also get their own row; carve-out recorded as the rejected alternative.

**Recommendation:** settle the source taxonomy before generating a single item.
Carve `natural_phrasing` out via `tags` and decide explicitly whether it sits
inside or outside the handwritten gate. Recompute the §11.2 share from the actual
generated counts rather than the planned ones.

### #12 — `eval.compare` compares two runs that are not comparable

**Bites: Phase 4.**

§11.5's CI runs `make eval-fast` (60 items) against §13.1's `ci` corpus ("frozen
fixture snapshot, ~2k chunks"), then compares against `eval/baselines/main.json`,
which §13.3 says is written by the nightly `full_eval` on the full corpus.
Retrieval on a 2k-chunk fixture is strictly easier than on the full corpus, so the
PR delta measures corpus size as much as code change. The `regression_tolerance`
block would fire on noise or mask real regressions depending on direction.

**Recommendation:** a second baseline (`eval/baselines/main_fast.json`) produced by
the same 60-item subset on the same fixture, refreshed by the same job. The fast
subset and the CI fixture must be co-designed so every gold chunk_id the subset
references exists in the fixture.

### #13 — `sufficiency@10` has no defined measurement point — BLOCKING Phase 3

§7.3 sets rerank output to top-8 (top-5 for `lookup`, top-10 for `synthesis`),
plus a score floor that can shorten the list further. The gated metric is
`sufficiency_at_10`. If it is computed post-rerank, `lookup` items are capped at 5
chunks and @10 is unreachable — and the 160+ `xbrl_auto` items are all lookups, so
the most-gated retrieval metric would mean something different per intent. §7.1
compounds it: `comparison` runs "k=50 x2 sub-queries", leaving `retrieved`
ambiguous between one branch and the union of both.

**Recommendation:** `eval_results.retrieved` stores the post-fusion, pre-rerank
ordered list, uncapped. Sufficiency / recall / MRR / nDCG are computed on that.
Reranker quality is measured separately as `sufficiency@8_post_rerank`. This keeps
the retrieval gate independent of the rerank budget — otherwise §11.7's reranker
ablation moves the metric by changing what it is measured on.

### #14 — The judge must be a different model family, but CI carries one provider key

**Bites: Phase 3.**

§11.3 requires a "different model family than the generator … same-model judging
is self-grading". §11.5's workflow passes exactly one secret,
`ANTHROPIC_API_KEY`. The same concern applies to §11.1 Stage 1's seeding model:
items seeded by the model that also generates answers are biased toward what that
model finds expressible.

**Recommendation:** decide before computing Cohen's kappa, not after. Either add a
second provider key to CI, or accept same-family judging and state it plainly in
the README next to the kappa figure.

### #15 — `CURATED_CONCEPTS` will not cover the banks

**Bites: Phase 3; mitigation lands in Phase 1.**

The §6.5.3 list leads with `Revenues, CostOfRevenue, GrossProfit, InventoryNet`.
JPM and BAC report none of `InventoryNet`, `GrossProfit`, or `CostOfRevenue`, and
`Revenues` itself is largely superseded by
`RevenueFromContractWithCustomerExcludingAssessedTax` for most modern filers. A
single a-priori list yields near-zero `xbrl_auto` items for 2 of the 8 companies
and skews the auto slice toward tech and retail — a sector skew the per-`source`
breakout does not catch.

**Recommendation:** derive `eval/concepts.yaml` empirically.
`scripts/concept_coverage.py` (Phase 1) counts concept coverage per company once
`companyfacts` is loaded; pick the ~25 with the best cross-company support and add
per-sector supplements for the banks.

### #16 — The re-embedding ablations are underbudgeted by roughly an order of magnitude

**Bites: Phase 4.**

§14 budgets "1-1.5h each including eval runs" for ablations. The chunk-size
(256/512/800/1200) and context-header ablations both change the embedded text and
require a full re-chunk and re-embed per variant; §13.2 puts initial indexing at
1-3 hours on CPU. Chunk size alone is 4 variants x 1-3h before any eval run. This
is the same class of error §14 was rewritten twice to remove.

**Recommendation:** run the re-embedding ablations on a reduced corpus slice and
label them as such in the README, or schedule them as overnight jobs. Fix the
estimate now so Phase 4 does not repeat v2.0's week 3.

---

## 2026-08-30 — Phase 1 decisions taken

Recorded here because they are deviations from PRD §13.4 / §8, approved before
build.

1. **Number normalization lives at `api/numbers.py`, not `api/verify/numbers.py`.**
   Phase 1 needs unit-scale conversion for §6.5.2 Trap 2 — `parse/tables.py`
   detects the "(in thousands)" caption and `ingest/xbrl_facts.py` normalizes to
   base units. Putting it at the package root avoids creating a `verify/` package
   four phases early, and avoids moving the file later.

2. **`xbrl_spans.chunk_id` is not created in Phase 1.** §6.5.2 declares it
   `REFERENCES chunks(chunk_id)` and `chunks` does not exist until Phase 2. Phase
   2 adds the column and the foreign key in its own migration.

3. **`filings` gains `parse_error TEXT` and `norm_path TEXT`.** §8 has
   `parse_status` and `parse_score` but no way to record *why* a document was
   quarantined, and no home for normalized document text.

4. **iXBRL extraction and HTML flattening are one traversal, not two passes.**
   §6.2 says to harvest `<ix:*>` spans "before you flatten", keyed by character
   offset — but §6.2's `Block.char_start` is an offset into *normalized* text.
   Those are different coordinate systems, and §6.5.3's span-to-chunk resolution
   plus Phase 2's ">=80% resolve" assertion both need the normalized one. A single
   traversal emits normalized text while recording each `ix` element's range in
   the text it emits, which preserves the intent (do not destroy the spans) and
   produces offsets in the coordinate system everything downstream uses. This is
   the unstated mechanism behind §16's "iXBRL offsets don't survive parsing" risk.

5. **Parser output is serialized to `data/parsed/{accession}.json`, not Postgres.**
   §8 defines no `sections` or `blocks` tables, and §15's golden-file tests
   snapshot the `Document` JSON. Postgres holds
   `filings.parse_status / parse_score / parser_version`; the structure lives on
   disk until Phase 2 turns it into chunks.

6. **`scripts/concept_coverage.py` is new** — the empirical derivation of
   `CURATED_CONCEPTS` from finding #15, which the PRD implicitly assigns to Phase
   3. Cheap to run once `companyfacts` is loaded, and it de-risks the 160-item
   target early.

7. **No `tenacity` dependency.** EDGAR retry/backoff is roughly fifteen lines for
   a single use case, and hand-rolling keeps the retry policy visible in
   `ingest/edgar.py` where it has to be defended.

---

## 2026-08-30 — Phase 1 build order and dev slice

Build order set by the owner, superseding my proposed ordering:

1. Postgres schema + migrations
2. EDGAR client with rate limiter — tested against ONE real filing before
   anything is built on top of it
3. Inline-XBRL span extractor
4. HTML normalizer, section detector, table extractor
5. companyfacts ingestion
6. Parser validation assertions

Dev slice: **COST, TGT, AAPL**, one year. Chosen to exercise the retail
confusable pair plus a clean baseline filing. Note this slice immediately
exercises the fiscal-calendar problem (Phase 1 decision on `fiscal_year`): COST
and TGT are on different retail fiscal calendars and AAPL is on a September
year-end, so no two of the three share a fiscal-year boundary.

Steps 3 and 4 remain **one traversal**, not two sequential components — the
approved single-pass design (Phase 1 decision 4). Step 3 owns the traversal and
emits normalized text plus span offsets into it; step 4's section and table
detection then runs over that normalized text.

## 2026-08-30 — Phase 2 and Phase 3 direction (parked, not started)

Recorded so it does not live only in chat scrollback. Not being built yet;
CLAUDE.md is one phase at a time.

**Phase 2.** The naive baseline is deliberately bad and must stay that way:
dense-only, top-5, unstructured generation. It is Config 1 in the §11.6
progression and its job is to be the number later configs beat. No hybrid
retrieval, no reranking. After chunking, resolve `xbrl_spans.chunk_id` by mapping
span offsets to the containing chunk and assert >=80% resolve; a much lower rate
means the offsets did not survive parsing and Phase 1 has to be fixed first.

**Phase 3.** Build order: XBRL auto-generation with evidence-set location →
paraphrase templating → LLM seeding plus the automated filters → metrics →
per-source breakout → LLM judge with Cohen's kappa → runner and reports.
Three constraints: the no-context filter is mandatory; faithfulness is computed
on `claims_pre`; and the owner authors all hand-written items personally (50
unanswerable, 20 adversarial, 30 natural-phrasing) — I build the schema and
tooling only. A review CLI for the 10-13 hour review pass is wanted.

---

## 2026-08-30 — Finding #5 resolved: fiscal_year comes from dei tags, not submissions

The original decision (Phase 1 decision on `fiscal_year`, same date) said the
label was the issuer's own and implied it would be read from the submissions
data. **That turned out to be impossible.** Recording why, because the reasoning
is the reusable part.

Verified against the live API for AAPL, COST, NVDA and TGT. `filings.recent`
carries exactly these fields:

    acceptanceDateTime, accessionNumber, act, core_type, fileNumber,
    filingDate, filmNumber, form, isInlineXBRL, isXBRL, isXBRLNumeric,
    items, primaryDocDescription, primaryDocument, reportDate, size

No fiscal-year label, and none at the top level either. The only fiscal-calendar
signal is a top-level `fiscalYearEnd` as an MMDD string:

    AAPL  0926      COST  0830      NVDA  0131      TGT  0201

which is exactly the divergence finding #5 predicted -- four companies, four
different fiscal calendars, no shared coordinate.

`fiscalYearEnd` is not enough to reconstruct the label. Deriving it from
`reportDate` fails on TGT, whose fiscal 2024 ends in February 2025: the calendar
year of `reportDate` is 2025 against a real label of 2024. Any rule that gets TGT
right by offsetting would then need to not break NVDA, whose fiscal 2024 ends in
January 2024 and where the calendar year happens to match. That is a heuristic
with company-specific exceptions, which is what finding #5 existed to prevent.

**Resolution.** Migration `0003_fiscal_labels_nullable.sql` makes
`filings.fiscal_year` and `filings.fiscal_quarter` nullable. Ingest writes
`period_end` from `reportDate` -- factual, no derivation -- and leaves the labels
NULL. Parsing fills them from `dei:DocumentFiscalYearFocus` and
`dei:DocumentFiscalPeriodFocus` in the filing's inline XBRL, which is the
issuer's own assertion of its own label.

**Consequence for Phase 2, handled now rather than later.** `chunks.fiscal_year`
is NOT NULL and feeds the metadata filter in PRD 7.1, so a filing with no
fiscal label cannot be chunked. `validate.py` (Phase 1 step 6) carries a hard
assertion: a parsed filing with no `DocumentFiscalYearFocus` is **quarantined**,
never silently defaulted. A wrong fiscal label in the index is worse than a
missing filing -- PRD 1.2 names period confusion "the single most damaging error
class", and a defaulted label produces exactly that, invisibly.

### The two fiscal_year columns have different provenance and may disagree

`filings.fiscal_year` comes from the `dei` tags in the filing document.
`xbrl_facts.fiscal_year` comes from `companyfacts`, which carries `fy`/`fp` per
fact. These are two different sources and they are not guaranteed to agree.

Note also that `companyfacts` `fy`/`fp` describe the **fiscal year and period
focus of the filing the fact was reported in**, not the period the fact itself
describes -- so a FY2023 comparative appearing in a FY2024 10-K may carry
`fy: 2024`. That is a second, separate reason the two columns can differ, and it
is a property of the API rather than an error.

**When they disagree, surface it -- do not reconcile silently.** A divergence is
either a genuine data-quality finding about the filing or a bug in our
extraction, and quietly picking one source destroys the evidence needed to tell
which. Treat it the same way PRD 6.5.2 treats restatements: detect, count,
report. Add a check alongside `scripts/key_sanity.sql` once both columns are
populated.

---

## 2026-08-30 — The dev slice is parser development only, confirmed live

Finding #6's resolution already set the eval corpus at **8 companies x 3 years,
frozen at the end of Phase 2**. Ingesting the three-company, one-year dev slice
produced the concrete evidence for why, so it is recorded here.

A one-year *filing-date* window returns exactly four filings per company -- one
10-K and three 10-Qs -- which looks like a complete fiscal year and is not:

    AAPL  10-K period_end 2025-09-27   10-Qs 2025-12-27, 2026-03-28, 2026-06-27
    COST  10-K period_end 2025-08-31   10-Qs 2025-11-23, 2026-02-15, 2026-05-10
    TGT   10-K period_end 2026-01-31   10-Qs 2025-11-01, 2026-05-02, 2026-08-01

In every case the 10-K closes one fiscal year while the 10-Qs report quarters of
the *next* one. No company in the slice has a 10-K together with its own three
10-Qs. That is a property of filing-date windows over offset fiscal calendars,
not a bug, and no window width fixes it for all eight companies at once.

**Consequence.** The dev slice cannot support PRD 11.1 comparison items, which
pair the same concept across fiscal years for one company. It also cannot support
the 160 `xbrl_auto` items: roughly 25 curated concepts across three companies for
one year is nowhere near that count. The slice exists to develop the parser
against real filings and nothing else.

The eval corpus stays 8 x 3, frozen once at the end of Phase 2 and not touched
again -- re-ingesting mid-project silently breaks metric comparability (PRD 11.4
and the corpus-drift row in PRD 16).

Live proof of the fiscal-label decision, incidentally: TGT's 10-K has
`period_end = 2026-01-31` and is the issuer's fiscal **2025**. Any derivation
from the calendar year of `period_end` gets it wrong by one.

---

## 2026-08-30 — A blessed snapshot is only a test if the baseline was verified

General rule, not a step-4 note.

`pytest --snapshot-update` writes whatever the code currently produces and calls
it correct. If the baseline is accepted without being read, the test asserts only
that behaviour has not *changed* -- it can never show that behaviour is *wrong*.
Commit a baseline generated from unverified output and you have added a test that
cannot fail, plus the false confidence of a green suite.

This is the same shape as the circular faithfulness metric in PRD 11.2, in a
different disguise. There, the verifier stripped every claim below threshold T
and faithfulness was then measured on what survived, so the metric was >= 0.90 by
construction and the gate could not fire. Here, the parser produces output and
the snapshot is taken from that same output, so the assertion is >= 100% by
construction. Both fail PRD 16's test: *could a component in my pipeline force
this value?* Yes, in both cases -- the component being graded is the one
producing the standard it is graded against.

**The rule.** Never run `--snapshot-update` and commit the result unread. Before
a baseline is committed, read it and check specific values against the source by
hand. Record in the test module's docstring that this was done, so a later reader
knows the baseline carries evidence rather than just history. When a snapshot
legitimately changes, re-verify the changed values -- do not re-bless the file.

**What was checked for the Phase 1 parser baseline**, on 2026-08-30:

- Section structure against the canonical 10-K: Items 1, 1A, 1B, 1C, 2, 3, 4 in
  Part I; 5, 6, 7, 7A, 8, 9, 9A, 9B, 9C in Part II; 10-14 in Part III; 15, 16 in
  Part IV. AAPL and TGT both yield all 23. The 10-Q yields the canonical 11.
- Section sizes for plausibility: Risk Factors is the largest prose section
  (68,042 / 56,221 chars), Financial Statements the largest overall (61,072 /
  77,778), and the stub items are stubs -- Item 1B is 40 characters, which is
  "None." plus its heading.
- Fiscal labels against the dei tags: AAPL 10-K FY2025, AAPL 10-Q Q2 FY2026,
  TGT 10-K FY2025 with period_end 2026-01-31.
- `contextref_resolved == spans_numeric` in all three, i.e. 100%.
- **Values against the printed document.** AAPL's balance sheet prints
  "Inventories 5,718 7,286"; the extractor yields two `us-gaap:InventoryNet`
  spans, 5,718 at instant 2025-09-27 and 7,286 at 2024-09-28, both scale 6, both
  stored as base units (5718000000 / 7286000000). That 7,286 is PRD 6.2's own
  worked example, here as the prior-year comparative -- and the fact that one
  filing carries both years is exactly why the fact key includes `accession`
  (F-01). Assets, AssetsCurrent, NetIncomeLoss, StockholdersEquity and
  CashAndCashEquivalents were checked the same way; durations came back as
  durations and instants as instants.

An inspection script written for this pass had a bug of its own -- a regex
extracting titles broke on the ASCII apostrophes in TGT's "Registrant's" and
"Management's", making two sections appear to vanish. Worth noting because it is
the failure mode the rule guards against, inverted: the tooling was wrong and the
code was right, and only checking against the source distinguished them.

---

## 2026-10-01 — Every corpus is an accession list, never a window relative to today

General rule, not a dev-slice note.

A window such as "filings from today minus N years" makes the corpus a function
of the date the ingest happens to run. Run it a month later and a new 10-Q
enters while an old one drops out, with no change to any file in the repo. That
breaks PRD 11.4: two eval runs are comparable only if they ran over the same
documents, and a date-relative definition cannot guarantee that even in
principle. The move to a new machine made this concrete -- the dev slice had to
be re-ingested from EDGAR, and with `years_back: 1` it would have come back as a
different set of filings than the one the parser baseline was verified against.

**The rule.** A corpus is defined by an explicit list of accession numbers
committed to the repo. Ingest selects exactly those, checks each one's form
against SEC's own value, and fails loudly if any accession is missing from the
company's submissions. It never substitutes a nearby filing: a silent swap
changes the corpus without changing its definition, which is the same failure
the window had.

A date window is still a fine way to *find* candidate accessions once. The output
of that search is what gets committed, not the search.

**Applied** to the dev slice: `corpus.dev_slice` in `api/config.yaml` is the 12
accessions, read by `python -m api.ingest.cli --dev-slice`. **Not yet applied**
to the Phase 2 eval corpus, which is still `years_back: 3` (F-42).

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: raw-hash drift, lint scope, untracking

Three decisions taken by the supervisor on the owner's behalf. Recorded with the
alternatives rejected, so each can be reversed knowingly.

### F-43 — what identifies a filing, and what the corpus freeze checks

**Decision.** Raw bytes stay exactly as fetched and `filings.content_hash` stays
sha256 of those bytes. PRD 6.1 asks for that hash as the idempotency and
provenance record. It never says the raw hash is the filing's identity. The
identity is the accession: SEC does not edit filings in place, and an amendment
gets a new accession.

The Phase 2 freeze record is `(accession, text_sha256, parser_version)` per
filing, and comparability is judged on `text_sha256`, because normalized text is
what the pipeline consumes:

- raw hash differs, `text_sha256` matches: informational log line, not a failure
- `text_sha256` differs under the same `parser_version`: filing content changed, fail

This is not circular. `text_sha256` is already in the parser snapshot, so parser
drift fails the snapshot test and forces a deliberate update; the freeze check
cannot silently absorb it. `tests/fixtures/manifest.json` stays as is: it
describes the committed bytes, and they match.

**Rejected:**
- *Hash the raw bytes with the injected script stripped.* The script path is a
  per-session bot-manager token on SEC's edge. A regex against markup we do not
  control will break again, and "raw minus our edits" is no longer raw.
- *`text_sha256` alone, without `parser_version`.* A changed hash would then be
  ambiguous between "the filing changed" and "the parser changed". Carrying the
  version separates the two.

Gap noted, not fixed: `filings.parser_version` and `filings.norm_path` exist in
migration 0001 and nothing under `api/` writes either. They are populated when
the parser's DB write lands with the validation suite (PRD 6.2), not now.

### F-44 — `ruff format --check` failing on `tools/bridge.py`

**Decision.** `[tool.ruff.format] exclude = ["tools"]` in `pyproject.toml`.
`tools/` is operator tooling, the owner's file, not project code; it also carries
uncommitted changes that are not ours. Format-only, so `ruff check` still lints it.

**Rejected:**
- *`ruff format tools/bridge.py`.* Rewrites a file someone else is editing.
- *Adding `tools` to `[tool.ruff] extend-exclude`.* Would drop `ruff check` too,
  losing real lint coverage for no reason.

### `.omo/` and `.serena/` tracked despite `.gitignore`

**Decision.** `git rm -r --cached .omo .serena`. Four files leave the index and
stay on disk.

**Rejected:** *leave them tracked.* The ignore rule does not apply to tracked
files, so `.omo/` session state would keep showing up in every diff.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: step 4c, where real tables departed from PRD 6.2 step 3

Each of these is a place the data contradicted the PRD's wording. Accepted by
the supervisor on the owner's behalf; recorded so the owner can overturn them.

1. **A bare year is not a numeric cell for header detection.** PRD: header rows
   are "first row(s) with no numeric cells". `2025 | 2024 | 2023` is the most
   common header in the slice and is numeric under that rule.
2. **The caption search includes the table's own header rows.** PRD: "the
   preceding 500 characters". TGT prints "(millions)" inside the table, and
   without "in", so PRD's `in millions` pattern would miss it twice over.
3. **The scale before "except" is the table's scale.** AAPL's statements read
   "(In millions, except number of shares, which are reflected in thousands, and
   per-share amounts)". Two scales with no "except" returns None, never a guess.
4. **`fiscal_periods` holds the printed column labels**, e.g. "Years ended
   September 27, 2025", "Three Months Ended March 28, 2026", TGT's "2025". PRD
   6.2's example is `["FY2024", "FY2023"]`. Converting a printed date to an FY
   label is the calendar derivation finding #5 rejected (TGT fiscal 2025 ends
   2026-01-31). The issuer's fiscal label for the *document* is in the context
   line, from dei; per-column labels stay as printed.
5. **Table titles are heuristic and PRD does not define them.** Order: a
   label-only header row inside the table, else the nearest short heading in the
   preceding blocks (skipping captions, page furniture and "...as follows:"
   lead-ins, stopping at prose or another table), else the label-column header.
   When none is found the context line reads `[Table | ...]`, never a guess.
6. **Currency is "USD" only when a cell prints `$`.** No currency is inferred
   from the company.
7. **`Block` gains `scale_source`** (`"caption" | "ixbrl" | None`), alongside
   the same field on `Table`. Not in PRD 6.2's `Block`. Additive, so the Phase 3
   unit-scale accuracy metric can be broken out by where the scale came from.

On item 4: if Phase 3's fiscal-period checks need per-column FY labels, that is a
separate tested function written then, driven by a measured miss -- not a guess
now. The document's fiscal label already comes from dei and is in the context
line.

### F-45 — a table with no caption takes its scale from iXBRL, never from its section

COST states units once per section ("(amounts in millions, ...)" under the Item 7
and notes headings), so the 500-character window finds no caption for 11-22
scaled tables per COST filing.

**Decision.** In order: (1) a caption in the window or the table's own header
rows; (2) else, if the table's tagged figures carry exactly one magnitude
`scale`, that scale; (3) else None. A caption wins when present.
`test_caption_scale_never_contradicts_ixbrl_scale` is the guard: if it fires on a
wider corpus, the answer is None plus a logged conflict, not a pick.

"Exactly one magnitude" counts only scales 3, 6 and 9. Measured on the slice:
of 266 tagged data tables, 187 are tagged at 6 alone, 17 at {0, 6}, 14 at
{-2, 6}, 20 at {0, 3, 6}, 10 at {3, 6}, 10 at {0, 3}. Scale 0 (per-share
amounts, counts) and -2 (percentages) sit inside a millions table the way
"except per share" sits inside a caption, so {0, 6} is millions. {3, 6} --
dollars in millions, share counts in thousands -- is None, the same rule as a
caption naming two scales with no "except".

**Rejected:**
- *Inherit the nearest caption in the same section.* A stray "(in thousands)"
  earlier in a section would silently scale every later table. A wrong scale is
  the 10^6 error and is invisible downstream; a missing one is detectable.
- *Leave None.* Throws away the issuer's own tagged assertion of the scale, which
  in 12 filings never once disagreed with a printed caption.

The residual -- data tables with no caption and no single tagged magnitude, 0-14
per filing -- is a number for the parse-quality score in the validation step, not
something to paper over. Much of it is genuinely unscaled (store counts,
percentages). Phase 3's unit-scale accuracy by `scale_source` is what says
whether the rest matters.

**Monetary veto (supervisor, 2026-10-01).** "Exactly one magnitude, ignoring 0
and -2" is accepted only with a veto: if any figure whose unit is a currency
carries a scale other than the chosen magnitude, the table gets None and a
logged conflict (`Table.scale_conflict`). Per-share amounts, share counts and
percentages are the "except" set; dollars are not, because a dollar figure at
units under a header reading "in millions" is the invisible 10^6 error this
fallback must never create.

Monetary means a resolved `xbrli:unit` with a single measure in the iso4217
namespace and no denominator. `usdPerShare` is a divide with USD on top, so it is
not monetary -- TGT's EPS figures carry no `scale` attribute at all, and a rule
that treated any iso4217 measure as money would have vetoed its income statement.

Measured on all 12 filings after the veto: **0 fallback tables flip** -- the
per-filing caption/ixbrl counts are unchanged. Fallback tables by scale set: {6}
54, {-2, 6} 5 (all COST), {0, 3} 6. The interpretation affects only caption-less
{0, 6} and {-2, 6} tables: **0 and 5**. (Correcting an earlier report that said
"31 more tables fall back to None": captioned tables keep their caption scale, so
only caption-less ones were ever in play.) Captioned tables with an off-scale
currency figure: also 0, though the veto does not apply to them.

So the reading is now a tested invariant rather than an interpretation:
`test_every_currency_figure_carries_its_tables_scale` asserts, on the three
fixtures, that no dollar figure in a scaled table is tagged at another scale.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: step 5, companyfacts decisions taken while building

Taken while building, each following from an earlier decision; all four
accepted by the supervisor on the owner's behalf.

1. **`xbrl_facts_unlinked.fiscal_year` nullable (migration 0004).** companyfacts
   reports no `fy` for 618 facts in non-periodic forms (8-K, DEF 14A, S-3ASR,
   S-8). Same reasoning as 0003: the column follows the source, and inventing a
   year is the derivation finding #5 rejected. `xbrl_facts` stays NOT NULL, so a
   linked fact without a year fails loudly. *Rejected:* skipping those facts,
   which drops history the unlinked table exists to keep.
2. **`is_comparative = fact.period_end < filing.period_end`.** PRD 6.5.2 says
   "reported as a prior-year column" and gives no rule. This catches the prior
   year in a 10-K and last year-end's balance in a 10-Q. Facts dated after the
   period (cover-page share counts) are not comparative. Unlinked facts have no
   filing row, so no flag.
3. **Value drift is an error, not an update.** A re-run that finds a stored
   fact's value changed in companyfacts raises. Overwriting would change the
   ground truth under any eval already run against it (PRD 11.4).
4. **All taxonomies are stored** (`us-gaap`, `dei`, `srt`, `ecd`, `ffd`), not only
   us-gaap. `CURATED_CONCEPTS` selects later; filtering at load would decide now
   what Phase 3 may ask about.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: step 6, validation suite and parse-quality score

**Assertions** (`api/parse/validate.py`, `check`). Any failure sets
`parse_status = 'quarantined'` and `parse_error` to the failed messages; this is
the only path to quarantine. From PRD 6.2: at least `min_sections` sections;
Item 1A present on a 10-K (a 10-Q's Part II 1A is optional); at least
`min_data_tables` tables; alpha ratio inside `alpha_ratio`. Added, each already
promised elsewhere: the required Items of PRD 6.2 step 2 (10-K 1/1A/7/7A/8,
10-Q I.1/I.2); a `dei:DocumentFiscalYearFocus` (finding #5: quarantine, never
default); every iXBRL span slicing back to its text (the module's load-bearing
invariant). `period_end` is NOT NULL in the schema, so it is not re-asserted.

Choices the PRD leaves open:

1. **The table count counts data tables**, not all table blocks. PRD 6.2 predates
   F-35; counting layout tables would let TGT pass on page footers alone.
2. **`alpha_char_ratio` = letters / all characters.** Measured both candidates on
   the 12 filings: letters/all is 0.720-0.779; letters/non-whitespace is
   0.857-0.918, close enough to the 0.95 bound that prose-heavy filings could be
   quarantined for being good.
3. **`parser_version` is a hash of the parser's own source** (`api/parse/*.py`
   except `validate.py`, plus `api/numbers.py`; first 12 hex). A hand-bumped version can be forgotten,
   and the F-42 freeze check -- "text_sha256 differs under the same
   parser_version: fail" -- is only sound if the version cannot lie. Cost: a
   comment-only edit also changes it, so re-freezing is more frequent than
   strictly necessary.
4. **Bounds live in `api/config.yaml` under `parser:`**, the Appendix A pattern
   for pipeline parameters, not in `eval/thresholds.yaml` (F-23).

**Score** (`score`, tracked in `filings.parse_score`, never gating). The
unweighted mean of whichever of these five are defined for the filing, each in
[0, 1]:

    scale_coverage     = (caption + ixbrl scaled data tables) / data tables with
                         a caption or a tagged magnitude
    uncollapsed_tables = 1 - data tables with a multi-figure value cell / data tables
    span_resolution    = numeric spans with a parsed value / numeric spans
    required_items     = 1 - missing required Items / required Items
    alpha_in_bounds    = 1 if the alpha ratio is inside the bounds, else 0

`required_items` and `alpha_in_bounds` are identically 1 on any row that passes
`check`, so on parsed filings the score separates only through `scale_coverage`,
`uncollapsed_tables` and `span_resolution`. Equal weights because nothing
measured yet justifies any other. A component with
a zero denominator is left out rather than scored as 1 or 0, either of which
would be a fabricated value. `scale_coverage` is reported with its source
split (caption / ixbrl) in the runner output so the Phase 3 metric can follow it.
The remaining imperfections are known: scale misses are the mixed-magnitude
tables, span misses are word-form numbers (F-33).

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: xbrl_spans rows, and the Phase 1 exit

**Which spans become rows.** `xbrl_spans` holds `is_numeric` spans with a parsed
value; word-form figures (F-33: "one", "two") are skipped and counted, 4-13 per
filing on the slice. `xbrl_spans.value` stays NOT NULL, as migration 0002 and PRD
6.5.2 declare it, and PRD scopes the table to `ix:nonFraction`.

*Rejected: make `value` nullable and store the word-form spans too.* Every
consumer of this table -- span-to-chunk resolution in Phase 2, gold labels and
the restatement-aware lookup in Phase 3 -- reads `value`, and a nullable column
pushes a "skip if NULL" into each of them, where forgetting it once compares a
claim against nothing. The skipped spans are not lost: `span_resolution` in the
parse-quality score counts them, and the parsed document still carries them.
Inventing a value from the word ("one" -> 1) is the guess CLAUDE.md rule 1
forbids.

Also: all contexts are stored, dimensional included (F-32 filtering is Phase 3's
job); spans are written in the same transaction as `norm_path` and the `filings`
row, deleted and rewritten per accession; a quarantined filing keeps none. No
columns beyond the migration -- `sign`, `unit_ref` and `element_id` stay in the
parsed document.

**Hand inspection at the Phase 1 exit was done by the builder**, not the owner:
two data tables and three stored spans per filing, all 12, in WORKLOG. The owner
should repeat it on those WORKLOG samples against the printed filings before
treating Phase 1 as signed off. The builder's pass found three implausible
table extractions, filed as F-50, F-51 and F-52; no stored span was implausible.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: F-50 and F-51, the last table fixes before chunking

Fixed before the chunker because a parser change after embedding means a
re-embed, and F-16 already says that budget is short. Scope is exactly two rules.

**F-50 -- the caption search stops at a preceding table boundary.** The window is
still 500 characters, but it begins no earlier than the end of the nearest
preceding table. A header-less continuation stays header-less. Same principle as
F-45: a scale or a label is never inherited, from a section or from a neighbour.
An inferred label in a cited chunk is a false grounding -- the chunk would assert
something the filing does not print at that location.

*Rejected:*
- *Inherit the preceding table's column labels* for a header-less continuation.
  Usually right, invisibly wrong when the continuation changes periods or
  measures, and the citation would point at text that never says it.
- *Merge the continuation into its predecessor.* Makes one table out of two
  printed ones, breaks PRD 6.3's "a table is never split" in reverse, and puts
  the merged chunk's offsets across text that is not one table.

Measured effect (all 12 filings, 404 data tables): 17 tables change scale. 8 were
percentage-only tables wrongly given "in millions" -- 4 AAPL gross-margin
percentage tables and 4 TGT ("Rate Analysis" x3, "Assumptions") -- now None. 5
AAPL continuations keep millions, now from iXBRL instead of a borrowed caption.
4 TGT ROIC "Denominator" tables, untagged non-GAAP dollar figures whose only
caption is in the preceding "Numerator" table, lose their scale: the cost of not
inheriting, and a missing scale rather than a borrowed one.

**F-51 -- a row whose cells right of the label column are all dashes is a body
row.** Header rows changed across 404 tables: exactly 1, AAPL 10-Q
0000320193-26-000020's share-repurchase table, whose labels lose the "—" and
"$—" and whose title becomes its real heading.

`text_sha256` unchanged on all 12 filings; `parser_version` bfe5929c604b ->
671106d02317.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: the chunker (Phase 2 step 1, PRD 6.3)

Built and stopped for review; not committed. Choices PRD 6.3 does not make:

1. **Blocks before the first Item are not chunked** -- cover page and table of
   contents, 29-47 blocks per filing. PRD 6.3 rule 2 says a chunk belongs to
   exactly one Item, and these belong to none. The cover facts (shares
   outstanding, registrant details) are in `dei` and companyfacts.
2. **`item_code` is part-qualified on a 10-Q** ("I.1", "II.1A"), plain on a 10-K
   ("1A"), because a 10-Q has two Item 1s (F-04). PRD 8's `item_code` comment
   shows plain codes; the metadata filter in PRD 7.1 must match this form.
3. **A prose run ends at every data table**, so no prose chunk's offsets span a
   table. Otherwise a span inside the table would resolve to both chunks.
4. **Page furniture** (PRD 6.2 step 4) is a non-data block whose digit-normalized
   text repeats `furniture_min_repeats` (5) times in the filing and does not end in
   "." or ":". Measured: footers 22-80 repeats, real repeated content at most 8,
   and the repeated content that matters ("None.", "Not applicable.") ends in a
   full stop. Misses TGT's rarer running headers (F-54).
5. **Layout tables with prose chunk as prose (F-46)** -- all layout tables that
   are not furniture. No length rule: tables of contents (85-129 chars) and
   exhibit indexes (180-370) overlap real prose tables (330-1,105) in cell length.
6. **Sentence pieces of an oversized paragraph, and row-group parts of an
   oversized table, keep their block's offsets.** *Reversed for tables by the
   supervisor -- see "chunk budget and tokenizer (F-53); split-table offsets".* Sub-block offsets would need a
   second coordinate system. Consequence for span resolution: a span in a split
   table falls in several chunks' ranges.
7. **`chunk_id` = `{accession}:{block}.{piece}:{block}.{piece}`**, PRD's
   `block_start:block_end` plus a piece index so sentence pieces and table parts
   stay unique.
8. **A prose chunk's `raw_text` is its kept units joined by newlines**, not a
   slice of the normalized text: dropped furniture between blocks is not in it.
   `char_start`/`char_end` still bound it in the normalized text.
9. **The token budget covers the whole embedded text**, header included.
10. **`page_hint` is not computed.** PRD 6.2 step 5 is approximate by its own
    account; nothing consumes it yet.

Open, not chosen: the tokenizer (a dependency) and the target size (F-53).

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: chunk budget and tokenizer (F-53); split-table offsets

**Budget: `chunking.target_tokens: 500`**, counted on the whole embedded text --
context header and [CLS]/[SEP] included -- with the embedding model's own
tokenizer. 500 is the floor of PRD 6.3's 500-800 range and inside
`embedding.max_seq_length: 512`. The chunker counts every chunk, prose and table,
whose `token_count` exceeds 512; a violation is a number in the run summary,
never a truncation.

*Rejected:*
- *Keep 700 and accept truncation.* bge-base-en-v1.5 would silently drop the tail
  of most chunks -- the PRD 7.5 trap for NLI, here for retrieval.
- *A longer-context embedding model.* Outside PRD 6.4's list, and a larger change
  than the chunk size.
- *Below 500.* Outside the PRD's range.

**Tokenizer: `tokenizers` added as a dependency**, loading the vendored
`tokenizer.json` of the pinned model revision. It is the file sentence-transformers
loads for the same model at step 3, so the count here and the truncation there
agree. Truncation and padding are switched off when counting, so a long chunk is
measured, not capped at 512. Unit counts exclude special tokens so pieces add up;
a chunk's final `token_count` includes them, so it is the real sequence length.

**Decision 6 reversed for tables.** A row-group part of a split table takes
`char_start`/`char_end` from its own rows: the first part from the table's start,
the last to its end, so the parts tile the table without overlap. Otherwise every
iXBRL span in a split statement would resolve to every part and Phase 3's gold
chunk would be ambiguous. Row offsets come from `Table.body_offsets`, carried
through `_cell_rows` and fragment merging, because empty HTML rows are dropped
before `Table.body` is built and Block.rows cannot be indexed by body position.
Sentence pieces of an oversized paragraph still share their block's offsets; step
2 counts spans landing in them.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: span-to-chunk resolution (Phase 2 step 2)

1. **A span resolves to a chunk whose `[char_start, char_end)` contains it; with
   several candidates, the earliest chunk wins.** Table spans have one candidate
   (split parts tile their table). Prose spans can have two -- overlap, or
   sentence pieces sharing a block's offsets -- and both cases are counted. On the
   slice: 6 overlap, 0 split-paragraph. *Rejected:* resolving to every candidate
   (one `chunk_id` column cannot hold it, and Phase 3's gold set would double-count
   the overlap region).
2. **The PRD's 80% floor lives in `api/config.yaml` under `span_resolution:`**, not
   in `chunking:`, so changing the floor does not change `chunker_version`.
3. **Spans before the first Item are their own category** and stay unresolved:
   on the slice, all 15 are `dei` cover-page facts (shares outstanding, public
   float), which no chunk covers by chunker decision 1.
   None of the 15 is a `CURATED_CONCEPTS` concept (PRD 6.5.3), so no gold set is
   lost; if `eval/concepts.yaml` ever adds a `dei` concept, PRD 6.5.3's
   `len(gold) == 0` branch routes it to human labeling.

`chunker_version` hashes `api/chunk/` code, the vendored tokenizer and the
`chunking:` config; `store.py` and `resolve.py` are excluded the way
`validate.py` is from `parser_version`. Chunking refuses a filing whose stored `parser_version` or
`norm_path` text differs from a fresh parse.

---

## 2026-10-01 — F-56: a sentence may start with a digit

The chunker's sentence splitter now allows 0-9 after a sentence end -- the same
class of false split as "Mr. Smith" already is, acting only inside paragraphs
already over budget, so offsets are unaffected; it removed both over-limit chunks
(TGT 10-K exhibit index, 648 and 992 tokens) and changed nothing outside that
filing.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: embedding cache (Phase 2 step 3)

**The content-hash cache is its own table, `embedding_cache` (migration 0006),
keyed on `(content_hash, model, revision)`; `chunks.embedding` is filled from
it.** `content_hash` is sha256 of `chunks.text`, header included -- exactly what
is embedded. The cache outlives chunk rows, which `store.py` deletes and
reinserts on every re-chunk, so an unchanged chunk is never re-encoded. Model and
revision are in the key, so a vector from a different model can never be read
back as current.

*Rejected: carry embeddings over inside `store.py`* (keep the old row's vector
when a re-chunked row has the same `content_hash`). It cannot tell a stale
model's vector from a fresh one -- `chunks` records no model or revision -- and it
would couple the chunk writer to the embedder.

Also decided while building, inside the supervisor's spec: `embedding.dim: 768`
and `embedding.batch_size: 64` live in `api/config.yaml` (Appendix A's keys), with
a third pre-write check that the model's dimension equals `dim` -- the columns are
`VECTOR(768)`. The model weights are not vendored: they come from the Hugging Face
cache at the pinned revision (the tokenizer, which decides chunk sizes, is
vendored and sha-checked).

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: F-54 navigation rule

The furniture rule's repeat signal, moved from text to link targets. No phrase
rule and no new number: it reuses `furniture_min_repeats` and the furniture
guard. Same candidates as furniture (every non-data block).

A block is navigation when (a) it has at least one in-document anchor
(`<a href="#...">`, recorded by the walker as `Block.anchors`), (b) its residual
-- the text with anchor spans removed, whitespace-normalized -- does not end in
"." or ":", and (c) its anchor-target set, as a sorted tuple, occurs on at least
`furniture_min_repeats` candidate blocks of the filing. Keying on targets, not
text, is what stops TGT's per-section label ("RISK FACTORS", "BUSINESS", ...) from
splitting the count; (b) is what keeps a hyperlinked cross-reference sentence
("See accompanying Notes to Consolidated Financial Statements.").

*Rejected:*
- *Residual-is-a-section-label.* Needs a length cap or a heading match: a new
  number or a phrase list.
- *Anchor-text fraction of the block.* A new number.
- *All-anchor blocks only.* Measured: 1 of 28-80 nav blocks per TGT filing.
- *Literal match on "Table of Contents".* Filer-specific.

Known false positive, measured, not tuned: TGT 10-K Item 15's list item
"•Notes to Consolidated Financial Statements" links to the Notes, shares that
target set with seven "See accompanying Notes..." sentences, and has no full stop
(F-58).

**Addendum (F-58).** Block 826 stays dropped through the freeze. The alternative
was a one-block rule -- a length cap, a phrase list or a bullet check, the shapes
rejected above -- tested on 3 filers but run on 8 in Phase 5; the block is a
hyperlink label with no figure and no span. Reopening it after the freeze
re-resolves every gold chunk id, so it is a before-Phase-3 decision for the owner.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: Phase 2 baseline

Scope is PRD 14's line and nothing from PRD 7.4: dense-only, top 5, unstructured
generation.

1. **No query instruction prefix.** The question is embedded with the same
   pinned model and revision as the chunks, exactly as they were: normalized,
   nothing prepended. PRD is silent. *Alternative:* the bge model card's prefix
   on queries only ("Represent this sentence for searching relevant passages: ").
   A query longer than `max_seq_length` fails, as a chunk would.
2. **`baseline.top_k: 5` in config**, separate from `retrieval.k_dense` (the
   Phase 4 hybrid candidate pool).
3. **Through chunks_hnsw.** On a corpus this small the planner picks an exact
   sequential scan; the retrieval transaction sets `enable_seqscan = off` (LOCAL)
   so the baseline uses the index it specifies, and the CLI prints the plan node.
4. **Generation: Anthropic, `tier_small` = `claude-haiku-4-5-20251001`**, with
   `tier_large` = `claude-sonnet-5-5` as given. PRD 12's CI carries only
   `ANTHROPIC_API_KEY`. `anthropic==1.11.0` pinned; it replaces nothing.
   `max_tokens: 1024` added to `generation:` -- the Messages API requires a cap
   and Appendix A has none. `usage` token counts are kept with every answer.
5. **No `temperature`.** The pinned SDK's `Messages.create` takes no sampling
   parameters at all, so Appendix A's 0.0 cannot be sent; the key is not kept in
   config, where it would claim a setting the run does not have (F-60).

**F-60 resolution path (supervisor, 2026-10-01).** Generation without a
temperature parameter is accepted: there is nothing else to send. The
determinism requirement in PRD 7.4, 11.4 and Appendix A is replaced by
measurement. In Phase 3 the runner records `response.model` per item and repeats
the fast subset at least 3 times on identical config, reporting the spread of
every gated metric beside its value. Kappa is computed on one fixed run against
the owner's hand labels. The spread is reported noise, never a reason to widen a
threshold; a threshold sitting inside it is an F-07 input. The PRD text stays as
is; this entry carries the override.

*Rejected:*
- *Downgrade the SDK to one that still has `temperature`.* The client is
  generated from the API surface, so an older one sends a parameter the API no
  longer defines -- the same "claims a setting the run does not have" removed
  from config.
- *A seed policy.* There is no seed parameter; a policy would be fiction.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: the eval corpus is the PRD's 3-year filing-date window, materialized (F-42)

The window, evaluated once as of 2026-10-01 (`scripts/materialize_corpus.py`):
10-K and 10-Q by exact form (no amendments, the dev slice's rule), filed in
[2023-10-01, 2026-10-01], reportDate present. The result, not the window, is what
gets committed under `corpus` in `api/config.yaml`; ingest reads the list.

*Rejected: a fiscal-year-aligned corpus* (e.g. the last three complete fiscal
years per company). The window is the PRD's own definition, nothing measured
argues for deviating from it, and it already gives every company three 10-Ks and
two complete fiscal years (10-K + Q1-Q3), which is what comparison items need.

**Paginated submissions.** `assert_recent_covers_window` fired on JPM, as it was
written to: `filings.recent` reaches back only to 2025-10-01 against 70 older
files (BAC: 21). `submissions_since` merges every paginated file whose `filingTo`
reaches the window, and the guard then counts only remaining files that could
hold window filings. `ingest_accessions` merges pages the same way when an asked-
for accession is not in `recent`, bounded by an optional earliest filing date.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: F-62, XOM's corpus source

ExxonMobil reorganized in 2026: SEC's ticker map now sends XOM to the successor
ExxonMobil Holdings Corp (CIK 0002115436, 8-K12B), whose first periodic filing is
the 2026-08-03 10-Q. All 12 window filings were filed by the predecessor, Exxon
Mobil Corp (CIK 0000034088) -- the shared 10-Q's accession prefix says so -- and
the predecessor's record now carries `tickers: []`, so a live ticker lookup can
never return it again.

**(a) chosen:** XOM's `companies` row is cik 0000034088, ticker XOM. All 12
filings come from it. The successor is a companyfacts source, not a filer of
anything in the corpus: `companyfacts_ciks: ["0000034088", "0002115436"]`, each
loaded with the pinned CIK as the stamp, linking by accession. No schema change;
one row per ticker holds.

*Rejected:*
- *(b) the successor CIK only:* 1 filing, so energy loses its comparison coverage.
- *(c) replace XOM:* changes PRD 4.4's company set. Both are larger deviations
  than pinning a CIK.

**CIK pinning, a deviation from PRD 6.1's ticker lookup**
(`company_tickers.json`, `cik = resolve_cik(ticker)`). All 8 companies carry a
pinned `cik` in `api/config.yaml`: the ticker-to-CIK mapping is SEC state at a
point in time, so the result is committed, not the lookup -- the F-42 principle
again. `resolve_cik` survives only in the materializer, which prints where SEC's
current mapping differs (XOM) and does not fail.

**Two ingest fixes the full corpus run forced:**
- *Page metadata is not trusted.* JPM's paginated file 020 is listed with
  `filingTo: 2023-10-31` but holds a 2023-11-01 10-Q, so bounding page reads by
  the listing skipped a corpus filing (the run failed loudly on it). Pages are
  now read newest first until the data itself passes the window start
  (materializer) or every asked-for accession has been seen (ingest). The
  `assert_recent_covers_window` guard became unread and was removed; the page
  loop is now the guarantee, measured on the data rather than the listing. The
  materialized list is identical either way (96).
- *Staged facts are promoted.* Facts loaded into `xbrl_facts_unlinked` before
  their filing joined the corpus stayed there after being inserted as linked
  (COST 2,569, TGT 2,831, AAPL 2,273 double-stored). The loader now deletes
  unlinked rows whose accession is in `filings`, in the same transaction, after
  checking incoming linked values against those staged copies for drift.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: fix the parse findings before the freeze (F-63..F-67)

Decided by the supervisor on the owner's behalf after 45 of 96 filings
quarantined and JPM's 10-Ks passed while mis-sectioned.

1. **Fix F-63 to F-67 before the freeze**, as PRD 6.2 section-detection bugs the
   full corpus exposed. Generic mechanisms only -- no per-ticker paths, no
   company-specific regexes. A filing that still fails stays quarantined with a
   finding. One commit per finding, each re-measured on the 48 clean filings
   (identical section lists, chunk-hash changes explained, resolve rate,
   snapshots, new `parser_version`). Order: content check, F-63, F-64,
   F-65/F-66, F-67.
2. **JPM: build PRD 6.2 step 2's table-of-contents-anchor fallback**, the unbuilt
   half of the specified mechanism. Primary heading detection stays
   authoritative; the fallback fills only Items it missed. If JPM's index rows
   carry page numbers with no hrefs, stop -- no page mechanism (F-55).
3. **A content check on required Items.** Minimum text length per required Item
   (10-K 1, 1A, 7, 7A, 8; 10-Q I.1, I.2) in `api/config.yaml` under `parser:`
   (F-23), each value the measured minimum across the 48 clean filings.

*Rejected:*
- *Freeze the 51 that parsed now.* Not PRD 4.4's corpus: no financials pair, no
  pharma, no energy.
- *Drop companies* (PRD 14 cut order 5). The owner's call, not the builder's.
- *Keep JPM as-is under Item 15.* Every JPM MD&A and statement chunk would carry
  an "Item 15" context header, and PRD 6.2 says bad parses do not enter the index
  silently.
- *Existence-only validation.* It passed JPM's 10-Ks with 395-char Items 7 and 8.

**How the fallback works (F-65), as built.** The walker records the text offset
where every `id`/`name` link target begins (`anchor_targets`; normalized text
unchanged on all 96). Any table that is not itself a heading table contributes
the Item and Part rows that carry their own resolvable in-document link -- not a
count of Items, because JPM splits one index over two tables, the first holding
only Item 1. A resolved Item row fills only an Item primary detection missed. A
resolved Part row joins the primary Part markers, and a Part starts at its
earliest known position: JPM's pages carry "Part IV" running headers that begin a
few blocks after Item 15's heading, so a fill-missing-only rule left Item 15 in
Part III. Rows with page numbers and no link contribute nothing (F-55).

**JPM's 10-K MD&A and statements are not relocated.** The index's Item 7 and 8
rows link to the in-body stubs, and the stubs name the Annual Report pages
holding the content with no link. That is the stop condition: no page mechanism
(F-55). The three 10-Ks stay quarantined by the content check (F-66).

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: F-67, splitting units over the token budget

Never raise 512, never truncate. Measured first: of the 28 chunks over 512 after
F-65, 16 were layout tables chunked as prose (PFE's pipeline tables, NVDA's
exhibit index; longest row 98 tokens) and 12 were ordinary paragraphs that are a
single over-budget sentence (BAC's forward-looking-statements sentence, 617-656
tokens of "; "-separated clauses; XOM's "These include ..." risk sentence).

1. **Layout tables (as specified):** a layout table over the prose budget splits
   at row boundaries, its first row repeated at the head of every part; parts
   take offsets from their rows and tile the table (PRD 6.3 rule 1).
2. **Over-budget sentences (beyond the spec, so flagged):** split at clause
   boundaries ("; "), and only a clause still over budget into whitespace
   windows -- the same last resort the spec allows for a single row. Without it
   the 12 paragraphs would either exceed 512 (the embedder refuses the run) or
   be truncated (ruled out).

Whitespace windows used across the 84 parsed filings: 0. *Rejected:* raising
`max_seq_length` (the model's input), truncation, and leaving the 12 for a later
fix (embedding cannot run until every chunk fits).

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: the stub check replaces the content floors (F-69); freeze at the resulting set

**The check, redefined by what it is for** -- F-66: content sitting outside the
Item whose label it should carry. One parameter, `parser.stub_max_chars`; an
Item at or below it is a cross-reference stub. 10-K Items 1, 1A, 7 and 10-Q
Items I.1, I.2 must not be stubs: every Item 7 stub in the corpus (JPM, XOM) has
its content outside the Item structure, and no data argues for relaxing 1 or 1A.
10-K Items 7A and 8 may be stubs but must exist (PRD 6.2): BAC's and PFE's 7A
point to "Market Risk Management" inside Item 7, NVDA's 8 to Item 15, so the
content keeps the label the filer gave it. Validation lists each filing's stub
Items, which makes F-68 visible per filing.

The value was set only after measuring: every required Item on all 96, each
under 5,000 chars quoted in WORKLOG. No Item 1, 1A, 7, I.1 or I.2 lies between
500 and 5,000 chars, so `stub_max_chars: 1000` was set as specified; the Items
at or below it are exactly JPM's and XOM's Item 7.

*Rejected:*
- *Keep the floors and freeze 84.* Excludes six faithful parses on a verdict
  known to be false.
- *A minimum over 8 filers.* The same defect -- a minimum over a sample rejects
  the next legitimately shorter filer by construction -- and choosing which new
  filings count as clean would fit the check to pass.

**The freeze at the resulting set: 90 of 96.** Written once the six admitted
10-Ks (BAC x3, PFE x3) passed the Phase 1 exit inspection, without waiting for
JPM or XOM. The record, `api/corpus_freeze.yaml` (next to the corpus list in
`api/config.yaml`), covers all 96 listed accessions: each parsed filing with
`(accession, text_sha256, parser_version)` per F-42, each quarantined one with
its reason and finding ID (F-66 JPM, F-70 XOM), a per-ticker count of 10-Ks and
10-Qs, and a reference to F-58. `python -m scripts.verify_freeze` re-derives
`text_sha256` for every frozen accession and exits 1 on any difference.

*Rejected:*
- *Wait for a JPM/XOM relocation mechanism.* The PRD specifies none (pages for
  JPM, section titles for XOM), and waiting blocks Phase 3. PRD 16: quarantine
  and move on.
- *Drop JPM and XOM.* PRD 14 cut order 5, the owner's call; their 10-Qs stay in.

**Phase 3 consequence.** No FY items for JPM or XOM -- their only annual filings
are quarantined -- so the bank pair's annual comparison (JPM vs BAC on 10-K
figures) is unavailable; quarterly comparisons from the 10-Qs remain.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: F-71 left as a known residual of the frozen corpus

BAC's 10-K Item 7 and 8 heading tables carry a "Table of Contents" cell that is
not a link, so it stays in the section title; Item 7's title also carries the
"Bank of America Corporation and Subsidiaries" prefix from the same table.
Measured on the stored chunks of the 90: exactly BAC 10-K Items 7 and 8, three
filings, 1,822 chunks. Company, form, period and Item in those headers are
correct; normalized text, offsets and span resolution are untouched. No parser
change and no re-freeze: the fix would be a literal-string rule for one filer's
heading table, would still leave the company-name prefix, and the freeze is
where parser work stops (PRD 14: timebox hard).

*Alternatives:*
- *Fix now and re-freeze.* Cheap today: no eval item or run depends on the freeze.
- *Fix after the golden set exists.* The header counts against the token budget,
  so BAC 10-K chunk IDs can shift: a re-freeze plus a dataset version bump.

**The cheap window closes when the first gold evidence set is written.**

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: Phase 3 step 1, what xbrl_auto may draw on

Measurement only; no eval item generated, no retrieval run against candidates.

1. **F-32:** `xbrl_auto` draws on non-dimensional facts only. companyfacts
   carries no dimensional facts, and gold chunks count only spans on
   non-dimensional contexts. F-32 stays OPEN until the generator enforces this
   under test.
2. **F-48:** a fact with no visible span has no gold chunk; PRD 6.5.3 sends it
   to the human-labeling queue (`eval/human_label_queue.csv`). The labeling is
   OWNER-BLOCKED.
3. **Corpus:** facts come only from the 90 parsed accessions in
   `api/corpus_freeze.yaml`.
4. **F-15:** the list lives in `eval/concepts.yaml` and
   `scripts/concept_coverage.py` reads it; every number about it comes from
   that script.
5. **The list, and the rule as applied.** 26 line items, 28 tags:
   - *named:* all 19 PRD 6.5.3 concepts, kept whatever their filer count
     (`GrossProfit` and R&D at 2 filers, `CostOfRevenue` at 1,
     `AccountsReceivableNetCurrent` at 3, `LongTermDebtNoncurrent` at 4);
   - *bank supplements:* net interest income, noninterest income, noninterest
     expense, the credit-loss allowance, deposits, pre-tax income and income
     tax -- chosen by PRD 6.5.3's own criterion, lines an analyst asks about,
     among concepts both JPM and BAC tag in nearly every frozen filing (not by
     coverage alone);
   - *variants:* `RevenueFromContractWithCustomerExcludingAssessedTax` for
     revenue and `CostOfGoodsAndServicesSold` for cost of revenue, used by a
     filer only if it has no fact under the named tag in the frozen 90. Revenue
     resolves to the variant for AAPL and TGT; cost of revenue to `CostOfRevenue`
     for NVDA and the variant for COST, TGT, AAPL and PFE. Each variant-only
     pair has a printed row caption in WORKLOG naming that line.

   No retrieval result was consulted.

   *Alternatives:*
   - *The builder's first 26* -- dropped PRD-named concepts (`CostOfRevenue`,
     `AccountsReceivableNetCurrent`, `LongTermDebtNoncurrent`) for reasons the
     data does not force, and fed both revenue tags to one question; for PFE's
     FY2023 10-K those differ (58,496M vs 50,914M), so one question had two
     answers.
   - *Basic EPS as its own concept.* A scope addition: basic is a different
     figure from the named diluted EPS. Struck, with `LongTermDebt` (it includes
     current maturities, so it is not the `LongTermDebtNoncurrent` line).
   - *Both revenue tags as line items with distinct labels.* Two questions whose
     wording a reader cannot tell apart, on a distinction (total vs contract
     revenue) the filings print differently from filer to filer.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: F-72, gold is exact-value spans only

A fact's gold chunks are the chunks holding a span of the same accession,
concept and non-dimensional period **whose value equals the fact's**. The
reference answer is the fact's value and numeric accuracy is exact match after
normalization; a chunk printing only "$201 billion" cannot produce 201,131
million, so counting it as sufficient would credit retrieval with evidence that
cannot yield the answer, and the miss would surface as a generation failure.
PRD 6.5.3's key assumed every span of a context prints the fact's value; 68
facts say otherwise, so the data wins. Buckets are computed on exact-value gold.
Nothing extra is stored on an item; rounded mentions stay derivable from
`xbrl_spans`.

Measured on the final list (`python -m scripts.concept_coverage`): 4,335 facts;
68 have a smaller gold set under exact value; no bucket changes; none left
without gold. *Alternative:* PRD 6.5.3's literal key `(accession, concept,
context)`. F-72 stays OPEN until the generator enforces it under test.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: F-11, the `source` enum and natural_phrasing

1. `source` keeps PRD 11.2's three values: `xbrl_auto`, `llm_seeded`,
   `handwritten`. The per-source breakout is `filter(source=src)`.
2. natural_phrasing is a `question_type` (a row of PRD 11.1's Type column) with
   `source = handwritten`.
3. **The handwritten gate is all of `source = handwritten`, controls included.**
   The 30 controls also get their own reported row (PRD 11.1) and feed
   `natural_phrasing_gap` (F-20). No threshold changes.
4. The xbrl_auto share is computed from the frozen dataset's counts and printed
   in every report, not argued from the plan (on the plan: 160 `xbrl_numeric` +
   40 auto comparisons = 200/410 = 49%).

*Alternatives:*
- *Carve natural_phrasing out of the handwritten gate* (the builder's first
  proposal, and the question finding #11 left open). Rejected: "they pull the
  slice down" is a reason about the score, not about what is measured. By PRD
  11.1's counts the carve-out leaves the 20 hand-written comparisons as the only
  handwritten items with gold evidence (unanswerable 50 and adversarial 20 have
  none), so the handwritten retrieval gate would rest on 20 items.
- *A fourth `source` value `natural_phrasing`.* Breaks PRD 11.2's three-column
  breakout and makes `source` mean something other than provenance.
- *A `natural_phrasing` tag.* A second place to encode what `question_type`
  already says.

F-11 stays OPEN until the share is printed from a real dataset.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: F-75, one item per period key

The sampling unit is the key (cik, concept, period_start, period_end), not the
fact: 1,234 of 2,553 keys appear in more than one parsed accession, so a
per-fact draw would ask the same question several times.

- **Eligible key:** all three hold.
  - (a) One distinct value across all parsed accessions carrying it.
  - (b) Every fact of the key, in every accession, is in the 1-3 bucket ("all
    1-3", not "mixed").
  - (c) At least one non-comparative fact, i.e. a parsed filing reports the
    period as its own. Measured: every key has exactly one such filing or none
    (1,898 vs 655).
- **The 61 value-differing keys are not auto items.** They go to
  `eval/review_queue.csv` with a reason, OWNER-BLOCKED. The cause of the
  difference is not established, and a question with two defensible answers is
  what PRD 6.5.3 routes to review.
- **Gold:** every exact-value chunk in every parsed accession carrying the key,
  each chunk its own alternative evidence set. `gold_accessions` lists every one
  of those accessions; `xbrl_fact_id` is the own-period filing's fact.
  Own-filing-only gold would score a retrieved comparative column that prints
  the exact figure as a miss, which is the noise PRD 11.1's evidence sets exist
  to remove.
- **Filing-scoped wording:** a template that names the filing ("According to
  its {year} 10-K") takes gold from that filing only. The pool keeps evidence per
  accession so both are derivable. This applies at templating.
- **Period label:** from the own-period filing's dei labels
  (`filings.fiscal_year`, `filings.fiscal_quarter`), never from
  `xbrl_facts.fiscal_year` / `fiscal_period`. Those are companyfacts `fy`/`fp`
  and describe the reporting filing. Verified: on all 20,187 comparative rows
  of the parsed filings they equal the reporting filing's labels (WORKLOG).
- **Why (c):** the 655 comparative-only keys have no issuer-stated label in the
  corpus. Deriving one from dates (TGT's FY2025 ends 2026-01-31) is how a wrong
  reference answer gets in silently.
- **QTD vs YTD:** a Q2/Q3 10-Q holds both under one dei label. The pool carries
  `period_start`/`period_end` so templating can word them apart.

*Alternatives:*
- *Original wins* for the 61 (the builder's proposal): picks an answer whose
  disagreement is unexplained.
- *Latest wins*: the same, in the other direction.
- *Filing-scoped templates only*: one answer per filing, but every question
  must name a filing and the cross-filing gold above is lost.
- *Own-filing-only gold*: scores an exact comparative-column hit as a miss.
- *Date-derived labels for comparative-only keys*: wrong when the fiscal year
  is named for the calendar year it ends in or not.

F-75 stays OPEN until the generator enforces this under test.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: xbrl_auto sampler design

- Pure function, seeded RNG; the seed goes in the dataset manifest with the
  freeze versions.
- Pool: eligible keys only (F-75 (a)-(c)). The rest are accounted for: review
  (>3, mixed key, value differs) in `eval/review_queue.csv`, or not sampled
  (comparative-only). 0-gold facts go to `eval/human_label_queue.csv`
  (currently empty).
- Strata: ticker x line item x form **of the own-period filing**. Equal
  allocation, 20 per ticker for 160 `xbrl_numeric` items, round-robin over the
  ticker's strata, no key drawn twice. Seed, total and allocation are config.
- If a ticker has fewer than 20 eligible keys, there is no backfill from
  another ticker; the shortfall is reported.

*Alternatives:* proportional to supply (over-weights AAPL and NVDA, starves
JPM and XOM); stratifying by line item first (bank supplements have only two
tickers); per-fact sampling (repeats keys, F-75).

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: pool and sampler code, config and validator rules

- **Location:** `eval/generate/` (PRD 13.4); `scripts/xbrl_pool.py` imports from
  it. `build_pool` takes fact rows, so `eval/generate` imports nothing from
  `scripts/`.
- **Config:** seed, total (160) and per-ticker allocation live in an
  `eval_sampler:` block of `api/config.yaml`, read by `api.config.eval_sampler()`
  like every other block. *Alternative:* a separate `eval/sampler.yaml` (a second
  config file and loader for three keys).
- **Allocation is explicit per ticker** (8 x 20) and must sum to `total`; the
  sampler raises `Shortfall` instead of backfilling. *Alternative:* a derived
  `total / n_tickers` (hides the allocation the owner may want to change).
- **Validator rules beyond the field list:** an `xbrl_auto` item names its
  `xbrl_fact_id`; `natural_phrasing` is `source = handwritten` (F-11); an abstain
  item has `reference_answer` null (PRD 8); an answerable non-`unanswerable` item
  has at least one evidence set. `question_type` follows PRD 11.1, not PRD 8
  (F-76).
- **A fact in the 0 bucket** sends its key to `no_gold` (PRD 6.5.3 human labeling),
  ahead of mixed/gt3. None exists on the frozen list.
- **Round-robin order:** per ticker, keys shuffled within each stratum and the
  strata order shuffled, both from one seeded `random.Random`; input sorted first
  so the draw does not depend on row order (tested).

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: the 1-3 rule stays per fact, per filing; no per-form split

**1-3 rule.** PRD 6.5.3's loop is per `(accession, concept, context)`, and its
reason for review is a value repeating inside one filing. Rule (b) of F-75
already applies it to every filing carrying a key. The size of the union over
filings counts how many later filings reprint the period, not ambiguity: 378 of
1,713 eligible keys have more than 3 evidence sets, the 18 largest listed in
WORKLOG.

*Alternatives:*
- *Cap the union at 3.* Sends 378 keys to review, selected by how often a period
  is reprinted: year-end balances and annual figures first, PRD 11.1's own
  example among them (AAPL inventory, 8 sets across 5 filings). Biases the pool
  and cuts the 10-K supply further.
- *Own-filing-only gold.* Rejected under F-75: scores an exact comparative-column
  hit as a miss.

How metrics score many alternative sets is undefined in PRD 11.2 (F-77). It is
settled when metrics are built; gold is not shaped around it.

**No per-form split.** The PRD sets none, and form is already a stratum, which
is why the draw is 60/160 from 10-Ks against 276/1,713 in the pool. A quota could
not hold anyway: JPM and XOM have no parsed 10-K (F-66, F-70). A split chosen
after seeing the draw would be tuning the dataset: the seed stays 20261001 and
there is no re-draw. The per-ticker form split is recorded in the candidates
manifest.

*Alternatives:* a per-form quota in config; a draw proportional to the pool.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: xbrl_numeric candidates (templates, values, fields)

- **Gold** comes from one pure function, `eval/generate/gold.select_gold`
  (non-dimensional, exact value, in a chunk), which the loader calls; tested on
  committed real span rows. *Alternative:* keep the rule inline in the script
  (untested).
- **Templates extend PRD 6.5.3's four annual-only forms.** 100 of the 160 keys
  are quarterly. `eval/templates.yaml` has five forms per period type --
  `duration` (annual, quarter, year-to-date) and `instant` -- so every line item
  has five; one per type names the filing (`scope: filing`) and takes gold from
  that filing only. The seeded RNG picks the form; its id is a tag.
  - Period label: the own-period filing's dei label ("fiscal 2024", "the second
    quarter of fiscal 2024", "the first two quarters of fiscal 2024", "the end of
    fiscal 2024"). Year-to-date is worded in quarters, which is true for every
    filer.
  - Dates: from `period_start`/`period_end`. Month wording for month-length
    periods (85-98, 175-189, 262-280 days); otherwise whole weeks, as Costco
    prints its 12-week quarters ("the 24 weeks ended February 16, 2025").
  - *Alternatives:* PRD 6.5.3's four forms only (no wording for 100 of 160
    keys); month wording for every quarter ("six months" for Costco's 24 weeks,
    wrong); calendar-year labels from dates (wrong for TGT, AAPL, NVDA, COST).
- **`format_value`.** USD at the one ix `scale` the own-period filing's
  exact-value spans print ("$7,286 million"); EPS unscaled at its printed places,
  minimum two ("$4.20"); a negative is "-$320 million". If those spans disagree
  on scale the key is reported and not generated: one key in the whole eligible
  pool (NVDA, F-80), none in the draw. *Alternatives:* always millions; the
  chunk's `unit_scale`; the majority scale (picks one).
- **Fields.** `question_type = xbrl_numeric`, `source = xbrl_auto`,
  `reviewed_by_human = false`, `difficulty = easy` (PRD 11.1's example; no rule
  in the PRD and no metric reads it, F-76). `item_id` is `xbrl_NNNN` in draw
  order. `dataset_version` is `xbrl_candidates_v1` (config).
- **Output** goes to `eval/candidates/`, never a `golden_*` file: the candidates,
  a manifest (seed and the `eval_sampler` block, the freeze's parser and chunker
  versions, the per-ticker form split, the evidence-set distribution, templates,
  the spot-check ids) and the 16-item spot-check sheet. Same seed, byte-identical
  output (tested; re-run checked by sha256).

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: negative and zero values keep their line item's wording

The question's label is a function of the line item, never of the value. Four
candidates are negative: xbrl_0070 (JPM operating cash flow, -$47,257 million),
xbrl_0113 and xbrl_0119 (PFE income tax), xbrl_0115 (PFE operating cash flow,
-$691 million). "Net cash provided by" a negative figure reads the same way as a
negative "expense". In the eligible pool: 32 negative keys (operating cash flow
15, income tax 10, pretax income 3, net income 2, diluted EPS 2) and 6 zero keys
(all share repurchases).

Two candidates are zero: xbrl_0116 and xbrl_0117 (PFE share repurchases),
reference answer "$0 million". Their gold spans print "—" (`value=0`, `scale=6`).
They stay candidates: PRD 6.5.3 auto-accepts on 1-3 gold, and the value is the
SEC's. No exclusion rule, no re-draw, seed unchanged.

All six are on the owner's spot-check sheet in a "flagged, outside the seeded
10%" section, selected by rule (`value <= 0`); the seeded 16 are unchanged.
How "-$28 million" or "$0 million" compare with an answer worded otherwise is
F-81, settled before any run, never by rewording gold.

*Alternatives:*
- *Sign-dependent label* ("income tax benefit", "net cash used in"). Rejected:
  it puts the sign of the answer in the question and makes question text depend
  on the gold value.
- *Sign-neutral caption for every item of those lines* ("income tax expense
  (benefit)"). Left to the owner at review: it rewords items after the draw was
  seen and adds filing vocabulary.
- *Drop negative keys.* Rejected: it selects the pool on the answer.
- *Exclude zero keys and re-draw.* Rejected: it changes the draw after seeing it.
- *Word a zero answer as "none".* Rejected: it breaks numeric exact match.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: guard `xbrl_fact_id` instead of fixing it (F-78)

The candidates manifest records each item's fact by natural key (accession,
concept, period_start, period_end, unit, value).
`python -m scripts.xbrl_candidates --verify` resolves every `xbrl_fact_id` in
`xbrl_facts`, compares it to that key and the candidates file to its recorded
sha256, and exits non-zero on any mismatch. The item schema stays field for
field PRD 11.1. The ids are still not reproducible by a rebuild; a stale id is
now caught instead of silently pointing at another fact.

*Alternatives:*
- *A deterministic `fact_id` via migration.* Rejected: it touches a Phase 1 table
  under the frozen corpus.
- *Do nothing.* Rejected: a stale id in a frozen file would go unnoticed.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: xbrl_auto comparison items (PRD 11.1 comparison row, Stage 3)

Every number here is printed by `python -m scripts.comparison_supply`.

**1. Pool: pairs whose two keys share no gold chunk.** A pair is two eligible
keys (F-75) of one filer and line item, same period kind and fiscal quarter, one
or two fiscal years apart by the own-period filing's dei label (`gaps` in
config). It is eligible only if no chunk holds a tagged exact-value span of both
sides. Only then is Stage 3's "gold set = both chunk_ids" true. The pool is what
the rule yields: instant one year apart 234, instant two years 182, quarter two
years 178, year-to-date two years 146 (740; 622 with neither side among the 160
drawn keys).
- *Excluded by the rule:* all 735 consecutive-year duration pairs, the 49 annual
  pairs two years apart, and 129 consecutive instant pairs (all 73 year-end, 56
  quarter-end) -- including the shape of PRD 7.1's own example (AAPL inventory
  FY2023 to FY2024). Plain year-over-year comparisons exist only in the 20
  hand-written comparison items (F-84). Stage 3's wording failing on real data
  is F-83.
- *"Needs two chunks" holds for tagged exact-value spans only.* 29 of the 622
  pairs have a chunk printing both sides' values somewhere untagged for this
  pair (token match, an upper bound: e.g. a 10-Q cash-flow statement printing
  year-ago quarter-end cash under another tag). They are not excluded; a drawn
  one goes on the flagged section of the spot-check sheet.
- Each item is tagged with its kind and gap.
- *Alternatives:* consecutive-year pairs as specified (40 single-table lookups
  under a label that implies multi-hop); a mix of both (blurs what the slice
  measures).

**2. An evidence set is a minimal sufficient set.** A chunk holding both values
would be a set on its own, and the data overrides Stage 3's wording. Under 1
this never arises for auto items: the generator raises if the two sides share a
chunk. The sets are every (a, b) combination of the two sides' gold chunks,
uncapped (as for the 1-3 rule; F-77 unchanged). The rule binds the hand-written
comparisons and the review. *Alternatives:* "both chunk_ids" literally (wrong
whenever one chunk suffices); a cap on sets.

**3. Reference answer: both values with their period labels, plus the
difference; no percent change.** The difference is later minus earlier on the
fact values (Decimal, base units), formatted at the shared printed scale, never
computed from formatted strings. The direction word ("an increase of", "a
decrease of") comes from its sign only; equal values give "a difference of $0
million", not "unchanged". No question form words a direction. A pair whose
sides print at different scales is reported and not generated (F-80
precedent): one such pair in the pool, NVDA income tax, whose later side is the
F-80 key. Equal-value pairs in the pool: 0. *Alternatives:* both values only
(the comparison itself is never checked); add a percent change (no rounding
rule, F-81, and undefined or misleading on zero sides and sign flips). Which
figures numeric accuracy requires is F-81; a difference is printed in no chunk,
F-85.

**4. No reuse.** Neither side among the 160 drawn xbrl_numeric keys, and no key
in more than one pair. *Alternative:* allow reuse (the same figures tested
twice, their errors counted twice).

**Also settled:**
- *Forms:* five per period type in `eval/templates.yaml` (`comparison_forms`),
  using both own-filing period labels; seeded pick; form id in tags; all
  corpus-scoped. No filing-scoped form: pairs two years apart never sit in one
  filing, so it would apply to some pairs and not others.
- *Sampler:* `eval_comparison` config block (seed 20261002, total 40, 5 per
  ticker, gaps, dataset_version, spot_check_n), fixed before the first draw; no
  re-draw. Strata ticker x line item x kind, the same round-robin as `sample`,
  `Shortfall` instead of backfill.
- *Edge values:* no exclusion. Drawn pairs with a side <= 0, a sign flip, or an
  untagged co-occurrence go on the flagged section.
- *Fields:* `question_type = comparison`, `source = xbrl_auto`,
  `reviewed_by_human = false`, `difficulty = medium` (F-76). `xbrl_fact_id` is
  the later period's own-filing fact; the earlier fact is in the manifest by id
  and natural key, and `--verify` checks both. *Alternative:* a list-valued
  `xbrl_fact_id` (changes PRD 8's table).
- *Spot-check:* the seeded 10% (4 of 40) plus the flagged, with each gold
  chunk's text; nothing marked reviewed (OWNER-BLOCKED).
- *Output:* `eval/candidates/`, never a `golden_*` file; byte-identical on re-run.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: tests use real rows; seeding before metric definitions

**Test rows.** A test asserts on a real pool row whenever the pool has an
instance of the case. A modified copy of a real row is allowed only where the
pool has none, and the test says so. The scale-mismatch test now runs on the real
NVDA income-tax pair (first half of fiscal 2025 vs 2027, scales (6,) / (6, 9));
the equal-values test stays a modified copy because the pool has no equal-value
pair (`comparison_supply`: 0). *Alternative:* any mutated copy. Rejected: the
mutated TGT pair asserted a case the pool actually contains, while the real one
went untested, and a mutation can produce a combination the data never shows.

**Ordering.** Next comes LLM seeding (PRD 11.1 Stage 1 and Stage 2, 50 `table` and
40 `synthesis` items): first a measurement (`scripts/seed_supply.py`), then a
proposal with no model-calling code. Hand-written authoring and validation
tooling and the review CLI follow, each logged OWNER-BLOCKED. The
metric-definitions proposal (F-77, F-81, F-13, F-09) comes after these, and no
metric code before it. PRD 14 and the Phase 3 build order put seeding and its
filters before metrics, and nothing in OPEN recorded the 90 `llm_seeded` items.
*Alternative:* definitions first. Rejected: the definitions would be fitted to
the two auto slices alone, and the seeded items' evidence shapes (table vs prose,
one chunk vs several) are what F-77 and F-81 must cover.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: LLM seeding

PRD 11.1 Stage 1 and 2 for the 50 `table` and 40 `synthesis` (`llm_seeded`)
items. Numbers are printed by `python -m scripts.seed_supply`; settings live in
the `eval_seeding` config block. No model call has been made (F-59).

1. **Table count: 50.** Six per ticker plus one each for two tickers picked by
   the seed (`pick_extra`, seed 20261003: AAPL, XOM), written into `per_ticker`
   before the draw. *Alternative:* 48, six per ticker. Rejected: it departs
   from PRD 11.1 for no data reason.
2. **Synthesis is single-chunk**, as Stage 1 writes it ("answerable ONLY from
   it"). No multi-chunk seeding design. PRD 7.1's `synthesis` intent
   (summaries, top-10 lists) has no eval item behind it (F-89), and no report
   may call this slice multi-chunk. *Alternative:* a multi-chunk seeding design.
   Not taken: Stage 1 does not describe one.
3. **Gold chunks excluded.** The 441 chunks already gold for a candidate are not
   seeded (439 table, 2 prose, in 16 strata), for the same reason as the
   comparison no-reuse rule. The manifest records the excluded count per
   stratum. *Alternative:* seed them (statement tables tested twice).
4. **Overdraw 2x, one draw.** `overdraw` is config. The draw order is fixed; the
   first survivors in draw order fill each stratum's slots; a short stratum is a
   `Shortfall`, with no backfill and no second draw. One model call per chunk: an
   unparseable or filtered output is a drop, never a re-generation; only
   transport errors are retried. Raw responses are committed with model id and
   prompt sha, and candidates are rebuilt from that file offline. Surplus
   survivors go to a reserve file in draw order, outside the 90; whether review
   rejections are replaced from it is the owner's call. *Alternatives:* seed
   exactly the target (a shortfall wherever Stage 2 drops); re-generate on a
   drop (selects outputs by the filter); re-draw (a second draw after seeing
   the first).
5. **Extra key-free filters, built** (`eval/generate/seeding.py`, tested on real
   chunk text):
   - *answer in quote / question leaks answer*: numeric answers only, exact
     after `api.numbers` normalization; the figure must be inside the supporting
     quote and not in the question. These drop.
   - No token-overlap score for interpretive answers: it would need a threshold
     with no basis.
   - *same number elsewhere*: a review aid, never evidence; same filer only;
     tagged-span matches listed apart from bare figure matches.
   - *quote elsewhere*: other chunks containing the supporting quote verbatim
     (the prose counterpart), a review aid.
   - Every drop goes to a dropped file with filter and reason; counts per filter
     in the manifest.
   *Alternative:* PRD's four filters only (the review catches the rest).

**Allocation: proportional within ticker, not round-robin.** Slots per
(form, item_code) follow eligible chunk counts, by largest remainder, with a
seeded draw within each stratum. Round-robin over shuffled strata would put ten
synthesis draws per ticker mostly into tiny item codes: 24 of the 35
(form, item_code) prose combinations hold under two chunks per filing (10-K II.6,
III.11, III.13, III.14: 18 chunks across 18 10-Ks; 10-Q II.3, II.4: 36 across 72),
and 10-Q II.6's 24 table chunks would weigh the same as I.1's 5,075. No
item-code exclusion list is needed. Every ticker gets MD&A slots (10-K II.7 or
10-Q I.2) at 1x and 2x for both types. *Alternative:* `sample`'s round-robin.

**Minimum prose length: proposed 40 body tokens (header excluded), not
decided** (`min_body_tokens: null` until then). Content criterion: below 40, a
body holds at most one sentence -- a heading ("Item 2. Properties"), "None.", a
pointer ("See accompanying notes ..."), a table lead-in ("The following table
presents ...") or a single footnote -- none of which can carry an interpretive
question. 1,233 of 12,489 prose chunks fall below. The cut is not clean: just
above it there are still lead-ins and "no material changes to the risk factors"
boilerplate, left to Stage 2 and the review. *Alternative:* no floor (the
allocation would then send slots to headings), or a percentile (not a reason).

**Also settled:**
- The model returns the printed figure only. Code attaches the scale from
  `chunks.unit_scale`; a percent is not scaled; a NULL scale is flagged on the
  sheet, never guessed (e.g. Apple's per-share note prints net income in
  millions with no `unit_scale`).
- Verbatim match normalizes whitespace and table pipes only; no fuzzy ratio.
- No-context filter (needs a model, F-59): numeric answers are compared by code;
  for interpretive ones the no-context answer is printed on the review sheet,
  and no judge drops items before its kappa exists.
- "Unanchored" pronoun, as a testable rule: a deictic phrase pointing at the
  source ("this table", "these periods") always is; a personal pronoun (it, its,
  they, ...) is unless a company name or ticker occurs before it. A question that
  names no company or ticker is dropped by `names_company`.
- 0.92, overdraw, minimum length and seeds live in `eval_seeding`, not in Python.
- **Known bias:** the seeding model is the system's own `tier_large`, so seeded
  questions may favour phrasings that model answers well.
- F-81 extended to seeded numeric answers (percentages, per-share, counts).
- Filter tests use real fixture chunk text (`tests/fixtures/seed_chunks.json`);
  question and answer strings stay inline in the tests, never under `eval/`.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: seeding scale, floor, prompt

**1. F-90: flag, never scale a mixed table.** `attach_scale` applies the chunk's
`unit_scale` only when nothing marks the table as mixed (`mixed_signals`). Mixed
means a scale-exception clause in the chunk text, or a tagged span in the chunk
whose ix scale is not the caption's magnitude (absent counts as 0). In filings
the clause sits in a column header cell ("Three Months Ended ... (In millions,
except per share data)"): 400 scaled table chunks hold one, none in the caption
line. A mixed table gets no scale and a flag, as NULL does. If the answer is
itself a tagged span, its ix scale is printed on the sheet as a review aid, not
applied. No signal covers an untagged per-share, percent or count row, so the
sheet shows printed figure, row label, caption scale and its source for all 50
table items, and scale is confirmed at review for every one. Measured by
`python -m scripts.seed_supply`: "except ... per share" 153, scale-exception
clause 400, tagged span at another ix scale 1,135, union 1,386 of 9,221.
*Alternatives:* the "except ... per share" text match alone (a lower bound:
misses other exceptions and split captions, F-67); a parser fix to keep the
clause (a new `parser_version` and a new freeze); trusting `unit_scale` (per-share
answers off by 10^6).

**2. Minimum prose length: 40 body tokens** (`min_body_tokens: 40`), a
sampling-frame rule fixed before any draw or model output, not a metric, and not
revisited after model output: drops clustering above the cut are reported, not
tuned away. The manifest records floor exclusions per stratum beside gold
exclusions. A report of the synthesis slice states its population: prose of at
least 40 body tokens, 11,254 of 12,487 eligible. XOM loses 141 of 463 (30%):
mostly one-line table titles emitted as their own prose chunk just before the
table (F-91). The floor stays. *Alternatives:* no floor (slots on headings and
pointers); a percentile (not a reason).

**3. Prompt: figures exactly as printed, with parentheses, `$` and `%`.** The
`answer_in_quote` filter stays exact: no absolute-value matching and no
re-generation. A drop where the answer's absolute value is in the quote with the
other sign is marked `sign_only`, counted apart in the manifest, so a loss of
outflow lines shows. A parenthesized answer is stored as printed and flagged;
code does not decide whether "(2,815)" is -2,815 or an outflow of 2,815 (F-87);
the reference answer's sign wording is set at review; scoring stays with F-81.
The prompt (`eval/generate/prompts/seed_v1.txt`, sha in the manifest) holds PRD
Stage 1's instruction, the format `parse_response` expects, and four
requirements: name the company, state the fiscal period, quote verbatim, copy
figures as printed. No example question or answer from the corpus. *Which
question becomes the item:* a table chunk gives its factual question, a prose
chunk its interpretive one; the other stays in the raw responses file and never
fills a slot. *Alternatives:* magnitude matching (hides sign errors); letting the
model normalize figures (the filter could no longer check them).
