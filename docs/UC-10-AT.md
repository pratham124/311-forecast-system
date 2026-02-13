# UC-10 Acceptance Test Suite: Spike Alerts (Threshold-Based)

**Use Case**: UC-10 Notify on Forecast Demand Threshold Exceedance  
**Scope**: Operations Analytics System  
**Goal**: Verify the system evaluates updated forecasts against configurable thresholds (by service category and optionally geography), sends notifications when thresholds are exceeded, and logs outcomes; and that it handles missing configuration, no-exceedance, and notification delivery failures with correct behavior and traceability.

---

## Assumptions / Test Harness Requirements
- A test environment with seeded **forecast outputs** for:
  - multiple categories (e.g., Category_A, Category_B)
  - optional geographies (e.g., Ward_1, Ward_2)
  - multiple forecast horizons/time windows (e.g., next day, next week)
- A controllable **Threshold Configuration Store** supporting:
  - thresholds configured by category
  - thresholds configured by category + geography
  - “not configured” condition (missing thresholds)
  - threshold updates (change value and/or scope)
- A controllable **Forecast Update Trigger**:
  - ability to simulate “forecast generated/updated” event (manual trigger or scheduled job)
- A controllable **Notification Service** supporting:
  - successful delivery
  - delivery failure (timeout / 5xx / provider outage)
  - ability to record attempted deliveries and final status
- Observability:
  - logs accessible for assertions (ideally with correlation/event id)
  - ability to inspect notification payload contents (category, optional geography, forecast value, threshold value, time window)
  - ability to verify retry/manual-review marking behavior (queue entry, status flag, dashboard entry, etc.)
- Notification channels (email/SMS/dashboard) can be stubbed; tests assert “notification event sent” and payload correctness.

---

## AT-01 — Forecast update triggers threshold evaluation
**Covers**: Main Success Scenario Steps 1–2  
**Preconditions**
- Forecast data exists.
- Thresholds are configured for at least one category (and optionally a geography).

**Steps**
1. Trigger a forecast generation/update event.
2. Observe processing and logs.

**Expected Results**
- System starts evaluation of forecast values against configured thresholds.
- Logs include an entry indicating:
  - forecast update detected
  - evaluation initiated (with event/correlation id if available)

---

## AT-02 — Threshold exceedance by category results in notification event creation
**Covers**: Main Success Scenario Steps 2–4  
**Preconditions**
- Threshold configured for `Category_A` (no geography scope).
- Forecast contains a value for `Category_A` exceeding its configured threshold for time window `W`.

**Steps**
1. Trigger forecast update event containing the exceeding value.
2. Observe evaluation outcome.
3. Inspect created notification event (or queued message).

**Expected Results**
- System detects exceedance for `Category_A` in window `W`.
- System creates a notification event containing at minimum:
  - category
  - forecasted value
  - threshold value
  - time window/horizon
- No geography is included (or geography is “not applicable”) for category-only thresholds.

---

## AT-03 — Threshold exceedance by category + geography results in scoped notification
**Covers**: Main Success Scenario Steps 2–4  
**Preconditions**
- Threshold configured for `Category_B` + `Ward_1`.
- Forecast contains `Category_B` for `Ward_1` exceeding threshold in window `W`.
- Forecast contains `Category_B` for `Ward_2` NOT exceeding threshold (control).

**Steps**
1. Trigger forecast update event containing values for `Ward_1` and `Ward_2`.
2. Observe evaluation outcome.
3. Inspect notification event(s).

**Expected Results**
- System detects exceedance only for `Category_B` + `Ward_1`.
- Notification event includes geography (`Ward_1`) and excludes `Ward_2` as it does not exceed.
- Payload correctly reflects the scoped forecast value, threshold value, and time window.

---

## AT-04 — Notification is delivered to operational manager on exceedance
**Covers**: Main Success Scenario Step 5; Success End Condition  
**Preconditions**
- An exceedance condition exists (as in AT-02 or AT-03).
- Notification Service is operational and configured for the Operational Manager.

**Steps**
1. Trigger a forecast update that produces an exceedance.
2. Observe notification delivery outcome in the Notification Service stub/log.

**Expected Results**
- System sends the notification to the Operational Manager via the configured channel(s).
- Notification delivery is marked successful in the Notification Service records.
- Operational Manager receives/has access to the alert (as asserted via stubbed channel receipt).

---

## AT-05 — Successful delivery is logged for monitoring
**Covers**: Main Success Scenario Step 6; Success End Condition  
**Preconditions**
- A successful notification delivery occurs (as in AT-04).

**Steps**
1. Execute a successful exceedance notification flow.
2. Retrieve logs/events for the run.

**Expected Results**
- Logs include:
  - evaluation completed
  - exceedance detected (category, optional geography, window)
  - notification event created
  - notification delivered successfully
- Entries are correlated (same event/correlation id) where available.

---

## AT-06 — Thresholds not configured: configuration issue is logged and no notification is sent
**Covers**: Extension 2a (2a1–2a2)  
**Preconditions**
- Forecast update occurs for categories/geographies where thresholds are **not configured**.
- Notification Service is operational (to ensure “no send” is intentional).

**Steps**
1. Trigger a forecast update event.
2. Observe system behavior and logs.
3. Check Notification Service records for any attempted sends.

**Expected Results**
- System logs a configuration issue indicating thresholds are missing/not configured.
- System does not create or send any notification for the unconfigured scope.
- No notification delivery attempt is recorded for that event.

---

## AT-07 — No threshold exceedance: system takes no action
**Covers**: Extension 3a (3a1)  
**Preconditions**
- Thresholds are configured for selected category/geography.
- Forecast values are all **below or equal to** thresholds for the relevant window(s).

**Steps**
1. Trigger a forecast update event.
2. Observe system behavior and notification outputs.

**Expected Results**
- System performs evaluation.
- No notification event is created.
- No notification is sent.
- (Optional) System logs that evaluation completed with “no exceedance” outcome.

---

## AT-08 — Notification delivery failure is logged and event is marked for retry/manual review
**Covers**: Extension 5a (5a1–5a2); Failed End Condition  
**Preconditions**
- Exceedance condition exists for a configured threshold.
- Notification Service is forced to fail delivery (timeout/5xx/outage).
- A retry or “manual review” marking mechanism exists (queue/status flag/ticket).

**Steps**
1. Trigger a forecast update that produces an exceedance.
2. Inject Notification Service delivery failure.
3. Observe system behavior, logs, and the event status.

**Expected Results**
- System logs the delivery failure (error category, timestamp, correlation id).
- System marks the notification event for **retry** or **manual review** (as implemented).
- Operational Manager does not receive the alert at that time (asserted via stubbed channel).

---

## AT-09 — Threshold configurability: updated thresholds change exceedance behavior on subsequent forecast updates
**Covers**: Cross-cutting requirement implied by “configurable threshold”  
**Preconditions**
- Threshold exists for `Category_A` (and optionally a geography).
- Ability to update threshold value/scope in configuration store.

**Steps**
1. Set threshold for `Category_A` to `X`.
2. Trigger forecast update with `Category_A` forecast value `V` such that `V > X` and observe notification occurs.
3. Update threshold for `Category_A` to `Y` where `Y >= V`.
4. Trigger the same forecast update again (or an equivalent with value `V`).
5. Observe evaluation results and notifications.

**Expected Results**
- With threshold `X`, system detects exceedance and sends notification.
- After updating to `Y`, system does **not** send an exceedance notification for value `V`.
- Logs reflect the threshold value used in each evaluation run.

---

## Traceability Matrix
| Acceptance Test | UC-10 Flow Covered |
|---|---|
| AT-01 | Main Success Scenario (1–2) |
| AT-02 | Main Success Scenario (2–4) |
| AT-03 | Main Success Scenario (2–4) with optional geography |
| AT-04 | Main Success Scenario (5); Success End Condition |
| AT-05 | Main Success Scenario (6); Success End Condition |
| AT-06 | Extension 2a |
| AT-07 | Extension 3a |
| AT-08 | Extension 5a; Failed End Condition |
| AT-09 | “Configurable threshold” behavior across updates |
