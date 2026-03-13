# Implementation Plan: Evaluate Forecasting Engine Against Baselines

**Branch**: `006-evaluate-forecast-baselines` | **Date**: 2026-03-13 | **Spec**: [spec.md](/home/asiad/ece493/311-forecast-system/specs/006-evaluate-forecast-baselines/spec.md)
**Input**: Feature specification from `/specs/006-evaluate-forecast-baselines/spec.md`

## Summary

Implement UC-06 as a backend evaluation workflow that compares persisted forecasting-engine outputs against configured baseline methods for both supported forecast products, while keeping daily and weekly evaluations separate. The workflow must reuse approved cleaned-data lineage from UC-02 and current forecast products from UC-03 and UC-04, calculate and store comparable metric summaries across overall, category, and time-period segments, preserve partial-metric results when only some metrics are invalid, and maintain one last-known-good official evaluation per forecast product when a new run fails.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: FastAPI, Pydantic-style typed schemas, SQLAlchemy-compatible PostgreSQL access layer, APScheduler-compatible scheduling, structured logging, pandas-compatible evaluation utilities, LightGBM-produced forecast lineage from UC-03 and UC-04, and dedicated baseline-evaluation service modules  
**Storage**: PostgreSQL for reused UC-01 through UC-04 lineage plus evaluation runs, retained evaluation results, segmented metric records, current evaluation markers, and migration-managed schema history  
**Testing**: pytest with unit, integration, contract, and acceptance coverage aligned to `docs/UC-06-AT.md`  
**Target Platform**: Linux server environment running backend API, scheduler, and evaluation pipeline  
**Project Type**: backend web service with scheduled and on-demand evaluation pipeline  
**Performance Goals**: At least 95% of scheduled or planner-initiated evaluation runs with all required inputs available publish reviewable results within 30 minutes; 100% of failed runs preserve the prior official evaluation; 100% of partial-metric runs store valid remaining results with exclusions identified  
**Constraints**: Must satisfy `docs/UC-06.md` and `docs/UC-06-AT.md`; must evaluate `daily_1_day` and `weekly_7_day` forecast products separately; must compare engine outputs, baseline outputs, and actuals over the same evaluation scope; must keep FastAPI routes thin, evaluation orchestration in services/pipelines, and persistence in repositories; must never replace the official evaluation with incomplete or failed output; must preserve exclusion details for invalid metrics; must keep published results limited to operationally necessary summaries and metric outputs rather than raw source rows  
**Scale/Scope**: One evaluation workflow supporting scheduled and on-demand triggers, two forecast products evaluated independently, retained history of evaluation runs and stored results, segmented metrics across service categories and time periods, and one official current evaluation marker per forecast product

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Use-case traceability**: PASS. The plan is anchored to [UC-06](/home/asiad/ece493/311-forecast-system/docs/UC-06.md) and [UC-06-AT](/home/asiad/ece493/311-forecast-system/docs/UC-06-AT.md), and the evaluation workflow remains bounded to the behavior defined there.
- **Canonical data-source usage**: PASS. UC-06 reuses the approved Edmonton 311 cleaned-data lineage from UC-02 and the persisted forecast products already defined by UC-03 and UC-04 rather than introducing alternate source paths.
- **Layered backend architecture**: PASS. Route handlers remain limited to trigger/read concerns, evaluation orchestration lives in dedicated services or pipelines, and persistence lives in repository modules.
- **Typed contracts and normalized schemas**: PASS. The plan defines typed evaluation-trigger, run-status, and current-result contracts with normalized metric and segment payloads.
- **Security coverage**: PASS. Trigger and read surfaces remain backend-protected and role-aware for the City Planner or equivalent authorized analytics roles.
- **Time-safe forecasting and evaluation**: PASS. Comparisons are explicitly constrained to the same evaluation window and slice across engine outputs, baseline outputs, and actual outcomes, preventing mismatched or leaky comparisons.
- **Operational safety / last-known-good activation**: PASS. Failed runs never replace the current official evaluation, and partial metric failures store only valid results with clear exclusions.

**Post-Design Check**: PASS. The research, data model, quickstart, and contract artifacts preserve UC-06 traceability, reuse canonical upstream lineage, maintain layered backend boundaries, and retain fair-comparison plus last-known-good guarantees after design.

## Project Structure

### Documentation (this feature)

```text
specs/006-evaluate-forecast-baselines/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── evaluation-api.yaml
└── tasks.md
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   └── routes/
│   ├── core/
│   ├── pipelines/
│   │   └── evaluation/
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

**Structure Decision**: Keep the constitution-mandated backend/frontend repository shape, but implement UC-06 entirely in `backend/` for evaluation triggering, run visibility, result retrieval, and persistence. Frontend structure remains a repository convention and is out of scope for this feature.

## Phase 0 Research Summary

- Confirmed UC-06 must treat `daily_1_day` and `weekly_7_day` as separate evaluation products rather than combining them into one shared result set.
- Confirmed the evaluation workflow should reuse approved cleaned dataset lineage from UC-02 and persisted forecast outputs from UC-03 and UC-04 instead of rebuilding forecast artifacts.
- Confirmed metric-computation failures should produce a stored partial result when the remaining valid metrics and segments are still comparable.
- Confirmed the system needs explicit fair-comparison metadata so engine outputs, baseline outputs, and actuals are provably aligned to the same window and category slice.
- Confirmed UC-06 needs its own evaluation lifecycle entities and current-result marker rather than overloading forecast markers or forecast versions.
- Confirmed scheduled and on-demand evaluation triggers should share one orchestration path so comparison logic, failure handling, and official-result activation stay consistent.
- Confirmed published evaluation outputs should expose only normalized metric summaries, segment coverage, exclusions, and lineage identifiers needed for operational review and acceptance tests.

## Phase 1 Design Summary

- Reuse UC-01 through UC-04 lineage entities as immutable upstream inputs, and add only UC-06-specific entities for evaluation runs, stored evaluation results, segmented comparisons, metric values, and current evaluation markers.
- Keep one evaluation run scoped to one forecast product at a time, with explicit references to either the UC-03 current daily forecast lineage or the UC-04 current weekly forecast lineage.
- Store complete and partial evaluation outcomes separately from run history so the latest official result can be promoted only after storage succeeds.
- Represent overall, service-category, and time-period summaries through evaluation segments with per-method metric records, making exclusions explicit when a metric is invalid.
- Expose typed backend contracts for on-demand trigger, run-status retrieval, and current-evaluation retrieval, with fair-comparison metadata and baseline-method coverage included in the response.

## Implementation Steps

1. **Resolve approved lineage and forecast product scope**
   - Read the approved cleaned dataset marker from UC-02 as the authoritative actuals lineage for evaluation.
   - Read the current forecast marker from UC-03 for `daily_1_day` evaluations and the current weekly forecast marker from UC-04 for `weekly_7_day` evaluations.
   - Reject any attempt to merge daily and weekly results into one evaluation run.

2. **Gate trigger and read surfaces through backend authorization**
   - Require authenticated access for manual evaluation triggers and evaluation-result retrieval.
   - Keep access denials and malformed requests outside evaluation-run outcomes.
   - Limit publishable result detail to operational summaries and metric outputs.

3. **Use one orchestration path for scheduled and on-demand runs**
   - Reuse one evaluation service or pipeline for manual and scheduled triggers.
   - Create evaluation-run records only for accepted attempts.
   - Keep routes transport-only and move all business decisions into services.

4. **Build fair-comparison evaluation inputs**
   - Resolve actuals, engine forecasts, and baseline forecasts for the same evaluation window and product scope.
   - Normalize service-category and time-period slices before metric calculation.
   - Reject or fail runs where comparison scope cannot be aligned fairly.

5. **Run baseline generation and metric calculation**
   - Generate configured baseline outputs for the selected forecast product and evaluation window.
   - Compute MAE, RMSE, and MAPE for the forecasting engine and each included baseline method.
   - Continue with valid remaining metrics when only a subset fails, and record exclusions explicitly.

6. **Persist segmented evaluation results**
   - Store one evaluation result per successful or partial-success run.
   - Store overall, category, and time-period segment summaries under that result.
   - Store per-method metric values and exclusion reasons without overwriting upstream forecast lineage.

7. **Promote official results safely**
   - Update the current evaluation marker only after the new result is fully stored.
   - Keep one official current evaluation per forecast product.
   - Preserve the prior official result on missing-data, missing-forecast, baseline-failure, and storage-failure paths.

8. **Expose bounded observability and retrieval**
   - Provide run-status retrieval for accepted evaluation runs.
   - Provide current-evaluation retrieval for planner review by forecast product.
   - Log success, partial-success, and each failure class with enough context for diagnosis.

9. **Verify acceptance behavior**
   - Validate on-demand and scheduled success flows.
   - Validate missing-data, missing-forecast, baseline-failure, and storage-failure retention behavior.
   - Validate partial metric exclusion behavior and fair-comparison metadata alignment.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No constitution violations or justified exceptions were required for this feature.
