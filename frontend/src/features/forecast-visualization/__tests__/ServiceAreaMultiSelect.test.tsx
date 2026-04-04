import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { ServiceAreaMultiSelect } from '../components/ServiceAreaMultiSelect';
import { createRef } from 'react';

afterEach(cleanup);

function renderSelect(overrides: Partial<Parameters<typeof ServiceAreaMultiSelect>[0]> = {}) {
  const defaults = {
    options: ['Roads', 'Waste', 'Transit'],
    selectedValues: [],
    onChange: vi.fn(),
    isOpen: true,
    onOpenChange: vi.fn(),
    containerRef: createRef<HTMLDivElement>(),
  };
  return render(<ServiceAreaMultiSelect {...defaults} {...overrides} />);
}

describe('ServiceAreaMultiSelect', () => {
  it('shows "All service areas" when selectedValues is empty', () => {
    renderSelect({ isOpen: false });
    expect(screen.getByText(/all service areas/i)).toBeInTheDocument();
  });

  it('shows individual names for up to 2 selected', () => {
    renderSelect({ selectedValues: ['Roads', 'Waste'], isOpen: false });
    expect(screen.getByText('Roads, Waste')).toBeInTheDocument();
  });

  it('shows count label for more than 2 but not all selected', () => {
    renderSelect({ selectedValues: ['Roads', 'Waste'], options: ['Roads', 'Waste', 'Transit', 'Parks'], isOpen: false });
    expect(screen.getByText('Roads, Waste')).toBeInTheDocument();
  });

  it('shows count label when 3+ items selected but not all', () => {
    renderSelect({ selectedValues: ['Roads', 'Waste', 'Transit'], options: ['Roads', 'Waste', 'Transit', 'Parks'], isOpen: false });
    expect(screen.getByText(/3 service areas selected/i)).toBeInTheDocument();
  });

  it('calls onOpenChange when toggle button clicked', async () => {
    const user = userEvent.setup();
    const onOpenChange = vi.fn();
    renderSelect({ isOpen: false, onOpenChange });
    await user.click(screen.getByRole('button', { name: /service areas|all service areas/i }));
    expect(onOpenChange).toHaveBeenCalledWith(true);
  });

  it('calls onChange with [] when "Clear all" is clicked', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    renderSelect({ selectedValues: ['Roads'], onChange });
    await user.click(screen.getByRole('button', { name: /clear all/i }));
    expect(onChange).toHaveBeenCalledWith([]);
  });

  it('deselects an option by clicking its row', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    renderSelect({ selectedValues: ['Roads', 'Waste'], options: ['Roads', 'Waste'], onChange });
    await user.click(screen.getByRole('button', { name: /Roads Selected/i }));
    expect(onChange).toHaveBeenCalledWith(['Waste']);
  });

  it('selects an option by clicking its row', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    renderSelect({ selectedValues: ['Waste'], options: ['Roads', 'Waste'], onChange });
    await user.click(screen.getByRole('button', { name: /^Roads$/i }));
    expect(onChange).toHaveBeenCalledWith(['Roads', 'Waste']);
  });

  it('calls onChange with [] when "All service areas" is clicked', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    renderSelect({ selectedValues: ['Roads'], onChange });
    await user.click(screen.getByRole('button', { name: /all service areas/i }));
    expect(onChange).toHaveBeenCalledWith([]);
  });

  it('shows "No service areas available" when options is empty', () => {
    renderSelect({ options: [], selectedValues: [] });
    expect(screen.getByText(/no service areas available/i)).toBeInTheDocument();
  });
});
