import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ForecastAccuracyPage } from '../src/pages/ForecastAccuracyPage';

describe('forecast accuracy success flow', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('loads and displays forecast accuracy with metrics and reports render success', async () => {
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
            forecastAccuracyRequestId: 'fa-1',
            forecastAccuracyResultId: 'result-1',
            timeRangeStart: '2026-03-01T00:00:00Z',
            timeRangeEnd: '2026-03-02T00:00:00Z',
            forecastProductName: 'daily_1_day',
            comparisonGranularity: 'hourly',
            viewStatus: 'rendered_with_metrics',
            metricResolutionStatus: 'computed_on_demand',
            metrics: { mae: 1, rmse: 1.2, mape: 10 },
            alignedBuckets: [
              {
                bucketStart: '2026-03-01T00:00:00Z',
                bucketEnd: '2026-03-01T01:00:00Z',
                forecastValue: 4,
                actualValue: 3,
                absoluteErrorValue: 1,
              },
            ],
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(new Response(JSON.stringify({ recordedOutcomeStatus: 'rendered', message: 'ok', forecastAccuracyRequestId: 'fa-1' }), { status: 202 }));

    render(
      <MemoryRouter>
        <ForecastAccuracyPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/compare retained forecasts against actual demand/i)).toBeInTheDocument();
    expect(await screen.findByRole('button', { name: /service category/i })).toBeInTheDocument();
    expect(await screen.findByText('1.0000')).toBeInTheDocument();
    expect(await screen.findByText(/2026/i)).toBeInTheDocument();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    expect(String(fetchMock.mock.calls[2][0])).toContain('/render-events');
  });
});
