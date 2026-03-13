# Data Model: Evaluate Forecasting Engine Against Baselines

## Overview

UC-06 extends the operational lineage defined by UC-01 through UC-04. The evaluation workflow consumes the approved cleaned dataset lineage from UC-02 and the current persisted forecast products from UC-03 and UC-04, compares them against configured baseline methods, and stores a reviewable official evaluation result per forecast product. The model below intentionally reuses the earlier entities instead of duplicating forecast or dataset lifecycle state.

## Reused Entities From Previous Specs

### Entity: IngestionRun

**Purpose**: Represents the UC-01 ingestion attempt that originally retrieved the Edmonton 311 source data.

**Reuse in UC-06**

- Preserves traceability back to the original canonical source for any actuals used in evaluation.
- Remains upstream lineage only and is never duplicated in UC-06 tables.

### Entity: DatasetVersion (Ingested)

**Purpose**: Represents the ingested dataset version created by UC-01 before validation and cleaning.

**Reuse in UC-06**

- Provides source lineage behind the approved cleaned dataset used as evaluation actuals.
- Remains distinct from any evaluation artifact.

### Entity: ValidationRun

**Purpose**: Represents the UC-02 validation and deduplication decision tied to an approved cleaned dataset.

**Reuse in UC-06**

- Preserves the approval lineage for actual outcomes entering evaluation.
- Allows evaluation results to be traced back to the validation decision that approved the input data.

### Entity: CleanedDatasetVersion

**Purpose**: Represents the approved cleaned operational dataset produced by UC-02.

**Reuse in UC-06**

- Serves as the canonical source of actual outcomes used in evaluation windows.
- Remains the shared actuals lineage for both daily and weekly evaluation products.

### Entity: CurrentDatasetMarker / Approved Dataset Marker

**Purpose**: Points to the cleaned dataset version currently approved for downstream use.

**Reuse in UC-06**

- Provides the authoritative actuals input pointer for evaluation.
- Must remain separate from any evaluation marker.

### Entity: ForecastRun

**Purpose**: Represents the UC-03 accepted attempt to obtain a current 1-day forecast.

**Reuse in UC-06**

- Preserves run lineage for the daily forecast product being evaluated.
- Provides the source run context behind daily evaluation results.

### Entity: ForecastVersion

**Purpose**: Represents one stored next-24-hour forecast produced by UC-03.

**Reuse in UC-06**

- Serves as the source of daily forecast outputs and stored quantiles used in daily-product evaluations.
- Remains the source of truth for daily forecast persistence and activation.

### Entity: ForecastBucket

**Purpose**: Represents one hourly forecast output slice within a UC-03 stored forecast version.

**Reuse in UC-06**

- Supplies the daily forecast values that are evaluated against actual outcomes and baseline outputs.
- Remains the source of truth for per-bucket daily forecast values.

### Entity: CurrentForecastMarker

**Purpose**: Points to the active UC-03 daily forecast product.

**Reuse in UC-06**

- Provides the authoritative pointer for the current daily forecast product selected for evaluation.
- Remains distinct from current evaluation markers.

### Entity: WeeklyForecastRun

**Purpose**: Represents the UC-04 accepted attempt to obtain a current weekly forecast.

**Reuse in UC-06**

- Preserves run lineage for the weekly forecast product being evaluated.
- Provides the source run context behind weekly evaluation results.

### Entity: WeeklyForecastVersion

**Purpose**: Represents one stored weekly forecast dataset produced by UC-04.

**Reuse in UC-06**

- Serves as the source of weekly forecast outputs used in weekly-product evaluations.
- Remains the source of truth for weekly forecast retention and activation.

### Entity: WeeklyForecastBucket

**Purpose**: Represents one daily forecast output slice within a UC-04 stored forecast version.

**Reuse in UC-06**

- Supplies the weekly forecast values that are evaluated against actual outcomes and baseline outputs.
- Remains the source of truth for per-bucket weekly forecast values.

### Entity: CurrentWeeklyForecastMarker

**Purpose**: Points to the active UC-04 weekly forecast product.

**Reuse in UC-06**

- Provides the authoritative pointer for the current weekly forecast product selected for evaluation.
- Remains distinct from current evaluation markers.

## New Entity: EvaluationRun

**Purpose**: Represents one accepted scheduled or on-demand attempt to evaluate a single forecast product against configured baseline methods.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `evaluation_run_id` | Identifier | Yes | Unique per accepted run |
| `trigger_type` | Enum | Yes | `scheduled` or `on_demand` |
| `forecast_product_name` | Enum | Yes | `daily_1_day` or `weekly_7_day` |
| `source_cleaned_dataset_version_id` | Identifier | No | Present when actuals lineage is resolved |
| `source_forecast_version_id` | Identifier | No | Present only for daily-product evaluations |
| `source_weekly_forecast_version_id` | Identifier | No | Present only for weekly-product evaluations |
| `evaluation_window_start` | Timestamp | Yes | Inclusive start of the comparison window |
| `evaluation_window_end` | Timestamp | Yes | Inclusive end of the comparison window |
| `started_at` | Timestamp | Yes | Set when evaluation orchestration begins |
| `completed_at` | Timestamp | No | Present after terminal outcome |
| `status` | Enum | Yes | `running`, `success`, `failed` |
| `result_type` | Enum | No | `stored_complete`, `stored_partial`, `missing_input_data`, `missing_forecast_output`, `baseline_failure`, `storage_failure` |
| `evaluation_result_id` | Identifier | No | Present when a stored evaluation result is created |
| `failure_reason` | String | No | Required when `status = failed` |

**Validation rules**

- Exactly one of `source_forecast_version_id` or `source_weekly_forecast_version_id` may be populated.
- `completed_at` is required when `status = success` or `status = failed`.
- `result_type = stored_complete` or `stored_partial` requires `status = success` and `evaluation_result_id`.
- Failure `result_type` values require `status = failed`.
- `evaluation_window_end` must not be earlier than `evaluation_window_start`.
- One run evaluates one forecast product only.

**State transitions**

`running` → `success`  
`running` → `failed`

No other transitions are valid.

## New Entity: EvaluationResult

**Purpose**: Represents one stored, reviewable evaluation outcome for a single forecast product and comparison window.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `evaluation_result_id` | Identifier | Yes | Unique per stored evaluation result |
| `evaluation_run_id` | Identifier | Yes | References the run that created it |
| `forecast_product_name` | Enum | Yes | `daily_1_day` or `weekly_7_day` |
| `source_cleaned_dataset_version_id` | Identifier | Yes | References the actuals lineage used for evaluation |
| `source_forecast_version_id` | Identifier | No | Present only for daily-product evaluations |
| `source_weekly_forecast_version_id` | Identifier | No | Present only for weekly-product evaluations |
| `evaluation_window_start` | Timestamp | Yes | Inclusive start of the evaluated window |
| `evaluation_window_end` | Timestamp | Yes | Inclusive end of the evaluated window |
| `comparison_status` | Enum | Yes | `complete` or `partial` |
| `baseline_methods_included` | Collection | Yes | Canonical ordered list of baseline methods included in the result |
| `metric_set` | Collection | Yes | Canonical ordered list of metric names included in the result |
| `storage_status` | Enum | Yes | `pending`, `stored`, `failed` |
| `is_current` | Boolean | Yes | `true` for at most one result per forecast product |
| `stored_at` | Timestamp | No | Present when storage succeeds |
| `activated_at` | Timestamp | No | Present only when `is_current = true` |

**Validation rules**

- Exactly one of `source_forecast_version_id` or `source_weekly_forecast_version_id` may be populated.
- `comparison_status = partial` requires at least one related segment or metric exclusion.
- `is_current = true` requires `storage_status = stored`.
- `activated_at` is valid only when `is_current = true`.
- No `EvaluationResult` exists for failed runs.

**State transitions**

`pending/not current` → `stored/not current`  
`stored/not current` → `stored/current`  
`pending/not current` → `failed/not current`

## New Entity: EvaluationSegment

**Purpose**: Represents one aggregated slice of an evaluation result, such as overall, one service category, or one time period.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `evaluation_segment_id` | Identifier | Yes | Unique per segment |
| `evaluation_result_id` | Identifier | Yes | References the owning `EvaluationResult` |
| `segment_type` | Enum | Yes | `overall`, `service_category`, or `time_period` |
| `segment_key` | String | Yes | Stable label for the aggregated slice |
| `segment_status` | Enum | Yes | `complete` or `partial` |
| `comparison_row_count` | Integer | Yes | Number of aligned comparison rows included in the segment |
| `excluded_metric_count` | Integer | Yes | Zero or greater |
| `notes` | String | No | Summary of partial coverage or exclusions when applicable |

**Validation rules**

- Each `EvaluationResult` must have exactly one `overall` segment.
- `segment_status = partial` requires `excluded_metric_count > 0` or explanatory `notes`.
- `comparison_row_count` must be greater than zero for stored segments.

## New Entity: MetricComparisonValue

**Purpose**: Stores one metric value for one compared method within one evaluation segment.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `metric_comparison_value_id` | Identifier | Yes | Unique per metric record |
| `evaluation_segment_id` | Identifier | Yes | References the owning `EvaluationSegment` |
| `compared_method` | Enum | Yes | `forecast_engine`, `seasonal_naive`, `moving_average`, or `other_baseline` |
| `compared_method_label` | String | Yes | Human-readable label for the compared method |
| `metric_name` | Enum | Yes | `mae`, `rmse`, or `mape` |
| `metric_value` | Decimal | No | Present when the metric is valid for this segment and method |
| `is_excluded` | Boolean | Yes | Indicates whether this metric was excluded |
| `exclusion_reason` | String | No | Required when `is_excluded = true` |

**Validation rules**

- `metric_value` is required when `is_excluded = false`.
- `exclusion_reason` is required when `is_excluded = true`.
- Each segment should contain one record per included method and metric name, even when the value is excluded.
- `compared_method = other_baseline` requires `compared_method_label` to contain the stable explicit published name of that additional baseline method.

## New Entity: CurrentEvaluationMarker

**Purpose**: Provides a stable pointer to the evaluation result currently considered official for one forecast product.

| Field | Type | Required | Rules |
|--------|-------------|----------|-------|
| `forecast_product_name` | Enum | Yes | Unique per evaluation product: `daily_1_day` or `weekly_7_day` |
| `evaluation_result_id` | Identifier | Yes | References the active `EvaluationResult` |
| `source_cleaned_dataset_version_id` | Identifier | Yes | Actuals lineage used by the active result |
| `source_forecast_version_id` | Identifier | No | Present only for active daily evaluations |
| `source_weekly_forecast_version_id` | Identifier | No | Present only for active weekly evaluations |
| `evaluation_window_start` | Timestamp | Yes | Start of the official result window |
| `evaluation_window_end` | Timestamp | Yes | End of the official result window |
| `comparison_status` | Enum | Yes | `complete` or `partial` |
| `updated_at` | Timestamp | Yes | Updated only on successful activation |
| `updated_by_run_id` | Identifier | Yes | `EvaluationRun` that activated the current result |

**Validation rules**

- Exactly one of `source_forecast_version_id` or `source_weekly_forecast_version_id` may be populated.
- Exactly one marker exists per forecast product.
- Marker updates occur only after the referenced result has been stored successfully.
- Marker must never reference a result with `storage_status != stored`.

## Relationships

- One approved `CleanedDatasetVersion` may be used by zero or more `EvaluationRun` records.
- One `EvaluationRun` may create zero or one stored `EvaluationResult`.
- One `EvaluationResult` belongs to exactly one `EvaluationRun`.
- One `EvaluationResult` has one or more `EvaluationSegment` records.
- One `EvaluationSegment` has one or more `MetricComparisonValue` records.
- One `CurrentEvaluationMarker` points to exactly one active `EvaluationResult` for one forecast product.
- One active `EvaluationResult` traces to exactly one approved `CleanedDatasetVersion` and exactly one daily or weekly forecast version lineage.

## Derived Invariants

- Daily and weekly forecast products always have separate evaluation-run history, separate evaluation results, and separate current-evaluation markers.
- Failed `EvaluationRun` records never change `CurrentEvaluationMarker`.
- Partial metric failures may still produce a stored `EvaluationResult`, but excluded metrics must be explicitly marked.
- Stored evaluation results remain queryable for historical review even after a newer official result is activated.
- Every official evaluation result can be traced back to one approved `CleanedDatasetVersion`, one `ValidationRun`, one ingested `DatasetVersion`, one `IngestionRun`, and one daily or weekly forecast lineage.
- Forecast markers from UC-03 and UC-04 remain operationally separate from current evaluation markers in UC-06.
- Evaluation results are comparable only when the referenced forecast outputs, baseline outputs, and actual outcomes all share the same evaluation window and segment definitions.
