import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import type { DemandComparisonContext, DemandComparisonFilters } from '../../../types/demandComparisons';

interface ComparisonFiltersProps {
  context: DemandComparisonContext | null;
  filters: DemandComparisonFilters;
  onChange: (next: DemandComparisonFilters) => void;
  onSubmit: () => void;
  disabled?: boolean;
}

function checkboxClass(isChecked: boolean): string {
  return `rounded-2xl border px-3 py-2 text-sm ${isChecked ? 'border-accent bg-accent text-white' : 'border-slate-300 bg-white text-ink'}`;
}

export function ComparisonFilters({ context, filters, onChange, onSubmit, disabled = false }: ComparisonFiltersProps) {
  const geographyOptions = context?.geographyOptions[filters.geographyLevel ?? ''] ?? [];

  return (
    <div className="grid gap-5">
      <div className="grid gap-2">
        <Label>Service categories</Label>
        <div className="flex flex-wrap gap-2">
          {context?.serviceCategories.map((category) => {
            const checked = filters.serviceCategories.includes(category);
            return (
              <button
                key={category}
                type="button"
                disabled={disabled}
                className={checkboxClass(checked)}
                onClick={() => {
                  const nextCategories = checked
                    ? filters.serviceCategories.filter((item) => item !== category)
                    : [...filters.serviceCategories, category];
                  onChange({ ...filters, serviceCategories: nextCategories });
                }}
              >
                {category}
              </button>
            );
          })}
        </div>
      </div>

      <div className="grid gap-2">
        <Label htmlFor="comparison-geo-level">Geography level</Label>
        <select
          id="comparison-geo-level"
          className="min-h-11 rounded-2xl border border-slate-300 bg-white px-3 text-sm text-ink"
          value={filters.geographyLevel ?? ''}
          disabled={disabled}
          onChange={(event) => onChange({ ...filters, geographyLevel: event.target.value || undefined, geographyValues: [] })}
        >
          <option value="">None</option>
          {context?.geographyLevels.map((level) => (
            <option key={level} value={level}>{level}</option>
          ))}
        </select>
      </div>

      {filters.geographyLevel ? (
        <div className="grid gap-2">
          <Label>Geography values</Label>
          <div className="flex flex-wrap gap-2">
            {geographyOptions.map((value) => {
              const checked = filters.geographyValues.includes(value);
              return (
                <button
                  key={value}
                  type="button"
                  disabled={disabled}
                  className={checkboxClass(checked)}
                  onClick={() => {
                    const nextValues = checked
                      ? filters.geographyValues.filter((item) => item !== value)
                      : [...filters.geographyValues, value];
                    onChange({ ...filters, geographyValues: nextValues });
                  }}
                >
                  {value}
                </button>
              );
            })}
          </div>
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2">
        <div className="grid gap-2">
          <Label htmlFor="comparison-start">Start</Label>
          <Input
            id="comparison-start"
            type="datetime-local"
            value={filters.timeRangeStart.slice(0, 16)}
            disabled={disabled}
            onChange={(event) => onChange({ ...filters, timeRangeStart: new Date(event.target.value).toISOString() })}
          />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="comparison-end">End</Label>
          <Input
            id="comparison-end"
            type="datetime-local"
            value={filters.timeRangeEnd.slice(0, 16)}
            disabled={disabled}
            onChange={(event) => onChange({ ...filters, timeRangeEnd: new Date(event.target.value).toISOString() })}
          />
        </div>
      </div>

      <button
        type="button"
        disabled={disabled || filters.serviceCategories.length === 0}
        onClick={onSubmit}
        className="inline-flex min-h-11 items-center justify-center rounded-2xl bg-accent px-4 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
      >
        Compare demand
      </button>
    </div>
  );
}
