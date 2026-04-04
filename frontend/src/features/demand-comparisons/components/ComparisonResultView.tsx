import { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import type { DemandComparisonResponse } from '../../../types/demandComparisons';

function formatDateLabel(value: string): string {
  return value.length > 10 ? value.slice(0, 10) : value;
}

function formatOutcomeLabel(value: string): string {
  return value.replace(/_/g, ' ');
}

export function ComparisonResultView({ response }: { response: DemandComparisonResponse }) {
  const series = response.series ?? [];
  const missing = response.missingCombinations ?? [];
  const outcomeTone =
    response.outcomeStatus === 'success'
      ? 'border-emerald-200 bg-emerald-50 text-emerald-800'
      : response.outcomeStatus === 'forecast_only' || response.outcomeStatus === 'historical_only'
        ? 'border-amber-200 bg-amber-50 text-amber-800'
        : 'border-sky-200 bg-sky-50 text-sky-800';

  const chartConfiguration = useMemo(() => {
    const groupedByDate: Record<string, { dateLabel: string; historical?: number; forecast?: number }> = {};

    series.forEach((s) => {
      s.points.forEach((p) => {
        const label = formatDateLabel(p.bucketStart);
        if (!groupedByDate[label]) {
          groupedByDate[label] = { dateLabel: label };
        }
        groupedByDate[label][s.seriesType] = (groupedByDate[label][s.seriesType] ?? 0) + p.value;
      });
    });

    return {
      data: Object.values(groupedByDate).sort((a, b) => a.dateLabel.localeCompare(b.dateLabel)),
    };
  }, [series]);

  const tableGroups = useMemo(() => {
    const grouped = new Map<string, typeof series>();
    series.forEach((item) => {
      const key = item.serviceCategory;
      const current = grouped.get(key) ?? [];
      current.push(item);
      grouped.set(key, current);
    });
    return Array.from(grouped.entries()).sort(([left], [right]) => left.localeCompare(right));
  }, [series]);

  return (
    <div className="grid gap-5 min-w-0">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-2xl text-ink">Comparison summary</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="flex flex-wrap items-center gap-3">
            <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] ${outcomeTone}`}>
              {formatOutcomeLabel(response.outcomeStatus)}
            </span>
            <p className="m-0 text-sm leading-6 text-muted">
              {response.message ?? 'Comparison results are ready to review.'}
            </p>
          </div>
          <div className="grid gap-3 md:grid-cols-3">
            <div className="rounded-[22px] border border-slate-200 bg-white/80 p-4">
              <span className="block text-xs font-semibold uppercase tracking-[0.16em] text-muted">Outcome</span>
              <strong className="mt-2 block text-base capitalize text-ink">{formatOutcomeLabel(response.outcomeStatus)}</strong>
            </div>
            <div className="rounded-[22px] border border-slate-200 bg-white/80 p-4">
              <span className="block text-xs font-semibold uppercase tracking-[0.16em] text-muted">Granularity</span>
              <strong className="mt-2 block text-base capitalize text-ink">{response.comparisonGranularity ?? 'daily'}</strong>
            </div>
            <div className="rounded-[22px] border border-slate-200 bg-white/80 p-4">
              <span className="block text-xs font-semibold uppercase tracking-[0.16em] text-muted">Series returned</span>
              <strong className="mt-2 block text-base text-ink">{series.length}</strong>
            </div>
          </div>
        </CardContent>
      </Card>

      {missing.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-xl text-ink">Missing combinations</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-2 text-sm text-ink">
            {missing.map((item) => (
              <p key={`${item.serviceCategory}:${item.geographyKey ?? 'all'}`}>{item.message}</p>
            ))}
          </CardContent>
        </Card>
      ) : null}

      {chartConfiguration.data.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-xl text-ink">Comparison Chart</CardTitle>
          </CardHeader>
          <CardContent className="h-[400px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartConfiguration.data} margin={{ top: 10, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.5} />
                <XAxis dataKey="dateLabel" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip 
                   contentStyle={{ backgroundColor: 'white', borderRadius: '8px', border: '1px solid #e2e8f0' }} 
                   itemStyle={{ fontSize: '13px' }}
                   labelStyle={{ fontWeight: 'bold', marginBottom: '8px' }}
                />
                <Legend wrapperStyle={{ paddingTop: '20px', fontSize: '13px' }} />
                <Line type="monotone" dataKey="historical" name="Historical" stroke="#0284c7" strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 6 }} />
                <Line type="monotone" dataKey="forecast" name="Forecast" stroke="#f97316" strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-xl text-ink">Series table</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4">
          <div className="grid gap-4 md:grid-cols-2">
            {tableGroups.map(([category, items]) => (
              <div
                key={category}
                className="rounded-[22px] border border-slate-200 bg-white/80 p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.5)]"
              >
                <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-1">
                  <h3 className="m-0 text-base font-semibold text-ink">{category}</h3>
                  <span className="text-xs font-semibold uppercase tracking-[0.22em] text-muted">
                    {items.length} series
                  </span>
                </div>
                <div className="mt-4 space-y-3">
                  {items.map((item) => (
                    <div
                      key={`${item.seriesType}:${item.serviceCategory}:${item.geographyKey ?? 'all'}`}
                      className="rounded-2xl border border-slate-100 bg-slate-50/70 p-3"
                    >
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="text-sm font-semibold uppercase tracking-[0.18em] text-muted">
                          {item.seriesType}
                        </span>
                        <span className="text-xs font-medium uppercase tracking-[0.16em] text-muted">
                          {item.points.length} points
                        </span>
                      </div>
                      <div className="mt-2 grid gap-2 text-xs leading-tight text-muted sm:grid-cols-2">
                        {item.points.map((point) => (
                          <div
                            key={`${point.bucketStart}:${point.bucketEnd}`}
                            className="flex items-center justify-between rounded-2xl bg-white/50 px-3 py-1 text-[11px] font-semibold text-ink shadow-[0_1px_3px_rgba(15,23,42,0.08)]"
                          >
                            <span>{formatDateLabel(point.bucketStart)}</span>
                            <span className="text-sm text-ink">{point.value}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
