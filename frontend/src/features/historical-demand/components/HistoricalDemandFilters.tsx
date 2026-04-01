import type { ChangeEvent } from 'react';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import { Select } from '../../../components/ui/select';
import type { HistoricalDemandContext, HistoricalDemandFilters } from '../../../types/historicalDemand';

type HistoricalDemandFiltersProps = {
  context: HistoricalDemandContext | null;
  filters: HistoricalDemandFilters;
  onChange: (nextFilters: HistoricalDemandFilters) => void;
  onSubmit: () => void;
  disabled?: boolean;
};

export function HistoricalDemandFilters({ context, filters, onChange, onSubmit, disabled = false }: HistoricalDemandFiltersProps) {
  const updateField = (event: ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = event.target;
    onChange({ ...filters, [name]: value || undefined });
  };

  return (
    <section className="grid gap-4" aria-label="historical demand filters">
      <div className="grid gap-2">
        <Label htmlFor="service-category">Service category</Label>
        <Select id="service-category" name="serviceCategory" value={filters.serviceCategory ?? ''} onChange={updateField} disabled={disabled}>
          <option value="">All categories</option>
          {context?.serviceCategories.map((category) => (
            <option key={category} value={category}>{category}</option>
          ))}
        </Select>
      </div>
      <div className="grid gap-2 md:grid-cols-2">
        <div className="grid gap-2">
          <Label htmlFor="time-range-start">Time range start</Label>
          <Input id="time-range-start" name="timeRangeStart" type="datetime-local" value={filters.timeRangeStart.replace('Z', '')} onChange={updateField} disabled={disabled} />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="time-range-end">Time range end</Label>
          <Input id="time-range-end" name="timeRangeEnd" type="datetime-local" value={filters.timeRangeEnd.replace('Z', '')} onChange={updateField} disabled={disabled} />
        </div>
      </div>
      <div className="grid gap-2 md:grid-cols-[0.9fr_1.1fr]">
        <div className="grid gap-2">
          <Label htmlFor="geography-level">Geography level</Label>
          <Select id="geography-level" name="geographyLevel" value={filters.geographyLevel ?? ''} onChange={updateField} disabled={disabled}>
            <option value="">City-wide</option>
            {context?.supportedGeographyLevels.map((level) => (
              <option key={level} value={level}>{level}</option>
            ))}
          </Select>
        </div>
        <div className="grid gap-2">
          <Label htmlFor="geography-value">Geography value</Label>
          <Input id="geography-value" name="geographyValue" value={filters.geographyValue ?? ''} onChange={updateField} disabled={disabled || !filters.geographyLevel} placeholder="e.g. Ward 1" />
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
