import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { useWeatherOverlay } from '../hooks/useWeatherOverlay';

vi.mock('../../../api/weatherOverlayApi', () => {
  return {
    fetchWeatherOverlay: vi.fn(),
    submitWeatherOverlayRenderEvent: vi.fn(),
  };
});

import { fetchWeatherOverlay } from '../../../api/weatherOverlayApi';

describe('useWeatherOverlay sync', () => {
  it('keeps only latest selection response', async () => {
    const pending: Array<(value: unknown) => void> = [];
    vi.mocked(fetchWeatherOverlay).mockImplementation(
      () => new Promise((resolve) => pending.push(resolve as (value: unknown) => void)) as Promise<any>,
    );

    type HookProps = {
      geographyId: string;
      timeRangeStart: string;
      timeRangeEnd: string;
      overlayEnabled: boolean;
      weatherMeasure: 'temperature' | 'snowfall';
    };

    const { result, rerender } = renderHook<ReturnType<typeof useWeatherOverlay>, HookProps>(
      (props) => useWeatherOverlay(props),
      {
        initialProps: {
          geographyId: 'citywide',
          timeRangeStart: '2026-03-20T00:00:00Z',
          timeRangeEnd: '2026-03-20T01:00:00Z',
          overlayEnabled: true,
          weatherMeasure: 'temperature',
        } satisfies HookProps,
      },
    );

    rerender({
      geographyId: 'citywide',
      timeRangeStart: '2026-03-20T00:00:00Z',
      timeRangeEnd: '2026-03-20T01:00:00Z',
      overlayEnabled: true,
      weatherMeasure: 'snowfall',
    } satisfies HookProps);

    await act(async () => {
      pending[0]({
        overlayRequestId: 'old',
        geographyId: 'citywide',
        timeRangeStart: '2026-03-20T00:00:00Z',
        timeRangeEnd: '2026-03-20T01:00:00Z',
        weatherMeasure: 'temperature',
        overlayStatus: 'visible',
        baseForecastPreserved: true,
        userVisible: true,
        observations: [{ timestamp: '2026-03-20T00:00:00Z', value: 1 }],
        stateSource: 'overlay-assembly',
      });
      pending[1]({
        overlayRequestId: 'new',
        geographyId: 'citywide',
        timeRangeStart: '2026-03-20T00:00:00Z',
        timeRangeEnd: '2026-03-20T01:00:00Z',
        weatherMeasure: 'snowfall',
        overlayStatus: 'visible',
        baseForecastPreserved: true,
        userVisible: true,
        observations: [{ timestamp: '2026-03-20T00:00:00Z', value: 2 }],
        stateSource: 'overlay-assembly',
      });
      await Promise.resolve();
    });

    expect(result.current.overlay?.overlayRequestId).toBe('new');
    expect(result.current.overlay?.weatherMeasure).toBe('snowfall');
  });
});
