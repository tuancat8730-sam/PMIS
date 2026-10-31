.PHONY: up down api-install api-test api-lint api-migrate create-admin seed-projects web-install web-lint web-build web-test

API_DIR := apps/api
WEB_DIR := apps/web
API_BIN := $(API_DIR)/.venv/bin
TEST_DATABASE_URL ?= postgresql+asyncpg://pmis:pmis@localhost:5432/pmis_test

up:
	docker compose up --build

down:
	docker compose down

api-install:
	cd $(API_DIR) && python3.12 -m venv .venv && ./.venv/bin/pip install -e ".[dev]"

api-test:
	cd $(API_DIR) && TEST_DATABASE_URL=$(TEST_DATABASE_URL) ./.venv/bin/pytest --cov

api-lint:
	cd $(API_DIR) && ./.venv/bin/ruff check . && ./.venv/bin/ruff format --check .

api-migrate:
	cd $(API_DIR) && ./.venv/bin/alembic upgrade head

create-admin:
	cd $(API_DIR) && ./.venv/bin/python -m app.cli create-admin --email $(EMAIL) --name "$(NAME)"

seed-projects:
	cd $(API_DIR) && ./.venv/bin/python -m app.db.seed_real_projects

web-install:
	cd $(WEB_DIR) && pnpm install

web-lint:
	cd $(WEB_DIR) && pnpm lint

web-build:
	cd $(WEB_DIR) && pnpm build

web-test:
	cd $(WEB_DIR) && pnpm test
