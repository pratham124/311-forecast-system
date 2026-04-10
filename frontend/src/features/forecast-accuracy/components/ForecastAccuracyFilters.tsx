import { useEffect, useRef, useState } from 'react';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import type { ForecastAccuracyFilters } from '../../../types/forecastAccuracy';

type ForecastAccuracyFiltersProps = {
  filters: ForecastAccuracyFilters;
  serviceCategoryOptions: string[];
  onChange: (next: ForecastAccuracyFilters) => void;
  onSubmit: () => void;
  disabled?: boolean;
};

function toDateInputValue(value?: string): string {
  if (!value) {
    return '';
  }
  return value.slice(0, 10);
}

export function ForecastAccuracyFilters({
  filters,
  serviceCategoryOptions,
  onChange,
  onSubmit,
  disabled = false,
}: ForecastAccuracyFiltersProps) {
  const [isCategoryOpen, setIsCategoryOpen] = useState(false);
  const categoryRef = useRef<HTMLDivElement>(null);
  const serviceCategoryLabel = filters.serviceCategory ?? 'All categories';
  const startValue = toDateInputValue(filters.timeRangeStart);
  const endValue = toDateInputValue(filters.timeRangeEnd);

  useEffect(() => {
    if (!isCategoryOpen) {
      return;
    }

    const handlePointerDown = (event: MouseEvent) => {
      const target = event.target;
      if (!(target instanceof Node)) {
        return;
      }
      if (categoryRef.current?.contains(target)) {
        return;
      }
      setIsCategoryOpen(false);
    };

    document.addEventListener('mousedown', handlePointerDown);
    return () => document.removeEventListener('mousedown', handlePointerDown);
  }, [isCategoryOpen]);

  return (
    <div className="grid gap-3">
      <div className="grid gap-3 md:grid-cols-2">
        <div className="grid gap-2">
          <Label htmlFor="forecast-accuracy-start">Start</Label>
          <Input
            id="forecast-accuracy-start"
            type="date"
            value={startValue}
            max={endValue || undefined}
            onChange={(event) => onChange({ ...filters, timeRangeStart: event.target.value ? `${event.target.value}T00:00:00.000Z` : undefined })}
            disabled={disabled}
          />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="forecast-accuracy-end">End</Label>
          <Input
            id="forecast-accuracy-end"
            type="date"
            value={endValue}
            min={startValue || undefined}
            onChange={(event) => onChange({ ...filters, timeRangeEnd: event.target.value ? `${event.target.value}T23:59:59.000Z` : undefined })}
            disabled={disabled}
          />
        </div>
      </div>
      <div className="grid gap-2">
        <Label htmlFor="forecast-accuracy-service-category">Service category</Label>
        <div ref={categoryRef} className={isCategoryOpen ? 'relative z-[120]' : 'relative z-10'}>
          <button
            id="forecast-accuracy-service-category"
            type="button"
            onClick={() => setIsCategoryOpen((current) => !current)}
            disabled={disabled}
            className="flex min-h-12 w-full items-center justify-between rounded-2xl border border-[rgba(25,58,90,0.14)] bg-white px-4 py-3 text-left text-sm text-ink shadow-sm transition hover:border-accent focus:border-accent focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
            aria-haspopup="listbox"
            aria-expanded={isCategoryOpen}
            aria-label="Service category"
          >
            <span>{serviceCategoryLabel}</span>
            <span className="ml-4 text-muted">{isCategoryOpen ? 'Hide' : 'Choose'}</span>
          </button>
          {isCategoryOpen ? (
            <div className="absolute z-[130] mt-2 w-full rounded-2xl border border-[rgba(25,58,90,0.14)] bg-white p-3 shadow-panel backdrop-blur-xl">
              <div role="listbox" aria-label="Service category" className="max-h-64 space-y-2 overflow-auto">
                <button
                  type="button"
                  onClick={() => {
                    onChange({ ...filters, serviceCategory: undefined });
                    setIsCategoryOpen(false);
                  }}
                  className="flex w-full items-center justify-between rounded-xl px-2 py-2 text-left text-sm text-ink transition hover:bg-[#eef5fa]"
                  aria-pressed={!filters.serviceCategory}
                >
                  <span>All categories</span>
                  {!filters.serviceCategory ? <span className="text-forecast">Selected</span> : null}
                </button>
                {serviceCategoryOptions.map((category) => (
                  <button
                    key={category}
                    type="button"
                    onClick={() => {
                      onChange({ ...filters, serviceCategory: category });
                      setIsCategoryOpen(false);
                    }}
                    className="flex w-full items-center justify-between rounded-xl px-2 py-2 text-left text-sm text-ink transition hover:bg-[#eef5fa]"
                    aria-pressed={filters.serviceCategory === category}
                  >
                    <span>{category}</span>
                    {filters.serviceCategory === category ? <span className="text-forecast">Selected</span> : null}
                  </button>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>
      <button
        type="button"
        disabled={disabled}
        onClick={onSubmit}
        className="inline-flex min-h-11 items-center justify-center rounded-2xl bg-accent px-5 text-sm font-semibold text-white transition hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-60"
      >
        Load accuracy
      </button>
    </div>
  );
}
