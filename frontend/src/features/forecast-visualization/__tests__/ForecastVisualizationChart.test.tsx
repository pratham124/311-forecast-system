import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ForecastVisualizationChart } from '../components/ForecastVisualizationChart';
import type { ForecastVisualization } from '../../../types/forecastVisualization';

const visualization: ForecastVisualization = {
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
  historicalSeries: [
    { timestamp: '2026-03-18T00:00:00Z', value: 7 },
    { timestamp: '2026-03-19T00:00:00Z', value: 9 },
  ],
  forecastSeries: [
    { timestamp: '2026-03-20T00:00:00Z', pointForecast: 10 },
    { timestamp: '2026-03-20T06:00:00Z', pointForecast: 12 },
  ],
  uncertaintyBands: {
    labels: ['P10', 'P50', 'P90'],
    points: [
      { timestamp: '2026-03-20T00:00:00Z', p10: 8, p50: 10, p90: 13 },
      { timestamp: '2026-03-20T06:00:00Z', p10: 9, p50: 12, p90: 15 },
    ],
  },
  alerts: [],
  pipelineStatus: [],
  viewStatus: 'success',
};

describe('ForecastVisualizationChart', () => {
  it('renders the chart and legend', () => {
    render(<ForecastVisualizationChart visualization={visualization} />);
    expect(screen.getByRole('img', { name: /demand forecast chart/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/chart legend/i)).toHaveTextContent('Recent demand');
    expect(screen.getByLabelText(/chart legend/i)).toHaveTextContent('Forecast');
    expect(screen.getByLabelText(/chart legend/i)).toHaveTextContent('Range');
  });
});
