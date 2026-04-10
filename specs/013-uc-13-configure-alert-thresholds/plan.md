# Implementation Plan: Configure Alert Thresholds

**Status**: Aligned with actual implementation (2026-04-10)

## Summary

The "Configure Alert Thresholds" feature has been implemented as a simplified, category-level management system. Instead of the complex immutable versioning originally planned, the system uses a mutable `ThresholdConfiguration` model with status-based lifecycle (active/inactive). All notifications are delivered to a consolidated Dashboard channel.

## Technical Architecture

### Backend
- **Storage**: `ThresholdConfiguration` table in PostgreSQL.
- **Repository**: `ThresholdConfigurationRepository` handles CRUD. Geography is currently hardcoded to `None` as per the simplification requirement.
- **API**: FastAPI routes in `api/routes/forecast_alerts.py`.
- **Logic**: Saving a threshold triggers an immediate background evaluation via `_schedule_recheck`.

### Frontend
- **Page**: `AlertReviewPage.tsx` acts as the host for both alert review and threshold settings.
- **Form**: A unified form for adding/editing thresholds by service category and window type (hourly/daily).
- **Client**: `forecastAlerts.ts` interacts with the `/api/v1/forecast-alerts` surface.

## Simplifications from Original Plan

| Original Feature | Current Implementation |
|------------------|------------------------|
| Multi-channel | Single "dashboard" channel (hardcoded/mocked) |
| Geography Scope | Category-only (geography is `None`) |
| Immutable Versions | Mutable rows with `status='active/inactive'` |
| Frequency Rules | Not implemented (re-evaluates on demand/publish) |

## Verification Status

- [x] Backend CRUD API
- [x] Frontend Threshold Management UI
- [x] Background Evaluation Trigger
- [x] Dashboard Delivery (Log/DB only)
- [x] Role-based Access Control (OperationalManager only)
