# Implementation Plan: View Forecast Accuracy and Compare Predictions to Actuals

**Branch**: `014-uc-14-forecast-accuracy` | **Date**: 2026-03-13 | **Spec**: [spec.md](/Users/sahmed/Documents/311-forecast-system/specs/014-uc-14-forecast-accuracy/spec.md)
**Input**: Feature specification from `/specs/014-uc-14-forecast-accuracy/spec.md`

## Summary

Implement UC-14 as an authenticated forecast-performance analysis flow that lets authorized city planners load a default last-30-completed-days comparison scope, retrieve retained historical daily forecast outputs and matching actual demand, reuse precomputed MAE/RMSE/MAPE metrics from the evaluation lineage when available, compute those metrics on demand when they are missing, align forecast and actual values on safe common buckets, and render a typed comparison payload that supports full results, comparisons without metrics, and explicit unavailable or error states with traceable operational outcomes.

## Technical Context

**Language/Version**: Python 3.11 backend services and TypeScript React frontend
**Primary Dependencies**: FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, structured logging, React, TypeScript, Tailwind CSS, shared typed API or domain models, JWT authentication, role-based authorization dependencies
**Storage**: PostgreSQL for reused UC-01 through UC-13 lineage plus UC-14 request observability, metric-resolution outcomes, prepared accuracy views, aligned bucket records, and render-event reporting
**Testing**: pytest for backend unit, integration, and contract coverage, frontend interaction tests for default load, scoped retrieval, metrics-present, metrics-missing, unavailable, and render-failure states, and acceptance tests aligned to [UC-14-AT.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-14-AT.md)
**Target Platform**: Linux-hosted web application with FastAPI backend and React frontend
**Project Type**: Web application with backend API plus typed frontend
**Performance Goals**: Return the default analysis view quickly enough for interactive use, complete alignment for the selected scope in one request, and preserve explicit traceability for metric fallback and render outcomes
**Constraints**: Only authenticated and authorized users may access forecast-performance data; default scope is the last 30 completed days; comparisons must align forecast and actual values to matching periods only; MAE, RMSE, and MAPE shown in the UI must correspond to the same scope and window as the displayed comparison; missing forecasts or missing actuals must produce unavailable or error states rather than partial misleading output; render failures must remain observable without corrupting the prepared comparison result
**Scale/Scope**: Planner-facing review of retained historical forecast quality across service-category and optional geography scopes, reusing evaluation lineage from UC-06 and visualization conventions from UC-05 without changing how forecasts are generated in UC-03

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- `PASS`: Use-case traceability is preserved. The plan remains bounded to [UC-14.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-14.md), [UC-14-AT.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-14-AT.md), and the clarified spec requirements already captured in UC-14.
- `PASS`: Canonical lineage reuse is preserved. UC-14 consumes upstream forecast, actual, evaluation, and visualization lineage from UC-01 through UC-13 instead of redefining those entities.
- `PASS`: Layered backend architecture is preserved. Route handlers remain thin; scope resolution, source selection, metric fallback, alignment, prepared-view assembly, and observability remain in services and repositories.
- `PASS`: Typed contract coverage is preserved. The API contract uses one canonical view-status vocabulary and one canonical metric-status vocabulary across retrieval and render-outcome reporting.
- `PASS`: Security coverage is preserved. Forecast-performance endpoints remain authenticated and role-aware, consistent with the constitution and the use case.
- `PASS`: Operational safety is preserved. Missing forecast data, missing actuals, metric fallback, alignment refusal, and render failure remain first-class observable outcomes rather than implicit empty views.
- `PASS`: No constitution waiver is required. The design stays within the required Python/FastAPI/PostgreSQL backend and React TypeScript frontend architecture.

## Phase 0 Research Decisions

- Reuse retained evaluation lineage from UC-06 as the primary source for MAE, RMSE, and MAPE before attempting on-demand computation.
- Resolve the default planner scope to the last 30 completed days rather than including the current partial day.
- Align only overlapping forecast and actual buckets and reject non-overlapping or unsafe comparisons instead of coercing mismatched periods.
- Persist one request-scoped prepared comparison result so retrieval, metric fallback, and render outcomes can be correlated for the same planner action.
- Report final client render outcomes separately from server-side preparation so chart-library failures are observable without losing the prepared result context.
- Keep UC-14 limited to viewing and comparing forecast performance; forecast generation, retained evaluation production, and active forecast activation remain owned by earlier use cases.

## Project Structure

### Documentation (this feature)

```text
specs/014-uc-14-forecast-accuracy/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── forecast-accuracy-api.yaml
└── spec.md
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   ├── services/
│   ├── repositories/
│   ├── models/
│   ├── clients/
│   └── core/
└── tests/

frontend/
├── src/
│   ├── api/
│   ├── components/
│   ├── features/
│   ├── hooks/
│   ├── pages/
│   ├── types/
│   └── utils/
└── tests/

tests/
├── contract/
├── integration/
└── unit/
```

**Structure Decision**: Use the existing FastAPI backend and React frontend split. Forecast-performance retrieval belongs in backend services and repositories rather than in scheduled pipelines because UC-14 is an interactive analysis workflow. The frontend remains a typed consumer of the normalized comparison payload and reports the final render outcome through a separate authenticated endpoint.

## Phase 1 Design

### Data Model Direction

- Reuse UC-01 through UC-13 entities and vocabularies without redefining them in UC-14, especially forecast lineage from UC-03, actual-demand lineage from UC-02, evaluation metrics from UC-06, comparison alignment semantics from UC-08, observability conventions from UC-12, and authenticated access patterns from UC-10 through UC-13.
- `ForecastAccuracyRequest` records one planner-initiated analysis request with the resolved scope, source lineage, and terminal retrieval status.
- `ForecastAccuracyMetricResolution` records whether MAE, RMSE, and MAPE came from retained UC-06 evaluation results, on-demand computation, or remained unavailable for the request.
- `ForecastAccuracyComparisonResult` stores the prepared normalized output for one request, including view status and metric availability status.
- `ForecastAccuracyAlignedBucket` stores one aligned forecast-versus-actual comparison bucket inside a prepared result.
- `ForecastAccuracyRenderEvent` records the final client render outcome for a prepared request so chart or table failures remain traceable.

### Service Direction

- `ForecastAccuracyQueryService` resolves the default or requested scope, selects the correct retained historical daily-forecast source, loads corresponding actual demand, and assembles a planner-ready view.
- `ForecastAccuracyMetricService` first attempts to resolve canonical MAE/RMSE/MAPE from retained UC-06 evaluation lineage and falls back to on-demand computation only when that retained metric set is unavailable for the exact scope and time window.
- `ForecastAccuracyAlignmentService` aligns forecast and actual values on matching buckets only and rejects unsafe or empty overlap rather than producing misleading comparisons.
- `ForecastAccuracyObservabilityService` records request lifecycle, metric fallback decisions, prepared-result status, and final render outcomes under one correlation context.

### API Contract Direction

- `GET /api/v1/forecast-accuracy` returns one normalized forecast-performance view for the default last-30-completed-days scope or an explicitly selected scope.
- `POST /api/v1/forecast-accuracy/{forecastAccuracyRequestId}/render-events` records whether the client render succeeded or failed after a prepared response was delivered.
- Successful retrieval with available metrics returns aligned comparison buckets plus MAE, RMSE, and MAPE in one typed response.
- Successful retrieval without metrics returns aligned comparison buckets plus explicit metric-unavailable messaging.
- Missing historical forecasts, missing actuals, or unsafe alignment returns a typed unavailable or error response instead of partial misleading comparison data.
- All endpoints require authenticated planner access with backend authorization checks; there is no anonymous or public forecast-performance surface.

### Implementation Notes

- The default request window must resolve to the last 30 completed days in the application timezone and exclude the current partial day.
- Historical forecast retrieval must use retained daily forecast versions and buckets that correspond to realized periods, not the currently active future-only forecast pointer unless it also represents the requested historical window.
- Metric reuse prefers retained UC-06 evaluation results only when the scope, granularity, and time window match the comparison shown to the planner; otherwise on-demand computation is required.
- When forecasts and actuals overlap only partially, UC-14 compares only the matching buckets and records any excluded non-overlapping buckets in request observability rather than shifting timestamps.
- If forecasts and actuals are available but both retained metrics retrieval and on-demand computation fail, the prepared result remains valid with `metrics_unavailable` semantics and explicit UI messaging.
- If forecasts are missing, actuals are missing, or overlap is empty, UC-14 must not produce comparison buckets and must return an unavailable or error status.
- A render-failure report must not delete or mutate the already prepared comparison result; it augments observability for the same request.

## Post-Design Constitution Check

- `PASS`: Design artifacts preserve UC-14 and UC-14-AT traceability and keep default-scope loading, exact-bucket alignment, metric fallback, and explicit failure handling concrete.
- `PASS`: Forecast accuracy remains downstream of canonical forecast, actual, and evaluation lineage from UC-01 through UC-13 and does not duplicate shared source-of-truth entities.
- `PASS`: Route handlers are limited to typed API concerns; scope resolution, metric fallback, alignment, prepared-result assembly, and observability remain isolated in service and repository layers.
- `PASS`: The design covers authentication, role-aware access, stable contract vocabulary, and explicit render-failure observability required by the constitution.
- `PASS`: Operational safety is preserved because missing inputs, alignment refusal, metric fallback failure, and render failure all produce explicit, traceable outcomes.

## Complexity Tracking

No constitution violations or complexity exemptions are required.
