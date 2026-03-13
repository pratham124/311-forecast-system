# Quickstart: Generate 7-Day Demand Forecast

## Purpose

Use this guide to implement and verify UC-04 backend forecasting behavior so operational users can receive a current weekly forecast by service category, with geography when available, while preserving last-known-good safety.

## Implementation Outline

1. Reuse upstream approved dataset lineage from UC-01 and UC-02.
2. Implement weekly forecast orchestration in backend service/pipeline modules with thin route handlers.
3. Support both scheduled and on-demand triggers through one orchestration path.
4. Apply deterministic operational week boundaries:
   - week starts Monday 00:00 local operational timezone
   - week ends Sunday 23:59 local operational timezone
5. Before model execution, check for an existing current forecast for the same operational week:
   - if found, return existing forecast and record `served_current`
   - if not found, continue generation
6. Generate and persist a 7-day forecast segmented by service category.
7. Include geography segmentation only when source geography completeness supports it.
8. Persist run outcomes and forecast entities:
   - `WeeklyForecastRun`
   - `WeeklyForecastVersion`
   - `WeeklyForecastBucket`
   - `CurrentWeeklyForecastMarker`
9. Update current marker only after successful full storage.
10. On missing input data, forecasting engine error, or storage failure:
    - mark run failed
    - retain prior current forecast
11. Expose and test contracts for:
    - weekly trigger endpoint
    - run-status endpoint
    - current-weekly-forecast endpoint

## Acceptance Alignment

Map implementation and tests directly to [UC-04-AT](/home/asiad/ece493/311-forecast-system/docs/UC-04-AT.md):

- `AT-01`: On-demand request generates and activates new weekly forecast
- `AT-02`: Scheduled run generates and activates new weekly forecast
- `AT-03`: Existing current weekly forecast is served without rerun
- `AT-04`: Missing required data fails run and preserves prior current forecast
- `AT-05`: Forecast engine failure preserves prior current forecast
- `AT-06`: Incomplete geography produces valid category-only forecast
- `AT-07`: Storage failure blocks activation and preserves prior forecast
- `AT-08`: No partial activation before successful storage

## Suggested Test Layers

- Unit tests for week-boundary calculation, reuse decision logic, and failure-safe activation guards
- Integration tests across trigger path, dataset lookup, forecasting service/pipeline, persistence, and current marker updates
- Contract tests for [forecast-api.yaml](/home/asiad/ece493/311-forecast-system/specs/004-weekly-demand-forecast/contracts/forecast-api.yaml)
- Acceptance tests mirroring UC-04-AT scenarios

## Exit Conditions

Implementation is ready for task breakdown when:

- Weekly operational boundary logic is deterministic and validated
- Reuse vs generate behavior is testable and auditable
- Category-only fallback path for incomplete geography is implemented and logged
- Current weekly marker updates only after successful storage
- Failure paths preserve prior current forecast in all required scenarios
- Run outcomes and historical forecast versions are queryable
