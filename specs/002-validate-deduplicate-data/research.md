# Research: Validate and Deduplicate Ingested Data

## Decision: Extend the UC-01 dataset lifecycle instead of creating a separate approval domain

**Rationale**: UC-02 begins only after ingestion has already created candidate or stored dataset artifacts in UC-01. Reusing the same lineage for `IngestionRun`, ingested `DatasetVersion`, and the approved dataset marker avoids contradictory notions of "current" data and keeps the last-known-good activation rule consistent across features.

**Alternatives considered**:
- Create a separate UC-02-only active dataset model: rejected because it would duplicate activation state and make cross-feature acceptance checks ambiguous.
- Treat UC-02 as an in-memory post-processing step with no persistent linkage to UC-01: rejected because acceptance tests require durable status and approval evidence.

## Decision: Point the approval marker to the cleaned dataset version after full UC-02 success

**Rationale**: The current spec now makes explicit that approval follows validation, deduplication, and storage of the cleaned dataset. The active marker therefore needs to reference the cleaned dataset version produced by UC-02, not only the ingested source dataset from UC-01.

**Alternatives considered**:
- Keep the approval marker on the ingested UC-01 dataset version: rejected because it would hide the cleaned output actually approved for downstream use.
- Maintain separate active markers for ingested and cleaned datasets: rejected because it would add state complexity without feature value.

## Decision: Use a percentage-based duplicate threshold

**Rationale**: The spec clarification fixed excessive duplication as a percentage of total records. That makes review-needed behavior scale predictably across small and large datasets and avoids arbitrary bias from raw record counts.

**Alternatives considered**:
- Fixed duplicate-count threshold: rejected because the same count can be negligible in a large ingest and severe in a small one.
- Combined count and percentage thresholds: rejected because the current spec does not require the extra policy complexity.

## Decision: Represent duplicate resolution as one cleaned record per duplicate group

**Rationale**: The accepted clarification requires deterministic output for each duplicate group, including consolidation of non-conflicting values. Modeling the resolution this way supports acceptance checks and downstream dataset stability.

**Alternatives considered**:
- Keep one original record with no consolidation: rejected because it does not capture the clarified policy.
- Discard every duplicate group entirely: rejected because it would reduce usable data beyond the approved feature scope.

## Decision: Treat review-needed as a terminal blocked outcome in UC-02

**Rationale**: The clarification established that manual review only blocks approval in this feature. Recording a review-needed state without manual action endpoints keeps the feature bounded and prevents plan drift into operational tooling not required by UC-02.

**Alternatives considered**:
- Add manual approval endpoints now: rejected because the spec explicitly excludes them.
- Add reprocessing controls now: rejected because they are separate workflow concerns.

## Decision: Treat schema-validation failure as `rejected` and reserve `failed` for processing or storage breakdowns

**Rationale**: The synchronized spec now defines clear decision boundaries: schema-invalid datasets are rejected, while failed outcomes are reserved for processing that cannot complete after work has begun. This keeps acceptance expectations and operator-facing statuses consistent.

**Alternatives considered**:
- Classify schema validation failure as `failed`: rejected because it conflicts with the current spec wording and muddies outcome meaning.
- Collapse rejected and failed into one error state: rejected because the feature now requires clearer operational distinction.

## Decision: Persist validation outcomes separately from ingestion outcomes

**Rationale**: UC-01 records ingestion success and failure, while UC-02 needs finer-grained schema, duplicate, review-needed, and approval signals. A dedicated validation-run model can capture those stages while still referencing the original ingestion lineage.

**Alternatives considered**:
- Overload the UC-01 ingestion run with all validation states: rejected because it would mix distinct responsibilities and make acceptance assertions harder to express.
- Store only final approval status: rejected because UC-02 acceptance coverage needs stage-specific failure behavior.

## Decision: Preserve the existing Operational Manager and City Planner query model

**Rationale**: UC-01 already established authenticated operational read surfaces for dataset state. Reusing that model keeps the backend access pattern consistent and avoids unnecessary role redesign for a related pipeline stage.

**Alternatives considered**:
- Introduce a new reviewer role in UC-02: rejected because no manual review actions exist in scope.
- Leave validation state accessible only through logs: rejected because the spec requires operational users to determine approval and processing outcomes.

## Decision: Document explicit status normalization and API/query error coverage

**Rationale**: The spec uses requirements-level prose statuses including `review-needed`, while contracts and storage may use normalized enum values such as `review_needed`. Making that normalization explicit keeps planning artifacts consistent. Likewise, operational status surfaces now require explicit unauthorized or forbidden, missing-resource, and invalid-query behavior to avoid under-specified API expectations.

**Alternatives considered**:
- Leave normalization implicit: rejected because it invites drift between spec prose and backend contracts.
- Omit error-surface requirements from the planning artifacts: rejected because the spec now explicitly requires them.

## Decision: Fail safe when outcome details cannot be stored or exposed reliably

**Rationale**: The spec now requires degraded-state safety: if reliable outcome persistence or exposure is unavailable, the candidate dataset cannot become approved and the previous approved cleaned dataset must remain active. This preserves the constitution's last-known-good rule.

**Alternatives considered**:
- Approve the cleaned dataset as long as storage succeeded even if status exposure failed: rejected because operators would have uncertain activation state.
- Leave degraded-state behavior undefined: rejected because it creates acceptance ambiguity and operational risk.
