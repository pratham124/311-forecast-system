# Data Model: Storm Mode Forecast Adjustments

## Overview

UC-15 extends the shared lineage defined by UC-01 through UC-14 without redefining those upstream entities. The feature consumes approved demand lineage, retained forecast lineage, weather-retrieval conventions, existing alert and notification workflows, and established observability patterns, then adds only the UC-15-specific run, trigger, activation, forecast-adjustment, and alert-evaluation records required to support validated storm-mode activation, safe baseline fallback, adjustment failure reversion, and traceable notification outcomes.

## Reused Shared Entities and Vocabulary

UC-15 references shared entities and vocabularies from earlier use cases and does not redefine their fields here:

- UC-01 and UC-02: ingestion and approved cleaned-demand lineage used as the canonical actual-demand context
- UC-03 and UC-04: retained daily and weekly forecast lineage, including `ForecastRun`, `ForecastVersion`, `ForecastBucket`, `WeeklyForecastRun`, `WeeklyForecastVersion`, and `WeeklyForecastBucket`
- UC-05 through UC-08: visualization, historical-alignment, and normalized-scope conventions reused when storm-mode outcomes are inspected downstream
- UC-09: approved weather-provider, geography-alignment, and time-bucket matching conventions for external weather context
- UC-10: `ThresholdConfiguration`, `ThresholdEvaluationRun`, `ThresholdScopeEvaluation`, `NotificationEvent`, and `NotificationChannelAttempt` as the existing threshold-alert and delivery source of truth
- UC-11: `SurgeNotificationEvent` and `SurgeNotificationChannelAttempt` as the existing surge-notification lineage when storm-mode-sensitive evaluation reuses that path
- UC-12 through UC-14: authenticated observability, correlation, render or detail diagnostics, and planner-facing typed review conventions

UC-15 also reuses these shared modeling concepts without redefining upstream entities:

- Canonical evaluation scope: service category plus optional geography plus effective time window
- Structured operational correlation using evaluation id, request id, actor identity, timestamps, and optional correlation id
- Delivery-status vocabulary already established by UC-10 and UC-11: `delivered`, `partial_delivery`, `retry_pending`, `manual_review_required`

## Canonical UC-15 Vocabulary

### Trigger Outcome

- `validated`
- `rejected`
- `weather_unavailable`
- `no_trigger`

### Activation Status

- `active`
- `inactive`
- `reverted_to_baseline`
- `expired`

### Forecast Adjustment Status

- `storm_adjusted`
- `baseline_applied`
- `adjustment_failed`

### Alert Sensitivity Status

- `storm_adjusted`
- `baseline_applied`
- `not_applicable`

### Alert Evaluation Outcome

- `no_alert`
- `alert_created`
- `baseline_only`
- `evaluation_failed`

### Shared Notification Reference Type

- `threshold_alert`
- `surge_alert`

## New Entity: StormModeEvaluationRun

**Purpose**: Records one storm-mode monitoring, decisioning, and downstream-adjustment pass for one monitoring cycle, forecast refresh, or equivalent replay context.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `storm_mode_evaluation_run_id` | Identifier | Yes | Unique per storm-mode decision pass |
| `trigger_source` | Enum | Yes | `scheduled_monitoring`, `forecast_refresh`, or `manual_replay` |
| `started_at` | Timestamp | Yes | Set when storm-mode evaluation begins |
| `completed_at` | Timestamp | No | Required when the run reaches a terminal state |
| `status` | Enum | Yes | `running`, `completed`, or `completed_with_failures` |
| `evaluated_scope_count` | Integer | Yes | Zero or greater |
| `validated_trigger_count` | Integer | Yes | Zero or greater |
| `activation_count` | Integer | Yes | Zero or greater |
| `baseline_reversion_count` | Integer | Yes | Zero or greater |
| `linked_notification_count` | Integer | Yes | Zero or greater |
| `failure_summary` | String | No | Present only when infrastructure or downstream adjustment failures occur |
| `correlation_id` | String | No | Shared operational identifier when supported |

**Validation rules**

- `completed_at` is required for terminal `status` values.
- `validated_trigger_count` must not exceed `evaluated_scope_count`.
- `activation_count` must not exceed `validated_trigger_count`.
- `baseline_reversion_count` must not exceed `activation_count`.
- `linked_notification_count` must not exceed `activation_count`.

## New Entity: StormModeTriggerAssessment

**Purpose**: Records storm-trigger detection and validation for one canonical scope inside a storm-mode evaluation run.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `storm_mode_trigger_assessment_id` | Identifier | Yes | Unique per scope-level trigger assessment |
| `storm_mode_evaluation_run_id` | Identifier | Yes | References the owning evaluation run |
| `weather_source` | Enum | Yes | Approved external source used for the assessment |
| `service_category` | String | No | Present when the assessment is category-scoped |
| `geography_type` | String | No | Present only for geography-scoped assessment |
| `geography_value` | String | No | Required when `geography_type` is present |
| `effective_window_start` | Timestamp | Yes | Inclusive start of the evaluated storm-impact window |
| `effective_window_end` | Timestamp | Yes | Inclusive end of the evaluated storm-impact window |
| `trigger_outcome` | Enum | Yes | `validated`, `rejected`, `weather_unavailable`, or `no_trigger` |
| `detected_condition_summary` | String | No | Present when a potential storm-related weather signal is detected |
| `validation_reason` | String | No | Required for `rejected` and `weather_unavailable`; optional for `no_trigger` |
| `validated_at` | Timestamp | No | Required when `trigger_outcome = validated` |
| `correlation_id` | String | No | Shared operational identifier when supported |

**Validation rules**

- `effective_window_end` must not be earlier than `effective_window_start`.
- `geography_value` must be absent when `geography_type` is absent.
- `validated_at` is required only when `trigger_outcome = validated`.
- `validation_reason` is required when `trigger_outcome = rejected` or `trigger_outcome = weather_unavailable`.
- `detected_condition_summary` is required when `trigger_outcome = validated` or `trigger_outcome = rejected`.

## New Entity: StormModeActivation

**Purpose**: Records the effective storm-mode state and parameter profile for one validated scope and time window.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `storm_mode_activation_id` | Identifier | Yes | Unique per activation record |
| `storm_mode_trigger_assessment_id` | Identifier | Yes | References the validated or terminal trigger assessment |
| `service_category` | String | No | Present when the activation is category-scoped |
| `geography_type` | String | No | Present only for geography-scoped activation |
| `geography_value` | String | No | Required when `geography_type` is present |
| `effective_window_start` | Timestamp | Yes | Inclusive start of the activation window |
| `effective_window_end` | Timestamp | Yes | Inclusive end of the activation window |
| `activation_status` | Enum | Yes | `active`, `inactive`, `reverted_to_baseline`, or `expired` |
| `effective_uncertainty_profile` | Object | No | Required when storm mode becomes `active` or `reverted_to_baseline` |
| `effective_alert_sensitivity_profile` | Object | No | Required when storm mode becomes `active` or `reverted_to_baseline` |
| `activated_at` | Timestamp | No | Required when `activation_status = active` |
| `deactivated_at` | Timestamp | No | Required when `activation_status = inactive` or `expired` |
| `reversion_reason` | String | No | Required when `activation_status = reverted_to_baseline` |

**Validation rules**

- `effective_window_end` must not be earlier than `effective_window_start`.
- `geography_value` must be absent when `geography_type` is absent.
- `activated_at` is required when `activation_status = active`.
- `deactivated_at` is required when `activation_status = inactive` or `activation_status = expired`.
- `reversion_reason` is required when `activation_status = reverted_to_baseline`.
- `StormModeActivation` may be `active` only when the referenced `StormModeTriggerAssessment.trigger_outcome = validated`.

## New Entity: StormModeForecastAdjustment

**Purpose**: Records whether forecast uncertainty was widened or reverted to baseline for one activation and one reused retained forecast reference.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `storm_mode_forecast_adjustment_id` | Identifier | Yes | Unique per forecast-adjustment record |
| `storm_mode_activation_id` | Identifier | Yes | References the owning activation |
| `forecast_run_id` | Identifier | No | Present when a retained daily or weekly forecast run is linked |
| `forecast_version_id` | Identifier | No | Present when a retained forecast version is linked |
| `forecast_product_name` | String | Yes | Canonical forecast product evaluated for storm adjustment |
| `adjustment_status` | Enum | Yes | `storm_adjusted`, `baseline_applied`, or `adjustment_failed` |
| `baseline_uncertainty_summary` | Object | Yes | Snapshot of the comparable baseline uncertainty parameters |
| `effective_uncertainty_summary` | Object | Yes | Snapshot of the final uncertainty parameters applied |
| `uncertainty_widening_applied` | Boolean | Yes | `true` only when wider-than-baseline uncertainty was applied |
| `adjusted_at` | Timestamp | Yes | Set when the adjustment outcome is recorded |
| `failure_reason` | String | No | Required when `adjustment_status = adjustment_failed` |

**Validation rules**

- `forecast_version_id` requires `forecast_product_name`.
- `uncertainty_widening_applied = true` is valid only when `adjustment_status = storm_adjusted`.
- `uncertainty_widening_applied = false` is required when `adjustment_status = baseline_applied` or `adjustment_status = adjustment_failed`.
- `failure_reason` is required when `adjustment_status = adjustment_failed`.
- `effective_uncertainty_summary` must equal `baseline_uncertainty_summary` when `adjustment_status = baseline_applied` or `adjustment_status = adjustment_failed`.

## New Entity: StormModeAlertEvaluation

**Purpose**: Records the effective alert-sensitivity decision and downstream alert outcome for one activation, including linkage to the reused shared notification workflow when an alert is created.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `storm_mode_alert_evaluation_id` | Identifier | Yes | Unique per alert-evaluation record |
| `storm_mode_activation_id` | Identifier | Yes | References the owning activation |
| `threshold_evaluation_run_id` | Identifier | No | Present when UC-10 threshold evaluation is the downstream alert path |
| `service_category` | String | No | Present when the evaluation is category-scoped |
| `geography_type` | String | No | Present only for geography-scoped evaluation |
| `geography_value` | String | No | Required when `geography_type` is present |
| `alert_sensitivity_status` | Enum | Yes | `storm_adjusted`, `baseline_applied`, or `not_applicable` |
| `effective_alert_sensitivity_summary` | Object | Yes | Snapshot of the final alert-sensitivity parameters used |
| `baseline_alert_sensitivity_summary` | Object | Yes | Snapshot of baseline alert-sensitivity parameters for comparison |
| `evaluation_outcome` | Enum | Yes | `no_alert`, `alert_created`, `baseline_only`, or `evaluation_failed` |
| `notification_reference_type` | Enum | No | `threshold_alert` or `surge_alert`; required when an alert is created |
| `notification_reference_id` | Identifier | No | Required when an alert is created |
| `notification_delivery_status` | Enum | No | Reuses shared delivery vocabulary when a linked notification exists |
| `evaluated_at` | Timestamp | Yes | Set when the alert-evaluation outcome is recorded |
| `failure_reason` | String | No | Required when `evaluation_outcome = evaluation_failed` |

**Validation rules**

- `geography_value` must be absent when `geography_type` is absent.
- `notification_reference_type` and `notification_reference_id` are required when `evaluation_outcome = alert_created`.
- `notification_delivery_status` may be present only when `notification_reference_id` is present.
- `failure_reason` is required when `evaluation_outcome = evaluation_failed`.
- `alert_sensitivity_status = baseline_applied` is required when the linked `StormModeForecastAdjustment.adjustment_status = adjustment_failed` for the same activation.
- `evaluation_outcome = baseline_only` is valid only when `alert_sensitivity_status = baseline_applied` or `alert_sensitivity_status = not_applicable`.

## New Derived Entity: StormModeActivationView

**Purpose**: Represents the stable authenticated diagnostic payload for current storm-mode activation state by scope.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `storm_mode_activation_id` | Identifier | Yes | Unique link to the activation record |
| `service_category` | String | No | Present when scoped by category |
| `geography_type` | String | No | Present only for geography-scoped activation |
| `geography_value` | String | No | Present only when `geography_type` is present |
| `effective_window_start` | Timestamp | Yes | Inclusive start of the activation window |
| `effective_window_end` | Timestamp | Yes | Inclusive end of the activation window |
| `activation_status` | Enum | Yes | `active`, `inactive`, `reverted_to_baseline`, or `expired` |
| `effective_uncertainty_profile` | Object | No | Present when the activation carries parameter context |
| `effective_alert_sensitivity_profile` | Object | No | Present when the activation carries parameter context |
| `status_message` | String | No | Required for `inactive`, `reverted_to_baseline`, and `expired` states |
| `correlation_id` | String | No | Shared operational identifier when supported |

**Validation rules**

- `status_message` is required when `activation_status = reverted_to_baseline`.
- `effective_uncertainty_profile` and `effective_alert_sensitivity_profile` must not be omitted for `activation_status = active`.

## New Derived Entity: StormModeEvaluationView

**Purpose**: Represents the stable authenticated diagnostic payload for one detailed storm-mode evaluation.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `storm_mode_evaluation_run_id` | Identifier | Yes | Unique evaluation identifier |
| `trigger_source` | Enum | Yes | `scheduled_monitoring`, `forecast_refresh`, or `manual_replay` |
| `status` | Enum | Yes | `running`, `completed`, or `completed_with_failures` |
| `started_at` | Timestamp | Yes | Evaluation start time |
| `completed_at` | Timestamp | No | Present when terminal |
| `correlation_id` | String | No | Shared operational identifier when supported |
| `trigger_assessments` | Collection | Yes | Ordered scope-level trigger assessments |
| `activations` | Collection | Yes | Ordered scope-level activation records |
| `forecast_adjustments` | Collection | Yes | Ordered forecast-adjustment records |
| `alert_evaluations` | Collection | Yes | Ordered alert-evaluation records |
| `failure_summary` | String | No | Present when the run completed with failures |

**Validation rules**

- `completed_at` is required when `status = completed` or `status = completed_with_failures`.
- Every linked record in the collections must reference the same `storm_mode_evaluation_run_id` through its owning entities.

## Relationships

- One `StormModeEvaluationRun` owns many `StormModeTriggerAssessment` records.
- One `StormModeTriggerAssessment` may produce zero or one `StormModeActivation`.
- One `StormModeActivation` may produce zero or one `StormModeForecastAdjustment`.
- One `StormModeActivation` may produce zero or one `StormModeAlertEvaluation`.
- One `StormModeActivation` may produce exactly one `StormModeActivationView` representation for the current diagnostic read path.
- One `StormModeEvaluationRun` may produce exactly one `StormModeEvaluationView` representation for detailed authenticated diagnostics.

## Derived Invariants

- UC-15 must not redefine or mutate shared upstream entities from UC-01 through UC-14 inside `data-model.md`; it only adds storm-mode-specific records and read models.
- Storm mode may affect only the service category, optional geography, and time window carried by the validated trigger and activation records.
- A rejected trigger, unavailable weather input, or absent trigger must never produce an `active` storm-mode activation.
- If storm-mode forecast adjustment fails for a scope, alert sensitivity for that same scope must revert to baseline in the persisted UC-15 outcome records.
- Notification delivery truth remains owned by the shared notification records from UC-10 or UC-11; UC-15 may only link to and summarize those outcomes.
- Effective uncertainty and alert-sensitivity summaries must be persisted explicitly enough to verify that storm-mode behavior differed from baseline when the feature claimed a storm adjustment.
