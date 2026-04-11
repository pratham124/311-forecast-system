import { useEffect, type ReactNode } from 'react';
import { Alert, AlertDescription, AlertTitle } from '../../components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import type { AlertComponentStatus, AlertDetail, AlertDriver, AlertSummary } from '../../types/alertDetails';
import type { OverallDeliveryStatus } from '../../types/forecastAlerts';
import { ChartErrorBoundary } from '../forecast-visualization/components/ChartErrorBoundary';
import { AlertDistributionChart } from './AlertDistributionChart';

const STATUS_STYLES: Record<OverallDeliveryStatus, { bg: string; text: string; label: string }> = {
  delivered: { bg: 'bg-emerald-50', text: 'text-emerald-700', label: 'Delivered' },
  partial_delivery: { bg: 'bg-amber-50', text: 'text-amber-700', label: 'Partial' },
  retry_pending: { bg: 'bg-sky-50', text: 'text-sky-700', label: 'Retry Pending' },
  manual_review_required: { bg: 'bg-red-50', text: 'text-red-700', label: 'Review Required' },
};

function StatusBadge({ status }: { status: OverallDeliveryStatus }) {
  const state = STATUS_STYLES[status] ?? STATUS_STYLES.delivered;
  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wider ${state.bg} ${state.text}`}>
      {state.label}
    </span>
  );
}

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString([], {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

function sourceBadgeClasses(sourceLabel: AlertSummary['sourceLabel']): string {
  return sourceLabel === 'Surge'
    ? 'border-amber-200 bg-amber-50 text-amber-800'
    : 'border-sky-200 bg-sky-50 text-sky-800';
}

function componentStatusClasses(status: AlertComponentStatus): string {
  if (status === 'failed') return 'bg-red-50 text-red-700';
  if (status === 'unavailable') return 'bg-slate-100 text-slate-600';
  return 'bg-emerald-50 text-emerald-700';
}

function formatWindowLabel(summary: AlertSummary | AlertDetail): string {
  return `${formatDateTime(summary.windowStart)} to ${formatDateTime(summary.windowEnd)}`;
}

function ViewStatusBanner({ detail }: { detail: AlertDetail }) {
  if (detail.viewStatus === 'rendered') {
    return null;
  }
  if (detail.viewStatus === 'partial') {
    return (
      <Alert className="border-amber-200 bg-amber-50/70">
        <AlertTitle>Partial detail available</AlertTitle>
        <AlertDescription>Some alert-detail components are missing, but the rest of the drill-down is still available.</AlertDescription>
      </Alert>
    );
  }
  if (detail.viewStatus === 'unavailable') {
    return (
      <Alert>
        <AlertTitle>Detail unavailable</AlertTitle>
        <AlertDescription>{detail.failureReason ?? 'No drill-down context is available for this alert yet.'}</AlertDescription>
      </Alert>
    );
  }
  return (
    <Alert variant="destructive">
      <AlertTitle>Detail preparation failed</AlertTitle>
      <AlertDescription>{detail.failureReason ?? "We couldn't prepare this alert detail."}</AlertDescription>
    </Alert>
  );
}

function ComponentCard({
  title,
  status,
  children,
  emptyMessage,
}: {
  title: string;
  status: AlertComponentStatus;
  children: ReactNode;
  emptyMessage?: string | null;
}) {
  return (
    <section className="grid gap-4 rounded-[24px] border border-[rgba(25,58,90,0.10)] bg-white/80 p-5">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-lg font-semibold text-ink">{title}</h3>
        <span className={`inline-flex rounded-full px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em] ${componentStatusClasses(status)}`}>
          {status.replace('_', ' ')}
        </span>
      </div>
      {status === 'available' ? children : <p className="text-sm text-muted">{emptyMessage}</p>}
    </section>
  );
}

function DriverList({ drivers }: { drivers: AlertDriver[] }) {
  const maxMagnitude = Math.max(...drivers.map((driver) => Math.abs(driver.contribution)), 1);
  return (
    <div className="grid gap-3">
      {drivers.map((driver) => (
        <div key={driver.label} className="grid gap-1.5">
          <div className="flex items-center justify-between gap-3 text-sm">
            <span className="font-medium text-ink">{driver.label}</span>
            <span className={driver.contribution >= 0 ? 'text-emerald-700' : 'text-red-700'}>
              {driver.contribution >= 0 ? '+' : ''}
              {driver.contribution.toFixed(2)}
            </span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-slate-100">
            <div
              className={driver.contribution >= 0 ? 'h-full rounded-full bg-emerald-500' : 'h-full rounded-full bg-red-500'}
              style={{ width: `${Math.max((Math.abs(driver.contribution) / maxMagnitude) * 100, 8)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function RenderReporter({
  alertDetailLoadId,
  onRenderSuccess,
}: {
  alertDetailLoadId: string;
  onRenderSuccess: (alertDetailLoadId: string) => void;
}) {
  useEffect(() => {
    onRenderSuccess(alertDetailLoadId);
  }, [alertDetailLoadId, onRenderSuccess]);
  return null;
}

function AlertDetailPanelContent({
  detail,
  onRenderSuccess,
}: {
  detail: AlertDetail;
  onRenderSuccess: (alertDetailLoadId: string) => void;
}) {
  return (
    <>
      <RenderReporter alertDetailLoadId={detail.alertDetailLoadId} onRenderSuccess={onRenderSuccess} />
      <ViewStatusBanner detail={detail} />

      <div className="grid gap-4 xl:grid-cols-[1.3fr_0.7fr]">
        <ComponentCard
          title="Distribution context"
          status={detail.distribution.status}
          emptyMessage={detail.distribution.failureReason ?? detail.distribution.unavailableReason}
        >
          <AlertDistributionChart points={detail.distribution.points} />
        </ComponentCard>

        <ComponentCard
          title="Driver attribution"
          status={detail.drivers.status}
          emptyMessage={detail.drivers.failureReason ?? detail.drivers.unavailableReason}
        >
          <DriverList drivers={detail.drivers.drivers} />
        </ComponentCard>
      </div>

      <ComponentCard
        title="Anomaly context"
        status={detail.anomalies.status}
        emptyMessage={detail.anomalies.failureReason ?? detail.anomalies.unavailableReason}
      >
        <div className="grid gap-3">
          {detail.anomalies.items.map((item) => (
            <div
              key={item.surgeCandidateId}
              className={`grid gap-2 rounded-[22px] border px-4 py-4 text-sm ${
                item.isSelectedAlert
                  ? 'border-amber-200 bg-amber-50/70'
                  : 'border-slate-200 bg-slate-50/80'
              }`}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="space-y-1">
                  <p className="font-semibold text-ink">{formatDateTime(item.evaluationWindowStart)}</p>
                  <p className="text-xs text-muted">{item.confirmationOutcome ? item.confirmationOutcome.replaceAll('_', ' ') : item.candidateStatus.replaceAll('_', ' ')}</p>
                </div>
                {item.isSelectedAlert ? (
                  <span className="inline-flex rounded-full bg-amber-100 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em] text-amber-800">
                    Selected surge
                  </span>
                ) : null}
              </div>
              <div className="flex flex-wrap gap-3 text-xs text-muted">
                <span>Actual <span className="font-semibold text-ink">{item.actualDemandValue}</span></span>
                <span>Forecast P50 <span className="font-semibold text-ink">{item.forecastP50Value ?? 'n/a'}</span></span>
                <span>z-score <span className="font-semibold text-ink">{item.residualZScore ?? 'n/a'}</span></span>
              </div>
            </div>
          ))}
        </div>
      </ComponentCard>
    </>
  );
}

export function AlertDetailPanel({
  selectedAlert,
  detail,
  isLoading,
  error,
  onRenderSuccess,
  onRenderFailure,
}: {
  selectedAlert: AlertSummary | null;
  detail: AlertDetail | null;
  isLoading: boolean;
  error: string | null;
  onRenderSuccess: (alertDetailLoadId: string) => void;
  onRenderFailure: (reason: string) => void;
}) {
  const detailForHeader = detail ?? selectedAlert;
  const detailScope = detail?.scope;

  return (
    <Card className="overflow-hidden rounded-[28px] border-white/60 bg-white/85 shadow-[0_20px_60px_rgba(15,23,42,0.08)]">
      <div
        className="h-1.5"
        style={{
          background: detailForHeader?.alertSource === 'surge_alert'
            ? 'linear-gradient(90deg, #f59e0b, #f97316, #ef4444)'
            : 'linear-gradient(90deg, #005087, #0081BC, #38bdf8)',
        }}
      />
      <CardHeader>
        <p className="m-0 text-[11px] font-semibold uppercase tracking-[0.22em] text-accent/80">Alert Inspector</p>
        <CardTitle className="text-2xl text-ink">Alert Detail</CardTitle>
        <CardDescription>Drill into the forecast distribution, top model drivers, and recent anomaly context.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-5">
        {!selectedAlert ? (
          <div className="flex flex-col items-center gap-3 py-10 text-center">
            <span className="text-5xl opacity-20">📋</span>
            <p className="text-sm font-medium text-muted">Select an alert from the list to inspect its drill-down context.</p>
          </div>
        ) : (
          <>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-lg font-bold text-ink">{selectedAlert.serviceCategory}</p>
                  <span className={`inline-flex rounded-full border px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em] ${sourceBadgeClasses(selectedAlert.sourceLabel)}`}>
                    {selectedAlert.sourceLabel}
                  </span>
                </div>
                <p className="text-xs text-muted">{formatWindowLabel(selectedAlert)}</p>
                {detailScope?.geographyValue ? (
                  <p className="text-xs text-muted">
                    {detailScope.geographyType ?? 'Geography'}: {detailScope.geographyValue}
                  </p>
                ) : null}
              </div>
              <StatusBadge status={(detail ?? selectedAlert).overallDeliveryStatus} />
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl bg-slate-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-wider text-muted/70">{(detail ?? selectedAlert).primaryMetricLabel}</p>
                <p className="mt-1 text-xl font-bold text-ink">{(detail ?? selectedAlert).primaryMetricValue}</p>
              </div>
              <div className="rounded-xl bg-slate-50 px-4 py-3">
                <p className="text-[11px] font-bold uppercase tracking-wider text-muted/70">{(detail ?? selectedAlert).secondaryMetricLabel}</p>
                <p className="mt-1 text-xl font-bold text-ink">{(detail ?? selectedAlert).secondaryMetricValue}</p>
              </div>
            </div>

            {isLoading ? (
              <Alert>
                <AlertDescription>Loading alert detail while keeping the selected alert context visible.</AlertDescription>
              </Alert>
            ) : null}

            {error ? (
              <Alert variant="destructive">
                <AlertTitle>Unable to load alert detail</AlertTitle>
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            ) : null}

            {detail ? (
              <ChartErrorBoundary
                onError={(chartError) => onRenderFailure(chartError.message)}
                fallback={
                  <Alert variant="destructive">
                    <AlertTitle>We couldn't display this alert detail</AlertTitle>
                    <AlertDescription>The render failure has been recorded. Please refresh the page and try again.</AlertDescription>
                  </Alert>
                }
              >
                <AlertDetailPanelContent detail={detail} onRenderSuccess={onRenderSuccess} />
              </ChartErrorBoundary>
            ) : null}
          </>
        )}
      </CardContent>
    </Card>
  );
}
