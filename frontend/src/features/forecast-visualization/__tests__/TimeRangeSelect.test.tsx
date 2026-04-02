import { cleanup, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { TimeRangeSelect } from '../components/TimeRangeSelect';
import { createRef } from 'react';

afterEach(cleanup);

describe('TimeRangeSelect', () => {
  it('renders the button with the selected label when closed', () => {
    render(
      <TimeRangeSelect
        value="daily_1_day"
        onChange={vi.fn()}
        isOpen={false}
        onOpenChange={vi.fn()}
        containerRef={createRef()}
      />,
    );
    expect(screen.getByRole('button', { name: /next 24 hours/i })).toBeInTheDocument();
    expect(screen.queryByRole('listbox')).not.toBeInTheDocument();
  });

  it('shows the dropdown when isOpen is true', () => {
    render(
      <TimeRangeSelect
        value="daily_1_day"
        onChange={vi.fn()}
        isOpen={true}
        onOpenChange={vi.fn()}
        containerRef={createRef()}
      />,
    );
    expect(screen.getByRole('listbox')).toBeInTheDocument();
    expect(screen.getAllByRole('button')).toHaveLength(3); // toggle + 2 options
  });

  it('calls onOpenChange when the toggle button is clicked', async () => {
    const user = userEvent.setup();
    const onOpenChange = vi.fn();
    render(
      <TimeRangeSelect
        value="daily_1_day"
        onChange={vi.fn()}
        isOpen={false}
        onOpenChange={onOpenChange}
        containerRef={createRef()}
      />,
    );
    await user.click(screen.getByRole('button', { name: /next 24 hours/i }));
    expect(onOpenChange).toHaveBeenCalledWith(true);
  });

  it('calls onChange with the selected value and closes the dropdown', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    const onOpenChange = vi.fn();
    render(
      <TimeRangeSelect
        value="daily_1_day"
        onChange={onChange}
        isOpen={true}
        onOpenChange={onOpenChange}
        containerRef={createRef()}
      />,
    );
    await user.click(screen.getByRole('button', { name: /next 7 days/i }));
    expect(onChange).toHaveBeenCalledWith('weekly_7_day');
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it('shows fallback label when value does not match any option', () => {
    render(
      <TimeRangeSelect
        value={'unknown_product' as any}
        onChange={vi.fn()}
        isOpen={false}
        onOpenChange={vi.fn()}
        containerRef={createRef()}
      />,
    );
    // 'Select time range' is the ?? fallback when OPTIONS.find returns undefined
    expect(screen.getByRole('button', { name: /select time range/i })).toBeInTheDocument();
  });

  it('marks the currently selected option as pressed', () => {
    render(
      <TimeRangeSelect
        value="weekly_7_day"
        onChange={vi.fn()}
        isOpen={true}
        onOpenChange={vi.fn()}
        containerRef={createRef()}
      />,
    );
    const listbox = screen.getByRole('listbox');
    const weeklyBtn = within(listbox).getByRole('button', { name: /next 7 days/i });
    expect(weeklyBtn).toHaveAttribute('aria-pressed', 'true');
    const dailyBtn = within(listbox).getByRole('button', { name: /next 24 hours/i });
    expect(dailyBtn).toHaveAttribute('aria-pressed', 'false');
  });
});
