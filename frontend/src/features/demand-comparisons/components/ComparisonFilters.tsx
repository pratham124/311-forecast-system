import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import type {
  DatePreset,
  DemandComparisonAvailability,
  DemandComparisonFilters,
} from '../../../types/demandComparisons';

interface ComparisonFiltersProps {
  availability: DemandComparisonAvailability | null;
  filters: DemandComparisonFilters;
  availableGeographyLevels: string[];
  availableGeographyValues: string[];
  dateWindowStart?: string;
  dateWindowEnd?: string;
  datePresets?: DatePreset[];
  dateRangeError?: string | null;
  onChange: (next: DemandComparisonFilters) => void;
  onApplyDatePreset?: (preset: DatePreset) => void;
  onSubmit: () => void;
  onAutoSelect?: () => void;
  isAutoSelecting?: boolean;
  autoSelectProgress?: { current: number; total: number };
  disabled?: boolean;
}

function toDateTimeLocalValue(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '';
  }
  return date.toISOString().slice(0, 16);
}

function isSameInstant(left: string, right: string): boolean {
  const leftDate = new Date(left);
  const rightDate = new Date(right);
  if (Number.isNaN(leftDate.getTime()) || Number.isNaN(rightDate.getTime())) {
    return false;
  }
  return leftDate.getTime() === rightDate.getTime();
}

export function ComparisonFilters({
  availability,
  filters,
  availableGeographyLevels,
  availableGeographyValues,
  dateWindowStart,
  dateWindowEnd,
  datePresets = [],
  dateRangeError = null,
  onChange,
  onApplyDatePreset,
  onSubmit,
  onAutoSelect,
  isAutoSelecting = false,
  autoSelectProgress = { current: 0, total: 0 },
  disabled = false,
}: ComparisonFiltersProps) {
  const serviceCategories = availability?.serviceCategories ?? [];
  const isDateRangeInvalid = Boolean(dateRangeError);
  const hasCategorySelection = filters.serviceCategories.length > 0;
  const showGeographyLevel = hasCategorySelection;
  const showGeographyValues = Boolean(filters.geographyLevel);
  const startMin = dateWindowStart ? toDateTimeLocalValue(dateWindowStart) : undefined;
  const endMax = dateWindowEnd ? toDateTimeLocalValue(dateWindowEnd) : undefined;
  const selectedPreset = datePresets.find(
    (preset) =>
      isSameInstant(filters.timeRangeStart, preset.timeRangeStart)
      && isSameInstant(filters.timeRangeEnd, preset.timeRangeEnd),
  );

  return (
    <div className="grid gap-5">
      <div className="grid gap-2">
        <Label htmlFor="comparison-categories">Service categories</Label>
        <select
          id="comparison-categories"
          multiple
          className="min-h-40 rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm text-ink"
          value={filters.serviceCategories}
          disabled={disabled}
          onChange={(event) => {
            const selected = Array.from(event.target.selectedOptions, (opt) => opt.value);
            onChange({ ...filters, serviceCategories: selected });
          }}
        >
          {serviceCategories.map((category) => (
            <option key={category} value={category}>{category}</option>
          ))}
        </select>
        <p className="text-xs text-muted">Hold Ctrl / Cmd to select multiple.</p>
      </div>

      {showGeographyLevel ? (
        <div className="grid gap-2">
          <Label htmlFor="comparison-geo-level">Geography level</Label>
          <select
            id="comparison-geo-level"
            className="min-h-11 rounded-2xl border border-slate-300 bg-white px-3 text-sm text-ink"
            value={filters.geographyLevel ?? ''}
            disabled={disabled || availableGeographyLevels.length === 0}
            onChange={(event) => onChange({ ...filters, geographyLevel: event.target.value || undefined, geographyValues: [] })}
          >
            <option value="">None</option>
            {availableGeographyLevels.map((level) => (
              <option key={level} value={level}>{level}</option>
            ))}
          </select>
        </div>
      ) : null}

      {showGeographyValues ? (
        <div className="grid gap-2">
          <Label htmlFor="comparison-geo-values">Geography values</Label>
          <select
            id="comparison-geo-values"
            multiple
            className="min-h-40 rounded-2xl border border-slate-300 bg-white px-3 py-2 text-sm text-ink"
            value={filters.geographyValues}
            disabled={disabled || availableGeographyValues.length === 0}
            onChange={(event) => {
              const selected = Array.from(event.target.selectedOptions, (opt) => opt.value);
              onChange({ ...filters, geographyValues: selected });
            }}
          >
            {availableGeographyValues.map((value) => (
              <option key={value} value={value}>{value}</option>
            ))}
          </select>
          <p className="text-xs text-muted">Hold Ctrl / Cmd to select multiple.</p>
        </div>
      ) : null}

      <div className="grid gap-4 md:grid-cols-2">
        <div className="grid gap-2">
          <Label htmlFor="comparison-start">Start</Label>
          <Input
            id="comparison-start"
            type="datetime-local"
            value={toDateTimeLocalValue(filters.timeRangeStart)}
            min={startMin}
            max={endMax}
            disabled={disabled}
            onChange={(event) => onChange({ ...filters, timeRangeStart: new Date(event.target.value).toISOString() })}
          />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="comparison-end">End</Label>
          <Input
            id="comparison-end"
            type="datetime-local"
            value={toDateTimeLocalValue(filters.timeRangeEnd)}
            min={startMin}
            max={endMax}
            disabled={disabled}
            onChange={(event) => onChange({ ...filters, timeRangeEnd: new Date(event.target.value).toISOString() })}
          />
        </div>
      </div>

      {datePresets.length > 0 && onApplyDatePreset ? (
        <div className="grid gap-2">
          <Label>Quick presets</Label>
          <div className="flex flex-wrap gap-2">
            {datePresets.map((preset) => (
              (() => {
                const isSelected = selectedPreset?.label === preset.label
                  && selectedPreset.timeRangeStart === preset.timeRangeStart
                  && selectedPreset.timeRangeEnd === preset.timeRangeEnd;
                return (
                  <button
                    key={`${preset.label}:${preset.timeRangeStart}:${preset.timeRangeEnd}`}
                    type="button"
                    aria-pressed={isSelected}
                    className={`rounded-full border px-3 py-1 text-xs font-medium transition ${isSelected
                      ? 'border-accent bg-accent/10 text-accent'
                      : 'border-slate-300 bg-white text-ink hover:bg-slate-50'}`}
                    disabled={disabled}
                    onClick={() => onApplyDatePreset(preset)}
                  >
                    {preset.label}
                  </button>
                );
              })()
            ))}
          </div>
          {selectedPreset ? (
            <p className="text-xs text-muted">Applied preset: {selectedPreset.label}</p>
          ) : null}
        </div>
      ) : null}

      {isDateRangeInvalid ? (
        <p className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {dateRangeError}
        </p>
      ) : null}

      {onAutoSelect ? (
        <div className="grid gap-2">
          <button
            type="button"
            disabled={disabled || isAutoSelecting || !availability || availability.serviceCategories.length === 0}
            onClick={onAutoSelect}
            className="inline-flex min-h-11 items-center justify-center rounded-2xl border border-slate-300 bg-white px-4 text-sm font-semibold text-ink transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isAutoSelecting
              ? `Applying best available combination... (${Math.max(1, autoSelectProgress.current)}/${Math.max(1, autoSelectProgress.total)})`
              : 'Auto-select forecast-backed combination'}
          </button>
          <p className="text-xs text-muted">Uses backend-verified category, geography, and preset defaults.</p>
        </div>
      ) : null}

      <button
        type="button"
        disabled={disabled || isAutoSelecting || filters.serviceCategories.length === 0 || isDateRangeInvalid}
        onClick={onSubmit}
        className="inline-flex min-h-11 items-center justify-center rounded-2xl bg-accent px-4 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
      >
        Compare demand
      </button>
    </div>
  );
}
