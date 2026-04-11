/**
 * Extra coverage for useForecastVisualization – service-categories error
 * and visualization fetch error paths.
 */
import { act, renderHook } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useForecastVisualization } from '../hooks/useForecastVisualization';
import * as api from '../../../api/forecastVisualizations';

vi.mock('../../../api/forecastVisualizations');

afterEach(() => {
  vi.clearAllMocks();
});

describe('useForecastVisualization – error paths', () => {
  it('ignores category-option success handling when the request is aborted', async () => {
    let resolveOptions: ((value: { forecastProduct: 'daily_1_day'; categories: string[] }) => void) | undefined;
    vi.mocked(api.fetchServiceCategoryOptions).mockImplementation(
      () => new Promise((resolve) => { resolveOptions = resolve as typeof resolveOptions; }),
    );
    vi.mocked(api.fetchCurrentForecastVisualization).mockResolvedValue({} as any);

    const { unmount } = renderHook(() => useForecastVisualization());
    act(() => { unmount(); });

    expect(resolveOptions).toBeDefined();
    await act(async () => {
      resolveOptions!({ forecastProduct: 'daily_1_day', categories: ['Roads'] });
      await Promise.resolve();
    });

    expect(api.fetchCurrentForecastVisualization).not.toHaveBeenCalled();
  });

  it('sets serviceCategoriesReady without options when service-categories fetch fails', async () => {
    vi.mocked(api.fetchServiceCategoryOptions).mockRejectedValue(new Error('Service category fetch failed'));
    vi.mocked(api.fetchCurrentForecastVisualization).mockResolvedValue({} as any);

    const { result } = renderHook(() => useForecastVisualization());

    await act(async () => { await new Promise((r) => setTimeout(r, 10)); });

    expect(result.current.serviceCategoryOptions).toEqual([]);
  });

  it('sets error when visualization fetch fails', async () => {
    vi.mocked(api.fetchServiceCategoryOptions).mockResolvedValue({ forecastProduct: 'daily_1_day', categories: ['Roads'] });
    vi.mocked(api.fetchCurrentForecastVisualization).mockRejectedValue(new Error('Viz fetch failed'));

    const { result } = renderHook(() => useForecastVisualization());

    await act(async () => { await new Promise((r) => setTimeout(r, 10)); });

    expect(result.current.error).toBe('Viz fetch failed');
    expect(result.current.visualization).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('ignores visualization fetch error when signal is aborted (lines 56-57)', async () => {
    vi.mocked(api.fetchServiceCategoryOptions).mockResolvedValue({ forecastProduct: 'daily_1_day', categories: ['Roads'] });

    // Make visualization fetch reject only after unmount (signal aborted)
    vi.mocked(api.fetchCurrentForecastVisualization).mockImplementation(
      (_product, _categories, _excluded, signal) =>
        new Promise((_resolve, reject) => {
          if (signal) {
            signal.addEventListener('abort', () => reject(new Error('aborted')));
          }
        }),
    );

    const { unmount, result } = renderHook(() => useForecastVisualization());

    // Wait for service categories to load, then unmount to trigger abort
    await act(async () => { await new Promise((r) => setTimeout(r, 10)); });
    act(() => { unmount(); });

    // After unmount, the aborted signal means the error is silently ignored
    expect(result.current.error).toBeNull();
  });

  it('keeps selected categories stable when options remain the same across product changes', async () => {
    vi.mocked(api.fetchServiceCategoryOptions).mockResolvedValue({
      forecastProduct: 'daily_1_day',
      categories: ['Roads', 'Waste'],
    });
    vi.mocked(api.fetchCurrentForecastVisualization).mockResolvedValue({
      visualizationLoadId: 'load-1',
    } as any);

    const { result } = renderHook(() => useForecastVisualization());
    await act(async () => { await new Promise((r) => setTimeout(r, 10)); });

    const previousCategories = result.current.serviceCategories;
    act(() => {
      result.current.setForecastProduct('weekly_7_day');
    });
    await act(async () => { await new Promise((r) => setTimeout(r, 10)); });

    expect(result.current.serviceCategories).toEqual([]);
    expect(result.current.serviceCategories).toBe(previousCategories);
  });

  it('resets service categories to all-selected when every option remains selected after a product change', async () => {
    vi.mocked(api.fetchServiceCategoryOptions)
      .mockResolvedValueOnce({
        forecastProduct: 'daily_1_day',
        categories: ['Roads', 'Waste'],
      })
      .mockResolvedValueOnce({
        forecastProduct: 'weekly_7_day',
        categories: ['Roads', 'Waste'],
      });
    vi.mocked(api.fetchCurrentForecastVisualization).mockResolvedValue({
      visualizationLoadId: 'load-all-selected',
    } as any);

    const { result } = renderHook(() => useForecastVisualization());
    await act(async () => { await new Promise((r) => setTimeout(r, 10)); });

    act(() => {
      result.current.setServiceCategories(['Roads', 'Waste']);
    });
    await act(async () => { await new Promise((r) => setTimeout(r, 10)); });

    act(() => {
      result.current.setForecastProduct('weekly_7_day');
    });
    await act(async () => { await new Promise((r) => setTimeout(r, 10)); });

    expect(result.current.serviceCategories).toEqual([]);
  });

  it('returns early from reportRenderEvent when visualization is not loaded', async () => {
    vi.mocked(api.fetchServiceCategoryOptions).mockImplementation(
      () => new Promise(() => {}),
    );

    const { result } = renderHook(() => useForecastVisualization());

    await act(async () => {
      await result.current.reportRenderEvent({ renderStatus: 'rendered' });
    });

    expect(api.submitVisualizationRenderEvent).not.toHaveBeenCalled();
  });

  it('returns early from reportConfidenceRenderEvent when visualization is not loaded', async () => {
    vi.mocked(api.fetchServiceCategoryOptions).mockImplementation(
      () => new Promise(() => {}),
    );

    const { result } = renderHook(() => useForecastVisualization());

    await act(async () => {
      await result.current.reportConfidenceRenderEvent({ renderStatus: 'rendered' });
    });

    expect(api.submitConfidenceRenderEvent).not.toHaveBeenCalled();
  });

  it('deduplicates confidence render events per load and status', async () => {
    vi.mocked(api.fetchServiceCategoryOptions).mockResolvedValue({ forecastProduct: 'daily_1_day', categories: ['Roads'] });
    vi.mocked(api.fetchCurrentForecastVisualization).mockResolvedValue({ visualizationLoadId: 'load-1' } as any);
    vi.mocked(api.submitConfidenceRenderEvent).mockResolvedValue(undefined);

    const { result } = renderHook(() => useForecastVisualization());
    await act(async () => { await new Promise((r) => setTimeout(r, 10)); });

    await act(async () => {
      await result.current.reportConfidenceRenderEvent({ renderStatus: 'rendered' });
      await result.current.reportConfidenceRenderEvent({ renderStatus: 'rendered' });
    });

    expect(api.submitConfidenceRenderEvent).toHaveBeenCalledTimes(1);
  });

  it('uses excluded categories when most service areas are selected', async () => {
    vi.mocked(api.fetchServiceCategoryOptions).mockResolvedValue({
      forecastProduct: 'daily_1_day',
      categories: ['Roads', 'Waste', 'Transit', 'Parks'],
    });
    vi.mocked(api.fetchCurrentForecastVisualization).mockResolvedValue({ visualizationLoadId: 'load-2' } as any);

    const { result } = renderHook(() => useForecastVisualization());
    await act(async () => { await new Promise((r) => setTimeout(r, 10)); });

    act(() => {
      result.current.setServiceCategories(['Roads', 'Waste', 'Transit']);
    });
    await act(async () => { await new Promise((r) => setTimeout(r, 10)); });

    expect(api.fetchCurrentForecastVisualization).toHaveBeenLastCalledWith(
      'daily_1_day',
      [],
      ['Parks'],
      expect.any(AbortSignal),
    );
  });
});
