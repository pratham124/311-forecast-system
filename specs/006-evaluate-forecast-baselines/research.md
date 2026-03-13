# Research: Evaluate Forecasting Engine Against Baselines

## Decision: Evaluate daily and weekly forecast products separately

**Rationale**: UC-06 was clarified to keep `daily_1_day` and `weekly_7_day` as separate evaluation products. Their horizons, bucket granularities, and operational questions differ, so combining them would produce misleading comparisons and awkward storage semantics.

**Alternatives considered**:
- Evaluate only the daily product: rejected because UC-06 must support both forecast products already defined by UC-03 and UC-04.
- Combine daily and weekly into one evaluation result: rejected because the comparison scopes are not equivalent.

## Decision: Reuse approved cleaned dataset lineage from UC-02 and persisted forecast lineage from UC-03 and UC-04

**Rationale**: UC-02 already defines the approved cleaned dataset used for downstream operational work, and UC-03/UC-04 already define the persisted forecast outputs that UC-06 must judge. Reusing those entities preserves traceability and avoids introducing a second forecast storage model.

**Alternatives considered**:
- Evaluate directly against raw ingested data: rejected because it bypasses validation and deduplication guarantees from UC-02.
- Rebuild forecasts inside UC-06: rejected because UC-06 is an evaluation feature, not a forecast-generation feature.

## Decision: Give UC-06 a dedicated evaluation lifecycle with its own current-result marker

**Rationale**: Forecast runs and forecast versions answer “what forecast is active,” while UC-06 needs to answer “what evaluation result is currently official.” A separate evaluation run, result, segment, metric, and current-marker lifecycle preserves last-known-good evaluation behavior without mutating forecast lineage.

**Alternatives considered**:
- Overload forecast markers to point to evaluation results: rejected because it mixes forecast activation with evaluation governance.
- Keep only ephemeral evaluation outputs: rejected because the use case and acceptance tests require stored, reviewable results.

## Decision: Treat metric-computation failures as partial stored results when valid comparisons remain

**Rationale**: UC-06 extension 5a explicitly continues evaluation for remaining valid metrics and stores results with exclusions noted. Modeling that as a stored partial result preserves useful evidence while making limitations explicit.

**Alternatives considered**:
- Fail the whole run on any metric error: rejected because it contradicts extension 5a.
- Ignore failed metrics silently: rejected because it weakens auditability and planner trust.

## Decision: Persist explicit fair-comparison metadata for every evaluation result

**Rationale**: Acceptance test AT-08 requires proof that engine outputs, baseline outputs, and actuals refer to the same window and slice. Storing the evaluation window, forecast product, and segment coverage explicitly makes that fairness queryable and testable.

**Alternatives considered**:
- Infer comparison scope implicitly from referenced forecast artifacts: rejected because it makes acceptance verification harder and leaves room for mismatched comparisons.
- Store only aggregated metrics: rejected because it hides whether comparisons were aligned fairly.

## Decision: Use one orchestration path for scheduled and on-demand evaluation runs

**Rationale**: UC-06 supports both scheduled and planner-initiated evaluation. Using one service path keeps baseline generation, metric exclusion handling, result storage, and official-result promotion consistent across trigger types.

**Alternatives considered**:
- Separate scheduled and manual evaluation code paths: rejected because it increases behavior drift risk.
- Support only scheduled evaluation: rejected because the use case explicitly allows manual initiation.

## Decision: Publish normalized metric summaries and exclusions, not raw source rows

**Rationale**: City Planners need reviewable metric summaries, baseline coverage, and explicit exclusions. They do not need raw actual rows, feature data, or internal model artifacts, and the constitution requires operationally bounded outputs.

**Alternatives considered**:
- Return raw prediction and actual datasets in the evaluation contract: rejected because it exposes unnecessary detail and expands the contract surface.
- Return only a pass/fail label: rejected because the use case requires stored metrics and comparative review.
