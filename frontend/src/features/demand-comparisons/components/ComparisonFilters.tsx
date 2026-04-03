import { useEffect, useMemo, useRef, useState, type ChangeEvent } from 'react';
import { Input } from '../../../components/ui/input';
import { Label } from '../../../components/ui/label';
import type {
  DemandComparisonAvailability,
  DemandComparisonFilters,
} from '../../../types/demandComparisons';

interface ComparisonFiltersProps {
  availability: DemandComparisonAvailability | null;
  filters: DemandComparisonFilters;
  dateWindowStart?: string;
  dateWindowEnd?: string;
  dateRangeError?: string | null;
  onChange: (next: DemandComparisonFilters) => void;
  onSubmit: () => void;
  disabled?: boolean;
}

const EDMONTON_TIMEZONE = 'America/Edmonton';

function toDateInputValue(value: string): string {
  if (!value) {
    return '';
  }
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return value;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '';
  }
  return date.toISOString().slice(0, 10);
}

function getTimeZoneOffsetMilliseconds(timeZone: string, value: Date): number {
  const formatter = new Intl.DateTimeFormat('en-CA', {
    timeZone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hourCycle: 'h23',
  });

  const parts = formatter.formatToParts(value);
  const year = Number(parts.find((part) => part.type === 'year')?.value ?? '0');
  const month = Number(parts.find((part) => part.type === 'month')?.value ?? '1');
  const day = Number(parts.find((part) => part.type === 'day')?.value ?? '1');
  const hour = Number(parts.find((part) => part.type === 'hour')?.value ?? '0');
  const minute = Number(parts.find((part) => part.type === 'minute')?.value ?? '0');
  const second = Number(parts.find((part) => part.type === 'second')?.value ?? '0');

  return Date.UTC(year, month - 1, day, hour, minute, second) - value.getTime();
}

function toEdmontonBoundaryIso(value: string, boundary: 'start' | 'end'): string {
  if (!value) {
    return value;
  }

  const [year, month, day] = value.split('-').map(Number);
  const hour = boundary === 'end' ? 23 : 0;
  const minute = boundary === 'end' ? 59 : 0;
  const second = boundary === 'end' ? 59 : 0;

  let utcGuess = Date.UTC(year, month - 1, day, hour, minute, second);
  for (let index = 0; index < 3; index += 1) {
    const offset = getTimeZoneOffsetMilliseconds(EDMONTON_TIMEZONE, new Date(utcGuess));
    const nextGuess = Date.UTC(year, month - 1, day, hour, minute, second) - offset;
    if (nextGuess === utcGuess) {
      break;
    }
    utcGuess = nextGuess;
  }

  return new Date(utcGuess).toISOString().replace('.000Z', 'Z');
}

export function ComparisonFilters({
  availability,
  filters,
  dateWindowStart,
  dateWindowEnd,
  dateRangeError = null,
  onChange,
  onSubmit,
  disabled = false,
}: ComparisonFiltersProps) {
  const [openMenu, setOpenMenu] = useState<'categories' | null>(null);
  const categoriesRef = useRef<HTMLDivElement>(null);
  const serviceCategories = availability?.serviceCategories ?? [];
  const isDateRangeInvalid = Boolean(dateRangeError);
  const canSubmitAllCategories = serviceCategories.length > 0;
  const startMin = dateWindowStart ? toDateInputValue(dateWindowStart) : undefined;
  const endMax = dateWindowEnd ? toDateInputValue(dateWindowEnd) : undefined;
  const serviceCategoriesLabel = useMemo(() => {
    if (filters.serviceCategories.length === 0) return 'All categories';
    if (filters.serviceCategories.length <= 2) return filters.serviceCategories.join(', ');
    return `${filters.serviceCategories.length} categories selected`;
  }, [filters.serviceCategories]);

  useEffect(() => {
    if (!openMenu) return;

    const handlePointerDown = (event: MouseEvent) => {
      const target = event.target;
      if (!(target instanceof Node)) return;
      if (categoriesRef.current?.contains(target)) return;
      setOpenMenu(null);
    };

    document.addEventListener('mousedown', handlePointerDown);
    return () => document.removeEventListener('mousedown', handlePointerDown);
  }, [openMenu]);

  const updateDateField = (boundary: 'start' | 'end') => (event: ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    onChange({
      ...filters,
      [boundary === 'start' ? 'timeRangeStart' : 'timeRangeEnd']: toEdmontonBoundaryIso(value, boundary),
    });
  };

  const toggleCategory = (category: string) => {
    const nextCategories = filters.serviceCategories.includes(category)
      ? filters.serviceCategories.filter((item) => item !== category)
      : [...filters.serviceCategories, category].sort();
    onChange({ ...filters, serviceCategories: nextCategories });
  };

  return (
    <div className="grid gap-5">
      <div className="grid gap-2">
        <Label htmlFor="comparison-categories">Service categories</Label>
        <div ref={categoriesRef} className={openMenu === 'categories' ? 'relative z-[120]' : 'relative z-10'}>
          <button
            id="comparison-categories"
            type="button"
            onClick={() => setOpenMenu((current) => (current === 'categories' ? null : 'categories'))}
            disabled={disabled}
            className="flex min-h-12 w-full items-center justify-between rounded-2xl border border-[rgba(25,58,90,0.14)] bg-white px-4 py-3 text-left text-sm text-ink shadow-sm transition hover:border-accent focus:border-accent focus:outline-none disabled:cursor-not-allowed disabled:opacity-50"
            aria-haspopup="listbox"
            aria-expanded={openMenu === 'categories'}
          >
            <span>{serviceCategoriesLabel}</span>
            <span className="ml-4 text-muted">{openMenu === 'categories' ? 'Hide' : 'Choose'}</span>
          </button>
          {openMenu === 'categories' ? (
            <div className="absolute z-[130] mt-2 w-full rounded-2xl border border-[rgba(25,58,90,0.14)] bg-white p-3 shadow-panel backdrop-blur-xl">
              <div className="mb-2 flex items-center justify-between">
                <p className="m-0 text-sm font-semibold text-ink">Service categories</p>
                <button
                  type="button"
                  onClick={() => onChange({ ...filters, serviceCategories: [] })}
                  className="text-sm font-medium text-forecast hover:underline"
                >
                  Clear all
                </button>
              </div>
              <div role="listbox" aria-label="Service categories" className="max-h-64 space-y-2 overflow-auto">
                {serviceCategories.length === 0 ? <p className="m-0 text-sm text-muted">No categories available.</p> : null}
                {serviceCategories.length > 0 ? (
                  <button
                    type="button"
                    onClick={() => {
                      onChange({ ...filters, serviceCategories: [] });
                      setOpenMenu(null);
                    }}
                    className="flex w-full items-center justify-between rounded-xl px-2 py-2 text-left text-sm text-ink transition hover:bg-[#eef5fa]"
                    aria-pressed={filters.serviceCategories.length === 0}
                  >
                    <span>All categories</span>
                    {filters.serviceCategories.length === 0 ? <span className="text-forecast">Selected</span> : null}
                  </button>
                ) : null}
                {serviceCategories.map((category) => (
                  <button
                    key={category}
                    type="button"
                    onClick={() => toggleCategory(category)}
                    className="flex w-full items-center justify-between rounded-xl px-2 py-2 text-left text-sm text-ink transition hover:bg-[#eef5fa]"
                    aria-pressed={filters.serviceCategories.includes(category)}
                  >
                    <span>{category}</span>
                    {filters.serviceCategories.includes(category) ? <span className="text-forecast">Selected</span> : null}
                  </button>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="grid gap-2">
          <Label htmlFor="comparison-start">Start</Label>
          <Input
            id="comparison-start"
            type="date"
            value={toDateInputValue(filters.timeRangeStart)}
            min={startMin}
            max={endMax}
            disabled={disabled}
            onChange={updateDateField('start')}
          />
        </div>
        <div className="grid gap-2">
          <Label htmlFor="comparison-end">End</Label>
          <Input
            id="comparison-end"
            type="date"
            value={toDateInputValue(filters.timeRangeEnd)}
            min={startMin}
            max={endMax}
            disabled={disabled}
            onChange={updateDateField('end')}
          />
        </div>
      </div>

      {isDateRangeInvalid ? (
        <p className="rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {dateRangeError}
        </p>
      ) : null}

      <button
        type="button"
        disabled={disabled || !canSubmitAllCategories || isDateRangeInvalid}
        onClick={onSubmit}
        className="inline-flex min-h-11 items-center justify-center rounded-2xl bg-accent px-4 text-sm font-semibold text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-60"
      >
        Compare demand
      </button>
    </div>
  );
}
