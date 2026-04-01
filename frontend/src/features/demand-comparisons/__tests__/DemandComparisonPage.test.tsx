import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { DemandComparisonPage } from '../../../pages/DemandComparisonPage';

const contextPayload = {
  serviceCategories: ['Roads', 'Waste'],
  geographyLevels: ['ward'],
  geographyOptions: { ward: ['Ward 1', 'Ward 2'] },
  summary: 'Comparison context ready.',
};

const successPayload = {
  comparisonRequestId: 'comparison-1',
  filters: {
    serviceCategories: ['Roads'],
    geographyLevel: 'ward',
    geographyValues: ['Ward 1'],
    timeRangeStart: '2026-03-01T00:00:00Z',
    timeRangeEnd: '2026-03-02T00:00:00Z',
  },
  outcomeStatus: 'success',
  resultMode: 'chart_and_table',
  comparisonGranularity: 'daily',
  forecastProduct: 'daily_1_day',
  forecastGranularity: 'hourly',
  sourceCleanedDatasetVersionId: 'dataset-1',
  sourceForecastVersionId: 'forecast-1',
  series: [
    {
      seriesType: 'historical',
      serviceCategory: 'Roads',
      geographyKey: 'Ward 1',
      points: [{ bucketStart: '2026-03-01T00:00:00Z', bucketEnd: '2026-03-02T00:00:00Z', value: 2 }],
    },
  ],
  message: 'Historical and forecast demand were aligned successfully.',
};

describe('DemandComparisonPage', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('loads context, submits a request, and renders replacement results', async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(contextPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(successPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ comparisonRequestId: 'comparison-1', recordedOutcomeStatus: 'rendered' }), { status: 202 }));

    render(<DemandComparisonPage />);

    await screen.findByRole('button', { name: /roads/i });
    fireEvent.click(screen.getByRole('button', { name: /compare demand/i }));

    expect(await screen.findByText(/comparison summary/i)).toBeInTheDocument();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
  });

  it('shows warning flow and proceeds after acknowledgement', async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(contextPayload), { status: 200 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            comparisonRequestId: 'warning-1',
            filters: successPayload.filters,
            outcomeStatus: 'warning_required',
            warning: { shown: true, acknowledged: false, message: 'This scope is large.' },
            message: 'This scope is large.',
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(new Response(JSON.stringify(successPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ comparisonRequestId: 'comparison-1', recordedOutcomeStatus: 'rendered' }), { status: 202 }));

    render(<DemandComparisonPage />);

    await screen.findByRole('button', { name: /compare demand/i });
    fireEvent.click(screen.getByRole('button', { name: /compare demand/i }));
    expect(await screen.findByText(/large request warning/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /proceed/i }));
    expect(await screen.findByText(/series table/i)).toBeInTheDocument();
  });
});
