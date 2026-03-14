# Research: View Forecast Accuracy and Compare Predictions to Actuals

## Decision: Reuse retained UC-06 evaluation results as the primary metric source

**Rationale**: UC-14 needs MAE, RMSE, and MAPE that match the displayed comparison scope. UC-06 already defines canonical retained evaluation lineage and metric vocabulary, so UC-14 should reuse those stored results first and only compute metrics on demand when no exact retained result exists.

**Alternatives considered**:
- Always compute metrics on demand: rejected because it duplicates existing retained evaluation behavior and weakens consistency with official evaluation lineage.
- Show only previously retained metrics and never compute on demand: rejected because the spec requires a fallback attempt before declaring metrics unavailable.

## Decision: Default the analysis window to the last 30 completed days

**Rationale**: The spec makes the default scope explicit and distinguishes completed periods from partial current-day data. Using completed days avoids misleading comparisons caused by incomplete actuals in the current day.

**Alternatives considered**:
- Use the last 30 calendar days including the current partial day: rejected because it introduces unstable actual totals.
- Require the planner to choose a window before any retrieval: rejected because the default view is a first-class requirement.

## Decision: Align only overlapping forecast and actual buckets

**Rationale**: The core trust requirement in UC-14 is that forecasts and actuals shown for a bucket represent the same interval. Restricting comparison output to matching buckets avoids off-by-one shifts and prevents fabricated alignment for partially overlapping inputs.

**Alternatives considered**:
- Pad missing buckets with zero values: rejected because it would imply observed or forecast values that do not exist.
- Shift timestamps to force a fixed bucket count: rejected because it would violate the spec's exact-interval alignment requirement.

## Decision: Persist one prepared comparison result per planner request

**Rationale**: UC-14 requires traceable retrieval, alignment, preparation, and rendering outcomes. A request-scoped prepared result provides a stable object that can be referenced by logs and render events while keeping comparison output immutable for that request.

**Alternatives considered**:
- Return the response without any request-scoped persistence: rejected because it weakens traceability for render failures and metric fallback outcomes.
- Persist only raw logs with no normalized result record: rejected because acceptance tests require stable request-level observability and reviewable prepared output semantics.

## Decision: Separate render-outcome reporting from server-side preparation

**Rationale**: The server can prepare a correct comparison payload while the client still fails to render it. A dedicated render-event report preserves this distinction and follows the same observability pattern already used in interactive visualization features.

**Alternatives considered**:
- Treat response generation as equivalent to successful rendering: rejected because chart-library or client exceptions would be invisible.
- Persist only backend preparation status and ignore client render failures: rejected because UC-14 explicitly requires render-failure logging and user-visible error handling.

## Decision: Keep UC-14 read-only with respect to forecast and evaluation lineage

**Rationale**: UC-14 is a review and comparison feature. It should consume retained forecast, actual, and evaluation data from earlier use cases rather than creating competing forecast or evaluation records.

**Alternatives considered**:
- Let UC-14 publish new official evaluation results: rejected because that responsibility already belongs to UC-06.
- Let UC-14 alter retained historical forecasts to simplify alignment: rejected because retained forecast lineage must remain immutable.
