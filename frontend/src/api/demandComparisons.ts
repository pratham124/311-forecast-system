import { env } from '../config/env';
import { getAccessToken } from '../lib/authSession';
import { refreshStoredSession } from './auth';
import type {
  DemandComparisonAvailability,
  DemandComparisonContext,
  DemandComparisonFilters,
  DemandComparisonRenderEvent,
  DemandComparisonRenderEventResponse,
  DemandComparisonResponse,
} from '../types/demandComparisons';

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

export async function fetchDemandComparisonAvailability(signal?: AbortSignal): Promise<DemandComparisonAvailability> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/demand-comparisons/availability`, { signal });
  if (!response.ok) {
    throw new Error(`Demand comparison availability request failed with status ${response.status}`);
  }
  return response.json() as Promise<DemandComparisonAvailability>;
}

export async function fetchDemandComparisonContext(signal?: AbortSignal): Promise<DemandComparisonContext> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/demand-comparisons/context`, { signal });
  if (!response.ok) {
    throw new Error(`Demand comparison context request failed with status ${response.status}`);
  }
  return response.json() as Promise<DemandComparisonContext>;
}

export async function submitDemandComparisonQuery(
  payload: DemandComparisonFilters & { proceedAfterWarning?: boolean },
  signal?: AbortSignal,
): Promise<DemandComparisonResponse> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/demand-comparisons/queries`, {
    method: 'POST',
    body: JSON.stringify(payload),
    signal,
  });
  if (!response.ok) {
    throw new Error(`Demand comparison request failed with status ${response.status}`);
  }
  return response.json() as Promise<DemandComparisonResponse>;
}

export async function submitDemandComparisonRenderEvent(
  comparisonRequestId: string,
  payload: DemandComparisonRenderEvent,
): Promise<DemandComparisonRenderEventResponse> {
  const response = await fetchWithAuthRetry(
    `${env.apiBaseUrl}/api/v1/demand-comparisons/${comparisonRequestId}/render-events`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
    },
  );
  if (!response.ok) {
    throw new Error(`Demand comparison render event failed with status ${response.status}`);
  }
  return response.json() as Promise<DemandComparisonRenderEventResponse>;
}
