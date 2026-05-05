SHELL := /bin/bash
.DEFAULT_GOAL := help

API_DIR := apps/api
WEB_DIR := apps/web

# Load .env if present
ifneq (,$(wildcard .env))
	include .env
	export
endif

.PHONY: help
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

.PHONY: setup
setup: env db-up api-install web-install migrate ## One-shot bootstrap

.PHONY: env
env: ## Create .env from .env.example if missing
	@[ -f .env ] || cp .env.example .env

.PHONY: api-install
api-install: ## uv sync backend deps
	cd $(API_DIR) && uv sync

.PHONY: web-install
web-install: ## pnpm install frontend deps
	cd $(WEB_DIR) && pnpm install

.PHONY: db-up
db-up: ## Start Postgres
	docker compose up -d db
	@echo "Waiting for Postgres..."
	@until docker compose exec -T db pg_isready -U $${POSTGRES_USER:-credit} >/dev/null 2>&1; do sleep 1; done
	@echo "Postgres ready."

.PHONY: db-down
db-down: ## Stop Postgres
	docker compose down

.PHONY: db-reset
db-reset: ## Destroy and recreate the database (DANGEROUS)
	docker compose down -v
	rm -rf .pgdata
	$(MAKE) db-up migrate

.PHONY: migrate
migrate: ## Run alembic migrations
	cd $(API_DIR) && uv run alembic upgrade head

.PHONY: migration
migration: ## Create a new migration: make migration name=add_foo
	cd $(API_DIR) && uv run alembic revision --autogenerate -m "$(name)"

.PHONY: api
api: ## Run backend (reload)
	cd $(API_DIR) && uv run uvicorn src.main:app --reload --host $${API_HOST:-127.0.0.1} --port $${API_PORT:-8000}

.PHONY: web
web: ## Run frontend dev server
	cd $(WEB_DIR) && pnpm dev

.PHONY: dev
dev: db-up ## Run db + api + web concurrently (Ctrl-C to stop both)
	@$(MAKE) -j2 api web

.PHONY: snapshot
snapshot: ## Trigger a one-off snapshot
	curl -fsS -X POST http://$${API_HOST:-127.0.0.1}:$${API_PORT:-8000}/snapshot/run | jq .

.PHONY: test
test: test-api test-web ## Run all tests

.PHONY: test-api
test-api: ## Run backend tests
	cd $(API_DIR) && uv run pytest

.PHONY: test-web
test-web: ## Run frontend tests
	cd $(WEB_DIR) && pnpm test --run

.PHONY: lint
lint: ## Lint everything
	cd $(API_DIR) && uv run ruff check .
	cd $(WEB_DIR) && pnpm lint

.PHONY: fmt
fmt: ## Format everything
	cd $(API_DIR) && uv run ruff format .
	cd $(WEB_DIR) && pnpm format

.PHONY: clean
clean: ## Remove caches and build artifacts
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type d -name .pytest_cache -prune -exec rm -rf {} +
	find . -type d -name .ruff_cache -prune -exec rm -rf {} +
	rm -rf $(WEB_DIR)/dist $(WEB_DIR)/.vite
