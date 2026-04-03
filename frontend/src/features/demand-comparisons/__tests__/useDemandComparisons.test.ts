import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useDemandComparisons } from '../hooks/useDemandComparisons';
import * as api from '../../../api/demandComparisons';

vi.mock('../../../api/demandComparisons');

const availabilityPayload = {
  serviceCategories: ['Roads', 'Waste'],
  byCategoryGeography: {
    Roads: {
      geographyLevels: ['ward'],
      geographyOptions: {
        ward: ['Ward 1', 'Ward 2'],
      },
    },
    Waste: {
      geographyLevels: ['ward'],
      geographyOptions: {
        ward: ['Ward 1'],
      },
    },
  },
  dateConstraints: {
    historicalMin: '2026-03-01T00:00:00Z',
    historicalMax: '2026-03-10T00:00:00Z',
    forecastMin: '2026-03-02T00:00:00Z',
    forecastMax: '2026-03-06T00:00:00Z',
    overlapStart: '2026-03-02T00:00:00Z',
    overlapEnd: '2026-03-05T00:00:00Z',
  },
  presets: [
    {
      label: 'Overlap window',
      timeRangeStart: '2026-03-02T00:00:00Z',
      timeRangeEnd: '2026-03-05T00:00:00Z',
    },
  ],
  forecastProduct: 'daily_1_day',
} as const;

describe('useDemandComparisons', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('loads availability and exposes progressive options', async () => {
    vi.mocked(api.fetchDemandComparisonAvailability).mockResolvedValue(availabilityPayload as any);

    const { result } = renderHook(() => useDemandComparisons());

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    expect(result.current.isLoadingAvailability).toBe(false);
    expect(result.current.availability?.serviceCategories).toEqual(['Roads', 'Waste']);
    expect(result.current.dateWindowStart).toBe('2026-03-01T00:00:00Z');
    expect(result.current.dateWindowEnd).toBe('2026-03-10T00:00:00Z');
  });

  it('clears stale geography state when filters are updated', async () => {
    vi.mocked(api.fetchDemandComparisonAvailability).mockResolvedValue(availabilityPayload as any);

    const { result } = renderHook(() => useDemandComparisons());

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    act(() => {
      result.current.setFilters({
        ...result.current.filters,
        serviceCategories: ['Roads', 'Waste'],
        geographyLevel: 'ward',
        geographyValues: ['Ward 2'],
      });
    });

    expect(result.current.filters.geographyLevel).toBeUndefined();
    expect(result.current.filters.geographyValues).toEqual([]);

    act(() => {
      result.current.setFilters({
        ...result.current.filters,
        serviceCategories: [],
      });
    });

    expect(result.current.filters.geographyLevel).toBeUndefined();
    expect(result.current.filters.geographyValues).toEqual([]);
  });

  it('clamps selected date range to backend window', async () => {
    vi.mocked(api.fetchDemandComparisonAvailability).mockResolvedValue(availabilityPayload as any);

    const { result } = renderHook(() => useDemandComparisons());

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    act(() => {
      result.current.setFilters({
        ...result.current.filters,
        serviceCategories: ['Roads'],
        timeRangeStart: '2026-02-25T00:00:00Z',
        timeRangeEnd: '2026-03-03T00:00:00Z',
      });
    });

    expect(result.current.filters.timeRangeStart).toBe('2026-03-01T00:00:00.000Z');
    expect(result.current.filters.timeRangeEnd).toBe('2026-03-03T00:00:00.000Z');
    expect(result.current.dateRangeError).toBeNull();
  });

  it('submits valid filters and stores response', async () => {
    vi.mocked(api.fetchDemandComparisonAvailability).mockResolvedValue(availabilityPayload as any);
    vi.mocked(api.submitDemandComparisonQuery).mockResolvedValue({
      comparisonRequestId: 'cmp-1',
      outcomeStatus: 'success',
      series: [],
    } as any);

    const { result } = renderHook(() => useDemandComparisons());

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    act(() => {
      result.current.setFilters({
        ...result.current.filters,
        serviceCategories: ['Roads'],
        timeRangeStart: '2026-03-02T00:00:00Z',
        timeRangeEnd: '2026-03-03T00:00:00Z',
      });
    });

    let response: any;
    await act(async () => {
      response = await result.current.submit();
    });

    expect(response?.outcomeStatus).toBe('success');
    expect(result.current.response?.comparisonRequestId).toBe('cmp-1');
    expect(api.submitDemandComparisonQuery).toHaveBeenCalledTimes(1);
    expect(api.submitDemandComparisonQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        geographyLevel: undefined,
        geographyValues: [],
      }),
    );
  });

  it('submits all available categories when the UI selection is empty', async () => {
    vi.mocked(api.fetchDemandComparisonAvailability).mockResolvedValue(availabilityPayload as any);
    vi.mocked(api.submitDemandComparisonQuery).mockResolvedValue({
      comparisonRequestId: 'cmp-all',
      outcomeStatus: 'success',
      series: [],
    } as any);

    const { result } = renderHook(() => useDemandComparisons());

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    let response: any;
    await act(async () => {
      response = await result.current.submit();
    });

    expect(response?.comparisonRequestId).toBe('cmp-all');
    expect(api.submitDemandComparisonQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        serviceCategories: ['Roads', 'Waste'],
      }),
    );
  });

  it('applies backend date preset', async () => {
    vi.mocked(api.fetchDemandComparisonAvailability).mockResolvedValue(availabilityPayload as any);

    const { result } = renderHook(() => useDemandComparisons());

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    act(() => {
      result.current.applyDatePreset({
        label: 'Overlap window',
        timeRangeStart: '2026-03-02T00:00:00Z',
        timeRangeEnd: '2026-03-05T00:00:00Z',
      });
    });

    expect(result.current.filters.timeRangeStart).toBe('2026-03-02T00:00:00.000Z');
    expect(result.current.filters.timeRangeEnd).toBe('2026-03-05T00:00:00.000Z');
  });

  it('auto-selects deterministic availability-backed combination', async () => {
    vi.mocked(api.fetchDemandComparisonAvailability).mockResolvedValue(availabilityPayload as any);
    vi.mocked(api.submitDemandComparisonQuery).mockResolvedValue({
      comparisonRequestId: 'cmp-auto',
      outcomeStatus: 'success',
      series: [],
    } as any);

    const { result } = renderHook(() => useDemandComparisons());

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    let response: any;
    await act(async () => {
      response = await result.current.autoSelectForecastBackedCombination();
    });

    expect(response?.comparisonRequestId).toBe('cmp-auto');
    expect(api.submitDemandComparisonQuery).toHaveBeenCalledWith(
      expect.objectContaining({
        serviceCategories: ['Roads'],
        geographyLevel: undefined,
        geographyValues: [],
        proceedAfterWarning: true,
      }),
    );
    expect(result.current.autoSelectProgress).toEqual({ current: 0, total: 0 });
    expect(result.current.isAutoSelecting).toBe(false);
  });

  it('deduplicates render event submissions', async () => {
    vi.mocked(api.fetchDemandComparisonAvailability).mockResolvedValue(availabilityPayload as any);
    vi.mocked(api.submitDemandComparisonQuery).mockResolvedValue({
      comparisonRequestId: 'cmp-render',
      outcomeStatus: 'success',
      series: [],
    } as any);

    const { result } = renderHook(() => useDemandComparisons());

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    act(() => {
      result.current.setFilters({
        ...result.current.filters,
        serviceCategories: ['Roads'],
        timeRangeStart: '2026-03-02T00:00:00Z',
        timeRangeEnd: '2026-03-03T00:00:00Z',
      });
    });

    await act(async () => {
      await result.current.submit();
    });

    await act(async () => {
      await result.current.reportRenderEvent({ renderStatus: 'rendered' } as any);
      await result.current.reportRenderEvent({ renderStatus: 'rendered' } as any);
    });

    expect(api.submitDemandComparisonRenderEvent).toHaveBeenCalledTimes(1);
  });

  it('maps availability load network failures to a friendly message', async () => {
    vi.mocked(api.fetchDemandComparisonAvailability).mockRejectedValue(new Error('Load failed'));

    const { result } = renderHook(() => useDemandComparisons());

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    expect(result.current.error).toBe('Unable to load comparison filters. Check your connection and try again.');
  });
});
