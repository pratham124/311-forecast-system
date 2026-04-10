import { env } from '../config/env';
import type {
  ThresholdAlertEvent,
  ThresholdAlertEventSummary,
  ThresholdConfiguration,
  ThresholdConfigurationWrite,
  ThresholdEvaluationTriggerResponse,
} from '../types/forecastAlerts';
import { buildHeaders, contentTypeFromHeaders, ApiError } from './evaluations';
import { refreshStoredSession } from './auth';

async function fetchWithAuthRetry(input: string, init: RequestInit = {}): Promise<Response> {
  const contentType = contentTypeFromHeaders(init.headers);
  let response = await fetch(input, { ...init, headers: buildHeaders(contentType) });
  if (response.status !== 401) {
    return response;
  }
  await refreshStoredSession();
  response = await fetch(input, { ...init, headers: buildHeaders(contentType) });
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

export async function triggerThresholdEvaluation(payload: {
  forecastReferenceId: string;
  forecastProduct: 'daily' | 'weekly';
  triggerSource: 'forecast_publish' | 'forecast_refresh' | 'scheduled_recheck' | 'manual_replay';
}): Promise<ThresholdEvaluationTriggerResponse> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/forecast-alerts/evaluations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw await parseApiError(response, `Threshold evaluation failed with status ${response.status}`);
  }
  return response.json() as Promise<ThresholdEvaluationTriggerResponse>;
}

export async function fetchThresholdAlertEvents(): Promise<ThresholdAlertEventSummary[]> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/forecast-alerts/events`);
  if (!response.ok) {
    throw await parseApiError(response, `Alert event request failed with status ${response.status}`);
  }
  const body = (await response.json()) as { items: ThresholdAlertEventSummary[] };
  return body.items;
}

export async function fetchThresholdAlertConfigurations(): Promise<ThresholdConfiguration[]> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/forecast-alerts/thresholds`);
  if (!response.ok) {
    throw await parseApiError(response, `Threshold configuration request failed with status ${response.status}`);
  }
  const body = (await response.json()) as { items: ThresholdConfiguration[] };
  return body.items;
}

export async function createThresholdConfiguration(payload: ThresholdConfigurationWrite): Promise<ThresholdConfiguration> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/forecast-alerts/thresholds`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw await parseApiError(response, `Threshold save failed with status ${response.status}`);
  }
  return response.json() as Promise<ThresholdConfiguration>;
}

export async function updateThresholdConfiguration(
  thresholdConfigurationId: string,
  payload: ThresholdConfigurationWrite,
): Promise<ThresholdConfiguration> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/forecast-alerts/thresholds/${thresholdConfigurationId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw await parseApiError(response, `Threshold update failed with status ${response.status}`);
  }
  return response.json() as Promise<ThresholdConfiguration>;
}

export async function deleteThresholdConfiguration(thresholdConfigurationId: string): Promise<void> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/forecast-alerts/thresholds/${thresholdConfigurationId}`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw await parseApiError(response, `Threshold delete failed with status ${response.status}`);
  }
}

export async function fetchThresholdServiceCategories(): Promise<string[]> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/forecast-alerts/service-categories`);
  if (!response.ok) {
    throw await parseApiError(response, `Threshold service category request failed with status ${response.status}`);
  }
  const body = (await response.json()) as { items: string[] };
  return body.items;
}

export async function fetchThresholdAlertEvent(notificationEventId: string): Promise<ThresholdAlertEvent> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/forecast-alerts/events/${notificationEventId}`);
  if (!response.ok) {
    throw await parseApiError(response, `Alert detail request failed with status ${response.status}`);
  }
  return response.json() as Promise<ThresholdAlertEvent>;
}
