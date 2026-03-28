# Flow Coverage Analysis Report

Below is a report of flow case analysis for each use case.

## Use Case 1

Overall, the implementation covers all flows from the use case.

1. Acceptance Scenario 1 (Scheduled ingestion stores and activates a new dataset) -> backend/tests/integration/test_ingestion_success.py
2. Acceptance Scenario 2 (Current-dataset marker references the newly activated dataset) -> backend/tests/integration/test_ingestion_success.py
3. Acceptance Scenario 3 (Authentication failure leaves current dataset unchanged) -> backend/tests/integration/test_ingestion_source_failures.py
4. Acceptance Scenario 4 (Source timeout or unavailability leaves current dataset unchanged and records failure) -> backend/tests/integration/test_ingestion_source_failures.py
5. Acceptance Scenario 5 (Validation failure leaves current dataset unchanged) -> backend/tests/integration/test_ingestion_processing_failures.py
6. Acceptance Scenario 6 (Storage failure leaves current dataset unchanged and records failure) -> backend/tests/integration/test_ingestion_processing_failures.py
7. Acceptance Scenario 7 (No new records is a successful no-change run) -> backend/tests/integration/test_ingestion_no_new_records.py
8. Acceptance Scenario 8 (No partial activation) -> backend/tests/integration/test_no_partial_activation.py
9. Acceptance Scenario 9 (Run status, current dataset, and failure notification query surfaces) -> backend/tests/contract/test_ingestion_api.py

## Use Case 2

Overall, the implementation covers all flows from the use case.

1. Acceptance Scenario 1 (Valid dataset is validated, deduplicated, stored, and approved) -> backend/tests/integration/test_validation_approval_flow.py
2. Acceptance Scenario 2 (Resolvable duplicates consolidate into one cleaned record per duplicate set) -> backend/tests/integration/test_validation_approval_flow.py
3. Acceptance Scenario 3 (Invalid dataset is rejected and not made available downstream) -> backend/tests/integration/test_schema_rejection_flow.py
4. Acceptance Scenario 4 (Rejected dataset preserves previously approved active dataset) -> backend/tests/integration/test_schema_rejection_flow.py
5. Acceptance Scenario 5 (Processing or storage failure blocks approval and preserves previous approved dataset) -> backend/tests/integration/test_validation_pipeline_failure_branch.py, backend/tests/integration/test_failed_outcome_safety.py
6. Acceptance Scenario 6 (Excessive duplicate percentage produces review-needed and preserves current approved dataset) -> backend/tests/integration/test_review_needed_flow.py
7. Acceptance Scenario 7 (Operational status surfaces distinguish approved and blocked states) -> backend/tests/integration/test_operational_status_visibility.py, backend/tests/contract/test_validation_run_status.py, backend/tests/contract/test_review_needed_status.py, backend/tests/contract/test_approved_dataset_status.py, backend/tests/contract/test_validation_status_errors.py

## Use Case 3

Overall, the implementation covers all flows from the use case.

1. Acceptance Scenario 1 (Generate a new 24-hour forecast when none current exists) -> backend/tests/integration/test_forecast_generation.py
2. Acceptance Scenario 2 (Include geographic breakdown when usable geographic data exists) -> backend/tests/integration/test_forecast_generation.py
3. Acceptance Scenario 3 (Stored successful forecast becomes current) -> backend/tests/integration/test_forecast_generation.py
4. Acceptance Scenario 4 (Accept request as a generation attempt when no current forecast covers the window) -> backend/tests/integration/test_forecast_generation.py, backend/tests/contract/test_forecast_api.py
5. Acceptance Scenario 5 (Reuse already current forecast) -> backend/tests/integration/test_forecast_reuse.py
6. Acceptance Scenario 6 (Record that current forecast was reused) -> backend/tests/integration/test_forecast_reuse.py
7. Acceptance Scenario 7 (Missing required input data fails and preserves current valid forecast) -> backend/tests/integration/test_forecast_failures.py
8. Acceptance Scenario 8 (Incomplete geography still publishes category-only forecast) -> backend/tests/integration/test_forecast_failures.py
9. Acceptance Scenario 9 (Access denial on trigger/read surfaces) -> backend/tests/contract/test_forecast_api.py

## Use Case 4

Overall, the implementation covers all flows from the use case.

1. Acceptance Scenario 1 (Generate forecast for 7 days) -> backend/tests/integration/test_weekly_forecast_generation.py
2. Acceptance Scenario 2 (Forecast event triggers) -> backend/tests/integration/test_weekly_forecast_generation.py
3. Acceptance Scenario 3 (Reuse current forecast) -> backend/tests/integration/test_weekly_forecast_reuse.py
4. Acceptance Scenario 4 (Required data is missing) -> backend/tests/integration/test_weekly_forecast_failures.py
5. Acceptance Scenario 5 (Execution error) -> backend/tests/integration/test_weekly_forecast_failures.py
6. Acceptance Scenario 6 (Cannot save forecast) -> backend/tests/integration/test_weekly_forecast_failures.py
7. Acceptance Scenario 7 (Deduplicate same-week in-progress runs) -> backend/tests/integration/test_weekly_forecast_reuse.py
8. Acceptance Scenario 8 (Weekly trigger/read contracts and role checks) -> backend/tests/contract/test_weekly_forecast_api.py

## Use Case 5

Overall, the implementation covers all flows from the use case.

1. Acceptance Scenario 1 (Show forecast, uncertainty, and historical demand together) -> backend/tests/integration/test_forecast_visualization_success.py, backend/tests/contract/test_forecast_visualization_api.py, frontend/src/features/forecast-visualization/__tests__/ForecastVisualizationPage.test.tsx, frontend/src/features/forecast-visualization/__tests__/ForecastVisualizationChart.test.tsx
2. Acceptance Scenario 2 (Align historical and forecast periods on a shared axis) -> backend/tests/contract/test_forecast_visualization_api.py, frontend/src/features/forecast-visualization/__tests__/ForecastVisualizationChart.test.tsx
3. Acceptance Scenario 3 (Record successful visualization outcome) -> backend/tests/integration/test_forecast_visualization_success.py
4. Acceptance Scenario 4 (Show forecast product, category filter, status, pipeline info, and last-updated timestamp) -> backend/tests/contract/test_forecast_visualization_api.py, frontend/src/features/forecast-visualization/__tests__/ForecastVisualizationPage.test.tsx
5. Acceptance Scenario 5 (History missing but forecast available) -> backend/tests/integration/test_forecast_visualization_success.py
6. Acceptance Scenario 6 (Uncertainty missing but forecast/history still shown) -> No clear acceptance/integration test found
7. Acceptance Scenario 7 (Record omitted optional element and do not misrepresent it as zero/complete) -> backend/tests/integration/test_forecast_visualization_success.py
8. Acceptance Scenario 8 (Use fallback snapshot when current forecast unavailable) -> backend/tests/integration/test_forecast_visualization_fallback.py, frontend/src/features/forecast-visualization/__tests__/ForecastVisualizationPage.test.tsx
9. Acceptance Scenario 9 (Explicit unavailable state when no fallback exists) -> backend/tests/integration/test_forecast_visualization_fallback.py, frontend/src/features/forecast-visualization/__tests__/ForecastVisualizationPage.test.tsx
10. Acceptance Scenario 10 (Protected visualization routes reject unauthenticated/unauthorized requests) -> backend/tests/contract/test_forecast_visualization_api.py

## Use Case 6

Overall, the implementation covers all flows from the use case.

1. Acceptance Scenario 1 (Run evaluation and store comparison results) -> backend/tests/integration/test_evaluation_success.py, backend/tests/contract/test_evaluation_api.py
2. Acceptance Scenario 2 (Scheduled evaluation completes and results are available) -> backend/tests/integration/test_evaluation_success.py
3. Acceptance Scenario 3 (Successful evaluation presents metrics for engine and baseline methods) -> backend/tests/contract/test_evaluation_api.py, backend/tests/integration/test_evaluation_success.py
4. Acceptance Scenario 4 (Latest successful evaluation includes comparison summary for the product) -> backend/tests/contract/test_evaluation_api.py
5. Acceptance Scenario 5 (Aggregate and store comparison results by service category) -> backend/tests/integration/test_evaluation_partial.py, backend/tests/contract/test_evaluation_api.py
6. Acceptance Scenario 6 (Provide results across time periods) -> backend/tests/contract/test_evaluation_api.py
7. Acceptance Scenario 7 (Exclude invalid metric for one segment and mark partial evaluation) -> backend/tests/integration/test_evaluation_partial.py, backend/tests/contract/test_evaluation_api.py
8. Acceptance Scenario 8 (Required historical data or forecast outputs unavailable preserves previous valid evaluation) -> backend/tests/integration/test_evaluation_failures.py, backend/tests/contract/test_evaluation_api.py
9. Acceptance Scenario 9 (Baseline method failure does not publish new official evaluation) -> backend/tests/integration/test_evaluation_failures.py
10. Acceptance Scenario 10 (Storage failure preserves previous official evaluation) -> backend/tests/integration/test_evaluation_failures.py