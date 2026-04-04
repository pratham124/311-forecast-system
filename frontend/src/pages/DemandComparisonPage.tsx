import { useEffect } from 'react';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { ComparisonFilters } from '../features/demand-comparisons/components/ComparisonFilters';
import { ComparisonOutcomeState } from '../features/demand-comparisons/components/ComparisonOutcomeState';
import { ComparisonResultView } from '../features/demand-comparisons/components/ComparisonResultView';
import { useDemandComparisons } from '../features/demand-comparisons/hooks/useDemandComparisons';

export function DemandComparisonPage() {
  const {
    availability,
    filters,
    setFilters,
    dateWindowStart,
    dateWindowEnd,
    dateRangeError,
    response,
    isLoadingAvailability,
    isSubmitting,
    error,
    submit,
    reportRenderEvent,
    clearResponse,
  } = useDemandComparisons();

  useEffect(() => {
    if (!response) {
      return;
    }
    if (response.outcomeStatus === 'success' || response.outcomeStatus === 'historical_only' || response.outcomeStatus === 'forecast_only' || response.outcomeStatus === 'partial_forecast_missing') {
      void reportRenderEvent({ renderStatus: 'rendered' });
    }
  }, [reportRenderEvent, response]);

  return (
    <main className="mx-auto w-full max-w-6xl px-4 pb-14 pt-7 sm:px-6 lg:px-8" aria-label="demand comparison page">
      <Card className="relative z-20 grid gap-4 rounded-[28px] border-white/60 bg-white/85 p-2 shadow-[0_20px_60px_rgba(15,23,42,0.08)] md:grid-cols-[1.45fr_1fr] md:gap-6">
        <CardHeader className="gap-3 px-5 pb-5 pt-5 sm:px-6 sm:pt-6">
          <p className="m-0 text-[11px] font-semibold uppercase tracking-[0.22em] text-accent/80">Demand Comparisons</p>
          <CardTitle className="m-0 max-w-3xl text-3xl leading-tight text-ink sm:text-4xl md:text-5xl md:leading-[1.02]">
            Explore approved history beside the active forecast
          </CardTitle>
          <CardDescription className="max-w-2xl text-sm leading-6 text-muted sm:text-[15px]">
            See how approved demand and the latest forecast line up for the same time window.
          </CardDescription>
          <p className="max-w-2xl text-sm leading-6 text-muted">
            Choose one or more categories, then set a continuous date range to review the active forecast lineage.
          </p>
        </CardHeader>
        <CardContent className="grid content-start gap-5 rounded-[24px] bg-slate-50/80 p-5 sm:p-6">
          {isLoadingAvailability ? (
            <Alert><AlertDescription>Loading comparison filters...</AlertDescription></Alert>
          ) : (
            <ComparisonFilters
              availability={availability}
              filters={filters}
              dateWindowStart={dateWindowStart}
              dateWindowEnd={dateWindowEnd}
              dateRangeError={dateRangeError}
              onChange={setFilters}
              onSubmit={() => {
                void submit();
              }}
              disabled={isSubmitting}
            />
          )}
        </CardContent>
      </Card>

      <div className="mt-5">
        <ComparisonOutcomeState
          error={error}
          isLoading={isSubmitting}
          response={response}
          onProceed={() => {
            void submit(undefined, true);
          }}
          onDecline={clearResponse}
        />
      </div>

      {response && ['success', 'partial_forecast_missing', 'historical_only', 'forecast_only'].includes(response.outcomeStatus) ? (
        <div className="mt-5">
          <ComparisonResultView response={response} />
        </div>
      ) : null}
    </main>
  );
}
