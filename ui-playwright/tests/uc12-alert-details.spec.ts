import * as fs from 'node:fs';
import * as path from 'node:path';

import { expect, test } from '@playwright/test';

const SHOT_DIR = path.join(process.cwd(), 'test-results', 'ui-smoke');

function shotPath(name: string): string {
  return path.join(SHOT_DIR, `${name}.png`);
}

async function fullShot(page: import('@playwright/test').Page, name: string): Promise<void> {
  fs.mkdirSync(SHOT_DIR, { recursive: true });
  await page.screenshot({ path: shotPath(name), fullPage: true });
}

function thresholdDetail(
  alertId: string,
  serviceCategory: string,
  loadId: string,
  viewStatus: 'partial' | 'error' | 'unavailable',
  options: {
    failureReason?: string;
    distributionStatus: 'available' | 'failed' | 'unavailable';
    distributionReason?: string;
    driversStatus: 'available' | 'failed' | 'unavailable';
    driversReason?: string;
    anomaliesStatus: 'available' | 'failed' | 'unavailable';
    anomaliesReason?: string;
  },
) {
  return {
    alertDetailLoadId: loadId,
    alertSource: 'threshold_alert',
    alertId,
    correlationId: alertId,
    alertTriggeredAt: '2026-04-01T12:05:00Z',
    overallDeliveryStatus: 'partial_delivery',
    forecastProduct: 'daily',
    forecastReferenceId: 'forecast-1',
    forecastWindowType: 'hourly',
    windowStart: '2026-04-01T12:00:00Z',
    windowEnd: '2026-04-01T13:00:00Z',
    primaryMetricLabel: 'Forecast',
    primaryMetricValue: 12,
    secondaryMetricLabel: 'Threshold',
    secondaryMetricValue: 8,
    scope: {
      serviceCategory,
      geographyType: null,
      geographyValue: null,
    },
    viewStatus,
    failureReason: options.failureReason ?? null,
    distribution: options.distributionStatus === 'available'
      ? {
          status: 'available',
          granularity: 'hourly',
          summaryValue: 12,
          points: [
            {
              label: '2026-04-01T12:00:00Z',
              bucketStart: '2026-04-01T12:00:00Z',
              bucketEnd: '2026-04-01T13:00:00Z',
              p10: 9,
              p50: 12,
              p90: 16,
              isAlertedBucket: true,
            },
          ],
        }
      : {
          status: options.distributionStatus,
          points: [],
          failureReason: options.distributionStatus === 'failed' ? options.distributionReason : undefined,
          unavailableReason: options.distributionStatus === 'unavailable' ? options.distributionReason : undefined,
        },
    drivers: options.driversStatus === 'available'
      ? {
          status: 'available',
          drivers: [
            { label: 'Weather', contribution: 1.4, direction: 'increase' },
            { label: 'Recent demand', contribution: -0.6, direction: 'decrease' },
          ],
        }
      : {
          status: options.driversStatus,
          drivers: [],
          failureReason: options.driversStatus === 'failed' ? options.driversReason : undefined,
          unavailableReason: options.driversStatus === 'unavailable' ? options.driversReason : undefined,
        },
    anomalies: options.anomaliesStatus === 'available'
      ? {
          status: 'available',
          items: [
            {
              surgeCandidateId: 'surge-related-1',
              surgeNotificationEventId: 'surge-related-event-1',
              evaluationWindowStart: '2026-03-31T11:00:00Z',
              evaluationWindowEnd: '2026-03-31T12:00:00Z',
              actualDemandValue: 5,
              forecastP50Value: 2,
              residualZScore: 3.4,
              percentAboveForecast: 150,
              candidateStatus: 'flagged',
              confirmationOutcome: 'confirmed',
              isSelectedAlert: false,
            },
          ],
        }
      : {
          status: options.anomaliesStatus,
          items: [],
          failureReason: options.anomaliesStatus === 'failed' ? options.anomaliesReason : undefined,
          unavailableReason: options.anomaliesStatus === 'unavailable' ? options.anomaliesReason : undefined,
        },
  };
}

function surgeDetail(
  alertId: string,
  serviceCategory: string,
  loadId: string,
  viewStatus: 'rendered' | 'unavailable',
  options: {
    failureReason?: string;
    driversStatus: 'available' | 'unavailable';
    driversReason?: string;
  },
) {
  return {
    alertDetailLoadId: loadId,
    alertSource: 'surge_alert',
    alertId,
    correlationId: `corr-${alertId}`,
    alertTriggeredAt: '2026-04-01T11:05:00Z',
    overallDeliveryStatus: 'delivered',
    forecastProduct: 'daily',
    forecastReferenceId: 'forecast-1',
    forecastWindowType: 'hourly',
    windowStart: '2026-04-01T11:00:00Z',
    windowEnd: '2026-04-01T12:00:00Z',
    primaryMetricLabel: 'Actual demand',
    primaryMetricValue: 6,
    secondaryMetricLabel: 'Forecast P50',
    secondaryMetricValue: 2,
    scope: {
      serviceCategory,
      geographyType: null,
      geographyValue: null,
    },
    viewStatus,
    failureReason: options.failureReason ?? null,
    distribution: viewStatus === 'unavailable'
      ? {
          status: 'unavailable',
          points: [],
          unavailableReason: 'Distribution unavailable.',
        }
      : {
          status: 'available',
          granularity: 'hourly',
          summaryValue: 6,
          points: [
            {
              label: '2026-04-01T11:00:00Z',
              bucketStart: '2026-04-01T11:00:00Z',
              bucketEnd: '2026-04-01T12:00:00Z',
              p10: 1,
              p50: 2,
              p90: 4,
              isAlertedBucket: true,
            },
          ],
        },
    drivers: options.driversStatus === 'available'
      ? {
          status: 'available',
          drivers: [
            { label: 'Weather', contribution: 1.2, direction: 'increase' },
            { label: 'Recent demand', contribution: -0.4, direction: 'decrease' },
          ],
        }
      : {
          status: 'unavailable',
          drivers: [],
          unavailableReason: options.driversReason,
        },
    anomalies: viewStatus === 'unavailable'
      ? {
          status: 'unavailable',
          items: [],
          unavailableReason: 'No recent anomalies.',
        }
      : {
          status: 'available',
          items: [
            {
              surgeCandidateId: 'surge-selected-1',
              surgeNotificationEventId: 'surge-selected-event-1',
              evaluationWindowStart: '2026-04-01T11:00:00Z',
              evaluationWindowEnd: '2026-04-01T12:00:00Z',
              actualDemandValue: 6,
              forecastP50Value: 2,
              residualZScore: 4.5,
              percentAboveForecast: 200,
              candidateStatus: 'flagged',
              confirmationOutcome: 'confirmed',
              isSelectedAlert: true,
            },
            {
              surgeCandidateId: 'surge-neighbor-1',
              surgeNotificationEventId: 'surge-neighbor-event-1',
              evaluationWindowStart: '2026-03-31T09:00:00Z',
              evaluationWindowEnd: '2026-03-31T10:00:00Z',
              actualDemandValue: 5,
              forecastP50Value: 2,
              residualZScore: 3.2,
              percentAboveForecast: 150,
              candidateStatus: 'flagged',
              confirmationOutcome: 'confirmed',
              isSelectedAlert: false,
            },
          ],
        },
  };
}

test.describe('UC-12 alert detail drill-down', () => {
  test('merged alerts support loading, rendered, error, and unavailable states', async ({ page }) => {
    const email = process.env.E2E_EMAIL;
    const password = process.env.E2E_PASSWORD;
    test.skip(!email || !password, 'Set E2E_EMAIL and E2E_PASSWORD for UC-12 browser validation');

    const renderCounts: Record<string, number> = {};

    await page.route('**/api/v1/forecast-alerts/service-categories', async (route) => {
      await route.fulfill({ json: { items: ['Roads', 'Waste', 'Transit', 'Parks'] } });
    });
    await page.route('**/api/v1/forecast-alerts/thresholds', async (route) => {
      await route.fulfill({
        json: {
          items: [
            {
              thresholdConfigurationId: 'threshold-config-1',
              serviceCategory: 'Roads',
              forecastWindowType: 'hourly',
              thresholdValue: 8,
              notificationChannels: ['dashboard'],
              operationalManagerId: 'manager-1',
              status: 'active',
              effectiveFrom: '2026-03-30T00:00:00Z',
            },
          ],
        },
      });
    });
    await page.route('**/api/v1/forecast-alerts/events', async (route) => {
      await route.fulfill({
        json: {
          items: [
            {
              notificationEventId: 'threshold-road-1',
              serviceCategory: 'Roads',
              forecastWindowType: 'hourly',
              forecastWindowStart: '2026-04-01T12:00:00Z',
              forecastWindowEnd: '2026-04-01T13:00:00Z',
              forecastValue: 12,
              thresholdValue: 8,
              overallDeliveryStatus: 'partial_delivery',
              createdAt: '2026-04-01T12:05:00Z',
            },
            {
              notificationEventId: 'threshold-transit-1',
              serviceCategory: 'Transit',
              forecastWindowType: 'hourly',
              forecastWindowStart: '2026-04-01T09:00:00Z',
              forecastWindowEnd: '2026-04-01T10:00:00Z',
              forecastValue: 15,
              thresholdValue: 10,
              overallDeliveryStatus: 'manual_review_required',
              createdAt: '2026-04-01T09:05:00Z',
            },
          ],
        },
      });
    });
    await page.route('**/api/v1/surge-alerts/events', async (route) => {
      await route.fulfill({
        json: {
          items: [
            {
              surgeNotificationEventId: 'surge-waste-1',
              surgeEvaluationRunId: 'surge-run-1',
              surgeCandidateId: 'surge-candidate-1',
              serviceCategory: 'Waste',
              evaluationWindowStart: '2026-04-01T11:00:00Z',
              evaluationWindowEnd: '2026-04-01T12:00:00Z',
              actualDemandValue: 6,
              forecastP50Value: 2,
              residualValue: 4,
              residualZScore: 4.5,
              percentAboveForecast: 200,
              overallDeliveryStatus: 'delivered',
              createdAt: '2026-04-01T11:05:00Z',
            },
            {
              surgeNotificationEventId: 'surge-parks-1',
              surgeEvaluationRunId: 'surge-run-2',
              surgeCandidateId: 'surge-candidate-2',
              serviceCategory: 'Parks',
              evaluationWindowStart: '2026-04-01T08:00:00Z',
              evaluationWindowEnd: '2026-04-01T09:00:00Z',
              actualDemandValue: 3,
              forecastP50Value: 1,
              residualValue: 2,
              residualZScore: 2.7,
              percentAboveForecast: 120,
              overallDeliveryStatus: 'manual_review_required',
              createdAt: '2026-04-01T08:05:00Z',
            },
          ],
        },
      });
    });
    await page.route('**/api/v1/alert-details/*/render-events', async (route) => {
      const url = new URL(route.request().url());
      const pathParts = url.pathname.split('/');
      const loadId = pathParts[pathParts.length - 2];
      const payload = route.request().postDataJSON() as { renderStatus: 'rendered' | 'render_failed' };
      renderCounts[loadId] = (renderCounts[loadId] ?? 0) + 1;
      await route.fulfill({
        status: 202,
        json: {
          alertDetailLoadId: loadId,
          recordedOutcomeStatus: payload.renderStatus,
          message: 'Render event recorded.',
        },
      });
    });
    await page.route(/\/api\/v1\/alert-details\/(threshold_alert|surge_alert)\/[^/]+$/, async (route) => {
      const url = new URL(route.request().url());
      const parts = url.pathname.split('/');
      const alertSource = parts[parts.length - 2];
      const alertId = parts[parts.length - 1];

      if (alertSource === 'threshold_alert' && alertId === 'threshold-road-1') {
        await route.fulfill({
          json: thresholdDetail('threshold-road-1', 'Roads', 'detail-road-1', 'partial', {
            distributionStatus: 'available',
            driversStatus: 'unavailable',
            driversReason: 'No compatible daily forecast model is currently available.',
            anomaliesStatus: 'available',
          }),
        });
        return;
      }

      if (alertSource === 'surge_alert' && alertId === 'surge-waste-1') {
        await new Promise((resolve) => setTimeout(resolve, 700));
        await route.fulfill({
          json: surgeDetail('surge-waste-1', 'Waste', 'detail-waste-1', 'rendered', {
            driversStatus: 'available',
          }),
        });
        return;
      }

      if (alertSource === 'threshold_alert' && alertId === 'threshold-transit-1') {
        await route.fulfill({
          json: thresholdDetail('threshold-transit-1', 'Transit', 'detail-transit-1', 'error', {
            failureReason: 'Forecast version not found.',
            distributionStatus: 'failed',
            distributionReason: 'Forecast version not found.',
            driversStatus: 'available',
            anomaliesStatus: 'available',
          }),
        });
        return;
      }

      if (alertSource === 'surge_alert' && alertId === 'surge-parks-1') {
        await route.fulfill({
          json: surgeDetail('surge-parks-1', 'Parks', 'detail-parks-1', 'unavailable', {
            failureReason: 'All detail components were unavailable for this alert.',
            driversStatus: 'unavailable',
            driversReason: 'No compatible daily forecast model is currently available.',
          }),
        });
        return;
      }

      await route.fulfill({ status: 404, json: { detail: 'Alert event not found' } });
    });

    await page.goto('/');
    await page.getByLabel('Email', { exact: true }).fill(email!);
    await page.getByLabel('Password', { exact: true }).fill(password!);
    await page.locator('form').getByRole('button', { name: 'Sign in' }).click();
    await page.waitForURL(/\/app\/forecasts/, { timeout: 60_000 });

    await page.goto('/app/alerts');
    await expect(page.getByRole('heading', { name: /set thresholds and inspect threshold plus surge alerts/i })).toBeVisible();
    await expect(page.getByText('Partial detail available')).toBeVisible();
    await expect(page.getByText('No compatible daily forecast model is currently available.')).toBeVisible();
    await fullShot(page, '12-alert-details-partial');

    await page.getByRole('button', { name: /Waste/i }).click();
    await expect(page.getByText('Loading alert detail while keeping the selected alert context visible.')).toBeVisible();
    await expect(page.getByText('Actual demand', { exact: true }).first()).toBeVisible();
    await expect(page.getByText('Forecast P50', { exact: true }).first()).toBeVisible();
    await expect(page.getByText('Weather')).toBeVisible();
    await expect(page.getByText('Selected surge')).toBeVisible();
    await fullShot(page, '13-alert-details-rendered');

    await page.getByRole('button', { name: /Transit/i }).click();
    await expect(page.getByText('Detail preparation failed')).toBeVisible();
    await expect(page.getByText('Forecast version not found.').first()).toBeVisible();
    await fullShot(page, '14-alert-details-error');

    await page.getByRole('button', { name: /Parks/i }).click();
    await expect(page.getByText('Detail unavailable')).toBeVisible();
    await expect(page.getByText('All detail components were unavailable for this alert.')).toBeVisible();
    await fullShot(page, '15-alert-details-unavailable');

    await expect.poll(() => renderCounts['detail-road-1'] ?? 0).toBe(1);
    await expect.poll(() => renderCounts['detail-waste-1'] ?? 0).toBe(1);
    await expect.poll(() => renderCounts['detail-transit-1'] ?? 0).toBe(1);
    await expect.poll(() => renderCounts['detail-parks-1'] ?? 0).toBe(1);
  });
});
