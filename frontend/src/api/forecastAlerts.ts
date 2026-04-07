import { env } from '../config/env';
import { getAccessToken } from '../lib/authSession';
import { refreshStoredSession } from './auth';
import type {
  ThresholdAlertEvent,
  ThresholdAlertEventListResponse,
  ThresholdConfiguration,
  ThresholdConfigurationListResponse,
  ThresholdConfigurationUpdateRequest,
} from '../types/forecastAlerts';

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function buildHeaders(contentType?: string): Headers {
  const headers = new Headers();
  const accessToken = getAccessToken();
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`);
  if (contentType) headers.set('Content-Type', contentType);
  return headers;
}

async function fetchWithAuthRetry(input: string, init: RequestInit = {}): Promise<Response> {
  let response = await fetch(input, { ...init, headers: buildHeaders('application/json') });
  if (response.status !== 401) return response;
  await refreshStoredSession();
  response = await fetch(input, { ...init, headers: buildHeaders('application/json') });
  return response;
}

async function parseApiError(response: Response, fallback: string): Promise<ApiError> {
  try {
    const body = (await response.json()) as { detail?: string };
    return new ApiError(response.status, body.detail ?? fallback);
  } catch {
    return new ApiError(response.status, fallback);
  }
}

export async function listThresholdAlertEvents(signal?: AbortSignal): Promise<ThresholdAlertEventListResponse> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/forecast-alerts/events`, { method: 'GET', signal });
  if (!response.ok) {
    throw await parseApiError(response, `Alert event list request failed with status ${response.status}`);
  }
  return response.json() as Promise<ThresholdAlertEventListResponse>;
}

export async function getThresholdAlertEvent(notificationEventId: string, signal?: AbortSignal): Promise<ThresholdAlertEvent> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/forecast-alerts/events/${notificationEventId}`, { method: 'GET', signal });
  if (!response.ok) {
    throw await parseApiError(response, `Alert event detail request failed with status ${response.status}`);
  }
  return response.json() as Promise<ThresholdAlertEvent>;
}

export async function updateThresholdConfiguration(payload: ThresholdConfigurationUpdateRequest): Promise<ThresholdConfiguration> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/forecast-alerts/threshold-configurations`, {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw await parseApiError(response, `Threshold update failed with status ${response.status}`);
  }
  return response.json() as Promise<ThresholdConfiguration>;
}

export async function listThresholdConfigurations(signal?: AbortSignal): Promise<ThresholdConfigurationListResponse> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/forecast-alerts/threshold-configurations?forecastWindowType=global`, {
    method: 'GET',
    signal,
  });
  if (!response.ok) {
    throw await parseApiError(response, `Threshold configuration list request failed with status ${response.status}`);
  }
  return response.json() as Promise<ThresholdConfigurationListResponse>;
}

export async function listDailyForecastCategories(signal?: AbortSignal): Promise<string[]> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/forecasts/current`, {
    method: 'GET',
    signal,
  });
  if (response.status === 404) {
    return [];
  }
  if (!response.ok) {
    throw await parseApiError(response, `Daily forecast category request failed with status ${response.status}`);
  }
  const payload = (await response.json()) as { buckets?: Array<{ serviceCategory?: string }> };
  const categories = new Set<string>();
  for (const bucket of payload.buckets ?? []) {
    const category = bucket?.serviceCategory;
    if (typeof category === 'string' && category.trim()) {
      categories.add(category.trim());
    }
  }
  return Array.from(categories).sort((a, b) => a.localeCompare(b));
}
