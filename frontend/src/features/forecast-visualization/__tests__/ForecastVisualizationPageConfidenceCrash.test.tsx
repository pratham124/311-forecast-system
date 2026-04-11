/**
 * Tests ForecastVisualizationPage when the confidence banner throws during render.
 * vi.mock must be at module level — kept separate from the non-mocked page tests.
 */
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ForecastVisualizationPage } from '../../../pages/ForecastVisualizationPage';

vi.mock('../../forecast-confidence/components/ForecastConfidenceBanner', () => ({
  ForecastConfidenceBanner: () => {
    throw new Error('Confidence banner crash');
  },
}));

const categoriesPayload = { forecastProduct: 'daily_1_day', categories: ['Roads'] };
const confidencePayload = {
  visualizationLoadId: 'load-confidence',
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
  forecastConfidence: {
    assessmentStatus: 'degraded_confirmed',
    indicatorState: 'display_required',
    reasonCategories: ['anomaly'],
    supportingSignals: ['recent_confirmed_surge'],
    message: 'Forecast confidence is reduced because recent surge conditions were confirmed for the selected service areas.',
  },
  viewStatus: 'success',
};

describe('ForecastVisualizationPage – confidence banner crash', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('records a confidence render failure while keeping the chart visible', async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(categoriesPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(confidencePayload), { status: 200 }))
      .mockResolvedValue(new Response(null, { status: 202 }));

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    render(<ForecastVisualizationPage />);

    expect(await screen.findByRole('img', { name: /demand forecast chart/i })).toBeInTheDocument();

    await waitFor(() => {
      const calls = fetchMock.mock.calls.map((c) => String(c[0]));
      expect(calls.some((url) => url.includes('/confidence-render-events'))).toBe(true);
    });

    consoleSpy.mockRestore();
  });
});
