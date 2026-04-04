import { useEffect, useState } from 'react';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { ApiError, fetchCurrentDataset, fetchIngestionRunStatus, triggerIngestionRun } from '../api/ingestion';
import type { CurrentDataset, IngestionRunStatus } from '../types/ingestion';

const READER_ROLES = new Set(['CityPlanner', 'OperationalManager']);
const TRIGGER_ROLES = new Set(['OperationalManager']);

export function canReadIngestion(roles: string[]): boolean {
  return roles.some((role) => READER_ROLES.has(role));
}

export function canTriggerIngestion(roles: string[]): boolean {
  return roles.some((role) => TRIGGER_ROLES.has(role));
}

export function formatDateTime(value?: string | null): string {
  if (!value) return 'Not available';
  return new Date(value).toLocaleString();
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

export function describeRunStatus(status: IngestionRunStatus | null): string {
  if (!status) return 'No run started in this session.';
  if (status.status === 'running') return '311 ingestion is running.';
  if (status.status === 'failed') return status.failureReason || '311 ingestion failed.';
  return '311 ingestion completed.';
}

export function formatIngestionResultType(value?: string | null): string {
  if (!value) return 'Pending';
  return value
    .replace(/_/g, ' ')
    .split(' ')
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export async function wait(ms: number): Promise<void> {
  await new Promise((resolve) => window.setTimeout(resolve, ms));
}

type IngestionPageProps = {
  roles: string[];
};

export function IngestionPage({ roles }: IngestionPageProps) {
  const [dataset, setDataset] = useState<CurrentDataset | null>(null);
  const [runStatus, setRunStatus] = useState<IngestionRunStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isTriggering, setIsTriggering] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [storedRunIdChecked, setStoredRunIdChecked] = useState(false);

  const readable = canReadIngestion(roles);
  const triggerable = canTriggerIngestion(roles);

  useEffect(() => {
    if (!readable) return;
    const controller = new AbortController();
    setIsLoading(true);
    setError(null);
    fetchCurrentDataset(controller.signal)
      .then((payload) => {
        setDataset(payload);
      })
      .catch((requestError) => {
        if (controller.signal.aborted) return;
        setError(requestError instanceof Error ? requestError.message : 'Unable to load the current dataset.');
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      });
    return () => controller.abort();
  }, [readable]);

  useEffect(() => {
    const storedRunId = window.localStorage.getItem('ingestion_run_id');
    if (!storedRunId || storedRunIdChecked) {
      setStoredRunIdChecked(true);
      return;
    }
    fetchIngestionRunStatus(storedRunId)
      .then((status) => {
        setRunStatus(status);
        if (status.status !== 'running') {
          window.localStorage.removeItem('ingestion_run_id');
        }
      })
      .catch(() => {
        window.localStorage.removeItem('ingestion_run_id');
      })
      .finally(() => {
        setStoredRunIdChecked(true);
      });
  }, [storedRunIdChecked]);

  const handleTrigger = async () => {
    setIsTriggering(true);
    setError(null);
    try {
      const accepted = await triggerIngestionRun();
      let latestStatus: IngestionRunStatus | null = null;
      window.localStorage.setItem('ingestion_run_id', accepted.runId);
      while (latestStatus === null || latestStatus.status === 'running') {
        latestStatus = await fetchIngestionRunStatus(accepted.runId);
        setRunStatus(latestStatus);
        if (latestStatus.status !== 'running') {
          break;
        }
        await wait(1000);
      }
      if (latestStatus?.status !== 'running') {
        window.localStorage.removeItem('ingestion_run_id');
      }
      const refreshedDataset = await fetchCurrentDataset();
      setDataset(refreshedDataset);
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError(requestError instanceof Error ? requestError.message : 'Unable to trigger 311 ingestion.');
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
          <AlertTitle>311 ingestion access is restricted</AlertTitle>
          <AlertDescription>Your current role does not include access to the 311 ingestion workflow.</AlertDescription>
        </Alert>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-6xl px-4 pb-14 pt-7 sm:px-6 lg:px-8" aria-label="ingestion page">
      <Card className="relative z-20 grid gap-4 rounded-[28px] border-white/60 bg-white/85 p-2 shadow-[0_20px_60px_rgba(15,23,42,0.08)] md:grid-cols-[1.35fr_0.95fr] md:gap-6">
        <CardHeader className="gap-3 px-5 pb-5 pt-5 sm:px-6 sm:pt-6">
          <p className="m-0 text-[11px] font-semibold uppercase tracking-[0.22em] text-accent/80">311 Ingestion</p>
          <CardTitle className="m-0 max-w-3xl text-3xl leading-tight text-ink sm:text-4xl md:text-5xl md:leading-[1.02]">
            Fetch the latest Edmonton 311 data
          </CardTitle>
          <CardDescription className="max-w-2xl text-sm leading-6 text-muted sm:text-[15px]">
            Pull the latest 311 source data and review the approved dataset in one place.
          </CardDescription>
          <p className="max-w-2xl text-sm leading-6 text-muted">
            Use this page to monitor the run outcome, confirm record counts, and see when the approved data was last refreshed.
          </p>
        </CardHeader>
        <CardContent className="grid content-center gap-5 rounded-[24px] bg-slate-50/80 p-5 sm:p-6">
          <div className="space-y-1">
            <p className="text-sm font-semibold text-ink">Run and monitor ingestion</p>
            <p className="text-sm leading-6 text-muted">Trigger a new pull when needed, then watch the current dataset state and run status below.</p>
          </div>
          <div className="flex flex-wrap items-center gap-3 pt-1">
            {triggerable ? (
              <button
                type="button"
                onClick={() => {
                  void handleTrigger();
                }}
                disabled={isTriggering || runStatus?.status === 'running'}
                className="inline-flex min-h-11 items-center justify-center rounded-2xl bg-accent px-5 text-sm font-semibold text-white transition hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isTriggering ? 'Running 311 ingestion...' : 'Trigger 311 ingestion'}
              </button>
            ) : (
              <span className="text-sm text-muted">Only operational managers can trigger a new 311 ingestion run.</span>
            )}
          </div>
        </CardContent>
      </Card>

      {isLoading ? (
        <Alert className="mt-5">
          <AlertDescription>Loading the current dataset...</AlertDescription>
        </Alert>
      ) : null}

      {error ? (
        <Alert variant="destructive" className="mt-5">
          <AlertTitle>311 ingestion request failed</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      ) : null}

      {runStatus ? (
        <Card className="mt-5 rounded-[22px]" tone={runStatus.status === 'failed' ? 'danger' : 'accent'}>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg text-ink">Latest run status</CardTitle>
            <CardDescription>{describeRunStatus(runStatus)}</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4">
            <div className="flex flex-wrap items-center gap-3">
              <span
                className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] ${
                  runStatus.status === 'failed'
                    ? 'border-red-200 bg-red-50 text-red-800'
                    : runStatus.status === 'running'
                      ? 'border-amber-200 bg-amber-50 text-amber-800'
                      : 'border-emerald-200 bg-emerald-50 text-emerald-800'
                }`}
              >
                {runStatus.status}
              </span>
              <p className="m-0 text-sm leading-6 text-muted">Ingestion status updated.</p>
            </div>
            <div className="grid gap-3 md:grid-cols-3">
              <div className="rounded-[18px] border border-slate-200 bg-white/80 p-4">
                <span className="block text-xs font-semibold uppercase tracking-[0.16em] text-muted">Run status</span>
                <strong className="mt-2 block text-base capitalize text-ink">{runStatus.status}</strong>
              </div>
              <div className="rounded-[18px] border border-slate-200 bg-white/80 p-4">
                <span className="block text-xs font-semibold uppercase tracking-[0.16em] text-muted">Result</span>
                <strong className="mt-2 block text-base text-ink">{formatIngestionResultType(runStatus.resultType)}</strong>
              </div>
              <div className="rounded-[18px] border border-slate-200 bg-white/80 p-4">
                <span className="block text-xs font-semibold uppercase tracking-[0.16em] text-muted">Records received</span>
                <strong className="mt-2 block text-base text-ink">{runStatus.recordsReceived ?? 0}</strong>
              </div>
            </div>
          </CardContent>
        </Card>
      ) : null}

      {dataset ? (
        <section className="mt-5 grid gap-4">
          <Card className="rounded-[22px]">
            <CardContent className="p-5">
              <p className="m-0 text-sm font-semibold text-ink">Approved dataset snapshot</p>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">
                This is the current approved 311 source snapshot available to the rest of the app.
              </p>
            </CardContent>
          </Card>
          <div className="grid gap-4 md:grid-cols-3">
            <Card className="rounded-[22px]">
              <CardContent className="p-5">
                <span className="block text-xs font-semibold uppercase tracking-[0.16em] text-muted">Record count</span>
                <strong className="mt-2 block text-2xl text-ink">{dataset.recordCount}</strong>
              </CardContent>
            </Card>
            <Card className="rounded-[22px]">
              <CardContent className="p-5">
                <span className="block text-xs font-semibold uppercase tracking-[0.16em] text-muted">Last updated</span>
                <strong className="mt-2 block text-lg text-ink">{formatUpdatedDateTime(dataset.updatedAt)}</strong>
              </CardContent>
            </Card>
            <Card className="rounded-[22px]">
              <CardContent className="p-5">
                <span className="block text-xs font-semibold uppercase tracking-[0.16em] text-muted">Latest source activity</span>
                <strong className="mt-2 block text-lg text-ink">{formatUpdatedDateTime(dataset.latestRequestedAt)}</strong>
              </CardContent>
            </Card>
          </div>
        </section>
      ) : !isLoading && !error ? (
        <Alert className="mt-5">
          <AlertTitle>No current dataset yet</AlertTitle>
          <AlertDescription>
            There is no approved current 311 dataset yet. {triggerable ? 'Trigger ingestion to populate it.' : 'An operational manager must trigger the first ingestion run.'}
          </AlertDescription>
        </Alert>
      ) : null}
    </main>
  );
}
