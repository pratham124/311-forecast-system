import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { Select } from './select';

afterEach(() => {
  cleanup();
});

describe('Select', () => {
  it('ignores non-option children when building options', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();

    render(
      <Select value="roads" onChange={onChange} name="serviceCategory">
        <option value="roads">Roads</option>
        <div>ignored child</div>
        <option value="waste">Waste</option>
      </Select>,
    );

    await user.click(screen.getByRole('button', { name: /roads/i }));
    expect(screen.getAllByRole('option')).toHaveLength(2);

    await user.click(screen.getByRole('option', { name: /waste/i }));
    expect(onChange).toHaveBeenCalledWith({ target: { value: 'waste', name: 'serviceCategory' } });
  });

  it('falls back to the first option when the current value does not match', () => {
    render(
      <Select value="missing">
        <option value="roads">Roads</option>
        <option value="waste">Waste</option>
      </Select>,
    );

    expect(screen.getByText('Roads')).toBeInTheDocument();
  });

  it('shows the generic placeholder when no options exist', () => {
    render(<Select value="missing" />);
    expect(screen.getByRole('button', { name: /select\.\.\./i })).toBeInTheDocument();
  });
});
