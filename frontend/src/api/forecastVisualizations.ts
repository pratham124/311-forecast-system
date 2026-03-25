import { env } from '../config/env';
import { getAccessToken } from '../lib/authSession';
import { refreshStoredSession } from './auth';
import type { ForecastProduct, ForecastVisualization, ServiceCategoryOptions, VisualizationRenderEvent } from '../types/forecastVisualization';

function buildQuery(forecastProduct: ForecastProduct, serviceCategories?: string[], excludedServiceCategories?: string[]): string {
  const search = new URLSearchParams();
  search.set('forecastProduct', forecastProduct);
  for (const category of serviceCategories ?? []) {
    if (category) {
      search.append('serviceCategory', category);
    }
  }
  for (const category of excludedServiceCategories ?? []) {
    if (category) {
      search.append('excludeServiceCategory', category);
    }
  }
  return search.toString();
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

export async function fetchCurrentForecastVisualization(
  forecastProduct: ForecastProduct,
  serviceCategories?: string[],
  excludedServiceCategories?: string[],
  signal?: AbortSignal,
): Promise<ForecastVisualization> {
  const response = await fetchWithAuthRetry(
    `${env.apiBaseUrl}/api/v1/forecast-visualizations/current?${buildQuery(forecastProduct, serviceCategories, excludedServiceCategories)}`,
    { signal },
  );
  if (!response.ok) {
    throw new Error(`Visualization request failed with status ${response.status}`);
  }
  return response.json() as Promise<ForecastVisualization>;
}

export async function fetchServiceCategoryOptions(
  forecastProduct: ForecastProduct,
  signal?: AbortSignal,
): Promise<ServiceCategoryOptions> {
  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/forecast-visualizations/service-categories?forecastProduct=${forecastProduct}`, { signal });
  if (!response.ok) {
    throw new Error(`Service category request failed with status ${response.status}`);
  }
  return response.json() as Promise<ServiceCategoryOptions>;
}

export async function submitVisualizationRenderEvent(
  visualizationLoadId: string,
  payload: VisualizationRenderEvent,
): Promise<void> {
  if (env.renderEventSubmission === 'disabled') {
    return;
  }
  const response = await fetchWithAuthRetry(
    `${env.apiBaseUrl}/api/v1/forecast-visualizations/${visualizationLoadId}/render-events`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
  );
  if (!response.ok) {
    throw new Error(`Render event submission failed with status ${response.status}`);
  }
}
