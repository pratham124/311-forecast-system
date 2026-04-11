import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AlertReviewPage } from '../src/pages/AlertReviewPage';

function okJson(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), { status });
}

function baseFetch(url: string): Response {
  if (url.endsWith('/api/v1/forecast-alerts/service-categories')) return okJson({ items: ['Roads'] });
  if (url.endsWith('/api/v1/forecast-alerts/thresholds')) return okJson({ items: [] });
  if (url.endsWith('/api/v1/surge-alerts/events')) return okJson({ items: [] });
  if (url.endsWith('/api/v1/forecast-alerts/events')) {
    return okJson({
      items: [
        {
          notificationEventId: 'event-threshold-1',
          serviceCategory: 'Roads',
          forecastWindowType: 'hourly',
          forecastWindowStart: '2026-03-20T00:00:00Z',
          forecastWindowEnd: '2026-03-20T01:00:00Z',
          forecastValue: 12,
          thresholdValue: 8,
          overallDeliveryStatus: 'manual_review_required',
          createdAt: '2026-03-20T00:05:00Z',
        },
      ],
    });
  }
  if (url.includes('/render-events')) return new Response(null, { status: 202 });
  return okJson({ items: [] });
}

describe('Alert detail state rendering', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('renders the dedicated unavailable-detail state', async () => {
    fetchMock.mockImplementation((input) => {
      const url = String(input);
      if (url.includes('/api/v1/alert-details/threshold_alert/event-threshold-1')) {
        return Promise.resolve(okJson({
          alertDetailLoadId: 'detail-load-unavailable',
          alertSource: 'threshold_alert',
          alertId: 'event-threshold-1',
          alertTriggeredAt: '2026-03-20T00:05:00Z',
          overallDeliveryStatus: 'manual_review_required',
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
          viewStatus: 'unavailable',
          failureReason: 'All detail components were unavailable for this alert.',
          distribution: { status: 'unavailable', points: [], unavailableReason: 'Distribution unavailable.' },
          drivers: { status: 'unavailable', drivers: [], unavailableReason: 'Drivers unavailable.' },
          anomalies: { status: 'unavailable', items: [], unavailableReason: 'Anomalies unavailable.' },
        }));
      }
      return Promise.resolve(baseFetch(url));
    });

    render(<AlertReviewPage roles={['OperationalManager']} />);

    expect(await screen.findByText(/detail unavailable/i)).toBeInTheDocument();
    expect(await screen.findByText(/all detail components were unavailable/i)).toBeInTheDocument();
  });

  it('renders the error-detail state when preparation fails', async () => {
    fetchMock.mockImplementation((input) => {
      const url = String(input);
      if (url.includes('/api/v1/alert-details/threshold_alert/event-threshold-1')) {
        return Promise.resolve(okJson({
          alertDetailLoadId: 'detail-load-error',
          alertSource: 'threshold_alert',
          alertId: 'event-threshold-1',
          alertTriggeredAt: '2026-03-20T00:05:00Z',
          overallDeliveryStatus: 'manual_review_required',
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
          viewStatus: 'error',
          failureReason: 'Forecast version not found.',
          distribution: { status: 'failed', points: [], failureReason: 'Forecast version not found.' },
          drivers: { status: 'available', drivers: [{ label: 'Weather', contribution: 0.6, direction: 'increase' }] },
          anomalies: { status: 'available', items: [] },
        }));
      }
      return Promise.resolve(baseFetch(url));
    });

    render(<AlertReviewPage roles={['OperationalManager']} />);

    expect(await screen.findByText(/detail preparation failed/i)).toBeInTheDocument();
    expect(await screen.findAllByText(/forecast version not found/i)).toHaveLength(2);
  });
});
