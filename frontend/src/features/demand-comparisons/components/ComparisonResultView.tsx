import { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import type { DemandComparisonResponse } from '../../../types/demandComparisons';

const COLORS = ["#0284c7", "#f97316", "#16a34a", "#9333ea", "#e11d48", "#ca8a04", "#0891b2", "#84cc16"];

export function ComparisonResultView({ response }: { response: DemandComparisonResponse }) {
  const series = response.series ?? [];
  const missing = response.missingCombinations ?? [];

  const chartConfiguration = useMemo(() => {
    const groupedByDate: Record<string, any> = {};
    const lineKeys = new Set<string>();

    series.forEach((s) => {
      const key = `${s.seriesType.toUpperCase()}: ${s.serviceCategory} (${s.geographyKey ?? 'All'})`;
      lineKeys.add(key);
      s.points.forEach((p) => {
        const label = p.bucketStart.length > 10 ? p.bucketStart.slice(0, 10) : p.bucketStart;
        if (!groupedByDate[label]) {
          groupedByDate[label] = { dateLabel: label };
        }
        groupedByDate[label][key] = p.value;
      });
    });

    return {
      data: Object.values(groupedByDate).sort((a, b) => a.dateLabel.localeCompare(b.dateLabel)),
      lines: Array.from(lineKeys)
    };
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
                {chartConfiguration.lines.map((key, i) => (
                  <Line
                    key={key}
                    type="monotone"
                    dataKey={key}
                    stroke={COLORS[i % COLORS.length]}
                    strokeWidth={2}
                    dot={{ r: 3 }}
                    activeDot={{ r: 6 }}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-xl text-ink">Series table</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto min-w-0">
          <table className="min-w-full border-collapse text-left text-sm text-ink">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="py-2 pr-4">Type</th>
                <th className="py-2 pr-4">Category</th>
                <th className="py-2 pr-4">Geography</th>
                <th className="py-2 pr-4">Points</th>
              </tr>
            </thead>
            <tbody>
              {series.map((item) => (
                <tr key={`${item.seriesType}:${item.serviceCategory}:${item.geographyKey ?? 'all'}`} className="border-b border-slate-100 align-top">
                  <td className="py-2 pr-4">{item.seriesType}</td>
                  <td className="py-2 pr-4">{item.serviceCategory}</td>
                  <td className="py-2 pr-4">{item.geographyKey ?? 'All selected'}</td>
                  <td className="py-2 pr-4">
                    <div className="max-h-32 overflow-y-auto overflow-x-hidden break-all min-w-[200px]">
                      {item.points.map((point) => (
                        <div key={`${point.bucketStart}:${point.bucketEnd}`}>
                          {point.bucketStart} - {point.value}
                        </div>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}