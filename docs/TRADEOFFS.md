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
4. **Overdraw 2x, one draw** (amended: the overdraw applies per stratum, see
   "seeding overdraw is per stratum (draw_v2)" below). `overdraw` is config. The draw order is fixed; the
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

---

## 2026-10-01 — OWNER DECISION - Max subscription as dev generator

Decided by the developer (owner), not the builder or the supervisor. Until an
API key exists, generation runs on the developer's Claude Max subscription
through the `claude` CLI. This partly unblocks F-59.

- **Switch:** `generation.backend: claude_cli | anthropic_api` in
  `api/config.yaml`, default `claude_cli`. The `anthropic_api` path is
  unchanged (`generate_api`); CI and every published number use it later.
- **The call** (`api/generate/claude_cli.py`, subprocess only, no new
  dependency): `claude -p <prompt> --model <tier model id> --system-prompt
  <generation.cli_system_prompt> --tools "" --strict-mcp-config
  --disable-slash-commands --setting-sources "" --no-session-persistence
  --output-format json`.
  - Run with cwd a fresh empty temp directory, never the repo, or Claude Code
    loads CLAUDE.md/AGENTS.md into the generator's context.
  - `ANTHROPIC_API_KEY` removed from the child environment: the invalid shell key
    would override the Max login (401).
  - Never `--bare`: it accepts only an API key, never the Max login.
  - JSON: `result` is the text; `is_error` true raises; `modelUsage` keys give
    the model actually served; `usage` gives tokens.
- **Limits:**
  - *Known contamination:* Claude Code still injects an agent identity line, the
    working directory, today's date and the account email into the context.
  - No temperature control (F-60 unchanged) and no max-tokens flag: the
    recorded response reports `maxOutputTokens: 32000`, and `max_tokens: 1024`
    applies to `anthropic_api` only. The CLI enabled extended thinking on its own
    (34 thinking tokens in the recorded response), counted in `output_tokens`.
  - The system prompt (`cli_system_prompt`, "You are a helpful assistant.")
    replaces Claude Code's own; the `anthropic_api` path sends none, so the two
    backends do not send identical requests.
  - Latency about 8 s per call (observed by the owner; the smoke run below took
    14.8 s end to end, model load and retrieval included).
- **Dev-only labelling:** every answer records its backend (`Answer.backend`,
  printed by the baseline), and every eval run must record it in its config
  snapshot. `claude_cli` results are development numbers: never in the README,
  never a CI baseline (`eval/baselines/*`), never compared against
  `anthropic_api` runs. Final and published runs are re-run on `anthropic_api`.
- **Seeding** (`eval/generate/seeding.py`) may use the same backend. Seeding and
  generating with one model family is the bias F-14 describes.
- **Serving (2026-10-02, OWNER DECISION, same scope).** Until a key exists the
  local API answers on `claude_cli`. Every `/query` response carries `backend`,
  `model_served` and `development: true`; the Answer screen shows a persistent
  banner from that response field, never from config; latency and cost on screen
  are the response's own and labelled dev. No screenshot of a `claude_cli` answer
  goes into the README; the README's screenshot slots are OWNER-BLOCKED under
  F-59. The eval dashboard renders only from committed run files: model-free
  retrieval runs, the gate's per-metric table (pass / fail / pending with each
  pending reason) and the owner-blocked list from OPEN; development runs appear
  only as run ids with the banner "development run on `claude_cli`, not a
  result", linked to their files, with no metric value; any run whose meta has
  `development_run: true` is excluded from every chart and table by code, with a
  test. A gated run appears by the same rule when it exists.
- *Alternatives (owner's):* wait for an API key (Phase 2 exit and all model-based
  Phase 3 work stay blocked); `--bare` with the shell key (rejected: 401, and
  `--bare` cannot use the Max login).

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: seeding overdraw is per stratum (draw_v2)

Decided by the supervisor; recorded here for the owner. Amends item 4 of "LLM
seeding".

- **Rule:** each slotted stratum draws `overdraw` x its 1x slots (`draw_target`);
  a stratum with no 1x slot draws nothing. The 1x allocation is unchanged, so the
  composition of the 90 is the same; only where the spares sit moves.
- **Why:** slots fill per stratum, so a spare helps only in its own stratum. In
  `draw_v1` (per-ticker 2x by largest remainder), read from its manifest: 16 of
  the 180 draws (6 table, 10 synthesis) sat in strata with zero 1x slots and could
  only reach the reserve, while 13 slotted strata (2 table, 11 synthesis) had no
  spare, so one Stage 2 drop there would be a shortfall.
- **Mechanics:** the per-stratum shuffle seed is kept, so each stratum's order is
  unchanged and only the cut length moves (checked: all 57 `draw_v2` strata agree
  with `draw_v1` on their common prefix). Totals stay 100 and 80. A stratum with
  fewer eligible chunks than its target draws what exists and is listed (none).
- **Files:** `eval/seeding/draw_v2.json` (sha256 1c23e9f6...). `draw_v1.json`
  (sha256 25e1bfc1d21eeef0353d281e19ebeb9ccaa4830ac69634b48bc791e37176b147,
  commit 8e6854d) is removed in the same commit so nothing can read it.
  `scripts.seed_supply` prints the same rule, so the two scripts never print
  different allocations.
- **This is the only re-draw.** It is legitimate because no seeding output
  exists. After the first call on a drawn chunk the draw is frozen. A stratum
  where every draw drops is a shortfall against PRD 11.1's 50/40, reported per
  stratum and logged as a finding: no third draw, no overdraw change, no
  backfill, and the surviving candidates are still written.

*Alternatives:*
- *Keep per-ticker 2x* (draw_v1): 16 draws unusable for any slot, 13 slotted
  strata without a spare.
- *Raise the overdraw:* more calls, and per-ticker allocation still guarantees
  no spare per stratum.
- *Backfill across strata after Stage 2:* the composition would then depend on
  model output.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: the seeding runner

Implements item 4 of "LLM seeding" (as amended for draw_v2).

- `python -m scripts.seed_run` makes no call by default (status only). `--run`
  must be given explicitly; `--verify CHUNK` asserts the chunk is in neither
  `draw_v2` nor gold and writes to `eval/seeding/verify_v1.jsonl`, which nothing
  that builds candidates reads.
- One call per chunk on `tier_large`. Each record is appended and fsynced as it
  arrives; a chunk with any recorded response, an error included, is never
  called again. Only transport errors (timeout, exit without output) are retried,
  3 attempts; an `is_error` result is recorded and becomes a drop (superseded:
  a call with no response halts the run and leaves the chunk pending, see "seeding
  runner halts on a call with no response" below).
- Each raw record carries backend, requested and served model, prompt sha, draw
  sha, usage (including the CLI's cache-read and cache-creation tokens, which its
  `input_tokens` excludes) and CLI version. Before writing, any field holding an
  email address or the home path is dropped and named in `scrubbed_fields`.
- The runner refuses if the prompt file's sha differs from the draw manifest's.
- `outcome` rebuilds Stage 2's key-free result offline from a record. A
  parenthesized figure keeps its scaled magnitude and a null value: the sign is
  set at review (F-87), not by `parse_number`'s accounting convention.

*Alternatives:* write records at the end of the run (a crash loses them); retry
`is_error` results (a re-generation); record only `input_tokens` (understates
input on the CLI, which reported 2 for the verification call).

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: seeding runner halts on a call with no response; rebuild before the run

Decided by the supervisor before any drawn chunk was called; recorded for the
owner. Amends "the seeding runner".

1. **A call that returns no model output does not consume the chunk.** An
   `is_error` result, non-JSON output, a missing `modelUsage`, or a transport
   failure after 3 attempts goes to `eval/seeding/call_errors_v1.jsonl` (one
   record per halt, with every attempt's error and UTC time); the chunk stays
   pending and the run exits 1. `raw_v1.jsonl` holds only records with a
   response. A chunk that has halted 3 runs stops the run (exit 2) without a
   call: it is reported, not skipped. Not a re-generation: nothing is selected
   on model output, and every failed attempt stays on file. Why: a Max usage
   limit, a 429/529 or an expired login at call N would otherwise turn every
   remaining chunk into a `call_error` drop within seconds, and there is no
   third draw. Tested with a patched `complete` (`tests/unit/test_seed_run.py`).
2. **Scrub redacts in place.** An email address or the home path is replaced
   (`[redacted email]`, `[redacted home]`) and the field named in
   `scrubbed_fields`; the field is kept, so a response still parses. Every record
   carries `called_at` (UTC).
3. **The offline rebuild is built before the run** (`eval/generate/seed_build.py`,
   `scripts/seed_build.py`), a pure function of the raw file, the draw and the
   chunks, so parse, filter and slot code cannot be fitted to the output. Stage 2
   order: key-free filters, no-context, near-duplicate, slot fill per stratum in
   draw order, reserve. It writes the dropped file (filter, reason, `sign_only`)
   and prints key-free survivors per stratum with counts per filter, and refuses
   to write candidates or the reserve while any survivor lacks a no-context
   record; no provisional candidates file. The verification record never enters
   it. After the run, any change to parse, filter or slot code gets an entry here
   with counts before and after; a low yield is a finding, not a reason to loosen
   a filter. The no-context runner comes after the run under the same one-call
   rule; its numeric match rule is proposed before any no-context call.
4. **Quarter label on a multi-period span (F-92), rule fixed before the run.** A
   kept question is flagged when it carries a quarter label (Q1-Q4, "first ...
   fourth quarter") and also states a span longer than one quarter (6/9/12
   months, 16 to 53 weeks, first half, year to date). The rebuild counts the
   flags; the review sheet prints the chunk header beside each question. No drop
   and no prompt change on one observation: the prompt stays frozen.

*Alternatives:*
- *An `is_error` becomes a drop* (as first built): one outage drains the draw.
- *A circuit breaker that still spends one chunk per incident:* each incident
  costs a chunk with no third draw to replace it.
- *Rebuild after the run:* the code could be fitted to the output.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: seeding run protocol

Decided by the supervisor before any drawn call; recorded for the owner.

- **Wrong model halts.** If the requested `tier_large` model is not among the
  `modelUsage` keys, the attempt (kind `wrong_model`, response text kept) goes to
  `call_errors_v1.jsonl` and the chunk stays pending. *Alternatives:*
  record-and-drop (a silent fallback drains the draw); record-and-keep (mixed
  models under one manifest).
- **Malformed or empty result halts.** A non-object document, a missing or
  non-integer `usage`, or a missing, non-string or empty `result` raises
  `CliError` (previously the first three escaped as `KeyError` and never reached
  the errors file, and an empty `result` entered raw and spent the chunk).
  *Alternative:* a parse drop (an outage would spend chunks).
- **JSONL reads split on "\n" only**: `splitlines()` also splits on U+2028,
  U+2029 and U+0085, which `ensure_ascii=False` writes raw.
- **The rebuild refuses** a duplicate `chunk_id`, a record for a chunk not in the
  draw, or a `draw_sha256`/`prompt_sha256` that differs from the draw file; it
  prints every slotted stratum (survivors / slots / drawn / pending),
  `model_served` counts, and the records whose response was redacted (a redacted
  quote fails `quote_verbatim` and must not read as a filter drop).
- **Prose verification outside the draw** before any drawn call: the lowest
  `chunk_id` in the largest synthesis stratum (by `eligible`) in neither
  `draw_v2` nor gold. *Alternative:* first exercising prose on drawn chunks.
- **Batches**: one process at a time, `--run --limit 5`, then `seed_build`, then
  batches of 20; `raw_v1.jsonl` and `call_errors_v1.jsonl` committed after each
  batch, never edited. From the first drawn call: no edits to the prompt,
  `seeding.py`, `outcome`, `seed_build.py` or `eval_seeding`. Exit 1: read the
  error record first; for a usage or rate limit wait for the reset (each re-run
  spends one of the chunk's 3 halts). Exit 2, a traceback, or a raw response that
  is CLI/API error text: stop and report. Filter drops, parse drops of real model
  output and shortfalls are findings, not stop conditions. *Alternative:* one
  180-call process (a tool kill loses a call unrecorded).

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: no-context filter rule

Proposed by the builder, adopted by the supervisor with one change (tolerance).

- **Rule** (`eval/generate/no_context.py`): a table item is answerable without its
  chunk, and dropped, when any figure in the no-context answer, normalized by its
  own scale word (thousand, million, billion, trillion), is within **0.5%** of the
  item's value in magnitude. Percentages, per-share figures and counts compare as
  plain values. Within 5% but not 0.5% is a near-match: kept and flagged for the
  review sheet. "unknown", or an answer with no figure, is not a match.
- **Why 0.5%:** PRD 11.1 Stage 2 drops an item if the model "answers correctly"
  without the chunk, and the PRD's own definition of two figures being the same
  number is the 0.5% tolerance of 6.5.4 and 7.5. An answer the PRD would accept as
  the same figure at runtime is a correct answer here; exact-only would keep
  items the model knows to the PRD's tolerance, which is the leak the filter
  exists to stop. Shortfall pressure (F-95) is not a reason to keep them.
  Example: "$1.4 billion" against 1,434 million is 2.4% off: a near-match, not a
  drop.
- **Scale unknown or mixed table:** printed values are compared with the same
  tolerance; a match drops and is filtered as `no_context:digits_only`. An item
  is not kept because its scale is unresolved.
- **Sign:** magnitude only (F-87); a magnitude match whose sign disagrees with
  the item's printed sign still drops and is counted as `sign_only`.
- **Interpretive items:** code judges nothing; the no-context answer is printed
  beside the item on the review sheet (F-96, OWNER-BLOCKED).
- **Calls:** one per key-free survivor (158), in draw order, on `tier_large`; the
  prompt is the question plus "Answer from your own knowledge; if you do not
  know, say unknown." (`eval/generate/prompts/no_context_v1.txt`, sha in each
  record); raw to `eval/seeding/no_context_v1.jsonl`, errors to
  `no_context_errors_v1.jsonl`; same halt, resume and batch-and-commit rules as
  seeding. From the first call: no edits to the prompt, the rule or the
  extractor.
- **Rebuild:** `seed_build`'s no-context stage (added before the first
  no-context call; the key-free code and its output are unchanged, checked by
  diff) refuses duplicate records, records for non-survivors and a different
  prompt sha; drops are appended to `dropped_v1.jsonl`.
- **Known bias (F-14):** the same model family seeds the questions and answers
  them without context, so the filter measures what this model knows, not what
  any model knows.

*Alternatives:* exact match (keeps items the model knows to the PRD's own
tolerance); matching with sign (treats a correct magnitude as wrong over
accounting presentation, F-87); a judge model for numbers (no kappa exists).

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: seeded item fields

Proposed by the builder, approved by the supervisor with changes; recorded for
the owner. `eval/generate/seed_items.py`, written by `python -m
scripts.seed_build` from the committed raw files.

- `question_type` `table` / `synthesis`; `difficulty` `easy` for table (PRD
  11.1's item example is literally `question_type: "table", difficulty:
  "easy"`, the only rule the PRD gives) and `medium` for synthesis (no rule; F-76).
- `reference_answer`: the model's answer string, unchanged; no rewording of gold.
  Scale is not written into the answer; it is a tag.
- `gold_evidence_sets = [[seed chunk]]`, `gold_accessions = [its accession]`,
  `expected_abstain = false`, `xbrl_fact_id = null`, `reviewed_by_human = false`,
  `source = llm_seeded`.
- `tags`: ticker, form, item_code, `kind:factual|interpretive`; table items
  `unit_scale_<caption scale>` or `unit_scale_unknown` (NULL or mixed scale, and
  a percent answer, confirmed at review, F-90); `quarter_label_on_span` (F-92),
  `no_context:near_match`, `parenthesized`, `seed_backend:claude_cli` and
  `seed_model:claude-sonnet-5-5` (F-59: development-grade, visible to every
  report).
- The supporting quote, the resolved value and scale, the no-context answer and
  its extracted figures (all, and those within 5%), and the stratum go in the
  manifest (`eval/candidates/llm_seeded_manifest.json`), not the item.
- `dataset_version`: `llm_seeded_candidates_v1` (config `eval_seeded_items`).
  Accepted by the supervisor. These candidate versions are pre-freeze labels: at
  PRD 11.1 Stage 6 the frozen dataset gets a single `golden_v1`.
  The instruction was "the same as the existing 200 candidates", but those carry
  two values (`xbrl_candidates_v1`, `comparison_candidates_v1`); this follows
  their shared pattern. `eval_seeding` is frozen, so the value lives in a new
  block.
- The 53 reserve survivors are in `eval/seeding/reserve_v1.json`, in draw order,
  headed "NOT AN EVAL ARTEFACT"; nothing there enters the candidates except
  through a recorded rebuild.
- The review sheet (`eval/candidates/llm_seeded_review.md`) covers all 83 (PRD
  11.1 Stage 5: 100% review of everything not XBRL-derived): question, answer,
  supporting quote, chunk header, no-context answer, the figures extracted from
  it and those within 5%, flags, tags; for table items, the other chunks of the
  same filing printing the item's figure (by magnitude) as candidate alternative
  evidence for the owner, never written to gold. A last section lists the 18
  no-context drops with the figure that matched.
- The near-duplicate comparison set is the 200 non-seeded candidates; the
  seeded file is excluded so that a rebuild compares against the same set.

*Alternatives:* difficulty by a heuristic (no PRD rule, nothing reads it);
reference answers normalized to base units (rewords gold, F-81 settles scoring);
candidate alternatives added to gold automatically (unreviewed evidence
inflates recall).

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: nDCG over alternative evidence sets (F-77) -- decided

Status: proposed by the builder, adopted by the supervisor as written. F-77
resolves when the code and its tests exist (`eval/metrics/retrieval.py`).

**Definition.** nDCG@k is computed per evidence set and the item takes the best:

    nDCG@k(item) = max over es in gold_evidence_sets of DCG_es@k / IDCG_es@k
    DCG_es@k  = sum over ranks i <= k of rel_i / log2(i + 1),
                rel_i = 1 if retrieved[i] is in es and not already counted, else 0
    IDCG_es@k = sum over i = 1 .. min(|es|, k) of 1 / log2(i + 1)

This is the reading PRD 11.2 already uses for its neighbours: retrieval
"succeeds if any one [set] is fully covered" (Sufficiency@k) and Recall@k is
`max_es` per-set coverage. A single-chunk set found at rank r scores
1/log2(r+1) whatever the number of alternatives: the 8-alternative item of F-77
with one gold chunk at rank 1 scores 1.0, not 0.25. A two-chunk comparison set
with one chunk at rank 1 and the other missing scores 1/(1 + 1/log2 3) = 0.61;
both at ranks 1 and 2 score 1.0. MRR, Precision@k and context precision stay as
PRD 11.2 writes them (first chunk of any set; union for precision).

*Alternatives:*
- *Union as relevant* (rel_i = 1 for any gold chunk, IDCG over the union): an
  item scores worse the more alternative sets its gold lists -- 0.25 for the F-77
  example -- so the metric falls with the completeness of gold, which review is
  meant to raise. Rejected.
- *Graded relevance by set size* (rel = 1/|es|): ad hoc weights with no PRD
  basis.
- *Best set by rank of completion* (score only fully covered sets): duplicates
  Sufficiency@k and gives two-chunk sets no partial credit.

Gold is not shaped around the metric: the evidence-set counts in F-77 stand.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: numeric accuracy normalization (F-81) -- decided

Status: proposed by the builder, adopted by the supervisor with changes. F-81
resolves when the code and its tests exist (`eval/metrics/numeric.py`).

**Scope.** Items whose reference answer is a figure: `xbrl_numeric` (160),
`comparison` (40), `llm_seeded` table items (47, `kind:factual`). Synthesis and
abstain items are outside it.

**Figures from the answer.** From the generator's claim `figure` objects first
(PRD 7.4 makes them required on numeric claims; value scaled by its `unit`);
free-text extraction is the fallback, and every use of it is counted. The
free-text extractor is new code, not the frozen no-context one: it does not read
figures out of period labels, dates, form names or item numbers ("Q2", "FY2026",
"10-Q", "March 28, 2026", "Item 7"), so F-97's defect cannot exist in the
scorer; tested on those strings before any run. Each figure is scaled by its own
scale word; percentages and per-share figures are plain values.

**Gated figure: exact at the reference's printed precision, magnitude only.**
The answer's figure is rounded to the reference's last printed digit (in base
units) and must equal it: "$7.286 billion" and "$7,286.4 million" match a
"$7,286 million" reference; "$7.3 billion" does not. Magnitude only: "a benefit
of $28 million", "(28)" and "-$28 million" all match a "-$28 million" reference
(sign presentation differs by filing, F-87). Reported beside it, never gated:
0.5%-tolerant accuracy, and sign agreement over answers that state a sign
explicitly (minus or parentheses). The asymmetry with the no-context filter is
deliberate: there 0.5% drops items, here exactness withholds credit; both err
against inflating the score.

**Which figure.** The gated rule is "any figure matches". Reported beside it:
the strict variant, where only the answer's first claim figure (or first
extracted figure) is compared, and the figure count per answer. If the two
diverge materially on a run, that is a finding, not a reason to pick the higher.

**Zero.** "none", "nil", "zero" or a dash count as 0 only when the reference is 0
and the item was answered, not abstained (F-09).

**Comparison items:** correct only if both values and the difference match;
values-only accuracy is reported separately. A percent change earns nothing.

**Scale unknown** (`unit_scale_unknown`, 10 seeded items): out of the
denominator, and the excluded count is printed on every report that shows the
metric. Parenthesized seeded answers ("(1,434)") match by magnitude.

**Abstained numeric items** stay in the denominator as incorrect, and the
abstention count among numeric items is reported beside the metric. F-09's
answered-only rule is for faithfulness_pre, where the unit is a claim; it does
not transfer to an item-level accuracy, where excluding abstentions would reward
abstaining on hard numbers. The figure-count distribution is reported too.

*Alternatives:* 0.5% as the gated number (credits rounded answers PRD 11.2 calls
wrong); signed match (scores a correct magnitude as wrong over presentation,
F-87); first figure only as the gated rule (brittle to answers that restate the
question's period or context first); comparison by difference only (credits a
right difference from wrong values); reusing the no-context extractor (carries
F-97 into scoring).

*2026-10-02, OWNER DECISION, period accuracy (F-126).* The gated period accuracy
keeps figure claims whose period cannot be checked against XBRL (`period_ok`
null) in the denominator as not correct, as built. Beside it the report prints
the rate over checkable claims only and the count of uncheckable ones. Dropping
them would let a system raise the number by citing periods we cannot check.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: retrieval metrics are measured post-fusion, pre-rerank (F-13)

As OPEN's recommendation for F-13 already states. Retrieval metrics
(Sufficiency@k, Recall@k, MRR, nDCG@k, Precision@k) are computed on the ordered
post-fusion, pre-rerank list, stored per item as `retrieved` (PRD 8's
`eval_results.retrieved`). Reranker quality is measured separately as
`sufficiency@k_post_rerank` on the post-rerank list, stored beside it. Until a
reranker exists (Phase 4) the stored list is the dense top-k of the baseline and
the post-rerank field is empty. Why: a reranker that drops gold chunks would
otherwise show up as a retrieval regression, and one that only reorders would
hide recall lost at fusion; measuring at one fixed point keeps the two apart.
*Alternatives:* post-rerank only (mixes reranker and retriever errors);
whatever list the generator receives (moves with `top_k` and the score floor).

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: the eval runner (built, not run)

`eval/runner.py` (pure scoring and report) and `scripts/eval_run.py`.

- No retrieval or model call without `--run`; the default prints the plan.
- `--baseline-out` calls `refuse_dev_baseline` before any work: a `claude_cli`
  run cannot write `eval/baselines/*` (F-59).
- Every report starts with the backend and the requested model; a `claude_cli`
  run carries a "DEVELOPMENT RUN" banner. The models actually served are counted
  per run and stored per item (`model_served`).
- Metrics per `source` column (`xbrl_auto`, `llm_seeded`, `handwritten`) and
  aggregate (PRD 11.2). Retrieval metrics at `eval_run.k` (10) on the stored
  pre-rerank list (F-13; today the dense top-k, depth `retrieve_depth`); the
  generator gets `baseline.top_k` of it. Numeric accuracy prints its excluded
  `unit_scale_unknown` count and the reported variants on every report.
- The Phase 2 generator returns free text, no claims and no verdict: every
  result is `PASS` with `claims: []`, so numeric accuracy uses the counted
  free-text fallback until PRD 7.4's structured output exists.
- Run output (amended before the first run): `eval/runs/<run_id>.meta.json`
  (backend, models, freeze versions, dataset shas, item order),
  `<run_id>.results.jsonl` (one record per item, appended and fsynced as it
  completes), `<run_id>.errors.jsonl`, and `<run_id>.json` (the report). `--resume
  RUN_ID` skips recorded items after checking backend, datasets and freeze
  versions are unchanged; a call with no usable response (or a model other than
  the requested one) halts with exit 1, the item unrecorded. Run files are
  committed, not git-ignored; the code refuses to promote a dev run to a
  baseline.
- PARTIAL counts as answered in the 2x2 (F-21, entry below).
- Retrieval-only runs (`python -m scripts.retrieval_run`, no model call) are
  written to `eval/runs/<run_id>.retrieval.json`, report and per-item lists in
  one file, beside the eval runs' `<run_id>.json` / `.meta.json` /
  `.results.jsonl`. Both kinds are committed; every number in a finding comes
  from a committed run file. The other run kinds in `eval/runs/` (added
  2026-10-02): rerank runs `<run_id>.rerank.json` (`scripts.rerank_run`);
  filter runs `<run_id>.filter.json` (report, filters and both lists per item)
  with the raw router responses in `<run_id>.router.jsonl` and any failed calls
  in `<run_id>.router_errors.jsonl` (`scripts.filter_run`; e.g. 8b6bcc14f274). Smoke runs
  `<run_id>.smoke.json` (`scripts.eval_run --smoke SEED`): pipeline checks, not
  measurements; they store which records broke and no metric. Derived files, never a
  new run id: `<run_id>.rescore-<threshold>.json` (NLI re-score, F-125) and
  `<run_id>.reverify-<tag>.json` (model-free checks re-run over stored claims;
  e.g. a4e39a65c2c8.reverify-f128-f129-f130).

*Alternatives:* store results in PRD 8's `eval_runs`/`eval_results` tables (no
migration exists yet; JSON keeps the run reproducible without one); one column
for all sources (PRD 11.2 forbids it).

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: PARTIAL counts as answered in the abstention 2x2 (F-21)

Decided by the supervisor. A PARTIAL verdict (PRD 7.5: supported claims only,
with a partial-verification notice) lands in the "answered" column: on an
unanswerable item it is a failure to abstain (a false answer), on an answerable
one the user received an answer (not over-abstention). Its rate is reported as
its own row. The conservative placement is the one that can score against the
system. `eval/metrics/abstention.py` implements it, tested. The API response
shape part of F-21 stays open for Phase 4.

*Alternatives:* PARTIAL as abstained (an unanswerable item answered partially
would score as correct abstention); a third column (the 2x2 stops being one, and
false-answer rate stops counting partial answers).

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: review decisions are an overlay

`eval/review_decisions.py` and `scripts/review.py`. The owner fills a YAML worksheet made
from a review sheet (accept / reject / edit_evidence, with every alternative
evidence set for an edit); `import` validates every entry (decision value,
chunks in the frozen corpus, a reviewer name) and appends all or nothing to
`eval/review/decisions_v1.jsonl`, the only thing that sets
`reviewed_by_human = true`. `effective` applies the decisions as an overlay:
copies only, rejected items left out, edited evidence with accessions
recomputed; the latest decision for an item wins and earlier ones stay on file.
No candidates file is edited; PRD 11.1 Stage 6's freeze will read the overlay.

*Alternatives:* edit the candidates in place (no record of who decided what, and
a rebuild would overwrite it); decisions typed into the markdown sheets (the
sheets are regenerated by their scripts).

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: the LLM judge and its validation set

`eval/judge/` (`rubrics.py`, `judge.py`, `agreement.py`, PRD 13.4) and
`scripts/judge.py`.

- Rubric: answer correctness 1-5 with a written anchor per level (PRD 11.3); a
  null reference means the system should abstain (declining scores 5).
- Structured output: strict JSON `{"score", "rationale"}`; anything else is a
  parse error, recorded, never re-asked. No temperature can be set on either
  backend (F-60), so PRD 11.3's `temperature=0` is not met.
- The judge calls `complete()` with `eval_judge.tier` (tier_large), the same
  backend abstraction as generation, and stamps backend, served model, family
  and whether the family is the generator's. On `claude_cli` the judge and the
  generator are both Claude: same-family judging, which PRD 11.3 forbids for
  published numbers (F-14). The stamp makes it visible; it does not fix it.
- Validation set: 50 (item, answer) pairs drawn by seed (`eval_judge.label_seed`)
  from dev run 19693d4aa874's answers, proportional by source (largest
  remainder): 35 xbrl_auto, 15 llm_seeded. The owner labels before any judge
  score exists; `run` and `kappa` refuse until all 50 labels are in.
- Agreement: unweighted Cohen's kappa over the five categories, as PRD 11.3
  names it; < 0.6 is reported as unreliable. Undefined (None) when chance
  agreement is 1.

*Alternatives:* weighted kappa (the PRD names Cohen's kappa; a weighted value
can be added beside it later); a uniform draw over all 283 (could leave the
seeded slice with few pairs); judging the dev run before labels exist (the
owner's labels could be anchored on the judge's scores).

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: hybrid retrieval as first built (Phase 4)

- Dense: unchanged `dense_top_k`, except `hnsw.ef_search` is raised to k when k
  exceeds pgvector's default 40, because HNSW returns at most `ef_search` rows;
  at k = 10 (the Phase 2 baseline) nothing changes.
- Sparse: Postgres full-text over `chunks.tsv` ranked by `ts_rank_cd`, as PRD
  6.4's "Postgres tsvector + ts_rank_cd" option. The query ORs the question's
  lexemes: an AND of every term of a natural-language question rarely matches a
  chunk.
- Fusion: weighted RRF exactly as PRD 7.2 (k = 60, weights 1.0 / 1.0), dense and
  sparse top-50 each (`retrieval` config block, Appendix A values); ties to the
  better best rank, then the smaller chunk id. The fused list is the pre-rerank
  list on which retrieval metrics are measured (F-13).
- Measured by `python -m scripts.retrieval_run` (no model call), against the
  stored dense lists of the dev runs.

*Alternatives:* `websearch_to_tsquery` (AND semantics; most questions match
nothing); a Python BM25 over all chunks (a new dependency, not asked for yet);
OpenSearch BM25 (PRD 6.4's other option; a second service).

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: Okapi BM25 for the sparse branch (F-108)

Decided by the supervisor on the F-108 measurement. PRD 6.4 calls Postgres FTS
"adequate" and PRD 14 says "BM25"; the data decided.

- `api/query/bm25.py`: self-written Okapi BM25, no new dependency. k1 = 1.2, b =
  0.75 (`retrieval.sparse`), standard values, not tuned on the candidates; any
  tuning is PRD 11.7's ablation, later, and only on reviewed items. IDF
  `ln(1 + (N - df + 0.5) / (df + 0.5))`, never negative.
- Tokenizer (one tested pure function): lowercase; a figure with thousands
  separators is one token without commas ("7,286" -> "7286"); hyphen-joined
  alphanumeric runs stay whole ("10-q", "8-k", "non-gaap"); otherwise
  alphanumeric runs ("7a", "fy2025", "aapl"). No stemming: financial line items
  are matched literally, and a stemmer would be a dependency to pin.
- Indexed text: the chunk's stored `text`, context header included, so tickers,
  Item codes and period labels match.
- Index cached under `data/cache/`, keyed on `chunker_version` plus a hash of
  every chunk's text; rebuilt when either (or k1, b) changes; `Index.check`
  refuses an index used against another key. The run report records the sparse
  backend and the index key.
- Postgres FTS (`ts_rank_cd`) stays as the Phase 2 artifact, selectable as
  `retrieval.sparse.backend: postgres_fts`.

Measured (retrieval-only, Sufficiency@10, xbrl_auto / llm_seeded / aggregate):
dense 0.290 / 0.699 / 0.410 (at `ef_search` 100); BM25 0.175 / 0.892 / 0.385;
hybrid 0.365 / 0.892 / 0.519 (run 01019ff395ec).

*Alternatives:*
- *Postgres FTS, `ts_rank_cd` over OR-ed lexemes* (rejected; run 188304ccaf94):
  sparse 0.025 / 0.241 / 0.088, and fusion lowered dense, hybrid 0.215 / 0.687 /
  0.353 against dense 0.290 / 0.675 / 0.403. No inverse document frequency.
- *A Postgres BM25 extension* (rejected): new infrastructure and a Docker image
  change, and nothing in the PRD asks for it.

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: `hnsw.ef_search` pinned at 100 (F-109)

Decided by the supervisor. `retrieval.hnsw_ef_search: 100`, at least `k_dense`
(50), chosen for recall, not for any score; `dense_top_k` sets it before every
dense query and refuses an `ef_search` below k; eval runs record it in their
meta beside `retrieve_depth` and `k_dense`, retrieval-only runs in their
report. Measured once (`python -m scripts.exact_nn_check`): exact nearest
neighbours by sequential scan over all 22,354 chunk embeddings against HNSW at
100 for the 283 candidate questions: 0 top-10 lists differ. Not changed in
response to any metric. *Alternatives:* pgvector's default 40 (HNSW returned a
different top-10 on 10 of 283 items between 40 and 50, F-109); exact search
always (fine at this size; the PRD specifies HNSW).

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: cross-encoder reranking as first built (PRD 7.3)

- `api/query/rerank.py`: `BAAI/bge-reranker-base` pinned at revision
  2cfc18c9415c912f9d8155881c133215df768a70 (config `rerank`), over the fused
  top-50 in one forward pass; scores are the logit through a sigmoid (0-1), so
  the floor is on PRD 7.3's "normalized" scale. Output top-8, top-10 for
  synthesis items (PRD 7.3; there is no `lookup` type, F-76). Ties to the
  smaller chunk id.
- Score floor 0.30 (PRD 7.3's "~0.3 normalized"), `floor_calibration: pending`:
  it is calibrated only on reviewed items (F-104, F-112), never on the
  candidates; an item whose every chunk falls below it abstains.
- Timeout 800 ms with fall-through to RRF order, as PRD 7.3. Not applied in the
  offline measurement, which records the latency instead (F-111).
- Measured by `python -m scripts.rerank_run <retrieval run>` on the stored
  pre-rerank lists, reported as post-rerank sufficiency at the item's top-n
  beside pre-rerank sufficiency at 8 and 10 (F-13). Run files:
  `eval/runs/<run_id>.rerank.json`.

*Alternatives:* `cross-encoder/ms-marco-MiniLM-L-6-v2` (PRD 7.3's other option;
smaller and faster, not measured); raw logits for the floor (no fixed scale for
"0.3").

---

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: reranker chosen to meet the 800 ms timeout (F-111)

Decided by the supervisor's rule: the 800 ms timeout is PRD 7.3's spec and stays;
the fix is within PRD 7.3's two named models, chosen on measured latency, never
on sufficiency; if both met it, bge-base would be kept. Every rerank run records
device, torch version and machine (CPU, GPU, RAM).

Measured on the 283 candidates' fused lists (retrieval run 01019ff395ec), Apple
M1 Pro (16 GPU cores), 16 GB, torch 2.14.1, one batched pass of 50 pairs, warm-up
excluded:

| model | device | p50 | p95 | over 800 ms | run |
|---|---|---|---|---|---|
| bge-reranker-base | mps | 1.406 s | 1.802 s | 283 | dd372192a070 |
| ms-marco-MiniLM-L-6-v2 | cpu | 0.756 s | 0.834 s | 34 | 45e3ed5c8f13 |
| ms-marco-MiniLM-L-6-v2 | mps | 0.259 s | 0.272 s | 0 | 46523deda1c0 |

Adopted: `cross-encoder/ms-marco-MiniLM-L-6-v2` @233902d25c44 on `mps`, the only
combination under the timeout. Run 4aef651ade44, first reported as CPU, was in
fact on `mps`: sentence-transformers places a CrossEncoder on `mps` when no
device is given (checked), so its latency is bge-base on the GPU. Its quality
numbers stand.

The adopted model reranks worse than the order it receives (F-113): post-rerank
Sufficiency at top-n 0.431 against 0.488 at 8 pre-rerank (aggregate), against
bge-base's 0.562. That is reported, not acted on: the rule forbids choosing on
sufficiency.

*Alternatives:* raise the timeout to fit this machine (rejected: loosening PRD
7.3's threshold, which also feeds the p95 latency row); bge-base on CPU (not
measured; the GPU run already misses the timeout); choose bge-base for its
sufficiency (rejected: the eval set would pick the component).

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: `make eval` runs Config 4 and stores every list (F-13, F-61)

Implements supervisor decision 2. `eval_run.pipeline` names PRD 11.6's config
(`config_1_dense | config_3_hybrid | config_4_rerank`); the default is
`config_4_rerank` (BM25 + dense, RRF, then the cross-encoder). Each result stores
`retrieved` (the fused pre-rerank list, the F-13 measurement point),
`retrieved_post_rerank`, `generator_input` (the chunk ids the generator saw),
`rerank_seconds` and `rerank_fell_back`. Over the 800 ms timeout the pipeline
falls back to RRF order (PRD 7.3); when the floor empties the list the item
abstains without a generator call. Run meta names the pipeline, the retrieval and
rerank config, the BM25 index key and the machine; a resume refuses if any of
them changed. Dense-only remains selectable as Config 1 (F-61 unchanged: no
fixed-512-char chunk set exists).

The floor stays at 0.30 with `floor_calibration: pending` (F-112). Runs with
it are dev runs on `claude_cli` and are not comparable with `f2e616e0a7d7`
beyond showing direction: that run is Config 1 at ef_search 40.

*Alternatives:* store only the generator's list (rejected: F-13 needs the
pre-rerank list); make Config 4 a separate target and keep `make eval` dense
(rejected: decision 2); skip the floor until calibrated (rejected: that changes
the pipeline the PRD specifies; the floor is reported as pending instead).

## 2026-10-01 — AUTONOMOUS DECISION - owner to review: router and metadata filters as first built (PRD 7.1)

One small-tier call per question (`claude-haiku-4-5-20251001` on the dev
backend) returns PRD 7.1's JSON. The parse is strict (exact keys, intent in the
taxonomy, confidence a number in [0, 1]); one fenced code block is unwrapped; any
other output is a parse failure, counted, and the item retrieves unfiltered. The
prompt lists the corpus companies by ticker.

Filters apply only at `retrieval.filter_confidence_min` (0.6, PRD 7.1 and
Appendix A) or above. Tickers outside the corpus, periods not of the form
`FY2024` / `Q2 FY2025`, and forms other than 10-K / 10-Q are dropped, never
guessed; if nothing usable is left, retrieval is unfiltered. A filter list that
is empty does not restrict. Filtered retrieval: exact nearest neighbours among
the allowed chunks (index scans off; a filtered HNSW scan can return fewer than
k), BM25 restricted to the same ids, then RRF as unfiltered. A filtered result
that is empty falls back to unfiltered and is counted as `filter_zero_recall`.
The harness also counts, per source, items whose every gold chunk lies outside
the filter: the silent wrong-filter failure PRD 7.1 warns about, which
`filter_zero_recall` does not catch.

Measured retrieval-only against hybrid run 01019ff395ec; not yet in `make eval`.
Router intent, tier selection and sub-queries are recorded but not used.

*Alternatives:* soft filters as a score boost (rejected: PRD 7.1 says hard
filters); filtering inside HNSW with iterative scans (pgvector 0.8.6 has them;
rejected for the first build because exact search over a filtered slice is
simple and has no recall question); re-asking the router on a parse failure
(rejected: eval_run's rule, record and move on).

## 2026-10-02 — OWNER DECISION - periods are resolved in code, not by the router (F-119)

Decided by the supervisor for the owner. The router extracts only what the
question states: tickers, and each period as the question words it. Code maps a
stated date (also inside "fiscal year ended <date>") through `filings.period_end`
to that filing's own `fiscal_year` / `fiscal_quarter`, the dei labels already
stored; the year written in the date is not used. An FY label ("FY2025", "Q3
FY2024", "fiscal 2024") is taken literally, since the filer's filings and the
templated questions carry the filer's own convention. Anything else, including a
date that is no filing's period end, is unresolved and dropped from the filter,
never guessed. No fiscal-year-end table is given to the model: the model's
knowledge of filer conventions is what failed at confidence 0.95.

*Alternatives:* tell the router each filer's fiscal-year convention (rejected:
the same knowledge that failed, moved into the prompt); filter on period-end
date ranges instead of fiscal labels (rejected: a stated FY label would then need
the convention to turn into dates).

*2026-10-02, OWNER DECISION, label defect.* The rule as set accepts quarter
labels; the code rejected a leading article ("the third quarter of fiscal
2023"), a defect in the rule's code, not a new rule. Fixed: an optional "the"
before the label. In filter run d2e59dc4b792 this moves 2 items from ticker-only
filtering to a resolved period (cmp_0018: "the third quarter of fiscal 2023" /
"... 2025"; xbrl_0100: "the third quarter of fiscal 2026"); measured only in the
next full run. Year-to-date phrases ("first three quarters of fiscal 2024", 10
items, F-124) get no fourth rule: they come from our own comparison templates and
a rule added after seeing them cost 2 items would be fitted to the eval set;
ticker-only filtering loses no gold to a wrong period. Checked on d2e59dc4b792's
recorded router responses, no new calls: cmp_0018 keeps 4 of 6 gold chunks in
its filter, xbrl_0100 1 of 1.

## 2026-10-02 — OWNER DECISION - filters and intent budgets go into `make eval` (`config_4_routed`)

Decided by the supervisor for the owner: PRD 7.1's pipeline is what Phase 4's
exit is measured on. `eval_run.pipeline: config_4_routed` (PRD 11.6 Config 8's
component on top of Config 4; Configs 5-7 not built, so this is not Config 8).
The handwritten slice, when it lands, is the gate on filtered numbers (PRD 11.2).
Synthesis routing is not changed to match the candidates' labels (F-121, F-89).

## 2026-10-02 — AUTONOMOUS DECISION - owner to review: how `config_4_routed` applies PRD 7.1's budgets

- One router call per item on `tier_small`, recorded raw. A response that does
  not parse runs as `unrouted` with Config 4's settings (k 50, top-n 8, small
  tier), unfiltered; PRD 7.1 does not say. `unsupported` is declined: no
  retrieval, no generator call, `abstain_reason: unsupported`.
- Budgets from PRD 7.1's table in `router.budgets`: lookup small tier, k 20,
  top-n 5; comparison large tier, k 50 per sub-query, top-n 8; synthesis large
  tier, k 50, top-n 10. k applies to both dense and BM25 per query. Rerank top-n
  now comes from intent, not from the eval item's `question_type` (F-123).
- Lookup and synthesis retrieve for the question itself; comparison for the
  router's two sub-queries (the question stands in for a missing one). Each
  sub-query's fused list is reranked against that sub-query, with the timeout
  and floor applied per rerank pass; the two post-rerank lists are interleaved
  to top-n so both periods reach the generator. The stored pre-rerank list for a
  comparison is the RRF of the two sub-query lists (up to 100), every query's
  lists are stored beside it.
- Filters as in the filter runs: exact dense within the allowed chunks, BM25
  restricted, RRF; an empty filtered result falls back to unfiltered for that
  query (`filter_zero_recall`).
- On `claude_cli`, comparison and synthesis answers come from `tier_large`
  (`claude-sonnet-5-5`), the judge's model; F-14 applies to those items.

*Alternatives:* rerank a comparison's merged candidates once against the
original question (rejected: one period's chunks can take every slot; and 100
pairs per pass would miss the timeout on this machine, F-114); top-n by score
across sub-queries (rejected: same reason); keep Appendix A's single `top_n: 8`
(F-122: PRD 7.1's table is the more specific rule).

## 2026-10-02 — AUTONOMOUS DECISION - owner to review: PRD 7.4 structured output as first built

- Enforcement: `claude_cli` with `--json-schema` (checked: the CLI answers through
  a forced tool call, `stop_reason: tool_use`, and returns `structured_output`; a
  result without it is a CliError, never parsed from prose); `anthropic_api` with
  a forced tool (`tool_choice`) whose `input_schema` is the contract. The API
  path is not exercised (F-59).
- Schema: PRD 7.4's keys; `citations` at least one; `figure` required on every
  claim, null for claims without a number (PRD: "treat it as required on any
  claim containing a number"); `figure.unit` an enum of scales (`ones`,
  `thousands`, `millions`, `billions`, `trillions`, `percent`) so unit scale is
  machine-checkable and numeric scoring reads it directly; `currency`, `concept`
  nullable; `period` free text, as the PRD example.
- System prompt: PRD 7.4's draft verbatim, plus one paragraph on the figure
  object. The plain prompt stays for `generation.structured: false` (Phase 2
  baseline).
- Contract breaches the schema cannot express are recorded per result
  (`contract_violations`: citations to chunks not given, a number with no
  figure, duplicate claim ids, sufficient evidence with no claims, abstention
  with no reason) and never repaired: the verifier's job (PRD 7.5).
- The model's `sufficient_evidence: false` is an abstention (`abstain_reason:
  insufficient_evidence`), counted in the 2x2. Claims are stored in
  `answer.claims`, which numeric scoring reads; `claims_pre` stays empty until
  the verifier adds its per-claim checks, so the claim metrics still print
  "n/a: no claims".

*Alternatives:* ask for JSON in the prompt and parse it (rejected: PRD 7.4 says
enforced, not asked); drop or repair claims with bad citations at generation
(rejected: hides the pre-verification faithfulness the PRD charts).

## 2026-10-02 — AUTONOMOUS DECISION - owner to review: numeric grounding (PRD 7.5), and F-82, F-85, F-87

Decided before any verifier code, without touching gold or reference answers.

**What a claim's numbers are.** The figures `eval.metrics.numeric.text_figures`
reads from the claim text (dates, period labels, form names, item numbers,
period lengths and bare years masked first), each as a magnitude in base units
using the claim's own scale words; plus the figure object's value times its
unit scale. Percentages are kept apart from amounts.

**What a cited chunk offers.** Every figure printed in the chunk (same reader),
each as up to three candidate magnitudes: printed × the chunk's stated scale
(the context line's "in thousands / millions / billions"), printed × a scale
word printed beside it, and printed as is. A claim number is grounded when its
magnitude equals one candidate of one cited chunk exactly (Decimal equality at
the claim's printed precision; no tolerance: PRD 7.4 rule 3 forbids
approximating).

- **F-87, sign.** Grounding compares magnitudes. 296 positive facts print in
  parentheses and 3 negative facts print plain, so a sign-sensitive match would
  strip correct claims. Sign is not part of grounding; it is reported by the
  existing sign-agreement row and the XBRL check below.
- **F-82, zero.** A claim number 0 is grounded when a cited chunk prints 0, or
  holds an inline-XBRL span of value 0 (the filer's "—" for a nil fact,
  `xbrl_spans.raw_text`). A dash with no span behind it does not ground a zero:
  a dash also means "not applicable".
- **F-85, differences.** A number printed in no cited chunk is grounded *as
  derived* when it equals the difference of, or the percent change between, two
  other figures of the same answer that are themselves grounded (percent change
  rounded to the claim's printed decimals). The claim records
  `numbers_derived: true`; derived claims are counted in the report, separately.
  Only differences and percent changes, only between the answer's own grounded
  figures: anything wider would let chance arithmetic over a chunk's numbers
  ground a made-up figure.

**Unit scale (`unit_ok`).** The figure object's value × unit equals a candidate
built with the chunk's stated scale or a printed scale word, not the "as is"
candidate; a chunk whose context line says "except per share" also admits "as
is" for that chunk. A figure grounded only "as is" in a scaled table is a unit
error.

**Period stated.** The claim text names a period: a date, an FY or quarter
label, "fiscal YYYY", "year/months/quarter ended", or a year.

*2026-10-02, amended after smoke run 4d1f5ce1e3f2 (a runner defect, not a
measurement):* a figure grounded only as derived (F-85) is printed in no chunk,
so the unit-scale rule above failed it on every correct comparison answer
(cmp_0010's "$4,008 million" difference: grounded as derived, `unit_ok` false,
verdict PARTIAL). Its scale is consistent when the figure object's base value is
the derived value, since the operands were grounded at their printed scale; it
is then `unit_ok`.

*Alternatives:* sign-sensitive grounding (rejected, F-87); a 0.5% tolerance in
grounding (rejected: rule 3; the tolerance belongs to the XBRL check, PRD 6.5.4);
treating every dash as zero (rejected: dashes also mean n/a); stripping all
derived numbers (rejected: strips every correct comparison answer, F-85);
grounding derived numbers against any pair of chunk numbers (rejected: chance
matches).

## 2026-10-02 — AUTONOMOUS DECISION - owner to review: runtime XBRL validation (PRD 6.5.4, 7.5)

- **Which fact.** Per figure claim, per cited chunk's filing (the accession,
  never "the latest value", Trap 1): facts of that filing for the claim's
  concept whose `period_end` is the claim's period end. `xbrl_facts.fiscal_year`
  / `fiscal_period` are the reporting filing's, not the fact's (checked: AAPL's
  FY2024 10-Qs carry the 2023-09-30 inventory as fiscal_year 2024), so periods
  are matched on `period_end` only.
- **Claim period to period end.** The figure's `period` text through the
  router's resolver (F-119): a stated date is the period end; an FY / quarter
  label resolves to the period end of the filer's own filing for that fiscal
  year and quarter (Q4 and FY: the 10-K). Both durations ending that day (three
  months and year to date) are candidates. Unresolvable period: no lookup.
- **Concept.** `figure.concept` against a hand-written synonym map over the
  curated line items (PRD 6.5.4: "keep a hand-written synonym map for your 25
  curated concepts"), `api/verify/concept_synonyms.yaml`; tag and variant both
  candidates. Not in the map: no lookup, no penalty.
- **Compare.** Magnitudes (F-87), base units, within 0.5%
  (`xbrl.match_tolerance_pct`). Percent figures are not checked.
- **Outcomes** (PRD 6.5.4): a cited filing's candidate fact matches →
  `verified`; none does but the same company, concept and period end has a
  matching fact in another filing → `restatement` (accepted; the other filing
  and value recorded); a cited filing has candidate facts and nothing matches
  anywhere → `contradiction` (strip, and the answer abstains); no candidate fact
  → `no_fact` (falls through to grounding, no penalty).
- **`period_ok`** (PRD 11.2 period accuracy): true when verified or restated;
  false when the value matches a fact of the same concept in a cited filing at a
  different period end (the right number for the wrong period); otherwise
  unknown (null).

*Alternatives:* general taxonomy matching (rejected by PRD 6.5.4); matching on
`fiscal_year` (rejected: it is the filing's year); a contradiction when any cited
filing mismatches though another cited filing matches (rejected: comparisons cite
two filings).

## 2026-10-02 — AUTONOMOUS DECISION - owner to review: NLI for prose claims and its AUC gate (PRD 7.5)

- Model `cross-encoder/nli-deberta-v3-base` @6c749ce3425c, on prose claims only
  (no figure object). Premise: one cited chunk at a time, hypothesis: the claim
  text; `entail` is the softmax probability of the label the model's own
  `id2label` names `entailment`; a claim's score is the max over its cited
  chunks (PRD 7.5 correction 1). Pairs over 512 tokens are truncated by the
  model; each pair records its token count and whether it was truncated, so the
  truncation PRD 7.5 warns about is visible, not silent.
- Gate: 40 (prose claim, cited chunk) pairs drawn by seed from a run's
  `claims_pre`, labelled by the owner (supports / does not) before any score is
  shown; AUC of `entail` against the labels. AUC < 0.75: NLI is dropped and
  prose claims fall to PRD 7.5's fallback (citation validity plus an LLM-judge
  call), not built until that result. AUC ≥ 0.75: `nli_threshold` is the
  threshold maximizing Youden's J on those 40 pairs, written to config with the
  AUC, the sheet and the date. Nothing else sets it.
- Until then `nli_threshold` is null: runs store every check including `entail`;
  the report refuses claim metrics, as it already does.

*Alternatives:* score against the eight chunks concatenated (rejected by PRD
7.5); a threshold of 0.5 by convention (rejected: "set only from that check");
labels by the developer's agent (rejected: PRD 7.5 asks for the owner's own
labels, as for the judge, F-105).

## 2026-10-02 — OWNER DECISION - the first full run is scored before the NLI threshold exists; re-score is derived (F-125)

Decided by the supervisor for the owner. `make eval` runs with
`nli_threshold: null`. Each claim in `claims_pre` stores every check, including
the raw `entail` per cited chunk and its token count, so nothing is regenerated
later. Items with a prose claim carry verdict `PENDING_NLI`; the report prints
the pending count per source and every claim metric as "pending NLI threshold
(F-125)" instead of refusing, so retrieval and numeric columns still print.

The 40-pair NLI sheet is drawn from this run by seed, stratified by source and
by whether the claim passes the gate's other checks (citation validity, entity
match), allocated in proportion to each stratum's pairs.

**Re-score derivation.** Once the owner's labels set `nli_threshold`
(TRADEOFFS, NLI gate), `python -m scripts.eval_run --rescore RUN_ID THRESHOLD`
applies a pure, tested function to the stored results: for each prose claim,
`citations_supporting` = cited chunks with stored `entail` ≥ threshold; then PRD
7.5's verdict and `claims_post` over the stored checks, and the item verdict
exactly as the live gate sets it (the model's own abstention stands; an XBRL
contradiction abstains). Figure claims' checks are not touched. Output:
`eval/runs/<run_id>.rescore-<threshold>.json` with the rebuilt report, the
re-scored verdicts and claims_post per item, the source run id and the
threshold, never a new run id. The source run's files are not modified.

*Amended after smoke 55cb57be9164 (the report raised on verdict
`PENDING_NLI`):* the abstention 2x2 rates of a column also print as pending
while any verdict in it is pending; computing them over the decided items alone
would drop exactly the items with prose claims.

*Alternatives:* re-run generation once the threshold exists (rejected: a second
sample of a nondeterministic generator, F-60, would change what the threshold
was fitted on); write re-scored verdicts back into the run's results (rejected:
a run's files record what the run did).

## 2026-10-02 — OWNER DECISION - XBRL contradictions require matching unit kinds; synonym matches are reported

Decided by the supervisor for the owner. A claim is compared only with facts of
its own unit kind: monetary (fact unit `USD`) when the figure has a currency and
is not per share; per share (`USD/shares`) when the claim or its concept says
"per share" or EPS; shares (`shares`) when it has no currency; percent figures
are not checked (no `pure` comparison). Facts of another kind are ignored, so a
mismatch of kind is `no_fact`, never a contradiction ("gross margin" as a
percent cannot force an ABSTAIN against a dollar fact). Each XBRL result records
the matched synonym phrase, the tags, the claim's kind and the period ends; the
report lists every contradiction with the synonym, the claim figure, the cited
facts and their periods, and counts claims matched per synonym. A contradiction
caused by a wrong synonym is a finding with the item id, never a map edit after
the fact.

## 2026-10-02 — OWNER DECISION - grounding checks digits; the unit check reports what it can (F-130)

Decided by the supervisor for the owner, after eval run a4e39a65c2c8. When a
cited chunk states no scale (no "in thousands / millions / billions" in its
context line) and prints the claim's digits (the claim's magnitude is a printed
number times 10^3, 10^6, 10^9 or 10^12), the number is grounded
(`how: printed_unscaled`) and the figure's `unit_ok` is `unknown`, not false. The
verdict does not drop a claim for an unknown scale. Unit-scale accuracy keeps
unknown claims in the denominator as not correct (F-126's rule), with the
unknown count printed beside it; `unknown` becomes `true` only when the XBRL
check matches a fact within tolerance (`verified`, or `restatement`, a match to
another filing's fact), which confirms the scale. Before: 36 figure claims in 31
items ungrounded for this reason (F-130). The re-verification of a4e39a65c2c8
(entry below) gives the after.

Scale of the gap in the frozen corpus (`chunks`, table chunks whose context line
states no scale and that print figures): AAPL 146 of 443, BAC 470 of 3,052,
COST 230 of 437, JPM 1,208 of 3,315, NVDA 188 of 596, PFE 101 of 1,040, TGT 150
of 506, XOM 188 of 476; all 2,681 of 9,865. No parser change (F-90).

The 4 per-share unit failures of the same run (cmp_0019 claims 1 and 2,
seed_0014, xbrl_0147) are F-90's caption gap: an "in millions" context line
whose "except per share" exception the parser dropped. Logged under F-90; the
unit rule is not widened for them.

*Alternatives:* keep failing the claim (rejected: strips figures the chunk
prints); treat an unknown scale as correct (rejected: lets a claim choose its own
scale unchecked).

## 2026-10-02 — OWNER DECISION - a claim is read at its own printed precision; `rounded` is not a contradiction (F-129)

Decided by the supervisor for the owner. The 0.5% tolerance stays the definition
of `verified`. A claim whose figure has at least two significant digits asserts
the half-unit interval of its printed precision ("$58 billion" asserts [57.5,
58.5) billion; significant digits from the figure value with trailing integer
zeros dropped, so "60" has one). If a cited filing's fact at the claim's period
lies inside that interval but outside 0.5%, the result is `rounded`: the claim
is kept, not verified, counted on the report, `period_ok` true. A
contradiction, which forces ABSTAIN, needs the fact outside both the 0.5% band
and the printed-precision interval. One significant digit gets no interval:
"$60 billion" against 57,639 million is still a contradiction. This reads the
claim at its own precision; it does not widen the tolerance. In a4e39a65c2c8
this concerns xbrl_0104 ("$58 billion" vs 57,639 million), xbrl_0125 ("$4.8
billion" vs 4,767 million) and xbrl_0143 ("$4.9 billion" vs 4,868 million).

*Rejected:* the strict rule as built (any fact outside 0.5% is a contradiction),
which forced those three correct rounded answers to ABSTAIN; a wider tolerance
(would accept a wrong exact figure).

## 2026-10-02 — OWNER DECISION - three synonyms removed; the run's stored claims re-verified (F-128)

Decided by the supervisor for the owner: data wins over the map. Removed from
`api/verify/concept_synonyms.yaml`: "allowance for credit losses" (to the
loans-only tag; BAC's allowance for credit losses includes unfunded
commitments), bare "net sales" (to revenue; Costco's net sales exclude
membership fees), "share repurchases" (to the cash-payments tag). The rest of
the map stays an owner-review item (F-127). The loader also stopped deriving a phrase
from each line-item id: the id `share_repurchases` had put "share repurchases"
back; phrases are now each line item's label and its written synonyms only.

The three changes above are measured by re-running grounding and the XBRL check
over the stored claims of a4e39a65c2c8, no model call:
`python -m scripts.eval_run --reverify a4e39a65c2c8 TAG` writes
`eval/runs/<run_id>.reverify-<TAG>.json` (derived report, per-item verdicts,
re-verified figure checks; prose claims keep their stored checks and `entail`).
Never a new run id; the run's files are not modified.

## 2026-10-02 — AUTONOMOUS DECISION - owner to review: the gate verifies faithfulness, not correctness (F-133)

Decided by the supervisor. The PRD 7.5 gate checks claims against their cited
evidence. Whether the answer addresses the question is correctness, measured by
numeric accuracy and, once F-105 lands, the judge's answer correctness. **PASS is
a faithfulness verdict, never a correctness claim**; that sentence goes into the
README when Phase 5 writes it. The report prints, per source, the verdict
against numeric correctness (correct / wrong / generator abstained / not scored;
unanswerable items marked), so a PASS on a wrong answer is visible. On
a4e39a65c2c8 re-verified (f128-f129-f130): xbrl_auto PASS 102 correct, 24 wrong;
llm_seeded PASS 26 correct, 3 wrong (9 not scored for unit scale, 1 not numeric).

*Rejected:* a question-concept check in the gate (the claim's concept against the
concept the question asks for): faithfulness would then depend on the router and
the synonym map, and a PASS would mean two things.

## 2026-10-02 — AUTONOMOUS DECISION - owner to review: the CI gate, `eval-fast` and the workflow (PRD 11.4, 11.5)

- **`eval/thresholds.yaml` did not exist.** PRD 11.5 names it the single source
  of truth and prints its contents; the repo had no such file. Created as a
  byte-for-byte copy of that block (extracted from `docs/PRD.md`), no number
  changed. §11.2 prose drift stays F-07.
- **`eval/compare.py`** (PRD 11.5's `eval.compare` and `eval.gate` in one, by
  the supervisor's instruction) reads the file as it is. Rows:
  `absolute_minimums` and `maximums` on the aggregate and on the handwritten
  slice (`by_source.handwritten` overrides its two keys there); each other
  `by_source` slice on its own keys; `regression_tolerance` on the aggregate
  against the baseline (a negative tolerance bounds a drop, a positive one a
  rise). A metric that is pending (NLI threshold, judge), not measured (cost per
  query, F-134), on an empty slice (handwritten, F-103) or without a baseline
  prints as pending and fails the gate. A baseline from another subset fails the
  regression rows (F-12). A development-backend report fails. Exit 1 on any
  failure; per-metric table to stdout and Markdown for the PR comment.
  On the full dev run a4e39a65c2c8: GATE FAILED (sufficiency aggregate 0.792 <
  0.82, xbrl_auto 0.705 < 0.90; llm_seeded 1.000 passes; claim metrics pending
  F-125; handwritten empty; claude_cli).
- **Fast subset** `eval/fast_subset_v1.yaml` (`python -m scripts.draw_fast`,
  seed 20261007): 60 items, source quotas by planned set size (xbrl_auto 200,
  llm_seeded 83, handwritten 120 targets) by largest remainder: xbrl_auto 30,
  llm_seeded 12, handwritten 18 reserved and empty until F-103 (filled by a v2
  draw, never by moving the others); within a source, by question type. `make
  eval-fast` runs it on the same pipeline (`eval_run --subset`, which records
  the subset file and hash in the run meta) and then the gate against
  `eval/baselines/main_fast.json`, which must come from the same subset;
  `refuse_dev_baseline` blocks writing it from claude_cli (checked).
- **Backend in CI.** `FILINGQA_GENERATION_BACKEND` overrides
  `generation.backend` (validated); the workflow sets `anthropic_api`. The run
  meta records the backend used.
- **Workflow** `.github/workflows/eval.yml` on pull requests: the first step
  fails the job when `ANTHROPIC_API_KEY` is empty, with that reason, and writes
  it as the PR comment (checked locally: exit 1); then migrate, restore the corpus
  snapshot (fails: no fixture exists, F-135), `make eval-fast`; the gate table is
  posted as a PR comment whenever it exists. Never a skip, never a pass without
  a run.

*Alternatives:* gate only the aggregate (rejected: PRD 14's exit names the
handwritten slice); treat pending metrics as passing until measured (rejected:
a gate that cannot evaluate a gated metric does not pass); skip the job without
a key (rejected: indistinguishable from a pass in the PR checks).

## 2026-10-02 — OWNER DECISION - CI restores a corpus snapshot; rebuilding from the freeze is the fallback only (F-135)

Decided by the supervisor for the owner. `scripts/corpus_snapshot.py dump`
writes `pg_dump -Fc --data-only` of companies, filings, chunks (with
embeddings), xbrl_facts and xbrl_spans, and records the archive's sha256, size,
tables and the parser/chunker versions it carries under `snapshot:` in
`api/corpus_freeze.yaml` (first archive: 104,583,437 bytes, sha256
9a8a82719f6d…). `restore` refuses an archive with another sha256, restores into
the migrated schema, rebuilds the HNSW index in bulk, then runs
`verify_freeze --snapshot` (raw documents are not in the archive; the recorded
hash pins its content; every frozen accession must be present with its status
and every chunk must have an embedding). The workflow downloads release
`corpus-snapshot-<sha12>`, restores through the service container
(`PG_EXEC=docker exec -i <id>`, so the client matches pg 18) and runs
`make eval-fast VERIFY_FLAGS=--snapshot`. Checked locally into a scratch
database: restored 22,354 chunks with embeddings, 43,122 facts, 209,608 spans;
`verify_freeze --snapshot` mismatches 0.

Hosting the archive needs repository credentials: OWNER-BLOCKED (F-135). The
restore does not reproduce the HNSW graph, which moves dense top-50 lists and
the metrics (F-136).

*Fallback, documented only:* rebuild in CI from the freeze (about 90 SEC
downloads per run at 8 req/s, parsing, chunking and embedding 22,354 chunks); not
a CI step.

## 2026-10-02 — OWNER DECISION - cost_per_query defined (F-134)

Decided by the supervisor for the owner. `cost_per_query` is the mean over items
of the cost of every model call made to answer the item: the router and the
generator. The judge is eval cost and excluded; the local NLI model and the
reranker cost zero. Each call's input, output, cache-read and cache-creation
tokens are priced from `eval/pricing.yaml` (model id, USD per million tokens,
the date and source the prices were read from: 2026-10-02,
platform.claude.com pricing page; Claude Haiku 4.5 $1 / $5, Claude Sonnet 5.5
$2 / $10, cache writes at the 5-minute rate, cache reads at the table's rate).
A model with no price, or a call whose tokens were not recorded, makes the cost
pending, never estimated. On `claude_cli` the report prints the token counts
and "cost n/a (dev backend)", and the gate treats that as pending. The router
call's token usage was not stored before this change (a4e39a65c2c8's token
totals cover the generator only); it is stored from now on. F-134 resolves with
the first priced run, which is F-59.

## 2026-10-02 — OWNER DECISION - exact dense search for eval and serving; a deviation from PRD 6.4's HNSW (F-136)

Decided by the supervisor for the owner. `retrieval.dense_search: exact` (a
sequential scan ordered by cosine distance, ties to the smaller chunk id) is the
default for eval and serving; `hnsw` stays a config option, off by default. Every
run's meta records `dense_search`, so a run is reproducible from the corpus
snapshot alone. Why: HNSW at the pipeline's depth is not reproducible: at depth
50, 68 of 283 dense lists differ from exact search on the live database and 89 on
a restored one, and recomputing 01019ff395ec's hybrid lists on a restore changes
49 fused top-10 lists (F-136). Cost, measured on the 283 questions (retrieval run
5b3c3ac13e5e, M1 Pro, 22,354 vectors): p50 0.075 s, p95 0.112 s, max 0.244 s per
dense query. Stored runs are immutable records and are not recomputed;
5b3c3ac13e5e is the new comparison point, and its difference from 01019ff395ec
is a finding (F-139), not a gain. F-109's HNSW check held at depth 10 only.
The Phase 2 baseline's own query (`api/query/baseline.py`, specified through
HNSW) and `scripts/exact_nn_check.py` keep HNSW.

*Rejected:* a physical snapshot carrying the HNSW index (HNSW builds are not
deterministic across machines either); keeping HNSW and rebuilding the CI
baseline on every restore (comparisons would depend on the build).

## 2026-10-02 — OWNER DECISION - rerank device `auto`; the timeout holds on any hardware (F-137)

Decided by the supervisor for the owner. `rerank.device: auto` resolves to `mps`,
else `cuda`, else `cpu`; the device used is recorded in every run's meta
(`rerank.device_used`) and in rerank runs. The 800 ms timeout and the RRF
fallback stay: on CPU the eval measures the system as it would run on that
hardware; `rerank_fell_back` is printed per source and a run with any fallback
is flagged `hardware_dependent: true` in its report. No CI-only exemption. A
GPU runner is the owner's cost decision (F-137): MiniLM on CPU had p95 0.834 s,
34 of 283 over the timeout (rerank run 45e3ed5c8f13).

## 2026-10-02 — OWNER DECISION - Phase 5 "ingest remaining 5 companies" was satisfied at the freeze

Decided by the supervisor. The item dates from the PRD's 3-company development
slice. The frozen eval corpus has been 8 companies × 3 years since the Phase 2
freeze (F-06, F-42: 96 accessions, 8 tickers, `api/corpus_freeze.yaml`), so the
item is done; the frozen corpus is never re-ingested (PRD 11.4). No separate demo
corpus: the PRD does not ask for one.

## 2026-10-02 — AUTONOMOUS DECISION - owner to review: the HTTP API as first built (PRD 9)

- **One path.** `POST /api/v1/query` calls `api.pipeline.answer_question`, the
  function `scripts.eval_run` calls for `config_4_routed`, with the same config
  (`eval_run.pipeline`, `generation`, `retrieval`, `rerank`, `router`,
  `verification`); the routed pipeline moved from `scripts/eval_run.py` into
  `api/pipeline.py` unchanged. A test asserts both callers reach that function
  with the same config. Only `config_4_routed` is served (the other configs
  need the eval item's label, F-123); any other configured pipeline returns 503.
- **Shapes** as PRD 9, plus `backend`, `model_served`, `development` and, for a
  verdict still waiting on the NLI threshold, `verification_pending` (verdict
  `PENDING_NLI`, F-125). `page_hint` is null (F-55). `confidence` is the
  fraction of the generator's claims the gate kept (0.0 on ABSTAIN, null while
  pending): a plain ratio, not a calibrated probability. Claims shown are
  `claims_post` (PARTIAL shows supported claims only, PRD 7.5), each with its
  XBRL status and, for a restatement, the restating filing. `cost_usd` follows
  F-134 (null with "cost n/a (dev backend)" on claude_cli). `nearest_evidence`
  `rerank_score` is null: per-chunk rerank scores are not kept by the pipeline.
- **Errors.** 400 for a malformed or empty request and for the request's
  `filters` / `options` overrides (deferred, F-140); 422 when the question is
  longer than the embedder's own window (512 tokens), checked before any model
  call (no separate limit invented); 503 when the database is unreachable.
  Abstention is a 200.
- **Concurrency.** One process, one loaded model set: queries run one at a time.
- **Prompt injection (PRD 15).** The question is data in the user turn after
  the evidence; the system prompt is fixed. Tests (stubbed generator, inline
  facts, no database): a filing-text injection telling the model to report
  revenue as $1 billion, obeyed by the generator, is caught by the cited
  filing's XBRL revenue fact and never reaches the answer; a question telling
  the model to cite a chunk it was not given fails citation validity and is
  dropped. The injected chunk exists only in the test module (F-24).

*Alternatives:* a separate serving pipeline (rejected: the shipped path would
not be the measured path); a fixed character limit for 422 (rejected: invents a
number the PRD does not give).

## 2026-10-02 — AUTONOMOUS DECISION - owner to review: the frontend as first built (PRD 10)

Stack as PRD 10 (supervisor decision): Next.js 16.3.8 App Router, TypeScript,
Tailwind 4, shadcn/ui (radix base), in `web/`. **npm**, since pnpm is not
installed; `web/package-lock.json` is committed and Node is pinned to the
installed major in `web/.nvmrc` (24). `make web-dev`, `make web-build`; `make
lint` adds ESLint and `tsc --noEmit` for `web/`, `make test` adds the Playwright
suite, and CI has a `web` job doing the same.

- **No `/query` through the browser.** A live answer takes 20-55 s; the Next dev
  proxy cuts rewrites at 30 s (checked in `next/dist/server/lib/router-utils`).
  The Answer page is a server component that calls the API directly
  (`web/src/lib/api.ts`, `API_BASE`), with a loading state; the source panel's
  chunk lookup goes through a route handler (`/web-api/chunks/[id]`). Nothing in
  `web/` imports from `eval/` or reads run files.
- **Rendered from the response only.** The dev banner comes from the response's
  `development` field; the abstention panel, the "✓ matches SEC XBRL" badge,
  the restatement and printed-precision notes, the pending notice and the
  latency / cost line come from the response's verdict and per-claim records.
  Confidence shows as a band: High ≥ 0.9, Medium ≥ 0.6, Low below, the cut
  points of PRD 7.5's verdict ratios; Pending while the verdict waits on the NLI
  threshold. Citations are numbered in reading order.
- **Ask**: the three PRD 10 examples are a lookup, a comparison and "Should I buy
  NVIDIA stock right now?", which the pipeline declines live (intent
  `unsupported`), labelled "See how it handles a question it can't answer."
  Company / year filter chips are not built: the API's filter override is
  deferred (F-140).
- **Tests.** `@playwright/test` 1.63.0 with its Chromium (toolchain). The e2e
  suite (`web/e2e/`) runs against `e2e/mock-api.mjs`, which serves responses
  captured from the real API on `claude_cli` (`web/e2e/fixtures/`, labelled
  development, README there). The e2e Next server uses its own build directory
  (`NEXT_DIST_DIR=.next-e2e`): Next allows one dev server per directory, and
  `make test` must work while `make web-dev` runs. Its base URL is `localhost`:
  the dev server's HMR socket refused `127.0.0.1`, which left pages unhydrated.
  A manual live pass is `web/scripts/live-pass.mjs` (screenshots and a summary to
  `build/web-live/`, git-ignored, never committed or used in the README, F-59).

- **Dependencies** are pinned to exact versions in `web/package.json` and the
  committed lockfile. shadcn's `cn()` is the local `src/lib/utils.ts` over `clsx`
  and `tailwind-merge` (the scaffold had wired it to an unrelated npm package
  `cn`, removed). The `shadcn` CLI is a devDependency only because
  `globals.css` imports its `tailwind.css` (variants and keyframes), read at build
  time; nothing imports it at runtime.
- `web/AGENTS.md` and `web/CLAUDE.md` are written by `next dev` itself and left as
  the tool writes them; they are not this project's working agreement, which is
  the repository root's.

*Alternatives:* raise the dev proxy timeout (rejected: the production path
should not depend on a dev setting); call `/query` from the browser with CORS on
the API (rejected: same timeout question in production proxies, and the API key
story later is simpler server-side).

## 2026-10-02 — AUTONOMOUS DECISION - owner to review: `/metrics`, the Corpus screen and the eval dashboard

- `GET /api/v1/metrics` (`api/metrics.py`) reads committed files only: the gate
  table exactly as `eval/compare.py` computes it for the latest gated eval run
  (none yet: every row pending "no gated run exists (F-59)"; `compare.rows`
  now takes `None` for that case); each model-free retrieval run's per-source
  hybrid Sufficiency@10 beside its threshold, labelled Config 3 and "unreviewed
  candidates"; development runs as ids, files and the banner. A run is
  development when its report or meta says `development_run` or a development
  backend; filter and smoke runs are development. This is decided in the
  endpoint, and a test writes development reports with a sentinel value and
  asserts it appears nowhere in the payload. Runs whose files predate a field
  say so ("not recorded") rather than guess.
- `eval/dashboard.yaml` is the committed source for the current retrieval
  comparison run, the owner-blocked list and the metrics that stay pending even
  with a gated run; the README's status section and the dashboard both come from
  it, and `tests/unit/test_metrics.py` fails if the README's quoted run, figures,
  thresholds, pending list or owner-blocked table differ from `/metrics`.
- `/corpus/summary` adds the freeze totals and the six quarantined filings with
  their reasons and findings (F-66, F-70) from `api/corpus_freeze.yaml`. The
  Corpus screen says what is and is not in the index; it shows no generated text,
  so no banner.
- The dashboard renders `/metrics` only: the gate box and per-metric table, the
  current retrieval run (other runs as superseded comparison points), development
  run ids with the banner and no value, and the owner-blocked list.
