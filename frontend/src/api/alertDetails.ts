import { env } from '../config/env';
import type { AlertDetail, AlertDetailRenderEvent, AlertSource } from '../types/alertDetails';
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

export async function fetchAlertDetail(alertSource: AlertSource, alertId: string): Promise<AlertDetail> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/alert-details/${alertSource}/${alertId}`);
  if (!response.ok) {
    throw await parseApiError(response, `Alert detail request failed with status ${response.status}`);
  }
  return response.json() as Promise<AlertDetail>;
}

export async function submitAlertDetailRenderEvent(
  alertDetailLoadId: string,
  payload: AlertDetailRenderEvent,
): Promise<void> {
  if (env.renderEventSubmission === 'disabled') {
    return;
  }
  const response = await fetchWithAuthRetry(
    `${env.apiBaseUrl}/api/v1/alert-details/${alertDetailLoadId}/render-events`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
  );
  if (!response.ok) {
    throw await parseApiError(response, `Alert detail render event failed with status ${response.status}`);
  }
}
