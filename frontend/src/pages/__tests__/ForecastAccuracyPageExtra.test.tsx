import { render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { ForecastAccuracyPage } from '../ForecastAccuracyPage';

const hookState = vi.hoisted(() => ({
  value: {
    filters: {},
    setFilters: vi.fn(),
    serviceCategoryOptions: ['Roads'],
    response: null,
    isLoading: false,
    isSubmitting: false,
    error: null,
    submit: vi.fn(),
    reportRenderEvent: vi.fn(),
  },
}));

vi.mock('../../features/forecast-accuracy/hooks/useForecastAccuracy', () => ({
  useForecastAccuracy: () => hookState.value,
}));

vi.mock('../../features/forecast-accuracy/components/ForecastAccuracyMetrics', () => ({
  ForecastAccuracyMetrics: () => <div>metrics rendered</div>,
}));

vi.mock('../../features/forecast-accuracy/components/ForecastAccuracyMetricsUnavailable', () => ({
  ForecastAccuracyMetricsUnavailable: ({ message }: { message: string }) => <div>{message}</div>,
}));

vi.mock('../../features/forecast-accuracy/components/ForecastAccuracyComparison', () => ({
  ForecastAccuracyComparison: ({ alignedBuckets }: { alignedBuckets: unknown[] }) => {
    if ((alignedBuckets as Array<{ serviceCategory?: string }>)[0]?.serviceCategory === 'Crash') {
      throw new Error('comparison crashed');
    }
    return <div>comparison rendered</div>;
  },
}));

describe('ForecastAccuracyPage extra coverage', () => {
  beforeEach(() => {
    hookState.value = {
      filters: {},
      setFilters: vi.fn(),
      serviceCategoryOptions: ['Roads'],
      response: null,
      isLoading: false,
      isSubmitting: false,
      error: null,
      submit: vi.fn(),
      reportRenderEvent: vi.fn(),
    };
  });

  it('renders loading and request error states', () => {
    hookState.value.isLoading = true;
    hookState.value.error = 'request failed';

    render(<ForecastAccuracyPage />);

    expect(screen.getByText(/loading forecast accuracy/i)).toBeInTheDocument();
    expect(screen.getByText(/forecast accuracy request failed/i)).toBeInTheDocument();
    expect(screen.getAllByText(/request failed/i).length).toBeGreaterThan(0);
  });

  it('renders default unavailable and error fallback copy', () => {
    const { rerender } = render(<ForecastAccuracyPage />);

    hookState.value.response = { viewStatus: 'unavailable' };
    rerender(<ForecastAccuracyPage />);
    expect(screen.getByText(/forecast accuracy is unavailable\./i)).toBeInTheDocument();

    hookState.value.response = { viewStatus: 'error' };
    rerender(<ForecastAccuracyPage />);
    expect(screen.getByText(/forecast accuracy could not be prepared\./i)).toBeInTheDocument();
  });

  it('reports render failures for both rendered states', () => {
    const reportRenderEvent = vi.fn();
    hookState.value.reportRenderEvent = reportRenderEvent;
    hookState.value.response = {
      forecastAccuracyRequestId: 'fa-1',
      viewStatus: 'rendered_with_metrics',
      metrics: { mae: 1, rmse: 1, mape: 1 },
      alignedBuckets: [{ serviceCategory: 'Crash' }],
    };

    const { rerender } = render(<ForecastAccuracyPage />);

    expect(screen.getByText(/the comparison view could not be rendered\./i)).toBeInTheDocument();
    expect(reportRenderEvent).toHaveBeenCalledWith({ renderStatus: 'rendered' });
    expect(reportRenderEvent).toHaveBeenCalledWith({ renderStatus: 'render_failed', failureReason: 'comparison crashed' });

    reportRenderEvent.mockClear();
    hookState.value.response = {
      forecastAccuracyRequestId: 'fa-2',
      viewStatus: 'rendered_without_metrics',
      statusMessage: undefined,
      alignedBuckets: [{ serviceCategory: 'Crash' }],
    };
    rerender(<ForecastAccuracyPage />);

    expect(screen.getByText(/metrics are unavailable\./i)).toBeInTheDocument();
    expect(reportRenderEvent).toHaveBeenCalledWith({ renderStatus: 'rendered' });
    expect(reportRenderEvent).toHaveBeenCalledWith({ renderStatus: 'render_failed', failureReason: 'comparison crashed' });
  });
});
