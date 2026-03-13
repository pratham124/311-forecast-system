# Research: Visualize Forecast Curves with Uncertainty Bands

## Decision: Reuse persisted forecast products from UC-03 and UC-04 as visualization sources

**Rationale**: UC-03 and UC-04 already define the current forecast markers, forecast versions, and forecast buckets that UC-05 needs for chart rendering. Reusing those entities keeps visualization behavior aligned with established forecast lineage and avoids a second, conflicting forecast persistence model.

**Alternatives considered**:
- Create UC-05-specific forecast entities: rejected because it would duplicate existing forecast lifecycle state and drift from earlier contracts.
- Query raw model outputs directly: rejected because UC-03 and UC-04 already define the supported stored outputs and current-marker behavior.

## Decision: Use the approved cleaned dataset lineage from UC-02 for the historical overlay

**Rationale**: The approved cleaned dataset is the same canonical Edmonton 311 lineage used by downstream forecasting. Building the historical overlay from it keeps the chart’s context window consistent with the operational data already approved for forecast generation.

**Alternatives considered**:
- Read directly from raw ingested datasets: rejected because it bypasses UC-02 validation and deduplication guarantees.
- Persist a separate history table just for UC-05: rejected because the prior data lineage is already sufficient.

## Decision: Standardize dashboard uncertainty on `P10`, `P50`, and `P90`

**Rationale**: Those quantiles already exist in UC-03 and are now the clarified UC-05 contract. Standardizing on them keeps visualization terminology and acceptance assertions stable.

**Alternatives considered**:
- Use only `P50` and `P90`: rejected because it weakens the low-scenario view needed for planning.
- Accept arbitrary quantiles: rejected because it complicates contracts and tests.

## Decision: Use the previous 7 days as the standard historical context window

**Rationale**: Seven days provides enough recent context to interpret current demand patterns without making the view noisy, and it was explicitly clarified for UC-05.

**Alternatives considered**:
- Match the history window to the forecast horizon only: rejected because it provides too little context for interpretation.
- Use 30 days: rejected because it increases clutter and weakens operational readability.

## Decision: Persist visualization-specific load outcomes and fallback snapshots

**Rationale**: Forecast runs and forecast versions do not capture dashboard assembly, degraded rendering, or client render failures. Visualization-specific operational records are needed to satisfy UC-05 observability and fallback requirements without mutating forecast lineage.

**Alternatives considered**:
- Reuse forecast-run outcome records for visualization telemetry: rejected because render failures and dashboard degradations are not forecast-generation events.
- Keep fallback snapshots only in browser memory: rejected because UC-05 requires a reliable last-known-good visualization across failures.

## Decision: Expire fallback snapshots after 24 hours

**Rationale**: This preserves operational continuity for short-lived outages while preventing stale views from being mistaken for current information. The limit was explicitly clarified for UC-05.

**Alternatives considered**:
- Require same-cycle fallback only: rejected because it is unnecessarily strict and would remove useful short-term resilience.
- Allow unlimited fallback age with labels: rejected because it introduces stale-forecast risk.

## Decision: Normalize current daily and weekly forecasts into one visualization contract

**Rationale**: UC-05 must extend both the UC-03 and UC-04 forecast products. A single normalized API shape lets the frontend render either forecast product consistently while preserving the product-specific lineage fields underneath.

**Alternatives considered**:
- Separate visualization contracts for daily and weekly dashboards: rejected because it duplicates frontend rendering logic and weakens contract consistency.
- Support only UC-03 daily forecasts: rejected because the planning requirement explicitly calls for extending the data models from UC-04 as well.
