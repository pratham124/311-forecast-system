# Data Model: View Public Forecast of 311 Demand by Category

## Overview

UC-17 extends the shared lineage defined by UC-01 through UC-16 without redefining those upstream entities. The feature consumes approved forecast lineage, current-marker semantics, visualization conventions, and established request-correlation patterns, then adds only the UC-17-specific request, sanitization, normalized public-payload, and display-event records required to support anonymous public viewing, safe disclosure, incomplete-coverage messaging, and traceable render failures.

## Reused Shared Entities and Vocabulary

UC-17 references shared entities and vocabularies from earlier use cases and does not redefine their fields here:

- UC-01 and UC-02: ingestion and approved cleaned-demand lineage used as the historical source behind retained forecasts
- UC-03 and UC-04: retained daily and weekly forecast lineage, including canonical forecast run, version, bucket, and current-marker entities used to identify the currently approved forecast basis
- UC-05: forecast-visualization conventions for presenting category-level demand summaries
- UC-06 through UC-09: evaluation, comparison, and weather-enrichment lineage that may have shaped upstream retained forecast outputs but remain outside UC-17 ownership
- UC-10 through UC-16: observability, request-correlation, display-event, and normalized read-model conventions reused for public portal diagnostics without redefining authenticated operational entities

UC-17 also reuses these shared modeling concepts without redefining upstream entities:

- Canonical forecast scope: service category plus effective forecast time window
- Approved current-version semantics from upstream forecast publication workflows
- Structured operational correlation using request id, timestamps, optional client correlation, and terminal outcome state

## Reused Source Entity: ApprovedPublicForecastVersion

**Purpose**: Represents the already approved public-safe retained forecast version selected from shared upstream lineage for anonymous portal use.

UC-17 reuses the shared upstream forecast-version and approval-marker concepts rather than defining a new forecast dataset table. The public portal reads the currently approved public-safe version and treats it as immutable for the duration of one request.

## Canonical UC-17 Vocabulary

### Portal Status

- `available`
- `unavailable`
- `error`

### Sanitization Status

- `passed_as_is`
- `sanitized`
- `blocked`
- `failed`

### Coverage Status

- `complete`
- `incomplete`

### Display Outcome

- `rendered`
- `render_failed`

## New Entity: PublicForecastPortalRequest

**Purpose**: Records one anonymous attempt to load the public forecast portal and provides the correlation anchor for all UC-17-specific downstream records.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `public_forecast_request_id` | Identifier | Yes | Unique per portal-load attempt |
| `approved_forecast_version_id` | Identifier | No | References the reused approved public-safe forecast version when available |
| `requested_at` | Timestamp | Yes | Set when the portal request begins |
| `completed_at` | Timestamp | No | Required when the request reaches a terminal state |
| `portal_status` | Enum | Yes | `available`, `unavailable`, or `error` |
| `forecast_window_label` | String | No | Required when `portal_status = available` |
| `published_at` | Timestamp | No | Required when `portal_status = available` |
| `client_correlation_id` | String | No | Optional correlation identifier when the client provides one |
| `failure_reason` | String | No | Required when `portal_status = unavailable` or `portal_status = error` |

**Validation rules**

- `completed_at` is required for terminal `portal_status` values.
- `approved_forecast_version_id` is required when `portal_status = available`.
- `forecast_window_label` and `published_at` are required when `portal_status = available`.
- `failure_reason` is required when `portal_status = unavailable` or `portal_status = error`.

## New Entity: PublicForecastSanitizationOutcome

**Purpose**: Records the result of applying public-safety filtering rules to the retrieved public forecast content for one portal request.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `public_forecast_sanitization_outcome_id` | Identifier | Yes | Unique per sanitization outcome |
| `public_forecast_request_id` | Identifier | Yes | References the owning portal request |
| `sanitization_status` | Enum | Yes | `passed_as_is`, `sanitized`, `blocked`, or `failed` |
| `restricted_detail_detected` | Boolean | Yes | Indicates whether restricted detail was found during filtering |
| `removed_detail_count` | Integer | Yes | Zero or greater |
| `sanitization_summary` | String | No | Required when `sanitization_status = sanitized` |
| `failure_reason` | String | No | Required when `sanitization_status = blocked` or `sanitization_status = failed` |
| `evaluated_at` | Timestamp | Yes | Set when the filtering outcome is recorded |

**Validation rules**

- `removed_detail_count` must be zero when `restricted_detail_detected = false`.
- `removed_detail_count` must be greater than zero when `sanitization_status = sanitized`.
- `sanitization_summary` is required when `sanitization_status = sanitized`.
- `failure_reason` is required when `sanitization_status = blocked` or `sanitization_status = failed`.
- `sanitization_status = passed_as_is` is valid only when `restricted_detail_detected = false`.

## New Entity: PublicForecastVisualizationPayload

**Purpose**: Stores the normalized public-safe category-level content prepared for one successful portal response.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `public_forecast_payload_id` | Identifier | Yes | Unique per prepared public payload |
| `public_forecast_request_id` | Identifier | Yes | References the owning portal request |
| `approved_forecast_version_id` | Identifier | Yes | References the reused approved public-safe forecast version |
| `forecast_window_label` | String | Yes | Human-readable label for the covered public forecast window |
| `published_at` | Timestamp | Yes | Published or last-updated time for the approved public view |
| `coverage_status` | Enum | Yes | `complete` or `incomplete` |
| `coverage_message` | String | No | Required when `coverage_status = incomplete` |
| `category_summaries` | Collection | Yes | Ordered category-level public summaries safe for display |
| `prepared_at` | Timestamp | Yes | Set when the payload is prepared |

**Embedded category summary fields**

Each item in `category_summaries` contains:

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `service_category` | String | Yes | Public category label |
| `forecast_demand_value` | Number | No | Optional numeric forecast value when public-safe to show |
| `demand_level_summary` | String | No | Optional qualitative demand summary when numeric detail is not shown |

**Validation rules**

- `coverage_message` is required when `coverage_status = incomplete`.
- `category_summaries` must contain at least one category when the payload exists.
- Each category summary must include at least one of `forecast_demand_value` or `demand_level_summary`.
- Category summaries must not contain internal operational metadata, raw model diagnostics, or restricted details.
- `approved_forecast_version_id` must match the version referenced by the owning `PublicForecastPortalRequest`.

## New Entity: PublicForecastDisplayEvent

**Purpose**: Records the final client-visible display result for one prepared public forecast response.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `public_forecast_display_event_id` | Identifier | Yes | Unique per display-event record |
| `public_forecast_request_id` | Identifier | Yes | References the originating portal request |
| `public_forecast_payload_id` | Identifier | No | References the prepared payload when one existed |
| `display_outcome` | Enum | Yes | `rendered` or `render_failed` |
| `failure_reason` | String | No | Required when `display_outcome = render_failed` |
| `reported_at` | Timestamp | Yes | Set when the client reports the final display outcome |

**Validation rules**

- `public_forecast_payload_id` is required when the owning request completed with `portal_status = available`.
- `failure_reason` is required when `display_outcome = render_failed`.
- `display_outcome = rendered` must not mutate the prepared public payload.
- `display_outcome = render_failed` records observability for the same request and must not cause the system to claim a successful public display.

## New Derived Entity: PublicForecastView

**Purpose**: Represents the stable backend-to-frontend read model for the anonymous public forecast portal.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `public_forecast_request_id` | Identifier | Yes | Unique link to the portal request |
| `status` | Enum | Yes | `available`, `unavailable`, or `error` |
| `forecast_window_label` | String | No | Required when `status = available` |
| `published_at` | Timestamp | No | Required when `status = available` |
| `coverage_status` | Enum | No | Required when `status = available` |
| `coverage_message` | String | No | Required when `coverage_status = incomplete` |
| `sanitization_status` | Enum | No | Required when `status = available` |
| `sanitization_summary` | String | No | Present when restricted details were removed before display |
| `category_summaries` | Collection | No | Required when `status = available` |
| `status_message` | String | No | Required when `status = unavailable` or `status = error` |
| `client_correlation_id` | String | No | Echoed correlation identifier when supported |

**Validation rules**

- `forecast_window_label`, `published_at`, `coverage_status`, `sanitization_status`, and `category_summaries` are required when `status = available`.
- `coverage_message` is required when `coverage_status = incomplete`.
- `status_message` is required when `status = unavailable` or `status = error`.
- `category_summaries` must be absent when `status = unavailable` or `status = error`.
- `sanitization_status = blocked` or `sanitization_status = failed` is invalid when `status = available`.

## Relationships

- One reused `ApprovedPublicForecastVersion` may be referenced by many `PublicForecastPortalRequest` records over time.
- One `PublicForecastPortalRequest` produces exactly one `PublicForecastSanitizationOutcome`.
- One `PublicForecastPortalRequest` may produce zero or one `PublicForecastVisualizationPayload`.
- One `PublicForecastPortalRequest` may produce zero or many `PublicForecastDisplayEvent` records, though at most one terminal display event should be treated as canonical for the same client interaction.
- One successful `PublicForecastPortalRequest` produces exactly one `PublicForecastView` response shape for the requesting client.

## Derived Invariants

- UC-17 must not redefine shared upstream entities from UC-01 through UC-16 inside `data-model.md`; it only adds request-scoped public-view, sanitization, payload, and display-observability records specific to this use case.
- One portal response must be internally consistent to one approved public-safe forecast version even if a newer approved version becomes available during request processing.
- Omitted categories must never be represented as zero demand unless zero is the actual forecasted public-safe value.
- Restricted details must never appear in `PublicForecastVisualizationPayload` or `PublicForecastView`.
- A render failure may prevent the public chart or summary from appearing, but it must not cause the system to report a successful public display.
