/**
 * Extra coverage for useDemandComparisons – render event error and clearResponse.
 */
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useDemandComparisons } from '../hooks/useDemandComparisons';
import * as api from '../../../api/demandComparisons';

vi.mock('../../../api/demandComparisons');

const availabilityPayload = {
  serviceCategories: ['Roads'],
  byCategoryGeography: {
    Roads: { geographyLevels: ['ward'], geographyOptions: { ward: ['Ward 1'] } },
  },
  dateConstraints: {
    historicalMin: '2026-03-01T00:00:00Z',
    historicalMax: '2026-03-10T00:00:00Z',
    forecastMin: '2026-03-02T00:00:00Z',
    forecastMax: '2026-03-06T00:00:00Z',
    overlapStart: '2026-03-02T00:00:00Z',
    overlapEnd: '2026-03-05T00:00:00Z',
  },
  presets: [{ label: 'Overlap window', timeRangeStart: '2026-03-02T00:00:00Z', timeRangeEnd: '2026-03-05T00:00:00Z' }],
  forecastProduct: 'daily_1_day',
};

beforeEach(() => {
  vi.mocked(api.fetchDemandComparisonAvailability).mockResolvedValue(availabilityPayload as any);
});

afterEach(() => {
  vi.clearAllMocks();
});

describe('useDemandComparisons – render event error and clearResponse', () => {
  it('silently catches render event submission errors and logs to console', async () => {
    vi.mocked(api.submitDemandComparisonQuery).mockResolvedValue({
      comparisonRequestId: 'cmp-1',
      outcomeStatus: 'success',
      filters: {
        serviceCategories: ['Roads'],
        geographyValues: [],
        timeRangeStart: '2026-03-02T00:00:00Z',
        timeRangeEnd: '2026-03-05T00:00:00Z',
      },
      resultMode: 'chart_and_table',
      series: [],
      message: 'OK',
    } as any);
    vi.mocked(api.submitDemandComparisonRenderEvent).mockRejectedValue(new Error('render fail'));

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const { result } = renderHook(() => useDemandComparisons());
    await act(async () => { await new Promise((r) => setTimeout(r, 0)); });

    act(() => {
      result.current.setFilters({
        ...result.current.filters,
        serviceCategories: ['Roads'],
        timeRangeStart: '2026-03-02T00:00:00Z',
        timeRangeEnd: '2026-03-05T00:00:00Z',
      });
    });

    await act(async () => { await result.current.submit(); });

    await act(async () => {
      await result.current.reportRenderEvent({ renderStatus: 'rendered' });
    });

    expect(consoleSpy).toHaveBeenCalledWith(
      'Failed to submit demand comparison render event',
      expect.any(Error),
    );
    consoleSpy.mockRestore();
  });

  it('clearResponse resets response and error', async () => {
    vi.mocked(api.submitDemandComparisonQuery).mockRejectedValue(new Error('fail'));

    const { result } = renderHook(() => useDemandComparisons());
    await act(async () => { await new Promise((r) => setTimeout(r, 0)); });

    act(() => {
      result.current.setFilters({
        ...result.current.filters,
        serviceCategories: ['Roads'],
        timeRangeStart: '2026-03-02T00:00:00Z',
        timeRangeEnd: '2026-03-05T00:00:00Z',
      });
    });

    await act(async () => { await result.current.submit(); });
    expect(result.current.error).not.toBeNull();

    act(() => { result.current.clearResponse(); });

    expect(result.current.error).toBeNull();
    expect(result.current.response).toBeNull();
  });

  it('keeps direct filter updates when availability has not loaded yet', async () => {
    vi.mocked(api.fetchDemandComparisonAvailability).mockImplementation(
      () => new Promise(() => {}),
    );

    const { result } = renderHook(() => useDemandComparisons());

    act(() => {
      result.current.setFilters({
        ...result.current.filters,
        serviceCategories: ['Roads', 'Unknown'],
        geographyLevel: 'ward',
        geographyValues: ['Ward 99'],
      });
    });

    expect(result.current.filters.serviceCategories).toEqual(['Roads', 'Unknown']);
    expect(result.current.filters.geographyLevel).toBe('ward');
    expect(result.current.filters.geographyValues).toEqual(['Ward 99']);
  });

  it('blocks submit when range is invalid before availability is loaded', async () => {
    vi.mocked(api.fetchDemandComparisonAvailability).mockImplementation(
      () => new Promise(() => {}),
    );

    const { result } = renderHook(() => useDemandComparisons());

    act(() => {
      result.current.setFilters({
        ...result.current.filters,
        serviceCategories: ['Roads'],
        timeRangeStart: '2026-03-05T00:00:00Z',
        timeRangeEnd: '2026-03-04T00:00:00Z',
      });
    });

    let response: unknown;
    await act(async () => {
      response = await result.current.submit();
    });

    expect(response).toBeNull();
    expect(result.current.error).toBe('End date must be on or after the start date.');
    expect(api.submitDemandComparisonQuery).not.toHaveBeenCalled();
  });

  it('returns an explicit error when auto-select runs before availability is ready', async () => {
    vi.mocked(api.fetchDemandComparisonAvailability).mockImplementation(
      () => new Promise(() => {}),
    );

    const { result } = renderHook(() => useDemandComparisons());

    let response: unknown;
    await act(async () => {
      response = await result.current.autoSelectForecastBackedCombination();
    });

    expect(response).toBeNull();
    expect(result.current.error).toBe('Comparison filters are still loading. Please try again in a moment.');
  });

  it('returns an explicit error when no forecast-backed category can be auto-selected', async () => {
    vi.mocked(api.fetchDemandComparisonAvailability).mockResolvedValue({
      ...availabilityPayload,
      serviceCategories: [],
    } as any);

    const { result } = renderHook(() => useDemandComparisons());
    await act(async () => { await new Promise((r) => setTimeout(r, 0)); });

    let response: unknown;
    await act(async () => {
      response = await result.current.autoSelectForecastBackedCombination();
    });

    expect(response).toBeNull();
    expect(result.current.error).toBe('No forecast-backed categories are available for the selected window.');
  });

  it('skips render-event submission when there is no comparison response yet', async () => {
    const { result } = renderHook(() => useDemandComparisons());
    await act(async () => { await new Promise((r) => setTimeout(r, 0)); });

    await act(async () => {
      await result.current.reportRenderEvent({ renderStatus: 'rendered' });
    });

    expect(api.submitDemandComparisonRenderEvent).not.toHaveBeenCalled();
  });
});
