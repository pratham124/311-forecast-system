# Data Model: Demand Threshold Alerts

## Overview

UC-10 consumes already-published forecast outputs and configured alert thresholds to detect demand spikes for Edmonton 311 service categories and optional geography scopes. The data model reuses upstream forecast lineage and adds only the records needed to evaluate thresholds, suppress duplicate alerts until re-armed, create notification events, and preserve channel-level delivery traceability.

## Reused Entities From Previous Specs

### Entity: ForecastRun

**Purpose**: Represents the forecast-generation attempt that produced the forecast being evaluated for alerting.

**Reuse in UC-10**

- Anchors traceability from a threshold evaluation run back to the triggering forecast workflow.
- Remains upstream-only and is not duplicated by alerting persistence.

### Entity: ForecastVersion / WeeklyForecastVersion

**Purpose**: Represents the stored forecast product whose category, optional geography, forecast window type, and forecast window values are checked against thresholds.

**Reuse in UC-10**

- Supplies the forecast bucket values evaluated by UC-10.
- Remains the source of truth for forecast window type and forecast window identity.

### Entity: ForecastBucket / WeeklyForecastBucket

**Purpose**: Represents the forecasted demand bucket for a specific category, optional geography, forecast window type, and forecast window.

**Reuse in UC-10**

- Supplies the demand value that is compared to the applicable threshold.
- Remains upstream and is not copied into new forecast-storage tables.

## New Entity: ThresholdConfiguration

**Purpose**: Stores one alert threshold rule for a service category, optionally narrowed to a geographic scope, and bound to a forecast window type.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `threshold_configuration_id` | Identifier | Yes | Unique per stored threshold rule |
| `service_category` | String | Yes | Canonical Edmonton 311 category |
| `geography_type` | Enum | No | Present only when the threshold is geography-specific |
| `geography_value` | String | No | Required when `geography_type` is present |
| `forecast_window_type` | Enum | Yes | Canonical window type supplied by the published forecast product for this threshold |
| `threshold_value` | Decimal | Yes | Must be greater than zero |
| `notification_channels` | Collection | Yes | One or more configured alert channels for the owning operational manager |
| `operational_manager_id` | Identifier | Yes | Recipient owner of the threshold rule |
| `status` | Enum | Yes | `active` or `inactive` |
| `effective_from` | Timestamp | Yes | Inclusive activation timestamp |
| `effective_to` | Timestamp | No | Optional end timestamp |

**Validation rules**

- `service_category`, `geography_type`, `geography_value`, and `forecast_window_type` must be unique within the same active time range.
- `geography_value` must be absent when `geography_type` is absent.
- `notification_channels` must contain at least one channel when `status = active`.
- `effective_to`, when present, must be later than `effective_from`.
- Geography-specific thresholds are more specific than category-only thresholds for the same service category and forecast window type.

## New Entity: ThresholdEvaluationRun

**Purpose**: Records one evaluation pass triggered by a published or refreshed forecast.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `threshold_evaluation_run_id` | Identifier | Yes | Unique per evaluation run |
| `forecast_run_id` | Identifier | No | Present when the upstream trigger is a forecast run |
| `forecast_version_reference` | Identifier | Yes | References the concrete forecast product being evaluated |
| `trigger_source` | Enum | Yes | `forecast_publish`, `forecast_refresh`, `scheduled_recheck`, or `manual_replay` |
| `started_at` | Timestamp | Yes | Set when evaluation begins |
| `completed_at` | Timestamp | No | Set when evaluation ends |
| `status` | Enum | Yes | `running`, `completed`, or `completed_with_failures` |
| `evaluated_scope_count` | Integer | Yes | Zero or greater |
| `alert_created_count` | Integer | Yes | Zero or greater |
| `failure_summary` | String | No | Present only when evaluation infrastructure fails for part of the run |

**Validation rules**

- `forecast_version_reference` must resolve to exactly one active forecast product.
- `completed_at` is required for terminal statuses.
- `alert_created_count` must not exceed `evaluated_scope_count`.

## New Entity: ThresholdScopeEvaluation

**Purpose**: Stores the outcome of comparing one forecast scope to its applicable threshold rule.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `threshold_scope_evaluation_id` | Identifier | Yes | Unique per evaluated scope outcome |
| `threshold_evaluation_run_id` | Identifier | Yes | References the owning evaluation run |
| `threshold_configuration_id` | Identifier | No | Null only when no applicable threshold exists |
| `service_category` | String | Yes | Evaluated category |
| `geography_type` | Enum | No | Present only for geography-scoped evaluation |
| `geography_value` | String | No | Present only for geography-scoped evaluation |
| `forecast_window_type` | Enum | Yes | Canonical window type supplied by the published forecast product |
| `forecast_window_start` | Timestamp | Yes | Inclusive evaluated window start |
| `forecast_window_end` | Timestamp | Yes | Inclusive evaluated window end |
| `forecast_bucket_value` | Decimal | Yes | Must be zero or greater |
| `threshold_value` | Decimal | No | Required when a threshold configuration is applied |
| `outcome` | Enum | Yes | `configuration_missing`, `below_or_equal`, `exceeded_alert_created`, `exceeded_suppressed`, or `delivery_failed` |
| `notification_event_id` | Identifier | No | Present for `exceeded_alert_created` and `delivery_failed` |
| `recorded_at` | Timestamp | Yes | Set when the scope evaluation is persisted |

**Validation rules**

- `forecast_window_end` must not be earlier than `forecast_window_start`.
- `forecast_window_type` must match the threshold configuration and published forecast product used for the evaluation.
- `threshold_value` is required unless `outcome = configuration_missing`.
- `forecast_bucket_value <= threshold_value` is required for `below_or_equal`.
- `forecast_bucket_value > threshold_value` is required for `exceeded_alert_created`, `exceeded_suppressed`, and `delivery_failed`.
- `notification_event_id` is required for `delivery_failed` and optional for `exceeded_alert_created` if the event is persisted separately in the same transaction.
- When both a category-only threshold and a category-plus-geography threshold could match the same regional forecast bucket, only the geography-specific threshold may populate `threshold_configuration_id` for that evaluated scope.

## New Entity: ThresholdState

**Purpose**: Tracks whether an evaluated threshold scope is currently re-armed or suppressed after a prior sent alert, using the active threshold settings for that same scope.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `threshold_state_id` | Identifier | Yes | Unique per active threshold scope state |
| `threshold_configuration_id` | Identifier | Yes | References the threshold rule being tracked |
| `service_category` | String | Yes | Canonical category of the tracked scope |
| `geography_type` | Enum | No | Present only for geography-scoped state |
| `geography_value` | String | No | Present only for geography-scoped state |
| `forecast_window_type` | Enum | Yes | Canonical window type supplied by the published forecast product |
| `forecast_window_start` | Timestamp | Yes | Inclusive start of the tracked forecast window |
| `forecast_window_end` | Timestamp | Yes | Inclusive end of the tracked forecast window |
| `current_state` | Enum | Yes | `below_or_equal` or `above_threshold_alerted` |
| `last_forecast_bucket_value` | Decimal | Yes | Most recent evaluated forecast bucket value |
| `last_threshold_value` | Decimal | Yes | Threshold value used in the most recent evaluation |
| `last_evaluated_at` | Timestamp | Yes | Most recent evaluation timestamp |
| `last_notification_event_id` | Identifier | No | Present when `current_state = above_threshold_alerted` |

**Validation rules**

- The combination of `service_category`, `geography_type`, `geography_value`, `forecast_window_type`, `forecast_window_start`, and `forecast_window_end` must be unique.
- `forecast_window_end` must not be earlier than `forecast_window_start`.
- `last_notification_event_id` is required when `current_state = above_threshold_alerted`.
- A scope may transition from `below_or_equal` to `above_threshold_alerted` only when the current evaluation exceeds the currently active threshold for that same scope.
- A scope re-arms by transitioning from `above_threshold_alerted` to `below_or_equal` only when the current evaluation is less than or equal to the currently active threshold for that same scope.
- If threshold settings change between consecutive evaluations of the same scope, `threshold_configuration_id` and `last_threshold_value` must be updated to the newly applied active threshold before evaluating the next state transition.

**State transitions**

`below_or_equal` → `above_threshold_alerted`  
`above_threshold_alerted` → `below_or_equal`  
`below_or_equal` → `below_or_equal`  
`above_threshold_alerted` → `above_threshold_alerted`

No other transitions are valid.

## New Entity: NotificationEvent

**Purpose**: Represents one alert created when a threshold-crossing exceedance occurs.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `notification_event_id` | Identifier | Yes | Unique per alert event |
| `threshold_evaluation_run_id` | Identifier | Yes | References the run that produced the alert |
| `threshold_configuration_id` | Identifier | Yes | References the threshold rule that triggered the alert |
| `service_category` | String | Yes | Alerted category |
| `geography_type` | Enum | No | Present only for geography-scoped alerts |
| `geography_value` | String | No | Present only for geography-scoped alerts |
| `forecast_window_start` | Timestamp | Yes | Inclusive forecast window start |
| `forecast_window_end` | Timestamp | Yes | Inclusive forecast window end |
| `forecast_window_type` | Enum | Yes | Canonical window type supplied by the published forecast product |
| `forecast_value` | Decimal | Yes | Forecast bucket value that exceeded the threshold |
| `threshold_value` | Decimal | Yes | Threshold crossed by the alert |
| `overall_delivery_status` | Enum | Yes | `delivered`, `partial_delivery`, `retry_pending`, or `manual_review_required` |
| `created_at` | Timestamp | Yes | Set when the alert event is created |
| `delivered_at` | Timestamp | No | Present when at least one channel succeeds |
| `follow_up_reason` | String | No | Required for retry/manual review outcomes |

**Validation rules**

- `forecast_value` must be greater than `threshold_value`.
- `delivered_at` is required for `delivered` and `partial_delivery`.
- `follow_up_reason` is required for `retry_pending` and `manual_review_required`.
- `overall_delivery_status = delivered` is valid only when every configured channel attempt succeeded.
- `overall_delivery_status = partial_delivery` is valid only when at least one configured channel succeeded and at least one channel failed.
- `overall_delivery_status = retry_pending` or `manual_review_required` is valid only when no configured channel attempt succeeded.

## New Entity: NotificationChannelAttempt

**Purpose**: Stores the outcome of one channel-specific delivery attempt for a notification event.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `notification_channel_attempt_id` | Identifier | Yes | Unique per channel attempt |
| `notification_event_id` | Identifier | Yes | References the owning alert event |
| `channel_type` | Enum | Yes | `email`, `sms`, `dashboard`, or another approved channel |
| `attempt_number` | Integer | Yes | Starts at 1 and increments for retries on the same channel |
| `attempted_at` | Timestamp | Yes | Set when delivery is attempted |
| `status` | Enum | Yes | `succeeded` or `failed` |
| `failure_reason` | String | No | Required when `status = failed` |
| `provider_reference` | String | No | Optional provider correlation identifier |

**Validation rules**

- `attempt_number` must be 1 or greater.
- `failure_reason` is required when `status = failed`.
- At least one `NotificationChannelAttempt` with `status = succeeded` is required for `NotificationEvent.overall_delivery_status` to be `delivered` or `partial_delivery`.
- All configured channels for the alert must produce an attempt record, even if one succeeds earlier than the others.

## Relationships

- One `ThresholdConfiguration` can participate in many `ThresholdScopeEvaluation`, `ThresholdState`, and `NotificationEvent` records.
- One `ThresholdEvaluationRun` owns many `ThresholdScopeEvaluation` records and may create many `NotificationEvent` records.
- One `NotificationEvent` owns many `NotificationChannelAttempt` records.
- One `ThresholdState` tracks one service category, optional geography, forecast window type, and forecast window scope at a time and may change threshold configuration when active settings change.

## Outcome Vocabulary

- `configuration_missing`: no applicable threshold rule exists for the evaluated scope
- `below_or_equal`: threshold exists and the forecast is at or below it
- `exceeded_alert_created`: threshold exists, the forecast crossed above it, and an alert event was created
- `exceeded_suppressed`: threshold exists, the forecast remains above it, and an earlier alert still suppresses duplicates
- `delivery_failed`: an alert event was created but no configured channel succeeded and the event was moved into follow-up

## Delivery Status Vocabulary

- `delivered`: every configured channel attempt for the alert succeeded
- `partial_delivery`: at least one configured channel attempt succeeded and at least one configured channel attempt failed
- `retry_pending`: no configured channel attempt succeeded and the alert remains queued for retry
- `manual_review_required`: no configured channel attempt succeeded and the alert requires operator follow-up
