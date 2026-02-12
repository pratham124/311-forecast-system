# UC-13 Acceptance Test Suite: Alert Settings and Channels

**Use Case**: UC-13 Configure Alert Thresholds and Notification Channels  
**Scope**: Operations Analytics System  
**Goal**: Verify an Operational Manager can configure alert thresholds (by category and optional geography), choose notification channels (e.g., email; optional Slack/Teams), and set frequency/deduplication preferences; and that the system validates, saves, applies, and logs configuration changes while preventing unsupported/invalid settings and handling storage failures safely.

---

## Assumptions / Test Harness Requirements
- A test environment with an **Operational Manager** account that has access permissions. fileciteturn8file0
- A controllable **Configuration Store / Data Storage System** supporting:
  - read current configuration
  - write updated configuration
  - injected storage failure (DB outage / permission error / timeout)
  - verification that “previous configuration remains active” after failed save fileciteturn8file0
- A controllable **Notification Service** / channel integration layer supporting:
  - available supported channels (email; optional Slack/Teams) fileciteturn8file0
  - injected “unsupported channel” condition for validation testing fileciteturn8file0
- A defined validation policy for thresholds (e.g., non-negative; within max bounds) and for channel support.
- Observability:
  - logs accessible for assertions (including success and failure logs) fileciteturn8file0
  - UI states observable (loaded settings, validation error, save success, save failure)
  - ability to confirm the saved configuration is applied to future alerts (via a stubbed alert evaluation/notification test hook)

---

## AT-01 — Alert configuration settings loads and displays current values
**Covers**: Main Success Scenario Steps 1–2 fileciteturn8file0  
**Preconditions**
- Operational Manager is authenticated and has access permissions. fileciteturn8file0

**Steps**
1. Operational Manager accesses alert configuration settings. fileciteturn8file0
2. Observe the displayed settings.

**Expected Results**
- The system displays current:
  - threshold values (by category; optional geography scope) fileciteturn8file0
  - notification channel options (email; optional Slack/Teams) fileciteturn8file0
  - frequency and/or deduplication preferences fileciteturn8file0
- No error state is shown.

---

## AT-02 — Adjust thresholds by category (and optional geography)
**Covers**: Main Success Scenario Step 3 fileciteturn8file0  
**Preconditions**
- Settings page is loaded (AT-01).

**Steps**
1. Select `Category_A` and change its threshold value.
2. If geography-specific thresholds are supported, set a threshold for `Category_B` + `Geo_1` (e.g., a ward).
3. Review the updated values on screen.

**Expected Results**
- UI accepts edits for category thresholds.
- If applicable, UI accepts edits for category + geography thresholds.
- Changes are reflected in the settings form prior to saving (draft state).

---

## AT-03 — Select supported notification channels
**Covers**: Main Success Scenario Step 4 fileciteturn8file0  
**Preconditions**
- Settings page is loaded (AT-01).
- Supported channels are available (e.g., Email; optional Slack/Teams). fileciteturn8file0

**Steps**
1. Select Email as a notification channel.
2. If Slack/Teams integrations are supported in the test environment, select Slack or Teams as well.
3. Review selected channels on screen.

**Expected Results**
- UI allows selecting supported channel(s).
- Selected channel(s) are shown as active in the configuration form.

---

## AT-04 — Configure frequency/deduplication preferences
**Covers**: Main Success Scenario Step 5 fileciteturn8file0  
**Preconditions**
- Settings page is loaded (AT-01).

**Steps**
1. Configure a frequency limit (e.g., “no more than 1 alert per X minutes”) if available.
2. Enable or configure deduplication (e.g., “dedupe by category+geo within window”) if available.
3. Review the settings on screen.

**Expected Results**
- UI accepts frequency/deduplication configuration.
- Values are visible and persisted in the draft configuration state.

---

## AT-05 — Save configuration: system validates and stores updated settings
**Covers**: Main Success Scenario Steps 6–8; Success End Condition fileciteturn8file0  
**Preconditions**
- Draft configuration includes:
  - at least one threshold edit (AT-02)
  - at least one channel selected (AT-03)
  - frequency/dedup settings (AT-04)

**Steps**
1. Click Save.
2. Observe validation feedback (if shown).
3. Confirm successful save.

**Expected Results**
- System validates settings. fileciteturn8file0
- Validation succeeds.
- System stores updated configuration. fileciteturn8file0
- UI confirms configuration saved (toast/banner/state).
- Future alerts will follow configured rules (verified in AT-07). fileciteturn8file0

---

## AT-06 — Successful configuration update is logged
**Covers**: Main Success Scenario Step 9 fileciteturn8file0  
**Preconditions**
- A successful save occurs (AT-05).

**Steps**
1. Perform a successful save.
2. Retrieve logs/events for the operation.

**Expected Results**
- Logs include a successful configuration update entry (timestamp; actor; optional correlation id). fileciteturn8file0
- Logs include key changed dimensions (thresholds and channels) or a config version reference (implementation-dependent).

---

## AT-07 — Saved settings are applied to subsequent alert behavior
**Covers**: Success End Condition (“saved and applied”) fileciteturn8file0  
**Preconditions**
- Configuration saved successfully (AT-05).
- Test harness can trigger an alert evaluation/notification scenario (e.g., threshold-based alert flow) and inspect resulting delivery behavior.

**Steps**
1. Trigger an alert scenario that should fire under the new thresholds (e.g., forecast exceeds configured threshold for `Category_A`).
2. Observe which channels are used and whether frequency/dedup rules constrain notifications.
3. Trigger the same/duplicate alert within the dedup window (if configured).
4. Trigger again outside the window (if applicable).

**Expected Results**
- Alerts follow the configured threshold scope (category; optional geography).
- Notifications are delivered only to the configured channel(s).
- Frequency/dedup settings reduce duplicate/excess alerts as configured (e.g., suppression/aggregation within window).
- System behavior is consistent with the manager’s saved preferences. fileciteturn8file0

---

## AT-08 — Invalid threshold values are rejected and configuration is not saved
**Covers**: Extension 7a (7a1–7a2) fileciteturn8file0  
**Preconditions**
- Settings page is loaded (AT-01).

**Steps**
1. Enter an invalid threshold value (e.g., negative or outside allowed range) for a category or category+geo. fileciteturn8file0
2. Click Save.

**Expected Results**
- System displays a validation error identifying invalid threshold values. fileciteturn8file0
- Configuration is not saved. fileciteturn8file0
- Previously saved configuration remains unchanged/active.

---

## AT-09 — Unsupported notification channel selection is rejected
**Covers**: Extension 4a (4a1–4a2) fileciteturn8file0  
**Preconditions**
- Settings page is loaded (AT-01).
- Test harness can present or simulate selection of an unsupported channel.

**Steps**
1. Attempt to select an unsupported channel (or select a channel whose integration is not available). fileciteturn8file0
2. Click Save (or observe immediate validation if inline).

**Expected Results**
- System displays an error indicating the channel is unsupported. fileciteturn8file0
- The unsupported channel selection is rejected (unselected/blocked).
- Configuration cannot be saved until a supported channel is chosen. fileciteturn8file0

---

## AT-10 — Storage failure: system logs error and retains previous configuration
**Covers**: Extension 8a (8a1–8a2); Failed End Condition fileciteturn8file0  
**Preconditions**
- Draft configuration changes are valid (AT-02 to AT-04).
- Inject a storage failure (DB outage/permission issue). fileciteturn8file0

**Steps**
1. Click Save.
2. Trigger the storage failure during the store step.
3. Observe UI and logs.
4. Reload the settings page.

**Expected Results**
- System logs a storage error. fileciteturn8file0
- UI informs the manager the configuration could not be saved.
- Previous configuration remains active. fileciteturn8file0
- On reload, settings reflect the previous saved configuration (not the failed draft).

---

## AT-11 — Clarity over partial updates: only valid, supported configurations are applied; failures are logged; previous settings remain active
**Covers**: Key Behavioral Theme Across All Alternatives fileciteturn8file0  
**Preconditions**
- Test harness supports:
  - invalid thresholds (AT-08)
  - unsupported channel (AT-09)
  - storage failure (AT-10)
  - successful save (AT-05/AT-06)

**Steps**
1. Execute AT-08 and verify no save occurs.
2. Execute AT-09 and verify no save occurs until channel is supported.
3. Execute AT-10 and verify prior settings remain active after failed save.
4. Execute AT-05 and verify new settings are applied (AT-07).

**Expected Results**
- Only valid and supported configurations are applied. fileciteturn8file0
- Errors are clearly communicated to the manager. fileciteturn8file0
- Failures are logged for monitoring. fileciteturn8file0
- Previous configurations remain active on failure to prevent inconsistent alert behavior. fileciteturn8file0

---

## Traceability Matrix
| Acceptance Test | UC-13 Flow Covered |
|---|---|
| AT-01 | Main Success Scenario (1–2) fileciteturn8file0 |
| AT-02 | Main Success Scenario (3) fileciteturn8file0 |
| AT-03 | Main Success Scenario (4) fileciteturn8file0 |
| AT-04 | Main Success Scenario (5) fileciteturn8file0 |
| AT-05 | Main Success Scenario (6–8); Success End Condition fileciteturn8file0 |
| AT-06 | Main Success Scenario (9) fileciteturn8file0 |
| AT-07 | Success End Condition (saved and applied) fileciteturn8file0 |
| AT-08 | Extension 7a fileciteturn8file0 |
| AT-09 | Extension 4a fileciteturn8file0 |
| AT-10 | Extension 8a; Failed End Condition fileciteturn8file0 |
| AT-11 | Key Behavioral Theme Across All Alternatives fileciteturn8file0 |
