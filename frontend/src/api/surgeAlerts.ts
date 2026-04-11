import { env } from '../config/env';
import type {
  SurgeAlertEvent,
  SurgeAlertEventSummary,
  SurgeEvaluationRunDetail,
  SurgeEvaluationRunSummary,
} from '../types/surgeAlerts';
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

export async function fetchSurgeEvaluations(): Promise<SurgeEvaluationRunSummary[]> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/surge-alerts/evaluations`);
  if (!response.ok) {
    throw await parseApiError(response, `Surge evaluation request failed with status ${response.status}`);
  }
  const body = (await response.json()) as { items: SurgeEvaluationRunSummary[] };
  return body.items;
}

export async function fetchSurgeEvaluation(surgeEvaluationRunId: string): Promise<SurgeEvaluationRunDetail> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/surge-alerts/evaluations/${surgeEvaluationRunId}`);
  if (!response.ok) {
    throw await parseApiError(response, `Surge evaluation detail request failed with status ${response.status}`);
  }
  return response.json() as Promise<SurgeEvaluationRunDetail>;
}

export async function fetchSurgeEvents(): Promise<SurgeAlertEventSummary[]> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/surge-alerts/events`);
  if (!response.ok) {
    throw await parseApiError(response, `Surge alert event request failed with status ${response.status}`);
  }
  const body = (await response.json()) as { items: SurgeAlertEventSummary[] };
  return body.items;
}

export async function fetchSurgeEvent(surgeNotificationEventId: string): Promise<SurgeAlertEvent> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/surge-alerts/events/${surgeNotificationEventId}`);
  if (!response.ok) {
    throw await parseApiError(response, `Surge alert detail request failed with status ${response.status}`);
  }
  return response.json() as Promise<SurgeAlertEvent>;
}
