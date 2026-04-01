import { Card, CardContent, CardHeader, CardTitle } from '../../../components/ui/card';
import type { DemandComparisonResponse } from '../../../types/demandComparisons';

export function ComparisonResultView({ response }: { response: DemandComparisonResponse }) {
  const series = response.series ?? [];
  const missing = response.missingCombinations ?? [];

  return (
    <div className="grid gap-5">
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

      <Card>
        <CardHeader>
          <CardTitle className="text-xl text-ink">Series table</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
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
                    {item.points.map((point) => (
                      <div key={`${point.bucketStart}:${point.bucketEnd}`}>
                        {point.bucketStart} - {point.value}
                      </div>
                    ))}
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
