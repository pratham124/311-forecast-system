# Implementation Plan: Compare Demand and Forecasts Across Categories and Geographies

**Branch**: `008-compare-demand-forecasts` | **Date**: 2026-03-13 | **Spec**: [spec.md](/root/311-forecast-system/specs/008-compare-demand-forecasts/spec.md)
**Input**: Feature specification from `/specs/008-compare-demand-forecasts/spec.md`

## Summary

Implement UC-08 as a planner-facing comparison workflow that reuses approved historical-demand lineage from UC-02 and active forecast lineage from UC-03 or UC-04 to compare historical and forecast demand across selected service categories, optional geographic areas, and a continuous time range. The implementation must stay congruent with [UC-08](/root/311-forecast-system/docs/UC-08.md) and [UC-08-AT](/root/311-forecast-system/docs/UC-08-AT.md), apply one deterministic rule for forecast source selection, apply one deterministic rule for allowable comparison granularity, use one consistent outcome vocabulary across comparison execution and persisted outcome records, and expose `render_failed` only through the render-event path rather than the initial comparison-execution response.

## Technical Context

**Language/Version**: Python 3.11 for backend services and TypeScript for the React frontend  
**Primary Dependencies**: FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, structured logging, React, TypeScript, Tailwind CSS, shared typed API/domain models, and reusable comparison-chart and tabular visualization modules  
**Storage**: PostgreSQL for reused UC-01 through UC-04 lineage plus retained comparison-request, comparison-result, missing-combination, and comparison-outcome records with migration-managed schema history  
**Testing**: pytest for backend unit, integration, contract, and acceptance coverage plus frontend component and interaction tests aligned to `docs/UC-08-AT.md`  
**Target Platform**: Linux-hosted backend API with a browser-based React analysis interface for City Planners  
**Project Type**: web application with backend API and typed frontend comparison interface  
**Performance Goals**: For requests within the normal request size threshold, 95% of requests must show a terminal result, partial-result, or explicit error outcome within 10 seconds, measured from request submission until the first terminal outcome is displayed; 100% of requests over the high-volume threshold must warn before retrieval begins  
**Constraints**: Must satisfy `docs/UC-08.md` and `docs/UC-08-AT.md`; must reuse approved cleaned historical lineage from UC-02 and active forecast lineage from UC-03 or UC-04 rather than creating a separate forecast product; must keep FastAPI routes thin, business logic in services, persistence in repositories, and frontend rendering in typed feature modules; must use `daily_1_day` only for active UC-03 forecast lineage with hourly source granularity and `weekly_7_day` only for active UC-04 forecast lineage with daily source granularity; must select `daily_1_day` whenever both active forecast products could satisfy the same selected range, and fall back to `weekly_7_day` only when `daily_1_day` cannot satisfy that range but `weekly_7_day` can; must distinguish missing-data states from explicit `historical_retrieval_failed`, `forecast_retrieval_failed`, and `alignment_failed` outcomes; must expose `render_failed` only through the render-event surface and persisted comparison outcomes; must require authenticated access for context retrieval, comparison execution, and render-outcome reporting; must accept render events only from the authenticated session that owns the executed comparison request or an equivalently authorized backend component; must not expose raw source rows, secrets, or unstable upstream shapes directly to the frontend  
**Scale/Scope**: One comparison-analysis interface, one typed comparison request/response contract, one render-outcome reporting surface, support for multi-category and optional multi-geography comparison requests, retained request and outcome history, and acceptance coverage for `warning_required`, `success`, `historical_only`, `forecast_only`, `partial_forecast_missing`, `historical_retrieval_failed`, `forecast_retrieval_failed`, `alignment_failed`, and render-event-driven `render_failed`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Use-case traceability**: PASS. The plan remains explicitly tied to [UC-08](/root/311-forecast-system/docs/UC-08.md) and [UC-08-AT](/root/311-forecast-system/docs/UC-08-AT.md), and it keeps the mixed-availability behavior marked as a clarified extension rather than an explicit use-case alternative flow.
- **Canonical data-source usage**: PASS. Historical demand remains sourced from the approved UC-02 cleaned dataset lineage, and forecast demand remains sourced from active UC-03 or UC-04 forecast lineage rather than any new forecast store.
- **Layered backend architecture**: PASS. Retrieval orchestration, forecast source resolution, warning rules, alignment, and comparison assembly stay in backend services and repositories, while route handlers remain transport-only.
- **Typed frontend modularity and secure access**: PASS. The comparison interface stays in a typed React frontend that consumes normalized backend contracts only, with backend-enforced authenticated access and no direct client access to persistence or third-party APIs.
- **Operational safety / last-known-good and clarity guarantees**: PASS. Retrieval failures, alignment failures, and render failures produce explicit logged error states; missing-data states remain explicit and non-misleading; upstream current dataset and current forecast markers are read-only dependencies for this feature.
- **Forecasting and geography constraints**: PASS. UC-08 does not create or activate new forecasts; it compares against already active `daily_1_day` or `weekly_7_day` forecast products and only uses geographies that can be aligned reliably with the available forecast scope.

**Post-Design Check**: PASS. The research, data model, quickstart, and API contract keep UC-08 within the existing historical and forecast lineage, preserve deterministic source-selection and granularity rules, maintain one consistent comparison-execution outcome vocabulary, and carry the render-event security expectation through design.

## Project Structure

### Documentation (this feature)

```text
specs/008-compare-demand-forecasts/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── demand-comparison-api.yaml
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   └── routes/
│   ├── core/
│   ├── repositories/
│   ├── schemas/
│   └── services/
└── tests/
    ├── contract/
    ├── integration/
    └── unit/

frontend/
└── src/
    ├── api/
    ├── components/
    ├── features/
    ├── hooks/
    ├── pages/
    ├── types/
    └── utils/
```

**Structure Decision**: Use the repository’s intended backend/frontend split because UC-08 includes both a typed backend comparison contract and a planner-facing frontend comparison interface. This repository does not yet contain those source directories, so Phase 2 work will create them using the structure above rather than adapting an existing implementation tree.

## Phase 0 Research Summary

- Confirmed UC-08 must reuse approved historical-demand lineage from UC-02 and current forecast lineage from UC-03 or UC-04 instead of introducing a comparison-specific forecast source.
- Confirmed comparison execution must distinguish no matching data from explicit `historical_retrieval_failed` and `forecast_retrieval_failed` outcomes.
- Confirmed `render_failed` is a post-response outcome recorded through the render-event surface, not a comparison-execution response state.
- Confirmed `daily_1_day` is the reused UC-03 forecast product with hourly source granularity and `weekly_7_day` is the reused UC-04 forecast product with daily source granularity.
- Confirmed the deterministic source-selection rule is: choose `daily_1_day` whenever its active horizon fully covers the selected range; otherwise choose `weekly_7_day` when its active horizon fully covers the selected range; otherwise no forecast source is available for that request.
- Confirmed the deterministic comparison-granularity rule is: `hourly` only with `daily_1_day`; `weekly` only with `weekly_7_day`; `daily` only when the selected forecast source and historical data can both align to calendar-day buckets across the selected range.
- Confirmed render-outcome reporting must be accepted only from the authenticated session that owns the executed comparison request or an equivalently authorized backend component.

## Phase 1 Design Summary

- Reuse UC-01 through UC-04 lineage entities as read-only inputs and add only UC-08-specific records for comparison requests, assembled comparison results, missing-combination annotations, and terminal outcome records.
- Resolve forecast source deterministically with daily precedence over weekly whenever both active forecast products cover the selected range.
- Keep comparison-execution response outcomes limited to `warning_required`, `success`, `historical_only`, `forecast_only`, `partial_forecast_missing`, `historical_retrieval_failed`, `forecast_retrieval_failed`, and `alignment_failed`.
- Keep `render_failed` outside the comparison-execution response contract and record it only through the separate render-event surface and persisted outcome history.
- Encode contract dependencies structurally so `forecastProduct`, `forecastGranularity`, `sourceForecastVersionId`, `sourceWeeklyForecastVersionId`, and allowable `comparisonGranularity` combinations are explicit rather than descriptive only.

## Implementation Steps

1. **Resolve canonical comparison inputs**
   - Read the approved cleaned dataset marker from UC-02 as the historical comparison source.
   - Resolve `daily_1_day` from the current UC-03 forecast marker when the selected range is fully covered by the active hourly forecast horizon.
   - Resolve `weekly_7_day` only when `daily_1_day` does not fully cover the selected range and the selected range is fully covered by the active UC-04 weekly horizon.
   - If neither active forecast product fully covers the selected range, treat forecast data as unavailable rather than inventing a partial forecast source.

2. **Resolve comparison granularity from source compatibility**
   - Allow `hourly` comparison normalization only when `daily_1_day` is the selected forecast product and historical data can align to hourly buckets across the full selected range.
   - Allow `daily` comparison normalization only when the selected forecast product and historical data can both align to calendar-day buckets across the full selected range.
   - Allow `weekly` comparison normalization only when `weekly_7_day` is the selected forecast product and both historical and forecast data can align to calendar-week buckets across the selected range.
   - Return `alignment_failed` when the selected forecast source and historical data cannot produce one valid common comparison granularity.

3. **Gate comparison access through backend-authenticated contracts**
   - Require authenticated backend access for comparison context, comparison execution, and render-outcome reporting.
   - Keep authorization checks in backend dependencies and services.
   - Accept render events only from the authenticated session associated with the executed comparison request or an equivalently authorized backend component.

4. **Assemble normalized comparison responses in backend services**
   - Build one comparison service that accepts category, optional geography, and time-range filters.
   - Retrieve matching historical demand and forecast demand through repository or service boundaries.
   - Normalize both datasets onto one comparison axis before response assembly.
   - Keep FastAPI routes limited to HTTP concerns and typed schema mapping.

5. **Preserve warning and missing-data behavior from UC-08**
   - Detect high-volume requests before historical or forecast retrieval begins using the spec-defined threshold.
   - Return `warning_required` until the planner explicitly proceeds.
   - Return `forecast_only` when no historical data matches but forecast data is available from the selected forecast source.
   - Return `historical_only` when no forecast data matches for the selected range after deterministic forecast source selection.
   - Return `partial_forecast_missing` only for the clarified mixed-availability extension path.

6. **Separate missing data from failure outcomes**
   - Return `historical_retrieval_failed` only when historical retrieval errors rather than yielding no matches.
   - Return `forecast_retrieval_failed` only when forecast retrieval errors rather than yielding no matches.
   - Return `alignment_failed` when a valid common comparison basis cannot be established after both retrievals succeed.
   - Record `render_failed` only when the client later reports a failed render for a completed comparison request.

7. **Persist comparison-specific operational records**
   - Record one comparison request per executed retrieval attempt, including filters, warning status, resolved forecast source, resolved forecast granularity, and terminal outcome.
   - Persist normalized result metadata only for successful or partial-result comparison outcomes.
   - Persist missing-combination annotations only when the clarified mixed-availability extension is exercised.
   - Keep outcome history queryable without mutating upstream dataset, forecast, or visualization records.

8. **Bound observability and contract surfaces**
   - Provide one context endpoint for categories and geography options, one comparison execution endpoint, and one render-outcome reporting endpoint.
   - Limit the comparison execution response to the documented query-time outcome vocabulary.
   - Emit structured logs for request lifecycle transitions, high-volume warnings, missing-data outcomes, retrieval failures, alignment failures, and render outcomes.
   - Use the render-event contract to record `rendered` or `render_failed` after the comparison response has already been returned.
   - Never expose raw source payloads, secrets, unstable third-party formats, or upstream table shapes directly.

9. **Verify acceptance behavior**
   - Validate successful comparison retrieval and presentation against `docs/UC-08-AT.md`.
   - Validate high-volume warnings, forecast-only behavior, historical-only behavior, `historical_retrieval_failed`, `forecast_retrieval_failed`, and `alignment_failed` against the matching acceptance tests.
   - Validate render-failure logging through the render-event flow and mixed-availability behavior separately so it stays distinguishable from explicit UC-08 alternative flows.
   - Validate the 10-second normal-threshold timing target with explicit comparison-execution instrumentation and verification.
   - Run planner-facing usability validation for the core multi-category and multi-geography comparison workflow and retain the outcome record for `SC-001`.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations or justified exceptions were required for this feature.
