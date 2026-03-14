# Data Model: Drill Alert Details and Context

## Overview

UC-12 extends the shared lineage defined by UC-01 through UC-11 without redefining those upstream entities. The drill-down workflow reads an existing alert record, resolves its forecast and anomaly support context, normalizes that context into one detail payload, and adds only the UC-12-specific observability and read models needed to support complete, partial, and error detail views.

## Reused Shared Entities and Vocabulary

UC-12 references shared entities and vocabularies from earlier use cases and does not redefine their fields here:

- UC-01 through UC-04: ingestion, validation, and forecast lineage used to trace alert-supporting forecast context
- UC-05: forecast visualization conventions and normalized uncertainty-curve context
- UC-06 through UC-09: evaluation and exploratory analysis lineage where anomaly-supporting or historical-supporting context is derived
- UC-10: `NotificationEvent`, `NotificationChannelAttempt`, and delivery-review semantics for threshold alerts
- UC-11: `SurgeNotificationEvent`, `SurgeNotificationChannelAttempt`, and surge-review semantics for abnormal-demand alerts

UC-12 also reuses these shared modeling concepts without redefining upstream entities:

- Canonical alert identity resolved from an existing retained alert event
- Canonical operational correlation using alert id and optional correlation id
- Explicit user-visible state vocabularies rather than implicit empty visualizations

## Canonical UC-12 Vocabulary

### Alert Source

- `threshold_alert`
- `surge_alert`

### Component Status

- `available`
- `unavailable`
- `failed`

### View Status

- `loading`
- `rendered`
- `partial`
- `error`

### Failure Category

- `distribution-failed`
- `drivers-failed`
- `anomalies-failed`
- `preparation-failed`
- `render-failed`

## New Entity: AlertDetailLoadRecord

**Purpose**: Records one alert-detail retrieval and rendering attempt so request, component, preparation, and render outcomes remain traceable for the selected alert.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `alert_detail_load_id` | Identifier | Yes | Unique per detail-load attempt |
| `alert_source` | Enum | Yes | `threshold_alert` or `surge_alert` |
| `alert_id` | Identifier | Yes | References the selected upstream alert record |
| `requested_by_actor` | Enum | Yes | `operational_manager` only for UC-12 scope |
| `requested_at` | Timestamp | Yes | Set when the detail request begins |
| `completed_at` | Timestamp | No | Set when retrieval and any terminal render outcome are known |
| `view_status` | Enum | Yes | `loading`, `rendered`, `partial`, or `error` |
| `distribution_status` | Enum | Yes | `available`, `unavailable`, or `failed` |
| `drivers_status` | Enum | Yes | `available`, `unavailable`, or `failed` |
| `anomalies_status` | Enum | Yes | `available`, `unavailable`, or `failed` |
| `preparation_status` | Enum | Yes | `pending`, `completed`, or `failed` |
| `failure_category` | Enum | No | Required when `view_status = error` |
| `failure_reason` | String | No | Required when any component or preparation fails, or when render fails |
| `correlation_id` | String | No | Shared operational identifier when supported |
| `render_reported_at` | Timestamp | No | Present only after the client reports the final render outcome |

**Validation rules**

- `alert_id` must resolve to exactly one persisted upstream alert identified by `alert_source`.
- `completed_at` is required for terminal `view_status` values `rendered`, `partial`, and `error`.
- `view_status = rendered` requires `distribution_status`, `drivers_status`, and `anomalies_status` all to be `available` and `preparation_status = completed`.
- `view_status = partial` requires at least one component status to be `available`, no component status to be `failed`, and `preparation_status = completed`.
- `view_status = error` is required when any component status is `failed`, when `preparation_status = failed`, or when a client render failure is reported.
- `failure_category` and `failure_reason` are required when `view_status = error`.
- `render_reported_at` is required when the final outcome depends on a render event.

## New Derived Entity: ForecastDistributionContext

**Purpose**: Represents the normalized distribution or uncertainty data returned for the selected alert when forecast distribution context is available.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `alert_detail_load_id` | Identifier | Yes | References one detail-load attempt |
| `forecast_product` | Enum | Yes | Canonical upstream forecast product used by the selected alert context |
| `forecast_window_start` | Timestamp | Yes | Inclusive forecast window start |
| `forecast_window_end` | Timestamp | Yes | Inclusive forecast window end |
| `curve_points` | Collection | Yes | Ordered points for distribution rendering |
| `band_labels` | Collection | No | Present when the distribution is expressed as labeled quantile bands |
| `summary_value` | Decimal | No | Optional point forecast or central estimate shown with the distribution |
| `component_status` | Enum | Yes | `available`, `unavailable`, or `failed` |
| `status_message` | String | No | User-visible explanation when the component is not available |

**Validation rules**

- `forecast_window_end` must not be earlier than `forecast_window_start`.
- `curve_points` must be populated only when `component_status = available`.
- `band_labels`, when present, must align with the structure of `curve_points`.
- `status_message` is required when `component_status = unavailable` or `component_status = failed`.

## New Derived Entity: DriverAttributionContext

**Purpose**: Represents the normalized top-5 driver breakdown returned for the selected alert when attribution context is available.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `alert_detail_load_id` | Identifier | Yes | References one detail-load attempt |
| `component_status` | Enum | Yes | `available`, `unavailable`, or `failed` |
| `drivers` | Collection | No | Ordered ranked driver contributions |
| `rank_limit` | Integer | Yes | Must remain `5` for UC-12 |
| `status_message` | String | No | User-visible explanation when the component is not available |

**Validation rules**

- `rank_limit` must always equal `5`.
- `drivers` may contain at most 5 items and must be ordered by descending rank when `component_status = available`.
- `drivers` must be empty when `component_status = unavailable` or `component_status = failed`.
- `status_message` is required when `component_status = unavailable` or `component_status = failed`.

## New Derived Entity: AnomalyContextWindow

**Purpose**: Represents the normalized anomaly timeline returned for the selected alert when recent anomaly context is available.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `alert_detail_load_id` | Identifier | Yes | References one detail-load attempt |
| `component_status` | Enum | Yes | `available`, `unavailable`, or `failed` |
| `window_start` | Timestamp | Yes | Inclusive start of the anomaly context window |
| `window_end` | Timestamp | Yes | Inclusive end of the anomaly context window |
| `anomaly_points` | Collection | No | Ordered points or event markers shown on the timeline |
| `status_message` | String | No | User-visible explanation when the component is not available |

**Validation rules**

- `window_end` must be later than `window_start`.
- `window_end - window_start` must represent the previous 7-day context window for the selected alert.
- `anomaly_points` must be populated only when `component_status = available`.
- `status_message` is required when `component_status = unavailable` or `component_status = failed`.

## New Derived Entity: AlertDetailView

**Purpose**: Represents the stable backend-to-frontend read model that combines selected-alert metadata, component contexts, and overall display semantics.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `alert_detail_load_id` | Identifier | Yes | Unique link to the observability record |
| `alert_source` | Enum | Yes | `threshold_alert` or `surge_alert` |
| `alert_id` | Identifier | Yes | Selected alert identifier |
| `alert_title` | String | No | Optional concise label suitable for the detail header |
| `service_category` | String | Yes | Canonical category for the selected alert |
| `geography_type` | String | No | Present only when the alert scope is geography-specific |
| `geography_value` | String | No | Present only when `geography_type` is present |
| `alert_triggered_at` | Timestamp | Yes | Time the selected alert was originally created or confirmed |
| `view_status` | Enum | Yes | `loading`, `rendered`, `partial`, or `error` |
| `status_message` | String | No | Required for `partial` and `error` states |
| `forecast_distribution` | Object | No | Present when distribution context is included |
| `driver_attribution` | Object | No | Present when driver context is included |
| `anomaly_context` | Object | No | Present when anomaly context is included |
| `missing_components` | Collection | Yes | Explicit list of unavailable components, empty when none are missing |
| `failed_components` | Collection | Yes | Explicit list of failed components, empty when none failed |

**Validation rules**

- `status_message` is required when `view_status = partial` or `view_status = error`.
- `view_status = rendered` requires all three component objects to be present and no missing or failed components.
- `view_status = partial` requires at least one component object to be present, at least one missing component, and no failed components.
- `view_status = error` requires at least one failed component or a render failure recorded against the load.
- `missing_components` and `failed_components` must use the canonical component names `distribution`, `drivers`, and `anomalies`.
- The selected alert metadata must remain present for every `view_status`, including `loading` and `error`.

## Relationships

- One upstream alert identified by `alert_source` and `alert_id` may produce many `AlertDetailLoadRecord` rows over time.
- One `AlertDetailLoadRecord` may produce zero or one `ForecastDistributionContext`.
- One `AlertDetailLoadRecord` may produce zero or one `DriverAttributionContext`.
- One `AlertDetailLoadRecord` may produce zero or one `AnomalyContextWindow`.
- One `AlertDetailLoadRecord` produces exactly one `AlertDetailView` response shape for the requesting client.

## Derived Invariants

- UC-12 must never duplicate or mutate the persisted source alert entities from UC-10 or UC-11.
- A partial detail view is valid only when at least one supporting component remains reliable to show.
- A component marked `unavailable` must not be rendered as an unlabeled empty visualization.
- Any component marked `failed`, any preparation failure, or any render failure forces the overall alert-detail experience into `error`.
- The anomaly timeline window for UC-12 always covers the previous 7 days relative to the selected alert context.
- Driver attribution for UC-12 always exposes at most the top 5 ranked contributors.
