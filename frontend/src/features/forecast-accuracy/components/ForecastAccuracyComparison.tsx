import type { ForecastAccuracyAlignedBucket } from '../../../types/forecastAccuracy';

function formatBucketTime(value: string): string {
  return new Intl.DateTimeFormat([], {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
  }).format(new Date(value));
}

function getErrorSeverity(absoluteError: number, forecastValue: number): 'low' | 'medium' | 'high' {
  if (forecastValue === 0) return absoluteError === 0 ? 'low' : 'high';
  const pct = absoluteError / forecastValue;
  if (pct <= 0.1) return 'low';
  if (pct <= 0.3) return 'medium';
  return 'high';
}

const SEVERITY_STYLES = {
  low: 'bg-emerald-50 text-emerald-700 ring-emerald-200/60',
  medium: 'bg-amber-50 text-amber-700 ring-amber-200/60',
  high: 'bg-red-50 text-red-700 ring-red-200/60',
} as const;

const SEVERITY_DOT = {
  low: 'bg-emerald-400',
  medium: 'bg-amber-400',
  high: 'bg-red-400',
} as const;

export function ForecastAccuracyComparison({ alignedBuckets }: { alignedBuckets: ForecastAccuracyAlignedBucket[] }) {
  if (alignedBuckets.length === 0) {
    return (
      <div className="rounded-[22px] border border-dashed border-slate-300 bg-slate-50/60 p-8 text-center">
        <p className="m-0 text-sm text-muted">No aligned buckets to display.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-accent/10">
            <svg className="h-4 w-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
          </div>
          <div>
            <h3 className="m-0 text-sm font-semibold text-ink">Aligned Buckets</h3>
            <p className="m-0 text-xs text-muted">{alignedBuckets.length} comparison {alignedBuckets.length === 1 ? 'point' : 'points'}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {(['low', 'medium', 'high'] as const).map((level) => (
            <span key={level} className="flex items-center gap-1.5 text-[11px] font-medium text-slate-500">
              <span className={`inline-block h-2 w-2 rounded-full ${SEVERITY_DOT[level]}`} />
              {level === 'low' ? '≤10%' : level === 'medium' ? '10–30%' : '>30%'}
            </span>
          ))}
        </div>
      </div>

      {/* Table-style header row */}
      <div className="grid grid-cols-[1.3fr_1fr_1fr_1fr] gap-2 px-4 text-[11px] font-bold uppercase tracking-[0.18em] text-slate-400">
        <span>Time</span>
        <span className="text-right">Forecast</span>
        <span className="text-right">Actual</span>
        <span className="text-right">Abs Error</span>
      </div>

      {/* Bucket rows */}
      <div className="max-h-[460px] space-y-1.5 overflow-y-auto pr-1 custom-scrollbar">
        {alignedBuckets.map((bucket, index) => {
          const severity = getErrorSeverity(bucket.absoluteErrorValue, bucket.forecastValue);
          const diff = bucket.forecastValue - bucket.actualValue;
          const isOver = diff > 0;

          return (
            <div
              key={`${bucket.bucketStart}:${bucket.serviceCategory ?? 'all'}`}
              className="group grid grid-cols-[1.3fr_1fr_1fr_1fr] items-center gap-2 rounded-2xl border border-slate-100 bg-white/80 px-4 py-3 transition-all duration-200 hover:border-accent/30 hover:bg-white hover:shadow-[0_2px_12px_rgba(15,23,42,0.06)]"
              style={{ animationDelay: `${index * 20}ms` }}
            >
              {/* Time */}
              <div className="flex items-center gap-2.5">
                <span className={`inline-block h-2 w-2 shrink-0 rounded-full ${SEVERITY_DOT[severity]} transition-transform duration-200 group-hover:scale-125`} />
                <span className="text-sm font-medium text-ink">{formatBucketTime(bucket.bucketStart)}</span>
              </div>

              {/* Forecast */}
              <span className="text-right text-sm tabular-nums text-slate-600">
                {bucket.forecastValue.toFixed(2)}
              </span>

              {/* Actual */}
              <span className="text-right text-sm font-semibold tabular-nums text-ink">
                {bucket.actualValue.toFixed(2)}
              </span>

              {/* Abs error */}
              <div className="flex items-center justify-end gap-2">
                {diff !== 0 ? (
                  <span className={`text-[11px] font-medium ${isOver ? 'text-amber-500' : 'text-blue-500'}`}>
                    {isOver ? '▲' : '▼'}
                  </span>
                ) : null}
                <span className={`inline-flex rounded-lg px-2.5 py-1 text-xs font-semibold tabular-nums ring-1 ring-inset ${SEVERITY_STYLES[severity]}`}>
                  {bucket.absoluteErrorValue.toFixed(2)}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
