.PHONY: help install db-up db-down db-psql migrate lint fmt test eval eval-fast eval-gate \
	restore-corpus-snapshot serve

# Targets are added as the modules behind them land.

help:
	@echo "install   install the package plus dev extras"
	@echo "db-up     start Postgres (pgvector/pg16) and wait for it"
	@echo "db-down   stop Postgres, keeping the volume"
	@echo "db-psql   open a psql shell"
	@echo "migrate   apply pending migrations from infra/migrations/"
	@echo "lint      ruff check + ruff format --check"
	@echo "fmt       ruff format + ruff check --fix"
	@echo "test      pytest, excluding network-marked tests"
	@echo "eval      verify the freeze, run the eval over the candidates, print the report"
	@echo "eval-fast the 60-item fast subset on the same pipeline, then eval-gate"
	@echo "eval-gate eval/compare.py: build/eval_fast.json vs thresholds and main_fast baseline"
	@echo "serve     the HTTP API (PRD 9) on localhost:8000; docs at /docs"

install:
	python -m pip install -e ".[dev]"

db-up:
	docker compose up -d --wait postgres

db-down:
	docker compose stop postgres

db-psql:
	docker compose exec postgres psql -U filingqa -d filingqa

migrate:
	python -m api.db

lint:
	ruff check .
	ruff format --check .

fmt:
	ruff format .
	ruff check --fix .

test:
	pytest -m "not network"

# One full eval run (PRD 11.4): freeze check first, then every candidate item.
# The report carries the backend; a claude_cli run is marked a development run.
# Resume a stopped run with: python -m scripts.eval_run --resume RUN_ID
eval:
	python -m scripts.verify_freeze
	python -m scripts.eval_run --run

# PRD 11.5 fast eval for PRs: the committed 60-item subset (eval/fast_subset_v1.yaml)
# on the same pipeline, then the gate against a baseline from the same subset (F-12).
# The gate exits non-zero on any failed or pending gated metric.
eval-fast:
	python -m scripts.verify_freeze $(VERIFY_FLAGS)
	python -m scripts.eval_run --run --subset eval/fast_subset_v1.yaml --report-out build/eval_fast.json
	$(MAKE) eval-gate

eval-gate:
	python -m eval.compare --report build/eval_fast.json --baseline eval/baselines/main_fast.json \
		--thresholds eval/thresholds.yaml --md build/eval_gate.md

# CI restores the frozen corpus from the snapshot archive (scripts/corpus_snapshot.py),
# checked against the sha256 in api/corpus_freeze.yaml, then verify_freeze --snapshot.
# The archive must be in build/ first; hosting it is OWNER-BLOCKED (F-135).
restore-corpus-snapshot:
	python -m scripts.corpus_snapshot restore build/corpus_snapshot.dump

# PRD 9 API. On claude_cli every answer is labelled development (OWNER DECISION).
serve:
	uvicorn api.server:app --port 8000
