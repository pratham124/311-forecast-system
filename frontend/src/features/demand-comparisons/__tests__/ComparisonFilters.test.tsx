import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ComparisonFilters } from '../components/ComparisonFilters';
import type { DemandComparisonAvailability, DemandComparisonFilters } from '../../../types/demandComparisons';

const availability: DemandComparisonAvailability = {
  serviceCategories: ['Roads', 'Waste'],
  byCategoryGeography: {
    Roads: {
      geographyLevels: ['ward'],
      geographyOptions: {
        ward: ['Ward 1', 'Ward 2'],
      },
    },
    Waste: {
      geographyLevels: ['ward'],
      geographyOptions: {
        ward: ['Ward 1'],
      },
    },
  },
  dateConstraints: {
    overlapStart: '2026-03-02T00:00:00Z',
    overlapEnd: '2026-03-05T00:00:00Z',
  },
  presets: [
    {
      label: 'Overlap window',
      timeRangeStart: '2026-03-02T00:00:00Z',
      timeRangeEnd: '2026-03-05T00:00:00Z',
    },
  ],
  forecastProduct: 'daily_1_day',
};

const baseFilters: DemandComparisonFilters = {
  serviceCategories: [],
  geographyValues: [],
  timeRangeStart: '2026-03-02T00:00:00Z',
  timeRangeEnd: '2026-03-03T00:00:00Z',
};

describe('ComparisonFilters', () => {
  afterEach(() => {
    cleanup();
  });

  it('shows only categories first and keeps compare disabled with no selection', () => {
    render(
      <ComparisonFilters
        availability={availability}
        filters={baseFilters}
        availableGeographyLevels={[]}
        availableGeographyValues={[]}
        onChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    expect(screen.getByLabelText('Service categories')).toBeInTheDocument();
    expect(screen.queryByLabelText('Geography level')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Compare demand' })).toBeDisabled();
  });

  it('renders safely when availability is null', () => {
    render(
      <ComparisonFilters
        availability={null}
        filters={baseFilters}
        availableGeographyLevels={[]}
        availableGeographyValues={[]}
        onChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    expect(screen.getByLabelText('Service categories')).toBeInTheDocument();
  });

  it('reveals geography controls progressively', () => {
    const filtersWithCategory: DemandComparisonFilters = {
      ...baseFilters,
      serviceCategories: ['Roads'],
    };
    const { rerender } = render(
      <ComparisonFilters
        availability={availability}
        filters={filtersWithCategory}
        availableGeographyLevels={['ward']}
        availableGeographyValues={[]}
        onChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    expect(screen.getByLabelText('Geography level')).toBeInTheDocument();
    expect(screen.queryByLabelText('Geography values')).not.toBeInTheDocument();

    rerender(
      <ComparisonFilters
        availability={availability}
        filters={{ ...filtersWithCategory, geographyLevel: 'ward' }}
        availableGeographyLevels={['ward']}
        availableGeographyValues={['Ward 1']}
        onChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    expect(screen.getByLabelText('Geography values')).toBeInTheDocument();
  });

  it('emits changes for categories, geography, and date controls', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();

    render(
      <ComparisonFilters
        availability={availability}
        filters={{ ...baseFilters, serviceCategories: ['Roads'], geographyLevel: 'ward' }}
        availableGeographyLevels={['ward']}
        availableGeographyValues={['Ward 1', 'Ward 2']}
        onChange={onChange}
        onSubmit={vi.fn()}
      />,
    );

    await user.selectOptions(screen.getByLabelText('Service categories'), ['Waste']);
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ serviceCategories: ['Roads', 'Waste'] }),
    );

    await user.selectOptions(screen.getByLabelText('Geography values'), ['Ward 2']);
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ geographyValues: ['Ward 2'] }),
    );

    fireEvent.change(screen.getByLabelText('Start'), { target: { value: '2026-03-03T00:00' } });
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ timeRangeStart: new Date('2026-03-03T00:00').toISOString() }),
    );

    fireEvent.change(screen.getByLabelText('Geography level'), { target: { value: '' } });
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ geographyLevel: undefined, geographyValues: [] }),
    );

    fireEvent.change(screen.getByLabelText('End'), { target: { value: '2026-03-04T00:00' } });
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ timeRangeEnd: new Date('2026-03-04T00:00').toISOString() }),
    );
  });

  it('applies backend presets through callback', async () => {
    const user = userEvent.setup();
    const onApplyDatePreset = vi.fn();

    render(
      <ComparisonFilters
        availability={availability}
        filters={baseFilters}
        availableGeographyLevels={[]}
        availableGeographyValues={[]}
        datePresets={availability.presets}
        onApplyDatePreset={onApplyDatePreset}
        onChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    await user.click(screen.getByRole('button', { name: 'Overlap window' }));
    expect(onApplyDatePreset).toHaveBeenCalledWith(availability.presets[0]);
  });

  it('shows applied preset state when current dates match a preset', () => {
    render(
      <ComparisonFilters
        availability={availability}
        filters={{
          ...baseFilters,
          timeRangeStart: availability.presets[0].timeRangeStart,
          timeRangeEnd: availability.presets[0].timeRangeEnd,
        }}
        availableGeographyLevels={[]}
        availableGeographyValues={[]}
        datePresets={availability.presets}
        onApplyDatePreset={vi.fn()}
        onChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    expect(screen.getByText('Applied preset: Overlap window')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Overlap window' })).toHaveAttribute('aria-pressed', 'true');
  });

  it('shows date-range error and disables submit', () => {
    render(
      <ComparisonFilters
        availability={availability}
        filters={{ ...baseFilters, serviceCategories: ['Roads'] }}
        availableGeographyLevels={['ward']}
        availableGeographyValues={['Ward 1']}
        dateRangeError="End date is outside the available comparison window."
        onChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    expect(screen.getByText('End date is outside the available comparison window.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Compare demand' })).toBeDisabled();
  });
});
