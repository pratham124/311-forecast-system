import * as React from 'react';

import { cn } from '../../lib/utils';

const Select = React.forwardRef<HTMLSelectElement, React.ComponentProps<'select'>>(({ className, children, ...props }, ref) => (
  <div className="relative">
    <select
      ref={ref}
      className={cn(
        'flex h-12 w-full appearance-none rounded-2xl border border-[rgba(25,58,90,0.14)] bg-white px-4 py-3 pr-12 text-sm text-ink shadow-sm outline-none transition hover:border-accent focus-visible:border-accent focus-visible:ring-2 focus-visible:ring-accent/20 disabled:cursor-not-allowed disabled:opacity-50',
        className,
      )}
      {...props}
    >
      {children}
    </select>
    <span className="pointer-events-none absolute inset-y-0 right-4 flex items-center text-accent" aria-hidden="true">
      <svg viewBox="0 0 20 20" fill="none" className="h-4 w-4">
        <path d="M5 7.5 10 12.5 15 7.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </span>
  </div>
));
Select.displayName = 'Select';

export { Select };
