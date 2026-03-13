# Feature Specification: Abnormal Demand Surge Notifications

**Feature Branch**: `011-abnormal-demand-surge-notifications`  
**Created**: 2026-03-13  
**Status**: Draft  
**Input**: User description: "docs/UC-11.md, docs/UC-11-AT.md"

## Clarifications

### Session 2026-03-13

- Q: Which surge detection approach should storm mode use, given that LightGBM is already the system's core model? → A: Compare incoming actual demand from UC-01 ingestion against the active LightGBM P50 forecast residual and use a statistical residual-based anomaly signal, specifically a z-score over a rolling residual baseline, rather than a separate ML model.
- Q: Should surge persistence reuse UC-10 threshold-alert storage or have dedicated records? → A: Use separate surge-specific tables because surge events are operationally distinct from threshold alerts.
- Q: When should surge detection run? → A: Trigger surge detection after each successful UC-01 ingestion run completes; do not use a cron-based schedule or a real-time streaming trigger.
- Q: Is the residual z-score threshold alone enough to confirm a surge? → A: No. Confirmation requires a dual check: the residual z-score must exceed the configured z-score threshold and the absolute residual percent-above-forecast must exceed a configurable floor, such as actual demand being greater than 120% of P50.
- Q: How should confirmation behave when the active P50 forecast for a scope is exactly zero? → A: Treat any positive actual demand over a zero forecast as satisfying the percent-above-forecast confirmation floor, while zero actual demand over a zero forecast does not satisfy it. The numeric percent-above-forecast value may be left null in stored records and payloads when the denominator is zero.
- Q: What scope should surge detection evaluate? → A: Evaluate surges per service category, optionally narrowed by geography, matching the canonical scope used in UC-03, UC-04, and UC-10. Citywide aggregates may be computed but are not the primary detection scope.
- Q: How should repeated surges for the same scope behave? → A: Send one notification when a scope first enters confirmed surge state, suppress additional notifications while that same scope remains above both confirmation thresholds, and re-arm only after the scope returns to normal. Do not send periodic reminder notifications.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Receive a confirmed surge alert (Priority: P1)

As an operational manager, I want the system to notify me when abnormal demand is confirmed so that I can respond quickly to a real surge even when it was not fully forecasted.

**Why this priority**: This is the primary business outcome of the feature. Without confirmed surge notifications, the feature provides no operational response value.

**Independent Test**: Can be fully tested by completing a successful UC-01 ingestion run for a service category and optional geography whose newly ingested actual demand produces a residual against the active LightGBM P50 forecast with both a z-score above the configured rolling-baseline threshold and an absolute percent-above-forecast above the configured floor, and verifying that exactly one notification event for that scope is created, sent, and logged while the scope remains in surge state.

**Acceptance Scenarios**:

1. **Given** a successful UC-01 ingestion run completes for a service category and optional geography and the newly ingested actual demand produces a residual against the active LightGBM P50 forecast whose z-score exceeds the configured rolling-baseline threshold and whose absolute percent-above-forecast exceeds the configured floor, **When** the surge detector confirms the anomaly as an abnormal demand surge, **Then** the system creates a surge notification event containing the affected category, optional geography, surge magnitude, and detection or confirmation time.
2. **Given** a confirmed surge notification event exists and the notification service is operational, **When** delivery is attempted, **Then** the operational manager receives the alert through the configured channel and the delivery outcome is recorded as successful.
3. **Given** a confirmed surge alert is processed successfully, **When** operational logs are reviewed, **Then** the records show the detector flag, surge confirmation, notification event creation, and successful delivery using the same correlation or event identifier where available.
4. **Given** a scope has already entered confirmed surge state and a notification has been sent for that active surge, **When** subsequent ingestion runs for the same category and optional geography continue to produce residuals above both confirmation thresholds, **Then** the system suppresses additional surge notifications for that scope until the residuals return to normal.

---

### User Story 2 - Avoid alerts for invalid surges (Priority: P2)

As an operational manager, I want the system to filter false positives so that I am only interrupted for meaningful abnormal demand conditions.

**Why this priority**: Accurate surge alerts are critical to user trust and operational usefulness, but they depend on the core confirmed-alert flow already existing.

**Independent Test**: Can be fully tested by completing a successful UC-01 ingestion run whose newly ingested actual demand yields a residual pattern for a service category and optional geography that is evaluated by the residual-based detector but does not satisfy both configured abnormal-surge confirmation criteria, and verifying that no notification event is created or sent.

**Acceptance Scenarios**:

1. **Given** a successful UC-01 ingestion run produces a residual pattern for a service category and optional geography that causes the residual-based detector to flag a potential surge, **When** the confirmation or validation step determines that either the z-score threshold or the absolute percent-above-forecast floor is not satisfied, **Then** the system logs the event as filtered and does not create or send a surge notification.
2. **Given** the detector flags a potential surge after an ingestion run, **When** confirmation has not succeeded yet, **Then** the system does not notify the operational manager solely because the detector produced an initial residual spike signal.

---

### User Story 3 - Preserve traceability when detection or delivery fails (Priority: P3)

As an operational manager, I want failures in surge detection or notification delivery to be traceable so that missed alerts can be investigated and followed up.

**Why this priority**: Failure handling reduces operational risk, but it depends on the main surge-detection and notification workflow already existing.

**Independent Test**: Can be fully tested by forcing a residual-detector processing failure after a successful UC-01 ingestion run and a notification delivery failure after a confirmed surge, and verifying that the system records the correct failure outcomes, suppresses invalid sends, and marks confirmed but undelivered alerts for retry or manual review.

**Acceptance Scenarios**:

1. **Given** a successful UC-01 ingestion run has completed and the surge detection module encounters a processing error while evaluating residuals against the active LightGBM P50 forecast, **When** the failure occurs, **Then** the system logs the detection failure with timestamp and error category, does not attempt confirmation, and does not create or send a notification.
2. **Given** a surge has been confirmed and a notification event exists, **When** notification delivery fails, **Then** the system logs the failure with timestamp and correlation or event identifier and marks the event for retry or manual review.

### Edge Cases

- A detector processing error occurs after a successful UC-01 ingestion run but before confirmation can begin, and no notification event is created.
- The detector flags a surge candidate based on residual z-score, but confirmation rejects it because the absolute percent-above-forecast floor is not met even though the z-score threshold is exceeded.
- A confirmed surge has category and magnitude information but no applicable geography, and the notification still proceeds without geography.
- Notification delivery fails after the surge event is created, and the undelivered event must remain traceable for retry or manual follow-up.
- Multiple surge candidates may be evaluated across ingestion runs, and each candidate must retain its own confirmation and delivery outcome records.
- A scope remains above both confirmation thresholds across multiple ingestion runs, and the system must suppress duplicate notifications until that same scope returns to normal and later re-enters surge state.
- Surge detection evaluates only against the active daily forecast product from UC-03; weekly forecast products from UC-04 are excluded because ingestion-triggered actuals align to intraday or daily buckets rather than weekly aggregates.
- Operational logs are reviewed after either a success or failure path, and the relevant entries can be linked through a shared event or correlation identifier where available.
- The active P50 forecast for a scope is zero; positive actual demand must still be confirmable if the z-score threshold is also satisfied, without requiring division by zero in persisted metrics.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST trigger surge detection immediately after each successful UC-01 ingestion run completes.
- **FR-002**: For each triggered evaluation, the system MUST compare newly ingested actual demand from UC-01 against the active LightGBM P50 forecast to calculate residuals for each evaluated scope, where the primary scope is service category optionally narrowed by geography.
- **FR-003**: The system MUST identify potential surge candidates using a statistical residual-based anomaly signal computed as a z-score over a rolling baseline of forecast residuals, rather than a separate machine-learning detector.
- **FR-004**: The system MUST require a confirmation or validation step to determine whether a flagged surge candidate is a confirmed abnormal demand surge before any notification is sent.
- **FR-005**: The system MUST confirm a surge only when both of the following hold for the evaluated scope at the same time: the residual z-score exceeds the configured z-score threshold and the absolute residual percent-above-forecast exceeds a configurable floor.
- **FR-005a**: When the active P50 forecast for an evaluated scope is zero, the system MUST treat any positive actual demand as satisfying the percent-above-forecast confirmation floor, MUST treat zero actual demand as not satisfying that floor, and MAY persist the numeric percent-above-forecast value as null because the percentage denominator is zero.
- **FR-006**: The system MUST treat a candidate that fails either confirmation condition as not confirmed and MUST NOT create or send a surge notification for that evaluation.
- **FR-007**: The system MUST create a surge notification event only after a surge condition has been confirmed.
- **FR-008**: Each confirmed surge notification event MUST include the affected service category, optional geography when available, magnitude of deviation, and detection or confirmation time.
- **FR-009**: The system MUST send confirmed surge notifications to the operational manager through the configured notification channel or channels.
- **FR-010**: The system MUST record successful notification delivery outcomes for monitoring and audit purposes.
- **FR-011**: The system MUST log the ingestion-triggered detector evaluation, surge confirmation outcome, notification event creation, and notification delivery outcome for each evaluated surge flow.
- **FR-012**: If the surge detection module encounters a processing error, the system MUST log the failure with timestamp and error category, MUST NOT attempt surge confirmation for that failed evaluation, and MUST NOT create or send a notification for that failed evaluation.
- **FR-013**: If a flagged surge candidate is rejected during confirmation or validation, the system MUST log the event as filtered or cancelled and MUST NOT create or send a notification.
- **FR-014**: If notification delivery fails for a confirmed surge event, the system MUST log the delivery failure and preserve the event in a state of retry pending or manual review required.
- **FR-015**: The system MUST persist surge candidates, confirmation outcomes, notification events, delivery attempts, and per-scope surge state in surge-specific tables that are separate from UC-10 threshold-alert persistence.
- **FR-016**: The system MUST maintain traceable records linking the UC-01 ingestion run, detector outcome, confirmation outcome, notification event, and delivery attempt for each surge candidate or confirmed surge event.
- **FR-017**: Where the platform supports it, the system MUST use a shared event identifier or correlation identifier consistently across logs and records for the same surge candidate or confirmed surge event.
- **FR-018**: Notification payloads and operational records MUST represent geography as optional so the feature can support confirmed surges where category and magnitude are known but geography is not available.
- **FR-019**: The system MUST send at most one notification when a given service-category-and-optional-geography scope first enters confirmed surge state.
- **FR-020**: The system MUST suppress additional notifications for the same scope while that scope remains above both confirmation thresholds across subsequent ingestion-triggered evaluations.
- **FR-021**: The system MUST re-arm notification eligibility for a scope only after that scope returns to normal by no longer meeting the confirmation conditions, and it MUST NOT send periodic reminder notifications while the surge remains active.

### Key Entities *(include if feature involves data)*

- **Surge Candidate**: A detector-flagged evaluation outcome created after a successful UC-01 ingestion run for a service category and optional geography when newly ingested actual demand produces a forecast residual whose z-score against the rolling residual baseline exceeds the configured anomaly threshold and requires dual-threshold confirmation before the system may alert the operational manager.
- **Surge Confirmation Outcome**: The validation result for a surge candidate, recorded per evaluated scope as confirmed, filtered false positive, suppressed because the scope is already in an active surge state, or failed due to detection or confirmation error, and storing both the z-score and percent-above-forecast confirmation results.
- **Surge Notification Event**: A surge-specific notification record created for a confirmed surge when the evaluated scope first enters surge state, stored separately from UC-10 threshold-alert records, and including category, optional geography, surge magnitude, detection or confirmation time, delivery status, and any follow-up state such as retry pending or manual review required.
- **Surge Detection Evaluation**: A surge-specific operational record linked to a UC-01 ingestion run that stores the evaluated service category, optional geography, actual demand, the active LightGBM P50 forecast reference, computed residual, rolling-baseline context, z-score outcome, percent-above-forecast outcome, and detector status.
- **Surge State**: A per-scope operational record that tracks whether a service category and optional geography is currently in confirmed surge state, whether a notification has already been sent for the active surge interval, and when the scope returns to normal and becomes eligible to notify again.
- **Operational Manager**: The business recipient responsible for receiving and acting on confirmed abnormal-demand surge alerts.

## Assumptions

- The active LightGBM P50 forecast is available at surge-evaluation time for the same scope as the newly ingested actual demand from UC-01.
- The forecast reference used by UC-11 is always the active daily forecast product from UC-03 (`ForecastVersion` and `ForecastBucket`); UC-04 weekly forecast products are not eligible inputs for surge detection.
- The system can derive or access a rolling residual baseline for the evaluated scope when each ingestion-triggered surge check runs.
- The system can compute absolute residual percent-above-forecast for each evaluated scope and compare it against a configurable confirmation floor.
- Notification destinations for the operational manager are configured outside this feature.
- The notification channel may be a dashboard alert, email, SMS, or another configured mechanism, but this feature is concerned with the event creation and delivery outcome rather than channel-specific UX.
- Retry execution and manual review workflows may already exist elsewhere; this feature must place failed deliveries into a traceable follow-up state.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In stakeholder acceptance testing, 100% of ingestion-triggered residual patterns that satisfy both the configured z-score threshold and the configured percent-above-forecast floor for a service category and optional geography generate exactly one surge notification event when that scope enters surge state, with category, optional geography when available, magnitude, and detection or confirmation time populated.
- **SC-002**: In stakeholder acceptance testing, 100% of confirmed surges under a healthy notification service produce a recorded send attempt and a successful delivery outcome to the operational manager.
- **SC-003**: In stakeholder acceptance testing, 100% of detector-error, single-threshold-only, and filtered-false-positive cases triggered after successful UC-01 ingestion runs produce no notification event and no notification send attempt.
- **SC-004**: In stakeholder acceptance testing, 100% of notification delivery failures for confirmed surges leave a traceable event record with failure details and a follow-up state of retry pending or manual review required.
- **SC-005**: In stakeholder acceptance testing, 100% of repeated ingestion-triggered evaluations for a scope that remains above both confirmation thresholds while already in active surge state produce no additional notification event until that scope returns to normal and later re-enters confirmed surge state.
