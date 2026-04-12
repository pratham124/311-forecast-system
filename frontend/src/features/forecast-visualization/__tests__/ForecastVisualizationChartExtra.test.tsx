/**
 * Additional tests for ForecastVisualizationChart to cover remaining branches:
 * - non-hourly granularity (daily label format)
 * - overlapping timestamps between history/forecast and uncertainty bands
 * - missing forecastBoundary (null branch)
 * - invalid/NaN timestamp in formatTick
 */
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import {
  buildChartData,
  ForecastVisualizationChart,
  formatTick,
  formatTooltipLabel,
} from '../components/ForecastVisualizationChart';
import type { ForecastVisualization } from '../../../types/forecastVisualization';

const base: ForecastVisualization = {
  visualizationLoadId: 'load-2',
  forecastProduct: 'weekly_7_day',
  forecastGranularity: 'daily',
  categoryFilter: { selectedCategory: 'Roads', selectedCategories: ['Roads'] },
  historyWindowStart: '2026-03-13T00:00:00Z',
  historyWindowEnd: '2026-03-20T00:00:00Z',
  forecastWindowStart: '2026-03-20T00:00:00Z',
  forecastWindowEnd: '2026-03-27T00:00:00Z',
  lastUpdatedAt: '2026-03-20T00:00:00Z',
  historicalSeries: [
    { timestamp: '2026-03-18T00:00:00Z', value: 7 },
    { timestamp: '2026-03-19T00:00:00Z', value: 9 },
  ],
  forecastSeries: [
    { timestamp: '2026-03-20T00:00:00Z', pointForecast: 10 },
    { timestamp: '2026-03-21T00:00:00Z', pointForecast: 12 },
  ],
  uncertaintyBands: {
    labels: ['P10', 'P50', 'P90'],
    points: [
      { timestamp: '2026-03-20T00:00:00Z', p10: 8, p50: 10, p90: 13 },
      { timestamp: '2026-03-21T00:00:00Z', p10: 9, p50: 12, p90: 15 },
    ],
  },
  alerts: [],
  pipelineStatus: [],
  viewStatus: 'success',
};

afterEach(cleanup);

describe('ForecastVisualizationChart – additional branches', () => {
  it('returns fallback tooltip text for non-string labels', () => {
    expect(formatTooltipLabel('Mar 20')).toBe('Mar 20');
    expect(formatTooltipLabel(42)).toBe('Chart point');
  });

  it('returns the original timestamp when a tick value is invalid', () => {
    expect(formatTick('not-a-date', 'hourly')).toBe('not-a-date');
  });

  it('renders with daily granularity (non-hourly label path)', () => {
    render(<ForecastVisualizationChart visualization={base} />);
    expect(screen.getByRole('img', { name: /demand forecast chart/i })).toBeInTheDocument();
  });

  it('renders without forecastBoundary (null branch in ReferenceLine)', () => {
    const noForecastBoundary = { ...base, forecastBoundary: undefined };
    render(<ForecastVisualizationChart visualization={noForecastBoundary} />);
    expect(screen.getByRole('img', { name: /demand forecast chart/i })).toBeInTheDocument();
  });

  it('renders when uncertainty bands share timestamps with historical series (map merge path)', () => {
    const sharedTimestamps: ForecastVisualization = {
      ...base,
      historicalSeries: [{ timestamp: '2026-03-18T00:00:00Z', value: 7 }],
      forecastSeries: [{ timestamp: '2026-03-20T00:00:00Z', pointForecast: 10 }],
      uncertaintyBands: {
        labels: ['P10', 'P90'],
        points: [
          // Same timestamp as historicalSeries — exercises the map-get-truthy path
          { timestamp: '2026-03-18T00:00:00Z', p10: 5, p50: 7, p90: 9 },
        ],
      },
    };
    render(<ForecastVisualizationChart visualization={sharedTimestamps} />);
    expect(screen.getByRole('img', { name: /demand forecast chart/i })).toBeInTheDocument();
  });

  it('renders when uncertainty bands have timestamps NOT in historical or forecast series (null fallback path, lines 61-63)', () => {
    // When byTimestamp.get(point.timestamp) returns undefined, the ?? fallback
    // creates a new { timestamp, label } object. This covers lines 61-63.
    const novelUncertaintyTimestamp: ForecastVisualization = {
      ...base,
      historicalSeries: [{ timestamp: '2026-03-18T00:00:00Z', value: 7 }],
      forecastSeries: [{ timestamp: '2026-03-20T00:00:00Z', pointForecast: 10 }],
      uncertaintyBands: {
        labels: ['P10', 'P90'],
        points: [
          // NEW timestamp not in historical or forecast → triggers the ?? fallback
          { timestamp: '2026-03-22T00:00:00Z', p10: 5, p50: 7, p90: 9 },
        ],
      },
    };
    render(<ForecastVisualizationChart visualization={novelUncertaintyTimestamp} />);
    expect(screen.getByRole('img', { name: /demand forecast chart/i })).toBeInTheDocument();
  });

  it('builds chart data when uncertainty bands are unavailable', () => {
    const withoutBands: ForecastVisualization = {
      ...base,
      uncertaintyBands: undefined,
    };

    const data = buildChartData(withoutBands);
    expect(data.length).toBeGreaterThan(0);
    expect(data.some((point) => point.p10 !== undefined || point.p90 !== undefined)).toBe(false);
  });

  it('builds overlay points for visible overlays with timestamps outside the base series', () => {
    const data = buildChartData(base, {
      overlayRequestId: 'overlay-1',
      geographyId: 'citywide',
      timeRangeStart: '2026-03-13T00:00:00Z',
      timeRangeEnd: '2026-03-27T00:00:00Z',
      weatherMeasure: 'temperature',
      overlayStatus: 'visible',
      baseForecastPreserved: true,
      userVisible: true,
      observations: [{ timestamp: '2026-03-25T00:00:00Z', value: 4 }],
      stateSource: 'overlay-assembly',
    });

    expect(data.some((point) => point.timestamp === '2026-03-25T00:00:00Z' && point.overlay === 4)).toBe(true);
  });
});
