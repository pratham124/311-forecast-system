# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. Use it to
prove constitution compliance before implementation starts.

## Summary

[Summarize the feature, governing use cases, forecast horizon or workflow impact,
and the planned technical approach.]

## Technical Context

**Use Cases**: [UC-XX, UC-YY]
**Language/Version**: Python [version] backend, TypeScript [version] frontend
**Primary Dependencies**: FastAPI, PostgreSQL, Pydantic, React, Tailwind CSS,
[other required libraries]
**Data Sources**: Edmonton 311 Socrata API, archived yearly Edmonton 311 data
(if needed), GeoMet climate data, Nager.Date holidays
**Storage**: PostgreSQL system of record, plus versioned last-known-good
artifacts if applicable
**Testing**: [pytest, frontend test runner, contract tests, integration tests]
**Target Platform**: Web application with backend API and React frontend
**Project Type**: Full-stack forecasting and dashboard system
**Performance Goals**: [fill with feature-specific goals]
**Constraints**: Time-safe evaluation only; thin routes; typed API contracts;
no silent failure; no partial activation
**Scale/Scope**: Daily next-7-day category forecasts by default; citywide or
geographic views only where data quality supports them

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [ ] `UC-XX.md` and `UC-XX-AT.md` traceability is identified and complete.
- [ ] Edmonton 311 is the canonical demand source; any history extension uses
      archived Edmonton 311 datasets only as approved by the constitution.
- [ ] Required external integrations are isolated in client or ingestion
      modules; no third-party contract leaks past backend normalization layers.
- [ ] Backend design preserves thin FastAPI routes, service modules,
      repositories/data-access modules, dedicated pipeline modules, and core
      shared modules.
- [ ] Forecasting design uses chronological splits, prevents leakage, includes a
      baseline comparison, and emits quantiles required by the feature.
- [ ] Frontend design uses typed API clients/hooks, modular feature structure,
      and no direct database or third-party API access.
- [ ] Authentication, authorization, schema validation, logging, and
      last-known-good activation behavior are covered where relevant.
- [ ] Any constitution deviation is recorded in Complexity Tracking with explicit
      approval path.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   ├── schemas/
│   ├── services/
│   ├── repositories/
│   ├── clients/
│   ├── pipelines/
│   └── core/
└── tests/
    ├── contract/
    ├── integration/
    └── unit/

frontend/
├── src/
│   ├── pages/
│   ├── components/
│   ├── features/
│   ├── api/
│   ├── hooks/
│   ├── types/
│   └── utils/
└── tests/
```

**Structure Decision**: Default to the full-stack structure above unless the
feature is explicitly backend-only or frontend-only. Any deviation must preserve
the constitutional layering and modular boundaries.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., non-default geography view] | [current need] | [data quality or product reason] |
| [e.g., temporary dual-write] | [migration need] | [why standard activation flow is insufficient] |
