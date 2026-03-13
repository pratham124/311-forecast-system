# Research: Demand Threshold Alerts

## Decision: Reuse published forecast lineage as the only input to threshold evaluation

**Rationale**: UC-10 is triggered by forecast generation or refresh, and the constitution requires alerting behavior to remain downstream of the canonical Edmonton forecasting pipeline. Reusing the active forecast lineage preserves traceability and avoids introducing a second source of truth for forecast values.

**Alternatives considered**:
- Recompute alert-specific forecast values inside the alerting flow: rejected because it duplicates forecasting responsibility and breaks lineage clarity.
- Evaluate against ad hoc exported forecast files: rejected because it weakens traceability and typed-contract guarantees.

## Decision: Represent duplicate-alert suppression through persistent threshold state

**Rationale**: The accepted clarification requires a new alert only after a scope returns to or below threshold and later exceeds again. A persistent per-scope threshold state provides a deterministic re-arm rule across repeated forecast updates and makes suppression acceptance-testable.

**Alternatives considered**:
- Deduplicate by recent notification timestamp only: rejected because time-based suppression can fail to re-arm correctly when the value falls back below threshold.
- Deduplicate only within a single evaluation run: rejected because repeated forecast updates are the actual source of duplicate risk.

## Decision: Treat category-plus-geography thresholds as more specific than category-only thresholds

**Rationale**: UC-10 supports both category-level and category-plus-geography thresholds. Favoring the most specific matching threshold prevents ambiguous evaluation when both exist and keeps alert relevance aligned to the narrower operational scope.

**Alternatives considered**:
- Evaluate both thresholds for the same regional forecast slice: rejected because it can produce duplicate alerts for one operational condition.
- Always ignore category-level thresholds when geography is present anywhere in the forecast: rejected because category-level thresholds must still apply where no geography-specific rule exists.

## Decision: Model one notification event with many channel attempts

**Rationale**: The accepted clarification defines one alert whose overall delivery succeeds if at least one configured channel succeeds, while failed channels remain traceable. A parent alert event plus per-channel attempt records matches that behavior cleanly.

**Alternatives considered**:
- Create one independent alert event per channel: rejected because it blurs the business meaning of “one threshold-crossing alert.”
- Mark the whole alert as failed unless every channel succeeds: rejected because it conflicts with the accepted clarification.

## Decision: Record per-scope evaluation outcomes even when no alert is created

**Rationale**: UC-10 and UC-10-AT require operators to distinguish missing thresholds, no exceedance, suppressed duplicates, successful alert creation, and delivery failure. Per-scope outcome records preserve traceability without forcing alert creation for every evaluation result.

**Alternatives considered**:
- Log only alert-created cases: rejected because missing-threshold and no-exceedance outcomes would be hard to audit.
- Use free-form logs without structured outcome records: rejected because acceptance tests call for inspectable, traceable behavior.

## Decision: Expose a minimal API surface limited to evaluation triggering and alert retrieval

**Rationale**: UC-10 governs evaluation and notification behavior, not threshold authoring UX. A minimal contract keeps the feature bounded while still supporting scheduled execution, operational inspection, and typed frontend consumption where needed.

**Alternatives considered**:
- Add threshold-management endpoints in this feature: rejected because threshold configuration maintenance is assumed to exist elsewhere and is outside this clarified scope.
- Keep the feature entirely internal with no retrieval contract: rejected because operational traceability and acceptance testing benefit from a stable read interface.
