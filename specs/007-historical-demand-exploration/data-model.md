# Data Model: Explore Historical 311 Demand Data

## Overview

UC-07 extends the historical lineage defined by UC-01 and UC-02 without redefining those upstream entities. The historical-demand exploration workflow consumes the approved cleaned dataset lineage from UC-02, applies planner-selected filters for service category, time range, and supported reliable geography levels, and records analysis outcomes needed for warning, no-data, success, and failure observability.

## Reused Entities From Previous Specs

### Entity: IngestionRun

**Purpose**: Represents the UC-01 ingestion attempt that originally retrieved the Edmonton 311 source data.

**Reuse in UC-07**

- Preserves traceability back to the original canonical historical source.
- Remains upstream-only and is not duplicated by analysis persistence.

### Entity: DatasetVersion (Ingested)

**Purpose**: Represents the ingested dataset version created by UC-01 before validation and cleaning.

**Reuse in UC-07**

- Provides source lineage behind the approved cleaned dataset used in historical analysis.
- Remains distinct from planner-analysis artifacts.

### Entity: ValidationRun

**Purpose**: Represents the UC-02 validation and deduplication decision tied to an approved cleaned dataset.

**Reuse in UC-07**

- Preserves traceability for the approved historical data shown to planners.
- Is referenced indirectly through the approved cleaned dataset lineage and never duplicated in UC-07.

### Entity: CleanedDatasetVersion

**Purpose**: Represents the approved cleaned operational dataset produced by UC-02.

**Reuse in UC-07**

- Serves as the canonical source for historical demand analysis.
- Remains the shared historical-data lineage for planner exploration requests.

### Entity: CurrentDatasetMarker / Approved Dataset Marker

**Purpose**: Points to the cleaned dataset version currently approved for downstream use.

**Reuse in UC-07**

- Provides the authoritative input pointer for historical exploration.
- Must remain separate from analysis request and outcome records.

## New Entity: HistoricalDemandAnalysisRequest

**Purpose**: Records one planner-initiated historical-demand analysis request so selected filters, warning state, and terminal outcome remain queryable.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `analysis_request_id` | Identifier | Yes | Unique per executed analysis request |
| `requested_by_actor` | Enum | Yes | `city_planner` only for UC-07 scope |
| `source_cleaned_dataset_version_id` | Identifier | No | Approved cleaned dataset resolved for the request when available |
| `service_category_filter` | String | No | Canonical category when the request is filtered |
| `time_range_start` | Timestamp | Yes | Inclusive start of requested history window |
| `time_range_end` | Timestamp | Yes | Inclusive end of requested history window |
| `geography_filter_type` | Enum | No | Supported reliable geography level selected for the request |
| `geography_filter_value` | String | No | Specific geography key selected at the supported level |
| `warning_status` | Enum | Yes | `not_needed`, `shown`, or `acknowledged` |
| `status` | Enum | Yes | `running`, `success`, `no_data`, `retrieval_failed`, `render_failed` |
| `started_at` | Timestamp | Yes | Set when analysis begins |
| `completed_at` | Timestamp | No | Present after a terminal outcome |
| `failure_reason` | String | No | Required for failed terminal outcomes |

**Validation rules**

- `time_range_end` must not be earlier than `time_range_start`.
- `warning_status = acknowledged` is valid only when a high-volume warning was shown before retrieval.
- `geography_filter_value` may be populated only when `geography_filter_type` is populated.
- `completed_at` is required for terminal statuses other than `running`.
- Only supported reliable geography levels may be stored in `geography_filter_type`.

**State transitions**

`running` → `success`  
`running` → `no_data`  
`running` → `retrieval_failed`  
`running` → `render_failed`

No other transitions are valid.

## New Entity: HistoricalDemandAnalysisResult

**Purpose**: Represents the normalized aggregated historical-demand output prepared for one successful analysis request.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `analysis_result_id` | Identifier | Yes | Unique per stored analysis result |
| `analysis_request_id` | Identifier | Yes | References the request that produced it |
| `source_cleaned_dataset_version_id` | Identifier | Yes | References the approved cleaned dataset used for analysis |
| `aggregation_granularity` | Enum | Yes | `daily`, `weekly`, or `monthly` |
| `result_mode` | Enum | Yes | `chart`, `table`, or `chart_and_table` |
| `service_category_filter` | String | No | Canonical category reflected in the result |
| `time_range_start` | Timestamp | Yes | Inclusive start of represented history window |
| `time_range_end` | Timestamp | Yes | Inclusive end of represented history window |
| `geography_filter_type` | Enum | No | Supported reliable geography level reflected in the result |
| `geography_filter_value` | String | No | Specific geography key reflected in the result |
| `record_count` | Integer | Yes | Number of historical records contributing to the result |
| `stored_at` | Timestamp | Yes | Set when the result is persisted for observability |

**Validation rules**

- `record_count` must be greater than zero for successful results.
- `geography_filter_value` may be populated only when `geography_filter_type` is populated.
- `aggregation_granularity` must match the prepared historical summary granularity selected by the system for the request.
- No `HistoricalDemandAnalysisResult` exists for `no_data`, `retrieval_failed`, or `render_failed` outcomes.

## New Entity: HistoricalDemandSummaryPoint

**Purpose**: Represents one aggregated historical-demand point or row within a successful historical analysis result.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `summary_point_id` | Identifier | Yes | Unique per aggregated point |
| `analysis_result_id` | Identifier | Yes | References the owning `HistoricalDemandAnalysisResult` |
| `bucket_start` | Timestamp | Yes | Start of the represented aggregation bucket |
| `bucket_end` | Timestamp | Yes | End of the represented aggregation bucket |
| `service_category` | String | Yes | Canonical category represented by the point |
| `geography_key` | String | No | Geography value when geography filtering or grouping is applied |
| `demand_count` | Integer | Yes | Non-negative aggregated historical request count |

**Validation rules**

- `bucket_end` must not be earlier than `bucket_start`.
- `demand_count` must be zero or greater.
- `geography_key` may be populated only when the result includes a supported geography level.
- Summary points for one result must align to the result’s declared aggregation granularity.

## New Entity: HistoricalAnalysisOutcomeRecord

**Purpose**: Stores the monitorable terminal outcome of a historical-demand request, including warnings, no-data cases, and failures.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `analysis_outcome_id` | Identifier | Yes | Unique per recorded terminal outcome |
| `analysis_request_id` | Identifier | Yes | References the historical analysis request |
| `outcome_type` | Enum | Yes | `success`, `high_volume_warning`, `no_data`, `retrieval_failed`, or `render_failed` |
| `warning_acknowledged` | Boolean | Yes | `true` only when a high-volume request proceeded after warning |
| `recorded_at` | Timestamp | Yes | Set when the terminal outcome is recorded |
| `message` | String | Yes | Human-readable operational summary without raw source rows |

**Validation rules**

- `outcome_type = high_volume_warning` may be recorded only when the request triggered a warning.
- `warning_acknowledged = true` requires that a high-volume warning was shown and the request proceeded.
- Exactly one terminal outcome record exists per completed request.
- Outcome records must expose only operationally necessary summary details and never raw source payloads.

## Relationships

- One approved `CleanedDatasetVersion` may be used by zero or more `HistoricalDemandAnalysisRequest` records.
- One `HistoricalDemandAnalysisRequest` may produce zero or one `HistoricalDemandAnalysisResult`.
- One `HistoricalDemandAnalysisResult` belongs to exactly one `HistoricalDemandAnalysisRequest`.
- One `HistoricalDemandAnalysisResult` has one or more `HistoricalDemandSummaryPoint` records.
- One completed `HistoricalDemandAnalysisRequest` has exactly one `HistoricalAnalysisOutcomeRecord`.

## Derived Invariants

- Historical analysis always reads from the approved cleaned dataset lineage and never directly from raw ingested data.
- Unsupported or unreliable geography levels must not be offered or stored as valid request filters.
- No-data, retrieval-failure, and render-failure outcomes never create a successful `HistoricalDemandAnalysisResult`.
- Successful historical analysis results remain traceable to one approved `CleanedDatasetVersion`, one `ValidationRun`, one ingested `DatasetVersion`, and one `IngestionRun`.
- Historical exploration outcomes are operationally distinct from forecast and visualization outcomes and must not mutate forecast markers, evaluation markers, or dataset approval state.
