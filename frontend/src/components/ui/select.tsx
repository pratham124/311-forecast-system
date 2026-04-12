import * as React from 'react';
import { cn } from '../../lib/utils';

type SelectChangeEvent = {
  target: {
    value: string;
    name?: string;
  };
};

type SelectProps = Omit<React.HTMLAttributes<HTMLDivElement>, 'onChange'> & {
  value?: string;
  onChange?: (event: SelectChangeEvent) => void;
  name?: string;
  id?: string;
};

const Select = React.forwardRef<HTMLDivElement, SelectProps>((({ className, children, value, onChange, name, id, ...props }, ref) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const containerRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const handlePointerDown = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handlePointerDown);
    return () => document.removeEventListener('mousedown', handlePointerDown);
  }, []);

  const options = React.useMemo(() => {
    return React.Children.toArray(children).map((child) => {
      if (React.isValidElement(child) && child.type === 'option') {
        return {
          value: child.props.value as string,
          label: child.props.children as string,
        };
      }
      return null;
    }).filter(Boolean) as Array<{ value: string; label: string }>;
  }, [children]);

  const selectedOption = options.find((opt) => opt.value === value) || options[0];

  return (
    <div ref={containerRef} className={cn('relative w-full', isOpen ? 'z-[120]' : 'z-10')}>
      <button
        id={id}
        type="button"
        onBlur={() => {
          // We don't use onBlur here because it fires before click events on items
        }}
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          'flex min-h-12 w-full items-center justify-between rounded-2xl border border-[rgba(25,58,90,0.14)] bg-white px-4 py-3 text-left text-sm text-ink shadow-sm transition hover:border-accent focus:border-accent focus:outline-none',
          className
        )}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
      >
        <span className="truncate">{selectedOption?.label || 'Select...'}</span>
        <span className="ml-4 text-muted">{isOpen ? 'Hide' : 'Choose'}</span>
      </button>

      {isOpen ? (
        <div 
          className="absolute left-0 top-full z-[130] mt-2 w-full rounded-2xl border border-[rgba(25,58,90,0.14)] bg-white p-3 shadow-panel backdrop-blur-xl animate-in fade-in zoom-in-95 duration-200"
          role="listbox"
        >
          <div className="max-h-60 space-y-2 overflow-y-auto">
            {options.map((option) => (
              <button
                key={option.value}
                type="button"
                role="option"
                aria-selected={value === option.value}
                onClick={() => {
                  if (onChange) {
                    onChange({ target: { value: option.value, name } });
                  }
                  setIsOpen(false);
                }}
                className={cn(
                  "flex w-full items-center justify-between rounded-xl px-2 py-2 text-left text-sm text-ink transition hover:bg-[#eef5fa]",
                  value === option.value && "bg-[#eef5fa]"
                )}
              >
                <span>{option.label}</span>
                {value === option.value && <span className="text-forecast">Selected</span>}
              </button>
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}));
Select.displayName = 'Select';

export { Select };
