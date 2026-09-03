.PHONY: help install db-up db-down db-psql migrate lint fmt test

# Targets are added as the modules behind them land. Phase 1 only.

help:
	@echo "install   install the package plus dev extras"
	@echo "db-up     start Postgres (pgvector/pg16) and wait for it"
	@echo "db-down   stop Postgres, keeping the volume"
	@echo "db-psql   open a psql shell"
	@echo "migrate   apply pending migrations from infra/migrations/"
	@echo "lint      ruff check + ruff format --check"
	@echo "fmt       ruff format + ruff check --fix"
	@echo "test      pytest, excluding network-marked tests"

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
