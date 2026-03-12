# Research: UC-01 Scheduled 311 Data Pull

## Decision: Use Python 3.11 backend modules with FastAPI-compatible services and pytest-based acceptance coverage

**Rationale**: The constitution mandates Python, FastAPI, PostgreSQL, typed schemas, and layered modules. `pytest` is the most direct fit for acceptance, integration, and unit coverage in that stack and supports mocking external ingestion and storage failure paths required by UC-01-AT.

**Alternatives considered**:
- Python 3.12: viable, but not required by the constitution and unnecessary for the feature plan.
- Unspecified test framework: rejected because the plan must resolve technical context and define executable quality gates.

## Decision: Treat the Edmonton Socrata 311 endpoint as the only UC-01 source and normalize its response before validation and storage

**Rationale**: The constitution explicitly names the canonical Edmonton 311 Socrata dataset. Normalizing the upstream response into stable internal shapes preserves the layered design and prevents external API format leakage into services, repositories, or later consumers.

**Alternatives considered**:
- Pulling from archived yearly datasets during UC-01: rejected because UC-01 only requires the latest scheduled refresh and acceptance tests do not cover long-history backfill.
- Passing raw Socrata payloads through the application: rejected because it violates the constitution's stable internal contract requirement.

## Decision: Model the scheduler as a production scheduled trigger with a test harness entry point that executes the same ingestion workflow

**Rationale**: UC-01 requires unattended scheduled execution, while UC-01-AT explicitly requires a controllable trigger for tests. The lowest-risk design is one ingestion workflow callable by the scheduler in production and by a controlled trigger in testing, eliminating divergence between test and scheduled behavior.

**Alternatives considered**:
- Separate code path for manual test runs: rejected because it would weaken acceptance coverage and increase drift risk.
- Testing only the scheduler timing layer: rejected because the acceptance tests need observable end-to-end run outcomes.

## Decision: Use an exclusive last-successful-pull cursor and advance it only after a successful validated store

**Rationale**: The updated spec and assumptions require the pull window to be defined by the most recent successful validated store, not merely the most recent run. This prevents failed or no-new-records runs from skipping data and gives first-run behavior a deterministic fallback when no cursor exists.

**Alternatives considered**:
- Advancing the cursor on every completed run: rejected because it could skip records after failed runs.
- Advancing the cursor on no-new-records success: rejected because the source window is unchanged and no new dataset version was created.

## Decision: Persist candidate, stored, and current dataset states separately and switch the current dataset marker only after validation and storage succeed

**Rationale**: UC-01 and the constitution both require last-known-good safety. Explicit candidate, stored, and current dataset boundaries prevent partial activation, clarify when a new version exists versus when the run is a no-op success, and directly satisfy AT-04 through AT-07.

**Alternatives considered**:
- In-place overwrite of the current dataset: rejected because it makes rollback and safety assertions harder.
- Activating after retrieval but before full storage: rejected because it violates the no-partial-activation invariant.

## Decision: Record both structured logs and a persisted failure notification record for all failed runs

**Rationale**: UC-01-AT requires both diagnosable logs and a monitoring-visible failure record. A persisted notification entity linked to the run gives stable acceptance-test observability without depending on a specific alerting product.

**Alternatives considered**:
- Logs only: rejected because AT-08 requires a monitoring or notification record.
- External alerting integration in Phase 1: rejected because the feature only needs a queryable failure record, not a full alert-delivery system.

## Decision: Expose backend query surfaces for current dataset state and failed-run monitoring records

**Rationale**: UC-01-AT requires acceptance-visible state for the active dataset and for failure notification records. A backend query surface keeps the feature backend-only while providing stable observability for assertions.

**Alternatives considered**:
- Dashboard-only visibility: rejected because UC-01 excludes UI work.
- Log scraping as the primary assertion mechanism: rejected because current dataset state and monitoring records must be queryable.

## Decision: Use PostgreSQL-backed entities for runs, cursor state, stored dataset versions, current dataset state, and failure notifications

**Rationale**: PostgreSQL is mandated by the constitution and provides durable state for acceptance assertions around active dataset continuity, cursor advancement, run history, and failure notifications.

**Alternatives considered**:
- File-backed state: rejected because it does not match the constitution or the expected backend architecture.
- Ephemeral in-memory state: rejected because acceptance tests require post-run observability and durability.
