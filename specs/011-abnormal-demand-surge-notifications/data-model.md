# Data Model: Abnormal Demand Surge Notifications

## Overview

UC-11 extends the lineage defined by UC-01 through UC-10 without redefining those shared entities. The surge workflow consumes successful ingestion outputs, active LightGBM forecast lineage, and existing notification semantics, then adds only the surge-specific records needed to configure detection thresholds, persist residual-based candidates, confirm or filter them, suppress duplicates until re-armed, create surge notifications, and preserve channel-level delivery traceability.

## Reused Shared Entities and Vocabulary

UC-11 references the following shared entities from earlier use cases and does not redefine their fields here:

- UC-01: `IngestionRun`, `DatasetVersion`
- UC-02: `ValidationRun`, `CleanedDatasetVersion`, `CurrentDatasetMarker` where approved historical demand lineage is needed for residual-baseline derivation or audit
- UC-03: `ForecastRun`, `ForecastVersion`, `ForecastBucket`, `CurrentForecastMarker`
- UC-04: `WeeklyForecastRun`, `WeeklyForecastVersion`, `WeeklyForecastBucket`, `CurrentWeeklyForecastMarker` for upstream lineage context only; UC-11 does not select weekly forecast products during surge evaluation
- UC-10: delivery-status vocabulary and notification-review expectations only; UC-11 does not reuse UC-10 persistence tables because surge records must remain separate

UC-11 also reuses these shared modeling concepts without redefining the upstream entities:

- Canonical evaluation scope: service category plus optional geography
- Active forecast lineage as the source of truth for P50 forecast values
- Delivery-status vocabulary: `delivered`, `partial_delivery`, `retry_pending`, `manual_review_required`

## New Entity: SurgeDetectionConfiguration

**Purpose**: Stores one surge-detection rule for a service category, optionally narrowed to a geography scope, including the dual confirmation thresholds and rolling-baseline parameters used by UC-11 against the daily forecast lineage from UC-03.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `surge_detection_configuration_id` | Identifier | Yes | Unique per stored surge rule |
| `service_category` | String | Yes | Canonical Edmonton 311 category |
| `geography_type` | String | No | Present only when the rule is geography-specific |
| `geography_value` | String | No | Required when `geography_type` is present |
| `forecast_product` | Enum | Yes | Must be `daily`, referencing the active UC-03 `ForecastVersion` and `ForecastBucket` used for residual comparison; `weekly` is not allowed |
| `z_score_threshold` | Decimal | Yes | Must be greater than zero |
| `percent_above_forecast_floor` | Decimal | Yes | Expressed as percentage above P50 forecast; must be greater than zero |
| `rolling_baseline_window_count` | Integer | Yes | Number of prior comparable residual observations used in the z-score baseline; must be at least 2 |
| `notification_channels` | Collection | Yes | One or more configured alert channels |
| `operational_manager_id` | Identifier | Yes | Recipient owner of the rule |
| `status` | Enum | Yes | `active` or `inactive` |
| `effective_from` | Timestamp | Yes | Inclusive activation timestamp |
| `effective_to` | Timestamp | No | Optional end timestamp |

**Validation rules**

- `forecast_product` must always be `daily`; UC-11 configurations must reference only UC-03 forecast lineage and must reject UC-04 weekly products.
- For the same `service_category` and overlapping active time range, a geography-specific rule overrides a category-wide rule when both could match the evaluated scope.
- Overlapping configurations at the same specificity level must be rejected at authoring time; this includes category-wide peers for the same `service_category` and geography-specific peers for the same `service_category`, `geography_type`, and `geography_value`.
- `geography_value` must be absent when `geography_type` is absent.
- `z_score_threshold` and `percent_above_forecast_floor` must both be greater than zero.
- `rolling_baseline_window_count` must be at least 2.
- `notification_channels` must contain at least one channel when `status = active`.
- `effective_to`, when present, must be later than `effective_from`.

## New Entity: SurgeEvaluationRun

**Purpose**: Records one ingestion-triggered or replayed UC-11 evaluation pass.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `surge_evaluation_run_id` | Identifier | Yes | Unique per evaluation run |
| `ingestion_run_id` | Identifier | Yes | References the successful UC-01 ingestion run that triggered the evaluation |
| `trigger_source` | Enum | Yes | `ingestion_completion` or `manual_replay` |
| `started_at` | Timestamp | Yes | Set when evaluation begins |
| `completed_at` | Timestamp | No | Set when evaluation ends |
| `status` | Enum | Yes | `running`, `completed`, or `completed_with_failures` |
| `evaluated_scope_count` | Integer | Yes | Zero or greater |
| `candidate_count` | Integer | Yes | Zero or greater |
| `confirmed_count` | Integer | Yes | Zero or greater |
| `notification_created_count` | Integer | Yes | Zero or greater |
| `failure_summary` | String | No | Present only when run-level infrastructure failures occur |

**Validation rules**

- `ingestion_run_id` must resolve to exactly one successful UC-01 ingestion run.
- `completed_at` is required for terminal statuses.
- `confirmed_count` must not exceed `candidate_count`.
- `notification_created_count` must not exceed `confirmed_count`.

## New Entity: SurgeCandidate

**Purpose**: Stores one residual-based detector result for an evaluated scope after a successful ingestion run.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `surge_candidate_id` | Identifier | Yes | Unique per detector result |
| `surge_evaluation_run_id` | Identifier | Yes | References the owning evaluation run |
| `surge_detection_configuration_id` | Identifier | Yes | References the applied surge rule |
| `forecast_run_id` | Identifier | Yes | References the UC-03 daily forecast run used for residual comparison |
| `forecast_version_id` | Identifier | Yes | References the active UC-03 daily `ForecastVersion` used for the evaluated scope and window |
| `service_category` | String | Yes | Evaluated category |
| `geography_type` | String | No | Present only for geography-scoped evaluation |
| `geography_value` | String | No | Present only for geography-scoped evaluation |
| `evaluation_window_start` | Timestamp | Yes | Inclusive start of the actual-versus-forecast comparison window |
| `evaluation_window_end` | Timestamp | Yes | Inclusive end of the comparison window |
| `actual_demand_value` | Decimal | Yes | Aggregated actual demand from the new ingestion slice; must be zero or greater |
| `forecast_p50_value` | Decimal | Yes | Active P50 forecast value for the same scope and window; must be zero or greater |
| `residual_value` | Decimal | Yes | `actual_demand_value - forecast_p50_value` |
| `residual_z_score` | Decimal | No | Present when the rolling baseline is available |
| `percent_above_forecast` | Decimal | No | Present when `forecast_p50_value > 0`; may be null when `forecast_p50_value = 0` |
| `rolling_baseline_mean` | Decimal | No | Present when z-score calculation is available |
| `rolling_baseline_stddev` | Decimal | No | Present when z-score calculation is available |
| `candidate_status` | Enum | Yes | `flagged`, `below_candidate_threshold`, or `detector_failed` |
| `detected_at` | Timestamp | Yes | Set when detector output is persisted |
| `correlation_id` | String | No | Shared operational identifier when supported |
| `failure_reason` | String | No | Required when `candidate_status = detector_failed` |

**Validation rules**

- `forecast_run_id` and `forecast_version_id` are required and must reference the UC-03 daily forecast lineage selected by the applied `SurgeDetectionConfiguration`.
- `evaluation_window_end` must not be earlier than `evaluation_window_start`.
- `actual_demand_value` and `forecast_p50_value` must be zero or greater.
- `residual_z_score`, `rolling_baseline_mean`, and `rolling_baseline_stddev` must be present together when z-score computation succeeds.
- `percent_above_forecast` may be absent only when `forecast_p50_value = 0`.
- When `forecast_p50_value = 0` and `actual_demand_value > 0`, confirmation logic must treat the percent-floor check as passed even though `percent_above_forecast` remains null.
- When `forecast_p50_value = 0` and `actual_demand_value = 0`, confirmation logic must treat the percent-floor check as failed.
- `failure_reason` is required when `candidate_status = detector_failed`.
- `candidate_status = flagged` is valid only when the detector stage produced a residual-based anomaly signal requiring confirmation.

## New Entity: SurgeConfirmationOutcome

**Purpose**: Stores the confirmation decision for one surge candidate after dual-threshold validation and active-surge suppression checks.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `surge_confirmation_outcome_id` | Identifier | Yes | Unique per candidate confirmation result |
| `surge_candidate_id` | Identifier | Yes | References the candidate being decided |
| `z_score_threshold` | Decimal | Yes | Threshold applied for confirmation |
| `percent_above_forecast_floor` | Decimal | Yes | Floor applied for confirmation |
| `z_score_check_passed` | Boolean | Yes | `true` only when candidate z-score exceeds threshold |
| `percent_floor_check_passed` | Boolean | Yes | `true` only when percent-above-forecast exceeds floor |
| `outcome` | Enum | Yes | `confirmed`, `filtered`, `suppressed_active_surge`, or `failed` |
| `surge_state_id` | Identifier | No | Present when state was consulted or updated |
| `surge_notification_event_id` | Identifier | No | Present only when confirmation created a notification event |
| `confirmed_at` | Timestamp | Yes | Set when the confirmation result is persisted |
| `failure_reason` | String | No | Required when `outcome = failed` |

**Validation rules**

- `z_score_threshold` and `percent_above_forecast_floor` must match the applied `SurgeDetectionConfiguration`.
- `outcome = confirmed` requires both check fields to be `true`.
- `outcome = filtered` requires at least one check field to be `false`.
- `outcome = suppressed_active_surge` requires both check fields to be `true` and an already-active `SurgeState`.
- `surge_notification_event_id` is required only for `confirmed`.
- `failure_reason` is required only for `failed`.
- `percent_floor_check_passed` may be `true` when `SurgeCandidate.forecast_p50_value = 0` only if `SurgeCandidate.actual_demand_value > 0`.

## New Entity: SurgeState

**Purpose**: Tracks whether a canonical scope is currently in confirmed surge state and whether notification eligibility has been consumed for the active interval.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `surge_state_id` | Identifier | Yes | Unique per tracked surge scope |
| `surge_detection_configuration_id` | Identifier | Yes | References the applied surge rule |
| `service_category` | String | Yes | Canonical category of the tracked scope |
| `geography_type` | String | No | Present only for geography-scoped state |
| `geography_value` | String | No | Present only for geography-scoped state |
| `forecast_product` | Enum | Yes | Always `daily` for UC-11 surge-state tracking |
| `current_state` | Enum | Yes | `normal` or `active_surge` |
| `notification_armed` | Boolean | Yes | `true` only when the scope is eligible to notify on the next confirmed surge entry |
| `active_since` | Timestamp | No | Present only when `current_state = active_surge` |
| `returned_to_normal_at` | Timestamp | No | Present only after an active surge ends |
| `last_surge_candidate_id` | Identifier | No | Most recent evaluated candidate for the scope |
| `last_confirmation_outcome_id` | Identifier | No | Most recent confirmation result for the scope |
| `last_notification_event_id` | Identifier | No | Present when the active interval already produced a notification |
| `last_evaluated_at` | Timestamp | Yes | Most recent evaluation time |

**Validation rules**

- The combination of `service_category`, `geography_type`, `geography_value`, and `forecast_product` must be unique, with `forecast_product` fixed to `daily`.
- `active_since` is required when `current_state = active_surge`.
- `last_notification_event_id` is required when `current_state = active_surge` and `notification_armed = false`.
- A scope may transition from `normal` to `active_surge` only when a confirmation outcome is `confirmed`.
- A scope may transition from `active_surge` to `normal` only when a later evaluation no longer satisfies both confirmation checks.
- `notification_armed` must become `true` again only after the scope returns to `normal`.

**State transitions**

`normal` → `active_surge`  
`active_surge` → `normal`  
`normal` → `normal`  
`active_surge` → `active_surge`

No other transitions are valid.

## New Entity: SurgeNotificationEvent

**Purpose**: Represents one alert created when a scope newly enters confirmed surge state.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `surge_notification_event_id` | Identifier | Yes | Unique per surge alert event |
| `surge_evaluation_run_id` | Identifier | Yes | References the evaluation run that produced the alert |
| `surge_candidate_id` | Identifier | Yes | References the confirmed candidate |
| `surge_detection_configuration_id` | Identifier | Yes | References the surge rule that triggered the alert |
| `service_category` | String | Yes | Alerted category |
| `geography_type` | String | No | Present only for geography-scoped alerts |
| `geography_value` | String | No | Present only for geography-scoped alerts |
| `forecast_product` | Enum | Yes | Always `daily`, matching the UC-03 forecast product used during confirmation |
| `evaluation_window_start` | Timestamp | Yes | Inclusive comparison window start |
| `evaluation_window_end` | Timestamp | Yes | Inclusive comparison window end |
| `actual_demand_value` | Decimal | Yes | Actual demand observed |
| `forecast_p50_value` | Decimal | Yes | Forecast value used for comparison |
| `residual_value` | Decimal | Yes | Residual value communicated in the alert |
| `residual_z_score` | Decimal | Yes | Confirmed z-score communicated in the alert |
| `percent_above_forecast` | Decimal | No | Confirmed percent-above-forecast communicated in the alert when the forecast denominator is non-zero |
| `overall_delivery_status` | Enum | Yes | `delivered`, `partial_delivery`, `retry_pending`, or `manual_review_required` |
| `created_at` | Timestamp | Yes | Set when the alert event is created |
| `delivered_at` | Timestamp | No | Present when at least one channel succeeds |
| `follow_up_reason` | String | No | Required for retry/manual-review outcomes |
| `correlation_id` | String | No | Shared operational identifier when supported |

**Validation rules**

- `evaluation_window_end` must not be earlier than `evaluation_window_start`.
- `residual_z_score` must reflect a confirmed surge candidate.
- `percent_above_forecast` must reflect a confirmed surge candidate when `forecast_p50_value > 0` and may be null when `forecast_p50_value = 0`.
- `delivered_at` is required for `delivered` and `partial_delivery`.
- `follow_up_reason` is required for `retry_pending` and `manual_review_required`.
- `overall_delivery_status = delivered` is valid only when every configured channel attempt succeeded.
- `overall_delivery_status = partial_delivery` is valid only when at least one configured channel succeeded and at least one configured channel failed.
- `overall_delivery_status = retry_pending` or `manual_review_required` is valid only when no configured channel attempt succeeded.

## New Entity: SurgeNotificationChannelAttempt

**Purpose**: Stores the outcome of one channel-specific delivery attempt for a surge notification event.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `surge_notification_channel_attempt_id` | Identifier | Yes | Unique per channel attempt |
| `surge_notification_event_id` | Identifier | Yes | References the owning surge alert event |
| `channel_type` | Enum | Yes | `email`, `sms`, `dashboard`, or another approved channel |
| `attempt_number` | Integer | Yes | Starts at 1 and increments for retries on the same channel |
| `attempted_at` | Timestamp | Yes | Set when delivery is attempted |
| `status` | Enum | Yes | `succeeded` or `failed` |
| `failure_reason` | String | No | Required when `status = failed` |
| `provider_reference` | String | No | Optional provider correlation identifier |

**Validation rules**

- `attempt_number` must be 1 or greater.
- `failure_reason` is required when `status = failed`.
- At least one `SurgeNotificationChannelAttempt` with `status = succeeded` is required for `SurgeNotificationEvent.overall_delivery_status` to be `delivered` or `partial_delivery`.
- All configured channels for the surge alert must produce an attempt record, even if one succeeds earlier than the others.

## Relationships

- One `SurgeDetectionConfiguration` can participate in many `SurgeCandidate`, `SurgeState`, and `SurgeNotificationEvent` records.
- One `SurgeEvaluationRun` owns many `SurgeCandidate` records and may create many `SurgeNotificationEvent` records.
- One `SurgeCandidate` may produce one `SurgeConfirmationOutcome`.
- One `SurgeConfirmationOutcome` may create one `SurgeNotificationEvent` when the scope newly enters surge state.
- One `SurgeNotificationEvent` owns many `SurgeNotificationChannelAttempt` records.
- One `SurgeState` tracks one canonical scope at a time and changes only through evaluated confirmation outcomes.

## Candidate Status Vocabulary

- `flagged`: the residual-based detector produced a candidate that must be confirmed
- `below_candidate_threshold`: the evaluated scope did not produce a detector-stage candidate
- `detector_failed`: detector processing failed before candidate evaluation could complete

## Confirmation Outcome Vocabulary

- `confirmed`: both confirmation thresholds passed and the scope newly entered surge state
- `filtered`: the candidate failed at least one confirmation threshold
- `suppressed_active_surge`: both thresholds passed but the scope was already in active surge state
- `failed`: confirmation processing failed and no notification was created

## Delivery Status Vocabulary

- `delivered`: every configured channel attempt for the alert succeeded
- `partial_delivery`: at least one configured channel attempt succeeded and at least one configured channel attempt failed
- `retry_pending`: no configured channel attempt succeeded and the alert remains queued for retry
- `manual_review_required`: no configured channel attempt succeeded and the alert requires operator follow-up
