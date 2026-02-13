# UC-11 Acceptance Test Suite: Surge / Anomaly Alerts (“Storm Mode”)

**Use Case**: UC-11 Notify on Abnormal Demand Surge Detection  
**Scope**: Operations Analytics System  
**Goal**: Verify the system detects abnormal demand (“storm mode”) via a surge detector, confirms validity, creates an alert event with key details, notifies the Operational Manager, and logs outcomes; and that it handles detection errors, false positives, and notification delivery failures with correct behavior and traceability.

---

## Assumptions / Test Harness Requirements
- A test environment with a controllable **real-time demand stream** (or simulated stream) that can produce:
  - normal demand patterns
  - abnormal surge patterns that exceed configured abnormality thresholds
  - noisy patterns that trigger a detector but should be filtered as false positives
- A controllable **Surge Detection Module** supporting:
  - normal operation (flagging potential surges)
  - injected processing errors (data stream interruption, computational failure)
  - configurable abnormality thresholds / sensitivity
- A controllable **Surge Confirmation / Validation** step (if separate from detection) supporting:
  - confirmation success (“storm mode” confirmed)
  - confirmation invalid (false positive filtered)
- A controllable **Notification Service** supporting:
  - successful delivery
  - delivery failure (timeout / 5xx / outage)
  - ability to capture attempted deliveries and payloads
- Observability:
  - logs accessible for assertions (preferably with correlation/event id)
  - ability to inspect the notification payload (category, geography, magnitude, detection time)
  - ability to verify retry/manual-review marking behavior (queue entry, status flag, dashboard entry, etc.)
- Notification channels (dashboard/email/SMS) may be stubbed; tests assert that an alert event is created and a send attempt occurs.

---

## AT-01 — Incoming demand is monitored and potential surge events are evaluated
**Covers**: Main Success Scenario Steps 1–2  
**Preconditions**
- Surge Detection Module is configured and operational.
- Current demand data stream is active (real or simulated).

**Steps**
1. Start the demand stream with normal data.
2. Observe that the Surge Detection Module is processing incoming events.
3. Inject a demand pattern that should exceed abnormality thresholds.

**Expected Results**
- System monitors demand data continuously.
- System evaluates demand against abnormality thresholds.
- A potential surge is flagged when abnormality thresholds are exceeded.

---

## AT-02 — Surge condition is confirmed (“storm mode”) before alert creation
**Covers**: Main Success Scenario Step 3; Key Behavioral Theme  
**Preconditions**
- A demand pattern is injected that should be considered a true abnormal surge.

**Steps**
1. Inject an abnormal surge pattern into the demand stream.
2. Observe the system’s confirmation/validation behavior (if visible).
3. Inspect logs/events for confirmation outcome.

**Expected Results**
- System confirms the surge condition (“storm mode”) rather than immediately alerting on any detector spike.
- Confirmation outcome is logged (confirmed vs filtered) with correlation/event id where available.

---

## AT-03 — On confirmed surge, system creates a surge notification event with required details
**Covers**: Main Success Scenario Step 4  
**Preconditions**
- Surge condition is confirmed (“storm mode”).

**Steps**
1. Trigger a confirmed surge.
2. Inspect the created surge notification event (or queued message) payload.

**Expected Results**
- System creates a surge notification event containing relevant details:
  - affected **category**
  - affected **geography** (if applicable/available)
  - **magnitude** of deviation (e.g., delta, z-score, percent above baseline)
  - **time** of detection/confirmation
- Payload fields are populated consistently with the injected surge scenario.

---

## AT-04 — Notification is delivered to the operational manager for confirmed surges
**Covers**: Main Success Scenario Step 5; Success End Condition  
**Preconditions**
- Confirmed surge event exists (as in AT-03).
- Notification Service is operational and configured for the Operational Manager.

**Steps**
1. Trigger a confirmed surge.
2. Observe the Notification Service stub/log for send attempt and status.

**Expected Results**
- Notification Service sends an alert to the Operational Manager (via configured channel).
- Delivery is marked successful.
- The notification content reflects the event payload (category, geography, magnitude, time).

---

## AT-05 — Successful surge notification delivery is logged
**Covers**: Main Success Scenario Step 6; Success End Condition  
**Preconditions**
- A successful surge notification delivery occurs (as in AT-04).

**Steps**
1. Execute a confirmed surge flow.
2. Retrieve logs/events for the run.

**Expected Results**
- Logs include:
  - detector flagged surge
  - surge confirmation succeeded
  - notification event created
  - notification delivered successfully
- Entries are correlated (same event/correlation id) where available.

---

## AT-06 — Surge detection module error is logged and no notification is sent
**Covers**: Extension 2a (2a1–2a2)  
**Preconditions**
- Configure Surge Detection Module to produce an error (e.g., stream interruption or processing failure).
- Notification Service is operational (to ensure “no send” is intentional).

**Steps**
1. Start the demand stream.
2. Inject a detector processing error during evaluation.
3. Observe UI/logs and Notification Service records.

**Expected Results**
- System logs detection module failure with error category and timestamp.
- System does not attempt to confirm a surge condition.
- No notification event is created and no notification is sent.

---

## AT-07 — False positive is filtered: no notification is sent; outcome is logged
**Covers**: Extension 3a (3a1–3a2); Key Behavioral Theme  
**Preconditions**
- Configure a pattern that triggers the detector but should be invalidated by validation logic (noise/normal variation).
- Confirmation/validation logic is enabled.

**Steps**
1. Inject a noisy or borderline pattern that the detector flags.
2. Allow validation logic to run.
3. Inspect logs and Notification Service records.

**Expected Results**
- System determines surge condition is not valid (filtered false positive).
- System logs that the event was filtered/cancelled.
- No notification event is created and no notification is sent.

---

## AT-08 — Notification delivery failure is logged and event is marked for retry/manual review
**Covers**: Extension 5a (5a1–5a2); Failed End Condition  
**Preconditions**
- A confirmed surge condition occurs.
- Notification Service is forced to fail delivery (timeout / 5xx / outage).
- A retry or manual review marking mechanism exists (queue/status flag/ticket).

**Steps**
1. Trigger a confirmed surge (storm mode).
2. Inject Notification Service failure during delivery.
3. Observe logs and the resulting event status.

**Expected Results**
- System logs delivery failure (error category, timestamp, correlation id).
- System marks the event for **retry** or **manual review** (as implemented).
- Operational Manager does not receive the alert at that time (asserted via stubbed channel).

---

## Traceability Matrix
| Acceptance Test | UC-11 Flow Covered |
|---|---|
| AT-01 | Main Success Scenario (1–2) |
| AT-02 | Main Success Scenario (3); Key Behavioral Theme |
| AT-03 | Main Success Scenario (4) |
| AT-04 | Main Success Scenario (5); Success End Condition |
| AT-05 | Main Success Scenario (6); Success End Condition |
| AT-06 | Extension 2a |
| AT-07 | Extension 3a; Key Behavioral Theme |
| AT-08 | Extension 5a; Failed End Condition |
