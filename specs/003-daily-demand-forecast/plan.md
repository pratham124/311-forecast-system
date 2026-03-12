# Implementation Plan: Generate 1-Day Demand Forecast

**Branch**: `003-daily-demand-forecast` | **Date**: 2026-03-12 | **Spec**: [spec.md](/root/311-forecast-system/specs/003-daily-demand-forecast/spec.md)
**Input**: Feature specification from `/specs/003-daily-demand-forecast/spec.md`

## Summary

Implement the UC-03 backend-only forecast workflow as a feature-specific 1-day hourly operational forecast that serves the next 24 hours by service category, with geography only when the input data supports it. This UC-03 product remains intentionally narrower than the constitution's broader default forecasting direction of daily next-7-day service-category forecasting and does not replace that broader direction. The implementation must consume the approved cleaned dataset lineage from UC-02, enrich forecasts only through dedicated Government of Canada MSC GeoMet weather modules and Nager.Date Canada holiday modules, use thin FastAPI routes with service, repository, client, and pipeline separation, retain a single global LightGBM model plus baseline comparator with `P10`, `P50`, and `P90` outputs, enforce backend JWT auth and RBAC on trigger and read surfaces, and preserve last-known-good activation so no failed, partial, denied, invalid, or otherwise incomplete request can replace the current forecast.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, APScheduler-compatible scheduling, JWT authentication support, role-based authorization dependencies, structured logging, pandas-compatible feature preparation utilities, LightGBM, dedicated Government of Canada MSC GeoMet client or ingestion modules, dedicated Nager.Date Canada API client or ingestion modules  
**Storage**: PostgreSQL for reused UC-01 and UC-02 lineage state plus forecast runs, retained forecast versions, hourly forecast buckets, current forecast marker state, and migration-managed schema history  
**Testing**: pytest with unit, integration, contract, and acceptance coverage aligned to `docs/UC-03-AT.md`  
**Target Platform**: Linux server environment running the backend API, scheduler, and forecasting pipeline  
**Project Type**: backend web service with scheduled and on-demand forecasting pipeline  
**Performance Goals**: Deliver a newly generated next-24-hour forecast within 2 minutes for at least 95% of successful on-demand requests, return an already current forecast within 30 seconds for at least 95% of reuse requests, and preserve queryable run and current-forecast state for all acceptance assertions  
**Constraints**: Keep UC-03 congruent with `docs/UC-03.md` and `docs/UC-03-AT.md`; preserve the current feature-specific 24-hour hourly forecast scope without expanding into the constitution's broader default 7-day product; keep FastAPI routes thin; keep business rules in services and pipelines; keep database access in repositories; keep Edmonton 311, MSC GeoMet, and Nager.Date integrations in dedicated clients or ingestion modules; use one global LightGBM model with category as an input feature plus a retained baseline comparator and `P10`, `P50`, `P90` outputs; ensure all training, validation, and inference inputs remain chronologically safe and leakage-free; enforce backend JWT auth and RBAC on trigger and read surfaces; never expose secrets, raw source payloads, or model internals; avoid frontend work, dashboards, manual workflows, and redesign outside UC-03; and keep the UC-03 current-forecast lifecycle distinct from the UC-02 approved cleaned dataset lifecycle  
**Scale/Scope**: One backend forecast product for the next 24 hours in 24 hourly buckets, one current forecast marker for that product, one shared orchestration path for scheduled and on-demand runs, retained run and forecast history for operational diagnosis, and acceptance coverage for the UC-03 success, reuse, failure, missing-resource, invalid-request, and access-control behaviors

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Use-case traceability**: PASS. The plan remains explicitly tied to [UC-03](/root/311-forecast-system/docs/UC-03.md) and [UC-03-AT](/root/311-forecast-system/docs/UC-03-AT.md), and it preserves their 24-hour hourly operational behavior without introducing new workflows.
- **Canonical data-source usage**: PASS. UC-03 continues to consume approved Edmonton 311 lineage from UC-02 and makes weather enrichment explicit through dedicated Government of Canada MSC GeoMet modules and holiday enrichment explicit through dedicated Nager.Date Canada API modules.
- **Layered backend architecture**: PASS. Route handlers stay thin, orchestration and business rules stay in services and pipelines, persistence stays in repositories, and all external integrations stay in dedicated client or ingestion modules.
- **Typed contracts and normalized schemas**: PASS. The plan preserves Pydantic-style backend schemas, stable API contracts for trigger/status/current-forecast surfaces, and normalized internal handling of forecast, enrichment, and activation metadata.
- **Security coverage**: PASS. Trigger and read surfaces remain backend-enforced with JWT-authenticated RBAC, with unauthorized and forbidden outcomes kept separate from forecast-run outcomes.
- **Time-safe forecasting constraints**: PASS. UC-03 keeps its narrower 1-day hourly product while explicitly not replacing the constitution's broader 7-day default direction, and it preserves one global LightGBM model, retained baseline comparator, `P10`/`P50`/`P90`, and chronologically safe leakage-free inputs.
- **Operational safety / last-known-good activation**: PASS. Failed, partial, denied, missing-resource, and invalid requests never replace the active forecast, and current-forecast activation occurs only after successful durable storage.

**Post-Design Check**: PASS. Updated research, data model, quickstart, and contract artifacts keep UC-03 backend-only, preserve the current-forecast and approved-dataset separation, make the GeoMet and Nager.Date enrichment boundaries explicit, and keep the same seven constitution gates satisfied after design.

## Project Structure

### Documentation (this feature)

```text
specs/003-daily-demand-forecast/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── forecast-api.yaml
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   └── routes/
│   ├── clients/
│   ├── core/
│   ├── pipelines/
│   │   └── forecasting/
│   ├── repositories/
│   ├── schemas/
│   └── services/
└── tests/
    ├── contract/
    ├── integration/
    └── unit/

frontend/
└── src/
    ├── api/
    ├── features/
    ├── hooks/
    ├── pages/
    ├── types/
    └── utils/
```

**Structure Decision**: Keep the constitution-mandated backend/frontend repository shape, but implement UC-03 entirely in `backend/`. The frontend structure remains a repository convention only and is not part of this feature because UC-03 planning is limited to backend forecast generation, run visibility, and current-forecast reads.

## Phase 0 Research Summary

- Confirmed UC-03 remains a feature-specific 1-day hourly operational forecast and must not be reframed as the constitution's broader default next-7-day daily category forecast.
- Confirmed forecast input lineage must start from the UC-02 approved cleaned dataset marker and must stay operationally separate from the UC-03 current forecast marker.
- Confirmed any weather enrichment used by UC-03 must come from Government of Canada MSC GeoMet through dedicated client, ingestion, or pipeline modules rather than route or repository code.
- Confirmed any holiday enrichment used by UC-03 must come from the Nager.Date Canada API through dedicated client, ingestion, or pipeline modules rather than route or repository code.
- Confirmed scheduled and on-demand requests must share one orchestration path so reuse, activation, auth, and failure behavior stay congruent.
- Confirmed the constitution-required forecasting safeguards for this feature are one global LightGBM model, a retained baseline comparator, persisted `P10`, `P50`, and `P90` outputs, and leakage-free chronological input preparation.
- Confirmed backend trigger and read surfaces must enforce JWT authentication with role-based authorization and must keep access denials, missing-resource responses, and invalid-request responses outside forecast-run outcomes.
- Confirmed last-known-good activation requires the current forecast marker to move only after full forecast persistence succeeds and requires failed, partial, denied, and invalid requests to leave the active forecast unchanged.

## Phase 1 Design Summary

- Reuse UC-01 and UC-02 lineage entities and add explicit forecast-run, forecast-version, forecast-bucket, and current-forecast-marker entities for the 1-day hourly product.
- Keep FastAPI endpoints limited to HTTP concerns while placing reuse decisions, orchestration, enrichment, feature preparation, model execution, baseline comparison, and activation guards into services and forecasting pipelines.
- Isolate Edmonton 311, MSC GeoMet, and Nager.Date integrations into dedicated client or ingestion modules and normalize their responses into stable internal schemas before pipeline use.
- Keep repository modules responsible for approved-dataset lookup, run persistence, forecast version and bucket persistence, and current-forecast marker activation.
- Persist forecast outputs with `P10`, `P50`, `P90`, baseline values, and geography-scope metadata so operational reads remain bounded while the model safeguards stay auditable.
- Preserve backend-only scope by exposing trigger, run-status, and current-forecast contracts only and excluding dashboard rendering, manual review, manual activation, and frontend redesign work.

## Implementation Steps

1. **Load active input lineage and forecast scope**
   - Resolve the currently approved cleaned dataset from the UC-02 approval marker before any forecast generation starts.
   - Keep the approved cleaned dataset marker and the UC-03 current forecast marker as separate lifecycle controls.
   - Treat UC-03 as one product: a feature-specific next-24-hour operational forecast in 24 hourly buckets by service category, with optional geography.
   - Preserve the constitution note in code and docs that this feature does not replace the broader default next-7-day daily category forecast direction.

2. **Enforce backend authentication and authorization**
   - Require JWT-authenticated backend access for the forecast trigger, run-status, and current-forecast surfaces.
   - Restrict trigger access to authorized operational roles and enforce explicit role checks on the read surfaces.
   - Reject unauthorized, forbidden, missing-resource, and invalid requests before any forecast-run state is created or changed.
   - Keep access denials and request-validation errors outside the forecast-run outcome vocabulary.

3. **Use thin routes and layered orchestration**
   - Keep FastAPI routes limited to request parsing, auth dependencies, typed response shaping, and HTTP status mapping.
   - Place orchestration in forecast services and pipelines.
   - Keep database reads and writes in repository modules.
   - Keep Edmonton 311, GeoMet, and Nager.Date integrations in dedicated client or ingestion modules.

4. **Check current-forecast reuse before generation**
   - Create a forecast run only for accepted generation attempts.
   - Determine whether an already stored current forecast fully covers the requested next 24-hour window of 24 consecutive hourly buckets.
   - Return the stored current forecast immediately when reuse is valid and record the `served_current` outcome.
   - Prevent partial-window forecasts from being treated as current for reuse.

5. **Prepare leakage-free forecast inputs and enrichments**
   - Build forecast features only from the approved cleaned dataset lineage plus dedicated weather and holiday enrichments when they are used.
   - Source weather enrichment only from Government of Canada MSC GeoMet modules using Edmonton-area station selection rules.
   - Source holiday enrichment only from the Nager.Date Canada API through dedicated modules.
   - Ensure feature preparation, enrichment joins, and evaluation windows remain strictly chronological and leakage-free.

6. **Run the constitution-aligned forecasting path**
   - Execute one global LightGBM model for the UC-03 product, with service category represented as a model feature rather than separate per-category models.
   - Generate and retain a simple baseline comparator for every forecasted bucket.
   - Materialize `P10`, `P50`, and `P90` predictive quantiles together with the operational point forecast.
   - Produce geography slices only when input completeness supports them; otherwise generate a valid category-only forecast and record that geography was omitted.

7. **Persist forecasts and activate only after safe storage**
   - Store the forecast version, all 24 hourly buckets, enrichment lineage metadata, and dimension-scope metadata durably before activation.
   - Update the current forecast marker only after storage succeeds completely.
   - Leave the prior current forecast unchanged on missing input data, enrichment failure, model execution failure, storage failure, partial persistence, denied access, missing-resource reads, and invalid requests.
   - Preserve stored forecast versions and failed forecast-run records as operational history for diagnosis and acceptance verification.

8. **Expose bounded operational read surfaces**
   - Provide a trigger surface for accepted generation attempts, a run-status surface for recorded run outcomes, and a current-forecast read surface for the active forecast product.
   - Keep responses limited to operationally necessary identifiers, timestamps, outcome states, dimension scope, bucket data, quantiles, and baseline values.
   - Never expose raw source payloads, secrets, feature matrices, or model internals in responses or logs.
   - Do not add frontend pages, dashboard rendering, manual approval, or manual correction workflows.

9. **Emit structured observability for each terminal path**
   - Log successful generation, current-forecast reuse, category-only success, missing-input failure, enrichment failure, model failure, and storage failure with correlation identifiers.
   - Keep logs sufficient for diagnosis without exposing secrets or raw third-party payloads.
   - Ensure logs and persisted run records make it clear that denied access and invalid requests are not forecast-generation failures.

10. **Acceptance-aligned verification targets**
   - Verify on-demand and scheduled generation paths create or reuse forecasts exactly as required by `docs/UC-03-AT.md`.
   - Verify JWT-authenticated RBAC behavior for trigger and read surfaces.
   - Verify last-known-good activation by asserting the current forecast marker never moves before full successful storage.
   - Verify category-only success, missing-resource behavior, invalid-request behavior, and failure retention without introducing frontend or manual workflows.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations or justified exceptions were required for this feature.
