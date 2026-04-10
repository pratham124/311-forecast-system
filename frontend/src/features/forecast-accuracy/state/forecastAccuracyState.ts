import type { ForecastAccuracyResponse } from '../../../types/forecastAccuracy';

export function hasRenderableForecastAccuracy(response: ForecastAccuracyResponse | null): boolean {
  if (!response) {
    return false;
  }
  return response.viewStatus === 'rendered_with_metrics' || response.viewStatus === 'rendered_without_metrics';
}
