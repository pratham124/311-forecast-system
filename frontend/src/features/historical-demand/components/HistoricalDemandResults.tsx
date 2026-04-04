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
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-[20px] border border-slate-200 bg-white/80 p-4">
              <span className="block text-xs font-semibold uppercase tracking-[0.16em] text-muted">Total demand</span>
              <strong className="mt-2 block text-2xl text-ink">{totalDemand}</strong>
            </div>
            <div className="rounded-[20px] border border-slate-200 bg-white/80 p-4">
              <span className="block text-xs font-semibold uppercase tracking-[0.16em] text-muted">Peak day</span>
              <strong className="mt-2 block text-lg text-ink">{maxCount}</strong>
            </div>
            <div className="rounded-[20px] border border-slate-200 bg-white/80 p-4">
              <span className="block text-xs font-semibold uppercase tracking-[0.16em] text-muted">Categories</span>
              <strong className="mt-2 block text-lg text-ink">{uniqueCategories}</strong>
            </div>
          </div>
          {response.summaryPoints.map((point) => (
            <div
              key={`${point.bucketStart}:${point.serviceCategory}:${point.geographyKey ?? 'city'}`}
              className="rounded-[22px] border border-slate-200 bg-white/80 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.5)]"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="m-0 text-sm font-semibold text-ink">{point.serviceCategory}</p>
                  <div className="mt-1 flex flex-wrap items-center gap-2">
                    <span className="text-xs font-medium uppercase tracking-[0.14em] text-muted">
                      {formatBucketDate(point.bucketStart)}
                    </span>
                    {point.geographyKey ? (
                      <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-600">
                        {point.geographyKey}
                      </span>
                    ) : null}
                  </div>
                </div>
                <div className="text-right">
                  <span className="block text-[11px] font-semibold uppercase tracking-[0.14em] text-muted">Demand count</span>
                  <strong className="mt-1 block text-xl text-ink">{point.demandCount}</strong>
                </div>
              </div>
              <div className="mt-4 h-3 overflow-hidden rounded-full bg-slate-200">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-accent to-history"
                  style={{ width: `${(point.demandCount / maxCount) * 100}%` }}
                />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className="rounded-[28px]">
        <CardHeader>
          <CardTitle>Summary table</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <div className="min-w-full rounded-[22px] border border-slate-200 bg-white/80 p-2">
            <table className="min-w-full border-separate border-spacing-0 text-left text-sm text-ink">
              <thead>
                <tr className="text-muted">
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-[0.16em]">Date</th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-[0.16em]">Category</th>
                  <th className="px-4 py-3 text-xs font-semibold uppercase tracking-[0.16em]">Demand count</th>
                </tr>
              </thead>
              <tbody>
                {response.summaryPoints.map((point) => (
                  <tr key={`${point.bucketStart}:${point.serviceCategory}:${point.geographyKey ?? 'city'}:row`}>
                    <td className="px-4 py-3">
                      <div className="rounded-2xl bg-slate-50/80 px-3 py-2 font-medium text-ink">
                        {formatBucketDate(point.bucketStart)}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap items-center gap-2 rounded-2xl bg-slate-50/80 px-3 py-2">
                        <span className="font-medium text-ink">{point.serviceCategory}</span>
                        {point.geographyKey ? (
                          <span className="rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-600 shadow-sm">
                            {point.geographyKey}
                          </span>
                        ) : null}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="rounded-2xl bg-slate-50/80 px-3 py-2 text-right">
                        <strong className="text-base text-ink">{point.demandCount}</strong>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </section>
  );
}
