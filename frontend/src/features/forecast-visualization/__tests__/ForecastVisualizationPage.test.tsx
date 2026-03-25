import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ForecastVisualizationPage } from '../../../pages/ForecastVisualizationPage';

const successPayload = {
  visualizationLoadId: 'load-1',
  forecastProduct: 'daily_1_day',
  forecastGranularity: 'hourly',
  categoryFilter: { selectedCategory: 'Roads', selectedCategories: ['Roads'] },
  historyWindowStart: '2026-03-13T00:00:00Z',
  historyWindowEnd: '2026-03-20T00:00:00Z',
  forecastWindowStart: '2026-03-20T00:00:00Z',
  forecastWindowEnd: '2026-03-21T00:00:00Z',
  forecastBoundary: '2026-03-20T00:00:00Z',
  lastUpdatedAt: '2026-03-20T00:00:00Z',
  historicalSeries: [{ timestamp: '2026-03-19T00:00:00Z', value: 8 }],
  forecastSeries: [{ timestamp: '2026-03-20T00:00:00Z', pointForecast: 10 }],
  uncertaintyBands: { labels: ['P10', 'P50', 'P90'], points: [{ timestamp: '2026-03-20T00:00:00Z', p10: 8, p50: 10, p90: 12 }] },
  alerts: [],
  pipelineStatus: [{ code: 'forecast_loaded', level: 'info', message: 'Loaded daily forecast data.' }],
  viewStatus: 'success',
};

const categoriesPayload = {
  forecastProduct: 'daily_1_day',
  categories: ['Roads', 'Waste', 'Transit', 'Parks'],
};

describe('ForecastVisualizationPage', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('loads and renders the dashboard with all service areas selected, then submits a rendered event', async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(categoriesPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(successPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(null, { status: 202 }));

    render(<ForecastVisualizationPage />);

    expect(await screen.findByRole('img', { name: /demand forecast chart/i })).toBeInTheDocument();
    expect(screen.getByText(/all service areas/i)).toBeInTheDocument();
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(3);
    });
    expect(String(fetchMock.mock.calls[1][0])).toContain('forecastProduct=daily_1_day');
    expect(String(fetchMock.mock.calls[1][0])).not.toContain('serviceCategory=');
    expect(fetchMock.mock.calls[2][0]).toContain('/render-events');
  });

  it('shows fallback messaging when a retained snapshot is returned', async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(categoriesPayload), { status: 200 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            ...successPayload,
            viewStatus: 'fallback_shown',
            fallback: {
              snapshotId: 'snapshot-1',
              createdAt: '2026-03-20T00:00:00Z',
              expiresAt: '2026-03-21T00:00:00Z',
            },
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(new Response(null, { status: 202 }));

    render(<ForecastVisualizationPage />);

    expect(await screen.findByLabelText(/fallback snapshot banner/i)).toBeInTheDocument();
  });

  it('shows unavailable state when the API reports unavailable', async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(categoriesPayload), { status: 200 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            ...successPayload,
            forecastSeries: [],
            historicalSeries: [],
            uncertaintyBands: undefined,
            viewStatus: 'unavailable',
            summary: 'Forecast data is unavailable.',
          }),
          { status: 200 },
        ),
      );

    render(<ForecastVisualizationPage />);

    expect(await screen.findByText(/forecast view unavailable/i)).toBeInTheDocument();
  });

  it('starts with all service areas selected and updates the request when one is removed', async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(categoriesPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(successPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(null, { status: 202 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            ...successPayload,
            categoryFilter: { selectedCategory: 'Roads', selectedCategories: ['Roads', 'Transit', 'Parks'] },
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(new Response(null, { status: 202 }));

    render(<ForecastVisualizationPage />);
    await screen.findByRole('img', { name: /demand forecast chart/i });

    fireEvent.click(screen.getByRole('button', { name: /service areas/i }));
    fireEvent.click(screen.getByLabelText('Waste'));

    await waitFor(() => {
      const requestedUrls = fetchMock.mock.calls.map((call) => String(call[0]));
      expect(
        requestedUrls.some(
          (url) =>
            url.includes('excludeServiceCategory=Waste')
            && !url.includes('?serviceCategory=')
            && !url.includes('&serviceCategory='),
        ),
      ).toBe(true);
    });
  });
});
