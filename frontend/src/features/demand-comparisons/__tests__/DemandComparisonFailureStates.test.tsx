import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { DemandComparisonPage } from '../../../pages/DemandComparisonPage';

const contextPayload = {
  serviceCategories: ['Roads'],
  geographyLevels: ['ward'],
  geographyOptions: { ward: ['Ward 1'] },
};

describe('DemandComparison failure states', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('shows partial-forecast-missing messaging', async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(contextPayload), { status: 200 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            comparisonRequestId: 'comparison-2',
            filters: {
              serviceCategories: ['Roads'],
              geographyLevel: 'ward',
              geographyValues: ['Ward 1'],
              timeRangeStart: '2026-03-01T00:00:00Z',
              timeRangeEnd: '2026-03-02T00:00:00Z',
            },
            outcomeStatus: 'partial_forecast_missing',
            resultMode: 'chart_and_table',
            comparisonGranularity: 'daily',
            series: [],
            missingCombinations: [{ serviceCategory: 'Roads', geographyKey: 'Ward 1', missingSource: 'forecast', message: 'Forecast data is unavailable for Roads in Ward 1.' }],
            message: 'Comparison loaded with 1 selected combinations missing forecast data.',
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(new Response(JSON.stringify({ comparisonRequestId: 'comparison-2', recordedOutcomeStatus: 'rendered' }), { status: 202 }));

    render(<DemandComparisonPage />);
    await screen.findByRole('button', { name: /compare demand/i });
    fireEvent.click(screen.getByRole('button', { name: /compare demand/i }));
    expect(await screen.findByText(/missing combinations/i)).toBeInTheDocument();
  });

  it('shows alignment failure error state', async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(contextPayload), { status: 200 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            comparisonRequestId: 'comparison-3',
            filters: {
              serviceCategories: ['Roads'],
              geographyLevel: 'ward',
              geographyValues: ['Ward 1'],
              timeRangeStart: '2026-03-01T00:00:00Z',
              timeRangeEnd: '2026-03-02T00:00:00Z',
            },
            outcomeStatus: 'alignment_failed',
            message: 'Historical and forecast demand could not be aligned for the selected scope.',
          }),
          { status: 200 },
        ),
      );

    render(<DemandComparisonPage />);
    await screen.findByRole('button', { name: /compare demand/i });
    fireEvent.click(screen.getByRole('button', { name: /compare demand/i }));
    expect(await screen.findByText(/could not be aligned/i)).toBeInTheDocument();
  });
});
