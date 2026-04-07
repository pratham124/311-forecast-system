import { getWeatherOverlayStatusMessage } from '../state/statusMessages';
import type { WeatherOverlayResponse } from '../../../types/weatherOverlay';

interface WeatherOverlayStatusProps {
  overlay: WeatherOverlayResponse | null;
}

export function WeatherOverlayStatus({ overlay }: WeatherOverlayStatusProps) {
  if (!overlay) {
    return null;
  }
  if (overlay.overlayStatus === 'visible' || overlay.overlayStatus === 'loading') {
    return null;
  }

  return (
    <div className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900" role="status">
      {getWeatherOverlayStatusMessage(overlay.overlayStatus, overlay.statusMessage)}
    </div>
  );
}
