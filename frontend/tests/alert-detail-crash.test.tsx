import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AlertReviewPage } from '../src/pages/AlertReviewPage';

vi.mock('../src/features/alert-details/AlertDistributionChart', () => ({
  AlertDistributionChart: () => {
    throw new Error('Alert detail chart crash');
  },
}));

function okJson(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), { status });
}

describe('Alert detail crash handling', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('records render_failed when the alert detail chart crashes', async () => {
    fetchMock.mockImplementation((input) => {
      const url = String(input);
      if (url.endsWith('/api/v1/forecast-alerts/service-categories')) return Promise.resolve(okJson({ items: ['Roads'] }));
      if (url.endsWith('/api/v1/forecast-alerts/thresholds')) return Promise.resolve(okJson({ items: [] }));
      if (url.endsWith('/api/v1/surge-alerts/events')) return Promise.resolve(okJson({ items: [] }));
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
      if (url.includes('/api/v1/alert-details/threshold_alert/event-threshold-1')) {
        return Promise.resolve(okJson({
          alertDetailLoadId: 'detail-load-crash',
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
          distribution: {
            status: 'available',
            granularity: 'hourly',
            summaryValue: 12,
            points: [{ label: '2026-03-20T00:00:00Z', bucketStart: '2026-03-20T00:00:00Z', bucketEnd: '2026-03-20T01:00:00Z', p10: 8, p50: 12, p90: 16, isAlertedBucket: true }],
          },
          drivers: { status: 'available', drivers: [{ label: 'Weather', contribution: 1.2, direction: 'increase' }] },
          anomalies: { status: 'available', items: [] },
        }));
      }
      if (url.includes('/render-events')) return Promise.resolve(new Response(null, { status: 202 }));
      return Promise.resolve(okJson({ items: [] }));
    });

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(<AlertReviewPage roles={['OperationalManager']} />);

    expect(await screen.findByText(/couldn't display this alert detail/i)).toBeInTheDocument();

    await waitFor(() => {
      const urls = fetchMock.mock.calls.map((call) => String(call[0]));
      expect(urls.some((url) => url.includes('/render-events'))).toBe(true);
    });

    consoleSpy.mockRestore();
  });
});
