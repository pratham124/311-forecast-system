import { useEffect, useRef, useState } from 'react';
import { fetchWeatherOverlay, submitWeatherOverlayRenderEvent } from '../../../api/weatherOverlayApi';
import type { WeatherMeasure, WeatherOverlayResponse } from '../../../types/weatherOverlay';

interface UseWeatherOverlayInput {
  geographyId: string;
  timeRangeStart: string;
  timeRangeEnd: string;
  overlayEnabled: boolean;
  weatherMeasure: WeatherMeasure;
}

export function useWeatherOverlay({ geographyId, timeRangeStart, timeRangeEnd, overlayEnabled, weatherMeasure }: UseWeatherOverlayInput) {
  const [overlay, setOverlay] = useState<WeatherOverlayResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const selectionIdRef = useRef(0);

  useEffect(() => {
    const controller = new AbortController();
    const currentSelectionId = ++selectionIdRef.current;

    // Clear stale overlay state immediately on any selection change.
    setOverlay(null);
    setIsLoading(true);
    setError(null);

    fetchWeatherOverlay({
      geographyId,
      timeRangeStart,
      timeRangeEnd,
      weatherMeasure: overlayEnabled ? weatherMeasure : undefined,
      signal: controller.signal,
    })
      .then((response) => {
        if (controller.signal.aborted) return;
        if (currentSelectionId !== selectionIdRef.current) return;
        setOverlay(response);
      })
      .catch((requestError: Error) => {
        if (controller.signal.aborted) return;
        if (currentSelectionId !== selectionIdRef.current) return;
        setError(requestError.message);
        setOverlay(null);
      })
      .finally(() => {
        if (!controller.signal.aborted && currentSelectionId === selectionIdRef.current) {
          setIsLoading(false);
        }
      });

    return () => {
      controller.abort();
    };
  }, [geographyId, overlayEnabled, timeRangeEnd, timeRangeStart, weatherMeasure]);

  const reportRenderSuccess = async () => {
    if (!overlay) return;
    await submitWeatherOverlayRenderEvent({
      overlayRequestId: overlay.overlayRequestId,
      overlayStatus: overlay.overlayStatus,
      isLatestSelection: true,
      payload: { renderStatus: 'rendered', reportedAt: new Date().toISOString() },
    });
  };

  const reportRenderFailure = async (failureReason: string) => {
    if (!overlay) return;
    await submitWeatherOverlayRenderEvent({
      overlayRequestId: overlay.overlayRequestId,
      overlayStatus: overlay.overlayStatus,
      isLatestSelection: true,
      payload: { renderStatus: 'failed-to-render', reportedAt: new Date().toISOString(), failureReason },
    });
  };

  const clearOverlay = () => {
    setOverlay(null);
    setIsLoading(false);
    setError(null);
  };

  return {
    overlay,
    isLoading,
    error,
    clearOverlay,
    reportRenderSuccess,
    reportRenderFailure,
  };
}
