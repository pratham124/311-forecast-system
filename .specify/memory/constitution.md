<!--
Sync Impact Report:
- Version change: N/A (missing local file; restored using latest approved governance) -> 1.1.0
- Modified principles:
  - N/A -> I. Use-Case Traceability & Acceptance Coverage
  - N/A -> II. Authoritative Data Contracts & Safe Ingestion
  - N/A -> III. Time-Safe Global Forecasting & Evaluation
  - N/A -> IV. Operational Safety, Validation & Last-Known-Good Artifacts
  - N/A -> V. Layered Backend & Stable API Contracts
  - N/A -> VI. Modular Frontend & Typed Client Boundaries
  - N/A -> VII. Authentication & Authorization by Backend Authority
- Added sections:
  - Non-Negotiable Technical Standards
  - Delivery Workflow & Quality Gates
- Removed sections: None
- Templates requiring updates:
  - ✅ updated: .specify/templates/plan-template.md
  - ✅ updated: .specify/templates/spec-template.md
  - ✅ updated: .specify/templates/tasks-template.md
  - ⚠ pending: .specify/templates/commands/*.md (directory absent in repo)
- Runtime guidance reviewed:
  - ✅ reviewed: README.md
  - ℹ no updates required: existing runtime docs do not restate constitution rules
- Follow-up TODOs: None
-->
# Proactive311 Constitution

## Core Principles

### I. Use-Case Traceability & Acceptance Coverage
Every delivered capability MUST trace to one or more use cases in `docs/UC-XX.md`
and to matching acceptance tests in `docs/UC-XX-AT.md`. Specifications, plans,
tasks, pull requests, and implementation notes MUST cite the governing `UC-XX`
identifiers. Behavior changes are incomplete until the corresponding acceptance
tests are added or amended first or in the same change. Rationale: the project is
defined through use cases, so traceability is the primary control against scope
drift and ambiguous delivery.

### II. Authoritative Data Contracts & Safe Ingestion
The City of Edmonton 311 Requests Socrata dataset at
`https://data.edmonton.ca/resource/q7ua-agfg.json` is the primary demand source
and MUST remain the default production feed. When longer history is required,
archived yearly Edmonton 311 datasets MUST be incorporated without changing the
authoritative source hierarchy. External enrichment MUST use Government of Canada
MSC GeoMet weather data, preferring Edmonton Blatchford daily observations, and
Nager.Date Canada public holidays. External API contracts for Edmonton 311,
GeoMet, and Nager.Date MUST be normalized into stable internal models before the
rest of the system consumes them. All ingestion paths MUST validate schema, types,
critical fields, temporal coverage, and freshness; MUST log failures with
actionable detail; and MUST preserve the last-known-good dataset when a run fails
or yields invalid output. Rationale: forecasting quality depends on stable,
explicit source contracts and safe fallback behavior.

### III. Time-Safe Global Forecasting & Evaluation
The default forecasting task MUST predict daily Edmonton 311 demand for the next
7 days, primarily at the service-category level. Citywide aggregates MAY be
supported, and geography-level views such as ward or neighbourhood MUST only be
implemented where source data is consistently available and reliable. Forecasting
MUST use a single global LightGBM model across 311 service categories by default,
with category represented as an input feature rather than separate models unless a
constitution-compliant exception is approved. Feature pipelines MUST combine
historical 311 demand, weather features, holiday indicators, and derived temporal
features. Training, validation, evaluation, and backtesting MUST use
chronological, leakage-free splits only. Forecast outputs MUST include predictive
quantiles, at minimum P10, P50, and P90, and evaluation MUST include point
forecast metrics, quantile metrics, and comparison against a simple baseline.
Rationale: the core product promise is operationally safe forecasting with
explicit uncertainty and defensible evaluation, not point predictions optimized by
unsafe methodology.

### IV. Operational Safety, Validation & Last-Known-Good Artifacts
The system MUST never fail silently. Ingestion, validation, feature generation,
model training, forecast generation, dashboard publication, authentication,
authorization, and alerting failures MUST emit clear logs with enough context to
diagnose the fault. The platform MUST keep last-known-good datasets, feature
tables, models, forecasts, and alert outputs, and MUST NOT partially activate
incomplete or failed artifacts. Required schemas and critical input fields MUST be
validated before activation, and malformed or incomplete data MUST be rejected or
handled explicitly. Any workflow that cannot produce valid artifacts atomically
MUST leave the prior production artifact set active and mark the run failed.
Rationale: Edmonton 311 operations require continuity under data, model, and
infrastructure faults.

### V. Layered Backend & Stable API Contracts
The backend MUST be implemented in Python using FastAPI with PostgreSQL as the
system of record. The backend MUST follow a layered architecture: FastAPI route
handlers remain thin and handle only HTTP concerns; business logic lives in
service modules; database access is isolated in repository or data-access
modules; external integrations live in dedicated client or ingestion modules; and
feature generation, model training, forecast inference, and evaluation live in
separate pipeline modules, never inside API routes. Pydantic schemas MUST define
all API request and response shapes. Shared configuration, logging, and utility
code MUST live in dedicated core modules. Rationale: layered separation keeps the
system testable, maintainable, and resistant to accidental coupling between
transport, domain logic, and infrastructure concerns.

### VI. Modular Frontend & Typed Client Boundaries
The frontend MUST be implemented in React with TypeScript and communicate
exclusively through backend APIs. It MUST follow a modular, feature-based
structure with separate `pages`, `components`, `features`, `api`, `hooks`,
`types`, and `utils` layers. Top-level pages MUST compose smaller reusable
components rather than contain large amounts of logic directly. Data fetching and
backend API calls MUST be isolated in dedicated API or client modules and shared
hooks rather than embedded throughout presentational components. Reusable
TypeScript types for domain models and API request and response shapes MUST be
defined centrally and used consistently across components, hooks, and API
clients. Forecast charts, alert panels, filters, and status views MUST be
implemented as focused components with clear typed props. Rationale: maintainable
frontend code depends on separation of presentation, data access, and state
management.

### VII. Authentication & Authorization by Backend Authority
The system MUST support authentication and authorization. Authentication MUST be
implemented in the backend using secure token-based auth with password hashing and
protected API routes. Authorization MUST support at least basic role-based access
control so users can have distinct permissions. The frontend MUST handle
authenticated sessions only through backend APIs and MUST NOT implement
security-sensitive authorization logic solely on the client side. Protected routes
and authenticated API requests MUST use shared typed auth utilities and hooks.
Rationale: access control is a core system responsibility and cannot depend on
client-only enforcement.

## Non-Negotiable Technical Standards

- Forecast and dashboard interfaces MUST render uncertainty bands from backend
  quantile outputs rather than infer them client-side.
- Weather features MUST prioritize daily temperature, precipitation, snowfall,
  wind, and severe-weather indicators where available; hourly weather is optional
  and MUST be justified per feature.
- Forecasts MUST be regenerated daily, retraining MUST occur on a scheduled
  cadence, and failed scheduled runs MUST keep last-known-good outputs active.
- Alerts MUST be generated from forecast outputs using configurable threshold
  rules stored in the backend, and each alert MUST include the affected category,
  forecast date or window, severity, trigger condition, and a short explanation.
- Dashboard views MUST include forecast visualization with uncertainty bands,
  category filtering, an alerts panel, a last-updated timestamp, and basic data or
  pipeline status visibility.
- Secrets and environment-specific configuration MUST come from environment
  variables or configuration files and MUST NOT be hardcoded.
- New dependencies, alternative model families, architectural deviations, or
  geography-level forecasting expansions MUST include written justification in the
  implementation plan and pass the Constitution Check before build work begins.

## Delivery Workflow & Quality Gates

- Every implementation plan MUST confirm use-case mapping, authoritative data
  sources, normalization boundaries, layered backend ownership, modular frontend
  structure, authentication and authorization impact, time-safe evaluation design,
  and last-known-good/observability handling.
- Every feature specification MUST describe affected datasets, forecast horizons,
  uncertainty behavior, baseline comparison where relevant, failure modes,
  validation requirements, auth expectations, and acceptance scenarios for both
  success and degraded operation.
- Every task list MUST include work for schema validation, logging and monitoring,
  preservation or promotion of production artifacts, repository/client/pipeline
  separation, typed API contracts, and tests that prove chronological safety when
  forecasting logic changes.
- Reviews and acceptance checks MUST reject changes that bypass backend APIs,
  collapse layered boundaries, introduce data leakage, hide operational failures,
  hardcode secrets, or omit matching use-case and acceptance-test updates.

## Governance

- This constitution supersedes conflicting local conventions and templates.
- Amendments require a documented rationale, impacted principles or sections, and
  any migration or remediation steps needed for in-flight work.
- Versioning follows semantic versioning for governance: MAJOR for incompatible
  principle removals or redefinitions, MINOR for new principles or materially
  expanded obligations, and PATCH for clarifications that do not change required
  behavior.
- Compliance review is mandatory during planning, during review of implementation
  tasks, and before accepting a feature as complete.
- Exception requests MUST be explicit, time-bounded, and recorded in the relevant
  plan; silence does not grant an exception.

**Version**: 1.1.0 | **Ratified**: 2026-03-08 | **Last Amended**: 2026-03-08
