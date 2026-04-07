import type { WeatherOverlayStatus } from '../../../types/weatherOverlay';

const DEFAULT_STATUS_MESSAGE = 'Weather overlay is currently unavailable.';

export const WEATHER_OVERLAY_STATUS_MESSAGES: Partial<Record<WeatherOverlayStatus, string>> = {
  disabled: 'Weather overlay is off.',
  unavailable: 'No weather records were available for this selection.',
  'retrieval-failed': 'Weather provider retrieval failed. Try again in a moment.',
  misaligned: 'This geography is not supported for weather overlay.',
  superseded: 'A newer weather-overlay request replaced this one.',
  'failed-to-render': 'Weather overlay failed to render, but the base forecast is still available.',
};

export function getWeatherOverlayStatusMessage(status: WeatherOverlayStatus, serverMessage?: string): string {
  return serverMessage ?? WEATHER_OVERLAY_STATUS_MESSAGES[status] ?? DEFAULT_STATUS_MESSAGE;
}
