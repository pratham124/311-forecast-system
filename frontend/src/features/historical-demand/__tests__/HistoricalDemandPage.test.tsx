import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { HistoricalDemandPage } from '../../../pages/HistoricalDemandPage';

const contextPayload = {
  serviceCategories: ['Roads', 'Waste'],
  supportedGeographyLevels: ['ward'],
  summary: 'Using approved cleaned dataset test-version for historical demand exploration.',
};

const successPayload = {
  analysisRequestId: 'request-1',
  filters: {
    serviceCategory: 'Roads',
    timeRangeStart: '2026-03-01T00:00:00Z',
    timeRangeEnd: '2026-03-31T23:59:59Z',
    geographyLevel: 'ward',
    geographyValue: 'Ward 1',
  },
  aggregationGranularity: 'daily',
  resultMode: 'chart_and_table',
  summaryPoints: [
    {
      bucketStart: '2026-03-05T00:00:00Z',
      bucketEnd: '2026-03-06T00:00:00Z',
      serviceCategory: 'Roads',
      geographyKey: 'Ward 1',
      demandCount: 2,
    },
  ],
  outcomeStatus: 'success',
  message: 'Historical demand data loaded successfully.',
};

describe('HistoricalDemandPage', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('loads context, submits a valid request, and renders results', async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(contextPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(successPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(null, { status: 202 }));

    render(<HistoricalDemandPage />);

    await screen.findByRole('button', { name: /explore historical demand/i });
    fireEvent.click(screen.getByRole('button', { name: /explore historical demand/i }));

    expect(await screen.findByText(/historical demand pattern/i)).toBeInTheDocument();
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(3);
    });
    expect(String(fetchMock.mock.calls[1][0])).toContain('/api/v1/historical-demand/queries');
  });

  it('shows warning controls and supports proceed flow', async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(contextPayload), { status: 200 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            analysisRequestId: 'warning-1',
            filters: successPayload.filters,
            warning: { shown: true, acknowledged: false, message: 'This request spans a large historical scope and may take longer to load.' },
            summaryPoints: [],
            outcomeStatus: 'no_data',
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(new Response(JSON.stringify(successPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(null, { status: 202 }));

    render(<HistoricalDemandPage />);

    await screen.findByRole('button', { name: /explore historical demand/i });
    fireEvent.click(screen.getByRole('button', { name: /explore historical demand/i }));
    expect(await screen.findByText(/large request warning/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /proceed/i }));

    expect(await screen.findByText(/historical demand pattern/i)).toBeInTheDocument();
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(4);
    });
  });

  it('shows no-data messaging without partial results', async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(contextPayload), { status: 200 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            analysisRequestId: 'request-2',
            filters: successPayload.filters,
            summaryPoints: [],
            outcomeStatus: 'no_data',
            message: 'No historical demand data matches the selected filters.',
          }),
          { status: 200 },
        ),
      );

    render(<HistoricalDemandPage />);

    await screen.findByRole('button', { name: /explore historical demand/i });
    fireEvent.click(screen.getByRole('button', { name: /explore historical demand/i }));

    expect(await screen.findByText(/no data found/i)).toBeInTheDocument();
    expect(screen.queryByText(/summary table/i)).not.toBeInTheDocument();
  });
});
