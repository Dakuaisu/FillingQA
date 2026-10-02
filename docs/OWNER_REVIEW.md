# Owner review of the autonomous decisions — 2026-10-02

The owner has reviewed the "AUTONOMOUS DECISION - owner to review" entries in
`docs/TRADEOFFS.md` and the non-blocking review items in `docs/OPEN.md`. The decisions
below are OWNER DECISIONS. Where one conflicts with the PRD, the decision wins; record
each in `docs/TRADEOFFS.md` as `OWNER DECISION` with the PRD section it overrides.

All `CLAUDE.md` rules still apply: no fabricated numbers, faithfulness on `claims_pre`,
`eval/thresholds.yaml` untouched, no re-blessed snapshots, no re-freeze of the corpus,
development-backend runs labelled as such and never presented as a baseline.

## D1 — Reranker: use bge-reranker-base, relax the timeout (changes F-111, F-113, F-137)

The adopted MiniLM reranker lowers Sufficiency@10 below the fused order it reranks
(0.431 vs 0.488, F-113); bge-reranker-base raised it to 0.562 but missed the 800 ms
timeout (p95 1.80 s on mps). The owner prefers retrieval quality over the timeout.

1. `api/config.yaml` `rerank`: `model: BAAI/bge-reranker-base` at the revision measured
   in F-111 (pin the full commit sha), `timeout_ms: 3000`. Update the comments.
2. Re-measure on the frozen candidates with the existing rerank tooling: rerank latency
   p50/p95 and over-timeout count on mps, and the same on cpu (for F-137). Record the
   run ids. If the measured mps p95 is above 2,500 ms, set the timeout to the measured
   p95 plus 20%, rounded up to the next 500 ms, and say so.
3. Re-run the retrieval and rerank measurements and the `config_4_routed` eval on the
   development backend, the way earlier runs were made. Update `eval/dashboard.yaml`,
   `/metrics` and the README only through their existing mechanisms.
4. PRD 11 "Retrieval latency p95 ≤ 900ms" will be missed. It is not gated; report the
   measured value next to the target, marked as an owner-accepted trade-off.
5. The score floor stays `pending` (F-112): do not calibrate it on unreviewed items,
   even though the score distribution changes with the model.
6. F-137: no GPU runner. `device: auto` and the `hardware_dependent` flag stay; record
   the cpu over-timeout count for bge-reranker-base in F-137 and leave it as the owner's
   cost option.
7. Resolve F-113 and update F-111 in `docs/OPEN.md` with the new run ids.

## D2 — JPM and XOM 10-Ks stay quarantined; known limitation (F-66, F-70)

No parser change and no re-freeze. Add a "Known limitations" section to the README
(or extend it if one exists): six 10-Ks (JPM ×3, XOM ×3) are quarantined because their
MD&A and financial statements sit in an appended annual-report section the parser does
not follow; their 10-Qs are in the corpus; there are no 10-K questions for JPM or XOM.
Mark F-66 and F-70 resolved as "owner accepted as known limitation".

## D3 — Comparison items as built: accepted (F-83, F-84)

Auto comparison items draw only on pairs with no shared gold chunk; the 20 hand-written
comparison items are the plain year-over-year tests. No change. Note the owner's
acceptance on F-83.

## D4 — No temperature pin: accepted (F-60)

Keep generation without a temperature and keep measuring run-to-run noise. No SDK
change. Note the owner's acceptance on F-60.

## D5 — Unit-scale rules as built: accepted, with a review aid (step 4c, F-45, F-90)

The table-scale rules stand. Because "except per share" style exceptions are not
captured (F-90), make the risk visible during the owner's review: in the existing
review worksheets (`eval/review/worksheets/*.yaml`) and spot-check sheets, flag every
item whose gold chunk is a table with a scale-exception clause (the F-90 measurement's
definition), e.g. a `scale_exception: true` note. Do not change, drop or re-draw any
item, and do not fill any review decision.

## D6 — Everything else: accepted as is

Every other autonomous decision is accepted unchanged, including F-11 (natural phrasing
inside the hand-written gate), F-14 (judge family is still the owner's choice at F-105),
F-141 (untested frontend states stay as recorded) and the CI gate failing until the
owner-blocked items exist.

## Recording the review

Under each "AUTONOMOUS DECISION - owner to review" heading in `docs/TRADEOFFS.md`, add
one line without rewriting the entry:
- `OWNER REVIEW 2026-10-02: accepted.`, or
- `OWNER REVIEW 2026-10-02: changed by D1 (docs/OWNER_REVIEW.md).` for the reranker
  entries.

## Done when

- [ ] D1 config change, measurements, eval re-run, OPEN/TRADEOFFS updates, committed
- [ ] D2 README known limitations; F-66, F-70 resolved
- [ ] D3, D4 acceptances noted on F-83, F-60
- [ ] D5 flags on the review sheets, no item changed
- [ ] Every autonomous decision heading carries an owner-review line
- [ ] WORKLOG entry; test suite and lint pass; README, dashboard and `/metrics` agree

Then the project is back at the owner-blocked boundary (F-59, F-103 to F-106, F-112,
F-125, F-127, F-135, F-143).
