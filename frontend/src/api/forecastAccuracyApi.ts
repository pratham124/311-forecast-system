import { env } from '../config/env';
import { getAccessToken } from '../lib/authSession';
import { refreshStoredSession } from './auth';
import type {
  ForecastAccuracyFilters,
  ForecastAccuracyRenderEvent,
  ForecastAccuracyRenderEventResponse,
  ForecastAccuracyResponse,
} from '../types/forecastAccuracy';

function buildHeaders(contentType?: string): Headers {
  const headers = new Headers();
  const accessToken = getAccessToken();
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }
  if (contentType) {
    headers.set('Content-Type', contentType);
  }
  return headers;
}

async function fetchWithAuthRetry(input: string, init: RequestInit = {}): Promise<Response> {
  const contentType = init.body ? 'application/json' : undefined;
  let response = await fetch(input, { ...init, headers: buildHeaders(contentType) });
  if (response.status !== 401) {
    return response;
  }
  await refreshStoredSession();
  response = await fetch(input, { ...init, headers: buildHeaders(contentType) });
  return response;
}

function buildQuery(filters: ForecastAccuracyFilters): string {
  const search = new URLSearchParams();
  if (filters.timeRangeStart) search.set('timeRangeStart', filters.timeRangeStart);
  if (filters.timeRangeEnd) search.set('timeRangeEnd', filters.timeRangeEnd);
  if (filters.serviceCategory) search.set('serviceCategory', filters.serviceCategory);
  return search.toString();
}

export async function fetchForecastAccuracy(filters: ForecastAccuracyFilters, signal?: AbortSignal): Promise<ForecastAccuracyResponse> {
  const query = buildQuery(filters);
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/forecast-accuracy${query ? `?${query}` : ''}`, { signal });
  if (!response.ok) {
    throw new Error(`Forecast accuracy request failed with status ${response.status}`);
  }
  return response.json() as Promise<ForecastAccuracyResponse>;
}

export async function submitForecastAccuracyRenderEvent(
  forecastAccuracyRequestId: string,
  payload: ForecastAccuracyRenderEvent,
): Promise<ForecastAccuracyRenderEventResponse> {
  const response = await fetchWithAuthRetry(
    `${env.apiBaseUrl}/api/v1/forecast-accuracy/${forecastAccuracyRequestId}/render-events`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
  );
  if (!response.ok) {
    throw new Error(`Forecast accuracy render event failed with status ${response.status}`);
  }
  return response.json() as Promise<ForecastAccuracyRenderEventResponse>;
}
