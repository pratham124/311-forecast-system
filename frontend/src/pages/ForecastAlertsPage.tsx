import { useEffect, useState } from 'react';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import {
  ApiError,
  getThresholdAlertEvent,
  listThresholdAlertEvents,
  listThresholdConfigurations,
  updateThresholdConfiguration,
} from '../api/forecastAlerts';
import type { ThresholdAlertEvent, ThresholdAlertEventSummary, ThresholdConfiguration } from '../types/forecastAlerts';

const READER_ROLES = new Set(['CityPlanner', 'OperationalManager']);
const MANAGER_ROLES = new Set(['OperationalManager']);
const DEFAULT_THRESHOLD_VALUE = 100;

function canReadForecastAlerts(roles: string[]): boolean {
  return roles.some((role) => READER_ROLES.has(role));
}

function canManageThresholds(roles: string[]): boolean {
  return roles.some((role) => MANAGER_ROLES.has(role));
}

function formatDate(value: string | null | undefined): string {
  if (!value) return 'Not available';
  return new Date(value).toLocaleString();
}

type ForecastAlertsPageProps = {
  roles: string[];
};

export function ForecastAlertsPage({ roles }: ForecastAlertsPageProps) {
  const [items, setItems] = useState<ThresholdAlertEventSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ThresholdAlertEvent | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSavingThreshold, setIsSavingThreshold] = useState(false);
  const [thresholdSaveMessage, setThresholdSaveMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [thresholdConfig, setThresholdConfig] = useState<ThresholdConfiguration | null>(null);
  const [thresholdValueDraft, setThresholdValueDraft] = useState(DEFAULT_THRESHOLD_VALUE.toFixed(2));

  const readable = canReadForecastAlerts(roles);
  const canManage = canManageThresholds(roles);

  useEffect(() => {
    if (!readable) return;
    const controller = new AbortController();
    setIsLoading(true);
    setError(null);
    listThresholdAlertEvents(controller.signal)
      .then((response) => {
        setItems(response.items);
        if (response.items.length > 0) {
          setSelectedId(response.items[0].notificationEventId);
        }
      })
      .catch((requestError) => {
        if (controller.signal.aborted) return;
        setError(requestError instanceof Error ? requestError.message : 'Unable to load threshold alert events.');
      })
      .finally(() => {
        if (!controller.signal.aborted) setIsLoading(false);
      });
    return () => controller.abort();
  }, [readable]);

  useEffect(() => {
    if (!readable) return;
    const controller = new AbortController();
    listThresholdConfigurations(controller.signal)
      .then((response) => {
        const globalConfig = response.items[0] ?? null;
        setThresholdConfig(globalConfig);
        setThresholdValueDraft((globalConfig?.thresholdValue ?? DEFAULT_THRESHOLD_VALUE).toFixed(2));
      })
      .catch((requestError) => {
        if (controller.signal.aborted) return;
        setError(requestError instanceof Error ? requestError.message : 'Unable to load global threshold configuration.');
      });
    return () => controller.abort();
  }, [readable]);

  useEffect(() => {
    if (!selectedId || !readable) {
      setDetail(null);
      return;
    }
    const controller = new AbortController();
    getThresholdAlertEvent(selectedId, controller.signal)
      .then((payload) => {
        setDetail(payload);
      })
      .catch((requestError) => {
        if (controller.signal.aborted) return;
        setError(requestError instanceof Error ? requestError.message : 'Unable to load selected alert details.');
      });
    return () => controller.abort();
  }, [selectedId, readable]);

  const handleSaveThreshold = async () => {
    const parsed = Number(thresholdValueDraft);
    if (!Number.isFinite(parsed) || parsed <= 0) {
      setError('Threshold value must be greater than zero.');
      return;
    }
    setIsSavingThreshold(true);
    setThresholdSaveMessage(null);
    setError(null);
    try {
      const updated = await updateThresholdConfiguration({ thresholdValue: parsed });
      setThresholdConfig(updated);
      setThresholdValueDraft(updated.thresholdValue.toFixed(2));
      setThresholdSaveMessage('Global threshold updated. New value applies to future evaluations.');
    } catch (requestError) {
      if (requestError instanceof ApiError) {
        setError(requestError.message);
      } else {
        setError(requestError instanceof Error ? requestError.message : 'Unable to update threshold.');
      }
    } finally {
      setIsSavingThreshold(false);
    }
  };

  if (!readable) {
    return (
      <main className="mx-auto w-full max-w-6xl px-4 pb-14 pt-7 sm:px-6 lg:px-8">
        <Alert variant="destructive">
          <AlertTitle>Forecast alert access is restricted</AlertTitle>
          <AlertDescription>Your current role does not include UC-10 alert review access.</AlertDescription>
        </Alert>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-6xl px-4 pb-14 pt-7 sm:px-6 lg:px-8" aria-label="forecast alerts page">
      <Card className="rounded-[28px]">
        <CardHeader>
          <CardTitle>Forecast Alerts</CardTitle>
        </CardHeader>
        <CardContent>
          {canManage ? (
            <div className="mb-4 rounded-lg border border-slate-200 bg-white p-3">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-muted">Global demand threshold</p>
              <p className="mt-1 text-xs text-muted">One threshold value applies to every service category.</p>
              <div className="mt-2 flex max-w-md items-center gap-2">
                <input
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={thresholdValueDraft}
                  onChange={(event) => setThresholdValueDraft(event.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  aria-label="Threshold value"
                />
                <button
                  type="button"
                  onClick={() => {
                    void handleSaveThreshold();
                  }}
                  disabled={isSavingThreshold}
                  className="rounded-lg bg-accent px-3 py-2 text-sm font-semibold text-white disabled:opacity-60"
                >
                  {isSavingThreshold ? 'Saving...' : 'Update threshold'}
                </button>
              </div>
              <p className="mt-2 text-xs text-muted">
                Current global threshold: {(thresholdConfig?.thresholdValue ?? DEFAULT_THRESHOLD_VALUE).toFixed(2)}
              </p>
              {thresholdSaveMessage ? <p className="mt-2 text-xs text-emerald-700">{thresholdSaveMessage}</p> : null}
            </div>
          ) : null}
          {isLoading ? <p className="text-sm text-muted">Loading alert events...</p> : null}
          {error ? (
            <Alert variant="destructive">
              <AlertTitle>Alert request failed</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}
          {!isLoading && items.length === 0 ? <p className="text-sm text-muted">No alert events found.</p> : null}
          <div className="mt-2 grid gap-3 md:grid-cols-2">
            <div className="space-y-2">
              {items.map((item) => (
                <button
                  key={item.notificationEventId}
                  type="button"
                  onClick={() => setSelectedId(item.notificationEventId)}
                  className={`w-full rounded-xl border p-3 text-left ${
                    selectedId === item.notificationEventId ? 'border-accent bg-slate-50' : 'border-slate-200 bg-white'
                  }`}
                >
                  <p className="text-sm font-semibold text-ink">{item.serviceCategory}{item.geographyValue ? ` · ${item.geographyValue}` : ''}</p>
                  <p className="text-xs text-muted">{item.overallDeliveryStatus.replace(/_/g, ' ')} · {formatDate(item.createdAt)}</p>
                </button>
              ))}
            </div>
            <div className="rounded-xl border border-slate-200 p-3">
              {detail ? (
                <>
                  <p className="text-sm font-semibold text-ink">Alert Detail</p>
                  <p className="text-xs text-muted">Notification ID: {detail.notificationEventId}</p>
                  <p className="mt-3 text-sm text-ink">Forecast value: {detail.forecastValue.toFixed(2)}</p>
                  <p className="text-sm text-ink">Threshold value: {detail.thresholdValue.toFixed(2)}</p>
                  <p className="text-sm text-ink">Window: {formatDate(detail.forecastWindowStart)} - {formatDate(detail.forecastWindowEnd)}</p>
                  <p className="text-sm text-ink">Status: {detail.overallDeliveryStatus.replace(/_/g, ' ')}</p>
                  <div className="mt-3 space-y-2">
                    {detail.channelAttempts.map((attempt) => (
                      <div key={`${attempt.channelType}-${attempt.attemptNumber}`} className="rounded-lg border border-slate-100 bg-slate-50 p-2">
                        <p className="text-xs font-medium text-ink">{attempt.channelType} · attempt {attempt.attemptNumber}</p>
                        <p className="text-xs text-muted">{attempt.status}{attempt.failureReason ? ` · ${attempt.failureReason}` : ''}</p>
                      </div>
                    ))}
                  </div>
                </>
              ) : (
                <p className="text-sm text-muted">Select an alert event to view details.</p>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
