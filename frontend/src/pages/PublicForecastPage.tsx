import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Alert, AlertDescription } from '../components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { ChartErrorBoundary } from '../features/forecast-visualization/components/ChartErrorBoundary';
import { PublicForecastCoverageNotice } from '../features/public-forecast/components/PublicForecastCoverageNotice';
import { PublicForecastErrorState } from '../features/public-forecast/components/PublicForecastErrorState';
import { PublicForecastLoadingState } from '../features/public-forecast/components/PublicForecastLoadingState';
import { PublicForecastView } from '../features/public-forecast/components/PublicForecastView';
import { usePublicForecast } from '../features/public-forecast/hooks/usePublicForecast';

export function PublicForecastPage() {
  const { forecastProduct, setForecastProduct, forecast, isLoading, error, reportDisplayEvent } = usePublicForecast();
  const [sortOrder, setSortOrder] = useState<'desc' | 'asc'>('desc');

  useEffect(() => {
    if (!forecast) return;
    if (forecast.status !== 'available') return;
    void reportDisplayEvent({ displayOutcome: 'rendered' });
  }, [forecast, reportDisplayEvent]);

  const handleRenderFailure = (renderError: Error) => {
    if (!forecast) return;
    void reportDisplayEvent({ displayOutcome: 'render_failed', failureReason: renderError.message });
  };

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.97),_rgba(240,246,252,0.94)_36%,_rgba(210,225,236,0.9)_100%)] px-4 py-10 sm:px-6 lg:px-8">
      <div className="mx-auto w-full max-w-6xl">
        <header className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-[28px] border border-white/70 bg-white/72 px-5 py-4 shadow-[0_18px_50px_rgba(15,23,42,0.08)] backdrop-blur">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-accent">311 Forecast System</p>
            <p className="mt-1 text-sm text-muted">Public demand outlook</p>
          </div>
          <nav className="flex flex-wrap items-center gap-2" aria-label="public navigation">
            <Link
              to="/"
              className="inline-flex min-h-10 items-center justify-center rounded-2xl border border-slate-300 bg-white px-4 text-sm font-semibold text-ink transition hover:border-accent hover:text-accent"
            >
              Back
            </Link>
            <Link
              to="/feedback"
              className="inline-flex min-h-10 items-center justify-center rounded-2xl border border-slate-300 bg-white px-4 text-sm font-semibold text-ink transition hover:border-accent hover:text-accent"
            >
              Report an issue
            </Link>
          </nav>
        </header>
        <Card className="rounded-[32px] border-white/70 bg-white/88 shadow-[0_24px_80px_rgba(15,23,42,0.10)] backdrop-blur">
          <CardHeader className="gap-4 pb-4">
            <p className="text-xs uppercase tracking-[0.24em] text-accent">Public 311 forecast</p>
            <CardTitle className="max-w-4xl text-4xl leading-tight text-ink sm:text-5xl">
              Expected 311 demand by service category
            </CardTitle>
            <CardDescription className="max-w-3xl text-base leading-7 text-muted">
              This page only shows public-safe category summaries.
            </CardDescription>
          </CardHeader>
          <CardContent className="pb-6">
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => setForecastProduct('daily')}
                className={`inline-flex min-h-10 items-center justify-center rounded-2xl px-4 text-sm font-semibold transition ${forecastProduct === 'daily' ? 'bg-ink text-white' : 'border border-slate-300 bg-white text-ink hover:border-accent hover:text-accent'}`}
              >
                Daily
              </button>
              <button
                type="button"
                onClick={() => setForecastProduct('weekly')}
                className={`inline-flex min-h-10 items-center justify-center rounded-2xl px-4 text-sm font-semibold transition ${forecastProduct === 'weekly' ? 'bg-ink text-white' : 'border border-slate-300 bg-white text-ink hover:border-accent hover:text-accent'}`}
              >
                Weekly
              </button>
              <button
                type="button"
                onClick={() => setSortOrder('desc')}
                className={`inline-flex min-h-10 items-center justify-center rounded-2xl px-4 text-sm font-semibold transition ${sortOrder === 'desc' ? 'bg-accent text-white' : 'border border-slate-300 bg-white text-ink hover:border-accent hover:text-accent'}`}
              >
                Highest demand
              </button>
              <button
                type="button"
                onClick={() => setSortOrder('asc')}
                className={`inline-flex min-h-10 items-center justify-center rounded-2xl px-4 text-sm font-semibold transition ${sortOrder === 'asc' ? 'bg-accent text-white' : 'border border-slate-300 bg-white text-ink hover:border-accent hover:text-accent'}`}
              >
                Lowest demand
              </button>
            </div>
            {isLoading ? <PublicForecastLoadingState /> : null}
            {error ? (
              <Alert variant="destructive" className="mt-6 rounded-[24px]">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            ) : null}

            {forecast?.status === 'unavailable' ? (
              <PublicForecastErrorState
                title="Public forecast unavailable"
                message={forecast.statusMessage ?? "We can't show the public forecast right now."}
              />
            ) : null}

            {forecast?.status === 'error' ? (
              <PublicForecastErrorState
                title="Public forecast error"
                message={forecast.statusMessage ?? 'The public forecast could not be prepared.'}
              />
            ) : null}

            {forecast?.status === 'available' ? (
              <ChartErrorBoundary
                onError={handleRenderFailure}
                fallback={
                  <PublicForecastErrorState
                    title="We couldn't display the public forecast"
                    message="Please refresh the page and try again. We've recorded the problem."
                  />
                }
              >
                <PublicForecastCoverageNotice
                  coverageMessage={forecast.coverageMessage}
                  sanitizationSummary={forecast.sanitizationSummary}
                />
                <PublicForecastView forecast={forecast} sortOrder={sortOrder} />
              </ChartErrorBoundary>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}
