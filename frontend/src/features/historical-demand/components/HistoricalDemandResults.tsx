import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import type { HistoricalDemandResponse } from '../../../types/historicalDemand';

type HistoricalDemandResultsProps = {
  response: HistoricalDemandResponse;
};

function formatBucketDate(value: string): string {
  if (!value) {
    return '';
  }
  return value.slice(0, 10);
}

export function HistoricalDemandResults({ response }: HistoricalDemandResultsProps) {
  if (response.summaryPoints.length === 0) return null;
  const maxCount = Math.max(...response.summaryPoints.map((point) => point.demandCount), 1);
  const totalDemand = response.summaryPoints.reduce((sum, point) => sum + point.demandCount, 0);
  const uniqueCategories = new Set(response.summaryPoints.map((point) => point.serviceCategory)).size;

  return (
    <section className="grid gap-5" aria-label="historical demand results">
      <Card className="rounded-[28px]">
        <CardHeader>
          <CardTitle>Historical demand pattern</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-5">
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="relative overflow-hidden rounded-[20px] border border-slate-200 bg-white/80 p-5 shadow-sm transition-transform hover:-translate-y-0.5">
              <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-accent to-accent-strong" />
              <span className="block text-xs font-bold uppercase tracking-[0.16em] text-muted">Total demand</span>
              <strong className="mt-2 block text-3xl font-extrabold text-ink">{totalDemand}</strong>
            </div>
            <div className="relative overflow-hidden rounded-[20px] border border-slate-200 bg-white/80 p-5 shadow-sm transition-transform hover:-translate-y-0.5">
              <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-history to-emerald-400" />
              <span className="block text-xs font-bold uppercase tracking-[0.16em] text-muted">Peak day</span>
              <strong className="mt-2 block text-2xl font-extrabold text-ink">{maxCount}</strong>
            </div>
            <div className="relative overflow-hidden rounded-[20px] border border-slate-200 bg-white/80 p-5 shadow-sm transition-transform hover:-translate-y-0.5">
              <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-purple-500 to-indigo-500" />
              <span className="block text-xs font-bold uppercase tracking-[0.16em] text-muted">Categories</span>
              <strong className="mt-2 block text-2xl font-extrabold text-ink">{uniqueCategories}</strong>
            </div>
          </div>
          <div className="grid gap-5 max-h-[500px] overflow-y-auto pr-3 pb-2 custom-scrollbar">
          {response.summaryPoints.map((point) => (
            <div
              key={`${point.bucketStart}:${point.serviceCategory}:${point.geographyKey ?? 'city'}`}
              className="group rounded-[22px] border border-slate-200 bg-white/80 p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.5)] transition-all hover:-translate-y-1 hover:shadow-md hover:border-accent/40"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="m-0 text-[15px] font-bold text-ink">{point.serviceCategory}</p>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <span className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">
                      {formatBucketDate(point.bucketStart)}
                    </span>
                    {point.geographyKey ? (
                      <span className="rounded-full bg-slate-100/80 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em] text-slate-600 ring-1 ring-slate-200/50">
                        {point.geographyKey}
                      </span>
                    ) : null}
                  </div>
                </div>
                <div className="text-right">
                  <span className="block text-[11px] font-bold uppercase tracking-[0.14em] text-muted">Demand count</span>
                  <strong className="mt-1 block text-2xl font-extrabold text-ink transition-colors group-hover:text-accent">{point.demandCount}</strong>
                </div>
              </div>
              <div className="mt-5 h-3.5 overflow-hidden rounded-full bg-slate-100 shadow-inner">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-accent via-accent-strong to-history transition-all duration-1000 ease-out"
                  style={{ width: `${(point.demandCount / maxCount) * 100}%` }}
                />
              </div>
            </div>
          ))}
          </div>
        </CardContent>
      </Card>


    </section>
  );
}
