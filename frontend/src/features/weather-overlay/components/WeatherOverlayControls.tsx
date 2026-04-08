import type { RefObject } from 'react';
import type { WeatherMeasure } from '../../../types/weatherOverlay';

interface WeatherOverlayControlsProps {
  enabled: boolean;
  selectedMeasure: WeatherMeasure;
  onEnabledChange: (next: boolean) => void;
  onMeasureChange: (measure: WeatherMeasure) => void;
  isOpen?: boolean;
  onOpenChange?: (isOpen: boolean) => void;
  containerRef?: RefObject<HTMLDivElement>;
}

const MEASURES: Array<{ value: WeatherMeasure; label: string }> = [
  { value: 'temperature', label: 'Temperature' },
  { value: 'snowfall', label: 'Snowfall' },
  { value: 'precipitation', label: 'Precipitation' },
];

export function WeatherOverlayControls({
  enabled,
  selectedMeasure,
  onEnabledChange,
  onMeasureChange,
  isOpen = false,
  onOpenChange = () => {},
  containerRef,
}: WeatherOverlayControlsProps) {
  const selectedLabel = MEASURES.find((m) => m.value === selectedMeasure)?.label ?? 'Select measure';

  return (
    <section className="mt-5 rounded-2xl border border-[rgba(25,58,90,0.14)] bg-white p-4" aria-label="weather overlay controls">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-ink">Weather overlay</p>
          <p className="text-xs text-muted">Enable one measure at a time to compare weather context.</p>
        </div>
        <label className="inline-flex items-center gap-2 text-sm text-ink cursor-pointer">
          <input
            type="checkbox"
            className="h-4 w-4 cursor-pointer rounded border-slate-300 bg-white accent-[var(--accent)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--accent)]"
            checked={enabled}
            onChange={(event) => onEnabledChange(event.target.checked)}
            aria-label="Enable weather overlay"
          />
          Enable overlay
        </label>
      </div>
      <div className="mt-4" ref={containerRef}>
        <span className="block text-xs font-semibold uppercase tracking-[0.12em] text-muted mb-2">
          Weather measure
        </span>
        <div className={isOpen ? 'relative z-[120]' : 'relative z-10'}>
          <button
            id="weather-measure"
            type="button"
            onClick={() => {
              if (enabled) onOpenChange(!isOpen);
            }}
            disabled={!enabled}
            className="flex min-h-12 w-full items-center justify-between rounded-2xl border border-[rgba(25,58,90,0.14)] bg-white px-4 py-3 text-left text-sm text-ink shadow-sm transition hover:border-accent focus:border-accent focus:outline-none disabled:cursor-not-allowed disabled:bg-slate-50 disabled:opacity-60"
            aria-haspopup="listbox"
            aria-expanded={isOpen}
          >
            <span>{selectedLabel}</span>
            <span className="ml-4 text-muted">{isOpen ? 'Hide' : 'Choose'}</span>
          </button>
          {isOpen && enabled ? (
            <div className="absolute z-[130] mt-2 w-full rounded-2xl border border-[rgba(25,58,90,0.14)] bg-white p-3 shadow-panel backdrop-blur-xl">
              <div role="listbox" aria-label="Weather measure" className="space-y-2">
                {MEASURES.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => {
                      onMeasureChange(option.value);
                      onOpenChange(false);
                    }}
                    className="flex w-full items-center justify-between rounded-xl px-2 py-2 text-left text-sm text-ink transition hover:bg-[#eef5fa]"
                    aria-pressed={selectedMeasure === option.value}
                  >
                    <span>{option.label}</span>
                    {selectedMeasure === option.value ? <span className="text-forecast">Selected</span> : null}
                  </button>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
