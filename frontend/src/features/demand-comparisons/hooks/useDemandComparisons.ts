import { useEffect, useRef, useState } from 'react';
import {
  fetchDemandComparisonContext,
  submitDemandComparisonQuery,
  submitDemandComparisonRenderEvent,
} from '../../../api/demandComparisons';
import type {
  DemandComparisonContext,
  DemandComparisonFilters,
  DemandComparisonRenderEvent,
  DemandComparisonResponse,
} from '../../../types/demandComparisons';

function defaultDateRange(): Pick<DemandComparisonFilters, 'timeRangeStart' | 'timeRangeEnd'> {
  const now = new Date();
  const end = now.toISOString();
  const startDate = new Date(now);
  startDate.setUTCDate(startDate.getUTCDate() - 7);
  return {
    timeRangeStart: startDate.toISOString(),
    timeRangeEnd: end,
  };
}

export function useDemandComparisons() {
  const [context, setContext] = useState<DemandComparisonContext | null>(null);
  const [filters, setFilters] = useState<DemandComparisonFilters>({
    serviceCategories: [],
    geographyValues: [],
    ...defaultDateRange(),
  });
  const [response, setResponse] = useState<DemandComparisonResponse | null>(null);
  const [isLoadingContext, setIsLoadingContext] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const lastRequestToken = useRef(0);
  const renderEvents = useRef<Record<string, boolean>>({});

  useEffect(() => {
    const controller = new AbortController();
    fetchDemandComparisonContext(controller.signal)
      .then((payload) => {
        setContext(payload);
        setFilters((current) => ({
          ...current,
          serviceCategories: current.serviceCategories.length ? current.serviceCategories : payload.serviceCategories.slice(0, 1),
          geographyLevel: current.geographyLevel ?? payload.geographyLevels[0],
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

  const submit = async (overrides?: Partial<DemandComparisonFilters>, proceedAfterWarning = false) => {
    const nextFilters = { ...filters, ...overrides };
    setFilters(nextFilters);
    setIsSubmitting(true);
    setError(null);
    setResponse(null);
    const requestToken = ++lastRequestToken.current;
    try {
      const nextResponse = await submitDemandComparisonQuery(
        { ...nextFilters, proceedAfterWarning: proceedAfterWarning || undefined },
      );
      if (requestToken === lastRequestToken.current) {
        setResponse(nextResponse);
      }
      return nextResponse;
    } catch (requestError) {
      if (requestToken === lastRequestToken.current) {
        setError(requestError instanceof Error ? requestError.message : 'Unable to compare demand.');
        setResponse(null);
      }
      return null;
    } finally {
      if (requestToken === lastRequestToken.current) {
        setIsSubmitting(false);
      }
    }
  };

  const reportRenderEvent = async (payload: DemandComparisonRenderEvent) => {
    if (!response?.comparisonRequestId) {
      return;
    }
    const key = `${response.comparisonRequestId}:${payload.renderStatus}`;
    if (renderEvents.current[key]) {
      return;
    }
    renderEvents.current[key] = true;
    try {
      await submitDemandComparisonRenderEvent(response.comparisonRequestId, payload);
    } catch (requestError) {
      console.error('Failed to submit demand comparison render event', requestError);
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
