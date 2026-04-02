/**
 * Extra coverage for useHistoricalDemand – error paths and clearResponse.
 */
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useHistoricalDemand } from '../hooks/useHistoricalDemand';
import * as api from '../../../api/historicalDemand';

vi.mock('../../../api/historicalDemand');

beforeEach(() => {
  vi.mocked(api.fetchHistoricalDemandContext).mockResolvedValue({
    serviceCategories: ['Roads'],
    supportedGeographyLevels: ['ward'],
    summary: 'OK',
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

describe('useHistoricalDemand – error paths', () => {
  it('sets error when context fetch fails without abort', async () => {
    vi.mocked(api.fetchHistoricalDemandContext).mockRejectedValue(new Error('context failed'));

    const { result } = renderHook(() => useHistoricalDemand());
    await act(async () => { await new Promise((r) => setTimeout(r, 0)); });

    expect(result.current.error).toBe('context failed');
  });

  it('sets error and returns null when submit throws', async () => {
    vi.mocked(api.submitHistoricalDemandQuery).mockRejectedValue(new Error('Network failure'));

    const { result } = renderHook(() => useHistoricalDemand());
    await act(async () => { await new Promise((r) => setTimeout(r, 0)); });

    let ret: unknown;
    await act(async () => {
      ret = await result.current.submit();
    });

    expect(ret).toBeNull();
    expect(result.current.error).toBe('Network failure');
    expect(result.current.response).toBeNull();
  });

  it('sets generic error string when submit throws a non-Error', async () => {
    vi.mocked(api.submitHistoricalDemandQuery).mockRejectedValue('oops');

    const { result } = renderHook(() => useHistoricalDemand());
    await act(async () => { await new Promise((r) => setTimeout(r, 0)); });

    await act(async () => { await result.current.submit(); });

    expect(result.current.error).toBe('Unable to load historical demand data.');
  });

  it('clearResponse resets response and error state', async () => {
    vi.mocked(api.submitHistoricalDemandQuery).mockRejectedValue(new Error('fail'));

    const { result } = renderHook(() => useHistoricalDemand());
    await act(async () => { await new Promise((r) => setTimeout(r, 0)); });
    await act(async () => { await result.current.submit(); });

    expect(result.current.error).not.toBeNull();

    act(() => { result.current.clearResponse(); });

    expect(result.current.error).toBeNull();
    expect(result.current.response).toBeNull();
  });

  it('ignores context fetch error when signal is aborted (lines 47-49)', async () => {
    // Make fetchHistoricalDemandContext reject only after the signal is aborted
    vi.mocked(api.fetchHistoricalDemandContext).mockImplementation(
      (signal?: AbortSignal) =>
        new Promise((_resolve, reject) => {
          if (signal) {
            signal.addEventListener('abort', () => reject(new Error('aborted')));
          }
        }),
    );

    const { unmount, result } = renderHook(() => useHistoricalDemand());

    // Unmount immediately to trigger abort
    act(() => { unmount(); });

    // After unmount, the signal is aborted so the catch branch doesn't set error
    expect(result.current.error).toBeNull();
  });

  it('silently catches render event submission errors', async () => {
    vi.mocked(api.submitHistoricalDemandQuery).mockResolvedValue({
      analysisRequestId: 'req-1',
      outcomeStatus: 'success',
      filters: { serviceCategories: [], timeRangeStart: '', timeRangeEnd: '' },
      aggregationGranularity: 'daily',
      resultMode: 'chart_and_table',
      summaryPoints: [],
    } as any);
    vi.mocked(api.submitHistoricalDemandRenderEvent).mockRejectedValue(new Error('render fail'));

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const { result } = renderHook(() => useHistoricalDemand());
    await act(async () => { await new Promise((r) => setTimeout(r, 0)); });
    await act(async () => { await result.current.submit(); });

    await act(async () => {
      await result.current.reportRenderEvent({ renderStatus: 'rendered' });
    });

    expect(consoleSpy).toHaveBeenCalledWith(
      'Failed to submit historical demand render event',
      expect.any(Error),
    );
    consoleSpy.mockRestore();
  });

  it('returns early for reportRenderEvent when there is no response and deduplicates repeated events', async () => {
    vi.mocked(api.submitHistoricalDemandQuery).mockResolvedValue({
      analysisRequestId: 'req-dedupe',
      outcomeStatus: 'success',
      filters: { serviceCategories: [], timeRangeStart: '', timeRangeEnd: '' },
      aggregationGranularity: 'daily',
      resultMode: 'chart_and_table',
      summaryPoints: [],
    } as any);
    vi.mocked(api.submitHistoricalDemandRenderEvent).mockResolvedValue(undefined);

    const { result } = renderHook(() => useHistoricalDemand());
    await act(async () => { await new Promise((r) => setTimeout(r, 0)); });

    await act(async () => {
      await result.current.reportRenderEvent({ renderStatus: 'rendered' });
    });
    expect(api.submitHistoricalDemandRenderEvent).not.toHaveBeenCalled();

    await act(async () => { await result.current.submit(); });
    await act(async () => {
      await result.current.reportRenderEvent({ renderStatus: 'rendered' });
      await result.current.reportRenderEvent({ renderStatus: 'rendered' });
    });

    expect(api.submitHistoricalDemandRenderEvent).toHaveBeenCalledTimes(1);
  });

  it('returns early for reportRenderEvent when response has no analysisRequestId', async () => {
    vi.mocked(api.submitHistoricalDemandQuery).mockResolvedValue({
      outcomeStatus: 'success',
      filters: { serviceCategories: [], timeRangeStart: '', timeRangeEnd: '' },
      aggregationGranularity: 'daily',
      resultMode: 'chart_and_table',
      summaryPoints: [],
    } as any);

    const { result } = renderHook(() => useHistoricalDemand());
    await act(async () => { await new Promise((r) => setTimeout(r, 0)); });

    await act(async () => {
      await result.current.submit();
      await result.current.reportRenderEvent({ renderStatus: 'rendered' });
    });

    expect(api.submitHistoricalDemandRenderEvent).not.toHaveBeenCalled();
  });
});
