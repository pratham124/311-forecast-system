import { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import type { DemandComparisonResponse } from '../../../types/demandComparisons';

function formatDateLabel(value: string): string {
  return value.length > 10 ? value.slice(0, 10) : value;
}

export function ComparisonResultView({ response }: { response: DemandComparisonResponse }) {
  const series = response.series ?? [];
  const missing = response.missingCombinations ?? [];

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
        <CardHeader>
          <CardTitle className="text-2xl text-ink">Comparison summary</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 text-sm text-ink">
          <p>Outcome: <strong>{response.outcomeStatus}</strong></p>
          <p>Granularity: <strong>{response.comparisonGranularity ?? 'daily'}</strong></p>
          <p>Series returned: <strong>{series.length}</strong></p>
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
          {tableGroups.map(([category, items]) => (
            <div key={category} className="overflow-x-auto min-w-0 rounded-[22px] border border-slate-200 bg-white/80 p-4">
              <h3 className="m-0 text-base font-semibold text-ink">{category}</h3>
              <table className="mt-3 min-w-full border-collapse text-left text-sm text-ink">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="py-2 pr-4">Type</th>
                    <th className="py-2 pr-4">Points</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => (
                    <tr key={`${item.seriesType}:${item.serviceCategory}:${item.geographyKey ?? 'all'}`} className="border-b border-slate-100 align-top last:border-b-0">
                      <td className="py-2 pr-4">{item.seriesType}</td>
                      <td className="py-2 pr-4">
                        <div className="max-h-32 overflow-y-auto overflow-x-hidden break-all min-w-[200px]">
                          {item.points.map((point) => (
                            <div key={`${point.bucketStart}:${point.bucketEnd}`}>
                              {formatDateLabel(point.bucketStart)} - {point.value}
                            </div>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
