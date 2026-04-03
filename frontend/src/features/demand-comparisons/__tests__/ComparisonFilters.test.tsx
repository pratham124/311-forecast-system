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

  it('shows only categories first and allows compare when all categories are implied', () => {
    render(
      <ComparisonFilters
        availability={availability}
        filters={baseFilters}
        onChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    expect(screen.getByLabelText('Service categories')).toBeInTheDocument();
    expect(screen.queryByLabelText('Geography level')).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Compare demand' })).toBeEnabled();
  });

  it('renders safely when availability is null', () => {
    render(
      <ComparisonFilters
        availability={null}
        filters={baseFilters}
        onChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    expect(screen.getByLabelText('Service categories')).toBeInTheDocument();
  });

  it('does not show geography controls', () => {
    render(
      <ComparisonFilters
        availability={availability}
        filters={{ ...baseFilters, serviceCategories: ['Roads'] }}
        onChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    expect(screen.queryByLabelText('Geography level')).not.toBeInTheDocument();
    expect(screen.queryByLabelText('Geography values')).not.toBeInTheDocument();
  });

  it('emits changes for categories, geography, and date controls', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();

    render(
      <ComparisonFilters
        availability={availability}
        filters={{ ...baseFilters, serviceCategories: ['Roads'] }}
        onChange={onChange}
        onSubmit={vi.fn()}
      />,
    );

    await user.click(screen.getByLabelText('Service categories'));
    await user.click(screen.getByRole('button', { name: 'Waste' }));
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ serviceCategories: ['Roads', 'Waste'] }),
    );

    fireEvent.change(screen.getByLabelText('Start'), { target: { value: '2026-03-03' } });
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ timeRangeStart: '2026-03-03T07:00:00Z' }),
    );

    fireEvent.change(screen.getByLabelText('End'), { target: { value: '2026-03-04' } });
    expect(onChange).toHaveBeenCalledWith(
      expect.objectContaining({ timeRangeEnd: '2026-03-05T06:59:59Z' }),
    );
  });

  it('does not render quick presets or auto-select controls', () => {
    render(
      <ComparisonFilters
        availability={availability}
        filters={baseFilters}
        onChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    expect(screen.queryByText('Quick presets')).not.toBeInTheDocument();
    expect(screen.queryByText(/Auto-select forecast-backed combination/i)).not.toBeInTheDocument();
  });

  it('shows date-range error and disables submit', () => {
    render(
      <ComparisonFilters
        availability={availability}
        filters={{ ...baseFilters, serviceCategories: ['Roads'] }}
        dateRangeError="End date is outside the available comparison window."
        onChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    expect(screen.getByText('End date is outside the available comparison window.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Compare demand' })).toBeDisabled();
  });
});
