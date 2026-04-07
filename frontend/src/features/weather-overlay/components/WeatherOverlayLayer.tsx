import type { WeatherOverlayResponse } from '../../../types/weatherOverlay';

interface WeatherOverlayLayerProps {
  overlay: WeatherOverlayResponse;
}

export function WeatherOverlayLayer({ overlay }: WeatherOverlayLayerProps) {
  if (overlay.overlayStatus !== 'visible') {
    return null;
  }

  const unit = overlay.measurementUnit ?? '';
  const latest = overlay.observations[overlay.observations.length - 1];

  return (
    <section className="mt-4 rounded-2xl border border-sky-200 bg-sky-50/60 p-4" aria-label="weather overlay layer">
      <p className="text-xs font-semibold uppercase tracking-[0.12em] text-sky-900">Weather context ({overlay.weatherMeasure})</p>
      <p className="mt-1 text-sm text-sky-900">
        {overlay.observations.length} aligned points
        {latest ? `, latest ${latest.value.toFixed(1)} ${unit}` : ''}
      </p>
      <ul className="mt-3 max-h-44 overflow-auto rounded-lg border border-sky-100 bg-white px-3 py-2 text-xs text-slate-700">
        {overlay.observations.map((point) => (
          <li key={point.timestamp} className="flex items-center justify-between gap-3 py-1">
            <span>{new Date(point.timestamp).toLocaleString()}</span>
            <strong>{point.value.toFixed(1)} {unit}</strong>
          </li>
        ))}
      </ul>
    </section>
  );
}
