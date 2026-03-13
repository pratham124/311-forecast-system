# Research: Explore Historical 311 Demand Data

## Decision: Reuse the approved cleaned dataset lineage from UC-02 as the historical source of truth

**Rationale**: UC-02 already defines the approved cleaned dataset used for downstream operational features. Using that lineage for historical exploration keeps planner analysis aligned with validated historical demand data and avoids creating a second historical source lifecycle.

**Alternatives considered**:
- Query raw ingested data directly: rejected because it bypasses validation and deduplication guarantees.
- Persist a separate historical-analysis dataset: rejected because it duplicates lineage already covered by UC-02.

## Decision: Limit geography filtering to stored geography levels that are already available and consistently reliable

**Rationale**: UC-07 was clarified to restrict geography filtering to reliable stored geography levels. This avoids exposing unsupported filters that would create misleading zero-result interpretations or inconsistent planner experiences.

**Alternatives considered**:
- Expose every possible geography level regardless of quality: rejected because it weakens trust in analysis results.
- Restrict analysis to citywide only: rejected because the use case explicitly includes geography as a planner filter.

## Decision: Warn before executing exceptionally large historical requests

**Rationale**: UC-07 extension 3a explicitly warns the planner before a high-volume request runs. Preserving that warning step protects usability and keeps the interface honest about expensive retrievals.

**Alternatives considered**:
- Execute high-volume requests immediately: rejected because it conflicts with the use case.
- Automatically narrow large requests: rejected because it changes the planner’s intended analysis scope without consent.

## Decision: Preserve selected filter context in warning, no-data, and error states

**Rationale**: When the planner sees a warning or failure outcome, they need to know which request produced it. Keeping the selected filter context visible supports faster correction and clearer analysis behavior.

**Alternatives considered**:
- Reset filters on warning or failure: rejected because it adds friction and weakens traceability.
- Hide filter state once results fail: rejected because it obscures what request produced the outcome.

## Decision: Record analysis outcomes separately from historical dataset lineage

**Rationale**: Historical exploration requests create planner-visible operational outcomes such as success, high-volume warning acknowledged, no-data, retrieval failure, and rendering failure. Those belong in analysis-specific records rather than in dataset approval or visualization lineage entities.

**Alternatives considered**:
- Reuse dataset-version records for analysis telemetry: rejected because planner requests are not dataset lifecycle events.
- Keep outcome visibility only in logs: rejected because acceptance behavior benefits from queryable outcome history.

## Decision: Return normalized aggregated historical summaries rather than raw source rows

**Rationale**: City Planners need trend-oriented historical summaries, not raw operational rows. A normalized summary contract keeps frontend behavior stable while avoiding unnecessary source-data exposure.

**Alternatives considered**:
- Return raw records to the frontend: rejected because it expands the contract surface and exposes unnecessary detail.
- Return only one chart-specific payload: rejected because UC-07 allows charts, tables, or both and benefits from a display-agnostic response shape.
