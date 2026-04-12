import { act, render, renderHook, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../../api/publicForecastApi', () => ({
  fetchCurrentPublicForecast: vi.fn(),
  submitPublicForecastDisplayEvent: vi.fn(),
}));

import { fetchCurrentPublicForecast, submitPublicForecastDisplayEvent } from '../../../api/publicForecastApi';
import { PublicForecastCoverageNotice } from '../components/PublicForecastCoverageNotice';
import { PublicForecastView } from '../components/PublicForecastView';
import { usePublicForecast } from '../hooks/usePublicForecast';

describe('Public forecast extra coverage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders null coverage notice as empty and sorts/prints public forecast fallbacks', () => {
    const emptyNotice = render(<PublicForecastCoverageNotice />);
    expect(emptyNotice.container).toBeEmptyDOMElement();

    render(
      <PublicForecastView
        sortOrder="asc"
        forecast={{
          forecastWindowLabel: '2026-04-01 to 2026-04-02',
          publishedAt: null,
          coverageStatus: 'complete',
          categorySummaries: [
            { serviceCategory: 'Waste', forecastDemandValue: null, demandLevelSummary: null },
            { serviceCategory: 'Roads', forecastDemandValue: 5, demandLevelSummary: 'Busy' },
            { serviceCategory: 'Transit', forecastDemandValue: 5, demandLevelSummary: 'Also busy' },
          ],
        } as never}
      />,
    );

    expect(screen.getByText(/not available/i)).toBeInTheDocument();
    expect(screen.getByText(/public-safe demand summary available\./i)).toBeInTheDocument();
    expect(screen.getAllByRole('heading', { level: 2 }).map((node) => node.textContent)).toEqual([
      'Roads',
      'Transit',
      'Waste',
    ]);
    expect(screen.getByText('N/A')).toBeInTheDocument();
  });

  it('handles request failures and deduplicates display events', async () => {
    vi.mocked(fetchCurrentPublicForecast)
      .mockRejectedValueOnce(new Error('public failed'))
      .mockResolvedValueOnce({ publicForecastRequestId: 'public-1', status: 'available' } as never);

    const { result, rerender } = renderHook(() => usePublicForecast());

    await waitFor(() => {
      expect(result.current.error).toBe('public failed');
    });

    act(() => {
      result.current.setForecastProduct('weekly');
    });

    rerender();
    await waitFor(() => {
      expect(result.current.forecast?.publicForecastRequestId).toBe('public-1');
    });

    await act(async () => {
      await result.current.reportDisplayEvent({ displayOutcome: 'rendered' } as never);
      await result.current.reportDisplayEvent({ displayOutcome: 'rendered' } as never);
      await result.current.reportDisplayEvent({ displayOutcome: 'render_failed', failureReason: 'boom' } as never);
    });

    expect(submitPublicForecastDisplayEvent).toHaveBeenCalledTimes(2);
  });

  it('returns early when reporting without a forecast', async () => {
    vi.mocked(fetchCurrentPublicForecast).mockResolvedValue({ publicForecastRequestId: 'public-2', status: 'available' } as never);
    const { result } = renderHook(() => usePublicForecast());

    await act(async () => {
      await result.current.reportDisplayEvent({ displayOutcome: 'rendered' } as never);
    });

    expect(submitPublicForecastDisplayEvent).not.toHaveBeenCalled();
  });
});
