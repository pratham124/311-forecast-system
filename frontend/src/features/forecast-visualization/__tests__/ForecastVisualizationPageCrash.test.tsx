/**
 * Tests ForecastVisualizationPage when the chart component throws during render.
 * vi.mock must be at module level — kept in a separate file from other page tests.
 * Covers: handleRenderFailure → reportRenderEvent with render_failed
 */
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ForecastVisualizationPage } from '../../../pages/ForecastVisualizationPage';

vi.mock('../components/ForecastVisualizationChart', () => ({
  ForecastVisualizationChart: () => {
    throw new Error('Chart crash');
  },
}));

const categoriesPayload = { forecastProduct: 'daily_1_day', categories: ['Roads'] };
const successPayload = {
  visualizationLoadId: 'load-crash',
  forecastProduct: 'daily_1_day',
  forecastGranularity: 'daily',
  categoryFilter: { selectedCategory: 'Roads', selectedCategories: ['Roads'] },
  historyWindowStart: '2026-03-13T00:00:00Z',
  historyWindowEnd: '2026-03-20T00:00:00Z',
  forecastWindowStart: '2026-03-20T00:00:00Z',
  forecastWindowEnd: '2026-03-21T00:00:00Z',
  lastUpdatedAt: '2026-03-20T00:00:00Z',
  historicalSeries: [{ timestamp: '2026-03-19T00:00:00Z', value: 8 }],
  forecastSeries: [{ timestamp: '2026-03-20T00:00:00Z', pointForecast: 10 }],
  uncertaintyBands: { labels: ['P10', 'P90'], points: [{ timestamp: '2026-03-20T00:00:00Z', p10: 8, p50: 10, p90: 12 }] },
  alerts: [],
  pipelineStatus: [],
  viewStatus: 'success',
};

describe('ForecastVisualizationPage – chart crash', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('calls reportRenderEvent with render_failed when chart throws (handleRenderFailure)', async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(categoriesPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(successPayload), { status: 200 }))
      .mockResolvedValue(new Response(null, { status: 202 }));

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(<ForecastVisualizationPage />);
    await screen.findByText(/couldn't display the chart/i);

    await waitFor(() => {
      const calls = fetchMock.mock.calls.map((c) => String(c[0]));
      expect(calls.some((url) => url.includes('/render-events'))).toBe(true);
    });

    consoleSpy.mockRestore();
  });
});
