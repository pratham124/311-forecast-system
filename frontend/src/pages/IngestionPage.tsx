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

  const handleTrigger = async () => {
    setIsTriggering(true);
    setError(null);
    try {
      const accepted = await triggerIngestionRun();
      let latestStatus: IngestionRunStatus | null = null;
      for (let attempt = 0; attempt < 20; attempt += 1) {
        latestStatus = await fetchIngestionRunStatus(accepted.runId);
        setRunStatus(latestStatus);
        if (latestStatus.status !== 'running') {
          break;
        }
        await wait(1000);
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
      <Card className="relative z-20 grid gap-6 rounded-[28px] p-1 md:grid-cols-[1.35fr_0.95fr]">
        <CardHeader className="pb-6">
          <p className="mb-3 mt-0 text-xs uppercase tracking-[0.18em] text-accent">311 Ingestion</p>
          <CardTitle className="m-0 text-4xl leading-[0.95] text-ink md:text-6xl">
            Refresh the approved Edmonton 311 source snapshot.
          </CardTitle>
          <CardDescription className="mt-4 max-w-2xl text-base leading-7 text-muted">
            Trigger a fresh pull from the Edmonton 311 source, then monitor the run outcome and the currently approved dataset version from one place.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid content-start gap-4 p-7 pl-6 pt-7">
          <div className="flex flex-wrap items-center gap-3 pt-2">
            <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-slate-600">
              Current dataset visibility
            </span>
            {triggerable ? (
              <button
                type="button"
                onClick={() => {
                  void handleTrigger();
                }}
                disabled={isTriggering}
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
          <CardHeader>
            <CardTitle className="text-lg text-ink">Latest run status</CardTitle>
            <CardDescription>{describeRunStatus(runStatus)}</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-4">
            <div>
              <span className="block text-xs uppercase tracking-[0.16em] text-muted">Run id</span>
              <strong className="mt-2 block break-all text-sm text-ink">{runStatus.runId}</strong>
            </div>
            <div>
              <span className="block text-xs uppercase tracking-[0.16em] text-muted">Status</span>
              <strong className="mt-2 block text-sm capitalize text-ink">{runStatus.status}</strong>
            </div>
            <div>
              <span className="block text-xs uppercase tracking-[0.16em] text-muted">Result type</span>
              <strong className="mt-2 block text-sm text-ink">{runStatus.resultType ?? 'pending'}</strong>
            </div>
            <div>
              <span className="block text-xs uppercase tracking-[0.16em] text-muted">Records received</span>
              <strong className="mt-2 block text-sm text-ink">{runStatus.recordsReceived ?? 0}</strong>
            </div>
          </CardContent>
        </Card>
      ) : null}

      {dataset ? (
        <section className="mt-5 grid gap-4 md:grid-cols-2">
          <Card className="rounded-[22px]">
            <CardContent className="p-5">
              <span className="block text-sm text-muted">Record count</span>
              <strong className="mt-2 block text-lg text-ink">{dataset.recordCount}</strong>
            </CardContent>
          </Card>
          <Card className="rounded-[22px]">
            <CardContent className="p-5">
              <span className="block text-sm text-muted">Updated</span>
              <strong className="mt-2 block text-lg text-ink">{formatUpdatedDateTime(dataset.updatedAt)}</strong>
            </CardContent>
          </Card>
          <Card className="rounded-[22px] md:col-span-2">
            <CardContent className="p-5">
              <span className="block text-sm text-muted">Latest 311 requested_at in stored data</span>
              <strong className="mt-2 block text-lg text-ink">{formatUpdatedDateTime(dataset.latestRequestedAt)}</strong>
            </CardContent>
          </Card>
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
