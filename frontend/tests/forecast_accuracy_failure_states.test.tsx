import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ForecastAccuracyErrorBoundary } from '../src/features/forecast-accuracy/components/ForecastAccuracyErrorBoundary';
import { ForecastAccuracyPage } from '../src/pages/ForecastAccuracyPage';
import { MemoryRouter } from 'react-router-dom';

describe('forecast accuracy failure states', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('shows the unavailable state from the backend', async () => {
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
            forecastAccuracyRequestId: 'fa-3',
            forecastAccuracyResultId: 'result-3',
            timeRangeStart: '2026-03-01T00:00:00Z',
            timeRangeEnd: '2026-03-02T00:00:00Z',
            forecastProductName: 'daily_1_day',
            comparisonGranularity: 'hourly',
            viewStatus: 'unavailable',
            statusMessage: 'Historical forecast data is unavailable for the selected scope.',
            alignedBuckets: [],
          }),
          { status: 200 },
        ),
      );

    render(
      <MemoryRouter>
        <ForecastAccuracyPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/historical forecast data is unavailable/i)).toBeInTheDocument();
  });

  it('falls back when rendering crashes', async () => {
    const onRenderFailure = vi.fn();
    const Crash = () => {
      throw new Error('chart crashed');
    };

    render(
      <ForecastAccuracyErrorBoundary
        onRenderFailure={onRenderFailure}
        fallback={<div>fallback shown</div>}
      >
        <Crash />
      </ForecastAccuracyErrorBoundary>,
    );

    expect(await screen.findByText(/fallback shown/i)).toBeInTheDocument();
    await waitFor(() => expect(onRenderFailure).toHaveBeenCalled());
  });
});
