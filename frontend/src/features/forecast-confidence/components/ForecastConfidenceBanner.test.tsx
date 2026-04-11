import { render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { ForecastConfidenceBanner } from './ForecastConfidenceBanner';

describe('ForecastConfidenceBanner', () => {
  it('renders the warning copy and reports when mounted', async () => {
    const onRendered = vi.fn();

    render(
      <ForecastConfidenceBanner
        confidence={{
          assessmentStatus: 'degraded_confirmed',
          indicatorState: 'display_required',
          reasonCategories: ['anomaly'],
          supportingSignals: ['recent_confirmed_surge'],
          message: 'Forecast confidence is reduced because recent surge conditions were confirmed for the selected service areas.',
        }}
        onRendered={onRendered}
      />,
    );

    expect(screen.getByLabelText(/forecast confidence banner/i)).toBeInTheDocument();
    expect(screen.getByText(/recent surge conditions were confirmed/i)).toBeInTheDocument();
    await waitFor(() => {
      expect(onRendered).toHaveBeenCalledTimes(1);
    });
  });
});
