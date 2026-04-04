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
  const now = new Date();
  const end = now.toISOString();
  const startDate = new Date(now);
  startDate.setUTCDate(startDate.getUTCDate() - 30);
  const start = startDate.toISOString();
  return {
    timeRangeStart: start,
    timeRangeEnd: end,
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
    if (!nextFilters.timeRangeStart || !nextFilters.timeRangeEnd) {
      setError('Select both a start date and an end date.');
      setResponse(null);
      setIsSubmitting(false);
      return null;
    }
    if (nextFilters.timeRangeStart > nextFilters.timeRangeEnd) {
      setError('Select a valid date range. The end date must be on or after the start date.');
      setResponse(null);
      setIsSubmitting(false);
      return null;
    }
    setIsSubmitting(true);
    setError(null);
    try {
      const nextResponse = await submitHistoricalDemandQuery({ ...nextFilters, proceedAfterWarning: proceedAfterWarning || undefined });
      setResponse(nextResponse);
      setIsSubmitting(false);
      return nextResponse;
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to load historical demand data.');
      setResponse(null);
      setIsSubmitting(false);
      return null;
    }
  };

  const reportRenderEvent = async (payload: HistoricalDemandRenderEvent) => {
    if (!response?.analysisRequestId) return;
    const key = `${response.analysisRequestId}:${payload.renderStatus}`;
    if (renderedEvents.current[key]) return;
    renderedEvents.current[key] = true;
    try {
      await submitHistoricalDemandRenderEvent(response.analysisRequestId, payload);
    } catch (requestError) {
      console.error('Failed to submit historical demand render event', requestError);
    }
  };

  const clearResponse = () => {
    setResponse(null);
    setError(null);
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
    clearResponse,
  };
}
