# Research: Drill Alert Details and Context

## Decision: Reuse UC-10 and UC-11 alert records as the only drill-down entry points

**Rationale**: UC-12 begins when an operational manager selects an alert from the existing alert list. The cleanest way to preserve traceability is to resolve that selection back to the stored threshold-alert or surge-alert entity already persisted in UC-10 or UC-11, rather than creating a parallel alert identity just for drill-down.

**Alternatives considered**:
- Create a new generic alert table for UC-12: rejected because it duplicates alert identity and weakens lineage to the original alert-generation workflows.
- Allow arbitrary ad hoc detail lookup without a persisted alert record: rejected because the use case is explicitly tied to investigating an existing alert.

## Decision: Assemble alert-detail context on demand and persist only observability records

**Rationale**: The feature needs one coherent detail payload per selected alert, but it does not require a second long-lived copy of forecast distributions, driver attribution outputs, or anomaly windows. Persisting only an `AlertDetailLoadRecord` preserves observability while keeping upstream alert and analytics outputs authoritative.

**Alternatives considered**:
- Persist a full alert-detail snapshot for every load: rejected because it duplicates upstream context and complicates freshness rules.
- Rely only on unstructured logs for drill-down observability: rejected because acceptance tests require traceable retrieval, preparation, and rendering outcomes.

## Decision: Keep partial-view semantics explicit and separate from retrieval failure semantics

**Rationale**: UC-12 distinguishes between missing but reliable-to-report context and actual retrieval or preparation failure. Using explicit component-status values keeps the UI from confusing "no reliable data is available" with "the system failed while loading data."

**Alternatives considered**:
- Treat all missing component cases as global errors: rejected because the use case requires showing remaining reliable context.
- Return empty arrays with no status metadata: rejected because that would allow misleading empty visualizations.

## Decision: Limit driver attribution to the top 5 ranked contributors

**Rationale**: The accepted clarification chose the top 5 ranked contributing drivers. Enforcing that trim in the backend read model keeps the contract stable and ensures the frontend cannot accidentally render a broader, unbounded driver list.

**Alternatives considered**:
- Return every available driver and let the frontend trim: rejected because it weakens contract consistency and can leak unnecessary detail into the UI.
- Return only one primary driver: rejected because it does not satisfy the accepted clarification.

## Decision: Bound anomaly context to the previous 7 days

**Rationale**: The accepted clarification chose a 7-day anomaly window. A fixed backend window keeps retrieval deterministic, aligns with acceptance tests, and avoids inconsistent interpretation between clients.

**Alternatives considered**:
- Use a configurable or user-selected anomaly window: rejected because that adds scope not present in UC-12.
- Use only same-day anomalies: rejected because it narrows context below the accepted requirement.

## Decision: Record client render outcomes separately from backend load outcomes

**Rationale**: UC-12 must log visualization rendering failures distinctly from retrieval or preparation failures. A dedicated render-event endpoint allows the system to capture the final user-visible outcome even after the backend successfully assembled the detail payload.

**Alternatives considered**:
- Infer render success from backend response completion: rejected because client-side chart failures would be invisible.
- Push all render observability into browser logs only: rejected because backend observability needs correlated records tied to the selected alert.
