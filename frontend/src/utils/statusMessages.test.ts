import { describe, expect, it } from 'vitest';
import type { ForecastVisualization } from '../types/forecastVisualization';
import { buildStatusSummary, groupStatusMessages } from './statusMessages';

const baseVisualization: ForecastVisualization = {
  visualizationLoadId: 'load-1',
  forecastProduct: 'daily_1_day',
  forecastGranularity: 'hourly',
  categoryFilter: { selectedCategory: 'Roads', selectedCategories: ['Roads'] },
  historyWindowStart: '2026-03-13T00:00:00Z',
  historyWindowEnd: '2026-03-20T00:00:00Z',
  historicalSeries: [],
  forecastSeries: [],
  alerts: [],
  pipelineStatus: [],
  viewStatus: 'success',
};

describe('statusMessages', () => {
  it('appends neutral confidence copy for signals-missing and dismissed states', () => {
    expect(buildStatusSummary({
      ...baseVisualization,
      forecastConfidence: {
        assessmentStatus: 'signals_missing',
        indicatorState: 'not_required',
        reasonCategories: [],
        supportingSignals: ['signal'],
        message: 'Confidence signals are unavailable right now.',
      },
    })).toContain('Confidence signals are unavailable right now.');

    expect(buildStatusSummary({
      ...baseVisualization,
      forecastConfidence: {
        assessmentStatus: 'dismissed',
        indicatorState: 'not_required',
        reasonCategories: ['anomaly'],
        supportingSignals: ['signal'],
        message: 'Warnings were reviewed and dismissed.',
      },
    })).toContain('Warnings were reviewed and dismissed.');
  });

  it('preserves fallback, unavailable, degraded, and normal summaries', () => {
    expect(buildStatusSummary({ ...baseVisualization, viewStatus: 'fallback_shown' })).toContain('most recent saved view');
    expect(buildStatusSummary({ ...baseVisualization, viewStatus: 'unavailable', summary: 'Unavailable now.' })).toBe('Unavailable now.');
    expect(buildStatusSummary({ ...baseVisualization, degradationType: 'history_missing', viewStatus: 'degraded' })).toContain('Recent history');
    expect(buildStatusSummary(baseVisualization)).toContain('latest forecast');
  });

  it('groups status messages by level', () => {
    const grouped = groupStatusMessages([
      { code: 'a', level: 'info', message: 'Info' },
      { code: 'b', level: 'warning', message: 'Warn' },
      { code: 'c', level: 'error', message: 'Error' },
    ]);

    expect(grouped.info).toHaveLength(1);
    expect(grouped.warning).toHaveLength(1);
    expect(grouped.error).toHaveLength(1);
  });
});
