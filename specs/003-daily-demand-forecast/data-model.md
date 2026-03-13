# Data Model: Generate 1-Day Demand Forecast

## Overview

UC-03 extends the persistent lineage defined by UC-01 and UC-02. The forecasting workflow consumes the approved cleaned dataset version already tracked by the earlier specs, evaluates whether a current forecast can be reused, and either returns that current forecast or stores a new hourly forecast version for the next 24 hours. The model below intentionally reuses the relevant UC-01 and UC-02 entities so the cross-feature lineage remains explicit.

## Reused Entities From Previous Specs

### Entity: IngestionRun

**Purpose**: Represents the UC-01 execution that originally retrieved the Edmonton 311 data used by downstream validation and forecasting.

**Reuse in UC-03**

- Preserves the original ingestion trigger and source-window lineage for forecast inputs.
- Remains the authoritative source for source retrieval context and must not be duplicated in UC-03 tables.

### Entity: DatasetVersion (Ingested)

**Purpose**: Represents the ingested dataset version created by UC-01 before UC-02 validation and cleaning.

**Reuse in UC-03**

- Provides the upstream dataset lineage behind each approved cleaned dataset used for forecasting.
- Remains distinct from forecast artifacts and must not be reused as a forecast record.

### Entity: ValidationRun

**Purpose**: Represents the UC-02 validation and deduplication attempt that decided whether a cleaned dataset could be approved.

**Reuse in UC-03**

- Provides the validation lineage for the cleaned dataset version used in a forecast run.
- Allows operational and acceptance checks to trace forecast inputs back to the validation outcome that approved them.

### Entity: CleanedDatasetVersion

**Purpose**: Represents the cleaned dataset produced and approved in UC-02.

**Reuse in UC-03**

- Serves as the source dataset for each forecast run.
- Preserves cleaned record counts and duplicate-resolution lineage without copying those fields into forecast entities.

### Entity: CurrentDatasetMarker / Approved Dataset Marker

**Purpose**: Identifies the cleaned dataset version currently approved for downstream use.

**Reuse in UC-03**

- Provides the authoritative pointer to the approved cleaned dataset version that a forecast run must consume.
- Remains unchanged by UC-03 except as a read dependency; forecast activation uses a separate current-forecast marker.

## Entity: ForecastRun

**Purpose**: Represents one scheduled or on-demand attempt to obtain a current next-24-hour forecast.

**Fields**

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `forecast_run_id` | Identifier | Yes | Unique per forecast attempt |
| `trigger_type` | Enum | Yes | `scheduled` or `on_demand` |
| `source_cleaned_dataset_version_id` | Identifier | No | References the approved `CleanedDatasetVersion` used for the run when available |
| `weather_enrichment_source` | Enum | No | `msc_geomet` when weather enrichment is used |
| `holiday_enrichment_source` | Enum | No | `nager_date_canada` when holiday enrichment is used |
| `requested_horizon_start` | Timestamp | Yes | Start of the upcoming 24-hour planning window |
| `requested_horizon_end` | Timestamp | Yes | End of the upcoming 24-hour planning window |
| `started_at` | Timestamp | Yes | Set when forecast orchestration begins |
| `completed_at` | Timestamp | No | Present when the run reaches a terminal state |
| `status` | Enum | Yes | `running`, `success`, `failed` |
| `result_type` | Enum | No | `generated_new`, `served_current`, `missing_input_data`, `engine_failure`, `storage_failure` |
| `forecast_version_id` | Identifier | No | Present only when a new stored forecast version is created |
| `served_forecast_version_id` | Identifier | No | Present only when an existing current forecast is reused |
| `geography_scope` | Enum | No | `category_and_geography` or `category_only` after successful completion |
| `failure_reason` | String | No | Short summary for failed runs |

**Validation rules**

- A `ForecastRun` record is created only for accepted scheduled or on-demand generation attempts.
- `completed_at` is required when `status` is `success` or `failed`.
- `result_type = generated_new` is valid only when `status = success` and `forecast_version_id` is present.
- `result_type = served_current` is valid only when `status = success` and `served_forecast_version_id` is present.
- `result_type = missing_input_data`, `engine_failure`, and `storage_failure` are valid only when `status = failed`.
- `requested_horizon_end` must be exactly 24 hours after `requested_horizon_start`.
- `weather_enrichment_source` may be populated only as `msc_geomet`.
- `holiday_enrichment_source` may be populated only as `nager_date_canada`.
- `forecast_version_id` and `served_forecast_version_id` must not both be populated in the same run.
- Unauthorized, forbidden, missing-resource, and invalid-request outcomes must not create or mutate a `ForecastRun`.

**State transitions**

`running` → `success`  
`running` → `failed`

No other transitions are valid.

## Entity: ForecastVersion

**Purpose**: Represents one stored next-24-hour forecast generated from an approved cleaned dataset version.

**Fields**

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `forecast_version_id` | Identifier | Yes | Unique per stored forecast version |
| `forecast_run_id` | Identifier | Yes | References the `ForecastRun` that created it |
| `source_cleaned_dataset_version_id` | Identifier | Yes | References the approved `CleanedDatasetVersion` used for forecast generation |
| `weather_enrichment_source` | Enum | No | `msc_geomet` when weather enrichment contributed to the forecast |
| `holiday_enrichment_source` | Enum | No | `nager_date_canada` when holiday enrichment contributed to the forecast |
| `horizon_start` | Timestamp | Yes | Start of the covered planning window |
| `horizon_end` | Timestamp | Yes | End of the covered planning window |
| `bucket_granularity` | Enum | Yes | `hourly` only |
| `bucket_count` | Integer | Yes | Must equal `24` |
| `geography_scope` | Enum | Yes | `category_and_geography` or `category_only` |
| `model_family` | Enum | Yes | `lightgbm_global` |
| `baseline_method` | String | Yes | Summary label for the retained baseline comparator |
| `storage_status` | Enum | Yes | `pending`, `stored`, `failed` |
| `is_current` | Boolean | Yes | `true` for at most one forecast version covering a horizon |
| `stored_at` | Timestamp | No | Present when storage succeeds |
| `activated_at` | Timestamp | No | Present only when `is_current = true` |

**Validation rules**

- `bucket_granularity` must remain `hourly`.
- `bucket_count` must remain `24`.
- `weather_enrichment_source` may be populated only as `msc_geomet`.
- `holiday_enrichment_source` may be populated only as `nager_date_canada`.
- `storage_status = stored` is required before `is_current = true`.
- `activated_at` is valid only when `is_current = true`.
- `geography_scope = category_and_geography` requires at least one related bucket with geography populated.
- No `ForecastVersion` exists for reused-current responses or failed runs.

**State transitions**

`pending/not current` → `stored/not current`  
`stored/not current` → `stored/current`  
`pending/not current` → `failed/not current`

## Entity: ForecastBucket

**Purpose**: Represents one hourly forecast output slice within a stored forecast version.

**Fields**

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `forecast_bucket_id` | Identifier | Yes | Unique per forecast bucket |
| `forecast_version_id` | Identifier | Yes | References the owning `ForecastVersion` |
| `bucket_start` | Timestamp | Yes | Start timestamp of the hourly bucket |
| `bucket_end` | Timestamp | Yes | End timestamp of the hourly bucket |
| `service_category` | String | Yes | Canonical service category label |
| `geography_key` | String | No | Geography identifier when geographic segmentation is available |
| `point_forecast` | Decimal | Yes | Operational demand value for the bucket |
| `quantile_p10` | Decimal | Yes | Lower predictive quantile for the bucket |
| `quantile_p50` | Decimal | Yes | Median predictive quantile for the bucket |
| `quantile_p90` | Decimal | Yes | Upper predictive quantile for the bucket |
| `baseline_value` | Decimal | Yes | Baseline comparator value for the bucket |

**Validation rules**

- Every `ForecastVersion` must have bucket rows that collectively cover exactly 24 consecutive hourly intervals.
- `bucket_end` must be exactly one hour after `bucket_start`.
- `geography_key` is required only when the owning `ForecastVersion` has `geography_scope = category_and_geography`.
- `quantile_p10 <= quantile_p50 <= quantile_p90` must hold for every bucket.
- `point_forecast` must represent the operationally chosen forecast value for the bucket and must be non-negative.
- `baseline_value` must be non-negative.

## Entity: CurrentForecastMarker

**Purpose**: Provides a stable query point for the forecast version currently active for operational planning.

**Fields**

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `forecast_product_name` | String | Yes | Unique identifier for the 1-day hourly forecast product |
| `forecast_version_id` | Identifier | Yes | References the active `ForecastVersion` |
| `source_cleaned_dataset_version_id` | Identifier | Yes | References the approved cleaned dataset used to create the active forecast |
| `horizon_start` | Timestamp | Yes | Start of the active planning window |
| `horizon_end` | Timestamp | Yes | End of the active planning window |
| `updated_at` | Timestamp | Yes | Updated only on successful activation |
| `updated_by_run_id` | Identifier | Yes | `ForecastRun` that activated the current forecast |
| `geography_scope` | Enum | Yes | `category_and_geography` or `category_only` |

**Validation rules**

- There is exactly one marker for the 1-day hourly forecast product.
- Marker updates occur only after the referenced forecast version has been stored successfully.
- The marker must never point to a forecast version with `storage_status != stored`.
- The marker is operationally distinct from the UC-02 approved cleaned dataset marker and must not be used to identify the active cleaned input dataset.

## Relationships

- One approved `CleanedDatasetVersion` may be used by zero or more `ForecastRun` records.
- One `ForecastRun` may produce zero or one stored `ForecastVersion`.
- One `ForecastRun` may serve zero or one existing stored `ForecastVersion`.
- One `ForecastVersion` belongs to exactly one `ForecastRun`.
- One `ForecastVersion` has one or more `ForecastBucket` rows that together cover the 24-hour planning window.
- One `CurrentForecastMarker` points to exactly one active `ForecastVersion`.
- One active `ForecastVersion` references exactly one approved `CleanedDatasetVersion`, preserving lineage back to the shared approved dataset marker.

## Derived Invariants

- The current approved cleaned dataset marker from UC-02 and the current forecast marker from UC-03 are separate and must never point to the same type of entity.
- At most one `ForecastVersion` is current for the 1-day hourly forecast product at any time.
- The UC-03 product remains a 1-day hourly operational forecast and does not redefine the constitution's broader default 7-day daily forecasting direction.
- Failed `ForecastRun` records never change `CurrentForecastMarker`.
- Unauthorized, forbidden, missing-resource, and invalid-request outcomes never create a `ForecastRun` and never change `CurrentForecastMarker`.
- A `served_current` run creates no new `ForecastVersion` and does not invoke a new activation.
- Every stored `ForecastVersion` can be traced back to one approved `CleanedDatasetVersion`, one `ValidationRun`, one ingested `DatasetVersion`, and one `IngestionRun`.
- Every enrichment source recorded for a run or forecast version must resolve to dedicated `msc_geomet` or `nager_date_canada` ingestion or client modules rather than route, service, or repository-owned external calls.
- A category-only forecast is valid only when every stored bucket omits geography consistently and the run records the reduced geography scope.
- Stored `ForecastVersion` records and failed `ForecastRun` records are retained as operational history for this feature.
