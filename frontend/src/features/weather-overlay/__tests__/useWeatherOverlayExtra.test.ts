import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../../api/weatherOverlayApi', () => ({
  fetchWeatherOverlay: vi.fn(),
  submitWeatherOverlayRenderEvent: vi.fn(),
}));

import { fetchWeatherOverlay, submitWeatherOverlayRenderEvent } from '../../../api/weatherOverlayApi';
import { useWeatherOverlay } from '../hooks/useWeatherOverlay';

describe('useWeatherOverlay extra coverage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('resets immediately when requests are disabled', () => {
    const { result } = renderHook(() =>
      useWeatherOverlay({
        geographyId: 'citywide',
        timeRangeStart: '2026-03-01T00:00:00Z',
        timeRangeEnd: '2026-03-02T00:00:00Z',
        overlayEnabled: true,
        weatherMeasure: 'temperature',
        requestEnabled: false,
      }),
    );

    expect(result.current.overlay).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('passes an undefined weather measure when overlay is disabled and supports clear/report helpers', async () => {
    vi.mocked(fetchWeatherOverlay).mockResolvedValue({
      overlayRequestId: 'overlay-1',
      overlayStatus: 'visible',
      observations: [],
    } as never);

    const { result } = renderHook(() =>
      useWeatherOverlay({
        geographyId: 'citywide',
        timeRangeStart: '2026-03-01T00:00:00Z',
        timeRangeEnd: '2026-03-02T00:00:00Z',
        overlayEnabled: false,
        weatherMeasure: 'temperature',
        requestEnabled: true,
      }),
    );

    await waitFor(() => {
      expect(result.current.overlay?.overlayRequestId).toBe('overlay-1');
    });

    expect(fetchWeatherOverlay).toHaveBeenCalledWith(
      expect.objectContaining({ weatherMeasure: undefined }),
    );

    await act(async () => {
      await result.current.reportRenderSuccess();
      await result.current.reportRenderFailure('chart failed');
    });

    expect(submitWeatherOverlayRenderEvent).toHaveBeenCalledTimes(2);

    act(() => {
      result.current.clearOverlay();
    });

    expect(result.current.overlay).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isLoading).toBe(false);
  });

  it('does nothing when reporting without an overlay and surfaces request errors', async () => {
    vi.mocked(fetchWeatherOverlay).mockRejectedValue(new Error('overlay failed'));

    const { result } = renderHook(() =>
      useWeatherOverlay({
        geographyId: 'citywide',
        timeRangeStart: '2026-03-01T00:00:00Z',
        timeRangeEnd: '2026-03-02T00:00:00Z',
        overlayEnabled: true,
        weatherMeasure: 'temperature',
        requestEnabled: true,
      }),
    );

    await waitFor(() => {
      expect(result.current.error).toBe('overlay failed');
    });

    await act(async () => {
      await result.current.reportRenderSuccess();
      await result.current.reportRenderFailure('unused');
    });

    expect(submitWeatherOverlayRenderEvent).not.toHaveBeenCalled();
  });
});
