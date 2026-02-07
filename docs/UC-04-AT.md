# UC-04 Acceptance Test Suite: Generate 7-Day Demand Forecast

**Use Case**: UC-04 Generate 7-Day Demand Forecast  
**Scope**: Operations Analytics System  
**Goal**: Verify the system can generate (or retrieve) a current next-7-days forecast by service category and geography when available, store it safely, and handle defined failure/limitation paths without replacing the most recent valid weekly forecast.

---

## Assumptions / Test Harness Requirements
- A way to trigger weekly forecast generation:
  - on-demand request from Operational Manager
  - scheduled weekly forecast generation event
- A controllable data layer:
  - ability to provide “latest validated operational data” or simulate its absence/corruption
  - ability to simulate incomplete geographic fields
- Ability to inject failures:
  - forecasting engine execution failure
  - storage write failure
- Observability:
  - logs accessible for assertions
  - forecast store queryable for:
    - latest weekly forecast version `W_prev`
    - newly generated weekly forecast `W_new`
    - “current weekly forecast” pointer/flag
    - horizon metadata (covers next 7 days)
    - breakdown dimensions present (category; optionally geography)

---

## AT-01 — On-demand request generates a new 7-day forecast and marks it current
**Covers**: Main Success Scenario (on-demand)  
**Preconditions**
- Latest validated operational data is available.
- Forecasting engine is operational.
- Storage is healthy.
- Existing weekly forecast is absent or not current for the next 7-day window.
- If geography breakdown is expected: operational data includes geography fields.

**Steps**
1. Operational Manager initiates a 7-day forecast request.
2. Wait for forecast job completion.
3. Query forecast store for `W_new` and its metadata.
4. Query “current weekly forecast” pointer/flag.
5. Inspect forecast output structure (dimensions + horizon).

**Expected Results**
- Job status = **success**.
- `W_new` exists and is stored.
- `W_new` horizon covers the **next 7 days**.
- Forecast includes breakdown by **service category**.
- If geography is available, forecast includes geographic segmentation.
- “Current weekly forecast” points to `W_new`.
- Logs contain successful forecast generation record.

---

## AT-02 — Scheduled weekly run generates a new 7-day forecast and marks it current
**Covers**: Main Success Scenario (scheduled trigger)  
**Preconditions**
- Same as AT-01, but using scheduled trigger mechanism.

**Steps**
1. Trigger the scheduled weekly forecast generation event (or wait until schedule fires in test env).
2. Wait for completion and query forecast store / current pointer.

**Expected Results**
- Same as AT-01.

---

## AT-03 — Weekly forecast already current is retrieved without rerunning the model
**Covers**: Extension 1a  
**Preconditions**
- A weekly forecast `W_prev` exists and is marked **current** for the upcoming 7-day window.
- Ability to detect model execution (engine invocation counter, job audit log, or metric).

**Steps**
1. Operational Manager initiates a 7-day forecast request.
2. Observe system behavior and logs.
3. Query served forecast identifier and “current weekly forecast” pointer.

**Expected Results**
- No new weekly forecast is created (no `W_new`), unless system versions reads (then ensure model not rerun).
- The served forecast is `W_prev`.
- Forecasting engine is **not invoked** (or invocation count unchanged).
- Logs indicate “current weekly forecast served” (per 1a2).
- Success end condition satisfied (weekly forecast available and current).

---

## AT-04 — Required data unavailable causes failure and retains the most recent valid weekly forecast
**Covers**: Extension 2a  
**Preconditions**
- Most recent valid weekly forecast exists: `W_prev` is current/available.
- Latest validated operational data is missing, corrupted, or inaccessible (simulate retrieval failure).

**Steps**
1. Trigger 7-day forecast generation.
2. Wait for job completion.
3. Query “current weekly forecast” pointer and available forecasts.
4. Review logs for missing data issue.

**Expected Results**
- Job status = **failed**.
- No new weekly forecast is produced/stored as current.
- “Current weekly forecast” remains `W_prev`.
- Logs record missing data condition and run failure.

---

## AT-05 — Forecasting engine error causes failure and retains the most recent valid weekly forecast
**Covers**: Extension 4a  
**Preconditions**
- `W_prev` exists and is current/available.
- Latest validated data is available.
- Inject forecasting engine failure (runtime/config/resource error).

**Steps**
1. Trigger 7-day forecast generation.
2. Wait for completion.
3. Query current pointer and confirm no new current weekly forecast.
4. Review logs for model execution failure.

**Expected Results**
- Job status = **failed**.
- No new weekly forecast is marked current.
- “Current weekly forecast” remains `W_prev`.
- Logs include engine error details.

---

## AT-06 — Geographic data incomplete produces category-only weekly forecast and logs limitation
**Covers**: Extension 6a  
**Preconditions**
- Latest validated operational data is available but lacks sufficient geographic detail (simulate missing/partial geo fields).
- Forecasting engine and storage are healthy.

**Steps**
1. Trigger 7-day forecast generation.
2. Wait for completion.
3. Inspect forecast output dimensions.
4. Review logs for geo limitation.

**Expected Results**
- Job status = **success** (partial segmentation).
- Weekly forecast includes **service category** breakdown.
- Weekly forecast does **not** include geographic segmentation.
- Weekly forecast is stored and marked current.
- Logs indicate geographic data incomplete / limitation.

---

## AT-07 — Storage failure prevents updating “current weekly forecast” and retains prior weekly forecast
**Covers**: Extension 7a  
**Preconditions**
- `W_prev` exists and is current/available.
- Latest validated data is available.
- Forecasting engine runs successfully.
- Inject storage failure (DB outage/capacity/permission).

**Steps**
1. Trigger 7-day forecast generation.
2. Wait for completion.
3. Query “current weekly forecast” pointer.
4. Review logs for storage error.

**Expected Results**
- Job status = **failed**.
- New weekly forecast is not stored as current (may not exist at all, or exists only transiently).
- “Current weekly forecast” remains `W_prev`.
- Logs include storage failure details.

---

## AT-08 — No partial activation: weekly forecast becomes current only after successful store
**Covers**: Cross-cutting safety invariant  
**Preconditions**
- `W_prev` exists and is current/available.
- Configure a failure after model execution but before store (storage failure) OR fail during engine (4a).

**Steps**
1. Trigger weekly forecast generation with the selected failure injection.
2. Observe system state during/after run (poll current pointer).
3. Confirm current pointer does not change to an incomplete/unstored weekly forecast.

**Expected Results**
- “Current weekly forecast” remains `W_prev` throughout the failure.
- No partial/unfinished weekly forecast replaces the current one.
- Logs reflect failure and no activation.

---

## Traceability Matrix
| Acceptance Test | UC-04 Flow Covered |
|---|---|
| AT-01 | Main Success (on-demand) |
| AT-02 | Main Success (scheduled) |
| AT-03 | Extension 1a |
| AT-04 | Extension 2a |
| AT-05 | Extension 4a |
| AT-06 | Extension 6a |
| AT-07 | Extension 7a |
| AT-08 | Cross-cutting “no partial activation” property |
