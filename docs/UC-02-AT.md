# UC-02 Acceptance Test Suite: Validate and Deduplicate Ingested Data

**Use Case**: UC-02 Validate and Deduplicate Ingested Data  
**Scope**: Operations Analytics System  
**Goal**: Verify newly ingested datasets are schema-validated and deduplicated before being stored and marked approved for downstream forecasting/dashboards, and that failure paths preserve the previously approved dataset.

---

## Assumptions / Test Harness Requirements
- A way to submit an ingested dataset into the processing pipeline (e.g., upload/import, ingestion event trigger).
- A controllable **Validation Engine** and **Deduplication** configuration for test data (schema rules + dedup keys/policy).
- Ability to inject failures:
  - schema validation failure (malformed payload / missing fields)
  - deduplication process failure (rule engine exception/resource error)
  - storage write failure
- Observability:
  - logs accessible for assertions
  - “approved/clean dataset” marker queryable (e.g., dataset status = APPROVED/CLEAN)
  - ability to query latest approved dataset version `V_prev` and any candidate dataset `V_new`
  - ability to query downstream-availability flag used by forecasting/dashboards

---

## AT-01 — Valid dataset passes validation + dedup and becomes approved
**Covers**: Main Success Scenario  
**Preconditions**
- A previously approved dataset exists: `V_prev`.
- Schema rules and dedup rules are enabled.
- Storage is healthy.
- Ingested test dataset `D_new` conforms to schema and contains some duplicates resolvable by policy.

**Steps**
1. Ingest `D_new` (trigger UC-02).
2. Wait for validation + dedup processing to complete.
3. Query dataset processing status for `D_new`.
4. Query storage for stored cleaned dataset version `V_new`.
5. Query “approved/available for downstream” flag.

**Expected Results**
- `D_new` status transitions through validation + dedup to **CLEAN/APPROVED**.
- `V_new` exists in storage.
- `V_new` is marked **available** for forecasting/dashboards.
- Logs record successful validation and dedup (including duplicates removed/consolidated count if tracked).
- `V_prev` remains available but is superseded by `V_new` as the latest approved dataset (if the system uses a single “latest” pointer).

---

## AT-02 — Schema validation failure rejects dataset and does not proceed to dedup
**Covers**: Extension 2a  
**Preconditions**
- Latest approved dataset exists: `V_prev`.
- Ingested dataset `D_bad_schema` violates schema (e.g., missing required columns, wrong data types).

**Steps**
1. Ingest `D_bad_schema`.
2. Wait for processing attempt.
3. Query processing status and stage reached.
4. Query whether any cleaned dataset was stored/approved.
5. Verify downstream-availability pointer remains on `V_prev`.
6. Check logs for validation failure details.

**Expected Results**
- Processing status = **REJECTED/FAILED** due to schema errors.
- Deduplication stage is **not executed**.
- No new dataset is marked approved/available.
- `V_prev` remains the latest approved dataset.
- Logs include schema errors (what failed and why).

---

## AT-03 — Deduplication process failure prevents approval and preserves prior dataset
**Covers**: Extension 4a  
**Preconditions**
- Latest approved dataset exists: `V_prev`.
- Ingested dataset `D_ok_schema` passes schema validation.
- Inject deduplication processing failure (e.g., forced exception in dedup module).

**Steps**
1. Ingest `D_ok_schema`.
2. Wait for processing attempt.
3. Verify schema validation stage succeeded.
4. Verify deduplication stage failed.
5. Query whether dataset was stored and/or marked approved.
6. Check logs for dedup failure details.

**Expected Results**
- Schema validation = **passed**.
- Deduplication stage = **failed**.
- No dataset is marked **CLEAN/APPROVED**.
- Downstream availability remains pointing to `V_prev`.
- Logs include processing error and run marked failed.

---

## AT-04 — Excessive duplicate rate triggers “flag for review” and blocks approval
**Covers**: Extension 5a  
**Preconditions**
- Latest approved dataset exists: `V_prev`.
- Duplicate-rate threshold config is set for the test (even if “open issue” in spec, assume a configured value exists in test env).
- Ingested dataset `D_high_dupes` passes schema validation but contains duplicates exceeding the threshold.

**Steps**
1. Ingest `D_high_dupes`.
2. Wait for processing.
3. Query processing status and any “flagged for review” indicator.
4. Query whether dataset is marked clean/approved and available to downstream.
5. Check logs for duplicate-rate detection.

**Expected Results**
- Dataset is **FLAGGED_FOR_REVIEW** (or equivalent) and **not** marked CLEAN/APPROVED.
- Dataset is **not** available for forecasting/dashboards.
- `V_prev` remains the latest approved dataset for downstream use.
- Logs indicate excessive duplicate rate condition.

---

## AT-05 — Storage failure prevents approval even if validation + dedup succeed
**Covers**: Extension 7a  
**Preconditions**
- Latest approved dataset exists: `V_prev`.
- Ingested dataset `D_ok` passes schema validation and deduplication.
- Inject storage write failure (e.g., DB outage/capacity/permission error).

**Steps**
1. Ingest `D_ok`.
2. Wait for processing.
3. Verify validation and dedup steps complete successfully.
4. Observe storage write attempt fails.
5. Query dataset status and downstream-availability pointer.
6. Check logs for storage error.

**Expected Results**
- Processing status = **failed** due to storage.
- No new dataset is marked approved/available.
- `V_prev` remains available for forecasting/dashboards.
- Logs contain storage failure details.

---

## AT-06 — No partial activation: dataset becomes available only after full pipeline success
**Covers**: Cross-cutting safety invariant  
**Preconditions**
- Latest approved dataset exists: `V_prev`.
- Prepare an ingest dataset that passes schema validation.
- Inject failure at one stage (dedup failure or storage failure).

**Steps**
1. Ingest dataset.
2. During processing, poll dataset status transitions.
3. Assert that “available for forecasting/dashboards” remains false for the candidate dataset.
4. After failure, confirm the candidate dataset is not marked clean/approved.

**Expected Results**
- Candidate dataset is never marked available/approved unless all required steps succeed.
- `V_prev` remains active/available throughout.

---

## AT-07 — Deduplication policy is applied consistently for resolvable duplicates
**Covers**: Main success step 5 (policy behavior)  
**Preconditions**
- Dedup policy is defined in the test environment (e.g., “keep most recent by timestamp” or “merge non-conflicting fields”).
- Ingested dataset `D_dupes` includes a known duplicate pair where the expected surviving/merged record is deterministic.

**Steps**
1. Ingest `D_dupes`.
2. Wait for processing success.
3. Query cleaned dataset for the duplicate key(s).
4. Compare cleaned record(s) to expected policy outcome.

**Expected Results**
- Only one record per dedup key exists in cleaned dataset.
- The retained/merged record matches the configured dedup policy.
- Dataset is approved and available downstream.

---

## Traceability Matrix
| Acceptance Test | UC-02 Flow Covered |
|---|---|
| AT-01 | Main Success Scenario (1–9) |
| AT-02 | Extension 2a |
| AT-03 | Extension 4a |
| AT-04 | Extension 5a |
| AT-05 | Extension 7a |
| AT-06 | Cross-cutting “no partial activation” property |
| AT-07 | Step 5 deduplication policy correctness |
