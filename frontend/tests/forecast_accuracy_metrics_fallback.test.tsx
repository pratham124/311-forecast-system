import { cleanup, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ForecastAccuracyPage } from '../src/pages/ForecastAccuracyPage';

describe('forecast accuracy metrics fallback flow', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('shows metrics-unavailable messaging and still renders aligned buckets', async () => {
    fetchMock
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            forecastProduct: 'daily_1_day',
            categories: ['Roads', 'Waste'],
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            forecastAccuracyRequestId: 'fa-2',
            forecastAccuracyResultId: 'result-2',
            timeRangeStart: '2026-03-01T00:00:00Z',
            timeRangeEnd: '2026-03-02T00:00:00Z',
            forecastProductName: 'daily_1_day',
            comparisonGranularity: 'hourly',
            viewStatus: 'rendered_without_metrics',
            metricResolutionStatus: 'unavailable',
            statusMessage: 'Metrics are unavailable for this comparison window.',
            alignedBuckets: [
              {
                bucketStart: '2026-03-01T00:00:00Z',
                bucketEnd: '2026-03-01T01:00:00Z',
                forecastValue: 4,
                actualValue: 0,
                absoluteErrorValue: 4,
              },
            ],
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(new Response(JSON.stringify({ recordedOutcomeStatus: 'rendered', message: 'ok', forecastAccuracyRequestId: 'fa-2' }), { status: 202 }));

    render(
      <MemoryRouter>
        <ForecastAccuracyPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/metrics are unavailable for this comparison window/i)).toBeInTheDocument();
    expect(await screen.findByText(/aligned buckets/i)).toBeInTheDocument();
    expect(await screen.findByText(/abs error/i)).toBeInTheDocument();
    expect(await screen.findByText(/time/i)).toBeInTheDocument();
  });
});
