import { useEffect, useRef, useState } from 'react';
import {
  fetchHistoricalDemandContext,
  submitHistoricalDemandQuery,
  submitHistoricalDemandRenderEvent,
} from '../../../api/historicalDemand';
import type {
  HistoricalDemandContext,
  HistoricalDemandFilters,
  HistoricalDemandResponse,
  HistoricalDemandRenderEvent,
} from '../../../types/historicalDemand';

function defaultDateRange(): Pick<HistoricalDemandFilters, 'timeRangeStart' | 'timeRangeEnd'> {
  return {
    timeRangeStart: '2026-03-01T00:00:00Z',
    timeRangeEnd: '2026-03-31T23:59:59Z',
  };
}

export function useHistoricalDemand() {
  const [context, setContext] = useState<HistoricalDemandContext | null>(null);
  const [filters, setFilters] = useState<HistoricalDemandFilters>(defaultDateRange());
  const [response, setResponse] = useState<HistoricalDemandResponse | null>(null);
  const [isLoadingContext, setIsLoadingContext] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const renderedEvents = useRef<Record<string, boolean>>({});

  useEffect(() => {
    const controller = new AbortController();
    fetchHistoricalDemandContext(controller.signal)
      .then((payload) => {
        setContext(payload);
        setFilters((current) => ({
          ...current,
          serviceCategory: current.serviceCategory ?? payload.serviceCategories[0],
          geographyLevel: current.geographyLevel ?? payload.supportedGeographyLevels[0],
        }));
      })
      .catch((requestError: Error) => {
        if (!controller.signal.aborted) {
          setError(requestError.message);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoadingContext(false);
        }
      });
    return () => controller.abort();
  }, []);

  const submit = async (overrides?: Partial<HistoricalDemandFilters>, proceedAfterWarning = false) => {
    const nextFilters = { ...filters, ...overrides };
    setFilters(nextFilters);
    setIsSubmitting(true);
    setError(null);
    try {
      const nextResponse = await submitHistoricalDemandQuery({ ...nextFilters, proceedAfterWarning: proceedAfterWarning || undefined });
      setResponse(nextResponse);
      return nextResponse;
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to load historical demand data.');
      setResponse(null);
      return null;
    } finally {
      setIsSubmitting(false);
    }
  };

  const reportRenderEvent = async (payload: HistoricalDemandRenderEvent) => {
    if (!response?.analysisRequestId) return;
    const key = `${response.analysisRequestId}:${payload.renderStatus}`;
    if (renderedEvents.current[key]) return;
    renderedEvents.current[key] = true;
    await submitHistoricalDemandRenderEvent(response.analysisRequestId, payload);
  };

  return {
    context,
    filters,
    setFilters,
    response,
    isLoadingContext,
    isSubmitting,
    error,
    submit,
    reportRenderEvent,
  };
}
