import { env } from '../config/env';
import { getAccessToken } from '../lib/authSession';
import { refreshStoredSession } from './auth';
import type { WeatherMeasure, WeatherOverlayRenderEvent, WeatherOverlayResponse, WeatherOverlayStatus } from '../types/weatherOverlay';

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
  const headers = init.headers instanceof Headers ? init.headers : new Headers(init.headers);
  const contentType = headers.get('Content-Type') ?? undefined;

  let response = await fetch(input, { ...init, headers: buildHeaders(contentType) });
  if (response.status !== 401) {
    return response;
  }
  await refreshStoredSession();
  response = await fetch(input, { ...init, headers: buildHeaders(contentType) });
  return response;
}

export async function fetchWeatherOverlay(params: {
  geographyId: string;
  timeRangeStart: string;
  timeRangeEnd: string;
  weatherMeasure?: WeatherMeasure;
  signal?: AbortSignal;
}): Promise<WeatherOverlayResponse> {
  const search = new URLSearchParams();
  search.set('geographyId', params.geographyId);
  search.set('timeRangeStart', params.timeRangeStart);
  search.set('timeRangeEnd', params.timeRangeEnd);
  if (params.weatherMeasure) {
    search.set('weatherMeasure', params.weatherMeasure);
  }

  const response = await fetchWithAuthRetry(`${env.apiBaseUrl}/api/v1/forecast-explorer/weather-overlay?${search.toString()}`, { signal: params.signal });
  if (!response.ok) {
    throw new Error(`Weather overlay request failed with status ${response.status}`);
  }
  return response.json() as Promise<WeatherOverlayResponse>;
}

export async function submitWeatherOverlayRenderEvent(input: {
  overlayRequestId: string;
  overlayStatus: WeatherOverlayStatus;
  isLatestSelection: boolean;
  payload: WeatherOverlayRenderEvent;
}): Promise<void> {
  if (!input.isLatestSelection) return;
  if (input.overlayStatus === 'disabled' || input.overlayStatus === 'superseded') return;
  const response = await fetchWithAuthRetry(
    `${env.apiBaseUrl}/api/v1/forecast-explorer/weather-overlay/${input.overlayRequestId}/render-events`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(input.payload),
    },
  );
  if (!response.ok) {
    throw new Error(`Weather overlay render event failed with status ${response.status}`);
  }
}
