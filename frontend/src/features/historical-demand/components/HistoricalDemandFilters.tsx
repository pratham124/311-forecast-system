import { useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import type { HistoricalDemandContext, HistoricalDemandFilters } from '../../../types/historicalDemand';

type HistoricalDemandFiltersProps = {
  context: HistoricalDemandContext | null;
  filters: HistoricalDemandFilters;
  onChange: (nextFilters: HistoricalDemandFilters) => void;
  onSubmit: () => void;
  disabled?: boolean;
};

function toDateInputValue(value?: string): string {
  if (!value) {
    return '';
  }
  return value.slice(0, 10);
}

export function HistoricalDemandFilters({ context, filters, onChange, onSubmit, disabled = false }: HistoricalDemandFiltersProps) {
  const today = new Date().toISOString().slice(0, 10);
  const [isCategoryOpen, setIsCategoryOpen] = useState(false);
  const categoryRef = useRef<HTMLDivElement>(null);

  const updateField = (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = event.target;
    onChange({ ...filters, [name]: value || undefined });
  };

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

  const serviceCategoryLabel = useMemo(() => {
    if (!filters.serviceCategory) {
      return 'All categories';
    }
    return filters.serviceCategory;
  }, [filters.serviceCategory]);

  return (
    <section className="grid gap-4" aria-label="historical demand filters">
      <div className="grid gap-2">
        <Label htmlFor="service-category">Service category</Label>
        <div ref={categoryRef} className={isCategoryOpen ? 'relative z-[120]' : 'relative z-10'}>
          <button
            id="service-category"
            type="button"
            onClick={() => setIsCategoryOpen((current) => !current)}
            disabled={disabled}
            className="flex min-h-12 w-full items-center justify-between rounded-2xl border border-[rgba(25,58,90,0.14)] bg-white px-4 py-3 text-left text-sm text-ink shadow-sm transition hover:border-accent focus:border-accent focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
            aria-haspopup="listbox"
            aria-expanded={isCategoryOpen}
          >
            <span>{serviceCategoryLabel}</span>
            <span className="ml-4 text-muted">{isCategoryOpen ? 'Hide' : 'Choose'}</span>
          </button>
          {isCategoryOpen ? (
            <div className="absolute z-[130] mt-2 w-full rounded-2xl border border-[rgba(25,58,90,0.14)] bg-white p-3 shadow-panel backdrop-blur-xl">
              <div role="listbox" aria-label="Service category" className="space-y-2">
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
                {context?.serviceCategories.map((category) => (
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
      <div className="grid gap-2 md:grid-cols-2">
        <div className="grid gap-2">
          <Label htmlFor="time-range-start">Time range start</Label>
          <Input id="time-range-start" name="timeRangeStart" type="date" max={today} value={toDateInputValue(filters.timeRangeStart)} onChange={updateField} disabled={disabled} />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="time-range-end">Time range end</Label>
          <Input id="time-range-end" name="timeRangeEnd" type="date" max={today} value={toDateInputValue(filters.timeRangeEnd)} onChange={updateField} disabled={disabled} />
        </div>
      </div>
      <button
        type="button"
        onClick={onSubmit}
        disabled={disabled}
        className="inline-flex min-h-11 items-center justify-center rounded-2xl bg-accent px-5 text-sm font-semibold text-white transition hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-60"
      >
        Explore historical demand
      </button>
    </section>
  );
}
