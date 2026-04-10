# Data Model: Alert Threshold Configuration

## Overview
The simplified alert configuration uses mutable row-based persistence for thresholds.

## Entities

### ThresholdConfiguration
**Purpose**: Defines a limit for a specific service category that triggers a dashboard alert when exceeded.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `threshold_configuration_id` | UUID | Yes | Primary Key |
| `service_category` | String | Yes | E.g., "Potholes" |
| `forecast_window_type` | Enum | Yes | "hourly" or "daily" |
| `threshold_value` | Float | Yes | Must be > 0 |
| `notification_channels_json` | JSON | Yes | Defaults to `["dashboard"]` |
| `geography_type` | String | No | Currently `None` (reserved for future) |
| `geography_value` | String | No | Currently `None` (reserved for future) |
| `operational_manager_id` | String | Yes | ID of the manager who created/edited |
| `status` | String | Yes | `active` or `inactive` |
| `effective_from` | Timestamp | Yes | Start of validity |
| `effective_to` | Timestamp | No | End of validity (set on deactivation) |

### ThresholdEvaluationRun
**Purpose**: Records a background process that evaluated forecasts against all active thresholds.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `threshold_evaluation_run_id` | UUID | Yes | Primary Key |
| `forecast_version_reference` | String | Yes | Link to the forecast being evaluated |
| `status` | String | Yes | `pending`, `completed`, `failed` |
| `started_at` | Timestamp | Yes | |
| `completed_at` | Timestamp | No | |

### NotificationEvent
**Purpose**: Records a successfully triggered threshold alert.

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `notification_event_id` | UUID | Yes | Primary Key |
| `threshold_configuration_id` | UUID | Yes | Link to the triggering rule |
| `service_category` | String | Yes | |
| `forecast_value` | Float | Yes | The value that exceeded the threshold |
| `threshold_value` | Float | Yes | |
| `overall_delivery_status` | String | Yes | `delivered`, `failed` |
| `created_at` | Timestamp | Yes | |
