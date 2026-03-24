# Quickstart: Generate 1-Day Demand Forecast

## Purpose

Use this guide to implement and verify UC-03 with the minimum backend components required by [docs/UC-03-AT.md](/root/311-forecast-system/docs/UC-03-AT.md), while reusing the approved dataset lineage already defined in [data-model.md](/root/311-forecast-system/specs/001-pull-311-data/data-model.md) and [data-model.md](/root/311-forecast-system/specs/002-validate-deduplicate-data/data-model.md).

## Implementation Outline

1. Reuse and extend backend modules for:
   - Approved cleaned dataset lookup from the UC-02 pipeline
   - Auth and authorization dependency layer for all forecast surfaces
   - Dedicated MSC GeoMet weather client or ingestion module
   - Dedicated Nager.Date Canada holiday client or ingestion module
   - Forecast-run repository
   - Forecast feature-preparation service
   - Forecasting pipeline modules for enrichment joins, leakage-free feature assembly, model execution, and hourly bucket materialization
   - Forecasting engine service with one global LightGBM model and baseline comparator support
   - Forecast storage repository
   - Forecast bucket repository
   - Current forecast marker repository
   - Thin API routes for forecast trigger, run status, and current forecast visibility
2. Preserve the shared lineage entities from UC-01 and UC-02:
   - `IngestionRun`
   - `DatasetVersion` for ingested source datasets
   - `ValidationRun`
   - `CleanedDatasetVersion`
   - `CurrentDatasetMarker` or equivalent approved dataset marker
3. Persist the new UC-03 entities:
   - `ForecastRun`
   - `ForecastVersion`
   - `ForecastBucket`
   - `CurrentForecastMarker`
4. Ensure orchestration follows this order:
   - Resolve the currently approved cleaned dataset from UC-02
   - Reject unauthorized, forbidden, and invalid requests before forecast-run creation
   - Start a forecast run
   - Check whether a current forecast already covers the requested 24-hour window
   - Return that current forecast immediately when reuse is valid
   - Prepare forecast features only from the approved cleaned dataset lineage
   - Add weather enrichment only through dedicated MSC GeoMet modules
   - Add holiday enrichment only through dedicated Nager.Date Canada API modules
   - Keep all feature assembly and evaluation windows chronologically safe and leakage-free
   - Execute the one global LightGBM forecast and retained baseline comparator
   - Materialize 24 hourly buckets with service-category output, optional geography slices, and `P10`, `P50`, `P90` quantiles
   - Persist the forecast version and all hourly buckets
   - Update the current forecast marker only after storage succeeds
   - Emit structured logs for success, reused-current, category-only success, and each failure category
   - Return missing-resource responses for unknown run or current-forecast reads
   - Leave the previous active forecast untouched on any failed run

The UC-03 implementation remains a feature-specific 1-day hourly operational forecast and does not replace the constitution's broader default direction of daily next-7-day service-category forecasting.

## Acceptance Alignment

Map implementation and tests directly to these acceptance scenarios:

- `AT-01`: On-demand request generates a new stored 24-hour forecast and marks it current
- `AT-02`: Scheduled generation uses the same workflow and marks the new forecast current
- `AT-03`: Current forecast reuse returns the existing forecast without rerunning the engine
- `AT-04`: Missing approved input data fails the run and preserves the prior active forecast
- `AT-05`: Forecasting engine failure prevents activation and preserves the prior active forecast
- `AT-06`: Incomplete geography still produces a successful category-only forecast
- `AT-07`: Storage failure prevents activation even after forecast generation succeeds
- `AT-08`: No partial activation occurs before the full forecast storage step succeeds

## Suggested Test Layers

- Unit tests for horizon reuse rules, hourly bucket creation, category-versus-geography scope selection, quantile ordering, and activation guards
- Integration tests across approved dataset lookup, GeoMet and Nager.Date enrichment modules, auth-gated trigger and read surfaces, forecast-run persistence, forecast version storage, bucket storage, and current forecast marker updates
- Contract tests for [forecast-api.yaml](/root/311-forecast-system/specs/003-daily-demand-forecast/contracts/forecast-api.yaml)
- Acceptance-style tests that mirror `docs/UC-03-AT.md`

## Exit Conditions

Implementation is ready for task breakdown when:

- The UC-01 and UC-02 lineage entities and the UC-03 forecast entities are clearly linked
- Weather and holiday enrichments are isolated in dedicated MSC GeoMet and Nager.Date modules
- Route handlers stay thin while orchestration remains in services and forecasting pipelines and persistence remains in repositories
- The current forecast marker changes only after a new forecast version and its hourly buckets are stored successfully
- Reused-current responses do not create a new forecast version or invoke the forecasting engine
- The forecasting path retains one global LightGBM model, a baseline comparator, and `P10`, `P50`, `P90` outputs without leakage-prone feature assembly
- Unauthorized, forbidden, missing-resource, and invalid-request responses remain separate from forecast-run outcomes
- Category-only forecasts remain valid when geography is unavailable
- Failed runs never replace the prior active forecast
- Stored forecast versions and failed forecast-run records remain queryable as operational history
- Current forecast read surfaces return the 24 hourly buckets and stored dimension scope required for acceptance verification


## Implementation Notes

- Backend implementation now lives in `backend/app/api/routes/forecasts.py`, `backend/app/services/forecast_service.py`, and the supporting repository/client/pipeline modules added for UC-03.
- GeoMet station selection now defaults to discovering an Edmonton-area hourly station from the GeoMet stations API and then reusing that station's `CLIMATE_IDENTIFIER` for hourly observation requests.
- Forecast persistence is backed by the `003_uc03_daily_forecast` migration in `backend/migrations/versions/003_uc03_daily_forecast.py`.
- Test coverage for UC-03 lives in `backend/tests/unit/test_forecast_pipeline.py`, `backend/tests/contract/test_forecast_api.py`, and the three forecast integration suites.
- Verification command used for this implementation: `.venv/bin/python -m pytest tests/unit/test_forecast_pipeline.py tests/contract/test_forecast_api.py tests/integration/test_forecast_generation.py tests/integration/test_forecast_reuse.py tests/integration/test_forecast_failures.py` from `backend/`.

- GeoMet transport behavior is configurable through `GEOMET_CLIMATE_IDENTIFIER`, `GEOMET_STATION_SELECTOR`, and `GEOMET_TIMEOUT_SECONDS`. The default selector now discovers an Edmonton-area hourly station from the GeoMet stations API and reuses its climate identifier for hourly observation requests.
