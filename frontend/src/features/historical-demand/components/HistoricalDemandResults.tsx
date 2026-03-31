import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import type { HistoricalDemandResponse } from '../../../types/historicalDemand';

type HistoricalDemandResultsProps = {
  response: HistoricalDemandResponse;
};

export function HistoricalDemandResults({ response }: HistoricalDemandResultsProps) {
  if (response.summaryPoints.length === 0) return null;
  const maxCount = Math.max(...response.summaryPoints.map((point) => point.demandCount), 1);

  return (
    <section className="grid gap-5" aria-label="historical demand results">
      <Card className="rounded-[28px]">
        <CardHeader>
          <CardTitle>Historical demand pattern</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3">
          {response.summaryPoints.map((point) => (
            <div key={`${point.bucketStart}:${point.serviceCategory}:${point.geographyKey ?? 'city'}`} className="grid gap-2">
              <div className="flex items-center justify-between gap-4 text-sm text-ink">
                <span>{point.serviceCategory} · {new Date(point.bucketStart).toLocaleDateString()}</span>
                <strong>{point.demandCount}</strong>
              </div>
              <div className="h-3 overflow-hidden rounded-full bg-slate-200">
                <div className="h-full rounded-full bg-accent" style={{ width: `${(point.demandCount / maxCount) * 100}%` }} />
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
          <table className="min-w-full text-left text-sm text-ink">
            <thead>
              <tr className="border-b border-slate-200 text-muted">
                <th className="py-2 pr-4">Bucket</th>
                <th className="py-2 pr-4">Category</th>
                <th className="py-2 pr-4">Geography</th>
                <th className="py-2">Demand count</th>
              </tr>
            </thead>
            <tbody>
              {response.summaryPoints.map((point) => (
                <tr key={`${point.bucketStart}:${point.serviceCategory}:${point.geographyKey ?? 'city'}:row`} className="border-b border-slate-100">
                  <td className="py-2 pr-4">{new Date(point.bucketStart).toLocaleDateString()}</td>
                  <td className="py-2 pr-4">{point.serviceCategory}</td>
                  <td className="py-2 pr-4">{point.geographyKey ?? 'City-wide'}</td>
                  <td className="py-2">{point.demandCount}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </section>
  );
}
