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
- Python 3.11 + FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, APScheduler-compatible scheduling, structured logging, pandas-compatible feature preparation utilities, LightGBM, dedicated Government of Canada MSC GeoMet client or ingestion modules, dedicated Nager.Date Canada API client or ingestion modules (004-weekly-demand-forecast)
- PostgreSQL for reused UC-01 and UC-02 lineage plus weekly forecast runs, weekly forecast versions, daily forecast buckets, current weekly forecast marker, and migration-managed schema history (004-weekly-demand-forecast)
- Python 3.11 for backend services and TypeScript for the React frontend + FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, structured logging, React, TypeScript, Tailwind CSS, shared typed API/domain models, and a reusable chart-rendering layer for forecast curves and bands (005-uc-05-visualize)
- PostgreSQL for reused UC-01 through UC-04 lineage plus visualization load records, fallback visualization snapshots, and migration-managed schema history (005-uc-05-visualize)
- Python 3.11 + FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, APScheduler-compatible scheduling, structured logging, pandas-compatible evaluation utilities, LightGBM-produced forecast lineage from UC-03 and UC-04, and dedicated baseline-evaluation service modules (006-evaluate-forecast-baselines)
- PostgreSQL for reused UC-01 through UC-04 lineage plus evaluation runs, retained evaluation results, segmented metric records, current evaluation markers, and migration-managed schema history (006-evaluate-forecast-baselines)
- Python 3.11 for backend services and TypeScript for the React frontend + FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, structured logging, React, TypeScript, Tailwind CSS, shared typed API/domain models, and a reusable historical-data visualization layer for charts and tables (007-historical-demand-exploration)
- PostgreSQL for reused UC-01 and UC-02 lineage plus historical analysis outcome records, saved filter context, and migration-managed schema history (007-historical-demand-exploration)
- Python 3.11 for backend services and TypeScript for the React frontend + FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, structured logging, React, TypeScript, Tailwind CSS, shared typed API/domain models, and reusable comparison-chart and tabular visualization modules (008-compare-demand-forecasts)
- PostgreSQL for reused UC-01 through UC-04 lineage plus retained comparison-request, comparison-result, missing-combination, and comparison-outcome records with migration-managed schema history (008-compare-demand-forecasts)
- Python 3.11 for backend services and TypeScript for the React frontend + FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, structured logging, React, TypeScript, Tailwind CSS, shared typed API/domain models, dedicated Government of Canada MSC GeoMet client or ingestion modules, and a reusable chart-overlay rendering layer (009-add-weather-overlay)
- PostgreSQL for reused approved Edmonton 311 lineage and forecast explorer source state; structured operational logs for overlay retrieval, alignment, supersession, and render outcomes; no separate weather-overlay activation store required (009-add-weather-overlay)
- Python 3.11 backend services and TypeScript React frontend + FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, structured logging, React, TypeScript, Tailwind CSS, Government of Canada MSC GeoMet client modules (009-add-weather-overlay)
- PostgreSQL for forecast explorer lineage reuse and structured overlay operational logs; no separate overlay activation store (009-add-weather-overlay)
- Python 3.11 backend services and TypeScript React frontend + FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, APScheduler-compatible scheduling, structured logging, JWT authentication, role-based authorization dependencies (010-demand-threshold-alerts)
- PostgreSQL for threshold configuration, evaluation runs, per-scope evaluation outcomes, notification events, channel delivery attempts, and active threshold-state tracking (010-demand-threshold-alerts)
- PostgreSQL for threshold configuration, evaluation runs, per-scope evaluation outcomes, threshold state, notification events, and channel-attempt records (010-demand-threshold-alerts)

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
- 010-demand-threshold-alerts: Added Python 3.11 backend services and TypeScript React frontend + FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, APScheduler-compatible scheduling, structured logging, JWT authentication, role-based authorization dependencies
- 010-demand-threshold-alerts: Added Python 3.11 backend services and TypeScript React frontend + FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, APScheduler-compatible scheduling, structured logging, JWT authentication, role-based authorization dependencies
- 009-add-weather-overlay: Added Python 3.11 backend services and TypeScript React frontend + FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, structured logging, React, TypeScript, Tailwind CSS, Government of Canada MSC GeoMet client modules


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
