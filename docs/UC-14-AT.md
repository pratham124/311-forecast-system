# UC-14 Acceptance Test Suite: View Forecast Accuracy

**Use Case**: UC-14 View Forecast Accuracy and Compare Predictions to Actuals  
**Scope**: Operations Analytics System  
**Goal**: Verify a City Planner can view recent forecast accuracy and compare past predictions to actuals; the system retrieves historical forecasts and actual demand, computes or retrieves evaluation metrics, aligns data, and renders clear visuals; and it handles missing data/metrics and rendering failures with transparent messaging and logging.

---

## Assumptions / Test Harness Requirements
- A test environment with seeded datasets:
  - **historical forecasts** (multiple periods, categories, and geographies where applicable)
  - **actual demand** for the same periods
  - **evaluation metrics** (precomputed) OR a controllable metrics computation path
- A controllable **Data Storage / Retrieval Layer** supporting:
  - successful retrieval of forecasts and actuals
  - “missing forecasts” condition
  - “missing actuals” condition
  - injected retrieval failures (timeout / unavailable / 5xx)
- A controllable **Evaluation Module** supporting:
  - retrieve existing metrics (e.g., MAE/RMSE/MAPE)
  - “missing metrics” condition
  - compute metrics on-demand (optional, if supported)
- A controllable **Alignment/Aggregation** stage supporting:
  - successful alignment of forecast vs actual across time buckets (and category/geography)
  - forced alignment failure (optional, if supported)
- A controllable **Visualization Module** supporting:
  - successful render of comparison charts/tables and accuracy metrics
  - injected rendering failure (chart library/client exception)
- Observability:
  - UI states observable (loading, partial view without metrics, error state)
  - logs accessible for assertions, ideally with correlation id / request id
  - ability to spot-check known values (forecast and actual) against seeded truth

---

## AT-01 — Forecast performance analysis interface loads
**Covers**: Main Success Scenario Step 1  
**Preconditions**
- User is authenticated with access to forecast performance analysis.

**Steps**
1. City Planner opens the forecast performance analysis interface.

**Expected Results**
- Interface loads successfully.
- Controls/filters (if present) are visible (e.g., time range, category, geography).
- No error state is shown.

---

## AT-02 — System retrieves stored historical forecasts
**Covers**: Main Success Scenario Step 2  
**Preconditions**
- Historical forecasts exist for the selected/default scope.

**Steps**
1. Open the performance analysis interface.
2. Trigger retrieval (automatic on load or by applying filters).
3. Inspect logs or captured requests for forecast retrieval.

**Expected Results**
- System retrieves stored historical forecast outputs for the selected scope.
- Logs indicate forecast retrieval success (with scope and correlation id where available).

---

## AT-03 — System retrieves corresponding actual demand data
**Covers**: Main Success Scenario Step 3  
**Preconditions**
- Actual demand exists for the same periods as the stored forecasts.

**Steps**
1. Trigger a performance analysis request for a scope with known forecasts.
2. Inspect logs or captured requests for actuals retrieval.

**Expected Results**
- System retrieves actual demand data corresponding to the forecast periods and scope.
- Logs indicate actual demand retrieval success.

---

## AT-04 — System retrieves or computes accuracy metrics
**Covers**: Main Success Scenario Step 4  
**Preconditions**
- Metrics are precomputed and stored OR the system supports on-demand computation.

**Steps**
1. Trigger a performance analysis request for a scope with known forecasts/actuals.
2. Observe metrics retrieval/computation stage (via UI progress, logs, or events).

**Expected Results**
- System retrieves existing accuracy metrics (e.g., MAE/RMSE/MAPE) or computes them successfully.
- Metrics correspond to the same scope and time windows as the forecasts/actuals.

---

## AT-05 — System aligns forecasts and actuals for comparison
**Covers**: Main Success Scenario Step 5  
**Preconditions**
- Forecast and actual datasets exist and overlap for the selected scope.

**Steps**
1. Trigger performance analysis request.
2. Inspect the comparison output for correct period alignment (e.g., same dates/time buckets).

**Expected Results**
- System aligns forecasts and actuals on a common timeline (and category/geography where applicable).
- No off-by-one time bucket shifts are present.
- Spot-check a known time bucket: forecast and actual correspond to the same interval.

---

## AT-06 — System prepares data for visualization
**Covers**: Main Success Scenario Step 6  
**Preconditions**
- Forecasts, actuals, and metrics are available (or metrics optional per AT-10).

**Steps**
1. Trigger performance analysis request.
2. Observe transition from retrieval/alignment to visualization stage.
3. Inspect logs for “prepared for visualization” (or equivalent).

**Expected Results**
- Data is aggregated/bucketed as required for charts/tables.
- Visualization input payload is consistent with selected scope (time range/category/geography).

---

## AT-07 — System renders prediction-vs-actual comparisons and accuracy metrics
**Covers**: Main Success Scenario Steps 7–8; Success End Condition  
**Preconditions**
- Forecasts, actuals, and metrics are available.
- Visualization services are operational.

**Steps**
1. Trigger performance analysis for a scope with known data.
2. Inspect rendered visuals:
   - prediction vs. actual chart/table
   - metrics view (summary and/or trend)

**Expected Results**
- System renders clear charts/tables comparing forecasts to actuals.
- Accuracy metrics are displayed and interpretable.
- Values are consistent with seeded data (spot-check a small set of points).
- No misleading placeholders or empty charts are shown.

---

## AT-08 — Successful retrieval and visualization are logged
**Covers**: Main Success Scenario Step 9  
**Preconditions**
- A successful render occurs (AT-07).

**Steps**
1. Run a successful performance analysis request.
2. Retrieve logs/events for the request.

**Expected Results**
- Logs include:
  - interface access / request initiated
  - forecast retrieval success
  - actuals retrieval success
  - metrics retrieval/computation success (if applicable)
  - alignment success
  - visualization render success
- Entries are correlated (request id/correlation id) where available.

---

## AT-09 — Historical forecast data unavailable shows error state and logs condition
**Covers**: Extension 2a (2a1–2a2); Failed End Condition  
**Preconditions**
- Configure the data layer to return missing/unavailable historical forecasts for the selected scope.

**Steps**
1. Open performance analysis interface and trigger request for the affected scope.
2. Observe UI and logs.

**Expected Results**
- System logs missing historical forecast data condition.
- UI displays an error state (no comparisons shown).
- System does not attempt to present performance insights based on incomplete forecast history.

---

## AT-10 — Actual demand data unavailable shows error state and logs condition
**Covers**: Extension 3a (3a1–3a2); Failed End Condition  
**Preconditions**
- Historical forecasts exist.
- Configure actual demand retrieval to return missing/unavailable for the same scope.

**Steps**
1. Trigger performance analysis request for the affected scope.
2. Observe UI and logs.

**Expected Results**
- System logs missing actual demand data condition.
- UI displays an error state (no valid comparisons shown).

---

## AT-11 — Metrics missing: system logs condition and displays comparison without metrics when possible
**Covers**: Extension 4a (4a1–4a2)  
**Preconditions**
- Historical forecasts and actuals exist for the selected scope.
- Metrics are missing/not computed for that scope.
- The system supports rendering prediction-vs-actual comparisons without metrics.

**Steps**
1. Trigger performance analysis request for the affected scope.
2. Observe rendered views and any messaging.
3. Inspect logs.

**Expected Results**
- System logs missing metrics condition.
- If possible, UI displays prediction-vs-actual comparisons **without** summary metrics, with a clear message that metrics are unavailable.
- If not possible (implementation-dependent), UI shows an error state (handled by AT-12).

---

## AT-12 — Visualization rendering error shows error state and logs failure
**Covers**: Extension 7a (7a1–7a2); Failed End Condition  
**Preconditions**
- Forecasts and actuals (and optionally metrics) are available.
- Visualization module is forced to fail rendering.

**Steps**
1. Trigger performance analysis request for a valid scope.
2. Inject visualization rendering failure during chart/table render.
3. Observe UI and logs.

**Expected Results**
- System logs rendering failure with error category and correlation id (if available).
- UI displays an error state (no partial/corrupted visuals shown).

---

## Traceability Matrix
| Acceptance Test | UC-14 Flow Covered |
|---|---|
| AT-01 | Main Success Scenario (1) |
| AT-02 | Main Success Scenario (2) |
| AT-03 | Main Success Scenario (3) |
| AT-04 | Main Success Scenario (4) |
| AT-05 | Main Success Scenario (5) |
| AT-06 | Main Success Scenario (6) |
| AT-07 | Main Success Scenario (7–8); Success End Condition |
| AT-08 | Main Success Scenario (9) |
| AT-09 | Extension 2a; Failed End Condition |
| AT-10 | Extension 3a; Failed End Condition |
| AT-11 | Extension 4a |
| AT-12 | Extension 7a; Failed End Condition |
