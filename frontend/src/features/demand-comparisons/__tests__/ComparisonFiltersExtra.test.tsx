/**
 * Extra coverage for ComparisonFilters – NaN date handling in utility functions
 * and the auto-select progress label.
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
      availableGeographyLevels={['ward']}
      availableGeographyValues={['Ward 1']}
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

  it('renders quick presets and selected preset indicator with matching timestamps', () => {
    renderFilters({
      datePresets: [
        { label: 'Overlap window', timeRangeStart: '2026-03-02T00:00:00Z', timeRangeEnd: '2026-03-05T00:00:00Z' },
      ],
      onApplyDatePreset: vi.fn(),
    });
    expect(screen.getByText('Overlap window')).toBeInTheDocument();
    expect(screen.getByText(/Applied preset/i)).toBeInTheDocument();
  });

  it('renders preset button without selected indicator when times differ', () => {
    renderFilters({
      filters: { ...baseFilters, timeRangeStart: '2026-03-02T00:00:00Z', timeRangeEnd: '2026-03-04T00:00:00Z' },
      datePresets: [
        { label: 'Overlap window', timeRangeStart: '2026-03-02T00:00:00Z', timeRangeEnd: '2026-03-05T00:00:00Z' },
      ],
      onApplyDatePreset: vi.fn(),
    });
    expect(screen.queryByText(/Applied preset/i)).not.toBeInTheDocument();
  });

  it('shows auto-select progress text when isAutoSelecting', () => {
    renderFilters({
      onAutoSelect: vi.fn(),
      isAutoSelecting: true,
      autoSelectProgress: { current: 1, total: 3 },
    });
    expect(screen.getByText(/Applying best available combination/i)).toBeInTheDocument();
  });

  it('shows auto-select button label when not selecting', () => {
    renderFilters({ onAutoSelect: vi.fn(), isAutoSelecting: false });
    expect(screen.getByText(/Auto-select forecast-backed combination/i)).toBeInTheDocument();
  });

  it('returns false from isSameInstant when date strings are invalid (NaN path)', () => {
    // isSameInstant is called inside datePresets.find(); to trigger NaN branch,
    // pass invalid date strings AND non-empty datePresets with onApplyDatePreset.
    renderFilters({
      filters: { ...baseFilters, timeRangeStart: 'not-a-date', timeRangeEnd: 'also-not-a-date' },
      datePresets: [
        { label: 'Overlap', timeRangeStart: '2026-03-02T00:00:00Z', timeRangeEnd: '2026-03-05T00:00:00Z' },
      ],
      onApplyDatePreset: vi.fn(),
    });
    // isSameInstant('not-a-date', '2026-03-02T00:00:00Z') → NaN → return false
    // So no preset is selected; 'Applied preset' text should NOT appear
    expect(screen.queryByText(/Applied preset/i)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /compare demand/i })).toBeInTheDocument();
  });
});
