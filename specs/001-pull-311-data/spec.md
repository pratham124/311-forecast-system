# Feature Specification: UC-01 Scheduled 311 Data Pull

**Feature Branch**: `001-pull-311-data`  
**Created**: 2026-03-11  
**Status**: Draft  
**Input**: User description: "We are implementing one use case at a time, and UC-01 is already fully specified in: - docs/UC-01.md - docs/UC-01-AT.md Do NOT generate or rewrite the UC files. Treat UC-01-AT.md as the source of truth for required behavior and edge cases. Implement only what is necessary to satisfy UC-01 and make UC-01-AT.md pass, while strictly following constitution.md. If any minimal assumptions are unavoidable, document them briefly in docs/architecture/assumptions.md and keep them consistent with the UC and acceptance tests."

## Clarifications

### Session 2026-03-11

- Q: What UC-01 clarifications must be made explicit without changing `docs/UC-01.md` or `docs/UC-01-AT.md`? → A: Define outcome-based dataset creation and activation rules, the last-successful-pull cursor strategy including first-run behavior, the minimum queryable current-dataset fields, candidate versus stored versus current dataset states, the minimum failure-notification record contents and location, and UC-01 scope boundaries in `docs/architecture/assumptions.md`.

### Session 2026-03-12

- Q: Which UC-01 security and privacy clarifications should be reflected in the feature spec without changing acceptance behavior? → A: Make endpoint protection concrete with JWT authentication and explicit Operational Manager versus City Planner permissions, and constrain failure summaries and logs to exclude secrets and raw source payloads while allowing only summaries, counts, error codes, and at most a small redacted example that never includes full rows.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Refresh Current 311 Dataset (Priority: P1)

As an operational manager, I need the system to pull the latest Edmonton 311 service request data on schedule so the authoritative current dataset stays up to date without manual intervention.

**Why this priority**: This is the primary UC-01 outcome and the only path that makes analytics current.

**Independent Test**: Can be fully tested by triggering the scheduled ingestion flow with valid credentials and new records, then verifying that a newly stored validated dataset becomes the current active dataset.

**Acceptance Scenarios**:

1. **Given** valid Edmonton 311 data source credentials, a healthy storage system, and an existing current dataset, **When** the scheduled ingestion job runs and the source returns valid new records, **Then** the system stores a new dataset, marks it validated, activates it as current, and logs a successful completion record.
2. **Given** the scheduled ingestion job is running with valid new records, **When** validation and storage both complete successfully, **Then** the current-dataset marker references the newly activated stored dataset version.

---

### User Story 2 - Protect Last Known Good Dataset on Failures (Priority: P2)

As an operational manager, I need failed ingestion runs to leave the previously active dataset unchanged so downstream consumers never switch to partial, invalid, or unavailable data.

**Why this priority**: Preserving the last known good dataset is the critical safety requirement across all UC-01 failure paths.

**Independent Test**: Can be fully tested by triggering ingestion under authentication failure, source timeout, validation failure, or storage failure, then verifying that no new dataset becomes current and that failure records are available for monitoring.

**Acceptance Scenarios**:

1. **Given** an existing current dataset and a failed authentication attempt, **When** the scheduled ingestion job runs, **Then** the run is marked failed, the current dataset remains unchanged, and authentication failure details are logged.
2. **Given** an existing current dataset and a source timeout, validation failure, or storage failure, **When** the scheduled ingestion job runs, **Then** the run is marked failed, no intermediate dataset is activated, the current dataset remains unchanged, and a failure notification record is available for monitoring.

---

### User Story 3 - Treat No Updates as a Successful No-Change Run (Priority: P3)

As an operational manager, I need the system to recognize when there are no new 311 records so routine runs can complete successfully without replacing the active dataset unnecessarily.

**Why this priority**: This is a defined UC-01 edge path and avoids false failures when the source has no incremental changes.

**Independent Test**: Can be fully tested by triggering ingestion when the source reports no new records and verifying the run succeeds, the active dataset remains unchanged, and the logs show a successful no-update result.

**Acceptance Scenarios**:

1. **Given** an existing current dataset and a successful source response with no new records, **When** the scheduled ingestion job runs, **Then** the run is marked successful, the current dataset remains unchanged, and the logs record that no new records were available.

### Edge Cases

- Authentication failure prevents any data request and leaves the current dataset unchanged.
- Source timeout or unavailability causes the run to fail without activating any candidate dataset.
- Retrieved data that is malformed, incomplete, or has unexpected schema changes may exist only as a candidate dataset during the run, is rejected before durable storage, and is never marked current.
- Storage failure after successful retrieval and validation prevents the candidate dataset from becoming a stored dataset version or the current dataset.
- A run with no new records is considered successful, creates no stored dataset version, and leaves the current dataset unchanged.
- The first-ever run with no last-successful-pull cursor requests the full available source dataset and establishes the first cursor only after a successful validated store.
- Failed runs must record a monitoring notification tied to the failed run and failure category in a queryable monitoring record store.
- No partial activation is allowed: the current-dataset marker can change only after validation succeeds and durable storage succeeds for the same dataset.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST trigger the UC-01 ingestion flow from a configured schedule without requiring manual operational action.
- **FR-002**: The system MUST authenticate with the City of Edmonton 311 source using configured credentials before requesting data.
- **FR-003**: The system MUST request records newer than the exclusive last-successful-pull cursor captured from the most recent successful pull; if no successful-pull cursor exists yet, the system MUST request the full available source dataset for the first run and establish the first cursor only after a successful validated store.
- **FR-004**: The system MUST validate every retrieved dataset for required structure, required fields, valid data types, and completeness before storage activation is allowed.
- **FR-005**: The system MUST create a new stored dataset version only for a run that returns new records and passes validation, and it MUST mark that version as current only after storage completes successfully.
- **FR-006**: The system MUST leave the previously active dataset unchanged whenever authentication, source access, validation, or storage fails.
- **FR-007**: The system MUST reject invalid, incomplete, malformed, or partially processed data from becoming the current dataset.
- **FR-008**: The system MUST treat a successful source response with no new records as a successful run, create no candidate dataset for activation, create no new stored dataset version, and keep the current dataset unchanged.
- **FR-009**: The system MUST record the run status for every scheduled ingestion attempt as success or failure.
- **FR-010**: The system MUST log enough run detail to distinguish success, no-new-records, authentication failure, source timeout or unavailability, validation failure, and storage failure, but those logs MUST exclude secrets, credentials, tokens, raw source payloads, and full source records; logs may include only summaries, counts, and error codes, plus at most a small redacted example describing malformed fields or invalid types without including full row contents.
- **FR-011**: The system MUST record a failure notification for monitoring on every failed ingestion run in a queryable monitoring record store, including at minimum the failed run identifier or run timestamp, failure reason category, failed status, recorded-at timestamp, and a human-readable failure summary; failure summaries MUST exclude secrets, credentials, tokens, raw source payloads, and full source records, and may include only summaries, counts, error codes, and at most a small redacted example describing malformed fields or invalid types without including full row contents.
- **FR-012**: The system MUST make the current dataset state queryable with at minimum the source identifier, current dataset version identifier, activation timestamp, activating run identifier, and record count.
- **FR-013**: The system MUST protect backend ingestion trigger and query endpoints with JWT-authenticated access. The trigger-run surface MUST be accessible only to Operational Managers; the run-status, current-dataset, and failure-notification query surfaces MUST be accessible to Operational Managers and City Planners; and no separate developer-only or backdoor trigger surface is in scope for UC-01.

### Assumptions & Dependencies

- Governing contract: [`docs/UC-01.md`](/root/311-forecast-system/docs/UC-01.md) and [`docs/UC-01-AT.md`](/root/311-forecast-system/docs/UC-01-AT.md), with acceptance tests treated as the source of truth for required behavior and edge cases.
- Required external integration: the canonical Edmonton 311 data source defined by the constitution.
- Required supporting systems: a scheduling service that can fire the ingestion run, a storage system that can persist dataset versions, and operational monitoring that can persist failure notifications.
- Detailed default assumptions that were not fixed by the UC text, including cursor semantics, dataset-state terminology, failure-notification contents, security/privacy constraints on logs and monitoring records, and UC-01 scope boundaries, are documented in [`docs/architecture/assumptions.md`](/root/311-forecast-system/docs/architecture/assumptions.md).
- UC-01 scope is limited to scheduled ingestion, validation, storage, current-dataset activation, and failure monitoring records; it does not add forecasting behavior, dashboard UI behavior, or email alert delivery.
- UC-01 does not define forecast horizon or uncertainty outputs; those behaviors are deferred to later forecasting use cases and are out of scope for this ingestion-only feature.

### Key Entities *(include if feature involves data)*

- **Ingestion Run**: A single scheduled execution attempt, including its start time, completion status, failure category when applicable, and observable log or monitoring records.
- **Candidate Dataset**: Retrieved data for the current run before durable storage; it may be validated or rejected, but it is never current.
- **Dataset Version**: A durably stored snapshot of 311 service request data produced only by a run with new records that passed validation; it may be inactive or current.
- **Current Dataset Marker**: The queryable state that identifies the active stored dataset version and returns at minimum the source identifier, current dataset version identifier, activation timestamp, activating run identifier, and record count.
- **Failure Notification Record**: A monitoring record persisted in a queryable monitoring record store for a failed run, containing at minimum the failed run identifier or run timestamp, failure reason category, failed status, recorded-at timestamp, and a human-readable failure summary.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a scheduled run with valid credentials and new records, the system completes the ingestion flow and activates a new current dataset in one run without manual intervention.
- **SC-002**: In 100% of tested failure paths defined in UC-01-AT, the previously active dataset remains the current dataset after the run ends.
- **SC-003**: In 100% of tested invalid-data and storage-failure scenarios, no partial or candidate dataset is marked current.
- **SC-004**: In 100% of tested failed runs, an operator can identify the failure reason category and run reference from logs and monitoring records.
- **SC-005**: In the no-new-records scenario, the run is reported as successful and the active dataset remains unchanged.
