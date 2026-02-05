# User Stories for Proactive311

Proactive311 — A Time Series Forecasting + Alerting System for Edmonton 311 Service Demand. Target users: **Operational Managers** (staffing, dispatch), **City Planners / Performance Teams**, and **Public Residents**.

---

## User Story 1: Scheduled Data Refresh
**As an** operational manager  
**I want to** have 311 service request data pulled automatically on a schedule  
**So that** forecasts and the dashboard stay up to date without manual runs

## User Story 2: Valid and Consistent Data
**As a** city planner  
**I want to** have ingested data pass schema validation and deduplication  
**So that** downstream forecasting and dashboards use reliable, consistent inputs

## User Story 3: Short-Term Demand Forecast (1-Day)
**As an** operational manager  
**I want to** get a 1-day (next 24 hours) demand forecast per service category (and geography when available)  
**So that** I can plan staffing and dispatch for tomorrow

## User Story 4: Medium-Term Demand Forecast (7-Day)
**As an** operational manager  
**I want to** get a 7-day demand forecast per service category (and geography when available)  
**So that** I can allocate crews and equipment for the coming week

## User Story 5: Forecast Visualization with Uncertainty
**As an** operational manager  
**I want to** see forecast curves with uncertainty bands (e.g. P50/P90) overlaid on history  
**So that** I can judge likely demand, know how confident the system is, and plan for high/low scenarios

## User Story 6: Forecast Evaluation Against Baselines
**As a** performance analyst  
**I want to** have the forecasting engine evaluated against baselines (e.g. seasonal naive, moving average)  
**So that** we know the system adds value over simple rules

## User Story 7: Historical Trend Exploration
**As a** city planner  
**I want to** explore historical 311 demand by category, time range, and geography  
**So that** I can understand patterns and support capacity planning

## User Story 8: Compare Categories and Geographies
**As a** city planner  
**I want to** compare demand and forecasts across categories and geographies (e.g. wards)  
**So that** I can prioritize resources and spot regional differences

## User Story 9: Optional Weather Overlay
**As an** operational manager  
**I want to** have an optional weather overlay (e.g. temperature, snowfall) on the forecast explorer  
**So that** I can relate demand spikes to weather events

## User Story 10: Spike Alerts (Threshold-Based)
**As an** operational manager  
**I want to** be notified when forecasted demand for a category (and optionally geography) exceeds a configurable threshold  
**So that** I can prepare for likely spikes

## User Story 11: Surge / Anomaly Alerts
**As an** operational manager  
**I want to** be notified when a surge detector flags abnormal demand (“storm mode”)  
**So that** I can respond even when the spike wasn’t fully predicted

## User Story 12: Alert Drill-Down and Context
**As an** operational manager  
**I want to** drill into an alert and see forecast distribution, drivers, and recent anomaly context  
**So that** I can explain why the alert fired and decide on actions

## User Story 13: Alert Settings and Channels
**As an** operational manager  
**I want to** configure alert thresholds and notification channels (e.g. email; optional Slack/Teams)  
**So that** I receive alerts in the way that fits my workflow and am not overwhelmed by duplicate or excessive alerts

## User Story 14: View Forecast Accuracy
**As a** city planner or performance analyst  
**I want to** see recent forecast accuracy and compare past predictions to actuals  
**So that** I can evaluate and improve trust in the system

## User Story 15: Weather and Event Awareness
**As an** operational manager  
**I want to** have the system account for weather and major events (e.g. storms) in uncertainty and alerts  
**So that** during “storm mode” I get appropriately cautious forecasts and higher sensitivity where relevant

## User Story 16: Confidence Degraded Indicator
**As an** operational manager  
**I want to** see the UI show when confidence is degraded (e.g. during shocks or missing data)  
**So that** I don’t over-rely on point forecasts in abnormal conditions

## User Story 17: View Forecasts as Public Resident
**As a** public resident  
**I want to** view forecasts of 311 demand by category  
**So that** I can make an informed decision on the fastest way to reach services

## User Story 18: User Guide
**As a** user  
**I want to** access a user guide  
**So that** I can learn how to use the system

## User Story 19: Submit Feedback or Bug Report
**As a** user  
**I want to** submit feedback or report a bug to the dev team  
**So that** issues can be addressed
