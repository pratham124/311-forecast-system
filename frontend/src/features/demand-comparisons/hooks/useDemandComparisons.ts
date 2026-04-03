import { useEffect, useMemo, useRef, useState } from 'react';
import {
  fetchDemandComparisonAvailability,
  submitDemandComparisonQuery,
  submitDemandComparisonRenderEvent,
} from '../../../api/demandComparisons';
import type {
  DatePreset,
  DemandComparisonAvailability,
  DemandComparisonFilters,
  DemandComparisonRenderEvent,
  DemandComparisonResponse,
} from '../../../types/demandComparisons';

interface DateWindow {
  start?: string;
  end?: string;
}

export function isLikelyNetworkTransportError(message: string): boolean {
  const normalized = message.trim().toLowerCase();
  return (
    normalized === 'load failed'
    || normalized === 'failed to fetch'
    || normalized.includes('networkerror when attempting to fetch resource')
  );
}

export function toDisplayError(
  error: unknown,
  genericMessage: string,
  networkMessage: string,
): string {
  if (error instanceof Error) {
    const message = error.message.trim();
    if (!message) {
      return genericMessage;
    }
    if (isLikelyNetworkTransportError(message)) {
      return networkMessage;
    }
    return message;
  }
  return genericMessage;
}

export function uniqueStrings(values: string[]): string[] {
  return Array.from(new Set(values.filter((value) => value.trim().length > 0)));
}

export function defaultDateRange(): Pick<DemandComparisonFilters, 'timeRangeStart' | 'timeRangeEnd'> {
  const now = new Date();
  const start = new Date(now);
  start.setUTCHours(0, 0, 0, 0);
  const end = new Date(now);
  end.setUTCDate(end.getUTCDate() + 7);
  return {
    timeRangeStart: start.toISOString(),
    timeRangeEnd: end.toISOString(),
  };
}

export function parseIso(value?: string): Date | null {
  if (!value) {
    return null;
  }
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function clampIso(value: string, minIso?: string, maxIso?: string): string {
  const date = parseIso(value);
  if (!date) {
    return value;
  }
  const minDate = parseIso(minIso);
  if (minDate && date < minDate) {
    return minDate.toISOString();
  }
  const maxDate = parseIso(maxIso);
  if (maxDate && date > maxDate) {
    return maxDate.toISOString();
  }
  return date.toISOString();
}

export function getDateWindow(availability: DemandComparisonAvailability | null): DateWindow {
  if (!availability) {
    return {};
  }
  const dateConstraints = availability.dateConstraints ?? {};
  // Allow the full data span so users can query historical-only ranges even when
  // no overlap with the active forecast exists.
  const startOptions = [dateConstraints.historicalMin, dateConstraints.forecastMin].filter(
    (value): value is string => Boolean(value),
  );
  const endOptions = [dateConstraints.historicalMax, dateConstraints.forecastMax].filter(
    (value): value is string => Boolean(value),
  );
  const start = startOptions.reduce<string | undefined>((min, val) => {
    if (!min) return val;
    return val < min ? val : min;
  }, undefined);
  const end = endOptions.reduce<string | undefined>((max, val) => {
    if (!max) return val;
    return val > max ? val : max;
  }, undefined);
  return { start, end };
}

export function validateDateRange(filters: DemandComparisonFilters, dateWindow: DateWindow): string | null {
  const start = parseIso(filters.timeRangeStart);
  const end = parseIso(filters.timeRangeEnd);
  if (!start || !end) {
    return 'Select a valid start and end date.';
  }
  if (end < start) {
    return 'End date must be on or after the start date.';
  }

  const minDate = parseIso(dateWindow.start);
  if (minDate && start < minDate) {
    return 'Start date is outside the available comparison window.';
  }

  const maxDate = parseIso(dateWindow.end);
  if (maxDate && end > maxDate) {
    return 'End date is outside the available comparison window.';
  }

  return null;
}

export function applyAvailabilityRules(
  filters: DemandComparisonFilters,
  availability: DemandComparisonAvailability,
  dateWindow: DateWindow,
): DemandComparisonFilters {
  const serviceCategories = filters.serviceCategories.filter((category) =>
    availability.serviceCategories.includes(category),
  );

  const timeRangeStart = clampIso(filters.timeRangeStart, dateWindow.start, dateWindow.end);
  let timeRangeEnd = clampIso(filters.timeRangeEnd, dateWindow.start, dateWindow.end);
  const startDate = parseIso(timeRangeStart);
  const endDate = parseIso(timeRangeEnd);
  if (startDate && endDate && endDate < startDate) {
    timeRangeEnd = timeRangeStart;
  }

  return {
    ...filters,
    serviceCategories,
    geographyLevel: undefined,
    geographyValues: [],
    timeRangeStart,
    timeRangeEnd,
  };
}

export function expandAllCategoriesSelection(
  filters: DemandComparisonFilters,
  availability: DemandComparisonAvailability | null,
): DemandComparisonFilters {
  if (!availability || filters.serviceCategories.length > 0) {
    return filters;
  }
  return {
    ...filters,
    serviceCategories: [...availability.serviceCategories],
  };
}

export function pickPreferredPreset(presets: DatePreset[]): DatePreset | undefined {
  return presets.find((preset) => preset.label.toLowerCase().includes('overlap')) ?? presets[0];
}

export function buildDefaultAutoSelection(
  availability: DemandComparisonAvailability,
  dateWindow: DateWindow,
  fallbackFilters: DemandComparisonFilters,
): DemandComparisonFilters | null {
  const serviceCategory = availability.serviceCategories[0];
  if (!serviceCategory) {
    return null;
  }

  const serviceCategories = [serviceCategory];
  const preferredPreset = pickPreferredPreset(availability.presets);

  return {
    serviceCategories,
    geographyLevel: undefined,
    geographyValues: [],
    timeRangeStart: preferredPreset?.timeRangeStart ?? dateWindow.start ?? fallbackFilters.timeRangeStart,
    timeRangeEnd: preferredPreset?.timeRangeEnd ?? dateWindow.end ?? fallbackFilters.timeRangeEnd,
  };
}

type FiltersUpdate = DemandComparisonFilters | ((current: DemandComparisonFilters) => DemandComparisonFilters);

export function useDemandComparisons() {
  const [availability, setAvailability] = useState<DemandComparisonAvailability | null>(null);
  const [filters, setFiltersState] = useState<DemandComparisonFilters>({
    serviceCategories: [],
    geographyValues: [],
    ...defaultDateRange(),
  });
  const [response, setResponse] = useState<DemandComparisonResponse | null>(null);
  const [isLoadingAvailability, setIsLoadingAvailability] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isAutoSelecting, setIsAutoSelecting] = useState(false);
  const [autoSelectProgress, setAutoSelectProgress] = useState({ current: 0, total: 0 });
  const [error, setError] = useState<string | null>(null);
  const lastRequestToken = useRef(0);
  const renderEvents = useRef<Record<string, boolean>>({});

  const dateWindow = useMemo(() => getDateWindow(availability), [availability]);
  const datePresets = useMemo(() => availability?.presets ?? [], [availability]);
  const dateRangeError = useMemo(
    () => validateDateRange(filters, dateWindow),
    [filters, dateWindow],
  );

  useEffect(() => {
    const controller = new AbortController();
    fetchDemandComparisonAvailability(controller.signal)
      .then((payload) => {
        const nextDateWindow = getDateWindow(payload);
        setAvailability(payload);
        setFiltersState((current) => applyAvailabilityRules(current, payload, nextDateWindow));
      })
      .catch((requestError: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            toDisplayError(
              requestError,
              'Unable to load comparison filters.',
              'Unable to load comparison filters. Check your connection and try again.',
            ),
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoadingAvailability(false);
        }
      });
    return () => controller.abort();
  }, []);

  const setFilters = (update: FiltersUpdate) => {
    setFiltersState((current) => {
      const next = typeof update === 'function' ? update(current) : update;
      if (!availability) {
        return next;
      }
      return applyAvailabilityRules(next, availability, dateWindow);
    });
    setResponse(null);
    setError(null);
  };

  const submit = async (overrides?: Partial<DemandComparisonFilters>, proceedAfterWarning = false) => {
    const mergedFilters = { ...filters, ...overrides };
    const availabilityScopedFilters = availability
      ? applyAvailabilityRules(mergedFilters, availability, dateWindow)
      : mergedFilters;
    const nextFilters = expandAllCategoriesSelection(availabilityScopedFilters, availability);
    const nextRangeError = validateDateRange(nextFilters, dateWindow);
    setFiltersState(nextFilters);

    if (nextRangeError) {
      setError(nextRangeError);
      setResponse(null);
      setIsSubmitting(false);
      return null;
    }

    setIsSubmitting(true);
    setError(null);
    setResponse(null);
    const requestToken = ++lastRequestToken.current;

    let nextResponse: DemandComparisonResponse | null = null;
    let requestError: unknown = null;

    try {
      nextResponse = await submitDemandComparisonQuery(
        { ...nextFilters, proceedAfterWarning: proceedAfterWarning || undefined },
      );
    } catch (err) {
      requestError = err;
    }

    if (requestError) {
      if (requestToken === lastRequestToken.current) {
        setError(
          toDisplayError(
            requestError,
            'Unable to compare demand.',
            'Unable to compare demand. Check your connection and try again.',
          ),
        );
        setResponse(null);
        setIsSubmitting(false);
      }
      return null;
    }

    if (requestToken === lastRequestToken.current) {
      setResponse(nextResponse);
      setIsSubmitting(false);
    }
    return nextResponse;
  };

  const autoSelectForecastBackedCombination = async () => {
    if (!availability) {
      setError('Comparison filters are still loading. Please try again in a moment.');
      return null;
    }

    const candidate = buildDefaultAutoSelection(availability, dateWindow, filters);
    if (!candidate) {
      setError('No forecast-backed categories are available for the selected window.');
      return null;
    }

    setIsAutoSelecting(true);
    setAutoSelectProgress({ current: 1, total: 1 });
    try {
      return await submit(candidate, true);
    } finally {
      setIsAutoSelecting(false);
      setAutoSelectProgress({ current: 0, total: 0 });
    }
  };

  const applyDatePreset = (preset: DatePreset) => {
    setFilters((current) => ({
      ...current,
      timeRangeStart: preset.timeRangeStart,
      timeRangeEnd: preset.timeRangeEnd,
    }));
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
    availability,
    filters,
    setFilters,
    dateWindowStart: dateWindow.start,
    dateWindowEnd: dateWindow.end,
    datePresets,
    dateRangeError,
    response,
    isLoadingAvailability,
    isSubmitting,
    isAutoSelecting,
    autoSelectProgress,
    error,
    submit,
    autoSelectForecastBackedCombination,
    applyDatePreset,
    reportRenderEvent,
    clearResponse,
  };
}
