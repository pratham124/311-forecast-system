import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ForecastVisualizationPage } from '../../../pages/ForecastVisualizationPage';

const reportRenderSuccess = vi.fn();
const clearOverlay = vi.fn();
const visibleOverlay = {
  overlayRequestId: 'overlay-1',
  geographyId: 'citywide',
  timeRangeStart: '2026-03-19T00:00:00Z',
  timeRangeEnd: '2026-03-20T00:00:00Z',
  weatherMeasure: 'temperature' as const,
  measurementUnit: 'C',
  overlayStatus: 'visible' as const,
  baseForecastPreserved: true as const,
  userVisible: true as const,
  observationGranularity: 'hourly' as const,
  observations: [{ timestamp: '2026-03-20T00:00:00Z', value: 3 }],
  stateSource: 'overlay-assembly' as const,
};

vi.mock('../../weather-overlay/hooks/useWeatherOverlay', () => ({
  useWeatherOverlay: () => ({
    overlay: visibleOverlay,
    isLoading: false,
    error: null,
    reportRenderSuccess,
    reportRenderFailure: vi.fn(),
    clearOverlay,
  }),
}));

const categoriesPayload = { forecastProduct: 'daily_1_day', categories: ['Roads'] };
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
  pipelineStatus: [],
  viewStatus: 'success',
};

describe('ForecastVisualizationPage – weather overlay integration', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
    reportRenderSuccess.mockReset();
    clearOverlay.mockReset();
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('reports visible overlays and clears them when toggled off', async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(categoriesPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(successPayload), { status: 200 }))
      .mockResolvedValue(new Response(null, { status: 202 }));

    render(<ForecastVisualizationPage />);

    await screen.findByRole('img', { name: /demand forecast chart/i });
    await waitFor(() => {
      expect(reportRenderSuccess).toHaveBeenCalledTimes(1);
    });

    const checkbox = screen.getByLabelText(/enable weather overlay/i);
    fireEvent.click(checkbox);
    fireEvent.click(checkbox);

    expect(clearOverlay).toHaveBeenCalledTimes(1);
  });
});
