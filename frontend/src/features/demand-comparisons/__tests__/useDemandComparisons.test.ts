import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useDemandComparisons } from '../hooks/useDemandComparisons';
import * as api from '../../../api/demandComparisons';

vi.mock('../../../api/demandComparisons');

describe('useDemandComparisons', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('initializes context and handles abort correctly', async () => {
    const mockContext = { serviceCategories: ['Cat A'], geographyLevels: ['Level 1'], geographyOptions: {} };
    let resolveContext: any;
    vi.mocked(api.fetchDemandComparisonContext).mockReturnValue(new Promise((resolve) => {
      resolveContext = resolve;
    }));

    const { result, unmount } = renderHook(() => useDemandComparisons());
    expect(result.current.isLoadingContext).toBe(true);

    act(() => {
      resolveContext(mockContext);
    });

    await act(async () => {
      await new Promise(r => setTimeout(r, 0));
    });

    expect(result.current.isLoadingContext).toBe(false);
    expect(result.current.context).toEqual(mockContext);
    expect(result.current.filters.serviceCategories).toEqual(['Cat A']);
    expect(result.current.filters.geographyLevel).toBe('Level 1');

    unmount(); // Test abort block execution
  });

  it('handles fetchDemandComparisonContext error gracefully unless aborted', async () => {
    vi.mocked(api.fetchDemandComparisonContext).mockRejectedValue(new Error('Fetch Error'));
    const { result } = renderHook(() => useDemandComparisons());

    await act(async () => {
      await new Promise(r => setTimeout(r, 0));
    });

    expect(result.current.isLoadingContext).toBe(false);
    expect(result.current.error).toBe('Fetch Error');
  });

  it('handles abort properly on unmount during fetch', async () => {
    vi.mocked(api.fetchDemandComparisonContext).mockImplementation((signal) => {
      return new Promise((_, reject) => {
         signal?.addEventListener('abort', () => reject(new Error('AbortError')));
      });
    });
    const { result, unmount } = renderHook(() => useDemandComparisons());
    unmount(); // Aborts the signal immediately

    await act(async () => {
      await new Promise(r => setTimeout(r, 10));
    });

    // Error should not be set because signal was aborted
    expect(result.current.error).toBeNull();
  });

  it('submits query and updates states successfully', async () => {
    vi.mocked(api.fetchDemandComparisonContext).mockResolvedValue({ serviceCategories: [], geographyLevels: [], geographyOptions: {} });
    const mockResponse = { outcomeStatus: 'success', comparisonRequestId: 'req-1', message: 'Ok', series: [] };
    vi.mocked(api.submitDemandComparisonQuery).mockResolvedValue(mockResponse as any);

    const { result } = renderHook(() => useDemandComparisons());

    let promise: any;
    act(() => {
      promise = result.current.submit({ serviceCategories: ['New Cat'] }, true);
    });

    expect(result.current.isSubmitting).toBe(true);
    expect(result.current.filters.serviceCategories).toEqual(['New Cat']);

    const res = await act(async () => promise);
    expect(res).toEqual(mockResponse);
    expect(result.current.response).toEqual(mockResponse);
    expect(result.current.isSubmitting).toBe(false);
  });

  it('submits query and handles error', async () => {
    vi.mocked(api.fetchDemandComparisonContext).mockResolvedValue({ serviceCategories: [], geographyLevels: [], geographyOptions: {} });
    vi.mocked(api.submitDemandComparisonQuery).mockRejectedValue(new Error('Submit Error'));

    const { result } = renderHook(() => useDemandComparisons());

    const res = await act(async () => result.current.submit());

    expect(res).toBeNull();
    expect(result.current.error).toBe('Submit Error');
    expect(result.current.response).toBeNull();
    expect(result.current.isSubmitting).toBe(false);
  });

  it('submits query falling back to generic error', async () => {
    vi.mocked(api.fetchDemandComparisonContext).mockResolvedValue({ serviceCategories: [], geographyLevels: [], geographyOptions: {} });
    vi.mocked(api.submitDemandComparisonQuery).mockRejectedValue('String Error');

    const { result } = renderHook(() => useDemandComparisons());
    await act(async () => { await result.current.submit(); });
    expect(result.current.error).toBe('Unable to compare demand.');
  });

  it('handles race conditions via lastRequestToken', async () => {
    vi.mocked(api.fetchDemandComparisonContext).mockResolvedValue({ serviceCategories: [], geographyLevels: [], geographyOptions: {} });

    let resolveFirst: any;
    const promise1 = new Promise((r) => { resolveFirst = r; });
    const mockResponse2 = { outcomeStatus: 'success', message: 'Second', series: [] };

    vi.mocked(api.submitDemandComparisonQuery)
      .mockReturnValueOnce(promise1 as any)
      .mockResolvedValueOnce(mockResponse2 as any);

    const { result } = renderHook(() => useDemandComparisons());

    let submit1: any;
    let submit2: any;
    act(() => {
      submit1 = result.current.submit();
      submit2 = result.current.submit();
    });

    // submit2 resolves immediately
    await act(async () => { await submit2; });
    expect(result.current.response).toEqual(mockResponse2);
    expect(result.current.isSubmitting).toBe(false);

    // resolve submit1 now
    await act(async () => { resolveFirst({ outcomeStatus: 'success', message: 'First', series: [] }); await submit1; });
    // State should remain for submit2
    expect(result.current.response).toEqual(mockResponse2);
  });

  it('handles race condition for errors', async () => {
    vi.mocked(api.fetchDemandComparisonContext).mockResolvedValue({ serviceCategories: [], geographyLevels: [], geographyOptions: {} });

    let rejectFirst: any;
    const promise1 = new Promise((_, r) => { rejectFirst = r; });
    const mockResponse2 = { outcomeStatus: 'success', message: 'Second', series: [] };

    vi.mocked(api.submitDemandComparisonQuery)
      .mockReturnValueOnce(promise1 as any)
      .mockResolvedValueOnce(mockResponse2 as any);

    const { result } = renderHook(() => useDemandComparisons());

    let submit1: any;
    let submit2: any;
    act(() => {
      submit1 = result.current.submit();
      submit2 = result.current.submit();
    });

    await act(async () => { await submit2; });
    await act(async () => {
      rejectFirst(new Error('First Error'));
      try { await submit1; } catch (e) {}
    });

    // Should not inherit the error from the earlier stale request
    expect(result.current.error).toBeNull();
  });

  it('reports render event correctly and prevents duplicates', async () => {
    vi.mocked(api.fetchDemandComparisonContext).mockResolvedValue({ serviceCategories: [], geographyLevels: [], geographyOptions: {} });
    vi.mocked(api.submitDemandComparisonQuery).mockResolvedValue({ comparisonRequestId: 'test-req', outcomeStatus: 'success', message: 'Ok', series: [] } as any);

    const { result } = renderHook(() => useDemandComparisons());

    await act(async () => { await result.current.submit(); });

    await act(async () => {
      await result.current.reportRenderEvent({ renderStatus: 'rendered' } as any);
    });
    expect(api.submitDemandComparisonRenderEvent).toHaveBeenCalledWith('test-req', { renderStatus: 'rendered' });
    
    // call again to trigger early return branch for duplicate render events
    await act(async () => {
      await result.current.reportRenderEvent({ renderStatus: 'rendered' } as any);
    });
    expect(api.submitDemandComparisonRenderEvent).toHaveBeenCalledTimes(1);

    // Calling it again with same values shouldn't resubmit
    vi.mocked(api.submitDemandComparisonRenderEvent).mockClear();
    await act(async () => {
      await result.current.reportRenderEvent({ renderStatus: 'rendered' } as any);
    });
    expect(api.submitDemandComparisonRenderEvent).not.toHaveBeenCalled();
  });

  it('bails out of reportRenderEvent if no comparisonRequestId', async () => {
    vi.mocked(api.fetchDemandComparisonContext).mockResolvedValue({ serviceCategories: [], geographyLevels: [], geographyOptions: {} });
    vi.mocked(api.submitDemandComparisonQuery).mockResolvedValue({ outcomeStatus: 'success', message: 'Ok', series: [] } as any);

    const { result } = renderHook(() => useDemandComparisons());
    await act(async () => { await result.current.submit(); });

    await act(async () => {
      await result.current.reportRenderEvent({ renderStatus: 'rendered' } as any);
    });
    expect(api.submitDemandComparisonRenderEvent).not.toHaveBeenCalled();
  });

  it('handles reportRenderEvent error', async () => {
    vi.mocked(api.fetchDemandComparisonContext).mockResolvedValue({ serviceCategories: [], geographyLevels: [], geographyOptions: {} });
    vi.mocked(api.submitDemandComparisonQuery).mockResolvedValue({ comparisonRequestId: 'test-err', outcomeStatus: 'success', message: 'Ok', series: [] } as any);
    vi.mocked(api.submitDemandComparisonRenderEvent).mockRejectedValue(new Error('Render Event Error'));

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const { result } = renderHook(() => useDemandComparisons());
    await act(async () => { await result.current.submit(); });

    await act(async () => {
      await result.current.reportRenderEvent({ renderStatus: 'rendered' } as any);
    });

    expect(consoleSpy).toHaveBeenCalledWith('Failed to submit demand comparison render event', expect.any(Error));
    consoleSpy.mockRestore();
  });

  it('clears response and error', async () => {
    vi.mocked(api.fetchDemandComparisonContext).mockResolvedValue({ serviceCategories: [], geographyLevels: [], geographyOptions: {} });
    const { result } = renderHook(() => useDemandComparisons());

    act(() => { result.current.clearResponse(); });

    expect(result.current.response).toBeNull();
    expect(result.current.error).toBeNull();
  });
});