# Data Model: Compare Demand and Forecasts Across Categories and Geographies

## Overview

UC-08 extends the lineage defined by UC-01 through UC-04 without redefining those upstream entities. The comparison workflow consumes approved historical demand from UC-02 and active forecast demand from UC-03 or UC-04, aligns both on one allowable common comparison granularity, and records comparison-specific requests, results, missing-combination annotations, and terminal outcomes needed for warnings, partial-result states, and explicit failures.

## Reused Entities From Previous Specs

### Entity: IngestionRun

**Purpose**: Represents the UC-01 ingestion attempt that originally retrieved the Edmonton 311 source data.

**Reuse in UC-08**

- Preserves end-to-end traceability back to the canonical Edmonton 311 source.
- Remains upstream-only and is not duplicated by comparison persistence.

### Entity: DatasetVersion (Ingested)

**Purpose**: Represents the ingested dataset version created by UC-01 before validation and cleaning.

**Reuse in UC-08**

- Provides source lineage behind the approved cleaned dataset used for historical comparison input.
- Remains distinct from comparison-specific records.

### Entity: ValidationRun

**Purpose**: Represents the UC-02 validation and deduplication decision tied to an approved cleaned dataset.

**Reuse in UC-08**

- Preserves traceability for the approved historical data shown in comparisons.
- Is referenced indirectly through the approved cleaned dataset lineage and never duplicated in UC-08.

### Entity: CleanedDatasetVersion

**Purpose**: Represents the approved cleaned operational dataset produced by UC-02.

**Reuse in UC-08**

- Serves as the canonical historical source for comparison requests.
- Remains the shared historical-data lineage for planner comparisons.

### Entity: CurrentDatasetMarker / Approved Dataset Marker

**Purpose**: Points to the cleaned dataset version currently approved for downstream use.

**Reuse in UC-08**

- Provides the authoritative input pointer for historical comparison retrieval.
- Must remain separate from comparison request and outcome records.

### Entity: ForecastRun

**Purpose**: Represents the UC-03 attempt that produced or served the active daily forecast product.

**Reuse in UC-08**

- Preserves lineage for any daily forecast values included in a comparison.
- Remains a read-only upstream entity for this feature.

### Entity: ForecastVersion

**Purpose**: Represents one stored next-24-hour forecast produced by UC-03.

**Reuse in UC-08**

- Serves as a forecast source when the requested comparison range is satisfied by the active daily forecast product.
- Remains the source of truth for daily forecast bucket values and metadata.

### Entity: ForecastBucket

**Purpose**: Represents one hourly forecast output slice within a UC-03 stored forecast version.

**Reuse in UC-08**

- Supplies comparison-ready daily forecast points when the selected comparison uses the daily forecast product.
- Remains upstream and is not duplicated in comparison storage.

### Entity: CurrentForecastMarker

**Purpose**: Points to the active UC-03 daily forecast product.

**Reuse in UC-08**

- Provides the authoritative pointer for the current daily comparison source.
- Remains distinct from comparison persistence and result records.

### Entity: WeeklyForecastRun

**Purpose**: Represents the UC-04 attempt that produced or served the active weekly forecast product.

**Reuse in UC-08**

- Preserves lineage for any weekly forecast values included in a comparison.
- Remains a read-only upstream entity for this feature.

### Entity: WeeklyForecastVersion

**Purpose**: Represents one stored weekly forecast dataset produced by UC-04.

**Reuse in UC-08**

- Serves as a forecast source when the requested comparison range is satisfied by the active weekly forecast product.
- Remains the source of truth for weekly forecast bucket values and metadata.

### Entity: WeeklyForecastBucket

**Purpose**: Represents one daily forecast output slice within a UC-04 stored forecast version.

**Reuse in UC-08**

- Supplies comparison-ready weekly forecast points when the selected comparison uses the weekly forecast product.
- Remains upstream and is not duplicated in comparison storage.

### Entity: CurrentWeeklyForecastMarker

**Purpose**: Points to the active UC-04 weekly forecast product.

**Reuse in UC-08**

- Provides the authoritative pointer for the current weekly comparison source.
- Remains distinct from comparison persistence and result records.

## New Entity: DemandComparisonRequest

**Purpose**: Records one planner-initiated demand comparison request so selected filters, warning status, chosen forecast source, and terminal outcome remain queryable.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `comparison_request_id` | Identifier | Yes | Unique per executed comparison request |
| `requested_by_actor` | Enum | Yes | `city_planner` only for UC-08 scope |
| `source_cleaned_dataset_version_id` | Identifier | No | Approved historical dataset resolved for the request when available |
| `source_forecast_version_id` | Identifier | No | Present only when the comparison resolves to the active `daily_1_day` forecast product |
| `source_weekly_forecast_version_id` | Identifier | No | Present only when the comparison resolves to the active `weekly_7_day` forecast product |
| `forecast_product_name` | Enum | No | `daily_1_day` or `weekly_7_day` when a forecast source is resolved |
| `forecast_granularity` | Enum | No | `hourly` or `daily`, derived from the resolved forecast source |
| `service_category_filters` | Collection | Yes | One or more canonical service categories selected for the request |
| `geography_level` | String | No | Defined geography level used for the comparison |
| `geography_filters` | Collection | Yes | One or more selected geography values; may be empty for non-geographic scope |
| `time_range_start` | Timestamp | Yes | Inclusive start of the requested comparison range |
| `time_range_end` | Timestamp | Yes | Inclusive end of the requested comparison range |
| `warning_status` | Enum | Yes | `not_needed`, `shown`, or `acknowledged` |
| `status` | Enum | Yes | `running`, `success`, `historical_only`, `forecast_only`, `partial_forecast_missing`, `historical_retrieval_failed`, `forecast_retrieval_failed`, `alignment_failed`, or `render_failed` |
| `started_at` | Timestamp | Yes | Set when comparison processing begins |
| `completed_at` | Timestamp | No | Present after a terminal outcome |
| `render_reported_at` | Timestamp | No | Present only after the client reports final render outcome |
| `failure_reason` | String | No | Required for `historical_retrieval_failed`, `forecast_retrieval_failed`, `alignment_failed`, and `render_failed` |

**Validation rules**

- `time_range_end` must not be earlier than `time_range_start`.
- At most one of `source_forecast_version_id` or `source_weekly_forecast_version_id` may be populated for a resolved forecast source.
- `forecast_product_name = daily_1_day` requires `source_forecast_version_id`.
- `forecast_product_name = weekly_7_day` requires `source_weekly_forecast_version_id`.
- `forecast_product_name = daily_1_day` requires `forecast_granularity = hourly` and the selected range to be fully covered by the resolved UC-03 forecast horizon.
- `forecast_product_name = weekly_7_day` requires `forecast_granularity = daily`, the selected range to be fully covered by the resolved UC-04 forecast horizon, and `daily_1_day` to be unavailable for the same selected range.
- `warning_status = acknowledged` is valid only when a warning was shown before retrieval.
- `completed_at` is required for every terminal status other than `running`.
- `render_reported_at` is required only when the client has reported a final render outcome.
- `failure_reason` is required for `historical_retrieval_failed`, `forecast_retrieval_failed`, `alignment_failed`, and `render_failed`.
- `status = partial_forecast_missing` is valid only for the clarified mixed-availability extension path.

**State transitions**

`running` → `success`  
`running` → `historical_only`  
`running` → `forecast_only`  
`running` → `partial_forecast_missing`  
`running` → `historical_retrieval_failed`  
`running` → `forecast_retrieval_failed`  
`running` → `alignment_failed`  
`running` → `render_failed`

No other transitions are valid.

## New Entity: DemandComparisonResult

**Purpose**: Represents the normalized assembled comparison output prepared for one successful or partial-result request.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `comparison_result_id` | Identifier | Yes | Unique per stored comparison result |
| `comparison_request_id` | Identifier | Yes | References the request that produced it |
| `source_cleaned_dataset_version_id` | Identifier | No | Present when historical demand contributed to the result |
| `source_forecast_version_id` | Identifier | No | Present when `daily_1_day` forecast data contributed to the result |
| `source_weekly_forecast_version_id` | Identifier | No | Present when `weekly_7_day` forecast data contributed to the result |
| `forecast_product_name` | Enum | No | `daily_1_day` or `weekly_7_day` when forecast data contributed to the result |
| `forecast_granularity` | Enum | No | `hourly` or `daily` when forecast data contributed to the result |
| `result_mode` | Enum | Yes | `chart`, `table`, or `chart_and_table` |
| `comparison_granularity` | Enum | Yes | `hourly`, `daily`, or `weekly`, depending on the normalized comparison basis |
| `status` | Enum | Yes | `success`, `historical_only`, `forecast_only`, or `partial_forecast_missing` |
| `stored_at` | Timestamp | Yes | Set when the assembled result is persisted |

**Validation rules**

- `DemandComparisonResult` exists only for `success`, `historical_only`, `forecast_only`, and `partial_forecast_missing` outcomes.
- `source_cleaned_dataset_version_id` is required unless the result is `forecast_only`.
- At least one forecast source identifier is required unless the result is `historical_only`.
- `forecast_product_name` and `forecast_granularity` are required whenever forecast data contributed to the result.
- `forecast_product_name = daily_1_day` requires `forecast_granularity = hourly`, `source_forecast_version_id`, and no `source_weekly_forecast_version_id`.
- `forecast_product_name = weekly_7_day` requires `forecast_granularity = daily`, `source_weekly_forecast_version_id`, and no `source_forecast_version_id`.
- `comparison_granularity = hourly` is valid only when `forecast_product_name = daily_1_day` and the selected range is fully covered by the active daily forecast horizon.
- `comparison_granularity = daily` is valid only when historical and forecast data can both align to calendar-day buckets across the selected range.
- `comparison_granularity = weekly` is valid only when `forecast_product_name = weekly_7_day` and both historical and forecast data can align to calendar-week buckets across the selected range.
- When both active forecast products could satisfy the selected range, `forecast_product_name` must resolve to `daily_1_day`.
- `result_mode` must remain presentation-oriented and must not encode frontend-specific implementation details.

## New Entity: DemandComparisonSeriesPoint

**Purpose**: Represents one normalized historical or forecast point within a comparison result.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `comparison_point_id` | Identifier | Yes | Unique per comparison point |
| `comparison_result_id` | Identifier | Yes | References the owning `DemandComparisonResult` |
| `series_type` | Enum | Yes | `historical` or `forecast` |
| `bucket_start` | Timestamp | Yes | Start of the represented comparison bucket |
| `bucket_end` | Timestamp | Yes | End of the represented comparison bucket |
| `service_category` | String | Yes | Canonical category represented by the point |
| `geography_key` | String | No | Defined geography value represented by the point |
| `value` | Decimal | Yes | Non-negative demand value for the bucket |

**Validation rules**

- `bucket_end` must not be earlier than `bucket_start`.
- `value` must be zero or greater.
- `series_type = historical` points must originate from approved cleaned historical demand.
- `series_type = forecast` points must originate from an active stored forecast source.

## New Entity: ComparisonMissingCombination

**Purpose**: Records selected category or geography combinations that lack forecast data when the clarified mixed-availability extension is exercised.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `missing_combination_id` | Identifier | Yes | Unique per missing combination record |
| `comparison_result_id` | Identifier | Yes | References the owning `DemandComparisonResult` |
| `service_category` | String | Yes | Selected category missing forecast data |
| `geography_key` | String | No | Selected geography value missing forecast data |
| `missing_source` | Enum | Yes | `forecast` only for current clarified-extension scope |
| `message` | String | Yes | Planner-visible explanation of the missing combination |

**Validation rules**

- `ComparisonMissingCombination` records exist only when `DemandComparisonResult.status = partial_forecast_missing`.
- `missing_source` remains `forecast` only for UC-08 scope.
- The recorded category and geography combination must have been included in the original request filters.

## New Entity: DemandComparisonOutcomeRecord

**Purpose**: Stores the monitorable terminal outcome of a comparison request, including warnings, partial-result states, and failures.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `comparison_outcome_id` | Identifier | Yes | Unique per recorded terminal outcome |
| `comparison_request_id` | Identifier | Yes | References the comparison request |
| `outcome_type` | Enum | Yes | `success`, `historical_only`, `forecast_only`, `partial_forecast_missing`, `historical_retrieval_failed`, `forecast_retrieval_failed`, `alignment_failed`, `render_failed`, or `high_volume_warning` |
| `warning_acknowledged` | Boolean | Yes | `true` only when a high-volume request proceeded after warning |
| `recorded_at` | Timestamp | Yes | Set when the outcome is recorded |
| `message` | String | Yes | Human-readable operational summary without raw source rows |

**Validation rules**

- `outcome_type = high_volume_warning` may be recorded only when the request triggered a warning.
- `warning_acknowledged = true` requires that a high-volume warning was shown and the request proceeded.
- Exactly one terminal outcome record exists per completed request, excluding any non-terminal warning record.
- Outcome records must expose only operationally necessary summary details and never raw source payloads.

## Relationships

- One approved `CleanedDatasetVersion` may support zero or more `DemandComparisonRequest` records.
- One `ForecastVersion` may support zero or more daily-forecast `DemandComparisonRequest` and `DemandComparisonResult` records.
- One `WeeklyForecastVersion` may support zero or more weekly-forecast `DemandComparisonRequest` and `DemandComparisonResult` records.
- One `DemandComparisonRequest` may produce zero or one `DemandComparisonResult`.
- One `DemandComparisonResult` belongs to exactly one `DemandComparisonRequest`.
- One `DemandComparisonResult` has one or more `DemandComparisonSeriesPoint` records.
- One `DemandComparisonResult` may have zero or more `ComparisonMissingCombination` records.
- One completed `DemandComparisonRequest` has exactly one `DemandComparisonOutcomeRecord`, excluding any intermediate warning-only record.

## Derived Invariants

- UC-08 always reads from approved historical lineage and active forecast lineage and never mutates upstream dataset or forecast markers.
- `historical_retrieval_failed` and `forecast_retrieval_failed` are distinct from missing matching data and must not be stored as `historical_only` or `forecast_only`.
- Alignment failure never produces a `DemandComparisonResult`.
- `render_failed` may be recorded only after a comparison-execution response has already been returned and a client render event reports failure.
- `daily_1_day` and `weekly_7_day` are mutually exclusive resolved forecast products for any one comparison request, with `daily_1_day` taking precedence when both could satisfy the selected range.
- The clarified mixed-availability behavior applies only when some selected combinations are missing forecast data; it must remain explicitly marked as an extension beyond the written UC-08 alternative flows.
- Comparison responses shown to planners must always trace back to one executed `DemandComparisonRequest` and its terminal `DemandComparisonOutcomeRecord`.
