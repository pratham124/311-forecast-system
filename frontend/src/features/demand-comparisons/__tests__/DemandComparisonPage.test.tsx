import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { DemandComparisonPage } from '../../../pages/DemandComparisonPage';

const availabilityPayload = {
  serviceCategories: ['Roads', 'Waste'],
  byCategoryGeography: {
    Roads: {
      geographyLevels: ['ward'],
      geographyOptions: { ward: ['Ward 1'] },
    },
    Waste: {
      geographyLevels: ['ward'],
      geographyOptions: { ward: ['Ward 1'] },
    },
  },
  dateConstraints: {
    overlapStart: '2026-03-02T00:00:00Z',
    overlapEnd: '2026-03-05T00:00:00Z',
  },
  presets: [
    {
      label: 'Overlap window',
      timeRangeStart: '2026-03-02T00:00:00Z',
      timeRangeEnd: '2026-03-05T00:00:00Z',
    },
  ],
  forecastProduct: 'daily_1_day',
};

const successPayload = {
  comparisonRequestId: 'comparison-1',
  filters: {
    serviceCategories: ['Roads'],
    geographyLevel: 'ward',
    geographyValues: ['Ward 1'],
    timeRangeStart: '2026-03-02T00:00:00Z',
    timeRangeEnd: '2026-03-03T00:00:00Z',
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
      points: [{ bucketStart: '2026-03-02T00:00:00Z', bucketEnd: '2026-03-03T00:00:00Z', value: 2 }],
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

  it('loads availability, submits a request, and renders results', async () => {
    const user = userEvent.setup();
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(availabilityPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(successPayload), { status: 200 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ comparisonRequestId: 'comparison-1', recordedOutcomeStatus: 'rendered' }), { status: 202 }),
      );

    render(<DemandComparisonPage />);

    await screen.findByLabelText('Service categories');
    await user.click(screen.getByLabelText('Service categories'));
    await user.click(screen.getByRole('button', { name: 'Roads' }));
    fireEvent.click(screen.getByRole('button', { name: /compare demand/i }));

    expect(await screen.findByText(/comparison summary/i)).toBeInTheDocument();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
  });

  it('shows warning flow and proceeds after acknowledgement', async () => {
    const user = userEvent.setup();
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(availabilityPayload), { status: 200 }))
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
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ comparisonRequestId: 'comparison-1', recordedOutcomeStatus: 'rendered' }), { status: 202 }),
      );

    render(<DemandComparisonPage />);

    await screen.findByLabelText('Service categories');
    await user.click(screen.getByLabelText('Service categories'));
    await user.click(screen.getByRole('button', { name: 'Roads' }));
    fireEvent.click(screen.getByRole('button', { name: /compare demand/i }));

    expect(await screen.findByText(/large request warning/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /proceed/i }));
    expect(await screen.findByText(/series table/i)).toBeInTheDocument();
  });
});
