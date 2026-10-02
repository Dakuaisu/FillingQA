# FilingQA

Ask a question about the 10-K and 10-Q filings of eight US companies and get an
answer broken into claims, each citing the filing chunk it came from, each
checked against that chunk and, for figures, against the filing's own XBRL data;
when the filings do not support an answer, it says so. The pipeline exists to be
measured: the evaluation harness, and the CI gate built on it, is the point.
Full specification in [`docs/PRD.md`](docs/PRD.md).

## Architecture

1. **Ingest** EDGAR filings and XBRL facts; inline-XBRL spans are captured before
   the HTML is flattened (`api/ingest/`, `api/parse/ixbrl.py`).
2. **Chunk** by document structure, tables whole, every chunk headed with its
   company, form, period and section (`api/chunk/`).
3. **Retrieve** with exact dense search plus BM25, fused by RRF
   (`api/query/retrieve.py`, `api/query/bm25.py`).
4. **Route**: a small model classifies intent and extracts companies and periods;
   periods are resolved to fiscal years in code, not by the model
   (`api/query/router.py`).
5. **Rerank** with a cross-encoder, a score floor and a timeout that falls back
   to the fused order (`api/query/rerank.py`).
6. **Generate** schema-enforced claims, each with citations and a figure object
   (`api/generate/claims.py`).
7. **Verify** numeric grounding against the cited chunk
   (`api/verify/grounding.py`), figures against the cited filing's XBRL fact
   (`api/verify/xbrl_check.py`), prose by NLI, pending its threshold
   (`api/verify/nli.py`).
8. **Decide** PASS / PARTIAL / ABSTAIN from the checks (`api/verify/verdict.py`).
9. **Serve** the same function the eval runs (`api/pipeline.py`, `api/server.py`,
   `web/`).
10. **Measure** per source and gate it (`eval/runner.py`, `eval/compare.py`).

## What is hard here

What the build found, not what the PRD predicted:

- **The XBRL-templated questions are the hard slice.** Retrieval finds the right
  filing but not the chunk; the misses are ranking and budget, not a defect
  (F-98, F-138).
- **The LLM-seeded questions are lexically easy:** they reuse their source
  chunk's words, which flatters keyword retrieval (F-110).
- **PASS is a faithfulness verdict, never a correctness claim.** An answer about
  the wrong line item can be faithful to its chunk; correctness is measured
  separately (F-133).
- **Fiscal-year conventions:** NVIDIA's year ending January 2026 is fiscal 2026,
  Target's is fiscal 2025; a model asked to pick the year picked wrong
  confidently, so periods are resolved from the filings' own dates (F-119).
- **Scale captions:** "in millions" does not cover per-share rows, and many
  tables state no scale at all (F-90).
- **Restatements versus rounding:** the facts feed drops XBRL precision, so a
  rounded figure and a real restatement look alike (F-47).

## Metrics

Gated metrics by source (PRD 11.2, thresholds in `eval/thresholds.yaml`). No
value appears here until a gated run exists; the figures in the status section
below are model-free retrieval measurements, not this table.

| Metric | xbrl_auto | llm_seeded | handwritten | aggregate |
|---|---|---|---|---|
| Sufficiency@10 | waiting on a gated run (F-59) | waiting on a gated run (F-59) | waiting on F-103 | waiting on a gated run (F-59) |
| Faithfulness (pre) | waiting on a gated run (F-59) | waiting on a gated run (F-59) | waiting on F-103 | waiting on a gated run (F-59) |
| Claim retention | waiting on a gated run (F-59) | waiting on a gated run (F-59) | waiting on F-103 | waiting on a gated run (F-59) |
| Citation coverage | waiting on a gated run (F-59) | waiting on a gated run (F-59) | waiting on F-103 | waiting on a gated run (F-59) |
| Answer correctness | waiting on a gated run (F-59) | waiting on a gated run (F-59) | waiting on F-103 | waiting on a gated run (F-59) |
| False-answer rate | waiting on a gated run (F-59) | waiting on a gated run (F-59) | waiting on F-103 | waiting on a gated run (F-59) |
| Over-abstention rate | waiting on a gated run (F-59) | waiting on a gated run (F-59) | waiting on F-103 | waiting on a gated run (F-59) |
| XBRL contradiction rate | waiting on a gated run (F-59) | waiting on a gated run (F-59) | waiting on F-103 | waiting on a gated run (F-59) |

## Reproduce

- `make eval`: every candidate item through the served pipeline, a per-source
  report and the run files in `eval/runs/`.
- `make eval-fast`: the committed 60-item subset, then the gate
  (`eval/compare.py`), which exits non-zero on any failed or pending metric.
- On the default `claude_cli` backend every run is a development run: never a
  baseline, never a result, never able to pass the gate. Gated runs use
  `anthropic_api`.

## Status

**Built up to the items that wait on the owner. The CI eval gate fails.** Phases
1–3 are complete; Phases 4 and 5 are built up to the owner-blocked items below.

### Where the gate stands

The gate (`eval/compare.py` against `eval/thresholds.yaml`, PRD 11.5) does not
pass, and no number in this README describes it as passing:

- **No gated run exists.** Every generation run so far used a development
  backend (the `claude` CLI on a subscription); those runs are not results, are
  not quoted here, and cannot pass the gate by construction. A gated run needs
  `ANTHROPIC_API_KEY` in CI (F-59).
- **Retrieval sufficiency misses its thresholds.** The model-free hybrid
  retrieval measurement (BM25 + exact dense search, RRF; retrieval run
  `7fa009acac95`, Config 3 of PRD 11.6, no router, on unreviewed candidates)
  reaches Sufficiency@10 0.537 aggregate against 0.82, 0.375 on the
  XBRL-templated slice against 0.90, and 0.928 on the LLM-seeded slice against
  0.80 (that slice is inflated by lexical overlap with its source chunk, F-110). The specified pipeline adds the
  router and metadata filters; its numbers come from development runs and are
  not reported here. Why the XBRL slice misses: `docs/OPEN.md` F-138.
- **Every gated metric is pending,** and pending fails the gate: there is no
  gated run (F-59). Even once one exists, these stay pending:
  - faithfulness, claim retention, citation coverage and the abstention rates
    (the NLI threshold needs 40 owner labels, F-125);
  - answer correctness (judge labels, F-105);
  - the natural-phrasing gap and every handwritten-slice threshold (hand-written
    items, F-103);
  - cost per query (needs a priced run, F-134).

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
| Deploy: Fly.io and Vercel accounts, LangFuse keys, the deploy itself and the public URL (exact commands in the finding) | F-143 |

Dense search is exact, so any run is reproducible from the corpus snapshot
(F-136). The reranker runs on whatever device is present; a run where it hit
its timeout is marked hardware-dependent, and a GPU CI runner is the owner's
cost decision (F-137). Everything decided so
far is in [`docs/TRADEOFFS.md`](docs/TRADEOFFS.md); every finding, open or
resolved, in [`docs/OPEN.md`](docs/OPEN.md); the build log in
[`docs/WORKLOG.md`](docs/WORKLOG.md).

## Known limitations

- Six 10-Ks are not in the index: JPMorgan Chase's three and Exxon Mobil's
  three. Their MD&A and financial statements sit in an appended annual-report
  section that the parser does not follow, so they were quarantined at the corpus
  freeze (F-66, F-70). Their 10-Qs are in the corpus; there are no 10-K
  questions for JPM or XOM. The Corpus screen lists the six filings.

## Deploy

What exists: Docker images for the API (`deploy/api.Dockerfile`, which refuses to
serve unless the database matches the corpus freeze) and the frontend
(`web/Dockerfile`), `deploy/compose.yaml` running both on Postgres restored from
the corpus snapshot, hosting manifests (`deploy/fly.toml` for the API,
`web/vercel.json` for the frontend), and LangFuse tracing that sends nothing
without keys. `make deploy-check` builds and runs both images locally against
the snapshot and checks `/health` and the Ask page. Every secret is an
environment variable.

What waits on the owner: hosting the snapshot, a Postgres, Fly.io and Vercel
accounts, `ANTHROPIC_API_KEY` and LangFuse keys, the deploy itself and the public
URL. The exact commands are in `docs/OPEN.md` F-143. There is no public URL yet.

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
