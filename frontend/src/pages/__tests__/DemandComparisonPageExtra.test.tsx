/**
 * Extra coverage for DemandComparisonPage: onAutoSelect callback (lines 73-74).
 */
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { DemandComparisonPage } from '../DemandComparisonPage';

const availabilityPayload = {
  serviceCategories: ['Roads'],
  byCategoryGeography: {
    Roads: { geographyLevels: ['ward'], geographyOptions: { ward: ['Ward 1'] } },
  },
  dateConstraints: {
    historicalMin: '2026-01-01T00:00:00Z',
    historicalMax: '2026-12-31T00:00:00Z',
    forecastMin: '2026-01-01T00:00:00Z',
    forecastMax: '2026-12-31T00:00:00Z',
    overlapStart: '2026-01-01T00:00:00Z',
    overlapEnd: '2026-12-31T00:00:00Z',
  },
  presets: [
    { label: 'Overlap window', timeRangeStart: '2026-01-01T00:00:00Z', timeRangeEnd: '2026-12-31T00:00:00Z' },
  ],
  forecastProduct: 'daily_1_day',
};

const successPayload = {
  comparisonRequestId: 'cmp-auto',
  filters: {
    serviceCategories: ['Roads'],
    geographyLevel: 'ward',
    geographyValues: ['Ward 1'],
    timeRangeStart: '2026-01-01T00:00:00Z',
    timeRangeEnd: '2026-12-31T00:00:00Z',
  },
  outcomeStatus: 'success',
  resultMode: 'chart_and_table',
  comparisonGranularity: 'daily',
  series: [],
  message: 'Comparison completed.',
};

describe('DemandComparisonPage – auto-select path', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('triggers auto-select when the auto-select button is clicked', async () => {
    const user = userEvent.setup();
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(availabilityPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(successPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ comparisonRequestId: 'cmp-auto', recordedOutcomeStatus: 'rendered' }), { status: 202 }));

    render(<DemandComparisonPage />);
    await screen.findByRole('button', { name: /auto-select/i });

    await user.click(screen.getByRole('button', { name: /auto-select/i }));

    // After auto-select, the comparison query is submitted
    await screen.findByText(/Comparison completed/i);
  });
});
