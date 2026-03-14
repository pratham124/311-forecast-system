# Data Model: View Forecast Accuracy and Compare Predictions to Actuals

## Overview

UC-14 extends the shared lineage defined by UC-01 through UC-13 without redefining those upstream entities. The feature consumes retained historical forecast outputs, approved actual-demand lineage, retained evaluation metrics, and established visualization observability patterns, then adds only the UC-14-specific request, prepared-view, alignment, metric-resolution, and render-event records needed to support full, metrics-unavailable, unavailable, and error outcomes.

## Reused Shared Entities and Vocabulary

UC-14 references shared entities and vocabularies from earlier use cases and does not redefine their fields here:

- UC-01: `IngestionRun` and ingested dataset lineage as upstream provenance for realized demand
- UC-02: `ValidationRun`, `CleanedDatasetVersion`, and `CurrentDatasetMarker` as the canonical approved actual-demand source
- UC-03: `ForecastRun`, `ForecastVersion`, `ForecastBucket`, and `CurrentForecastMarker` for retained daily forecast lineage
- UC-05: visualization-ready forecasting payload conventions and chart or table presentation semantics
- UC-06: `EvaluationRun`, `EvaluationResult`, `EvaluationSegment`, `MetricComparisonValue`, and `CurrentEvaluationMarker` as the canonical retained MAE/RMSE/MAPE lineage
- UC-07 and UC-08: historical-demand and comparison alignment semantics where selected scope and normalized bucket alignment are reused
- UC-09: optional weather-overlay context remains unrelated and is not extended by UC-14
- UC-10 through UC-13: authenticated access, role-aware authorization, and explicit operational observability conventions used across planner-facing and operational views

UC-14 also reuses these shared modeling concepts without redefining upstream entities:

- Canonical comparison scope: time range, service category, and optional geography
- Forecast product vocabulary already established by retained daily forecast lineage
- Metric vocabulary `mae`, `rmse`, and `mape` from UC-06
- Structured operational correlation using actor identity, timestamps, request id, and optional correlation id

## Canonical UC-14 Vocabulary

### View Status

- `rendered_with_metrics`
- `rendered_without_metrics`
- `unavailable`
- `error`

### Request Status

- `running`
- `rendered_with_metrics`
- `rendered_without_metrics`
- `forecast_missing`
- `actual_missing`
- `alignment_unavailable`
- `preparation_failed`
- `render_failed`

### Metric Resolution Status

- `retrieved_precomputed`
- `computed_on_demand`
- `unavailable`
- `failed`

### Render Outcome

- `rendered`
- `failed`

## New Entity: ForecastAccuracyRequest

**Purpose**: Records one authenticated planner request to load forecast-performance analysis for a resolved scope.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `forecast_accuracy_request_id` | Identifier | Yes | Unique per analysis request |
| `requested_by_actor` | Enum | Yes | `city_planner` only for UC-14 scope |
| `requested_by_actor_id` | Identifier | Yes | References the authenticated caller |
| `source_cleaned_dataset_version_id` | Identifier | No | Present when actual-demand lineage is resolved |
| `source_forecast_version_id` | Identifier | No | Present only when the request resolves to retained daily forecast lineage |
| `source_evaluation_result_id` | Identifier | No | Present only when precomputed metrics are reused from UC-06 |
| `forecast_product_name` | Enum | No | `daily_1_day` when a retained forecast source is resolved |
| `comparison_granularity` | Enum | Yes | `hourly` or `daily` based on the resolved source and requested range |
| `time_range_start` | Timestamp | Yes | Inclusive scope start |
| `time_range_end` | Timestamp | Yes | Inclusive scope end |
| `service_category` | String | No | Present when the request is category-scoped |
| `geography_type` | String | No | Present only for geography-scoped requests |
| `geography_value` | String | No | Required when `geography_type` is present |
| `status` | Enum | Yes | `running`, `rendered_with_metrics`, `rendered_without_metrics`, `forecast_missing`, `actual_missing`, `alignment_unavailable`, `preparation_failed`, or `render_failed` |
| `started_at` | Timestamp | Yes | Set when processing begins |
| `completed_at` | Timestamp | No | Required when the request reaches a terminal state |
| `correlation_id` | String | No | Shared operational identifier when supported |
| `failure_reason` | String | No | Required for terminal failure or unavailable states |

**Validation rules**

- `time_range_end` must not be earlier than `time_range_start`.
- `forecast_product_name = daily_1_day` requires `source_forecast_version_id` and `comparison_granularity = hourly`.
- `geography_value` must be absent when `geography_type` is absent.
- `completed_at` is required for every terminal `status` except `running`.
- `failure_reason` is required for `forecast_missing`, `actual_missing`, `alignment_unavailable`, `preparation_failed`, and `render_failed`.

**State transitions**

`running` → `rendered_with_metrics`
`running` → `rendered_without_metrics`
`running` → `forecast_missing`
`running` → `actual_missing`
`running` → `alignment_unavailable`
`running` → `preparation_failed`
`running` → `render_failed`

No other transitions are valid.

## New Entity: ForecastAccuracyMetricResolution

**Purpose**: Records how UC-14 resolved or failed to resolve MAE, RMSE, and MAPE for one request scope.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `forecast_accuracy_metric_resolution_id` | Identifier | Yes | Unique per metric-resolution attempt |
| `forecast_accuracy_request_id` | Identifier | Yes | References the owning request |
| `source_evaluation_result_id` | Identifier | No | Present when metrics are retrieved from UC-06 |
| `resolution_status` | Enum | Yes | `retrieved_precomputed`, `computed_on_demand`, `unavailable`, or `failed` |
| `metric_names` | Collection | Yes | Ordered metric names; for UC-14 this is `mae`, `rmse`, and `mape` |
| `mae_value` | Decimal | No | Present when MAE is available |
| `rmse_value` | Decimal | No | Present when RMSE is available |
| `mape_value` | Decimal | No | Present when MAPE is available |
| `resolved_at` | Timestamp | Yes | Set when metric resolution finishes |
| `status_message` | String | No | Required when metrics are unavailable or metric computation fails |

**Validation rules**

- `metric_names` must contain exactly `mae`, `rmse`, and `mape` in stable order for UC-14.
- `source_evaluation_result_id` is required when `resolution_status = retrieved_precomputed`.
- `mae_value`, `rmse_value`, and `mape_value` must all be present for `retrieved_precomputed` and `computed_on_demand`.
- `status_message` is required when `resolution_status = unavailable` or `resolution_status = failed`.
- `resolution_status = unavailable` is valid only when forecasts and actuals remain available but metrics could not be produced.

## New Entity: ForecastAccuracyComparisonResult

**Purpose**: Represents the normalized prepared comparison output for one request after source retrieval, alignment, and metric resolution complete.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `forecast_accuracy_result_id` | Identifier | Yes | Unique per prepared result |
| `forecast_accuracy_request_id` | Identifier | Yes | References the request that produced the result |
| `metric_resolution_id` | Identifier | No | Present when a metric-resolution record exists |
| `source_cleaned_dataset_version_id` | Identifier | No | Present when actual-demand lineage contributed to the result |
| `source_forecast_version_id` | Identifier | No | Present only when retained daily forecast lineage contributed |
| `forecast_product_name` | Enum | No | `daily_1_day` when a forecast source contributed |
| `comparison_granularity` | Enum | Yes | `hourly` or `daily` |
| `view_status` | Enum | Yes | `rendered_with_metrics`, `rendered_without_metrics`, `unavailable`, or `error` |
| `metric_resolution_status` | Enum | No | Mirrors the linked `ForecastAccuracyMetricResolution` outcome when present |
| `bucket_count` | Integer | Yes | Zero or greater |
| `excluded_bucket_count` | Integer | Yes | Zero or greater |
| `status_message` | String | No | Required for `rendered_without_metrics`, `unavailable`, and `error` |
| `stored_at` | Timestamp | Yes | Set when the prepared result is persisted |

**Validation rules**

- `ForecastAccuracyComparisonResult` exists for every terminal request, including unavailable and error outcomes.
- `view_status = rendered_with_metrics` requires `metric_resolution_status` to be `retrieved_precomputed` or `computed_on_demand` and `bucket_count > 0`.
- `view_status = rendered_without_metrics` requires `metric_resolution_status = unavailable` or `failed`, `bucket_count > 0`, and `status_message`.
- `view_status = unavailable` requires `bucket_count = 0` and `status_message`.
- `view_status = error` requires `bucket_count = 0` and `status_message`.

## New Entity: ForecastAccuracyAlignedBucket

**Purpose**: Stores one aligned forecast-versus-actual bucket inside a prepared comparison result.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `forecast_accuracy_aligned_bucket_id` | Identifier | Yes | Unique per aligned bucket |
| `forecast_accuracy_result_id` | Identifier | Yes | References the owning prepared result |
| `bucket_start` | Timestamp | Yes | Inclusive aligned interval start |
| `bucket_end` | Timestamp | Yes | Inclusive aligned interval end |
| `service_category` | String | No | Present when the request is category-scoped |
| `geography_type` | String | No | Present only for geography-scoped requests |
| `geography_value` | String | No | Required when `geography_type` is present |
| `forecast_value` | Decimal | Yes | Retained forecast value for the aligned interval |
| `actual_value` | Decimal | Yes | Realized actual-demand value for the aligned interval |
| `absolute_error_value` | Decimal | Yes | Absolute difference between forecast and actual |
| `percentage_error_value` | Decimal | No | Present when percentage error is defined for the interval |
| `source_forecast_bucket_id` | Identifier | No | Present when the aligned forecast source is a UC-03 forecast bucket |

**Validation rules**

- `bucket_end` must not be earlier than `bucket_start`.
- `forecast_value` and `actual_value` must be zero or greater.
- `absolute_error_value` must equal the absolute difference between `forecast_value` and `actual_value`.
- `percentage_error_value` may be absent only when the percentage denominator is undefined for that interval.
- All buckets for one result must share the same `comparison_granularity` implied by the parent `ForecastAccuracyComparisonResult`.

## New Entity: ForecastAccuracyRenderEvent

**Purpose**: Records the final client render outcome for one prepared UC-14 request so chart or table failures remain traceable.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `forecast_accuracy_render_event_id` | Identifier | Yes | Unique per reported render event |
| `forecast_accuracy_request_id` | Identifier | Yes | References the prepared request the client attempted to render |
| `forecast_accuracy_result_id` | Identifier | Yes | References the prepared result shown to the client |
| `render_outcome` | Enum | Yes | `rendered` or `failed` |
| `reported_at` | Timestamp | Yes | Set when the client reports the render outcome |
| `failure_reason` | String | No | Required when `render_outcome = failed` |
| `reported_by_actor_id` | Identifier | Yes | References the authenticated caller reporting the event |

**Validation rules**

- `forecast_accuracy_request_id` and `forecast_accuracy_result_id` must refer to the same request lifecycle.
- `failure_reason` is required when `render_outcome = failed`.
- A `failed` render event may update the owning `ForecastAccuracyRequest.status` to `render_failed` but must not delete the prepared result.

## New Derived Entity: ForecastAccuracyView

**Purpose**: Represents the stable backend-to-frontend read model returned by UC-14 for one request.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `forecast_accuracy_request_id` | Identifier | Yes | Unique link to the request lifecycle |
| `forecast_accuracy_result_id` | Identifier | Yes | Unique link to the prepared result |
| `time_range_start` | Timestamp | Yes | Inclusive comparison start |
| `time_range_end` | Timestamp | Yes | Inclusive comparison end |
| `service_category` | String | No | Present when scoped by category |
| `geography_type` | String | No | Present only for geography-scoped requests |
| `geography_value` | String | No | Present only when `geography_type` is present |
| `forecast_product_name` | Enum | No | `daily_1_day` when a forecast source exists |
| `comparison_granularity` | Enum | Yes | `hourly` or `daily` |
| `view_status` | Enum | Yes | `rendered_with_metrics`, `rendered_without_metrics`, `unavailable`, or `error` |
| `metric_resolution_status` | Enum | No | `retrieved_precomputed`, `computed_on_demand`, `unavailable`, or `failed` |
| `status_message` | String | No | Required for non-ideal outcomes |
| `metrics` | Object | No | Present only when MAE, RMSE, and MAPE are available |
| `aligned_buckets` | Collection | Yes | Ordered comparison buckets; empty when unavailable or error |

**Validation rules**

- `metrics` is required only for `view_status = rendered_with_metrics`.
- `status_message` is required for `view_status = rendered_without_metrics`, `unavailable`, and `error`.
- `aligned_buckets` must be empty when `view_status = unavailable` or `error`.
- `aligned_buckets` must be ordered by ascending `bucket_start`.

## Relationships

- One `ForecastAccuracyRequest` may produce zero or one `ForecastAccuracyMetricResolution`.
- One `ForecastAccuracyRequest` produces exactly one `ForecastAccuracyComparisonResult` for each terminal outcome.
- One `ForecastAccuracyComparisonResult` owns zero or more `ForecastAccuracyAlignedBucket` records.
- One `ForecastAccuracyRequest` may receive many `ForecastAccuracyRenderEvent` records over time, though the latest accepted event is the operationally relevant final render outcome.
- One `ForecastAccuracyComparisonResult` produces exactly one `ForecastAccuracyView` response shape for the requesting client.

## Derived Invariants

- UC-14 must not redefine or mutate shared upstream entities from UC-01 through UC-13 inside `data-model.md`; it only adds forecast-performance view records specific to this use case.
- Forecast and actual values shown in one aligned bucket must always refer to the same interval and the same scope.
- Retained metrics from UC-06 may be reused only when they match the displayed scope, granularity, and time window exactly.
- If metrics are unavailable or metric computation fails, comparison output may still render only when aligned forecast and actual buckets remain valid.
- Missing forecasts, missing actuals, or empty aligned overlap must never produce bucket-level comparison output.
- A failed client render must remain observable without changing the prepared comparison result that the server already produced.
