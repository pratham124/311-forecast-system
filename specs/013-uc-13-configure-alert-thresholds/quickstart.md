# Quickstart: Alert Threshold Management

This guide covers how to use and maintain the **Configure Alert Thresholds** (UC-13) feature.

## User Interface

To manage alert thresholds:
1.  Navigate to the **Alerts** page (`/app/alerts`).
2.  Use the **Add Threshold** form at the top left:
    *   **Service Category**: Select the 311 service category (e.g., "Potholes").
    *   **Forecast Window**: Choose between "Hourly" (daily forecast buckets) or "Daily" (weekly forecast buckets).
    *   **Threshold Value**: Enter the numeric limit of forecasted requests that should trigger an alert.
3.  Click **Save Threshold**.
4.  The threshold will appear in the **Active Thresholds** list. You can edit or delete existing thresholds from here.

## How it Works

1.  **Storage**: Every threshold is stored in the `ThresholdConfiguration` table.
2.  **Trigger**: Saving a threshold triggers an immediate background evaluation of the latest forecast for that category.
3.  **Delivery**: If the forecast exceeds the saved threshold, a `NotificationEvent` is created with a status of `delivered` for the `dashboard` channel.
4.  **Review**: Alerts appear in the **Recorded Alerts** list on the same page. Click an alert to see the comparison between the forecast and the threshold.

## API Endpoints

- `GET /api/v1/forecast-alerts/thresholds`: List all active thresholds.
- `POST /api/v1/forecast-alerts/thresholds`: Create a new threshold.
- `PATCH /api/v1/forecast-alerts/thresholds/{id}`: Update an existing threshold.
- `DELETE /api/v1/forecast-alerts/thresholds/{id}`: Deactivate a threshold.

## Simplified Architecture Notes

- **Geography**: Currently ignored. All thresholds are at the Service Category level.
- **Channels**: Hardcoded to `dashboard`. No external notifications (Email/SMS) are sent.
- **Versioning**: Mutable. Editing a threshold updates the existing record.
