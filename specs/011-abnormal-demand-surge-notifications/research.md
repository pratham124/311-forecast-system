# Research: Abnormal Demand Surge Notifications

## Decision: Trigger surge detection only after successful UC-01 ingestion completion

**Rationale**: The accepted clarification explicitly rejects cron-only and streaming-only execution in favor of a deterministic post-ingestion trigger. Tying evaluation to `IngestionRun` completion preserves lineage to the canonical source update that introduced the new actual demand.

**Alternatives considered**:
- Schedule a periodic scan independent of ingestion completion: rejected because it weakens traceability and can re-evaluate unchanged demand unnecessarily.
- Run a separate real-time streaming detector outside UC-01: rejected because the current system already governs demand ingestion through UC-01 and the feature must remain bounded to that pipeline.

## Decision: Use residual-based anomaly detection against active LightGBM P50 forecasts

**Rationale**: UC-11 must work with the forecasting architecture already established in UC-03 and UC-04. Comparing actual demand against the active P50 forecast residual provides an explainable anomaly signal without introducing a second model family, duplicate training lifecycle, or disconnected operational baseline.

**Alternatives considered**:
- Train a dedicated anomaly-detection model: rejected because it duplicates modeling responsibility and complicates lineage, calibration, and acceptance testing.
- Detect surges from raw actual-demand thresholds only: rejected because it ignores forecast context and would over-alert on expected high-demand periods.

## Decision: Require dual-threshold confirmation before creating a surge notification

**Rationale**: The accepted clarification requires both a residual z-score threshold and a percent-above-forecast floor to pass before a surge is confirmed. This reduces false positives from statistically unusual but operationally small deviations and from large relative changes in low-volume categories.

**Alternatives considered**:
- Alert on z-score alone: rejected because it can overreact to statistically large but operationally minor changes.
- Alert on percent-above-forecast alone: rejected because it can miss unusual deviations in higher-volume scopes and removes baseline-sensitive validation.

## Decision: Persist one surge-state record per canonical scope for duplicate suppression and re-arming

**Rationale**: UC-11 sends exactly one notification when a scope enters confirmed surge state and suppresses repeats until the scope returns to normal. A persistent `SurgeState` record provides deterministic entry, suppression, and re-arm behavior across consecutive ingestion-triggered evaluations.

**Alternatives considered**:
- Deduplicate only by recent notification timestamp: rejected because time-based suppression does not prove the scope actually returned to normal.
- Deduplicate only within one evaluation run: rejected because repeated ingestion runs are the actual source of duplicate-notification risk.

## Decision: Keep surge persistence separate from UC-10 threshold-alert persistence

**Rationale**: The accepted clarification explicitly requires surge-specific tables because UC-11 events are operationally distinct from threshold alerts. Separate persistence avoids conflating detector candidates, confirmation outcomes, and state transitions with forecast-threshold exceedance records while still allowing UC-11 to reuse UC-10 delivery semantics.

**Alternatives considered**:
- Reuse UC-10 `NotificationEvent` and `ThresholdState` tables directly: rejected because surge detection has different trigger lineage, confirmation logic, and state semantics.
- Store surge outcomes only in free-form logs: rejected because acceptance tests require structured, inspectable records for candidates, confirmations, notifications, and failures.

## Decision: Expose a minimal API surface for replay and review only

**Rationale**: UC-11 is primarily an automated operational workflow. A minimal contract that supports protected replay plus surge-event retrieval keeps the feature bounded while still supporting acceptance testing, operational inspection, and typed frontend consumption where needed.

**Alternatives considered**:
- Add detector-configuration management endpoints in this feature: rejected because configuration authoring is not part of UC-11 scope.
- Keep all surge behavior internal with no retrieval contract: rejected because operators need a stable review surface for delivered, suppressed, filtered, and failed outcomes.
