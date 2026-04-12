BACKEND_DIR := backend
FRONTEND_DIR := frontend

BACKEND_VENV_PYTHON := $(BACKEND_DIR)/.venv/bin/python
BACKEND_VENV_PIP := $(BACKEND_DIR)/.venv/bin/pip
BACKEND_VENV_PYTEST := $(BACKEND_DIR)/.venv/bin/pytest
BACKEND_VENV_UVICORN := $(BACKEND_DIR)/.venv/bin/uvicorn

POSTGRES_DB := forecast_system
POSTGRES_USER := forecast_user
POSTGRES_PASSWORD := forecast_pass
POSTGRES_HOST := localhost
# Override if 5432 is already taken (e.g. local Postgres): export POSTGRES_PORT=5433
POSTGRES_PORT ?= 5432
DATABASE_URL := postgresql+psycopg2://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@$(POSTGRES_HOST):$(POSTGRES_PORT)/$(POSTGRES_DB)
FRONTEND_ORIGIN := http://127.0.0.1:5173
# Override if 8000 is busy: export BACKEND_PORT=8001 (use same value for make frontend-dev)
BACKEND_PORT ?= 8000
API_BASE_URL := http://127.0.0.1:$(BACKEND_PORT)

.PHONY: help \
	db-up db-down \
	backend-venv backend-install backend-run backend-run-debug backend-run-scheduled backend-test backend-coverage backend-test-auth \
	frontend-install frontend-dev frontend-test frontend-build \
	install test coverage

help:
	@echo "Available targets:"
	@echo "  make db-up                Start PostgreSQL with Docker Compose"
	@echo "  make db-down              Stop Docker Compose services"
	@echo "  If db-up fails with port 5432 already allocated: export POSTGRES_PORT=5433"
	@echo "    then use the same POSTGRES_PORT for make backend-run (or export once per shell)."
	@echo "  If backend-run fails with address already in use on 8000: export BACKEND_PORT=8001"
	@echo "    and run frontend with the same BACKEND_PORT (API_BASE_URL tracks it in this Makefile)."
	@echo ""
	@echo "Local signup: add your email to AUTH_SIGNUP_ALLOWLIST before backend-run"
	@echo "  (comma-separated entries, each email:Role — roles CityPlanner | OperationalManager)"
	@echo "  Example: AUTH_SIGNUP_ALLOWLIST='you@example.com:CityPlanner' make backend-run"
	@echo "  See backend/.env.example for a full env template (export vars yourself; app reads the process env)."
	@echo ""
	@echo "  make backend-venv         Create backend virtual environment"
	@echo "  make backend-install      Install backend requirements"
	@echo "  make backend-run          Run backend locally with scheduler disabled"
	@echo "  make backend-run-debug    Run backend locally without reload and with access/debug logs"
	@echo "  make backend-run-scheduled Run backend locally with scheduler enabled"
	@echo "  make backend-test         Run full backend test suite"
	@echo "  make backend-test-auth    Run auth-focused backend tests"
	@echo "  make frontend-install     Install frontend dependencies"
	@echo "  make frontend-dev         Run frontend dev server"
	@echo "  make frontend-test        Run frontend test suite"
	@echo "  make frontend-build       Build frontend"
	@echo "  make install              Install backend and frontend dependencies"
	@echo "  make test                 Run backend and frontend tests"
	@echo "  make coverage             Test with branch coverage"

db-up:
	POSTGRES_PORT=$(POSTGRES_PORT) docker compose up -d postgres

db-down:
	docker compose down

backend-venv:
	cd $(BACKEND_DIR) && python3 -m venv .venv

backend-install:
	cd $(BACKEND_DIR) && .venv/bin/pip install -r requirements.txt

backend-run:
	cd $(BACKEND_DIR) && \
	DATABASE_URL='$(DATABASE_URL)' \
	SCHEDULER_ENABLED=false \
	FRONTEND_ORIGIN='$(FRONTEND_ORIGIN)' \
	AUTH_COOKIE_SECURE=false \
	.venv/bin/uvicorn app.main:app --reload --port $(BACKEND_PORT)

backend-run-debug:
	cd $(BACKEND_DIR) && \
	DATABASE_URL='$(DATABASE_URL)' \
	SCHEDULER_ENABLED=false \
	FRONTEND_ORIGIN='$(FRONTEND_ORIGIN)' \
	AUTH_COOKIE_SECURE=false \
	.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port $(BACKEND_PORT) --log-level debug --access-log

backend-run-scheduled:
	cd $(BACKEND_DIR) && \
	DATABASE_URL='$(DATABASE_URL)' \
	SCHEDULER_ENABLED=true \
	SCHEDULER_CRON='0 0 * * 0' \
	FRONTEND_ORIGIN='$(FRONTEND_ORIGIN)' \
	AUTH_COOKIE_SECURE=false \
	.venv/bin/uvicorn app.main:app --reload --port $(BACKEND_PORT)

backend-test:
	cd $(BACKEND_DIR) && .venv/bin/pytest

backend-test-auth:
	cd $(BACKEND_DIR) && .venv/bin/python -m pytest \
		tests/unit/test_auth_service.py \
		tests/contract/test_auth_api.py \
		tests/unit/test_auth_roles.py \
		tests/unit/test_core_misc.py

backend-coverage:
	cd $(BACKEND_DIR) && .venv/bin/pytest --cov=app --cov-branch --cov-report=term-missing

frontend-install:
	cd $(FRONTEND_DIR) && npm install

frontend-dev:
	cd $(FRONTEND_DIR) && VITE_API_BASE_URL='$(API_BASE_URL)' npm run dev

frontend-test:
	cd $(FRONTEND_DIR) && npm test

frontend-build:
	cd $(FRONTEND_DIR) && VITE_API_BASE_URL='$(API_BASE_URL)' npm run build

install: backend-install frontend-install

test: backend-test frontend-test

# Lab-style aggregate: run from repo root after feature work (backend branch coverage).
coverage: backend-coverage
