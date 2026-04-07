import type { WeatherMeasure } from '../../../types/weatherOverlay';

interface WeatherOverlayControlsProps {
  enabled: boolean;
  selectedMeasure: WeatherMeasure;
  onEnabledChange: (next: boolean) => void;
  onMeasureChange: (measure: WeatherMeasure) => void;
}

export function WeatherOverlayControls({
  enabled,
  selectedMeasure,
  onEnabledChange,
  onMeasureChange,
}: WeatherOverlayControlsProps) {
  return (
    <section className="mt-5 rounded-2xl border border-slate-200 bg-white p-4" aria-label="weather overlay controls">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-ink">Weather overlay</p>
          <p className="text-xs text-muted">Enable one measure at a time to compare weather context.</p>
        </div>
        <label className="inline-flex items-center gap-2 text-sm text-ink">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(event) => onEnabledChange(event.target.checked)}
            aria-label="Enable weather overlay"
          />
          Enable overlay
        </label>
      </div>
      <div className="mt-3">
        <label htmlFor="weather-measure" className="block text-xs font-semibold uppercase tracking-[0.12em] text-muted">
          Weather measure
        </label>
        <select
          id="weather-measure"
          className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-ink"
          disabled={!enabled}
          value={selectedMeasure}
          onChange={(event) => onMeasureChange(event.target.value as WeatherMeasure)}
        >
          <option value="temperature">Temperature</option>
          <option value="snowfall">Snowfall</option>
          <option value="precipitation">Precipitation</option>
        </select>
      </div>
    </section>
  );
}
