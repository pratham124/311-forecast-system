import { useEffect, useRef, useState } from 'react';
import { fetchCurrentPublicForecast, submitPublicForecastDisplayEvent, type PublicForecastProduct } from '../../../api/publicForecastApi';
import type { PublicForecastDisplayEventRequest, PublicForecastView } from '../../../types/publicForecast';

export function usePublicForecast() {
  const [forecastProduct, setForecastProduct] = useState<PublicForecastProduct>('daily');
  const [forecast, setForecast] = useState<PublicForecastView | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const reported = useRef<Record<string, boolean>>({});

  useEffect(() => {
    const controller = new AbortController();
    setIsLoading(true);
    setError(null);
    fetchCurrentPublicForecast(forecastProduct, controller.signal)
      .then((response) => {
        if (!controller.signal.aborted) {
          setForecast(response);
        }
      })
      .catch((requestError: Error) => {
        if (controller.signal.aborted) {
          return;
        }
        setError(requestError.message);
        setForecast(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      });
    return () => controller.abort();
  }, [forecastProduct]);

  const reportDisplayEvent = async (payload: PublicForecastDisplayEventRequest) => {
    if (!forecast) return;
    const key = `${forecast.publicForecastRequestId}:${payload.displayOutcome}`;
    if (reported.current[key]) return;
    reported.current[key] = true;
    await submitPublicForecastDisplayEvent(forecast.publicForecastRequestId, payload);
  };

  return {
    forecastProduct,
    setForecastProduct,
    forecast,
    isLoading,
    error,
    reportDisplayEvent,
  };
}
