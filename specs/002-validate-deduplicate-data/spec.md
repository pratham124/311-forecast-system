# Feature Specification: Validate and Deduplicate Ingested Data

**Feature Branch**: `002-validate-deduplicate-data`  
**Created**: 2026-03-12  
**Status**: Draft  
**Input**: User description: "docs/UC-02.md docs/UC-02-AT.md"

## Clarifications

### Session 2026-03-12

- Q: What does "flagged for review" include within this feature's scope? → A: Manual review only blocks the dataset; approval or reprocessing happens outside this feature.
- Q: How is the excessive duplicate threshold measured? → A: Use a percentage of total records.
- Q: What should duplicate resolution produce in the cleaned dataset? → A: Produce one cleaned record per duplicate group, allowing consolidation of non-conflicting values.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Approve a clean dataset (Priority: P1)

As a city planner, I want newly ingested datasets to be checked for structural correctness and duplicate records before approval so that forecasting and dashboards use reliable data.

**Why this priority**: This is the core value of the feature. Without it, downstream planning outputs can be based on corrupt or duplicated data.

**Independent Test**: Submit a dataset that matches the expected structure and contains duplicates that can be resolved by policy, then confirm the cleaned dataset becomes the approved version for downstream use.

**Acceptance Scenarios**:

1. **Given** a previously approved dataset exists and a newly ingested dataset matches required fields and formats, **When** the dataset is processed, **Then** the system validates it successfully, applies duplicate-handling rules, stores the cleaned dataset, and marks it approved for downstream use.
2. **Given** a newly ingested dataset contains duplicate records that can be resolved according to policy, **When** processing completes successfully, **Then** the approved dataset contains one cleaned record for each duplicate set, including any allowed consolidation of non-conflicting values, and records the dataset as clean.

---

### User Story 2 - Reject invalid datasets safely (Priority: P2)

As a city planner, I want invalid datasets to be rejected before approval so that dashboards and forecasts never switch to untrusted data.

**Why this priority**: Protecting data integrity is the next most important outcome after approving valid data. Failure handling must be safe even when fresh data cannot be accepted.

**Independent Test**: Submit a dataset with missing required information or malformed values and confirm it is rejected, the failure reason is available for review, and the previous approved dataset remains active.

**Acceptance Scenarios**:

1. **Given** a newly ingested dataset is missing required information or contains invalid formats, **When** validation runs, **Then** the system rejects the dataset, records the validation issues, and does not make the dataset available downstream.
2. **Given** a dataset fails validation, **When** the failure is finalized, **Then** the previously approved dataset remains the active version for forecasting and dashboards.

---

### User Story 3 - Hold suspicious or failed runs for review (Priority: P3)

As a city planner, I want datasets with unresolved processing problems or suspicious duplicate patterns to be blocked from approval and flagged for follow-up so that unusual upstream issues can be investigated without disrupting current reporting.

**Why this priority**: This covers important exception handling, but it builds on the primary capability of approving valid datasets and rejecting clearly invalid ones.

**Independent Test**: Submit one dataset that triggers a processing failure and another that exceeds the acceptable duplicate rate, then confirm both are blocked from approval and the last approved dataset stays active.

**Acceptance Scenarios**:

1. **Given** a dataset passes structural checks but processing cannot complete, **When** the failure occurs during duplicate handling or storage, **Then** the system marks the run as failed, blocks approval, and keeps the previous approved dataset active.
2. **Given** a dataset has an unusually high share of duplicate records, **When** duplicate analysis completes, **Then** the system records a `review-needed` outcome, prevents approval, and leaves the current approved dataset unchanged.

### Edge Cases

- A dataset contains no duplicates but otherwise passes all validation checks.
- A dataset contains duplicate groups that require consolidation of non-conflicting values into a single cleaned record.
- A dataset fails validation after an approved dataset is already active; the active dataset must remain unchanged.
- A dataset passes validation and duplicate analysis but cannot be saved successfully; it must not become active.
- A dataset exceeds the acceptable duplicate-rate threshold even though duplicates are technically resolvable.
- A dataset with a large record count and a modest raw duplicate count must not be flagged unless the duplicate percentage exceeds the accepted threshold.
- A dataset reaches a `review-needed` outcome; the feature must stop at blocking approval and recording the outcome rather than allowing manual approval or reprocessing within this workflow.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST evaluate every newly ingested dataset produced by the UC-01 dataset lifecycle before it can be approved for forecasting or dashboard use.
- **FR-002**: The system MUST validate each newly ingested dataset against externally configured rules for required fields, data types, field formats, and structural completeness before approval is allowed.
- **FR-003**: The system MUST reject any dataset that fails validation and MUST prevent it from moving to approval.
- **FR-004**: The system MUST analyze each valid dataset for duplicate records using the defined duplicate-identification rules.
- **FR-005**: The system MUST resolve detected duplicates according to the active duplicate-handling policy by producing one cleaned record per duplicate group before a dataset can be marked clean.
- **FR-005a**: When duplicate records contain non-conflicting values, meaning values that can coexist in the cleaned record without contradicting each other for the same field, the system MUST allow those values to be consolidated into the single cleaned record produced for that duplicate group.
- **FR-006**: The system MUST use the following outcome statuses with these decision boundaries: `approved` only when validation, duplicate handling, and storage all succeed; `rejected` when schema validation fails; `failed` when processing or storage cannot complete after processing starts; and `review-needed` when duplicate analysis completes but the duplicate percentage exceeds the accepted threshold.
- **FR-007**: The system MUST mark a dataset as approved only after validation, duplicate handling, and storage completion all succeed.
- **FR-008**: The system MUST store the approved cleaned dataset as a distinct cleaned dataset version available for downstream forecasting and dashboards, and the approval marker MUST point to that cleaned dataset version after successful approval.
- **FR-009**: The system MUST keep the previously approved dataset active whenever a new dataset is rejected, reaches a `review-needed` outcome, or fails during processing or storage.
- **FR-010**: The system MUST record the outcome of each processing run, including success, `approved`, `rejected`, `failed`, or `review-needed` status, together with the reason for that outcome.
- **FR-011**: The system MUST flag a dataset for review and block approval when the percentage of duplicate records in the dataset exceeds the accepted threshold for normal processing.
- **FR-012**: The system MUST prevent partially processed datasets from becoming available to downstream consumers at any point before approval is complete.
- **FR-013**: Authorized operational users MUST be able to determine which cleaned dataset version is currently approved, the outcome of a newly processed candidate dataset, and whether candidate data is still in progress, blocked, or has become the approved active dataset.
- **FR-014**: The system MUST expose approval and review status details only to authorized users and MUST limit exposed information to operationally necessary identifiers, statuses, counts, timestamps, and summary reasons rather than raw source payloads or full source records.
- **FR-015**: Operational status surfaces MUST define responses for unauthorized or forbidden access, missing resources, and invalid query parameters.
- **FR-016**: If processing outcome details cannot be stored or exposed reliably, the system MUST treat the candidate dataset as not approved, preserve the previously approved dataset as active, and avoid presenting uncertain status details as approved state.
- **FR-017**: When a dataset is flagged for review, meaning it has reached the canonical `review-needed` outcome, this feature MUST limit its behavior to recording that outcome and blocking approval; any later approval or reprocessing workflow is out of scope.

### Assumptions

- UC-02 extends the UC-01 dataset lifecycle by evaluating newly ingested datasets and deciding whether a cleaned dataset version replaces the previously approved active dataset.
- A single approved cleaned dataset version is treated as the active source for forecasting and dashboards at any given time.
- Duplicate-identification rules, duplicate-handling policy, and the accepted duplicate-rate threshold are defined outside this feature and are available when processing runs.
- The accepted duplicate-rate threshold is expressed as a percentage of total records and is defined outside this feature.
- Failure details are retained long enough for operational review and audit of the dataset approval decision.
- Operational users who review outcomes already have appropriate permission to inspect dataset processing status.
- Any manual investigation or follow-up action on a flagged dataset is handled by a separate workflow outside this feature.

### Key Entities *(include if feature involves data)*

- **Ingested Dataset**: A newly received collection of records awaiting validation, duplicate analysis, and an approval decision.
- **Validation Run**: The processing record for one UC-02 evaluation attempt, including whether the candidate dataset is in progress, approved, rejected, failed, or review-needed.
- **Cleaned Dataset Version**: The stored snapshot created only after validation and duplicate handling succeed and that becomes the approved active dataset when storage completes successfully.
- **Validation Result**: The recorded outcome of required-field, data-type, format, and structural-completeness checks, including any rule violations that blocked approval.
- **Duplicate Review Status**: The outcome of duplicate analysis, including whether duplicate groups were consolidated into cleaned records normally, the dataset was rejected for validation failure, the run failed during processing or storage, or the dataset was held for review because the duplicate percentage exceeded the accepted threshold.
- **Approval Marker**: The business designation that identifies which cleaned dataset version is currently active for downstream forecasting and dashboards.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of newly ingested datasets receive an explicit outcome of `approved`, `rejected`, `failed`, or `review-needed` before downstream consumers can use them.
- **SC-002**: 100% of datasets that fail validation, exceed the accepted duplicate threshold, or encounter processing/storage failure remain unavailable to forecasting and dashboards.
- **SC-003**: For datasets that satisfy validation and duplicate-handling rules, an approved dataset version is available for downstream use within 15 minutes of ingestion completion.
- **SC-004**: Authorized operational users can identify the currently approved cleaned dataset version, the latest outcome of a newly ingested candidate dataset, and whether that candidate is active, in progress, or blocked within 2 minutes of checking the defined operational status surfaces.
- **SC-005**: In acceptance testing, 100% of failure-path scenarios preserve the previously approved dataset as the active downstream source.
