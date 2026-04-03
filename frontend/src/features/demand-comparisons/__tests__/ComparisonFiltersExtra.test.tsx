/**
 * Extra coverage for ComparisonFilters – NaN date handling and simplified UI state.
 */
import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ComparisonFilters } from '../components/ComparisonFilters';
import type { DemandComparisonAvailability, DemandComparisonFilters } from '../../../types/demandComparisons';

const availability: DemandComparisonAvailability = {
  serviceCategories: ['Roads'],
  byCategoryGeography: {
    Roads: { geographyLevels: ['ward'], geographyOptions: { ward: ['Ward 1'] } },
  },
  dateConstraints: {},
  presets: [],
};

const baseFilters: DemandComparisonFilters = {
  serviceCategories: ['Roads'],
  geographyValues: [],
  timeRangeStart: '2026-03-02T00:00:00Z',
  timeRangeEnd: '2026-03-05T00:00:00Z',
};

function renderFilters(overrides: Partial<Parameters<typeof ComparisonFilters>[0]> = {}) {
  return render(
    <ComparisonFilters
      availability={availability}
      filters={baseFilters}
      onChange={vi.fn()}
      onSubmit={vi.fn()}
      {...overrides}
    />,
  );
}

afterEach(cleanup);

describe('ComparisonFilters – date helper edge cases', () => {
  it('renders with invalid timeRangeStart without crashing (NaN date in toDateTimeLocalValue)', () => {
    renderFilters({
      filters: { ...baseFilters, timeRangeStart: 'not-a-date', timeRangeEnd: 'also-not-a-date' },
    });
    // Component should still render the submit button
    expect(screen.getByRole('button', { name: /compare demand/i })).toBeInTheDocument();
  });

  it('does not render quick presets when they are omitted from the UI', () => {
    renderFilters({
      filters: { ...baseFilters, timeRangeStart: '2026-03-02T00:00:00Z', timeRangeEnd: '2026-03-05T00:00:00Z' },
    });
    expect(screen.queryByText('Overlap window')).not.toBeInTheDocument();
    expect(screen.queryByText(/Applied preset/i)).not.toBeInTheDocument();
  });

  it('does not render auto-select controls', () => {
    renderFilters();
    expect(screen.queryByText(/Auto-select forecast-backed combination/i)).not.toBeInTheDocument();
  });

  it('renders safely with invalid dates and no preset UI', () => {
    renderFilters({
      filters: { ...baseFilters, timeRangeStart: 'not-a-date', timeRangeEnd: 'also-not-a-date' },
    });
    expect(screen.queryByText(/Applied preset/i)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /compare demand/i })).toBeInTheDocument();
  });
});
