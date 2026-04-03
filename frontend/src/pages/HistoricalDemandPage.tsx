import { useEffect } from 'react';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { HistoricalDemandFilters } from '../features/historical-demand/components/HistoricalDemandFilters';
import { HistoricalDemandResults } from '../features/historical-demand/components/HistoricalDemandResults';
import { HistoricalDemandStatus } from '../features/historical-demand/components/HistoricalDemandStatus';
import { useHistoricalDemand } from '../features/historical-demand/hooks/useHistoricalDemand';

export function toApiDateTime(value: string, boundary: 'start' | 'end' = 'start'): string {
  if (!value) {
    return value;
  }
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return boundary === 'end' ? `${value}T23:59:59Z` : `${value}T00:00:00Z`;
  }
  if (value.endsWith('Z') || /[+-]\d{2}:\d{2}$/.test(value)) {
    return value;
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toISOString();
}

export function HistoricalDemandPage() {
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
  } = useHistoricalDemand();

  useEffect(() => {
    if (!response || response.outcomeStatus !== 'success') return;
    void reportRenderEvent({ renderStatus: 'rendered' });
  }, [reportRenderEvent, response]);

  const normalizedFilters = {
    ...filters,
    timeRangeStart: toApiDateTime(filters.timeRangeStart, 'start'),
    timeRangeEnd: toApiDateTime(filters.timeRangeEnd, 'end'),
  };

  return (
    <main className="mx-auto w-full max-w-6xl px-4 pb-14 pt-7 sm:px-6 lg:px-8" aria-label="historical demand page">
      <Card className="relative z-20 grid gap-6 rounded-[28px] p-1 md:grid-cols-[1.45fr_1fr]">
        <CardHeader className="pb-6">
          <p className="mb-3 mt-0 text-xs uppercase tracking-[0.18em] text-accent">Historical Demand</p>
          <CardTitle className="m-0 text-4xl leading-[0.95] text-ink md:text-6xl">
            Explore how 311 demand has shifted across time and geography.
          </CardTitle>
          <CardDescription className="mt-4 max-w-2xl text-base leading-7 text-muted">
            Filter historical records by service category and time range to review how demand has changed over time.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid content-start gap-4 p-7 pl-6 pt-7">
          {isLoadingContext ? (
            <Alert><AlertDescription>Loading available historical filters...</AlertDescription></Alert>
          ) : (
            <HistoricalDemandFilters
              context={context}
              filters={filters}
              onChange={setFilters}
              onSubmit={() => {
                void submit(normalizedFilters);
              }}
              disabled={isSubmitting}
            />
          )}
        </CardContent>
      </Card>

      <div className="mt-5">
        <HistoricalDemandStatus
          isLoading={isSubmitting}
          error={error}
          response={response}
          onProceed={() => {
            void submit(normalizedFilters, true);
          }}
          onDecline={() => {
            clearResponse();
          }}
        />
      </div>

      {response?.outcomeStatus === 'success' ? <div className="mt-5"><HistoricalDemandResults response={response} /></div> : null}
    </main>
  );
}
