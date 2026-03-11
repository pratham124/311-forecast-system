# 311-forecast-system Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-11

## Active Technologies
- PostgreSQL for ingestion runs, successful-pull cursor state, candidate-to-stored dataset version lifecycle, current dataset marker, and failure notification records (001-pull-311-data)

- Python 3.11 + FastAPI, Pydantic, SQLAlchemy or SQLModel-compatible PostgreSQL access layer, HTTP client for Socrata ingestion, APScheduler-compatible scheduling, structured logging (001-pull-311-data)

## Project Structure

```text
backend/
frontend/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11: Follow standard conventions

## Recent Changes
- 001-pull-311-data: Added Python 3.11 + FastAPI, Pydantic, SQLAlchemy or SQLModel-compatible PostgreSQL access layer, HTTP client for Socrata ingestion, APScheduler-compatible scheduling, structured logging

- 001-pull-311-data: Added Python 3.11 + FastAPI, Pydantic, SQLAlchemy or SQLModel-compatible PostgreSQL access layer, HTTP client for Socrata ingestion, APScheduler-compatible scheduling, structured logging

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
