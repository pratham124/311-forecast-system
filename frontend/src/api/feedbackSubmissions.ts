import { env } from '../config/env';
import { getAccessToken } from '../lib/authSession';
import { refreshStoredSession } from './auth';
import type {
  FeedbackSubmissionCreateRequest,
  FeedbackSubmissionCreateResponse,
  FeedbackSubmissionDetail,
  FeedbackSubmissionFieldErrors,
  FeedbackSubmissionListResponse,
  ProcessingStatus,
  ReportType,
} from '../types/feedbackSubmissions';

type ValidationDetail = {
  loc?: Array<string | number>;
  msg?: string;
  type?: string;
};

type ErrorBody = {
  detail?: string | ValidationDetail[];
};

export class FeedbackApiError extends Error {
  status: number;
  fieldErrors: FeedbackSubmissionFieldErrors;

  constructor(status: number, message: string, fieldErrors: FeedbackSubmissionFieldErrors = {}) {
    super(message);
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

function buildHeaders(contentType?: string, accessToken?: string | null): Headers {
  const headers = new Headers();
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }
  if (contentType) {
    headers.set('Content-Type', contentType);
  }
  return headers;
}

async function fetchWithOptionalAuthRetry(input: string, init: RequestInit = {}): Promise<Response> {
  const token = getAccessToken();
  const response = await fetch(input, {
    ...init,
    headers: buildHeaders('application/json', token),
  });
  if (response.status !== 401 || !token) {
    return response;
  }
  const refreshed = await refreshStoredSession();
  return fetch(input, {
    ...init,
    headers: buildHeaders('application/json', refreshed.accessToken),
  });
}

async function fetchWithAuthRetry(input: string, init: RequestInit = {}): Promise<Response> {
  const token = getAccessToken();
  const response = await fetch(input, {
    ...init,
    headers: buildHeaders('application/json', token),
  });
  if (response.status !== 401) {
    return response;
  }
  const refreshed = await refreshStoredSession();
  return fetch(input, {
    ...init,
    headers: buildHeaders('application/json', refreshed.accessToken),
  });
}

function normalizeFieldMessage(field: 'reportType' | 'description' | 'contactEmail', detail: ValidationDetail): string {
  if (field === 'reportType' && detail.type === 'missing') {
    return 'Choose whether you are sending feedback or a bug report.';
  }
  if (field === 'reportType') {
    return 'Choose Feedback or Bug Report.';
  }
  if (field === 'description') {
    return 'Describe the feedback or issue before submitting.';
  }
  return detail.msg ?? 'Enter a valid contact email or leave it blank.';
}

function normalizeFieldErrors(details: ValidationDetail[]): FeedbackSubmissionFieldErrors {
  const fieldErrors: FeedbackSubmissionFieldErrors = {};
  for (const detail of details) {
    const field = detail.loc?.[detail.loc.length - 1];
    if (typeof field !== 'string') {
      continue;
    }
    if (field === 'reportType' || field === 'description' || field === 'contactEmail') {
      fieldErrors[field] = normalizeFieldMessage(field, detail);
    }
  }
  return fieldErrors;
}

async function parseApiError(response: Response, fallback: string): Promise<FeedbackApiError> {
  try {
    const body = (await response.json()) as ErrorBody;
    if (typeof body.detail === 'string') {
      return new FeedbackApiError(response.status, body.detail);
    }
    if (Array.isArray(body.detail) && body.detail.length > 0) {
      const fieldErrors = normalizeFieldErrors(body.detail);
      const firstFieldError = Object.values(fieldErrors)[0];
      return new FeedbackApiError(response.status, firstFieldError ?? fallback, fieldErrors);
    }
  } catch {
    // Fall through to fallback.
  }
  return new FeedbackApiError(response.status, fallback);
}

export async function submitFeedbackSubmission(
  payload: FeedbackSubmissionCreateRequest,
): Promise<FeedbackSubmissionCreateResponse> {
  const response = await fetchWithOptionalAuthRetry(`${env.apiBaseUrl}/api/v1/feedback-submissions`, {
    method: 'POST',
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw await parseApiError(response, `Feedback submission failed with status ${response.status}`);
  }
  return response.json() as Promise<FeedbackSubmissionCreateResponse>;
}

export async function listFeedbackSubmissions(
  filters: {
    reportType?: ReportType | 'all';
    processingStatus?: ProcessingStatus | 'all';
  } = {},
  signal?: AbortSignal,
): Promise<FeedbackSubmissionListResponse> {
  const search = new URLSearchParams();
  if (filters.reportType && filters.reportType !== 'all') {
    search.set('reportType', filters.reportType);
  }
  if (filters.processingStatus && filters.processingStatus !== 'all') {
    search.set('processingStatus', filters.processingStatus);
  }
  const suffix = search.toString() ? `?${search.toString()}` : '';
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/feedback-submissions${suffix}`, {
    method: 'GET',
    signal,
  });
  if (!response.ok) {
    throw await parseApiError(response, `Feedback queue request failed with status ${response.status}`);
  }
  return response.json() as Promise<FeedbackSubmissionListResponse>;
}

export async function getFeedbackSubmission(
  feedbackSubmissionId: string,
  signal?: AbortSignal,
): Promise<FeedbackSubmissionDetail> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/feedback-submissions/${feedbackSubmissionId}`, {
    method: 'GET',
    signal,
  });
  if (!response.ok) {
    throw await parseApiError(response, `Feedback detail request failed with status ${response.status}`);
  }
  return response.json() as Promise<FeedbackSubmissionDetail>;
}
