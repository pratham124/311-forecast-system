import { useEffect, useRef, useState } from 'react';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Label } from '../components/ui/label';
import { TimeRangeSelect } from '../features/forecast-visualization/components/TimeRangeSelect';
import { ApiError, fetchCurrentEvaluation, fetchEvaluationRunStatus, triggerEvaluationRun } from '../api/evaluations';
import type { CurrentEvaluation, EvaluationRunStatus, ForecastProduct } from '../types/evaluation';

const FORECAST_PRODUCT_LABELS: Record<ForecastProduct, string> = {
  daily_1_day: 'Daily',
  weekly_7_day: 'Weekly',
};

const READER_ROLES = new Set(['CityPlanner', 'OperationalManager']);
const TRIGGER_ROLES = new Set(['OperationalManager']);

export function formatDateTime(value?: string | null): string {
  if (!value) return 'Not available';
  return new Date(value).toLocaleString([], {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: 'numeric',
  });
}

export function formatUpdatedDateTime(value?: string | null): string {
  if (!value) return 'Not available';
  return new Date(value).toLocaleString([], {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: 'numeric',
  });
}

function formatSegmentKey(segmentType: CurrentEvaluation['segments'][number]['segmentType'], segmentKey: string): string {
  if (segmentType !== 'time_period') return segmentKey;
  const date = new Date(segmentKey);
  if (Number.isNaN(date.getTime())) return segmentKey;
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, '0');
  const day = String(date.getUTCDate()).padStart(2, '0');
  const hour24 = date.getUTCHours();
  const meridiem = hour24 >= 12 ? 'PM' : 'AM';
  const hour12 = hour24 % 12 === 0 ? 12 : hour24 % 12;
  return `${year}-${month}-${day} ${hour12} ${meridiem}`;
}

function formatDisplayLabel(value: string): string {
  return value
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

export function canReadEvaluation(roles: string[]): boolean {
  return roles.some((role) => READER_ROLES.has(role));
}

export function canTriggerEvaluation(roles: string[]): boolean {
  return roles.some((role) => TRIGGER_ROLES.has(role));
}

export function describeRunStatus(status: EvaluationRunStatus | null): string {
  if (!status) return 'No run started in this session.';
  if (status.status === 'running') return 'Evaluation is running.';
  if (status.status === 'failed') return status.failureReason || status.summary || 'Evaluation failed.';
  return status.summary || 'Evaluation completed.';
}

type ParsedRunSummary = {
  headline: string;
  excludedCategories: string[];
};

function parseRunSummary(summary?: string | null): ParsedRunSummary | null {
  if (!summary) return null;
  const marker = 'excluded categories without baseline history:';
  const markerIndex = summary.toLowerCase().indexOf(marker);

  if (markerIndex === -1) {
    return {
      headline: summary,
      excludedCategories: [],
    };
  }

  const headline = summary.slice(0, markerIndex).trim().replace(/;\s*$/, '');
  const categoryText = summary.slice(markerIndex + marker.length).trim();
  const excludedCategories = categoryText
    .split(',')
    .map((category) => category.trim())
    .filter(Boolean);

  return {
    headline: headline || 'Evaluation summary',
    excludedCategories,
  };
}

export async function wait(ms: number): Promise<void> {
  await new Promise((resolve) => window.setTimeout(resolve, ms));
}

type EvaluationPageProps = {
  roles: string[];
};

export function EvaluationPage({ roles }: EvaluationPageProps) {
  const [forecastProduct, setForecastProduct] = useState<ForecastProduct>('daily_1_day');
  const [isProductPickerOpen, setIsProductPickerOpen] = useState(false);
  const productPickerRef = useRef<HTMLDivElement>(null);
  const [evaluation, setEvaluation] = useState<CurrentEvaluation | null>(null);
  const [runStatus, setRunStatus] = useState<EvaluationRunStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isTriggering, setIsTriggering] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const readable = canReadEvaluation(roles);
  const triggerable = canTriggerEvaluation(roles);
  const runStatusTone =
    runStatus?.status === 'failed'
      ? 'border-red-200 bg-red-50 text-red-800'
      : runStatus?.status === 'running'
        ? 'border-amber-200 bg-amber-50 text-amber-800'
        : 'border-emerald-200 bg-emerald-50 text-emerald-800';
  const runResultLabel = runStatus?.resultType ? runStatus.resultType.replace(/_/g, ' ') : 'pending';
  const parsedRunSummary = parseRunSummary(runStatus?.summary);

  useEffect(() => {
    if (!isProductPickerOpen) return;

    const handlePointerDown = (event: MouseEvent) => {
      const target = event.target;
      if (!(target instanceof Node)) return;
      if (productPickerRef.current?.contains(target)) return;
      setIsProductPickerOpen(false);
    };

    document.addEventListener('mousedown', handlePointerDown);
    return () => document.removeEventListener('mousedown', handlePointerDown);
  }, [isProductPickerOpen]);

  useEffect(() => {
    if (!readable) return;
    const controller = new AbortController();
    setIsLoading(true);
    setError(null);
    fetchCurrentEvaluation(forecastProduct, controller.signal)
      .then((payload) => {
        setEvaluation(payload);
      })
      .catch((requestError) => {
        if (controller.signal.aborted) return;
        setError(requestError instanceof Error ? requestError.message : 'Unable to load the current evaluation.');
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      });
    return () => controller.abort();
  }, [forecastProduct, readable]);

  const handleTrigger = async () => {
    setIsTriggering(true);
    setError(null);
    try {
      const accepted = await triggerEvaluationRun(forecastProduct);
      let latestStatus: EvaluationRunStatus | null = null;
      for (let attempt = 0; attempt < 12; attempt += 1) {
        latestStatus = await fetchEvaluationRunStatus(accepted.evaluationRunId);
        setRunStatus(latestStatus);
        if (latestStatus.status !== 'running') {
          break;
        }
        await wait(1000);
      }
      if (latestStatus && latestStatus.status !== 'running') {
        const refreshedEvaluation = await fetchCurrentEvaluation(forecastProduct);
        setEvaluation(refreshedEvaluation);
      }
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError(requestError instanceof Error ? requestError.message : 'Unable to trigger the evaluation.');
      }
    } finally {
      setIsTriggering(false);
      setIsLoading(false);
    }
  };

  if (!readable) {
    return (
      <main className="mx-auto w-full max-w-6xl px-4 pb-14 pt-7 sm:px-6 lg:px-8">
        <Alert variant="destructive">
          <AlertTitle>Evaluation access is restricted</AlertTitle>
          <AlertDescription>Your current role does not include UC-06 evaluation access.</AlertDescription>
        </Alert>
      </main>
    );
  }

  const overallSegment = evaluation?.segments.find((segment) => segment.segmentType === 'overall') ?? null;

  return (
    <main className="mx-auto w-full max-w-6xl px-4 pb-14 pt-7 sm:px-6 lg:px-8" aria-label="evaluation page">
      <Card className="relative z-20 grid gap-4 rounded-[28px] border-white/60 bg-white/85 p-2 shadow-[0_20px_60px_rgba(15,23,42,0.08)] md:grid-cols-[1.35fr_0.95fr] md:gap-6">
        <CardHeader className="gap-3 px-5 pb-5 pt-5 sm:px-6 sm:pt-6">
          <p className="m-0 text-[11px] font-semibold uppercase tracking-[0.22em] text-accent/80">Forecast Evaluation</p>
          <CardTitle className="m-0 max-w-3xl text-3xl leading-tight text-ink sm:text-4xl md:text-5xl md:leading-[1.02]">
            Review how the forecasting engine performs against its baselines
          </CardTitle>
          <CardDescription className="max-w-2xl text-sm leading-6 text-muted sm:text-[15px]">
            Compare the current official forecast with baseline methods used for internal review.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid content-start gap-5 rounded-[24px] bg-slate-50/80 p-5 sm:p-6">
          <div className="space-y-1">
            <p className="text-sm font-semibold text-ink">Choose the evaluation scope</p>
            <p className="text-sm leading-6 text-muted">Switch between daily and weekly evaluation outputs, then trigger a fresh run if your role allows it.</p>
          </div>
          <div className="grid gap-2.5">
            <Label htmlFor="forecast-product" className="text-sm font-medium text-ink">Time range</Label>
            <TimeRangeSelect
              value={forecastProduct}
              onChange={setForecastProduct}
              isOpen={isProductPickerOpen}
              onOpenChange={setIsProductPickerOpen}
              containerRef={productPickerRef}
            />
          </div>
          <div className="flex flex-wrap items-center gap-3 pt-1">
        {triggerable ? (
          <button
            type="button"
            onClick={() => {
              void handleTrigger();
            }}
            disabled={isTriggering}
            className="inline-flex min-h-11 items-center justify-center rounded-2xl bg-accent px-5 text-sm font-semibold text-white transition hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isTriggering ? 'Running evaluation...' : `Trigger ${forecastProduct === 'daily_1_day' ? 'daily' : 'weekly'} evaluation`}
          </button>
        ) : (
              <span className="text-sm text-muted">Only operational managers can trigger a new evaluation run.</span>
            )}
          </div>
        </CardContent>
      </Card>

      {isLoading ? (
        <Alert className="mt-5">
          <AlertDescription>Loading the current evaluation...</AlertDescription>
        </Alert>
      ) : null}

      {error ? (
        <Alert variant="destructive" className="mt-5">
          <AlertTitle>Evaluation request failed</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {runStatus ? (
        <Card className="mt-5 rounded-[22px]" tone={runStatus.status === 'failed' ? 'danger' : 'accent'}>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg text-ink">Latest run status</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4">
            <div className="flex flex-wrap items-center gap-3">
              <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] ${runStatusTone}`}>
                {runStatus.status}
              </span>
              {runStatus.status === 'failed' ? (
                <p className="m-0 text-sm leading-6 text-muted">
                  {runStatus.failureReason || runStatus.summary || 'Evaluation failed.'}
                </p>
              ) : null}
            </div>
            {parsedRunSummary && parsedRunSummary.excludedCategories.length > 0 ? (
              <div className="rounded-[18px] border border-amber-200 bg-amber-50/80 p-4">
                <span className="block text-xs font-semibold uppercase tracking-[0.16em] text-amber-800">Excluded categories</span>
                <p className="mt-1 text-sm text-amber-900">No baseline history was available for these categories:</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {parsedRunSummary.excludedCategories.map((category) => (
                    <span key={category} className="rounded-full border border-amber-300 bg-white px-3 py-1 text-xs font-medium text-amber-900">
                      {category}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
            <div className="grid gap-3 md:grid-cols-3">
              <div className="rounded-[18px] border border-slate-200 bg-white/80 p-4">
                <span className="block text-xs font-semibold uppercase tracking-[0.16em] text-muted">Run status</span>
                <strong className="mt-2 block text-base capitalize text-ink">{runStatus.status}</strong>
              </div>
              <div className="rounded-[18px] border border-slate-200 bg-white/80 p-4">
                <span className="block text-xs font-semibold uppercase tracking-[0.16em] text-muted">Result</span>
                <strong className="mt-2 block text-base capitalize text-ink">{runResultLabel}</strong>
              </div>
              <div className="rounded-[18px] border border-slate-200 bg-white/80 p-4">
                <span className="block text-xs font-semibold uppercase tracking-[0.16em] text-muted">Completed at</span>
                <strong className="mt-2 block text-base text-ink">{formatDateTime(runStatus.completedAt)}</strong>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : null}

      {evaluation ? (
        <>
          <section className="mt-5 grid gap-4 md:grid-cols-4">
            <Card className="rounded-[22px]">
              <CardContent className="p-5">
                <span className="block text-sm text-muted">Comparison status</span>
                <strong className="mt-2 block text-lg capitalize text-ink">{evaluation.comparisonStatus}</strong>
              </CardContent>
            </Card>
            <Card className="rounded-[22px]">
              <CardContent className="p-5">
                <span className="block text-sm text-muted">Updated</span>
                <strong className="mt-2 block text-lg text-ink">{formatUpdatedDateTime(evaluation.updatedAt)}</strong>
              </CardContent>
            </Card>
            <Card className="rounded-[22px]">
              <CardContent className="p-5">
                <span className="block text-sm text-muted">Baselines</span>
                <strong className="mt-2 block text-lg text-ink">{evaluation.baselineMethods.map(formatDisplayLabel).join(', ')}</strong>
              </CardContent>
            </Card>
            <Card className="rounded-[22px]">
              <CardContent className="p-5">
                <span className="block text-sm text-muted">Segment coverage</span>
                <strong className="mt-2 block text-lg text-ink">{evaluation.fairComparison.segmentCoverage.length}</strong>
              </CardContent>
            </Card>
          </section>

          <Card className="mt-5 rounded-[28px]">
            <CardHeader>
              <CardTitle>Current official evaluation</CardTitle>
              <CardDescription>{evaluation.comparisonSummary ?? evaluation.summary ?? 'No evaluation summary is available.'}</CardDescription>
              <p className="mt-3 text-sm text-muted">
                Fair comparison window: {formatUpdatedDateTime(evaluation.fairComparison.evaluationWindowStart)} to {formatUpdatedDateTime(evaluation.fairComparison.evaluationWindowEnd)}
              </p>
            </CardHeader>
            <CardContent>
              <div className="rounded-[24px] border border-slate-200 bg-white/80 p-4">
                <div className="flex items-center justify-between gap-4 border-b border-slate-200 pb-3">
                  <div>
                    <h2 className="m-0 text-base font-semibold text-ink">Overall metrics</h2>
                    <p className="mt-1 text-sm text-muted">{overallSegment?.comparisonRowCount ?? 0} aligned comparison rows</p>
                  </div>
                  <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-slate-600">
                    {overallSegment?.segmentStatus ?? evaluation.comparisonStatus}
                  </span>
                </div>
                <div className="mt-4 space-y-4">
                  {(overallSegment?.methodMetrics ?? []).map((method) => (
                    <div key={method.methodName} className="rounded-[18px] border border-slate-200 bg-slate-50/80 p-4">
                      <h3 className="m-0 text-sm font-semibold uppercase tracking-[0.14em] text-slate-700">{formatDisplayLabel(method.methodName)}</h3>
                      <div className="mt-3 grid gap-3 sm:grid-cols-3">
                        {method.metrics.map((metric) => (
                          <div key={`${method.methodName}-${metric.metricName}`} className="rounded-2xl bg-white px-3 py-3 shadow-sm">
                            <span className="block text-xs uppercase tracking-[0.12em] text-muted">{metric.metricName}</span>
                            <strong className="mt-2 block text-base text-ink">
                              {metric.isExcluded ? 'Excluded' : metric.metricValue?.toFixed(4) ?? 'Not available'}
                            </strong>
                            {metric.exclusionReason ? <span className="mt-2 block text-xs text-muted">{metric.exclusionReason}</span> : null}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="mt-5 rounded-[28px]">
            <CardHeader>
              <CardTitle>Segment summaries</CardTitle>
              <CardDescription>Review category and time-period slices, especially where exclusions reduced the metric set.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {evaluation.segments.map((segment) => (
                <div key={`${segment.segmentType}-${segment.segmentKey}`} className="rounded-[22px] border border-slate-200 bg-white/80 p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h3 className="m-0 text-sm font-semibold uppercase tracking-[0.14em] text-slate-700">{segment.segmentType.replace('_', ' ')} · {formatSegmentKey(segment.segmentType, segment.segmentKey)}</h3>
                      <p className="mt-1 text-sm text-muted">{segment.comparisonRowCount} rows · {segment.excludedMetricCount} excluded metrics</p>
                    </div>
                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-slate-600">
                      {segment.segmentStatus}
                    </span>
                  </div>
                  {segment.notes ? <p className="mt-3 text-sm text-muted">{segment.notes}</p> : null}
                </div>
              ))}
            </CardContent>
          </Card>
        </>
      ) : !isLoading && !error ? (
        <Alert className="mt-5">
          <AlertTitle>No current evaluation yet</AlertTitle>
          <AlertDescription>
            There is no published evaluation for {FORECAST_PRODUCT_LABELS[forecastProduct]}. {triggerable ? 'Trigger one to populate this review page.' : 'An operational manager must trigger the first run.'}
          </AlertDescription>
        </Alert>
      ) : null}
    </main>
  );
}
