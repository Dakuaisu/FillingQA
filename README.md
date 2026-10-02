# FilingQA

Citation-grounded question answering over SEC 10-K and 10-Q filings, built around
a CI-gated evaluation harness. The RAG pipeline exists to be measured; the harness
is the point. Full specification in [`docs/PRD.md`](docs/PRD.md).

**Status: Phase 5 (ship and document) started. The CI eval gate fails.** Phases
1–3 are complete; Phase 4 is built up to the items that wait on the owner (below).

### Where the gate stands

The gate (`eval/compare.py` against `eval/thresholds.yaml`, PRD 11.5) does not
pass, and no number in this README describes it as passing:

- **No gated run exists.** Every generation run so far used a development
  backend (the `claude` CLI on a subscription); those runs are not results, are
  not quoted here, and cannot pass the gate by construction. A gated run needs
  `ANTHROPIC_API_KEY` in CI (F-59).
- **Retrieval sufficiency misses its thresholds.** The model-free hybrid
  retrieval measurement (BM25 + dense, RRF; retrieval run `01019ff395ec`, Config
  3 of PRD 11.6, no router, on unreviewed candidates) reaches Sufficiency@10
  0.519 aggregate against 0.82, 0.365 on the XBRL-templated slice against 0.90,
  and 0.892 on the LLM-seeded slice against 0.80 (that slice is inflated by
  lexical overlap with its source chunk, F-110). The specified pipeline adds the
  router and metadata filters; its numbers come from development runs and are
  not reported here. Why the XBRL slice misses: `docs/OPEN.md` F-138.
- **Gated metrics that cannot be evaluated yet,** which fail the gate as
  pending: faithfulness, claim retention, citation coverage and the abstention
  rates (the NLI threshold needs 40 owner labels, F-125), answer correctness
  (judge labels, F-105), the natural-phrasing gap and every handwritten-slice
  threshold (hand-written items, F-103), cost per query (needs a priced run,
  F-134).

**PASS is a faithfulness verdict, never a correctness claim.** The verifier
checks each claim against the evidence it cites (PRD 7.5); whether the answer
addresses the question is measured separately (numeric accuracy, and the judge
once validated). Reports print the two side by side (F-133).

### What waits on the owner

| Item | Finding |
|---|---|
| API key for CI runs, the fast-eval baseline, a priced run, the deliberate-regression PR and its screenshot | F-59, F-134 |
| Hand-written eval items (unanswerable, adversarial, natural phrasing, comparison) | F-103 |
| Human review of the candidates; the golden-set freeze; ablations run only on reviewed items | F-104, F-106 |
| Judge validation labels | F-105 |
| NLI gate labels (40 pairs, `eval/nli/label_sheet_v1.md`) | F-125 |
| Rerank score-floor calibration | F-112 |
| Hosting the corpus snapshot for CI (exact command in the finding) | F-135 |
| Review of the XBRL concept synonym map | F-127 |

Open decisions on reproducibility in CI: F-136 (dense top-50 after a corpus
restore), F-137 (no `mps` reranker device on CI runners). Everything decided so
far is in [`docs/TRADEOFFS.md`](docs/TRADEOFFS.md); every finding, open or
resolved, in [`docs/OPEN.md`](docs/OPEN.md); the build log in
[`docs/WORKLOG.md`](docs/WORKLOG.md).

## Local setup

Requires Postgres 18 with the `vector` extension available, and Python 3.11+.

```bash
python -m pip install -e ".[dev]"
cp .env.example .env      # set DATABASE_URL, and SEC_USER_AGENT to a real email
make migrate
```

`make migrate` applies everything in `infra/migrations/` in filename order and
records each file in `schema_migrations`, so re-running it is a no-op.

If you do not have a local Postgres, `make db-up` starts one in Docker
(`pgvector/pgvector:pg18`) matching the default DSN in `.env.example`.

## Development

```bash
make lint
make test
make eval        # full candidate set on the configured pipeline (verify_freeze first)
make eval-fast   # the committed 60-item subset, then the gate (eval/compare.py)
```

`make eval` on the default `claude_cli` backend produces development runs only;
they are never a baseline (`refuse_dev_baseline`) and never pass the gate.

## Documents

- [`docs/PRD.md`](docs/PRD.md) — the specification
- [`docs/TRADEOFFS.md`](docs/TRADEOFFS.md) — decisions taken, and deferred PRD
  defects logged against the phase where they have to be resolved
