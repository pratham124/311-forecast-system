import { useEffect } from 'react';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { ComparisonFilters } from '../features/demand-comparisons/components/ComparisonFilters';
import { ComparisonOutcomeState } from '../features/demand-comparisons/components/ComparisonOutcomeState';
import { ComparisonResultView } from '../features/demand-comparisons/components/ComparisonResultView';
import { useDemandComparisons } from '../features/demand-comparisons/hooks/useDemandComparisons';

export function DemandComparisonPage() {
  const {
    context,
    filters,
    setFilters,
    response,
    isLoadingContext,
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
      <Card className="relative z-20 grid gap-6 rounded-[28px] p-1 md:grid-cols-[1.45fr_1fr]">
        <CardHeader className="pb-6">
          <p className="mb-3 mt-0 text-xs uppercase tracking-[0.18em] text-accent">Demand Comparisons</p>
          <CardTitle className="m-0 text-4xl leading-[0.95] text-ink md:text-6xl">
            Compare approved history with the active forecast scope.
          </CardTitle>
          <CardDescription className="mt-4 max-w-2xl text-base leading-7 text-muted">
            Select one or more categories, optionally narrow to geographies, and compare one continuous time range using the active forecast lineage chosen by the backend.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid content-start gap-4 p-7 pl-6 pt-7">
          {isLoadingContext ? (
            <Alert><AlertDescription>Loading comparison filters...</AlertDescription></Alert>
          ) : (
            <ComparisonFilters
              context={context}
              filters={filters}
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

      {response && response.outcomeStatus !== 'warning_required' && response.outcomeStatus !== 'historical_retrieval_failed' && response.outcomeStatus !== 'forecast_retrieval_failed' && response.outcomeStatus !== 'alignment_failed' ? (
        <div className="mt-5">
          <ComparisonResultView response={response} />
        </div>
      ) : null}
    </main>
  );
}
