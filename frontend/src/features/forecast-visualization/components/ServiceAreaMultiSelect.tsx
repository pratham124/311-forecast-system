import { useMemo, type RefObject } from 'react';

interface ServiceAreaMultiSelectProps {
  options: string[];
  selectedValues: string[];
  onChange: (values: string[]) => void;
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  containerRef: RefObject<HTMLDivElement>;
}

export function ServiceAreaMultiSelect({ options, selectedValues, onChange, isOpen, onOpenChange, containerRef }: ServiceAreaMultiSelectProps) {
  const allSelected = selectedValues.length === 0;

  const buttonLabel = useMemo(() => {
    if (allSelected) return 'All service areas';
    if (selectedValues.length <= 2) return selectedValues.join(', ');
    return `${selectedValues.length} service areas selected`;
  }, [allSelected, selectedValues]);

  const toggleValue = (value: string) => {
    if (selectedValues.includes(value)) {
      onChange(selectedValues.filter((item) => item !== value));
      return;
    }
    onChange([...selectedValues, value].sort());
  };

  return (
    <div ref={containerRef} className={isOpen ? 'relative z-[120]' : 'relative z-10'}>
      <button
        id="service-category"
        type="button"
        onClick={() => onOpenChange(!isOpen)}
        className="flex min-h-12 w-full items-center justify-between rounded-2xl border border-[rgba(25,58,90,0.14)] bg-white px-4 py-3 text-left text-sm text-ink shadow-sm transition hover:border-accent focus:border-accent focus:outline-none"
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <span>{buttonLabel}</span>
        <span className="ml-4 text-muted">{isOpen ? 'Hide' : 'Choose'}</span>
      </button>
      {isOpen ? (
        <div className="absolute z-[130] mt-2 w-full rounded-2xl border border-[rgba(25,58,90,0.14)] bg-white p-3 shadow-panel backdrop-blur-xl">
          <div className="mb-2 flex items-center justify-between">
            <p className="m-0 text-sm font-semibold text-ink">Service areas</p>
            <button
              type="button"
              onClick={() => onChange([])}
              className="text-sm font-medium text-forecast hover:underline"
            >
              Clear all
            </button>
          </div>
          <div role="listbox" aria-label="Service areas" className="max-h-64 space-y-2 overflow-auto">
            {options.length === 0 ? <p className="m-0 text-sm text-muted">No service areas available.</p> : null}
            {options.length > 0 ? (
              <button
                type="button"
                onClick={() => {
                  onChange([]);
                  onOpenChange(false);
                }}
                className="flex w-full items-center justify-between rounded-xl px-2 py-2 text-left text-sm text-ink transition hover:bg-[#eef5fa]"
                aria-pressed={allSelected}
              >
                <span>All service areas</span>
                {allSelected ? <span className="text-forecast">Selected</span> : null}
              </button>
            ) : null}
            {options.map((option) => (
              <button
                key={option}
                type="button"
                onClick={() => toggleValue(option)}
                className="flex w-full items-center justify-between rounded-xl px-2 py-2 text-left text-sm text-ink transition hover:bg-[#eef5fa]"
                aria-pressed={selectedValues.includes(option)}
              >
                <span>{option}</span>
                {selectedValues.includes(option) ? <span className="text-forecast">Selected</span> : null}
              </button>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}
