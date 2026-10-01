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
