# Data Model: Visualize Forecast Curves with Uncertainty Bands

## Overview

UC-05 extends the lineage defined by UC-01 through UC-04 without redefining those upstream entities. The visualization workflow consumes approved operational history from UC-02 and current forecast products from UC-03 and UC-04, normalizes them into one dashboard-ready view, and adds only the visualization-specific persistence needed for fallback snapshots and load observability.

## Reused Entities From Previous Specs

### Entity: IngestionRun

**Purpose**: Represents the UC-01 ingestion attempt that originally retrieved the Edmonton 311 source data.

**Reuse in UC-05**

- Preserves end-to-end lineage back to the original canonical Edmonton 311 source.
- Remains upstream-only and is not duplicated by visualization persistence.

### Entity: DatasetVersion (Ingested)

**Purpose**: Represents the UC-01 ingested dataset version before validation and cleaning.

**Reuse in UC-05**

- Provides the source lineage behind the approved cleaned dataset used to assemble historical context.
- Stays distinct from visualization artifacts and forecast outputs.

### Entity: ValidationRun

**Purpose**: Represents the UC-02 validation and deduplication decision tied to an approved cleaned dataset.

**Reuse in UC-05**

- Preserves traceability for the historical demand context used in the dashboard.
- Is referenced indirectly through the approved cleaned dataset lineage and never duplicated in UC-05.

### Entity: CleanedDatasetVersion

**Purpose**: Represents the approved cleaned operational dataset produced by UC-02.

**Reuse in UC-05**

- Serves as the canonical source for the previous 7 days of historical demand shown in the chart.
- Remains the shared historical-data lineage for both daily and weekly forecast visualizations.

### Entity: CurrentDatasetMarker / Approved Dataset Marker

**Purpose**: Points to the cleaned dataset version currently approved for downstream use.

**Reuse in UC-05**

- Provides the authoritative input pointer for historical overlay assembly.
- Must remain separate from all forecast markers and visualization snapshots.

### Entity: ForecastRun

**Purpose**: Represents the UC-03 accepted attempt to obtain a current 1-day forecast.

**Reuse in UC-05**

- Preserves operational lineage for the daily forecast product.
- Provides source run context for any fallback snapshot built from a daily forecast version.

### Entity: ForecastVersion

**Purpose**: Represents one stored next-24-hour forecast produced by UC-03.

**Reuse in UC-05**

- Serves as the source of daily forecast metadata, last-updated state, and stored quantiles for the dashboard.
- Must not be duplicated in UC-05 under a visualization-specific forecast entity.

### Entity: ForecastBucket

**Purpose**: Represents one hourly forecast output slice within a UC-03 stored forecast version.

**Reuse in UC-05**

- Supplies chart-ready daily forecast points and the canonical `P10`, `P50`, and `P90` values when the selected product is the daily forecast.
- Remains the source of truth for daily forecast bucket values.

### Entity: CurrentForecastMarker

**Purpose**: Points to the active UC-03 daily forecast product.

**Reuse in UC-05**

- Provides the authoritative pointer for the current daily visualization source.
- Remains operationally separate from visualization snapshots and outcome records.

### Entity: WeeklyForecastRun

**Purpose**: Represents the UC-04 accepted attempt to obtain a current weekly forecast.

**Reuse in UC-05**

- Preserves operational lineage for the weekly forecast product.
- Provides source run context for any fallback snapshot built from a weekly forecast version.

### Entity: WeeklyForecastVersion

**Purpose**: Represents one stored weekly forecast dataset produced by UC-04.

**Reuse in UC-05**

- Serves as the source of weekly forecast metadata and stored bucket values for the dashboard.
- Remains the source of truth for weekly forecast activation and retention.

### Entity: WeeklyForecastBucket

**Purpose**: Represents one daily forecast output slice within a UC-04 stored forecast version.

**Reuse in UC-05**

- Supplies chart-ready weekly forecast points when the selected product is the weekly forecast.
- UC-05 must normalize weekly bucket data into the same `P10`, `P50`, and `P90` visualization contract when those values are available; otherwise the load must remain valid and be recorded as `uncertainty_missing`.

### Entity: CurrentWeeklyForecastMarker

**Purpose**: Points to the active UC-04 weekly forecast product.

**Reuse in UC-05**

- Provides the authoritative pointer for the current weekly visualization source.
- Remains distinct from daily forecast markers and visualization snapshots.

## New Entity: VisualizationLoadRecord

**Purpose**: Records one dashboard-load attempt for UC-05 so rendering success, degraded states, fallback use, and failure outcomes are queryable without mutating forecast-run history.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `visualization_load_id` | Identifier | Yes | Unique per dashboard load |
| `requested_by_actor` | Enum | Yes | `operational_manager` only for UC-05 scope |
| `forecast_product_name` | Enum | Yes | `daily_1_day` or `weekly_7_day` |
| `forecast_granularity` | Enum | Yes | `hourly` or `daily`, derived from the selected forecast product |
| `service_category_filter` | String | No | Canonical service category when the dashboard is filtered |
| `history_window_start` | Timestamp | Yes | Start of the historical context window |
| `history_window_end` | Timestamp | Yes | End of the historical context window and forecast boundary |
| `forecast_window_start` | Timestamp | No | Start of the displayed forecast horizon when current or fallback forecast data is available |
| `forecast_window_end` | Timestamp | No | End of the displayed forecast horizon when current or fallback forecast data is available |
| `source_cleaned_dataset_version_id` | Identifier | No | Approved cleaned dataset used for historical context when resolved |
| `source_forecast_version_id` | Identifier | No | Source forecast version used when the selected product is daily |
| `source_weekly_forecast_version_id` | Identifier | No | Source forecast version used when the selected product is weekly |
| `fallback_snapshot_id` | Identifier | No | Present only when a fallback visualization snapshot is shown |
| `status` | Enum | Yes | `running`, `success`, `degraded`, `fallback_shown`, `unavailable`, `render_failed` |
| `degradation_type` | Enum | No | `history_missing` or `uncertainty_missing` when `status = degraded` |
| `started_at` | Timestamp | Yes | Set when dashboard data assembly begins |
| `completed_at` | Timestamp | No | Present after the load reaches a terminal status |
| `render_reported_at` | Timestamp | No | Present only after the client reports final render outcome |
| `failure_reason` | String | No | Required for `unavailable` and `render_failed` outcomes |

**Validation rules**

- Exactly one of `source_forecast_version_id` or `source_weekly_forecast_version_id` may be populated for a given load.
- `history_window_end` must equal the forecast boundary for the selected view.
- `status = degraded` requires `degradation_type`.
- `status = fallback_shown` requires `fallback_snapshot_id`.
- `status = unavailable` or `render_failed` requires `failure_reason`.
- `completed_at` is required for all terminal statuses except `running`.
- `render_reported_at` is required only when the final client render outcome has been reported.

**State transitions**

`running` → `success`  
`running` → `degraded`  
`running` → `fallback_shown`  
`running` → `unavailable`  
`running` → `render_failed`

No other transitions are valid.

## New Entity: VisualizationSnapshot

**Purpose**: Stores a last-known-good visualization payload that can be reused as a bounded fallback when current forecast data is unavailable.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `visualization_snapshot_id` | Identifier | Yes | Unique per stored fallback snapshot |
| `forecast_product_name` | Enum | Yes | `daily_1_day` or `weekly_7_day` |
| `forecast_granularity` | Enum | Yes | `hourly` or `daily` |
| `service_category_filter` | String | No | Canonical service category when the snapshot reflects a filtered view |
| `source_cleaned_dataset_version_id` | Identifier | Yes | Approved cleaned dataset used for the snapshot’s historical overlay |
| `source_forecast_version_id` | Identifier | No | Present only for daily forecast snapshots |
| `source_weekly_forecast_version_id` | Identifier | No | Present only for weekly forecast snapshots |
| `source_forecast_run_id` | Identifier | No | Present when the snapshot originates from a daily forecast product |
| `source_weekly_forecast_run_id` | Identifier | No | Present when the snapshot originates from a weekly forecast product |
| `history_window_start` | Timestamp | Yes | Start of the historical context window stored in the snapshot |
| `history_window_end` | Timestamp | Yes | End of the historical context window and forecast boundary |
| `forecast_window_start` | Timestamp | Yes | Start of the stored forecast horizon |
| `forecast_window_end` | Timestamp | Yes | End of the stored forecast horizon |
| `band_standard` | Enum | Yes | `p10_p50_p90` only |
| `snapshot_status` | Enum | Yes | `stored`, `expired` |
| `created_at` | Timestamp | Yes | Set when the snapshot is created from a successful visualization |
| `expires_at` | Timestamp | Yes | Must be no more than 24 hours after `created_at` |
| `created_from_load_id` | Identifier | Yes | References the `VisualizationLoadRecord` that produced the snapshot |

**Validation rules**

- Exactly one of `source_forecast_version_id` or `source_weekly_forecast_version_id` must be populated.
- Exactly one of `source_forecast_run_id` or `source_weekly_forecast_run_id` may be populated to match the referenced forecast product lineage.
- `band_standard` must remain `p10_p50_p90`.
- `expires_at` must be exactly 24 hours after `created_at`.
- `snapshot_status = expired` means the snapshot must not be served as fallback.
- Only successful, non-degraded visualization loads may produce a stored snapshot.

**State transitions**

`stored` → `expired`

No other transitions are valid.

## Derived Read Model: ForecastVisualization

**Purpose**: Represents the normalized backend-to-frontend view model assembled from shared forecast lineage plus visualization-specific metadata.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `visualization_load_id` | Identifier | Yes | Links the rendered payload to its recorded load |
| `forecast_product_name` | Enum | Yes | `daily_1_day` or `weekly_7_day` |
| `forecast_granularity` | Enum | Yes | `hourly` or `daily` |
| `service_category_filter` | String | No | Selected category filter when applied |
| `history_window_start` | Timestamp | Yes | Previous 7-day window start |
| `history_window_end` | Timestamp | Yes | Forecast boundary |
| `forecast_window_start` | Timestamp | No | Start of the displayed forecast horizon |
| `forecast_window_end` | Timestamp | No | End of the displayed forecast horizon |
| `historical_series` | Collection | No | Historical points aggregated from the approved cleaned dataset |
| `forecast_series` | Collection | No | Forecast points normalized from daily or weekly forecast buckets |
| `uncertainty_bands` | Collection | No | `P10`, `P50`, and `P90` points when available |
| `alerts_summary` | Collection | Yes | Status and alert entries required by the forecast-view contract |
| `pipeline_status` | Collection | Yes | Data freshness and pipeline state indicators for the selected view |
| `last_updated_at` | Timestamp | No | Latest forecast or snapshot update timestamp shown to the user |
| `view_status` | Enum | Yes | `success`, `degraded`, `fallback_shown`, `unavailable`, `render_failed` |
| `fallback_metadata` | Object | No | Present only when a fallback snapshot is shown |

**Validation rules**

- `historical_series` and `forecast_series` must use one shared time axis in the assembled payload.
- `uncertainty_bands` may be omitted only when the source forecast product lacks normalized `P10`, `P50`, and `P90`.
- `fallback_metadata` may be populated only when `view_status = fallback_shown`.
- `alerts_summary` and `pipeline_status` must always be present, even when empty, to keep the frontend contract stable.

## Relationships

- One `CleanedDatasetVersion` may support zero or more `VisualizationLoadRecord` rows and zero or more `VisualizationSnapshot` rows.
- One `ForecastVersion` may support zero or more daily-product `VisualizationLoadRecord` rows and zero or more daily-product `VisualizationSnapshot` rows.
- One `WeeklyForecastVersion` may support zero or more weekly-product `VisualizationLoadRecord` rows and zero or more weekly-product `VisualizationSnapshot` rows.
- One `VisualizationLoadRecord` may produce zero or one `VisualizationSnapshot`.
- One `VisualizationSnapshot` belongs to exactly one `VisualizationLoadRecord`.
- One derived `ForecastVisualization` is assembled from exactly one `VisualizationLoadRecord` plus lineage from one cleaned dataset version and one selected forecast product version.

## Derived Invariants

- UC-05 must never redefine or mutate UC-03 or UC-04 forecast lifecycle entities; it only reads from them.
- The approved cleaned dataset marker, current daily forecast marker, current weekly forecast marker, and visualization snapshot lifecycle are separate controls and must not be conflated.
- A fallback visualization can be served only from a `VisualizationSnapshot` whose `snapshot_status = stored` and whose `expires_at` has not passed.
- Historical context for UC-05 always uses the 7 days immediately preceding the forecast boundary.
- Normalized uncertainty labels for UC-05 remain `P10`, `P50`, and `P90` regardless of the underlying forecast product.
- A visualization load outcome must remain queryable even when no current forecast is available or when the client reports a render failure.
