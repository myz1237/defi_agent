# DeFi Agent — common tasks. Run `make` or `make help` to list targets.
# Backend port is overridable: `make api PORT=8000`. Frontend is fixed at :3000 (web/.env.local -> :8001).

.DEFAULT_GOAL := help
PORT ?= 8001

.PHONY: help install env setup db-up db-down migrate ingest \
        api cli studio web web-install test eval lint fmt check clean

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-13s\033[0m %s\n", $$1, $$2}'

## --- Setup ---
install: ## Install Python deps (uv sync)
	uv sync

env: ## Create .env from .env.example (won't overwrite an existing .env)
	@test -f .env && echo ".env already exists, skipping" || cp .env.example .env

setup: install db-up migrate ingest ## One-shot: deps + Postgres + migrations + doc ingestion

## --- Database / data ---
db-up: ## Start local Postgres+pgvector (docker compose)
	docker compose up -d

db-down: ## Stop local Postgres
	docker compose down

migrate: ## Apply Alembic migrations (business tables + doc_chunks)
	uv run alembic upgrade head

ingest: ## Ingest LI.FI/Morpho docs into the pgvector store (idempotent)
	uv run python scripts/ingest_docs.py

## --- Run ---
api: ## Run the FastAPI backend (SSE) on :8001 (override with PORT=)
	uv run uvicorn app.main:app --port $(PORT)

cli: ## Run the terminal chat CLI (multi-turn, interrupt/resume)
	uv run python scripts/chat.py

studio: ## Open LangGraph Studio (visualize the graph)
	uv run langgraph dev

web-install: ## Install frontend deps
	cd web && npm install

web: ## Run the Next.js frontend on :3000 (needs the API running)
	cd web && npm run dev

## --- Test / quality ---
test: ## Run the test suite
	uv run pytest -q

eval: ## Run the scope-guard routing eval (real LLM calls)
	uv run python scripts/eval_routing.py

lint: ## Lint with ruff
	uv run ruff check app/ scripts/ tests/

fmt: ## Auto-format with ruff
	uv run ruff format app/ scripts/ tests/

check: lint test ## Lint + test

clean: ## Remove caches (__pycache__, .pytest_cache, .ruff_cache)
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache
