# Implementation Plan: Generate 7-Day Demand Forecast

**Branch**: `004-weekly-demand-forecast` | **Date**: 2026-03-13 | **Spec**: [spec.md](/home/asiad/ece493/311-forecast-system/specs/004-weekly-demand-forecast/spec.md)
**Input**: Feature specification from `/specs/004-weekly-demand-forecast/spec.md`

## Summary

Implement UC-04 as a backend weekly forecasting workflow that generates or reuses a current 7-day demand forecast for operational planning by service category, with geography included only when source quality supports it. The workflow must support on-demand, scheduled weekly, and automated daily regeneration triggers, use one deterministic operational week boundary (Monday 00:00 through Sunday 23:59 in local operational timezone), persist run and forecast lineage, persist `P10`/`P50`/`P90` uncertainty plus a baseline comparator for each bucket, enforce last-known-good activation, deduplicate concurrent same-week trigger attempts, and keep failure paths from replacing the active weekly forecast. The design remains aligned with [UC-04](/home/asiad/ece493/311-forecast-system/docs/UC-04.md) and [UC-04-AT](/home/asiad/ece493/311-forecast-system/docs/UC-04-AT.md).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, APScheduler-compatible scheduling, structured logging, pandas-compatible feature preparation utilities, LightGBM, dedicated Government of Canada MSC GeoMet client or ingestion modules, dedicated Nager.Date Canada API client or ingestion modules  
**Storage**: PostgreSQL for reused UC-01 and UC-02 lineage plus weekly forecast runs, weekly forecast versions, daily forecast buckets, current weekly forecast marker, and migration-managed schema history  
**Testing**: pytest with unit, integration, contract, and acceptance coverage aligned to `docs/UC-04-AT.md`  
**Target Platform**: Linux server environment running backend API, scheduler, and forecasting pipeline  
**Project Type**: backend web service with scheduled and on-demand forecasting pipeline  
**Performance Goals**: At least 95% of on-demand requests return a current weekly forecast within 2 minutes; at least 98% of scheduled weekly runs record terminal outcome within 15 minutes; 100% of failed runs preserve prior current weekly forecast; 100% of overlapping same-week trigger requests deduplicate to one active run  
**Constraints**: Must satisfy `docs/UC-04.md` and `docs/UC-04-AT.md`; keep FastAPI routes thin; keep orchestration in services/pipelines and persistence in repositories; isolate Edmonton 311, GeoMet, and Nager.Date integrations in dedicated modules; define weekly horizon as Monday 00:00 to Sunday 23:59 local operational timezone; run automated daily regeneration attempts for the active weekly forecast product; persist `P10`/`P50`/`P90` plus baseline comparator outputs; never activate partial/failed outputs; keep previous valid weekly forecast active across missing-data, engine, and storage failures; enforce trigger/read role boundaries in backend authorization  
**Scale/Scope**: One weekly forecast product covering 7 daily buckets per category and optional geography slices, one current marker per operational week, and retained historical runs/versions for diagnosis and acceptance verification

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Use-case traceability**: PASS. Plan is anchored to [UC-04](/home/asiad/ece493/311-forecast-system/docs/UC-04.md) and [UC-04-AT](/home/asiad/ece493/311-forecast-system/docs/UC-04-AT.md) and preserves their success/reuse/failure semantics.
- **Canonical data-source usage**: PASS. Weekly forecasting consumes validated Edmonton 311 lineage and keeps weather and holiday enrichment explicitly tied to GeoMet and Nager.Date modules.
- **Layered backend architecture**: PASS. Routes remain HTTP-only, orchestration lives in services/pipelines, persistence in repositories, and external calls in dedicated clients/ingestion modules.
- **Typed contracts and normalized schemas**: PASS. Plan includes typed request/response contracts and normalized internal forecast/run entities.
- **Security coverage**: PASS. Operational trigger/read surfaces remain backend-protected with authenticated and role-appropriate access.
- **Time-safe forecasting constraints**: PASS. Weekly output is next-7-day category forecast with leakage-safe chronology and explicit calendar-week boundaries.
- **Operational safety / last-known-good activation**: PASS. Activation occurs only after successful storage; any failure preserves prior active forecast.

**Post-Design Check**: PASS. Phase 1 artifacts keep UC-04 traceability, preserve layered boundaries, define typed contracts and data invariants, and retain explicit last-known-good activation rules without introducing constitution violations.

## Project Structure

### Documentation (this feature)

```text
specs/004-weekly-demand-forecast/
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

**Structure Decision**: Keep the constitution-mandated backend/frontend repository shape, but implement UC-04 entirely in `backend/` for forecast generation, run visibility, and current-weekly-forecast retrieval. Frontend structure remains a repository convention and is out of scope for this feature.

## Phase 0 Research Summary

- Confirmed UC-04 uses one operational calendar week definition: Monday 00:00 through Sunday 23:59 in local operational timezone.
- Confirmed scheduled, daily regeneration, and on-demand triggers should share one orchestration path to avoid behavior drift.
- Confirmed reuse behavior returns existing current forecast for the same operational week without invoking model execution.
- Confirmed geography is optional and category-only output remains valid when geo completeness is insufficient.
- Confirmed failure handling preserves prior current forecast across missing data, engine failure, and storage failure.
- Confirmed run and forecast history should be retained for diagnostics and acceptance auditability.
- Confirmed constitution alignment requires explicit observability and safe activation boundaries.

## Phase 1 Design Summary

- Reuse UC-01 and UC-02 lineage entities and add UC-04 entities for forecast runs, forecast versions, daily forecast buckets, and current weekly marker.
- Define weekly forecast contracts for trigger, run-status, and current-weekly retrieval with typed and bounded payloads.
- Keep weekly orchestration in forecast service/pipeline modules while repositories own persistence and activation updates.
- Persist one weekly forecast version with daily buckets by service category and optional geography scope, with `P10`/`P50`/`P90` and baseline comparator values, then activate only after full storage succeeds.
- Capture deterministic weekly boundaries, concurrent-run deduplication, and reuse rules directly in data validation and contract fields.

## Implementation Steps

1. **Resolve approved input lineage and week boundary**
   - Resolve the currently approved cleaned dataset from UC-02 before generation.
   - Derive the operational week window as Monday 00:00 through Sunday 23:59 local operational timezone.
   - Keep approved dataset marker and current forecast marker as separate lifecycle controls.

2. **Gate trigger and read surfaces by role-appropriate access**
   - Require authenticated access for weekly trigger and forecast read surfaces.
   - Enforce role checks so only authorized operations roles can trigger generation.
   - Keep access denials and malformed requests outside forecast-run outcomes.

3. **Use one orchestration path for scheduled, daily-regeneration, and on-demand runs**
   - Reuse one service entry path for all trigger types.
   - Create forecast-run records only for accepted generation attempts.
   - Keep route handlers thin and transport-only.

4. **Perform current-week reuse check before generation**
   - If a current forecast already exists for the same operational week, return it.
   - Record a `served_current` successful outcome without running model execution.
   - Ensure no replacement forecast is created during reuse.
   - If a same-week run is already in progress, deduplicate additional triggers to that active run instead of creating a second run.

5. **Prepare leakage-safe forecast inputs**
   - Build features from approved operational dataset lineage only.
   - Apply weather and holiday enrichments through dedicated modules.
   - Enforce chronological, leakage-free preparation and evaluation windows.

6. **Run weekly forecasting and segmentation**
   - Generate next-7-day demand values by service category.
   - Include geography segmentation only when data completeness is sufficient.
   - Record whether result scope is `category_and_geography` or `category_only`.
   - Produce and persist `P10`, `P50`, `P90`, and baseline comparator values for each forecast bucket.

7. **Persist and activate safely**
   - Persist forecast version and all daily buckets before activation.
   - Update current weekly forecast marker only after storage succeeds.
   - Preserve prior current forecast for missing input, engine, and storage failures.

8. **Expose bounded observability and retrieval**
   - Provide run-status retrieval for accepted run outcomes.
   - Provide current-weekly-forecast retrieval for planning consumers.
   - Log success, reuse, category-only success, and each failure class with diagnostic detail.

9. **Verify acceptance behavior**
   - Validate all UC-04 acceptance scenarios AT-01 through AT-08.
   - Validate no partial activation and deterministic week-boundary behavior.
   - Validate forecast reuse semantics and failure-safe retention semantics.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations or justified exceptions were required for this feature.
