# Data Model: Configure Alert Thresholds and Notification Channels

## Overview

UC-13 extends the shared lineage defined by UC-01 through UC-12 without redefining those upstream entities. The feature adds only the shared-configuration records needed to author, activate, and audit one alert configuration for the whole alerting system while preserving the previously active configuration whenever validation or storage fails.

## Reused Shared Entities and Vocabulary

UC-13 references shared entities and vocabularies from earlier use cases and does not redefine their fields here:

- UC-01 through UC-04: ingestion, validation, and forecast lineage that downstream alerting workflows continue to consume after configuration changes are activated
- UC-10: `ThresholdConfiguration`, `ThresholdState`, `NotificationEvent`, and `NotificationChannelAttempt` semantics for downstream threshold-alert evaluation and delivery behavior
- UC-11: `SurgeDetectionConfiguration`, `SurgeNotificationEvent`, and `SurgeNotificationChannelAttempt` as existing alerting lineage that remains separate from UC-13 authoring persistence
- UC-12: operational observability conventions for explicit success and failure outcomes

UC-13 also reuses these shared modeling concepts without redefining upstream entities:

- Canonical evaluation scope: service category with optional geography
- One shared active marker pattern used elsewhere in the platform to point to the current version
- Structured operational correlation using actor identity, timestamps, and optional correlation id

## Canonical UC-13 Vocabulary

### Configuration Lifecycle Status

- `active`
- `superseded`

### Save Outcome

- `validation_rejected`
- `stored_successfully`
- `storage_failed`

### Scope Type

- `category_only`
- `category_geography`

## New Entity: AlertConfigurationVersion

**Purpose**: Stores one immutable saved snapshot of the shared alert configuration for the whole alerting system.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `alert_configuration_version_id` | Identifier | Yes | Unique per saved configuration version |
| `version_number` | Integer | Yes | Monotonically increasing positive integer |
| `lifecycle_status` | Enum | Yes | `active` or `superseded` |
| `created_by_actor` | Enum | Yes | `operational_manager` for UC-13 scope |
| `created_by_actor_id` | Identifier | Yes | References the authenticated manager who saved the version |
| `created_at` | Timestamp | Yes | Set when the version is persisted |
| `activated_at` | Timestamp | Yes | Set when the version becomes active |
| `superseded_at` | Timestamp | No | Present only after a later version becomes active |
| `version_note` | String | No | Optional human-readable save summary |
| `correlation_id` | String | No | Shared operational identifier when supported |

**Validation rules**

- `version_number` must be unique and greater than zero.
- Exactly one `AlertConfigurationVersion` may have `lifecycle_status = active` at a time.
- `superseded_at` is required when `lifecycle_status = superseded`.
- `superseded_at`, when present, must be later than or equal to `activated_at`.

## New Entity: ActiveAlertConfigurationMarker

**Purpose**: Points to the one shared active alert configuration that future alerts must consume.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `active_alert_configuration_marker_id` | Identifier | Yes | Unique marker row for UC-13 |
| `alert_configuration_version_id` | Identifier | Yes | References the currently active configuration version |
| `updated_at` | Timestamp | Yes | Set when the active marker changes |
| `updated_by_actor_id` | Identifier | Yes | References the actor who activated the current version |

**Validation rules**

- Exactly one marker row may exist for the alerting system.
- `alert_configuration_version_id` must reference an `AlertConfigurationVersion` with `lifecycle_status = active`.
- Updating the marker and promoting a new active version must occur atomically.

## New Entity: AlertConfigurationThresholdRule

**Purpose**: Stores one threshold rule inside a saved alert configuration version for a service category and optional geography scope.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `alert_configuration_threshold_rule_id` | Identifier | Yes | Unique per saved threshold rule |
| `alert_configuration_version_id` | Identifier | Yes | References the owning configuration version |
| `service_category` | String | Yes | Canonical Edmonton 311 category |
| `scope_type` | Enum | Yes | `category_only` or `category_geography` |
| `geography_type` | String | No | Present only when `scope_type = category_geography` |
| `geography_value` | String | No | Required when `geography_type` is present |
| `threshold_value` | Decimal | Yes | Must satisfy the configured threshold validation policy |
| `validation_policy_name` | String | Yes | Name of the threshold policy applied at save time |
| `created_at` | Timestamp | Yes | Set when the rule is persisted with its version |

**Validation rules**

- The combination of `alert_configuration_version_id`, `service_category`, `scope_type`, `geography_type`, and `geography_value` must be unique.
- `geography_type` and `geography_value` must both be absent when `scope_type = category_only`.
- `geography_type` and `geography_value` are both required when `scope_type = category_geography`.
- `threshold_value` must satisfy the configured policy and must not be persisted when validation fails.
- A category-plus-geography rule and a category-only rule for the same `service_category` may coexist in the same version because they represent distinct scopes.

## New Entity: AlertConfigurationChannelSelection

**Purpose**: Stores one supported notification channel selected for a saved alert configuration version.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `alert_configuration_channel_selection_id` | Identifier | Yes | Unique per stored channel selection |
| `alert_configuration_version_id` | Identifier | Yes | References the owning configuration version |
| `channel_type` | Enum | Yes | Supported channel such as `email`, `slack`, or `teams` |
| `channel_status_at_save` | Enum | Yes | `supported` only for persisted selections |
| `created_at` | Timestamp | Yes | Set when the selection is persisted with its version |

**Validation rules**

- The combination of `alert_configuration_version_id` and `channel_type` must be unique.
- At least one `AlertConfigurationChannelSelection` must exist for every saved `AlertConfigurationVersion`.
- `channel_type` must be in the supported-channel capability set at save time.
- Unsupported or unavailable channels must be rejected before any new configuration version is stored.

## New Entity: AlertConfigurationDeliveryPreference

**Purpose**: Stores frequency controls, deduplication controls, or both for one service category and optional geography scope inside a saved configuration version.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `alert_configuration_delivery_preference_id` | Identifier | Yes | Unique per stored scoped preference |
| `alert_configuration_version_id` | Identifier | Yes | References the owning configuration version |
| `service_category` | String | Yes | Canonical Edmonton 311 category |
| `scope_type` | Enum | Yes | `category_only` or `category_geography` |
| `geography_type` | String | No | Present only when `scope_type = category_geography` |
| `geography_value` | String | No | Required when `geography_type` is present |
| `frequency_limit_count` | Integer | No | Positive integer when a frequency control is configured |
| `frequency_limit_window_minutes` | Integer | No | Positive integer when a frequency control is configured |
| `deduplication_window_minutes` | Integer | No | Positive integer when deduplication is configured |
| `deduplication_key_mode` | Enum | No | Canonical grouping mode applied inside the deduplication window |
| `created_at` | Timestamp | Yes | Set when the preference is persisted with its version |

**Validation rules**

- The combination of `alert_configuration_version_id`, `service_category`, `scope_type`, `geography_type`, and `geography_value` must be unique.
- `geography_type` and `geography_value` must both be absent when `scope_type = category_only`.
- `geography_type` and `geography_value` are both required when `scope_type = category_geography`.
- At least one of `frequency_limit_count` plus `frequency_limit_window_minutes`, or `deduplication_window_minutes`, must be present.
- `frequency_limit_count` and `frequency_limit_window_minutes` must either both be present or both be absent.
- `frequency_limit_count`, `frequency_limit_window_minutes`, and `deduplication_window_minutes`, when present, must all be greater than zero.
- `deduplication_key_mode` is required when `deduplication_window_minutes` is present.

## New Entity: AlertConfigurationUpdateAttempt

**Purpose**: Records one authorized attempt to save a new shared alert configuration so validation rejection, successful activation, and storage failure remain traceable.

| Field | Type | Required | Rules |
|--------|------|----------|-------|
| `alert_configuration_update_attempt_id` | Identifier | Yes | Unique per save attempt |
| `attempted_by_actor` | Enum | Yes | `operational_manager` for UC-13 scope |
| `attempted_by_actor_id` | Identifier | Yes | References the authenticated manager who submitted the save |
| `attempted_at` | Timestamp | Yes | Set when save processing begins |
| `completed_at` | Timestamp | No | Set when the attempt reaches a terminal outcome |
| `save_outcome` | Enum | Yes | `validation_rejected`, `stored_successfully`, or `storage_failed` |
| `previous_active_configuration_version_id` | Identifier | Yes | References the version that was active when the attempt started |
| `resulting_active_configuration_version_id` | Identifier | Yes | References the active version after the attempt completes |
| `candidate_version_number` | Integer | No | Present only when a new version number was allocated |
| `validation_error_count` | Integer | Yes | Zero or greater |
| `storage_failure_reason` | String | No | Required when `save_outcome = storage_failed` |
| `validation_error_summary` | String | No | Required when `save_outcome = validation_rejected` |
| `correlation_id` | String | No | Shared operational identifier when supported |

**Validation rules**

- `completed_at` is required for terminal outcomes `validation_rejected`, `stored_successfully`, and `storage_failed`.
- `resulting_active_configuration_version_id` must equal `previous_active_configuration_version_id` when `save_outcome = validation_rejected` or `save_outcome = storage_failed`.
- `resulting_active_configuration_version_id` must differ from `previous_active_configuration_version_id` when `save_outcome = stored_successfully`.
- `validation_error_count` must be greater than zero when `save_outcome = validation_rejected`.
- `validation_error_summary` is required when `save_outcome = validation_rejected`.
- `storage_failure_reason` is required when `save_outcome = storage_failed`.
- `candidate_version_number` must be absent when validation fails before version allocation.

## Relationships

- One `AlertConfigurationVersion` owns many `AlertConfigurationThresholdRule` records.
- One `AlertConfigurationVersion` owns many `AlertConfigurationChannelSelection` records.
- One `AlertConfigurationVersion` owns many `AlertConfigurationDeliveryPreference` records.
- One `ActiveAlertConfigurationMarker` points to exactly one `AlertConfigurationVersion`.
- One `AlertConfigurationVersion` may be referenced by many `AlertConfigurationUpdateAttempt` records as the previous or resulting active version.

## Derived Invariants

- UC-13 must not redefine or mutate shared upstream entities from UC-01 through UC-12 inside `data-model.md`; it only adds shared-configuration entities specific to this use case.
- Exactly one shared alert configuration version is active at a time for the entire alerting system.
- Every saved configuration version must contain at least one selected supported notification channel.
- Validation rejection and storage failure must preserve the previous active configuration version.
- Category-only and category-plus-geography configuration scope must remain distinguishable in both threshold rules and delivery preferences.
- Future alerts consume the configuration version referenced by `ActiveAlertConfigurationMarker`, not unsaved drafts or failed save attempts.
