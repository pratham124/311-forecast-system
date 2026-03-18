BACKEND_DIR := backend
VENV_PYTHON := $(BACKEND_DIR)/.venv/bin/python
VENV_PIP := $(BACKEND_DIR)/.venv/bin/pip
VENV_PYTEST := $(BACKEND_DIR)/.venv/bin/pytest
VENV_UVICORN := $(BACKEND_DIR)/.venv/bin/uvicorn
BACKEND_VENV_PIP := .venv/bin/pip
BACKEND_VENV_PYTEST := .venv/bin/pytest
BACKEND_VENV_UVICORN := .venv/bin/uvicorn

POSTGRES_DB := forecast_system
POSTGRES_USER := forecast_user
POSTGRES_PASSWORD := forecast_pass
POSTGRES_HOST := localhost
POSTGRES_PORT := 5432
DATABASE_URL := postgresql+psycopg2://$(POSTGRES_USER):$(POSTGRES_PASSWORD)@$(POSTGRES_HOST):$(POSTGRES_PORT)/$(POSTGRES_DB)

.PHONY: help db-up db-down venv install run run-scheduled test coverage

help:
	@echo "Available targets:"
	@echo "  make db-up           Start PostgreSQL with Docker Compose"
	@echo "  make db-down         Stop PostgreSQL with Docker Compose"
	@echo "  make venv            Create backend virtual environment"
	@echo "  make install         Install backend requirements into the virtual environment"
	@echo "  make run             Run backend locally with scheduler disabled"
	@echo "  make run-scheduled   Run backend locally with scheduler enabled"
	@echo "  make test            Run backend test suite"
	@echo "  make coverage        Run backend branch coverage"

db-up:
	docker compose up -d postgres

db-down:
	docker compose down

venv:
	cd $(BACKEND_DIR) && python3 -m venv .venv

install:
	cd $(BACKEND_DIR) && $(BACKEND_VENV_PIP) install -r requirements.txt

run:
	cd $(BACKEND_DIR) && \
	DATABASE_URL='$(DATABASE_URL)' \
	SCHEDULER_ENABLED=false \
	$(BACKEND_VENV_UVICORN) app.main:app --reload

run-scheduled:
	cd $(BACKEND_DIR) && \
	DATABASE_URL='$(DATABASE_URL)' \
	SCHEDULER_ENABLED=true \
	SCHEDULER_CRON='0 0 * * 0' \
	$(BACKEND_VENV_UVICORN) app.main:app --reload

test:
	cd $(BACKEND_DIR) && $(BACKEND_VENV_PYTEST)

coverage:
	cd $(BACKEND_DIR) && $(BACKEND_VENV_PYTEST) --cov=app --cov-branch --cov-report=term-missing
