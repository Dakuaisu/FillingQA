.PHONY: help install db-up db-down db-psql migrate lint fmt test eval

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
