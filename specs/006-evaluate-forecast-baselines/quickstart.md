# Quickstart: Evaluate Forecasting Engine Against Baselines

## Purpose

Use this guide to implement and verify UC-06 as a backend evaluation workflow that reuses approved dataset lineage from UC-02 and current forecast products from UC-03 and UC-04, while adding only the persistence and contracts needed to compare forecasting-engine performance against baseline methods.

## Implementation Outline

1. Reuse upstream lineage and forecast entities:
   - `IngestionRun`
   - `DatasetVersion`
   - `ValidationRun`
   - `CleanedDatasetVersion`
   - `CurrentDatasetMarker`
   - `ForecastRun`
   - `ForecastVersion`
   - `ForecastBucket`
   - `CurrentForecastMarker`
   - `WeeklyForecastRun`
   - `WeeklyForecastVersion`
   - `WeeklyForecastBucket`
   - `CurrentWeeklyForecastMarker`
2. Add only the UC-06 evaluation-specific persistence:
   - `EvaluationRun`
   - `EvaluationResult`
   - `EvaluationSegment`
   - `MetricComparisonValue`
   - `CurrentEvaluationMarker`
3. Build one backend evaluation orchestration path that:
   - resolves the approved cleaned dataset for actual outcomes
   - resolves exactly one current forecast product per run
   - generates configured baseline outputs for the same comparison window
   - computes `MAE`, `RMSE`, and `MAPE` for the forecasting engine and each included baseline
   - keeps daily and weekly products in separate runs and stored results
4. Preserve fair-comparison rules:
   - actuals, engine outputs, and baseline outputs must cover the same window and segment scope
   - mismatched windows or slices fail the run instead of producing misleading results
   - partial metric failures store only the valid remaining metrics and mark exclusions explicitly
5. Keep route handlers thin:
   - `POST` evaluation trigger
   - `GET` evaluation run status
   - `GET` current official evaluation by forecast product
   - all comparison logic in services or pipelines
   - all persistence in repositories
6. Promote official results safely:
   - update the current evaluation marker only after full result storage succeeds
   - preserve the prior official evaluation on missing-data, missing-forecast, baseline-failure, and storage-failure paths
   - never let failed runs or raw partial artifacts replace the last known good result

## Verification Steps

Run the UC-06 verification slice from the repository root:

```bash
backend/.venv/bin/python -m pytest   backend/tests/unit/test_evaluation_service.py   backend/tests/contract/test_evaluation_api.py   backend/tests/integration/test_evaluation_success.py   backend/tests/integration/test_evaluation_partial.py   backend/tests/integration/test_evaluation_failures.py
```

Map the verification output directly to `docs/UC-06-AT.md`:

- `AT-01`: `test_evaluation_trigger_and_current_daily_flow`, `test_on_demand_evaluation_stores_daily_result`
- `AT-02`: `test_scheduled_evaluation_runs_for_both_products`
- `AT-03`: `test_evaluation_service_fails_when_cleaned_dataset_missing`, `test_previous_result_is_retained_across_all_failure_paths` missing-input branch
- `AT-04`: `test_failure_outcome_selection_for_missing_forecast_baseline_and_storage` missing-forecast branch, `test_missing_forecast_output_fails_without_current_replacement`
- `AT-05`: `test_baseline_failure_is_recorded`, `test_failure_outcome_selection_for_missing_forecast_baseline_and_storage` baseline branch
- `AT-06`: `test_segmented_current_evaluation_and_partial_payload_structure`, `test_partial_evaluation_marks_excluded_metrics`, `test_category_and_time_period_aggregation_and_exclusion_labels`
- `AT-07`: `test_storage_failure_preserves_previous_current_marker`, `test_failure_outcome_selection_for_missing_forecast_baseline_and_storage` storage branch
- `AT-08`: `test_segmented_current_evaluation_and_partial_payload_structure`, `test_partial_evaluation_marks_excluded_metrics`

## Acceptance Alignment

Map implementation and tests directly to `docs/UC-06-AT.md`:

- `AT-01`: On-demand evaluation completes and stores engine-vs-baseline results
- `AT-02`: Scheduled evaluation completes and stores results
- `AT-03`: Missing required data fails evaluation and preserves previous official result
- `AT-04`: Missing forecast output fails evaluation and preserves previous official result
- `AT-05`: Baseline failure fails evaluation and preserves previous official result
- `AT-06`: Metric computation failure stores partial results with exclusions noted
- `AT-07`: Storage failure prevents official replacement and preserves previous result
- `AT-08`: Fair-comparison metadata proves the same window and slice were used across engine, baselines, and actuals

## Suggested Test Layers

- Unit tests for comparison-window alignment, baseline generation orchestration, metric calculation, exclusion handling, and official-result promotion logic
- Integration tests across approved-dataset lookup, current forecast lookup, evaluation result storage, current-marker updates, historical-result retrieval, and last-known-good preservation
- Contract tests for `specs/006-evaluate-forecast-baselines/contracts/evaluation-api.yaml`
- Acceptance-style tests mirroring `docs/UC-06-AT.md`

## Exit Conditions

Implementation is ready for task breakdown when:

- UC-06 reads actuals from the approved cleaned dataset lineage and forecast outputs from UC-03 or UC-04 without redefining upstream entities
- Daily and weekly forecast products are evaluated in separate runs and stored results
- Stored evaluation results include overall, category, and time-period summaries with per-method metric values
- Partial metric failures are retained as explicit exclusions rather than hidden or treated as full success
- The current evaluation marker changes only after a new result is fully stored
- Planner-facing contracts expose normalized comparison summaries and fair-comparison metadata without raw source rows
