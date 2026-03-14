# Data Model: Indicate Degraded Forecast Confidence in UI

## Overview

UC-16 extends the shared lineage defined by UC-01 through UC-15 without redefining those upstream entities. The feature consumes existing forecast-visualization context, retained forecast lineage, evaluation and anomaly signals, weather or storm-mode quality context where applicable, and established authenticated observability patterns, then adds only the UC-16-specific request, signal-resolution, prepared-assessment, and render-event records required to support clear degraded-confidence indication, safe normal-display fallback, and traceable render failures.

## Reused Shared Entities and Vocabulary

UC-16 references shared entities and vocabularies from earlier use cases and does not redefine their fields here:

- UC-01 and UC-02: ingestion and approved cleaned-demand lineage used by upstream quality and actual-demand context
- UC-03 and UC-04: retained daily and weekly forecast lineage, including canonical forecast run, version, and bucket entities
- UC-05: forecast visualization conventions and the existing forecast-view context this feature augments
- UC-06 through UC-09: evaluation metrics, anomaly-supporting analysis, comparison semantics, and weather-alignment conventions that may contribute confidence or quality signals
- UC-10 and UC-11: authenticated alert and observability conventions reused for role-aware operational access patterns
- UC-12 through UC-14: request correlation, render-event reporting, and normalized read-model conventions for interactive UI workflows
- UC-15: storm-mode and weather-driven adjustment diagnostics that may contribute degraded-confidence reasons without being redefined here

UC-16 also reuses these shared modeling concepts without redefining upstream entities:

- Canonical forecast scope: service category plus optional geography plus effective time window
- Structured operational correlation using request id, actor identity, timestamps, and optional correlation id
- Existing authenticated forecast-view access and shared role-based authorization boundaries

## Canonical UC-16 Vocabulary

### Assessment Status

- `degraded_confirmed`
- `normal`
- `signals_missing`
- `dismissed`
- `error`

### Indicator State

- `display_required`
- `not_displayed`
- `render_failed`

### Signal Resolution Status

- `resolved`
- `missing`
- `dismissed`
- `failed`

### Reason Category

- `missing_inputs`
- `shock`
- `anomaly`
- `quality_condition`
- `unknown`

### Render Outcome

- `rendered`
- `render_failed`

## New Entity: ForecastConfidenceRequest

**Purpose**: Records one operational-manager attempt to load degraded-confidence status for a forecast view and provides the correlation anchor for all downstream UC-16 records.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `forecast_confidence_request_id` | Identifier | Yes | Unique per confidence-load attempt |
| `forecast_view_id` | Identifier | No | Present when the request is tied to a persisted or reusable forecast-view context |
| `forecast_run_id` | Identifier | No | References the reused forecast lineage when known |
| `forecast_version_id` | Identifier | No | References the reused forecast version when known |
| `service_category` | String | No | Present when the request is category-scoped |
| `geography_type` | String | No | Present only for geography-scoped requests |
| `geography_value` | String | No | Required when `geography_type` is present |
| `time_range_start` | Timestamp | Yes | Inclusive start of the forecast scope being evaluated |
| `time_range_end` | Timestamp | Yes | Inclusive end of the forecast scope being evaluated |
| `requested_by_actor` | Enum | Yes | `operational_manager` only for UC-16 scope |
| `requested_at` | Timestamp | Yes | Set when the confidence request begins |
| `completed_at` | Timestamp | No | Required when the request reaches a terminal state |
| `assessment_status` | Enum | Yes | `degraded_confirmed`, `normal`, `signals_missing`, `dismissed`, or `error` |
| `correlation_id` | String | No | Shared operational identifier when supported |

**Validation rules**

- `time_range_end` must not be earlier than `time_range_start`.
- `geography_value` must be absent when `geography_type` is absent.
- `completed_at` is required for terminal `assessment_status` values.
- `assessment_status = degraded_confirmed` requires at least one linked `ForecastConfidenceSignalResolution` with `signal_resolution_status = resolved`.

## New Entity: ForecastConfidenceSignalResolution

**Purpose**: Records the confidence or quality signals resolved for one request, including missing-signal, dismissed-signal, and signal-processing failure outcomes.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `forecast_confidence_signal_resolution_id` | Identifier | Yes | Unique per signal-resolution record |
| `forecast_confidence_request_id` | Identifier | Yes | References the owning confidence request |
| `signal_source` | String | Yes | Canonical upstream source or signal family used in assessment |
| `signal_resolution_status` | Enum | Yes | `resolved`, `missing`, `dismissed`, or `failed` |
| `candidate_reason_category` | Enum | No | Present when a signal suggests a degraded-confidence reason |
| `materiality_confirmed` | Boolean | No | Required when `signal_resolution_status = resolved` or `dismissed` |
| `signal_summary` | String | No | Optional normalized description suitable for operations review |
| `dismissal_reason` | String | No | Required when `signal_resolution_status = dismissed` |
| `failure_reason` | String | No | Required when `signal_resolution_status = failed` |
| `resolved_at` | Timestamp | Yes | Set when this signal-resolution outcome is recorded |

**Validation rules**

- `candidate_reason_category` must use the canonical UC-16 reason vocabulary when present.
- `materiality_confirmed = true` is valid only when `signal_resolution_status = resolved`.
- `materiality_confirmed = false` is required when `signal_resolution_status = dismissed`.
- `dismissal_reason` is required when `signal_resolution_status = dismissed`.
- `failure_reason` is required when `signal_resolution_status = failed`.
- `candidate_reason_category` is required when `signal_resolution_status = resolved` and degraded confidence is confirmed by this record.

## New Entity: ForecastConfidenceAssessmentResult

**Purpose**: Stores the normalized backend-prepared confidence-display result for one request, including what indicator state the client should use.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `forecast_confidence_result_id` | Identifier | Yes | Unique per prepared assessment result |
| `forecast_confidence_request_id` | Identifier | Yes | References the owning confidence request |
| `assessment_status` | Enum | Yes | `degraded_confirmed`, `normal`, `signals_missing`, `dismissed`, or `error` |
| `indicator_state` | Enum | Yes | `display_required`, `not_displayed`, or `render_failed` |
| `warning_message` | String | No | Required when `assessment_status = degraded_confirmed` |
| `reason_categories` | Collection | No | Ordered distinct reason categories shown to the user when available |
| `status_message` | String | No | Required for `signals_missing`, `dismissed`, and `error` |
| `forecast_visible` | Boolean | Yes | Must remain `true` unless a separate upstream forecast failure prevents display |
| `prepared_at` | Timestamp | Yes | Set when the assessment result is prepared |

**Validation rules**

- `indicator_state = display_required` is valid only when `assessment_status = degraded_confirmed`.
- `indicator_state = not_displayed` is required when `assessment_status = normal`, `signals_missing`, or `dismissed`.
- `warning_message` is required when `assessment_status = degraded_confirmed`.
- `reason_categories` may be populated only when `assessment_status = degraded_confirmed`.
- `status_message` is required when `assessment_status = signals_missing`, `dismissed`, or `error`.
- `forecast_visible` must remain `true` for `degraded_confirmed`, `normal`, `signals_missing`, and `dismissed`.

## New Entity: ForecastConfidenceRenderEvent

**Purpose**: Records the final client render outcome for one prepared confidence result so indicator-render failures remain traceable after response delivery.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `forecast_confidence_render_event_id` | Identifier | Yes | Unique per render-event record |
| `forecast_confidence_request_id` | Identifier | Yes | References the originating confidence request |
| `forecast_confidence_result_id` | Identifier | Yes | References the prepared assessment result |
| `render_outcome` | Enum | Yes | `rendered` or `render_failed` |
| `indicator_render_attempted` | Boolean | Yes | `true` when the client attempted to render a degraded-confidence indicator |
| `failure_reason` | String | No | Required when `render_outcome = render_failed` |
| `rendered_at` | Timestamp | Yes | Set when the client reports the final render outcome |

**Validation rules**

- `failure_reason` is required when `render_outcome = render_failed`.
- `indicator_render_attempted = true` is required when the linked `ForecastConfidenceAssessmentResult.indicator_state = display_required`.
- `indicator_render_attempted = false` is valid only when the linked prepared result did not require indicator display.
- `render_outcome = rendered` must not mutate the linked prepared assessment result.
- `render_outcome = render_failed` records observability for the same request and may cause downstream diagnostic views to expose `indicator_state = render_failed`, but it must not change the original `assessment_status`.

## New Derived Entity: ForecastConfidenceView

**Purpose**: Represents the stable backend-to-frontend read model for confidence status in a forecast view.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `forecast_confidence_request_id` | Identifier | Yes | Unique link to the request record |
| `forecast_confidence_result_id` | Identifier | Yes | Unique link to the prepared result |
| `forecast_view_id` | Identifier | No | Present when tied to a persisted or reusable forecast-view context |
| `time_range_start` | Timestamp | Yes | Inclusive start of the evaluated forecast scope |
| `time_range_end` | Timestamp | Yes | Inclusive end of the evaluated forecast scope |
| `service_category` | String | No | Present when category-scoped |
| `geography_type` | String | No | Present only when geography-scoped |
| `geography_value` | String | No | Present only when `geography_type` is present |
| `assessment_status` | Enum | Yes | `degraded_confirmed`, `normal`, `signals_missing`, `dismissed`, or `error` |
| `indicator_state` | Enum | Yes | `display_required`, `not_displayed`, or `render_failed` |
| `warning_message` | String | No | Present when degraded confidence is confirmed |
| `reason_categories` | Collection | Yes | Empty when no explanatory categories are available or no warning is shown |
| `status_message` | String | No | Required for `signals_missing`, `dismissed`, `error`, and `render_failed` display semantics |
| `forecast_visible` | Boolean | Yes | Indicates whether forecast content remains displayable |
| `correlation_id` | String | No | Shared operational identifier when supported |

**Validation rules**

- `time_range_end` must not be earlier than `time_range_start`.
- `reason_categories` must be empty when `assessment_status != degraded_confirmed`.
- `warning_message` is required when `assessment_status = degraded_confirmed`.
- `status_message` is required when `assessment_status = signals_missing`, `dismissed`, or `error`.
- When a linked `ForecastConfidenceRenderEvent.render_outcome = render_failed` exists, `indicator_state` may be surfaced as `render_failed` in the view while `assessment_status` remains unchanged.

## Relationships

- One `ForecastConfidenceRequest` may produce many `ForecastConfidenceSignalResolution` records.
- One `ForecastConfidenceRequest` produces exactly one `ForecastConfidenceAssessmentResult`.
- One `ForecastConfidenceAssessmentResult` may produce zero or many `ForecastConfidenceRenderEvent` records over time, though at most one terminal render event should be treated as canonical for the same client interaction.
- One `ForecastConfidenceRequest` produces exactly one `ForecastConfidenceView` response shape for the requesting client.

## Derived Invariants

- UC-16 must not redefine or mutate shared upstream entities from UC-01 through UC-15 inside `data-model.md`; it only adds request-scoped confidence-display records and read models specific to this use case.
- A degraded-confidence warning is valid only when at least one resolved signal confirms material degradation for the same forecast scope and window.
- Missing signals and dismissed non-material signals must remain distinguishable in persisted outcomes even though both suppress the warning in the UI.
- A render failure may prevent the indicator from appearing, but it must not cause the system to claim the warning rendered successfully.
- Forecast visibility remains independent from indicator visibility in UC-16 unless an upstream forecast-view failure outside this use case prevents forecast display altogether.
