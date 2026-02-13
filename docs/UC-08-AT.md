# UC-08 Acceptance Test Suite: Compare Demand and Forecasts Across Categories and Geographies

**Use Case**: UC-08 Compare Demand and Forecasts Across Categories and Geographies  
**Scope**: Operations Analytics System  
**Goal**: Verify a City Planner can compare **historical demand** and **forecast demand** across selected **service categories**, **geographies** (e.g., wards), and **time ranges**; and that the system correctly retrieves, aligns, aggregates, visualizes, and logs outcomes while handling missing data, alignment, and rendering failures.

---

## Assumptions / Test Harness Requirements
- A test environment with seeded data across:
  - multiple **service categories** (e.g., Sanitation, Roads, Forestry)
  - multiple **geographies** (e.g., Ward 1, Ward 2, District A)
  - multiple time ranges (days/weeks/months; at least one multi-year window)
- Historical demand dataset availability is controllable:
  - normal retrieval
  - no matching records (for selected filters)
  - retrieval failure (timeout / unavailable / 5xx)
- Forecast data availability is controllable (or Forecasting Engine can be stubbed):
  - normal retrieval
  - missing forecast dataset for selected filters
  - retrieval failure / engine error
- Alignment/aggregation pipeline is controllable:
  - supports forced alignment failure (e.g., mismatched intervals or geo definitions)
- Visualization module is controllable:
  - supports normal render
  - supports forced rendering failure (chart library/client exception)
- Observability:
  - logs accessible for assertions (with correlation id / request id where possible)
  - UI states observable (loading, warning, partial, error)
  - effective query parameters are inspectable (logs, debug panel, or captured requests)
- A configured threshold or detector exists for “high-volume comparative request”.

---

## AT-01 — Comparative analysis interface loads and shows filters
**Covers**: Main Success Scenario Steps 1–2  
**Preconditions**
- Comparative analysis interface is reachable.
- Visualization services are operational.

**Steps**
1. City Planner opens the comparative analysis interface.
2. Observe the filter controls displayed.

**Expected Results**
- Interface loads successfully.
- Filter controls are present for:
  - **service categories** (multi-select if supported)
  - **geographic regions** (multi-select if supported)
  - **time range**
- Default selections (if any) are clearly shown.

---

## AT-02 — Retrieve and visualize side-by-side/overlaid comparison with both historical and forecast data
**Covers**: Main Success Scenario Steps 3–9  
**Preconditions**
- Seeded data includes matching **historical** and **forecast** records for:
  - Categories = {`Category_A`, `Category_B`}
  - Geographies = {`Geo_1`, `Geo_2`}
  - Time period = `T1`–`T2`

**Steps**
1. Select `Category_A` and `Category_B`, select `Geo_1` and `Geo_2`, and set time period `T1`–`T2`.
2. Apply/submit filters.
3. Observe loading/progress state until results appear.
4. Inspect the visualization output (charts/tables) for comparison layout.

**Expected Results**
- System retrieves historical demand data matching the selections.
- System retrieves forecast demand data matching the selections.
- System aligns historical and forecast data on comparable dimensions (time buckets, geo boundaries, category definitions).
- System aggregates and prepares data for comparison.
- Visualization renders **side-by-side** or **overlaid** comparisons across selected categories and geographies.
- Results are consistent with seeded data (spot-check a few known points).

---

## AT-03 — Successful comparative retrieval and visualization is logged
**Covers**: Main Success Scenario Step 10; Success End Condition  
**Preconditions**
- Same as AT-02 (both historical and forecast data exist for selected filters).

**Steps**
1. Perform a successful comparison query (as in AT-02).
2. Retrieve logs/events associated with the request.

**Expected Results**
- Logs include:
  - request initiated (selected categories, geographies, time range; or correlation id)
  - historical retrieval success
  - forecast retrieval success
  - alignment success
  - aggregation/prep success (if separately logged)
  - visualization render success
- No failure logs are recorded for the same request id/correlation.

---

## AT-04 — High-volume comparative request triggers warning and proceeds on acknowledgment
**Covers**: Extension 3a (3a1–3a4)  
**Preconditions**
- Choose or configure filters known to exceed the high-volume threshold
  (e.g., 5 categories × all districts × multi-year horizon).
- High-volume detection is enabled.

**Steps**
1. Select a high-volume combination (e.g., multiple categories, many geographies, long time range).
2. Apply filters.
3. Observe warning message.
4. Acknowledge warning and proceed.
5. Observe continued processing and final outcome.

**Expected Results**
- System detects high-volume request and displays a **warning** about significant load time/unresponsiveness risk.
- After acknowledgment, system proceeds to retrieve historical and forecast data.
- UI shows a persistent loading/progress indicator during processing.
- If retrieval and processing completes, comparative visuals are displayed; otherwise, an error state is shown and logged (see AT-08/AT-09/AT-10).

---

## AT-05 — No historical data available shows forecast-only with clear messaging and logging
**Covers**: Extension 4a (4a1–4a2)  
**Preconditions**
- Forecast data exists for the chosen filters.
- Historical dataset returns **no matches** for the chosen filters.

**Steps**
1. Select filters that yield no historical results but do yield forecast results.
2. Apply filters.
3. Observe visualization and messages.
4. Inspect logs.

**Expected Results**
- System logs missing historical data condition.
- UI displays **forecast data only** with a clear message that historical data is unavailable for the selection.
- UI avoids presenting misleading “comparisons” implying historical data exists.

---

## AT-06 — Forecast data unavailable shows historical-only with clear messaging and logging
**Covers**: Extension 5a (5a1–5a2)  
**Preconditions**
- Historical data exists for the chosen filters.
- Forecast dataset is unavailable (or returns no results) for the chosen filters.

**Steps**
1. Select filters that yield historical results but no forecast results.
2. Apply filters.
3. Observe visualization and messages.
4. Inspect logs.

**Expected Results**
- System logs missing forecast data condition.
- UI displays **historical data only** with a clear message that forecast data is unavailable for the selection.
- UI avoids presenting misleading “comparisons” implying forecast data exists.

---

## AT-07 — Filter integrity: comparisons reflect selected categories and geographies only
**Covers**: Correctness invariant across Main Success Scenario Steps 3–9  
**Preconditions**
- Seeded dataset contains different demand patterns across:
  - Category_A vs Category_B
  - Geo_1 vs Geo_2
- Ability to inspect effective request parameters (logs/debug/capture).

**Steps**
1. Run Query A: categories {Category_A}, geographies {Geo_1}, time `T1`–`T2`.
2. Run Query B: change only geography to {Geo_2} (same category/time).
3. Run Query C: change only category to {Category_B} (same geo/time).
4. Run Query D: change only time range (e.g., `T3`–`T4`) for same category/geo.
5. Compare outputs and inspect effective parameters in logs/captured requests.

**Expected Results**
- Each query’s visualized results match the selected filters.
- Results differ between A/B/C/D in ways consistent with seeded differences.
- System does not include values outside the selected time range, category set, or geography set.
- Logged/effective parameters match UI-selected filters.

---

## AT-08 — Data alignment issue prevents comparison and shows error state
**Covers**: Extension 6a (6a1–6a2); Failed End Condition  
**Preconditions**
- Historical and forecast retrieval both succeed for a chosen filter set.
- Alignment step is forced to fail (e.g., mismatched time intervals or geo definitions).

**Steps**
1. Select filters that return both historical and forecast data.
2. Apply filters and allow retrieval to complete.
3. Trigger an alignment failure during Step 6.
4. Observe UI and logs.

**Expected Results**
- System logs an alignment error.
- UI displays a clear **error state** (not a partial/misleading comparison).
- No comparative visualization is shown.

---

## AT-09 — Visualization rendering error shows error state and logs failure
**Covers**: Extension 8a (8a1–8a2); Failed End Condition  
**Preconditions**
- Retrieval, alignment, and aggregation succeed for a chosen filter set.
- Visualization module is forced to fail rendering.

**Steps**
1. Select filters that return both historical and forecast data.
2. Apply filters and allow processing to complete.
3. Trigger a rendering failure in the visualization module.
4. Observe UI and logs.

**Expected Results**
- System logs a rendering failure.
- UI displays an **error state** indicating visualization could not be rendered.
- No corrupted or partial charts/tables are displayed.

---

## AT-10 — Retrieval failure for either dataset shows error state and logs failure
**Covers**: Failed End Condition (retrieval cannot be completed)  
**Preconditions**
- Configure system so one of the retrieval steps fails:
  - historical retrieval failure (Step 4), OR
  - forecast retrieval failure (Step 5) as an error (not “missing forecast” case).

**Steps**
1. Apply any valid filter set.
2. Inject a retrieval failure during historical retrieval or forecast retrieval.
3. Observe UI and logs.

**Expected Results**
- UI displays an **error state** indicating comparative data could not be retrieved.
- Logs capture:
  - which retrieval failed (historical vs forecast)
  - error category (timeout/unavailable/5xx)
  - timestamp and correlation id (if available)
- UI does not show misleading comparisons.

---

## Traceability Matrix
| Acceptance Test | UC-08 Flow Covered |
|---|---|
| AT-01 | Main Success Scenario (1–2) |
| AT-02 | Main Success Scenario (3–9) |
| AT-03 | Main Success Scenario (10); Success End Condition |
| AT-04 | Extension 3a |
| AT-05 | Extension 4a |
| AT-06 | Extension 5a |
| AT-07 | Cross-cutting correctness invariant (filters → results) |
| AT-08 | Extension 6a; Failed End Condition |
| AT-09 | Extension 8a; Failed End Condition |
| AT-10 | Failed End Condition (retrieval failure) |