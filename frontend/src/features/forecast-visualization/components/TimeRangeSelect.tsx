import { useMemo, type RefObject } from 'react';
import type { ForecastProduct } from '../../../types/forecastVisualization';

interface TimeRangeSelectProps {
  value: ForecastProduct;
  onChange: (value: ForecastProduct) => void;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  containerRef: RefObject<HTMLDivElement>;
}

const OPTIONS: Array<{ value: ForecastProduct; label: string }> = [
  { value: 'daily_1_day', label: 'Next 24 hours' },
  { value: 'weekly_7_day', label: 'Next 7 days' },
];

export function TimeRangeSelect({ value, onChange, isOpen, onOpenChange, containerRef }: TimeRangeSelectProps) {
  const selectedLabel = useMemo(() => OPTIONS.find((option) => option.value === value)?.label ?? 'Select time range', [value]);

  return (
    <div ref={containerRef} className={isOpen ? 'relative z-[120]' : 'relative z-10'}>
      <button
        id="forecast-product"
        type="button"
        onClick={() => onOpenChange(!isOpen)}
        className="flex min-h-12 w-full items-center justify-between rounded-2xl border border-[rgba(25,58,90,0.14)] bg-white px-4 py-3 text-left text-sm text-ink shadow-sm transition hover:border-accent focus:border-accent focus:outline-none"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <span>{selectedLabel}</span>
        <span className="ml-4 text-muted">{isOpen ? 'Hide' : 'Choose'}</span>
      </button>
      {isOpen ? (
        <div className="absolute z-[130] mt-2 w-full rounded-2xl border border-[rgba(25,58,90,0.14)] bg-white p-3 shadow-panel backdrop-blur-xl">
          <div role="listbox" aria-label="Time range" className="space-y-2">
            {OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => {
                  onChange(option.value);
                  onOpenChange(false);
                }}
                className="flex w-full items-center justify-between rounded-xl px-2 py-2 text-left text-sm text-ink transition hover:bg-[#eef5fa]"
                aria-pressed={value === option.value}
              >
                <span>{option.label}</span>
                {value === option.value ? <span className="text-forecast">Selected</span> : null}
              </button>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
