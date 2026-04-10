import { useEffect, useRef, useState } from 'react';
import { fetchForecastAccuracy, submitForecastAccuracyRenderEvent } from '../../../api/forecastAccuracyApi';
import { fetchServiceCategoryOptions } from '../../../api/forecastVisualizations';
import type {
  ForecastAccuracyFilters,
  ForecastAccuracyRenderEvent,
  ForecastAccuracyResponse,
} from '../../../types/forecastAccuracy';

export function defaultForecastAccuracyRange(): Required<Pick<ForecastAccuracyFilters, 'timeRangeStart' | 'timeRangeEnd'>> {
  const now = new Date();
  const end = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate()));
  const start = new Date(end);
  start.setUTCDate(start.getUTCDate() - 30);
  return {
    timeRangeStart: start.toISOString(),
    timeRangeEnd: end.toISOString(),
  };
}

export function useForecastAccuracy() {
  const [filters, setFilters] = useState<ForecastAccuracyFilters>(defaultForecastAccuracyRange());
  const [serviceCategoryOptions, setServiceCategoryOptions] = useState<string[]>([]);
  const [response, setResponse] = useState<ForecastAccuracyResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const renderEvents = useRef<Record<string, boolean>>({});

  useEffect(() => {
    const controller = new AbortController();
    fetchServiceCategoryOptions('daily_1_day', controller.signal)
      .then((payload) => {
        if (!controller.signal.aborted) {
          setServiceCategoryOptions(payload.categories);
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) {
          setServiceCategoryOptions([]);
        }
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    fetchForecastAccuracy(filters, controller.signal)
      .then((payload) => {
        setResponse(payload);
      })
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) {
          setError(requestError instanceof Error ? requestError.message : 'Unable to load forecast accuracy.');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      });
    return () => controller.abort();
  }, []);

  const submit = async (overrides?: Partial<ForecastAccuracyFilters>) => {
    const nextFilters = { ...filters, ...overrides };
    setFilters(nextFilters);
    setIsSubmitting(true);
    setError(null);
    try {
      const payload = await fetchForecastAccuracy(nextFilters);
      setResponse(payload);
      setIsSubmitting(false);
      return payload;
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to load forecast accuracy.');
      setResponse(null);
      setIsSubmitting(false);
      return null;
    }
  };

  const reportRenderEvent = async (payload: ForecastAccuracyRenderEvent) => {
    if (!response?.forecastAccuracyRequestId) return;
    const key = `${response.forecastAccuracyRequestId}:${payload.renderStatus}`;
    if (renderEvents.current[key]) return;
    renderEvents.current[key] = true;
    try {
      await submitForecastAccuracyRenderEvent(response.forecastAccuracyRequestId, payload);
    } catch (requestError) {
      console.error('Failed to submit forecast accuracy render event', requestError);
    }
  };

  return {
    filters,
    setFilters,
    serviceCategoryOptions,
    response,
    isLoading,
    isSubmitting,
    error,
    submit,
    reportRenderEvent,
  };
}
