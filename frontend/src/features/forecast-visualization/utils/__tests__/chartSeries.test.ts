import { describe, expect, it } from 'vitest';
import { computeChartGeometry, linePath } from '../chartSeries';
import type { ForecastVisualization } from '../../../../types/forecastVisualization';

function makeVisualization(overrides: Partial<ForecastVisualization> = {}): ForecastVisualization {
  return {
    visualizationLoadId: 'v1',
    forecastProduct: 'daily_1_day',
    viewStatus: 'live',
    historicalSeries: [
      { timestamp: '2026-03-01T00:00:00Z', value: 10 },
      { timestamp: '2026-03-02T00:00:00Z', value: 20 },
    ],
    forecastSeries: [
      { timestamp: '2026-03-03T00:00:00Z', pointForecast: 15, p10: 10, p90: 20 },
    ],
    statusMessages: [],
    ...overrides,
  } as ForecastVisualization;
}

describe('computeChartGeometry', () => {
  it('returns expected geometry shape for basic visualization', () => {
    const viz = makeVisualization();
    const geometry = computeChartGeometry(viz);

    expect(geometry.width).toBe(960);
    expect(geometry.height).toBe(420);
    expect(geometry.historyLine).toHaveLength(2);
    expect(geometry.forecastLine).toHaveLength(1);
    expect(geometry.bandArea).toBe('');
    expect(geometry.axisTicks).toHaveLength(5);
    expect(geometry.boundaryX).toBeNull();
  });

  it('throws when no timestamps are present', () => {
    const viz = makeVisualization({ historicalSeries: [], forecastSeries: [] });
    expect(() => computeChartGeometry(viz)).toThrow('No chart points available to render.');
  });

  it('computes bandArea when uncertaintyBands are provided', () => {
    const viz = makeVisualization({
      uncertaintyBands: {
        points: [
          { timestamp: '2026-03-03T00:00:00Z', p10: 10, p90: 20 },
          { timestamp: '2026-03-04T00:00:00Z', p10: 12, p90: 22 },
        ],
      },
    });
    const geometry = computeChartGeometry(viz);
    expect(geometry.bandArea).not.toBe('');
    expect(typeof geometry.bandArea).toBe('string');
  });

  it('returns empty string for bandArea when uncertaintyBands has no points', () => {
    const viz = makeVisualization({
      uncertaintyBands: { points: [] },
    });
    const geometry = computeChartGeometry(viz);
    expect(geometry.bandArea).toBe('');
  });

  it('computes boundaryX when forecastBoundary is set', () => {
    const viz = makeVisualization({
      forecastBoundary: '2026-03-03T00:00:00Z',
    });
    const geometry = computeChartGeometry(viz);
    expect(typeof geometry.boundaryX).toBe('number');
    expect(geometry.boundaryX).toBeGreaterThan(0);
  });

  it('correctly scales points within the chart dimensions', () => {
    const viz = makeVisualization();
    const geometry = computeChartGeometry(viz);

    for (const point of geometry.historyLine) {
      expect(point.x).toBeGreaterThanOrEqual(0);
      expect(point.y).toBeGreaterThanOrEqual(0);
      expect(point.x).toBeLessThanOrEqual(960);
      expect(point.y).toBeLessThanOrEqual(420);
    }
  });

  it('handles a single timestamp (minX === maxX)', () => {
    const viz = makeVisualization({
      historicalSeries: [{ timestamp: '2026-03-01T00:00:00Z', value: 5 }],
      forecastSeries: [],
    });
    const geometry = computeChartGeometry(viz);
    expect(geometry.historyLine).toHaveLength(1);
    expect(geometry.axisTicks).toHaveLength(5);
  });
});

describe('linePath', () => {
  it('returns empty string for empty points', () => {
    expect(linePath([])).toBe('');
  });

  it('starts with M for first point', () => {
    const path = linePath([{ x: 10, y: 20 }]);
    expect(path).toBe('M 10 20');
  });

  it('uses L for subsequent points', () => {
    const path = linePath([
      { x: 10, y: 20 },
      { x: 30, y: 40 },
      { x: 50, y: 60 },
    ]);
    expect(path).toBe('M 10 20 L 30 40 L 50 60');
  });
});
