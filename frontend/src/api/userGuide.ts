import { env } from '../config/env';
import { getAccessToken } from '../lib/authSession';
import { refreshStoredSession } from './auth';
import type { GuideRenderOutcomeRequest, UserGuideView } from '../types/userGuide';

function buildHeaders(contentType?: string): Headers {
  const headers = new Headers();
  const token = getAccessToken();
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  if (contentType) {
    headers.set('Content-Type', contentType);
  }
  return headers;
}

async function fetchWithAuthRetry(input: string, init: RequestInit = {}): Promise<Response> {
  const contentType = new Headers(init.headers).get('Content-Type') ?? undefined;

  let response = await fetch(input, { ...init, headers: buildHeaders(contentType) });
  if (response.status !== 401) {
    return response;
  }
  await refreshStoredSession();
  response = await fetch(input, { ...init, headers: buildHeaders(contentType) });
  return response;
}

export async function fetchUserGuide(entryPoint: string, signal?: AbortSignal): Promise<UserGuideView> {
  const search = new URLSearchParams();
  search.set('entryPoint', entryPoint);
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/help/user-guide?${search.toString()}`, { signal });
  if (!response.ok) {
    throw new Error(`User guide request failed with status ${response.status}`);
  }
  return response.json() as Promise<UserGuideView>;
}

export async function submitUserGuideRenderEvent(
  guideAccessEventId: string,
  payload: GuideRenderOutcomeRequest,
): Promise<void> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/help/user-guide/${guideAccessEventId}/render-events`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error(`User guide render event failed with status ${response.status}`);
  }
}
