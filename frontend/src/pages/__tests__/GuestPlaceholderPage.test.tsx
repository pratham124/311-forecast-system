import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { GuestPlaceholderPage } from '../GuestPlaceholderPage';

describe('GuestPlaceholderPage', () => {
  it('renders the placeholder and handles the back action', async () => {
    const user = userEvent.setup();
    const onBack = vi.fn();

    render(<GuestPlaceholderPage onBack={onBack} />);

    expect(screen.getByRole('heading', { name: /guest view/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/guest placeholder page/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /back/i }));
    expect(onBack).toHaveBeenCalledTimes(1);
  });
});
