# 311-forecast-system Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-11

## Active Technologies
- PostgreSQL for ingestion runs, successful-pull cursor state, candidate-to-stored dataset version lifecycle, current dataset marker, and failure notification records (001-pull-311-data)
- Python 3.11 + FastAPI, Pydantic, SQLAlchemy or SQLModel-compatible PostgreSQL access layer, HTTP client for Socrata ingestion, APScheduler-compatible scheduling, JWT authentication support, role-based authorization dependencies, structured logging (001-pull-311-data)
- PostgreSQL for ingestion runs, successful-pull cursor state, candidate-to-stored dataset version lifecycle, current dataset marker, failure notification records, and migration-managed schema state (001-pull-311-data)
- PostgreSQL for UC-01 ingestion state plus validation runs, duplicate-analysis outcomes, cleaned dataset versions, review-needed outcomes, and the approved dataset marker shared with earlier specs (002-validate-deduplicate-data)
- PostgreSQL for UC-01 ingestion state plus validation runs, validation outcomes, duplicate-analysis outcomes, cleaned dataset versions, operational status records, and the approval marker that points to the active cleaned dataset version (002-validate-deduplicate-data)
- Python 3.11 + FastAPI, Pydantic, SQLAlchemy-compatible PostgreSQL access layer, APScheduler-compatible scheduling, JWT authentication support, role-based authorization dependencies, structured logging, pandas-compatible feature preparation utilities, LightGBM for the primary forecast model (003-daily-demand-forecast)
- PostgreSQL for reused UC-01 and UC-02 lineage state plus forecast runs, forecast versions, hourly forecast buckets, current forecast marker state, and migration-managed schema history (003-daily-demand-forecast)
- PostgreSQL for reused UC-01 and UC-02 lineage state plus retained forecast runs, retained forecast versions, hourly forecast buckets, current forecast marker state, and migration-managed schema history (003-daily-demand-forecast)
- Python 3.11 + FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, APScheduler-compatible scheduling, JWT authentication support, role-based authorization dependencies, structured logging, pandas-compatible feature preparation utilities, LightGBM, dedicated Government of Canada MSC GeoMet client or ingestion modules, dedicated Nager.Date Canada API client or ingestion modules (003-daily-demand-forecast)
- PostgreSQL for reused UC-01 and UC-02 lineage state plus forecast runs, retained forecast versions, hourly forecast buckets, current forecast marker state, and migration-managed schema history (003-daily-demand-forecast)

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
- 003-daily-demand-forecast: Added Python 3.11 + FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, APScheduler-compatible scheduling, JWT authentication support, role-based authorization dependencies, structured logging, pandas-compatible feature preparation utilities, LightGBM, dedicated Government of Canada MSC GeoMet client or ingestion modules, dedicated Nager.Date Canada API client or ingestion modules
- 003-daily-demand-forecast: Added Python 3.11 + FastAPI, Pydantic, SQLAlchemy-compatible PostgreSQL access layer, APScheduler-compatible scheduling, JWT authentication support, role-based authorization dependencies, structured logging, pandas-compatible feature preparation utilities, LightGBM for the primary forecast model
- 003-daily-demand-forecast: Added Python 3.11 + FastAPI, Pydantic, SQLAlchemy-compatible PostgreSQL access layer, APScheduler-compatible scheduling, JWT authentication support, role-based authorization dependencies, structured logging, pandas-compatible feature preparation utilities, LightGBM for the primary forecast model


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
