# UC-01 Acceptance Test Suite: Automatically Pull 311 Service Request Data

**Use Case**: UC-01 Automatically Pull 311 Service Request Data  
**Scope**: Operations Analytics System  
**Goal**: Verify scheduled ingestion pulls 311 data, validates it, stores it safely, and handles failure/edge conditions without corrupting the “current” dataset.

---

## Assumptions / Test Harness Requirements
- A controllable **Scheduling Service** test trigger (manual fire of the scheduled job) and observable run status.
- A stub/mock or sandbox **311 Data Source API** supporting:
  - success with new records
  - success with no new records
  - auth failure
  - timeout/unavailable
  - malformed/invalid payload
- A **Data Storage System** test environment supporting failure injection (write failure).
- Observability:
  - system logs accessible for assertions
  - “current dataset” marker (e.g., flag/version pointer) queryable
  - ability to query “latest active dataset” and record counts/version ids

---

## AT-01 — Scheduled trigger runs ingestion successfully and activates new dataset
**Covers**: Main Success Scenario  
**Preconditions**
- Valid 311 API credentials configured.
- Storage is healthy.
- Current dataset exists with version `V_prev`.
- 311 API is configured to return a valid dataset with **new records** since last pull.

**Steps**
1. Trigger the scheduled ingestion job at the configured time (or manually trigger the schedule event).
2. Observe the job execution completion status.
3. Query storage for a newly stored dataset version `V_new`.
4. Query the system “current dataset” pointer/flag.

**Expected Results**
- Job status = **success**.
- `V_new` exists and is stored.
- Dataset validation status for `V_new` = **passed**.
- “Current dataset” points to `V_new` (not `V_prev`).
- Logs include a success record containing run timestamp and completion status.

---

## AT-02 — Authentication failure does not change current dataset
**Covers**: Extension 2a  
**Preconditions**
- Current dataset exists with version `V_prev`.
- 311 API credentials are invalid/expired OR API stub returns auth failure.

**Steps**
1. Trigger the scheduled ingestion job.
2. Observe job completion status.
3. Query “current dataset” pointer/flag.
4. Review logs for authentication error record.

**Expected Results**
- Job status = **failed**.
- No new dataset version is activated.
- “Current dataset” remains `V_prev`.
- Logs contain authentication failure details.

---

## AT-03 — Data source unavailable/timeout does not change current dataset
**Covers**: Extension 4a  
**Preconditions**
- Current dataset exists with version `V_prev`.
- 311 API stub simulates timeout/unavailability.

**Steps**
1. Trigger the scheduled ingestion job.
2. Observe job completion status.
3. Query “current dataset” pointer/flag.
4. Review logs for connection/timeout record.

**Expected Results**
- Job status = **failed**.
- “Current dataset” remains `V_prev`.
- Logs contain timeout/unavailable error details.

---

## AT-04 — “No new records” is treated as success and dataset remains unchanged
**Covers**: Extension 4b  
**Preconditions**
- Current dataset exists with version `V_prev`.
- 311 API stub returns success with **no new records** since last pull (empty incremental set or explicit “no updates”).

**Steps**
1. Trigger the scheduled ingestion job.
2. Observe job completion status.
3. Query “current dataset” pointer/flag.
4. Review logs for “no new records” message.

**Expected Results**
- Job status = **success**.
- “Current dataset” remains `V_prev` (no new active dataset created/activated).
- Logs indicate **no new records** and that the run completed successfully.

---

## AT-05 — Validation failure rejects data and does not activate new dataset
**Covers**: Extension 5a  
**Preconditions**
- Current dataset exists with version `V_prev`.
- 311 API stub returns a payload that violates schema/validation rules (e.g., missing required columns, invalid date types).

**Steps**
1. Trigger the scheduled ingestion job.
2. Observe job completion status.
3. Query whether a new dataset version `V_candidate` was stored/activated.
4. Query “current dataset” pointer/flag.
5. Review logs for validation error details.

**Expected Results**
- Job status = **failed**.
- Invalid dataset is **not** marked current (no activation).
- “Current dataset” remains `V_prev`.
- Logs contain validation errors and rejection outcome.

---

## AT-06 — Storage failure does not activate new dataset
**Covers**: Extension 6a  
**Preconditions**
- Current dataset exists with version `V_prev`.
- 311 API stub returns valid data.
- Storage system is configured to fail writes (e.g., permission/capacity/forced error).

**Steps**
1. Trigger the scheduled ingestion job.
2. Observe job completion status.
3. Query “current dataset” pointer/flag.
4. Review logs for storage error.

**Expected Results**
- Job status = **failed**.
- No new dataset is activated.
- “Current dataset” remains `V_prev`.
- Logs contain storage failure details.

---

## AT-07 — No partial activation: current dataset changes only after validation + successful store
**Covers**: Safety property across all extensions  
**Preconditions**
- Current dataset exists with version `V_prev`.
- 311 API returns valid data.
- Inject a failure **after retrieval** but **before successful store** (e.g., force storage failure or force validation failure).

**Steps**
1. Trigger the scheduled ingestion job with the chosen failure injection.
2. During/after run, query the “current dataset” pointer/flag.
3. Verify whether any intermediate dataset exists and whether it is marked current.

**Expected Results**
- If the run fails, “current dataset” remains `V_prev`.
- No intermediate/partial dataset is marked current.
- Logs show failure and no activation.

---

## AT-08 — Failure notification is recorded for monitoring on failed runs
**Covers**: Failed End Condition (“failure notification is recorded”)  
**Preconditions**
- Configure a failure mode (auth fail OR timeout OR validation fail OR storage fail).
- Monitoring/notification record mechanism is accessible for assertion (e.g., monitoring table, event bus topic, alert log).

**Steps**
1. Trigger the scheduled ingestion job under the failure mode.
2. Verify run status is failed.
3. Check the monitoring/notification record store for an entry corresponding to the run.

**Expected Results**
- Job status = **failed**.
- A failure notification record exists, referencing the run (timestamp/id) and failure reason category.
- “Current dataset” remains unchanged.

---

## Traceability Matrix
| Acceptance Test | UC-01 Flow Covered |
|---|---|
| AT-01 | Main Success Scenario |
| AT-02 | Extension 2a |
| AT-03 | Extension 4a |
| AT-04 | Extension 4b |
| AT-05 | Extension 5a |
| AT-06 | Extension 6a |
| AT-07 | Cross-cutting safety invariant |
| AT-08 | Failed End Condition (monitoring notification) |
