import React from 'react';
import { render, screen, fireEvent, cleanup } from '@testing-library/react';
import { describe, it, expect, vi, afterEach } from 'vitest';
import { ComparisonFilters } from '../components/ComparisonFilters';
import type { DemandComparisonContext, DemandComparisonFilters } from '../../../types/demandComparisons';

describe('ComparisonFilters', () => {
  afterEach(() => {
    cleanup();
  });

  const mockContext: DemandComparisonContext = {
    serviceCategories: ['Category A', 'Category B'],
    geographyLevels: ['borocd', 'precinct'],
    geographyOptions: {
      borocd: ['Bronx 1', 'Bronx 2'],
      precinct: ['001', '002']
    }
  };

  const defaultFilters: DemandComparisonFilters = {
    serviceCategories: [],
    geographyValues: [],
    timeRangeStart: '2023-01-01T00:00:00.000Z',
    timeRangeEnd: '2023-01-08T00:00:00.000Z'
  };

  it('renders with empty context and disabled state', () => {
    const onChange = vi.fn();
    const onSubmit = vi.fn();
    render(<ComparisonFilters context={null} filters={defaultFilters} onChange={onChange} onSubmit={onSubmit} disabled={true} />);
    expect(screen.getByText('Service categories')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Compare demand' })).toBeDisabled();
  });

  it('toggles service categories correctly', () => {
    const onChange = vi.fn();
    const onSubmit = vi.fn();
    const { rerender } = render(
      <ComparisonFilters context={mockContext} filters={defaultFilters} onChange={onChange} onSubmit={onSubmit} />
    );

    // Initial click -> add
    const btnA = screen.getByRole('button', { name: 'Category A' });
    fireEvent.click(btnA);
    expect(onChange).toHaveBeenCalledWith({ ...defaultFilters, serviceCategories: ['Category A'] });

    // Rerender with Category A checked to test unchecking
    rerender(
      <ComparisonFilters context={mockContext} filters={{ ...defaultFilters, serviceCategories: ['Category A', 'Category B'] }} onChange={onChange} onSubmit={onSubmit} />
    );
    const btnAChecked = screen.getByRole('button', { name: 'Category A' });
    fireEvent.click(btnAChecked);
    expect(onChange).toHaveBeenCalledWith({ ...defaultFilters, serviceCategories: ['Category B'] });
  });

  it('handles geography level changes', () => {
    const onChange = vi.fn();
    render(<ComparisonFilters context={mockContext} filters={defaultFilters} onChange={onChange} onSubmit={vi.fn()} />);

    const select = screen.getByLabelText('Geography level');
    fireEvent.change(select, { target: { value: 'borocd' } });
    expect(onChange).toHaveBeenCalledWith({ ...defaultFilters, geographyLevel: 'borocd', geographyValues: [] });

    fireEvent.change(select, { target: { value: '' } });
    expect(onChange).toHaveBeenCalledWith({ ...defaultFilters, geographyLevel: undefined, geographyValues: [] });
  });

  it('toggles geography values correctly when level is selected', () => {
    const onChange = vi.fn();
    const filtersWithGeo: DemandComparisonFilters = { ...defaultFilters, geographyLevel: 'borocd' };
    const { rerender } = render(
      <ComparisonFilters context={mockContext} filters={filtersWithGeo} onChange={onChange} onSubmit={vi.fn()} />
    );

    const btnBronx1 = screen.getByRole('button', { name: 'Bronx 1' });
    fireEvent.click(btnBronx1);
    expect(onChange).toHaveBeenCalledWith({ ...filtersWithGeo, geographyValues: ['Bronx 1'] });

    rerender(
      <ComparisonFilters context={mockContext} filters={{ ...filtersWithGeo, geographyValues: ['Bronx 1', 'Bronx 2'] }} onChange={onChange} onSubmit={vi.fn()} />
    );
    const btnBronx1Checked = screen.getByRole('button', { name: 'Bronx 1' });
    fireEvent.click(btnBronx1Checked);
    expect(onChange).toHaveBeenCalledWith({ ...filtersWithGeo, geographyValues: ['Bronx 2'] });
  });

  it('handles date range changes', () => {
    const onChange = vi.fn();
    render(<ComparisonFilters context={mockContext} filters={defaultFilters} onChange={onChange} onSubmit={vi.fn()} />);

    const startInput = screen.getByLabelText('Start');
    fireEvent.change(startInput, { target: { value: '2023-01-02T10:00' } });
    expect(onChange).toHaveBeenCalledWith({ ...defaultFilters, timeRangeStart: new Date('2023-01-02T10:00').toISOString() });

    const endInput = screen.getByLabelText('End');
    fireEvent.change(endInput, { target: { value: '2023-01-09T10:00' } });
    expect(onChange).toHaveBeenCalledWith({ ...defaultFilters, timeRangeEnd: new Date('2023-01-09T10:00').toISOString() });
  });

  it('submits correctly', () => {
    const onSubmit = vi.fn();
    render(<ComparisonFilters context={mockContext} filters={{ ...defaultFilters, serviceCategories: ['A'] }} onChange={vi.fn()} onSubmit={onSubmit} />);

    const submitBtn = screen.getByRole('button', { name: 'Compare demand' });
    expect(submitBtn).not.toBeDisabled();
    fireEvent.click(submitBtn);
    expect(onSubmit).toHaveBeenCalled();
  });
});