# Data Model: Generate 7-Day Demand Forecast

## Overview

UC-04 consumes approved operational lineage from UC-01 and UC-02, then either reuses an existing current weekly forecast for the same operational week or persists a newly generated weekly forecast. This model preserves last-known-good activation and makes success/reuse/failure outcomes queryable.

## Reused Lineage Entities

### Entity: IngestionRun

**Purpose**: Records the UC-01 ingestion attempt that produced source operational data.

### Entity: DatasetVersion (Ingested)

**Purpose**: Records a source ingested dataset version produced by UC-01.

### Entity: ValidationRun

**Purpose**: Records UC-02 validation/deduplication decisions used to approve cleaned datasets.

### Entity: CleanedDatasetVersion

**Purpose**: Records cleaned operational data versions approved for downstream use.

### Entity: CurrentDatasetMarker (Approved Dataset Marker)

**Purpose**: Points to the currently approved cleaned dataset used as forecast input lineage.

## Entity: WeeklyForecastRun

**Purpose**: Represents one accepted scheduled or on-demand attempt to obtain a current weekly forecast.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `weekly_forecast_run_id` | Identifier | Yes | Unique per accepted run |
| `trigger_type` | Enum | Yes | `scheduled` or `on_demand` |
| `week_start_local` | Timestamp | Yes | Monday 00:00 local operational timezone |
| `week_end_local` | Timestamp | Yes | Sunday 23:59 local operational timezone |
| `source_cleaned_dataset_version_id` | Identifier | No | Present when input dataset is resolved |
| `started_at` | Timestamp | Yes | Set on orchestration start |
| `completed_at` | Timestamp | No | Set on terminal state |
| `status` | Enum | Yes | `running`, `success`, `failed` |
| `result_type` | Enum | No | `generated_new`, `served_current`, `missing_input_data`, `engine_failure`, `storage_failure` |
| `generated_forecast_version_id` | Identifier | No | Set when new forecast version created |
| `served_forecast_version_id` | Identifier | No | Set when existing current forecast served |
| `geography_scope` | Enum | No | `category_and_geography` or `category_only` on success |
| `failure_reason` | String | No | Required when `status = failed` |

**Validation rules**:
- Run records are created only for accepted generation attempts.
- `week_start_local` and `week_end_local` must correspond to a single operational week boundary.
- `generated_forecast_version_id` and `served_forecast_version_id` cannot both be set.
- `result_type = generated_new` requires `status = success` and `generated_forecast_version_id`.
- `result_type = served_current` requires `status = success` and `served_forecast_version_id`.
- `result_type` in failure set requires `status = failed` and `failure_reason`.

## Entity: WeeklyForecastVersion

**Purpose**: Represents one persisted weekly forecast dataset.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `weekly_forecast_version_id` | Identifier | Yes | Unique per stored version |
| `weekly_forecast_run_id` | Identifier | Yes | References the run that generated it |
| `source_cleaned_dataset_version_id` | Identifier | Yes | References approved cleaned dataset lineage |
| `week_start_local` | Timestamp | Yes | Monday 00:00 local operational timezone |
| `week_end_local` | Timestamp | Yes | Sunday 23:59 local operational timezone |
| `bucket_granularity` | Enum | Yes | `daily` |
| `bucket_count_days` | Integer | Yes | Must equal `7` |
| `geography_scope` | Enum | Yes | `category_and_geography` or `category_only` |
| `storage_status` | Enum | Yes | `pending`, `stored`, `failed` |
| `is_current` | Boolean | Yes | True for at most one version per operational week |
| `stored_at` | Timestamp | No | Present when storage succeeds |
| `activated_at` | Timestamp | No | Present only when current marker updated |

**Validation rules**:
- `bucket_granularity` must be `daily` and `bucket_count_days` must be `7`.
- `is_current = true` only when `storage_status = stored`.
- `geography_scope = category_and_geography` requires at least one bucket with geography populated.
- No version is created for reused-current responses.

## Entity: WeeklyForecastBucket

**Purpose**: Represents one daily demand prediction for a category and optional geography.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `weekly_forecast_bucket_id` | Identifier | Yes | Unique per daily bucket row |
| `weekly_forecast_version_id` | Identifier | Yes | Parent weekly forecast version |
| `forecast_date_local` | Date | Yes | One of the 7 dates in the operational week |
| `service_category` | String | Yes | Canonical service category |
| `geography_key` | String | No | Populated when geography scope is available |
| `point_forecast` | Decimal | Yes | Non-negative demand estimate |

**Validation rules**:
- Each weekly forecast version must include rows that cover all 7 operational-week dates per included category.
- `geography_key` is required only when geography scope includes geography.
- `point_forecast` must be non-negative.

## Entity: CurrentWeeklyForecastMarker

**Purpose**: Provides a stable pointer to the weekly forecast currently active for planning.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `forecast_product_name` | String | Yes | Unique product identifier for UC-04 weekly forecast |
| `weekly_forecast_version_id` | Identifier | Yes | References active weekly forecast version |
| `source_cleaned_dataset_version_id` | Identifier | Yes | Input lineage used by active forecast |
| `week_start_local` | Timestamp | Yes | Monday 00:00 of active week |
| `week_end_local` | Timestamp | Yes | Sunday 23:59 of active week |
| `geography_scope` | Enum | Yes | `category_and_geography` or `category_only` |
| `updated_at` | Timestamp | Yes | Marker update time |
| `updated_by_run_id` | Identifier | Yes | Run that activated this marker |

**Validation rules**:
- Exactly one marker exists for this forecast product.
- Marker updates occur only after referenced version storage succeeds.
- Marker must never reference a version with `storage_status != stored`.

## Relationships

- One approved `CleanedDatasetVersion` may be used by zero or more `WeeklyForecastRun` records.
- One `WeeklyForecastRun` may generate zero or one `WeeklyForecastVersion`.
- One `WeeklyForecastRun` may serve zero or one existing `WeeklyForecastVersion`.
- One `WeeklyForecastVersion` has one or more `WeeklyForecastBucket` records.
- One `CurrentWeeklyForecastMarker` points to exactly one active `WeeklyForecastVersion`.

## State Transitions

### WeeklyForecastRun

`running` -> `success`  
`running` -> `failed`

### WeeklyForecastVersion

`pending/not current` -> `stored/not current`  
`stored/not current` -> `stored/current`  
`pending/not current` -> `failed/not current`

## Derived Invariants

- At most one weekly forecast version is current for a given operational week.
- Reused-current outcomes do not create a new weekly forecast version.
- Failed runs never change `CurrentWeeklyForecastMarker`.
- Missing-data, engine-failure, and storage-failure outcomes preserve prior active forecast marker.
- Geography-incomplete success is valid only when output is explicitly marked `category_only`.
- Weekly forecast lineage remains traceable to `CleanedDatasetVersion` and upstream UC-01/UC-02 entities.
