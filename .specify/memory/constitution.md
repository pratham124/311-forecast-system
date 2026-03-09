<!--
Sync Impact Report:
- Version change: N/A (no local constitution) → 1.0.0
- Modified principles: N/A → I. Use-Case Traceability & Acceptance Contract; II. Canonical Edmonton Data & Time-Safe Forecasting; III. Layered Backend & Pipeline Isolation; IV. Typed Frontend Modularity & Secure Access; V. Operational Safety, Observability & Last-Known-Good Activation
- Added sections: Technology & Delivery Constraints; Development Workflow & Quality Gates
- Removed sections: None
- Templates requiring updates:
  - ✅ updated: .specify/templates/plan-template.md
  - ✅ updated: .specify/templates/spec-template.md
  - ✅ updated: .specify/templates/tasks-template.md
  - ⚠ pending: .specify/templates/commands/*.md (directory not present in this repository)
- Follow-up TODOs: None
-->
# Proactive311 Constitution

## Core Principles

### I. Use-Case Traceability & Acceptance Contract
Every product behavior MUST trace to a documented use case in `docs/UC-XX.md` and a
paired acceptance test definition in `docs/UC-XX-AT.md`. Specs, plans, tasks, and
implementation changes MUST reference the governing `UC-XX` identifiers. Behavior
changes are incomplete until the corresponding use case and acceptance test files are
updated first or in the same change. This is non-negotiable because the project uses
use cases and acceptance tests as the operational contract for forecasting,
dashboarding, and alerting behavior.

### II. Canonical Edmonton Data & Time-Safe Forecasting
The system MUST use the City of Edmonton official 311 Requests dataset from the
Socrata API at `https://data.edmonton.ca/resource/q7ua-agfg.json` as the primary
demand source, and MUST incorporate archived yearly Edmonton 311 datasets when longer
history is required. Weather enrichment MUST use Government of Canada MSC GeoMet data,
prefer Edmonton Blatchford or the best available Edmonton-area climate station, and
holiday enrichment MUST use the Nager.Date Canada API. Forecasting MUST default to
daily next-7-day demand at the service-category level, use a single global LightGBM
model with category encoded as a feature, produce predictive quantiles including P10,
P50, and P90, and use strictly chronological, leakage-free training, validation, and
evaluation splits. A simple baseline forecast MUST be retained for comparison.

### III. Layered Backend & Pipeline Isolation
The backend MUST be implemented in Python with FastAPI and PostgreSQL, and MUST keep a
layered architecture. Route handlers MUST remain thin and limited to HTTP concerns.
Business rules MUST live in service modules. Database access MUST live in repository
or data-access modules. External integrations for Edmonton 311, GeoMet weather, and
holidays MUST live in dedicated client or ingestion modules. Feature generation, model
training, forecast inference, evaluation, and alert generation MUST live in dedicated
pipeline modules and MUST NOT be embedded in API routes. Shared configuration,
logging, and utilities MUST live in core modules. This separation is required to keep
the system testable, diagnosable, and safe to evolve.

### IV. Typed Frontend Modularity & Secure Access
The frontend MUST be implemented in React with TypeScript and communicate only through
backend APIs. It MUST NOT access the database directly or depend on third-party API
response formats. Tailwind CSS is the default styling layer, and reusable UI elements
SHOULD use `shadcn/ui` when it reduces duplication without obscuring behavior. The
frontend MUST follow a modular feature-based structure with `pages`, `components`,
`features`, `api`, `hooks`, `types`, and `utils` layers. Typed domain and API shapes
MUST be defined centrally and reused consistently. Authentication MUST be enforced in
the backend with secure token-based auth, password hashing, protected routes, and at
least basic role-based access control. The frontend MUST use shared auth hooks and API
utilities for authenticated sessions and MUST NOT implement security-sensitive access
control purely on the client.

### V. Operational Safety, Observability & Last-Known-Good Activation
The system MUST never fail silently and MUST never partially activate incomplete data,
features, models, forecasts, or alerts. Ingestion, validation, feature generation,
training, inference, scheduling, and alerting failures MUST be logged with enough
detail for diagnosis. Required schemas and critical input fields MUST be validated
before activation; malformed or incomplete inputs MUST be rejected or handled
explicitly. Last-known-good datasets, features, models, forecasts, and alerts MUST
remain active when scheduled or on-demand runs fail. Forecast regeneration MUST occur
daily, retraining MUST occur on a defined schedule, alert rules MUST be configurable in
the backend, and failed scheduled runs MUST leave prior valid outputs available.

## Technology & Delivery Constraints

- Backend implementations MUST use Python, FastAPI, PostgreSQL, Pydantic schemas, type
  hints, and small testable modules that follow PEP 8.
- Frontend implementations MUST use React, TypeScript, and typed component props,
  request shapes, response shapes, and state.
- Forecast views MUST include uncertainty bands, category filtering, an alerts panel, a
  last-updated timestamp, and pipeline or data status visibility.
- Forecast features MUST prioritize service-category forecasts; citywide aggregates MAY
  be supported; ward or neighbourhood views MUST only be exposed when the source data is
  consistently reliable.
- External API contracts MUST be normalized into stable internal backend shapes before
  they reach services or frontend consumers.
- Secrets and environment-specific configuration MUST come from environment variables or
  configuration files and MUST NOT be hardcoded.

## Development Workflow & Quality Gates

- Every plan MUST pass a constitution check before implementation begins and again after
  design. The check MUST verify use-case traceability, canonical data-source usage,
  layered architecture, typed contracts, security coverage, time-safe forecasting, and
  last-known-good activation behavior.
- Every spec MUST identify the governing use cases, required data sources, external
  integrations, forecast horizon, uncertainty outputs, failure handling, and measurable
  success criteria.
- Every task list MUST include work for acceptance-test alignment, schema validation,
  observability, auth where relevant, and failure-safe activation where relevant.
- Reviews MUST reject features that place business logic in FastAPI routes, bypass typed
  schemas, leak future data into model training or evaluation, allow direct frontend
  access to storage or third-party formats, or silently replace last-known-good outputs.
- Any exception to these rules requires a documented constitution amendment before the
  change is merged.

## Governance

- This constitution supersedes conflicting local process documents for Proactive311.
- Amendments require a written rationale, the affected principles or sections, any
  migration steps, and updates to impacted templates or guidance files in the same
  change.
- Semantic versioning governs this document: MAJOR for incompatible principle changes or
  removals, MINOR for new principles or materially expanded obligations, and PATCH for
  clarifications that do not change project requirements.
- Compliance review is mandatory during specification, planning, implementation review,
  and acceptance review. Non-compliant work MUST be corrected before completion claims
  are accepted.

**Version**: 1.0.0 | **Ratified**: 2026-03-08 | **Last Amended**: 2026-03-08
