import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AlertReviewPage } from '../src/pages/AlertReviewPage';

function okJson(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), { status });
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((resolver) => {
    resolve = resolver;
  });
  return { promise, resolve };
}

describe('AlertReviewPage', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('merges threshold and surge alerts, renders partial detail, and reports render success once', async () => {
    const user = userEvent.setup();
    const surgeDetailDeferred = deferred<Response>();

    fetchMock.mockImplementation((input) => {
      const url = String(input);
      if (url.endsWith('/api/v1/forecast-alerts/service-categories')) {
        return Promise.resolve(okJson({ items: ['Roads', 'Waste'] }));
      }
      if (url.endsWith('/api/v1/forecast-alerts/thresholds')) {
        return Promise.resolve(okJson({
          items: [
            {
              thresholdConfigurationId: 'threshold-1',
              serviceCategory: 'Roads',
              forecastWindowType: 'hourly',
              thresholdValue: 8,
              notificationChannels: ['dashboard'],
              operationalManagerId: 'manager-1',
              status: 'active',
              effectiveFrom: '2026-03-19T00:00:00Z',
            },
          ],
        }));
      }
      if (url.endsWith('/api/v1/forecast-alerts/events')) {
        return Promise.resolve(okJson({
          items: [
            {
              notificationEventId: 'event-threshold-1',
              serviceCategory: 'Roads',
              forecastWindowType: 'hourly',
              forecastWindowStart: '2026-03-20T00:00:00Z',
              forecastWindowEnd: '2026-03-20T01:00:00Z',
              forecastValue: 12,
              thresholdValue: 8,
              overallDeliveryStatus: 'partial_delivery',
              createdAt: '2026-03-20T00:05:00Z',
            },
          ],
        }));
      }
      if (url.endsWith('/api/v1/surge-alerts/events')) {
        return Promise.resolve(okJson({
          items: [
            {
              surgeNotificationEventId: 'event-surge-1',
              surgeEvaluationRunId: 'run-2',
              surgeCandidateId: 'candidate-2',
              serviceCategory: 'Waste',
              evaluationWindowStart: '2026-03-19T11:00:00Z',
              evaluationWindowEnd: '2026-03-19T12:00:00Z',
              actualDemandValue: 6,
              forecastP50Value: 2,
              residualValue: 4,
              residualZScore: 4.5,
              percentAboveForecast: 200,
              overallDeliveryStatus: 'delivered',
              createdAt: '2026-03-19T11:05:00Z',
            },
          ],
        }));
      }
      if (url.includes('/api/v1/alert-details/threshold_alert/event-threshold-1')) {
        return Promise.resolve(okJson({
          alertDetailLoadId: 'detail-load-1',
          alertSource: 'threshold_alert',
          alertId: 'event-threshold-1',
          correlationId: 'event-threshold-1',
          alertTriggeredAt: '2026-03-20T00:05:00Z',
          overallDeliveryStatus: 'partial_delivery',
          forecastProduct: 'daily',
          forecastReferenceId: 'forecast-1',
          forecastWindowType: 'hourly',
          windowStart: '2026-03-20T00:00:00Z',
          windowEnd: '2026-03-20T01:00:00Z',
          primaryMetricLabel: 'Forecast',
          primaryMetricValue: 12,
          secondaryMetricLabel: 'Threshold',
          secondaryMetricValue: 8,
          scope: { serviceCategory: 'Roads', geographyType: null, geographyValue: null },
          viewStatus: 'partial',
          distribution: {
            status: 'available',
            granularity: 'hourly',
            summaryValue: 12,
            points: [
              { label: '2026-03-20T00:00:00Z', bucketStart: '2026-03-20T00:00:00Z', bucketEnd: '2026-03-20T01:00:00Z', p10: 9, p50: 12, p90: 16, isAlertedBucket: true },
              { label: '2026-03-20T01:00:00Z', bucketStart: '2026-03-20T01:00:00Z', bucketEnd: '2026-03-20T02:00:00Z', p10: 8, p50: 11, p90: 15, isAlertedBucket: false },
            ],
          },
          drivers: {
            status: 'unavailable',
            drivers: [],
            unavailableReason: 'No compatible daily forecast model is currently available.',
          },
          anomalies: {
            status: 'available',
            items: [
              {
                surgeCandidateId: 'candidate-a',
                surgeNotificationEventId: 'surge-a',
                evaluationWindowStart: '2026-03-19T06:00:00Z',
                evaluationWindowEnd: '2026-03-19T07:00:00Z',
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
        }));
      }
      if (url.includes('/api/v1/alert-details/surge_alert/event-surge-1')) {
        return surgeDetailDeferred.promise;
      }
      if (url.includes('/api/v1/alert-details/detail-load-1/render-events')) {
        return Promise.resolve(new Response(null, { status: 202 }));
      }
      return Promise.resolve(okJson({ items: [] }));
    });

    render(<AlertReviewPage roles={['OperationalManager']} />);

    expect(await screen.findByText(/set thresholds and inspect threshold plus surge alerts/i)).toBeInTheDocument();
    expect(await screen.findByText(/partial detail available/i)).toBeInTheDocument();
    expect(await screen.findByText(/no compatible daily forecast model is currently available/i)).toBeInTheDocument();
    expect(await screen.findByRole('img', { name: /alert distribution chart/i })).toBeInTheDocument();
    expect(screen.getAllByText(/^Threshold$/)).not.toHaveLength(0);
    expect(screen.getAllByText(/^Surge$/)).not.toHaveLength(0);

    await user.click(screen.getByRole('button', { name: /waste/i }));
    expect(await screen.findByText(/loading alert detail while keeping the selected alert context visible/i)).toBeInTheDocument();

    await waitFor(() => {
      const renderEventCalls = fetchMock.mock.calls.filter(([url]) => String(url).includes('/render-events'));
      expect(renderEventCalls).toHaveLength(1);
    });
  });

  it('keeps selected alert metadata visible while the next detail request is loading', async () => {
    const user = userEvent.setup();
    const surgeDetailDeferred = deferred<Response>();

    fetchMock.mockImplementation((input) => {
      const url = String(input);
      if (url.endsWith('/api/v1/forecast-alerts/service-categories')) {
        return Promise.resolve(okJson({ items: ['Roads', 'Waste'] }));
      }
      if (url.endsWith('/api/v1/forecast-alerts/thresholds')) {
        return Promise.resolve(okJson({ items: [] }));
      }
      if (url.endsWith('/api/v1/forecast-alerts/events')) {
        return Promise.resolve(okJson({
          items: [
            {
              notificationEventId: 'event-threshold-1',
              serviceCategory: 'Roads',
              forecastWindowType: 'hourly',
              forecastWindowStart: '2026-03-20T00:00:00Z',
              forecastWindowEnd: '2026-03-20T01:00:00Z',
              forecastValue: 12,
              thresholdValue: 8,
              overallDeliveryStatus: 'partial_delivery',
              createdAt: '2026-03-20T00:05:00Z',
            },
          ],
        }));
      }
      if (url.endsWith('/api/v1/surge-alerts/events')) {
        return Promise.resolve(okJson({
          items: [
            {
              surgeNotificationEventId: 'event-surge-1',
              surgeEvaluationRunId: 'run-2',
              surgeCandidateId: 'candidate-2',
              serviceCategory: 'Waste',
              evaluationWindowStart: '2026-03-20T11:00:00Z',
              evaluationWindowEnd: '2026-03-20T12:00:00Z',
              actualDemandValue: 6,
              forecastP50Value: 2,
              residualValue: 4,
              residualZScore: 4.5,
              percentAboveForecast: 200,
              overallDeliveryStatus: 'delivered',
              createdAt: '2026-03-19T11:05:00Z',
            },
          ],
        }));
      }
      if (url.includes('/api/v1/alert-details/threshold_alert/event-threshold-1')) {
        return Promise.resolve(okJson({
          alertDetailLoadId: 'detail-load-1',
          alertSource: 'threshold_alert',
          alertId: 'event-threshold-1',
          alertTriggeredAt: '2026-03-20T00:05:00Z',
          overallDeliveryStatus: 'partial_delivery',
          forecastProduct: 'daily',
          forecastReferenceId: 'forecast-1',
          forecastWindowType: 'hourly',
          windowStart: '2026-03-20T00:00:00Z',
          windowEnd: '2026-03-20T01:00:00Z',
          primaryMetricLabel: 'Forecast',
          primaryMetricValue: 12,
          secondaryMetricLabel: 'Threshold',
          secondaryMetricValue: 8,
          scope: { serviceCategory: 'Roads' },
          viewStatus: 'rendered',
          distribution: { status: 'unavailable', points: [], unavailableReason: 'Distribution unavailable.' },
          drivers: { status: 'unavailable', drivers: [], unavailableReason: 'Drivers unavailable.' },
          anomalies: { status: 'unavailable', items: [], unavailableReason: 'Anomalies unavailable.' },
        }));
      }
      if (url.includes('/api/v1/alert-details/surge_alert/event-surge-1')) {
        return surgeDetailDeferred.promise;
      }
      if (url.includes('/render-events')) {
        return Promise.resolve(new Response(null, { status: 202 }));
      }
      return Promise.resolve(okJson({ items: [] }));
    });

    render(<AlertReviewPage roles={['OperationalManager']} />);

    expect(await screen.findByText(/roads/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /waste/i }));

    expect(await screen.findByText(/loading alert detail while keeping the selected alert context visible/i)).toBeInTheDocument();
    expect(screen.getAllByText(/^Waste$/)).not.toHaveLength(0);
    expect(screen.getAllByText(/^Actual$/i)).not.toHaveLength(0);
    expect(screen.getAllByText(/^Forecast P50$/i)).not.toHaveLength(0);
    expect(screen.getAllByText(/^6$/)).not.toHaveLength(0);
    expect(screen.getAllByText(/^2$/)).not.toHaveLength(0);

    surgeDetailDeferred.resolve(okJson({
      alertDetailLoadId: 'detail-load-2',
      alertSource: 'surge_alert',
      alertId: 'event-surge-1',
      alertTriggeredAt: '2026-03-20T11:05:00Z',
      overallDeliveryStatus: 'delivered',
      forecastProduct: 'daily',
      forecastReferenceId: 'forecast-1',
      forecastWindowType: 'hourly',
      windowStart: '2026-03-20T11:00:00Z',
      windowEnd: '2026-03-20T12:00:00Z',
      primaryMetricLabel: 'Actual demand',
      primaryMetricValue: 6,
      secondaryMetricLabel: 'Forecast P50',
      secondaryMetricValue: 2,
      scope: { serviceCategory: 'Waste' },
      viewStatus: 'rendered',
      distribution: {
        status: 'available',
        granularity: 'hourly',
        summaryValue: 6,
        points: [{ label: '2026-03-20T11:00:00Z', bucketStart: '2026-03-20T11:00:00Z', bucketEnd: '2026-03-20T12:00:00Z', p10: 1, p50: 2, p90: 4, isAlertedBucket: true }],
      },
      drivers: {
        status: 'available',
        drivers: [
          { label: 'Weather', contribution: 1.2, direction: 'increase' },
          { label: 'Recent demand', contribution: -0.4, direction: 'decrease' },
        ],
      },
      anomalies: { status: 'unavailable', items: [], unavailableReason: 'No anomalies.' },
    }));

    expect(await screen.findByText(/weather/i)).toBeInTheDocument();
  });
});
