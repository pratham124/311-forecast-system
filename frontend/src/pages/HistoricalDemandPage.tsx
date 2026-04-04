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
      <Card className="relative z-20 grid gap-4 rounded-[28px] border-white/60 bg-white/85 p-2 shadow-[0_20px_60px_rgba(15,23,42,0.08)] md:grid-cols-[1.45fr_1fr] md:gap-6">
        <CardHeader className="gap-3 px-5 pb-5 pt-5 sm:px-6 sm:pt-6">
          <p className="m-0 text-[11px] font-semibold uppercase tracking-[0.22em] text-accent/80">Historical Demand</p>
          <CardTitle className="m-0 max-w-3xl text-3xl leading-tight text-ink sm:text-4xl md:text-5xl md:leading-[1.02]">
            Explore how 311 demand changes over time
          </CardTitle>
          <CardDescription className="max-w-2xl text-sm leading-6 text-muted sm:text-[15px]">
            Review historical demand by service category and time range.
          </CardDescription>
          <p className="max-w-2xl text-sm leading-6 text-muted">
            Use the filters to see how request volume has shifted over time before comparing it with forecast output.
          </p>
        </CardHeader>
        <CardContent className="grid content-start gap-5 rounded-[24px] bg-slate-50/80 p-5 sm:p-6">
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
