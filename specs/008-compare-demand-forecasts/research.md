# Research: Compare Demand and Forecasts Across Categories and Geographies

## Decision: Reuse approved cleaned historical lineage from UC-02 and active forecast lineage from UC-03/UC-04

**Rationale**: UC-08 compares existing historical and forecast demand products; it does not define a new demand-ingestion or forecast-generation lifecycle. Reusing the approved cleaned dataset and the active forecast markers keeps the comparison aligned with existing lineage and avoids introducing parallel sources of truth.

**Alternatives considered**:
- Build a comparison-specific historical snapshot store: rejected because UC-02 already defines the approved historical source.
- Generate a new forecast specifically for comparison requests: rejected because UC-08 is a comparison workflow, not a forecast-generation workflow.

## Decision: Distinguish missing data from retrieval failure explicitly

**Rationale**: UC-08 extensions 4a and 5a treat unavailable matching data as forecast-only or historical-only partial-result states, while `UC-08-AT` AT-10 treats retrieval failure as an error state. Keeping those paths separate is necessary for traceable acceptance behavior and non-misleading planner output.

**Alternatives considered**:
- Treat all unavailable data as retrieval failure: rejected because it contradicts UC-08 extensions 4a and 5a.
- Treat retrieval failure as another partial-result state: rejected because `UC-08-AT` expects an error state when retrieval fails.

## Decision: Warn before running exceptionally large comparison requests

**Rationale**: UC-08 extension 3a explicitly requires a warning before high-volume comparison retrieval begins. Preserving that pre-execution checkpoint keeps planner intent explicit and avoids silent degradation.

**Alternatives considered**:
- Run high-volume requests immediately: rejected because it conflicts with the use case.
- Automatically narrow the request scope: rejected because it changes the planner’s requested comparison without consent.

## Decision: Block the full comparison on alignment failure

**Rationale**: UC-08 extension 6a and `UC-08-AT` AT-08 require an error state when historical and forecast data cannot be aligned reliably. Returning only the aligned subset would risk misleading comparisons across categories or geographies.

**Alternatives considered**:
- Show only aligned subsets: rejected because the accepted clarification requires the whole comparison to fail on alignment issues.
- Silently omit unaligned slices: rejected because it hides integrity problems from the planner.

## Decision: Keep mixed forecast availability as a clarified extension

**Rationale**: The spec clarifies that when some selected category/geography combinations have forecast data and others do not, the system should show the available comparisons and explicitly identify the missing combinations. This behavior improves planner utility, but it is not written as an explicit UC-08 alternative flow, so it must stay labeled as a clarified extension.

**Alternatives considered**:
- Remove the behavior entirely: rejected because the spec was explicitly clarified to support it.
- Treat it as part of the primary UC-08 alternative-flow set: rejected because that would overstate what `docs/UC-08.md` explicitly defines.

## Decision: Use one normalized comparison contract plus a render-outcome reporting surface

**Rationale**: The planner-facing frontend needs one stable response shape for charts, tables, warnings, partial-result states, and explicit errors. A separate render-outcome reporting call is the cleanest way to capture client rendering failures required by `UC-08-AT` without complicating the core comparison retrieval path.

**Alternatives considered**:
- Return raw historical rows and raw forecast rows separately: rejected because it exposes unnecessary source detail and weakens frontend stability.
- Encode render success or failure only in client logs: rejected because acceptance behavior requires render failures to be logged as feature outcomes.

## Decision: Record comparison requests and outcomes separately from upstream lineage

**Rationale**: Comparison execution is a planner-driven analytical workflow, not a dataset or forecast lifecycle event. Separate comparison records preserve observability for warnings, partial-result states, and failures without mutating upstream approved-dataset or current-forecast state.

**Alternatives considered**:
- Reuse forecast-run or dataset-version tables for comparison telemetry: rejected because they represent different workflows.
- Keep comparison outcomes only in logs: rejected because persisted comparison outcomes improve diagnosability and acceptance-test traceability.
