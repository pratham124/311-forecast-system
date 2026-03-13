# Research: Generate 7-Day Demand Forecast

## Decision: Define weekly forecast currency by operational calendar week

**Rationale**: The clarification session fixed “current” as one forecast per operational week. Anchoring week boundaries at Monday 00:00 through Sunday 23:59 in local operational timezone yields deterministic reuse, scheduling, and acceptance assertions.

**Alternatives considered**:
- Rolling 7-day horizon from request time: rejected because reuse and current-pointer behavior become non-deterministic.
- Sunday-start week: rejected to preserve the chosen clarification and reduce ambiguity across planning teams.

## Decision: Use one orchestration workflow for scheduled and on-demand triggers

**Rationale**: Shared orchestration ensures identical behavior for reuse checks, failure handling, activation safety, and logging regardless of trigger source.

**Alternatives considered**:
- Separate scheduled/on-demand code paths: rejected because it increases drift and regression risk.
- On-demand only: rejected because UC-04 explicitly includes scheduled generation.

## Decision: Reuse current weekly forecast when same-week forecast already exists

**Rationale**: UC-04 extension 1a requires returning an existing current weekly forecast without rerunning the model. This reduces unnecessary processing while preserving planning continuity.

**Alternatives considered**:
- Always regenerate: rejected because it violates the defined reuse extension.
- Reuse by generation date only: rejected because generation date does not guarantee same-week coverage.

## Decision: Persist separate lifecycle entities for runs, versions, buckets, and current marker

**Rationale**: Forecast execution attempts, generated forecast datasets, bucket-level outputs, and active marker state represent different operational lifecycles and should be queryable independently for diagnostics.

**Alternatives considered**:
- Single table for all forecast state: rejected because it weakens traceability and testability.
- Ephemeral current forecast only: rejected because acceptance tests require queryable stored state.

## Decision: Keep geography segmentation conditional and publish category-only forecasts when geography is incomplete

**Rationale**: UC-04 extension 6a treats missing geography as partial segmentation, not a hard failure. This preserves usable forecasts while explicitly logging geographic limitations.

**Alternatives considered**:
- Fail run when geography is incomplete: rejected because it conflicts with required category-only success behavior.
- Force synthetic geography defaults: rejected because it can mislead operational planning.

## Decision: Enforce last-known-good activation semantics

**Rationale**: UC-04 and the constitution require that no failed or partially stored output can replace the active forecast. Marker updates must happen only after full durable storage.

**Alternatives considered**:
- Activate before storage completion: rejected due to partial activation risk.
- Clear current forecast on failure: rejected because it harms operational continuity.

## Decision: Retain run outcomes and historical forecast versions

**Rationale**: Operational diagnosis and acceptance verification require historical visibility into success, reuse, and failure paths.

**Alternatives considered**:
- Keep only current forecast: rejected because it loses auditability for failure analysis.
- Keep logs only without structured run records: rejected because acceptance tests need queryable run state.

## Decision: Keep external enrichments isolated in dedicated modules

**Rationale**: Constitution requires dedicated integration modules for external data sources and layered architecture boundaries. Isolating enrichment dependencies avoids leaking third-party contracts into routing/business layers.

**Alternatives considered**:
- Call external providers directly from route handlers: rejected because it violates layering and increases coupling.
- Embed enrichment lookups in repository queries: rejected because it mixes persistence and integration responsibilities.
