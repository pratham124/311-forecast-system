# UC-07 Acceptance Test Suite: Historical Trend Exploration

**Use Case**: UC-07 Explore Historical 311 Demand Data  
**Scope**: Operations Analytics System  
**Goal**: Verify a City Planner can explore historical 311 demand by category, time range, and geography; the system retrieves, aggregates, and visualizes results reliably; and it handles no-data, high-volume, retrieval, and rendering failures with clear user feedback and logging.

---

## Assumptions / Test Harness Requirements
- A test environment with **historical 311 data** seeded across:
  - multiple categories (e.g., Waste, Roads, Noise)
  - multiple time ranges (days/weeks/months; multi-year)
  - multiple geographic segments (e.g., wards, neighborhoods, districts)
- A controllable **Data Storage / Query Layer** (real or stub) supporting:
  - success with matching records
  - success with no matching records
  - injected retrieval failures (e.g., DB unavailable, query timeout, 5xx)
- A controllable **Visualization Module** (real or stub) supporting:
  - successful render
  - injected rendering failure (e.g., chart library error, client render exception)
- Observability:
  - system logs accessible for assertions
  - UI state observable (loading, warning, no-data, error)
  - query parameters used for retrieval recorded (or otherwise inspectable)
- Performance threshold configuration accessible for the “high data volume” detector (or an equivalent test knob).

---

## AT-01 — Interface loads and displays available filtering options
**Covers**: Main Success Scenario Steps 1–2  
**Preconditions**
- Historical demand analysis interface is reachable.
- Filtering services are operational.

**Steps**
1. City Planner opens the historical demand analysis interface.
2. Observe the filter controls displayed.

**Expected Results**
- The interface loads successfully.
- Filter controls are present for:
  - **service category**
  - **time range**
  - **geography**
- Default selections (if any) are clearly shown.
- Logs include an entry indicating the interface was accessed (optional but preferred).

---

## AT-02 — Filtered retrieval succeeds and displays aggregated historical demand
**Covers**: Main Success Scenario Steps 3–7  
**Preconditions**
- Seeded historical data includes records matching:
  - Category = `Category_A`
  - Time range = `T1` to `T2`
  - Geography = `Geo_1`

**Steps**
1. Select `Category_A`, set time range `T1`–`T2`, and select `Geo_1`.
2. Submit/apply filters.
3. Observe loading state (if shown).
4. When results appear, inspect the chart/table and any summary metrics.

**Expected Results**
- System retrieves data matching the selected filters.
- System aggregates/prepares the data for visualization (e.g., daily/weekly/monthly buckets as configured).
- Charts/tables render and display historical demand patterns for the selected filters.
- Displayed values are consistent with seeded data (spot-check a small set of known points).
- No error state is shown.

---

## AT-03 — Successful retrieval and visualization is logged
**Covers**: Main Success Scenario Step 8; Success End Condition  
**Preconditions**
- Same as AT-02 (matching data exists).

**Steps**
1. Perform a successful filtered query (as in AT-02).
2. Retrieve logs/events associated with the request.

**Expected Results**
- Logs show:
  - request initiated (filters and timestamp or request id)
  - retrieval success
  - aggregation/prep success (if separately logged)
  - visualization render success
- No failure logs are recorded for the request id/timestamp.

---

## AT-04 — High data volume request triggers warning and proceeds on acknowledgment
**Covers**: Extension 3a (3a1–3a4)  
**Preconditions**
- Configure or choose filters known to exceed the performance threshold (e.g., **city-wide** + **multi-year**).
- The system’s high-volume detection is enabled.

**Steps**
1. Select a high-volume combination (e.g., Geography = City-wide, Time range = multi-year).
2. Apply filters.
3. Observe whether a warning is displayed.
4. Acknowledge the warning and choose to proceed.
5. Observe completion or continued loading.

**Expected Results**
- System detects the high-volume request and displays a **warning** indicating possible long load time/performance impact.
- After acknowledgment, the system proceeds with data retrieval.
- The UI shows an appropriate loading/progress state while processing.
- If retrieval completes, results are displayed; if not, an error state is shown with logs (covered by AT-06).

---

## AT-05 — No data matches selected filters shows “no data” message and logs condition
**Covers**: Extension 4a (4a1–4a2)  
**Preconditions**
- Choose filter combination guaranteed to return zero matches (e.g., nonexistent category or a time range outside seeded data).

**Steps**
1. Select filters that produce no matches.
2. Apply filters.
3. Observe the UI response and logs.

**Expected Results**
- UI displays a clear **no-data** message (not a generic error).
- No chart/table with misleading values is shown.
- System logs a no-data condition including the filter set (or a request id correlated to it).

---

## AT-06 — Data retrieval failure shows error state and logs failure
**Covers**: Extension 4b; Failed End Condition  
**Preconditions**
- Configure the data layer to fail retrieval (e.g., simulate DB outage, timeout, or 5xx).
- Interface and visualization module are otherwise operational.

**Steps**
1. Apply any valid filter set.
2. Inject a retrieval failure before/while the query runs.
3. Observe UI state and logs.

**Expected Results**
- UI displays an **error state** indicating data could not be retrieved.
- No partial/misleading chart or table is displayed.
- Logs include retrieval failure details (error type/category, timestamp, correlation id).

---

## AT-07 — Visualization rendering error shows error state and logs failure
**Covers**: Extension 6a; Failed End Condition  
**Preconditions**
- Data retrieval succeeds for a chosen filter set (matching data exists).
- Configure visualization module to fail rendering (e.g., injected exception).

**Steps**
1. Apply a filter set known to return matching data.
2. Allow data retrieval and aggregation to complete.
3. Inject visualization rendering failure.
4. Observe UI state and logs.

**Expected Results**
- UI displays an **error state** indicating visualization could not be rendered.
- System does not display incomplete or corrupted visuals.
- Logs include rendering failure details and correlation to the request.

---

## AT-08 — Filter integrity: results correspond to selected category, time range, and geography
**Covers**: Cross-cutting invariant; Success End Condition correctness  
**Preconditions**
- Seeded dataset contains:
  - overlapping categories across the same dates/geographies
  - overlapping geographies for the same categories/time ranges
- Ability to inspect the effective query parameters used (via logs, debug panel, or captured requests).

**Steps**
1. Run Query A with filters (Category_A, T1–T2, Geo_1).
2. Run Query B changing exactly one filter dimension (e.g., Geo_2, keeping Category_A and T1–T2).
3. Compare results between A and B (counts/trends should change consistently with seeded differences).
4. Repeat by changing category only, then time range only.

**Expected Results**
- Results change only in ways consistent with the filter dimension changed.
- The system does not “leak” values from outside the selected time range or geography.
- Logs/requests confirm the effective query parameters match the UI-selected filters.

---

## AT-09 — Clarity over partial results: system shows either valid data, no-data, or error (never a misleading partial)
**Covers**: Key behavioral theme across alternatives (data integrity & clarity)  
**Preconditions**
- Test harness supports injecting failures at different stages:
  - during retrieval
  - after retrieval, during aggregation/prep
  - during rendering

**Steps**
1. Run a query and inject a retrieval failure (as in AT-06).
2. Run a query and inject a rendering failure (as in AT-07).
3. If supported, inject an aggregation/prep failure between retrieval and rendering.
4. Observe the UI in each case.

**Expected Results**
- In each failure mode, UI shows a clear **error state** (or no-data where applicable).
- System does not display partial charts/tables that could be misinterpreted as complete.
- Logs reflect the correct failure stage and outcome.

---

## Traceability Matrix
| Acceptance Test | UC-07 Flow Covered |
|---|---|
| AT-01 | Main Success Scenario (1–2) |
| AT-02 | Main Success Scenario (3–7) |
| AT-03 | Main Success Scenario (8); Success End Condition |
| AT-04 | Extension 3a |
| AT-05 | Extension 4a |
| AT-06 | Extension 4b; Failed End Condition |
| AT-07 | Extension 6a; Failed End Condition |
| AT-08 | Cross-cutting correctness invariant (filters → results) |
| AT-09 | Cross-cutting integrity/clarity theme (no misleading partials) |
