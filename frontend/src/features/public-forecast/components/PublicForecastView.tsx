import { Card, CardContent } from '../../../components/ui/card';
import type { PublicForecastView as PublicForecastViewModel } from '../../../types/publicForecast';

type PublicForecastViewProps = {
  forecast: PublicForecastViewModel;
  sortOrder: 'desc' | 'asc';
};

function formatPublishedAt(value?: string | null): string {
  if (!value) return 'Not available';
  return new Date(value).toLocaleString([], {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
  });
}

function getDemandValue(value?: number | null): number | null {
  return value == null ? null : value;
}

function sortCategorySummaries(
  summaries: NonNullable<PublicForecastViewModel['categorySummaries']>,
  sortOrder: 'desc' | 'asc',
) {
  return [...summaries].sort((left, right) => {
    const leftValue = getDemandValue(left.forecastDemandValue);
    const rightValue = getDemandValue(right.forecastDemandValue);
    if (leftValue == null && rightValue == null) return left.serviceCategory.localeCompare(right.serviceCategory);
    if (leftValue == null) return 1;
    if (rightValue == null) return -1;
    if (leftValue === rightValue) return left.serviceCategory.localeCompare(right.serviceCategory);
    return sortOrder === 'desc' ? rightValue - leftValue : leftValue - rightValue;
  });
}

export function PublicForecastView({ forecast, sortOrder }: PublicForecastViewProps) {
  const categorySummaries = sortCategorySummaries(forecast.categorySummaries ?? [], sortOrder);

  return (
    <>
      <section className="mt-6 grid gap-4 md:grid-cols-3">
        <Card className="rounded-[24px] border-white/70 bg-white/90">
          <CardContent className="p-5">
            <span className="block text-xs uppercase tracking-[0.2em] text-muted">Forecast window</span>
            <strong className="mt-2 block text-lg text-ink">{forecast.forecastWindowLabel}</strong>
          </CardContent>
        </Card>
        <Card className="rounded-[24px] border-white/70 bg-white/90">
          <CardContent className="p-5">
            <span className="block text-xs uppercase tracking-[0.2em] text-muted">Published</span>
            <strong className="mt-2 block text-lg text-ink">{formatPublishedAt(forecast.publishedAt)}</strong>
          </CardContent>
        </Card>
        <Card className="rounded-[24px] border-white/70 bg-white/90">
          <CardContent className="p-5">
            <span className="block text-xs uppercase tracking-[0.2em] text-muted">Coverage</span>
            <strong className="mt-2 block text-lg capitalize text-ink">{forecast.coverageStatus}</strong>
          </CardContent>
        </Card>
      </section>

      <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {categorySummaries.map((summary) => (
          <Card key={summary.serviceCategory} className="rounded-[24px] border-[rgba(15,23,42,0.08)] bg-white/95 shadow-[0_18px_45px_rgba(15,23,42,0.08)]">
            <CardContent className="grid gap-3 p-5">
              <div>
                <p className="text-xs uppercase tracking-[0.2em] text-accent/80">Service category</p>
                <h2 className="mt-2 text-2xl font-semibold text-ink">{summary.serviceCategory}</h2>
              </div>
              <div className="grid gap-1">
                <span className="text-sm text-muted">Expected demand</span>
                <strong className="text-4xl leading-none text-ink">
                  {summary.forecastDemandValue != null ? Math.round(summary.forecastDemandValue) : 'N/A'}
                </strong>
              </div>
              <p className="text-sm leading-6 text-muted">{summary.demandLevelSummary ?? 'Public-safe demand summary available.'}</p>
            </CardContent>
          </Card>
        ))}
      </section>
    </>
  );
}
