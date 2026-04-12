import { fireEvent, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { ForecastAccuracyFilters } from '../components/ForecastAccuracyFilters';

describe('ForecastAccuracyFilters extra coverage', () => {
  it('handles date changes, selecting all categories, and outside clicks', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    const onSubmit = vi.fn();

    render(
      <ForecastAccuracyFilters
        filters={{
          timeRangeStart: '2026-03-01T00:00:00.000Z',
          timeRangeEnd: '2026-03-10T23:59:59.000Z',
          serviceCategory: 'Roads',
        }}
        serviceCategoryOptions={['Roads', 'Waste']}
        onChange={onChange}
        onSubmit={onSubmit}
      />,
    );

    await user.clear(screen.getByLabelText(/^start$/i));
    expect(onChange).toHaveBeenCalledWith({
      timeRangeStart: undefined,
      timeRangeEnd: '2026-03-10T23:59:59.000Z',
      serviceCategory: 'Roads',
    });

    await user.clear(screen.getByLabelText(/^end$/i));
    expect(onChange).toHaveBeenCalledWith({
      timeRangeStart: '2026-03-01T00:00:00.000Z',
      timeRangeEnd: undefined,
      serviceCategory: 'Roads',
    });

    await user.click(screen.getByRole('button', { name: /^service category$/i }));
    expect(screen.getByRole('listbox', { name: /^service category$/i })).toBeInTheDocument();

    fireEvent.mouseDown(document.body);
    expect(screen.queryByRole('listbox', { name: /^service category$/i })).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /^service category$/i }));
    await user.click(screen.getByRole('button', { name: /all categories/i }));

    expect(onChange).toHaveBeenCalledWith({
      timeRangeStart: '2026-03-01T00:00:00.000Z',
      timeRangeEnd: '2026-03-10T23:59:59.000Z',
      serviceCategory: undefined,
    });

    await user.click(screen.getByRole('button', { name: /load accuracy/i }));
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });
});
