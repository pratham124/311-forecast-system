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

## Use Case 9

Overall, the implementation covers most flows from the use case, with one remaining frontend polish coverage gap.

1. Acceptance Scenario 1 (Forecast explorer loads with weather-overlay controls available) -> frontend/src/features/weather-overlay/__tests__/WeatherOverlayControls.test.tsx, frontend/src/features/weather-overlay/__tests__/WeatherOverlaySync.test.tsx
2. Acceptance Scenario 2 (Enable overlay and retrieve weather data for selected geography/time range) -> backend/tests/contract/test_weather_overlay_get_contract.py, backend/tests/integration/test_weather_overlay_flows.py
3. Acceptance Scenario 3 (Weather observations are aligned to approved geography/time-bucket rules) -> backend/tests/unit/test_weather_overlay_service.py, backend/tests/integration/test_weather_overlay_flows.py
4. Acceptance Scenario 4 (Overlay remains optional and base forecast explorer is preserved) -> backend/tests/contract/test_weather_overlay_get_contract.py, backend/tests/integration/test_weather_overlay_flows.py, frontend/src/features/weather-overlay/__tests__/WeatherOverlayStatus.test.tsx
5. Acceptance Scenario 5 (Successful render outcome is accepted and logged via render-events API) -> backend/tests/contract/test_weather_overlay_render_event_contract.py, backend/tests/integration/test_weather_overlay_flows.py
6. Acceptance Scenario 6 (Missing weather data returns explicit non-visible `unavailable` state while preserving base view) -> backend/tests/integration/test_weather_overlay_flows.py, frontend/src/features/weather-overlay/__tests__/WeatherOverlayStatus.test.tsx
7. Acceptance Scenario 7 (Provider retrieval failure returns `retrieval-failed` without breaking base explorer) -> backend/tests/integration/test_weather_overlay_flows.py
8. Acceptance Scenario 8 (Unsupported geography/alignment failure returns `misaligned` and suppresses overlay) -> backend/tests/integration/test_weather_overlay_flows.py, backend/tests/unit/test_weather_overlay_service.py, frontend/src/features/weather-overlay/__tests__/WeatherOverlayStatus.test.tsx
9. Acceptance Scenario 9 (Client render failure is recorded and transitions to `failed-to-render`) -> backend/tests/contract/test_weather_overlay_render_event_contract.py, backend/tests/integration/test_weather_overlay_flows.py
10. Acceptance Scenario 10 (Disable and supersede behavior prevents stale overlays and blocks invalid render-event submissions) -> backend/tests/integration/test_weather_overlay_flows.py, frontend/src/features/weather-overlay/__tests__/WeatherOverlaySync.test.tsx, frontend/src/api/__tests__/weatherOverlayApi.test.ts
11. Supported-selection latency target validation (5-second path for supported selections) -> backend/tests/integration/test_weather_overlay_latency.py
12. Remaining gap (weather-layer readability and explicit frontend render-failure fallback component behavior) -> No clear dedicated frontend component test found; tracked by `T043` in `specs/009-add-weather-overlay/tasks.md`

## Use Case 15

Overall, the implementation covers all flows from the use case:

1. Acceptance Scenario 1 (Forecast behavior is weather-aware) -> backend/tests/unit/test_forecast_pipeline.py, backend/tests/integration/test_forecast_generation.py, backend/tests/unit/test_open_meteo_client.py
2. Acceptance Scenario 2 (UC-15 storm mode) -> backend/tests/contract/test_surge_alert_api.py, backend/tests/integration/test_surge_alert_flows.py
3. Acceptance Scenario 3 (Storm-mode-aware alert behavior) -> backend/tests/integration/test_surge_alert_flows.py
4. Acceptance Scenario 4 (Demand-risk evaluation) -> backend/tests/contract/test_surge_alert_api.py, backend/tests/integration/test_surge_alert_flows.py
5. Acceptance Scenario 5 (Operational records preserved) -> backend/tests/contract/test_surge_alert_api.py, backend/tests/integration/test_surge_alert_flows.py
6. Acceptance Scenario 6 (Weather context unavailable) -> backend/tests/integration/test_forecast_failures.py, backend/tests/unit/test_open_meteo_client.py
7. Acceptance Scenario 7 (Storm mode inactive) -> backend/tests/integration/test_surge_alert_flows.py
8. Acceptance Scenario 8 (Notification failure) -> backend/tests/unit/test_notification_delivery_service.py

## Use Case 17

Overall, the implementation covers all flows from the use case.

1. Acceptance Scenario 1 (Public forecast portal loads) -> frontend/tests/public-forecast-success.test.tsx
2. Acceptance Scenario 2 (System retrieves approved forecast demand data by service category) -> backend/tests/contract/test_public_forecast_api.py, backend/tests/integration/test_public_forecast_success.py
3. Acceptance Scenario 3 (System prepares data for public visualization) -> backend/tests/unit/test_public_forecast_service.py, backend/tests/integration/test_public_forecast_success.py
4. Acceptance Scenario 4 (Charts/summaries render showing expected demand levels by category) -> frontend/tests/public-forecast-success.test.tsx, backend/tests/contract/test_public_forecast_api.py
5. Acceptance Scenario 5 (Successful public display is logged) -> backend/tests/integration/test_public_forecast_success.py, frontend/tests/public-forecast-success.test.tsx
6. Acceptance Scenario 6 (Forecast data unavailable logs missing data and displays error message) -> backend/tests/integration/test_public_forecast_failures.py, backend/tests/contract/test_public_forecast_api.py, frontend/tests/public-forecast-error-states.test.tsx
7. Acceptance Scenario 7 (Public-safety filtering fails, system sanitizes data and displays safe summary) -> backend/tests/integration/test_public_forecast_sanitized.py, backend/tests/unit/test_public_forecast_sanitization.py, backend/tests/contract/test_public_forecast_api.py, frontend/tests/public-forecast-sanitized.test.tsx
8. Acceptance Scenario 8 (Visualization rendering error logs failure and displays error state) -> backend/tests/integration/test_public_forecast_failures.py, backend/tests/contract/test_public_forecast_api.py, frontend/tests/public-forecast-error-states.test.tsx
