import { env } from '../config/env';
import { getAccessToken } from '../lib/authSession';
import { refreshStoredSession } from './auth';
import type { CurrentEvaluation, EvaluationRunAccepted, EvaluationRunStatus, ForecastProduct } from '../types/evaluation';

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export function contentTypeFromHeaders(headers?: HeadersInit): string | undefined {
  if (!headers) return undefined;
  if (headers instanceof Headers) {
    return headers.get('Content-Type') ?? undefined;
  }
  if (Array.isArray(headers)) {
    const match = headers.find(([key]) => key.toLowerCase() === 'content-type');
    return match?.[1];
  }
  return headers['Content-Type'] ?? headers['content-type'];
}

export function buildHeaders(contentType?: string): Headers {
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

export async function fetchCurrentEvaluation(forecastProduct: ForecastProduct, signal?: AbortSignal): Promise<CurrentEvaluation | null> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/evaluations/current?forecastProduct=${forecastProduct}`, { signal });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw await parseApiError(response, `Evaluation request failed with status ${response.status}`);
  }
  return response.json() as Promise<CurrentEvaluation>;
}

export async function triggerEvaluationRun(forecastProduct: ForecastProduct): Promise<EvaluationRunAccepted> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/evaluation-runs/trigger`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ forecastProduct, triggerType: 'on_demand' }),
  });
  if (!response.ok) {
    throw await parseApiError(response, `Evaluation trigger failed with status ${response.status}`);
  }
  return response.json() as Promise<EvaluationRunAccepted>;
}

export async function fetchEvaluationRunStatus(evaluationRunId: string, signal?: AbortSignal): Promise<EvaluationRunStatus> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/evaluation-runs/${evaluationRunId}`, { signal });
  if (!response.ok) {
    throw await parseApiError(response, `Evaluation status request failed with status ${response.status}`);
  }
  return response.json() as Promise<EvaluationRunStatus>;
}
