import { env } from '../config/env';
import type { PublicForecastDisplayEventRequest, PublicForecastView } from '../types/publicForecast';

export type PublicForecastProduct = 'daily' | 'weekly';

export async function fetchCurrentPublicForecast(
  forecastProduct: PublicForecastProduct,
  signal?: AbortSignal,
): Promise<PublicForecastView> {
  const response = await fetch(`${env.apiBaseUrl}/api/v1/public/forecast-categories/current?forecastProduct=${forecastProduct}`, { signal });
  if (!response.ok) {
    throw new Error(`Public forecast request failed with status ${response.status}`);
  }
  return response.json() as Promise<PublicForecastView>;
}

export async function submitPublicForecastDisplayEvent(
  publicForecastRequestId: string,
  payload: PublicForecastDisplayEventRequest,
): Promise<void> {
  if (env.renderEventSubmission === 'disabled') {
    return;
  }
  const response = await fetch(
    `${env.apiBaseUrl}/api/v1/public/forecast-categories/${publicForecastRequestId}/display-events`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
  );
  if (!response.ok) {
    throw new Error(`Public forecast render event submission failed with status ${response.status}`);
  }
}
