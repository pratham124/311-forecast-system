import { env } from '../config/env';
import { getAccessToken } from '../lib/authSession';
import { refreshStoredSession } from './auth';
import type {
  HistoricalDemandContext,
  HistoricalDemandFilters,
  HistoricalDemandRenderEvent,
  HistoricalDemandResponse,
} from '../types/historicalDemand';

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
  let response = await fetch(input, { ...init, headers: buildHeaders(init.body ? 'application/json' : undefined) });
  if (response.status !== 401) {
    return response;
  }
  await refreshStoredSession();
  response = await fetch(input, { ...init, headers: buildHeaders(init.body ? 'application/json' : undefined) });
  return response;
}

export async function fetchHistoricalDemandContext(signal?: AbortSignal): Promise<HistoricalDemandContext> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/historical-demand/context`, { signal });
  if (!response.ok) {
    throw new Error(`Historical demand context request failed with status ${response.status}`);
  }
  return response.json() as Promise<HistoricalDemandContext>;
}

export async function submitHistoricalDemandQuery(
  payload: HistoricalDemandFilters & { proceedAfterWarning?: boolean },
  signal?: AbortSignal,
): Promise<HistoricalDemandResponse> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/historical-demand/queries`, {
    method: 'POST',
    body: JSON.stringify(payload),
    signal,
  });
  if (!response.ok) {
    throw new Error(`Historical demand request failed with status ${response.status}`);
  }
  return response.json() as Promise<HistoricalDemandResponse>;
}

export async function submitHistoricalDemandRenderEvent(
  analysisRequestId: string,
  payload: HistoricalDemandRenderEvent,
): Promise<void> {
  const response = await fetchWithAuthRetry(
    `${env.apiBaseUrl}/api/v1/historical-demand/queries/${analysisRequestId}/render-events`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
  );
  if (!response.ok) {
    throw new Error(`Historical demand render event failed with status ${response.status}`);
  }
}
