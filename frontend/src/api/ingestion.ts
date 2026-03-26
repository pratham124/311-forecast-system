import { env } from '../config/env';
import { getAccessToken } from '../lib/authSession';
import { refreshStoredSession } from './auth';
import type { CurrentDataset, IngestionRunAccepted, IngestionRunStatus } from '../types/ingestion';

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function contentTypeFromHeaders(headers?: HeadersInit): string | undefined {
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

function toAccepted(payload: { run_id: string; status: string }): IngestionRunAccepted {
  return {
    runId: payload.run_id,
    status: payload.status,
  };
}

function toRunStatus(payload: {
  run_id: string;
  status: string;
  result_type?: string | null;
  started_at: string;
  completed_at?: string | null;
  cursor_used?: string | null;
  cursor_advanced: boolean;
  candidate_dataset_id?: string | null;
  dataset_version_id?: string | null;
  records_received?: number | null;
  failure_reason?: string | null;
}): IngestionRunStatus {
  return {
    runId: payload.run_id,
    status: payload.status,
    resultType: payload.result_type ?? null,
    startedAt: payload.started_at,
    completedAt: payload.completed_at ?? null,
    cursorUsed: payload.cursor_used ?? null,
    cursorAdvanced: payload.cursor_advanced,
    candidateDatasetId: payload.candidate_dataset_id ?? null,
    datasetVersionId: payload.dataset_version_id ?? null,
    recordsReceived: payload.records_received ?? null,
    failureReason: payload.failure_reason ?? null,
  };
}

function toCurrentDataset(payload: {
  source_name: string;
  dataset_version_id: string;
  updated_at: string;
  updated_by_run_id: string;
  record_count: number;
  latest_requested_at?: string | null;
}): CurrentDataset {
  return {
    sourceName: payload.source_name,
    datasetVersionId: payload.dataset_version_id,
    updatedAt: payload.updated_at,
    updatedByRunId: payload.updated_by_run_id,
    recordCount: payload.record_count,
    latestRequestedAt: payload.latest_requested_at ?? null,
  };
}

export async function fetchCurrentDataset(signal?: AbortSignal): Promise<CurrentDataset | null> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/datasets/current`, { signal });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw await parseApiError(response, `Current dataset request failed with status ${response.status}`);
  }
  return toCurrentDataset((await response.json()) as {
    source_name: string;
    dataset_version_id: string;
    updated_at: string;
    updated_by_run_id: string;
    record_count: number;
    latest_requested_at?: string | null;
  });
}

export async function triggerIngestionRun(): Promise<IngestionRunAccepted> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/ingestion-runs/311/trigger`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw await parseApiError(response, `Ingestion trigger failed with status ${response.status}`);
  }
  return toAccepted((await response.json()) as { run_id: string; status: string });
}

export async function fetchIngestionRunStatus(runId: string, signal?: AbortSignal): Promise<IngestionRunStatus> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/ingestion-runs/${runId}`, { signal });
  if (!response.ok) {
    throw await parseApiError(response, `Ingestion status request failed with status ${response.status}`);
  }
  return toRunStatus(
    (await response.json()) as {
      run_id: string;
      status: string;
      result_type?: string | null;
      started_at: string;
      completed_at?: string | null;
      cursor_used?: string | null;
      cursor_advanced: boolean;
      candidate_dataset_id?: string | null;
      dataset_version_id?: string | null;
      records_received?: number | null;
      failure_reason?: string | null;
    },
  );
}
