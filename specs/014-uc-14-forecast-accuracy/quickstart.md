# Quickstart: View Forecast Accuracy and Compare Predictions to Actuals

## Purpose

Use this guide to implement and verify UC-14 as an authenticated planner workflow that loads a forecast-performance view for the default last 30 completed days or a selected scope, retrieves retained historical forecasts and matching actual demand, resolves MAE/RMSE/MAPE from retained evaluation lineage or on-demand computation, aligns comparison buckets safely, and reports explicit rendered, metrics-unavailable, unavailable, or error outcomes.

## Implementation Outline

1. Reuse shared lineage and vocabulary from prior use cases without redefining those entities:
   - UC-02 approved actual-demand lineage
   - UC-03 and UC-04 retained historical forecast lineage
   - UC-05 visualization-ready payload conventions
   - UC-06 evaluation metric lineage for MAE, RMSE, and MAPE
   - UC-08 comparison alignment semantics
   - UC-12 observability and render-outcome reporting conventions
   - shared authentication, authorization, and structured logging conventions used across the platform
2. Add only UC-14-specific persistence:
   - `ForecastAccuracyRequest`
   - `ForecastAccuracyMetricResolution`
   - `ForecastAccuracyComparisonResult`
   - `ForecastAccuracyAlignedBucket`
   - `ForecastAccuracyRenderEvent`
3. Build one backend forecast-accuracy path that:
   - resolves the default last-30-completed-days scope when the caller does not override it
   - loads retained historical forecasts for the selected scope
   - loads approved actual demand for the same scope and periods
   - retrieves retained MAE/RMSE/MAPE from UC-06 when an exact match exists
   - attempts on-demand metric computation when retained metrics are missing
   - aligns only matching forecast and actual buckets
   - assembles one typed comparison payload with explicit view and metric status
   - persists request, metric-resolution, prepared-result, and render-event observability
4. Keep route handlers thin:
   - one authenticated `GET` endpoint for loading the forecast-performance view
   - one authenticated `POST` endpoint for reporting final render success or failure
   - all scope resolution, source selection, metric fallback, alignment, and status derivation in services
   - all persistence in repositories
5. Keep frontend integration bounded:
   - load the default view automatically for authorized users
   - allow supported scope changes such as time range, category, and optional geography
   - render aligned prediction-versus-actual output and metrics when available
   - show explicit messaging when metrics are unavailable but comparison data remains valid
   - show unavailable or error states when forecasts, actuals, alignment, or rendering fails
   - report the final render outcome back to the backend for observability

## Acceptance Alignment

Map implementation and tests directly to [UC-14](/Users/sahmed/Documents/311-forecast-system/docs/UC-14.md) and [UC-14-AT.md](/Users/sahmed/Documents/311-forecast-system/docs/UC-14-AT.md):

- AT-01: load the forecast-performance interface for the default scope without an immediate error
- AT-02 and AT-03: retrieve retained historical forecasts and matching actual demand for the selected scope
- AT-04: retrieve retained MAE/RMSE/MAPE or compute them on demand for the same scope and time window
- AT-05 and AT-06: align forecast and actual values to the same buckets and prepare one visualization-ready payload
- AT-07 and AT-08: render prediction-versus-actual comparisons with metrics when available and record traceable success outcomes
- AT-09 and AT-10: return explicit unavailable or error states when forecasts or actuals are missing
- AT-11: render comparisons without summary metrics when metrics are unavailable but aligned data exists
- AT-12: record render failure and show an error state without corrupting the prepared result

## Suggested Test Layers

- Unit tests for default-scope resolution, retained-source selection, exact-window metric reuse, on-demand metric fallback, bucket alignment, and view-status derivation
- Integration tests across request persistence, actual and forecast retrieval, metric-resolution outcomes, prepared-result persistence, unavailable states, and render-event handling
- Contract tests for [forecast-accuracy-api.yaml](/Users/sahmed/Documents/311-forecast-system/specs/014-uc-14-forecast-accuracy/contracts/forecast-accuracy-api.yaml)
- Frontend interaction tests for default load, scope changes, metrics-present rendering, metrics-unavailable messaging, unavailable states, and render-failure handling

## Exit Conditions

Implementation is ready for task breakdown when:

- the default forecast-performance view loads the last 30 completed days for authorized users
- aligned forecast and actual buckets always represent the same scope and interval
- MAE, RMSE, and MAPE are shown only when they match the displayed scope and time window
- missing retained metrics trigger one on-demand computation attempt before metrics-unavailable fallback
- valid aligned comparisons can render without metrics when metric production fails
- missing forecasts, missing actuals, and unsafe alignment all return explicit unavailable or error states
- final client render outcomes are traceable without mutating the prepared comparison result
