import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../../api/forecastAccuracyApi', () => ({
  fetchForecastAccuracy: vi.fn(),
  submitForecastAccuracyRenderEvent: vi.fn(),
}));

vi.mock('../../../api/forecastVisualizations', () => ({
  fetchServiceCategoryOptions: vi.fn(),
}));

import {
  fetchForecastAccuracy,
  submitForecastAccuracyRenderEvent,
} from '../../../api/forecastAccuracyApi';
import { fetchServiceCategoryOptions } from '../../../api/forecastVisualizations';
import { useForecastAccuracy } from '../hooks/useForecastAccuracy';
import { hasRenderableForecastAccuracy } from '../state/forecastAccuracyState';

describe('useForecastAccuracy extra coverage', () => {
  beforeEach(() => {
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('falls back when bootstrap requests fail and submit receives a non-Error rejection', async () => {
    vi.mocked(fetchServiceCategoryOptions).mockRejectedValue(new Error('service categories unavailable'));
    vi.mocked(fetchForecastAccuracy)
      .mockRejectedValueOnce('unexpected')
      .mockRejectedValueOnce('still unexpected');

    const { result } = renderHook(() => useForecastAccuracy());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.serviceCategoryOptions).toEqual([]);
    expect(result.current.error).toBe('Unable to load forecast accuracy.');

    await act(async () => {
      await result.current.submit({ serviceCategory: 'Roads' });
    });

    expect(result.current.response).toBeNull();
    expect(result.current.error).toBe('Unable to load forecast accuracy.');
  });

  it('deduplicates render events and tolerates submission failures', async () => {
    vi.mocked(fetchServiceCategoryOptions).mockResolvedValue({ categories: ['Roads'] } as never);
    vi.mocked(fetchForecastAccuracy).mockResolvedValue({
      forecastAccuracyRequestId: 'fa-1',
      viewStatus: 'rendered_with_metrics',
      alignedBuckets: [],
    } as never);
    vi.mocked(submitForecastAccuracyRenderEvent).mockRejectedValue(new Error('network'));

    const { result } = renderHook(() => useForecastAccuracy());

    await waitFor(() => {
      expect(result.current.response?.forecastAccuracyRequestId).toBe('fa-1');
    });

    await act(async () => {
      await result.current.reportRenderEvent({ renderStatus: 'rendered' });
      await result.current.reportRenderEvent({ renderStatus: 'rendered' });
      await result.current.reportRenderEvent({ renderStatus: 'render_failed', failureReason: 'chart crashed' });
    });

    expect(submitForecastAccuracyRenderEvent).toHaveBeenCalledTimes(2);
    expect(console.error).toHaveBeenCalled();
  });

  it('reports renderability correctly', () => {
    expect(hasRenderableForecastAccuracy(null)).toBe(false);
    expect(hasRenderableForecastAccuracy({ viewStatus: 'error' } as never)).toBe(false);
    expect(hasRenderableForecastAccuracy({ viewStatus: 'rendered_without_metrics' } as never)).toBe(true);
  });
});
