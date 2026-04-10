import { useEffect } from 'react';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { ForecastAccuracyFilters } from '../features/forecast-accuracy/components/ForecastAccuracyFilters';
import { ForecastAccuracyMetrics } from '../features/forecast-accuracy/components/ForecastAccuracyMetrics';
import { ForecastAccuracyMetricsUnavailable } from '../features/forecast-accuracy/components/ForecastAccuracyMetricsUnavailable';
import { ForecastAccuracyComparison } from '../features/forecast-accuracy/components/ForecastAccuracyComparison';
import { ForecastAccuracyUnavailable } from '../features/forecast-accuracy/components/ForecastAccuracyUnavailable';
import { ForecastAccuracyError } from '../features/forecast-accuracy/components/ForecastAccuracyError';
import { ForecastAccuracyErrorBoundary } from '../features/forecast-accuracy/components/ForecastAccuracyErrorBoundary';
import { useForecastAccuracy } from '../features/forecast-accuracy/hooks/useForecastAccuracy';
import { hasRenderableForecastAccuracy } from '../features/forecast-accuracy/state/forecastAccuracyState';

export function ForecastAccuracyPage() {
  const {
    filters,
    setFilters,
    serviceCategoryOptions,
    response,
    isLoading,
    isSubmitting,
    error,
    submit,
    reportRenderEvent,
  } = useForecastAccuracy();

  useEffect(() => {
    if (!response || !hasRenderableForecastAccuracy(response)) {
      return;
    }
    void reportRenderEvent({ renderStatus: 'rendered' });
  }, [reportRenderEvent, response]);

  return (
    <main className="mx-auto w-full max-w-6xl px-4 pb-14 pt-7 sm:px-6 lg:px-8" aria-label="forecast accuracy page">
      <Card className="relative z-20 grid gap-4 rounded-[28px] border-white/60 bg-white/85 p-2 shadow-[0_20px_60px_rgba(15,23,42,0.08)] md:grid-cols-[1.45fr_1fr] md:gap-6">
        <CardHeader className="gap-3 px-5 pb-5 pt-5 sm:px-6 sm:pt-6">
          <p className="m-0 text-[11px] font-semibold uppercase tracking-[0.22em] text-accent/80">Forecast Accuracy</p>
          <CardTitle className="m-0 max-w-3xl text-3xl leading-tight text-ink sm:text-4xl md:text-5xl md:leading-[1.02]">
            Compare retained forecasts against actual demand
          </CardTitle>
          <CardDescription className="max-w-2xl text-sm leading-6 text-muted sm:text-[15px]">
            Review aligned forecast versus actual buckets and the matching summary metrics for the selected scope.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid content-start gap-5 rounded-[24px] bg-slate-50/80 p-5 sm:p-6">
          <ForecastAccuracyFilters
            filters={filters}
            serviceCategoryOptions={serviceCategoryOptions}
            onChange={setFilters}
            onSubmit={() => {
              void submit();
            }}
            disabled={isSubmitting}
          />
        </CardContent>
      </Card>

      {isLoading ? (
        <Alert className="mt-5">
          <AlertDescription>Loading forecast accuracy...</AlertDescription>
        </Alert>
      ) : null}

      {error ? (
        <Alert variant="destructive" className="mt-5">
          <AlertTitle>Forecast accuracy request failed</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {response?.viewStatus === 'rendered_with_metrics' && response.metrics ? (
        <div className="mt-5 space-y-5">
          <ForecastAccuracyMetrics metrics={response.metrics} />
          <ForecastAccuracyErrorBoundary
            onRenderFailure={(renderError) => {
              void reportRenderEvent({ renderStatus: 'render_failed', failureReason: renderError.message });
            }}
            fallback={<ForecastAccuracyError message="The comparison view could not be rendered." />}
          >
            <ForecastAccuracyComparison alignedBuckets={response.alignedBuckets} />
          </ForecastAccuracyErrorBoundary>
        </div>
      ) : null}

      {response?.viewStatus === 'rendered_without_metrics' ? (
        <div className="mt-5 space-y-5">
          <ForecastAccuracyMetricsUnavailable message={response.statusMessage ?? 'Metrics are unavailable.'} />
          <ForecastAccuracyErrorBoundary
            onRenderFailure={(renderError) => {
              void reportRenderEvent({ renderStatus: 'render_failed', failureReason: renderError.message });
            }}
            fallback={<ForecastAccuracyError message="The comparison view could not be rendered." />}
          >
            <ForecastAccuracyComparison alignedBuckets={response.alignedBuckets} />
          </ForecastAccuracyErrorBoundary>
        </div>
      ) : null}

      {response?.viewStatus === 'unavailable' ? (
        <div className="mt-5">
          <ForecastAccuracyUnavailable message={response.statusMessage ?? 'Forecast accuracy is unavailable.'} />
        </div>
      ) : null}

      {response?.viewStatus === 'error' ? (
        <div className="mt-5">
          <ForecastAccuracyError message={response.statusMessage ?? 'Forecast accuracy could not be prepared.'} />
        </div>
      ) : null}
    </main>
  );
}
