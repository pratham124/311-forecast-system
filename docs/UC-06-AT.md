# UC-06 Acceptance Test Suite: Evaluate Forecasting Engine Against Baselines

**Use Case**: UC-06 Evaluate Forecasting Engine Against Baselines  
**Scope**: Operations Analytics System  
**Goal**: Verify the system evaluates the forecasting engine against baseline methods using historical data and actuals, computes and aggregates metrics, stores results for review, and handles defined failure/limitation paths without overwriting prior valid evaluation results.

---

## Assumptions / Test Harness Requirements
- A way to trigger evaluation:
  - on-demand request by Performance Analyst
  - scheduled evaluation cycle event
- Controllable data layer/stubs for:
  - historical demand data (present/absent)
  - forecasting engine outputs (present/absent)
  - baseline model module (success/failure injection)
- Ability to inject failures:
  - baseline generation failure
  - metric computation failure (e.g., divide-by-zero in MAPE, insufficient data)
  - storage write failure
- Observability:
  - logs accessible for assertions
  - evaluation results store queryable for:
    - latest valid evaluation `E_prev`
    - newly produced evaluation `E_new`
    - “current evaluation” pointer/flag (if applicable)
    - per-metric values and aggregation breakdowns
    - notes/metadata for excluded metrics/categories in partial evaluations (5a)

---

## AT-01 — On-demand evaluation completes and stores results comparing engine vs baselines
**Covers**: Main Success Scenario (on-demand)  
**Preconditions**
- Historical demand data includes actual outcomes for a defined evaluation window.
- Recent forecast outputs exist for the same window (engine predictions).
- Baseline methods configured (e.g., seasonal naïve, moving average).
- Storage is healthy.

**Steps**
1. Performance Analyst initiates an evaluation.
2. Wait for evaluation completion.
3. Query evaluation results store for `E_new`.
4. Inspect `E_new` contents.

**Expected Results**
- Evaluation status = **success**.
- `E_new` exists and is stored.
- `E_new` contains:
  - engine metrics (MAE/RMSE/MAPE or configured set)
  - baseline metrics for each baseline method
  - direct comparison outputs (e.g., side-by-side table/fields)
  - aggregation across service categories and time periods
- Results are available for review (e.g., retrievable via report endpoint/UI).
- Logs indicate successful evaluation completion.

---

## AT-02 — Scheduled evaluation completes and stores results
**Covers**: Main Success Scenario (scheduled trigger)  
**Preconditions**
- Same as AT-01 but executed via scheduled evaluation event.

**Steps**
1. Trigger scheduled evaluation event (or allow schedule to fire in test env).
2. Wait for completion and query results.

**Expected Results**
- Same as AT-01.

---

## AT-03 — Required data unavailable fails evaluation and retains previous results
**Covers**: Extension 2a  
**Preconditions**
- Previous valid evaluation exists: `E_prev`.
- Historical demand data is missing/inaccessible OR actual outcomes missing for the evaluation window.

**Steps**
1. Trigger evaluation.
2. Wait for completion.
3. Query evaluation results store for changes.
4. Check logs.

**Expected Results**
- Evaluation status = **failed**.
- No new evaluation replaces `E_prev`.
- `E_prev` remains the latest available evaluation.
- Logs indicate missing data and run failure.

---

## AT-04 — Forecast output missing fails evaluation and retains previous results
**Covers**: Extension 4a  
**Preconditions**
- `E_prev` exists.
- Historical demand data is available.
- Forecasting engine outputs for the evaluation window are missing/incomplete.

**Steps**
1. Trigger evaluation.
2. Wait for completion.
3. Confirm no new evaluation is stored as current/latest.
4. Check logs.

**Expected Results**
- Evaluation status = **failed**.
- `E_prev` remains available as the latest valid evaluation.
- Logs indicate missing forecast outputs.

---

## AT-05 — Baseline model failure fails evaluation and retains previous results
**Covers**: Extension 3a  
**Preconditions**
- `E_prev` exists.
- Historical demand data and engine outputs available.
- Inject failure in baseline model module (e.g., moving average configuration error).

**Steps**
1. Trigger evaluation.
2. Wait for completion.
3. Query evaluation results store and current/latest pointer.
4. Check logs for baseline failure.

**Expected Results**
- Evaluation status = **failed**.
- No new evaluation replaces `E_prev`.
- Logs show baseline generation error and run marked failed.

---

## AT-06 — Metric computation failure produces partial results and stores with exclusions noted
**Covers**: Extension 5a  
**Preconditions**
- Historical demand data and engine/baseline outputs are available.
- Create a test condition causing metric failure for at least one metric/category (e.g., actual = 0 for MAPE, insufficient samples).
- Storage is healthy.

**Steps**
1. Trigger evaluation.
2. Wait for completion.
3. Query stored evaluation `E_new`.
4. Inspect metrics and metadata notes.

**Expected Results**
- Evaluation completes with **partial success** (still stored and available).
- Logs indicate metric calculation issue.
- `E_new` includes:
  - computed metrics for valid metrics/categories
  - excluded metrics/categories clearly identified (e.g., flags, nulls, “excluded_reason” metadata)
- Aggregations are computed using only valid included components (or clearly marked as partial).
- Success end condition is satisfied in a limited form (results stored and available with documented limitations).

---

## AT-07 — Storage failure prevents saving evaluation and retains previous results
**Covers**: Extension 7a  
**Preconditions**
- `E_prev` exists.
- Evaluation can compute successfully (data + baselines + metrics).
- Inject storage failure during write (DB outage/capacity/permission).

**Steps**
1. Trigger evaluation.
2. Wait for completion.
3. Query results store for presence of `E_new` and current/latest pointer.
4. Check logs.

**Expected Results**
- Evaluation status = **failed**.
- `E_new` is not stored as the latest/official result.
- `E_prev` remains available.
- Logs show storage error and evaluation marked failed.

---

## AT-08 — Comparability guard: evaluation uses same window/slice for engine and baseline
**Covers**: Step 4 correctness (fair comparison)  
**Preconditions**
- Define a known evaluation window and service categories.
- Provide engine outputs and baseline outputs for that exact window.
- Provide actuals for that exact window.

**Steps**
1. Trigger evaluation.
2. Inspect evaluation metadata for window definition (start/end timestamps) and category coverage.
3. Verify engine and baseline comparisons reference the same actuals set (counts/keys match).

**Expected Results**
- Evaluation metadata explicitly reflects the same window/slice across engine and baselines.
- No mismatch in row counts/keys between predictions and actuals used for each model (or mismatches are logged and handled per policy).
- Results are comparable and interpretable.

---

## Traceability Matrix
| Acceptance Test | UC-06 Flow Covered |
|---|---|
| AT-01 | Main Success (on-demand) |
| AT-02 | Main Success (scheduled) |
| AT-03 | Extension 2a |
| AT-04 | Extension 4a |
| AT-05 | Extension 3a |
| AT-06 | Extension 5a |
| AT-07 | Extension 7a |
| AT-08 | Step 4 fairness/comparability validation |
