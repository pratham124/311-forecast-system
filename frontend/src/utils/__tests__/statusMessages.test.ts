import { describe, expect, it } from 'vitest';
import { buildStatusSummary, groupStatusMessages } from '../statusMessages';
import type { ForecastVisualization } from '../../types/forecastVisualization';

function makeVisualization(overrides: Partial<ForecastVisualization>): ForecastVisualization {
  return {
    visualizationLoadId: 'v1',
    forecastProduct: 'daily_1_day',
    forecastGranularity: 'daily',
    categoryFilter: { selectedCategory: null, selectedCategories: [] },
    historyWindowStart: '2026-03-01T00:00:00Z',
    historyWindowEnd: '2026-03-31T23:59:59Z',
    alerts: [],
    pipelineStatus: [],
    viewStatus: 'success',
    historicalSeries: [],
    forecastSeries: [],
    ...overrides,
  } as ForecastVisualization;
}

describe('buildStatusSummary', () => {
  it('returns fallback copy for fallback_shown', () => {
    const result = buildStatusSummary(makeVisualization({ viewStatus: 'fallback_shown' }));
    expect(result).toMatch(/most recent saved view/i);
  });

  it('returns unavailable copy for unavailable without summary', () => {
    const result = buildStatusSummary(makeVisualization({ viewStatus: 'unavailable' }));
    expect(result).toMatch(/can't show/i);
  });

  it('returns custom summary for unavailable with summary', () => {
    const result = buildStatusSummary(makeVisualization({ viewStatus: 'unavailable', summary: 'Custom message' }));
    expect(result).toBe('Custom message');
  });

  it('returns degradation copy for history_missing', () => {
    const result = buildStatusSummary(makeVisualization({ viewStatus: 'degraded', degradationType: 'history_missing' }));
    expect(result).toMatch(/history is not available/i);
  });

  it('returns degradation copy for uncertainty_missing', () => {
    const result = buildStatusSummary(makeVisualization({ viewStatus: 'degraded', degradationType: 'uncertainty_missing' }));
    expect(result).toMatch(/shaded range/i);
  });

  it('returns default live copy', () => {
    const result = buildStatusSummary(makeVisualization({ viewStatus: 'success' }));
    expect(result).toMatch(/latest forecast/i);
  });
});

describe('groupStatusMessages', () => {
  it('groups messages by level', () => {
    const messages = [
      { code: 'i1', level: 'info' as const, message: 'Info message' },
      { code: 'w1', level: 'warning' as const, message: 'Warning message' },
      { code: 'e1', level: 'error' as const, message: 'Error message' },
      { code: 'i2', level: 'info' as const, message: 'Another info' },
    ];
    const result = groupStatusMessages(messages);
    expect(result.info).toHaveLength(2);
    expect(result.warning).toHaveLength(1);
    expect(result.error).toHaveLength(1);
  });
});
