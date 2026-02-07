# UC-03 Acceptance Test Suite: Generate 1-Day Demand Forecast

**Use Case**: UC-03 Generate 1-Day Demand Forecast  
**Scope**: Operations Analytics System  
**Goal**: Verify the system can generate (or retrieve) a current next-24-hour forecast by service category and geography when available, store it safely, and handle defined failure/limitation paths without replacing the most recent valid forecast.

---

## Assumptions / Test Harness Requirements
- A way to trigger forecast generation:
  - on-demand request from Operational Manager
  - scheduled forecast generation event
- A controllable data layer:
  - ability to provide “latest validated operational data” or simulate its absence
  - ability to simulate incomplete geographic fields
- Ability to inject failures:
  - forecasting engine execution failure
  - storage write failure
- Observability:
  - logs accessible for assertions
  - forecast store queryable for:
    - latest forecast version `F_prev`
    - newly generated forecast `F_new`
    - “current forecast” pointer/flag
    - forecast horizon metadata (covers next 24 hours)
    - breakdown dimensions present (category; optionally geography)

---

## AT-01 — On-demand request generates a new 24-hour forecast and marks it current
**Covers**: Main Success Scenario  
**Preconditions**
- Latest validated operational data is available.
- Forecasting engine is operational.
- Storage is healthy.
- Existing current forecast is either absent or not current for the upcoming 24-hour window.
- If geography breakdown is expected: operational data includes geography fields.

**Steps**
1. Operational Manager initiates a 1-day forecast request.
2. Wait for forecast job completion.
3. Query forecast store for `F_new` and its metadata.
4. Query “current forecast” pointer/flag.
5. Inspect forecast output structure (dimensions).

**Expected Results**
- Job status = **success**.
- `F_new` exists and is stored.
- `F_new` horizon covers the **next 24 hours**.
- Forecast includes breakdown by **service category**.
- If geography is available, forecast includes geography segmentation as well.
- “Current forecast” points to `F_new`.
- Logs contain successful forecast generation record.

---

## AT-02 — Scheduled run generates a new 24-hour forecast and marks it current
**Covers**: Main Success Scenario (scheduled trigger)  
**Preconditions**
- Same as AT-01, but using scheduled trigger mechanism.

**Steps**
1. Trigger the scheduled forecast generation event (or wait until schedule fires in test env).
2. Wait for completion and query forecast store / current pointer.

**Expected Results**
- Same as AT-01.

---

## AT-03 — Forecast already current is retrieved without rerunning the model
**Covers**: Extension 1a  
**Preconditions**
- A forecast `F_prev` exists and is marked **current** for the upcoming 24-hour window.
- Ability to detect model execution (e.g., engine invocation counter, job audit log, or metric).

**Steps**
1. Operational Manager initiates a 1-day forecast request.
2. Observe system behavior and logs.
3. Query returned/served forecast identifier and current pointer.

**Expected Results**
- No new forecast version is created (no `F_new`), unless system policy versions reads (then ensure model not rerun).
- The served forecast is `F_prev`.
- Forecasting engine is **not invoked** (or invocation count unchanged).
- Logs indicate “current forecast served” (per 1a2).
- Success end condition satisfied (forecast available and current).

---

## AT-04 — Required data unavailable causes failure and retains the most recent valid forecast
**Covers**: Extension 2a  
**Preconditions**
- Most recent valid forecast exists: `F_prev` is marked current (or at least available).
- Latest validated operational data is missing or inaccessible (simulate data retrieval failure).

**Steps**
1. Trigger 1-day forecast generation.
2. Wait for job completion.
3. Query “current forecast” pointer and available forecasts.
4. Review logs for missing data issue.

**Expected Results**
- Job status = **failed**.
- No new forecast is produced/stored as current.
- “Current forecast” remains `F_prev`.
- Logs record missing data condition and run failure.

---

## AT-05 — Forecasting engine error causes failure and retains the most recent valid forecast
**Covers**: Extension 4a  
**Preconditions**
- `F_prev` exists and is available/current.
- Latest validated data is available.
- Inject forecasting engine failure (runtime/config/resource error).

**Steps**
1. Trigger 1-day forecast generation.
2. Wait for completion.
3. Query current pointer and confirm no new current forecast.
4. Review logs for model execution failure.

**Expected Results**
- Job status = **failed**.
- No new forecast is marked current.
- “Current forecast” remains `F_prev`.
- Logs include engine error details.

---

## AT-06 — Geographic data incomplete produces category-only forecast and logs limitation
**Covers**: Extension 6a  
**Preconditions**
- Latest validated operational data is available but lacks sufficient geographic detail (simulate missing/partial geo fields).
- Forecasting engine and storage are healthy.

**Steps**
1. Trigger 1-day forecast generation.
2. Wait for completion.
3. Inspect forecast output dimensions.
4. Review logs for geo limitation.

**Expected Results**
- Job status = **success** (partial segmentation).
- Forecast includes **service category** breakdown.
- Forecast does **not** include geographic segmentation.
- Forecast is stored and marked current.
- Logs indicate geographic data incomplete / limitation.

---

## AT-07 — Storage failure prevents updating “current” forecast and retains prior forecast
**Covers**: Extension 7a  
**Preconditions**
- `F_prev` exists and is current/available.
- Latest validated data is available.
- Forecasting engine runs successfully.
- Inject storage failure (DB outage/capacity/permission).

**Steps**
1. Trigger 1-day forecast generation.
2. Wait for completion.
3. Query “current forecast” pointer.
4. Review logs for storage error.

**Expected Results**
- Job status = **failed**.
- New forecast is not stored as current (may not exist at all, or exists only transiently).
- “Current forecast” remains `F_prev`.
- Logs include storage failure details.

---

## AT-08 — No partial activation: forecast becomes current only after successful store
**Covers**: Cross-cutting safety invariant  
**Preconditions**
- `F_prev` exists and is current/available.
- Configure a failure after model execution but before store (storage failure) OR fail during engine (4a).

**Steps**
1. Trigger forecast generation with the selected failure injection.
2. Observe system state during/after run (poll current pointer).
3. Confirm current pointer does not change to an incomplete/unstored forecast.

**Expected Results**
- “Current forecast” remains `F_prev` throughout the failure.
- No partial/unfinished forecast replaces the current one.
- Logs reflect failure and no activation.

---

## Traceability Matrix
| Acceptance Test | UC-03 Flow Covered |
|---|---|
| AT-01 | Main Success (on-demand) |
| AT-02 | Main Success (scheduled) |
| AT-03 | Extension 1a |
| AT-04 | Extension 2a |
| AT-05 | Extension 4a |
| AT-06 | Extension 6a |
| AT-07 | Extension 7a |
| AT-08 | Cross-cutting “no partial activation” property |
