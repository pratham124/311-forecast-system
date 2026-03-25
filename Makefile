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
POSTGRES_PORT := 5432
DATABASE_URL := postgresql+psycopg2://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@$(POSTGRES_HOST):$(POSTGRES_PORT)/$(POSTGRES_DB)
FRONTEND_ORIGIN := http://127.0.0.1:5173
API_BASE_URL := http://127.0.0.1:8000

.PHONY: help \
	db-up db-down \
	backend-venv backend-install backend-run backend-run-debug backend-run-scheduled backend-test backend-coverage backend-test-auth \
	frontend-install frontend-dev frontend-test frontend-build \
	install test

help:
	@echo "Available targets:"
	@echo "  make db-up                Start PostgreSQL with Docker Compose"
	@echo "  make db-down              Stop Docker Compose services"
	@echo "  make backend-venv         Create backend virtual environment"
	@echo "  make backend-install      Install backend requirements"
	@echo "  make backend-run          Run backend locally with scheduler disabled"
	@echo "  make backend-run-debug    Run backend locally without reload and with access/debug logs"
	@echo "  make backend-run-scheduled Run backend locally with scheduler enabled"
	@echo "  make backend-test         Run full backend test suite"
	@echo "  make backend-test-auth    Run auth-focused backend tests"
	@echo "  make backend-coverage     Run backend coverage"
	@echo "  make frontend-install     Install frontend dependencies"
	@echo "  make frontend-dev         Run frontend dev server"
	@echo "  make frontend-test        Run frontend test suite"
	@echo "  make frontend-build       Build frontend"
	@echo "  make install              Install backend and frontend dependencies"
	@echo "  make test                 Run backend and frontend tests"

db-up:
	docker compose up -d postgres

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
	.venv/bin/uvicorn app.main:app --reload

backend-run-debug:
	cd $(BACKEND_DIR) && \
	DATABASE_URL='$(DATABASE_URL)' \
	SCHEDULER_ENABLED=false \
	FRONTEND_ORIGIN='$(FRONTEND_ORIGIN)' \
	AUTH_COOKIE_SECURE=false \
	.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level debug --access-log

backend-run-scheduled:
	cd $(BACKEND_DIR) && \
	DATABASE_URL='$(DATABASE_URL)' \
	SCHEDULER_ENABLED=true \
	SCHEDULER_CRON='0 0 * * 0' \
	FRONTEND_ORIGIN='$(FRONTEND_ORIGIN)' \
	AUTH_COOKIE_SECURE=false \
	.venv/bin/uvicorn app.main:app --reload

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
