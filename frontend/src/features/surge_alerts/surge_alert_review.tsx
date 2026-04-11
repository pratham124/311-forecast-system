import { useEffect, useState } from 'react';
import { fetchSurgeEvaluation, fetchSurgeEvaluations, fetchSurgeEvent, fetchSurgeEvents } from '../../api/surgeAlerts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import type { SurgeAlertEvent, SurgeAlertEventSummary, SurgeEvaluationRunDetail, SurgeEvaluationRunSummary, OverallDeliveryStatus } from '../../types/surgeAlerts';

const READER_ROLES = new Set(['CityPlanner', 'OperationalManager']);

const STATUS_LABELS: Record<OverallDeliveryStatus, string> = {
  delivered: 'Delivered',
  partial_delivery: 'Partial delivery',
  retry_pending: 'Retry pending',
  manual_review_required: 'Manual review required',
};

function canReadAlerts(roles: string[]): boolean {
  return roles.some((role) => READER_ROLES.has(role));
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

function formatEvaluationTitle(value: string): string {
  return `Evaluation started ${formatDateTime(value)}`;
}

function formatRunStatus(value: string): string {
  return value.replaceAll('_', ' ');
}

function sectionDivider(label: string) {
  return (
    <div className="flex items-center gap-3 pt-3">
      <div className="h-px flex-1 bg-gradient-to-r from-transparent via-[rgba(25,58,90,0.12)] to-transparent" />
      <span className="text-[11px] font-bold uppercase tracking-[0.22em] text-muted/60">{label}</span>
      <div className="h-px flex-1 bg-gradient-to-r from-transparent via-[rgba(25,58,90,0.12)] to-transparent" />
    </div>
  );
}

export function SurgeAlertReview({ roles }: { roles: string[] }) {
  const [evaluations, setEvaluations] = useState<SurgeEvaluationRunSummary[]>([]);
  const [events, setEvents] = useState<SurgeAlertEventSummary[]>([]);
  const [selectedEvaluation, setSelectedEvaluation] = useState<SurgeEvaluationRunDetail | null>(null);
  const [selectedEvent, setSelectedEvent] = useState<SurgeAlertEvent | null>(null);
  const [selectedEvaluationId, setSelectedEvaluationId] = useState<string | null>(null);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const readable = canReadAlerts(roles);

  async function refreshSurgeData(): Promise<void> {
    try {
      const [evaluationItems, eventItems] = await Promise.all([fetchSurgeEvaluations(), fetchSurgeEvents()]);
      setEvaluations(evaluationItems);
      setEvents(eventItems);
      if (evaluationItems[0]) {
        setSelectedEvaluationId(evaluationItems[0].surgeEvaluationRunId);
        setSelectedEvaluation(await fetchSurgeEvaluation(evaluationItems[0].surgeEvaluationRunId));
      }
      if (eventItems[0]) {
        setSelectedEventId(eventItems[0].surgeNotificationEventId);
        setSelectedEvent(await fetchSurgeEvent(eventItems[0].surgeNotificationEventId));
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Unable to load surge alerts.');
    }
  }

  useEffect(() => {
    if (!readable) {
      return;
    }
    void refreshSurgeData();
  }, [readable]);

  async function handleSelectEvaluation(surgeEvaluationRunId: string): Promise<void> {
    setSelectedEvaluationId(surgeEvaluationRunId);
    setSelectedEvaluation(await fetchSurgeEvaluation(surgeEvaluationRunId));
  }

  async function handleSelectEvent(surgeNotificationEventId: string): Promise<void> {
    setSelectedEventId(surgeNotificationEventId);
    setSelectedEvent(await fetchSurgeEvent(surgeNotificationEventId));
  }

  if (!readable) {
    return <div className="text-sm text-slate-600">Your current role does not include surge alert review access.</div>;
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
      <Card className="rounded-[28px] border-white/60 bg-white/85 shadow-[0_20px_60px_rgba(15,23,42,0.08)]">
        <CardHeader>
          <p className="m-0 text-[11px] font-semibold uppercase tracking-[0.22em] text-accent/80">Surge Alerts</p>
          <CardTitle className="text-3xl text-ink">Review surge evaluations and notifications</CardTitle>
          <CardDescription>Inspect automatically generated surge evaluations, detector failures, confirmation outcomes, duplicate suppression, and delivery attempts.</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4">
          {error ? <p className="text-sm font-medium text-red-700">{error}</p> : null}

          {sectionDivider('Evaluation Runs')}

          <div className="grid max-h-80 gap-2 overflow-auto">
            {evaluations.length === 0 ? <p className="text-sm text-slate-500">No surge evaluations are available yet.</p> : null}
            {evaluations.map((item) => (
              <button
                key={item.surgeEvaluationRunId}
                type="button"
                onClick={() => {
                  void handleSelectEvaluation(item.surgeEvaluationRunId);
                }}
                className={`group grid gap-1.5 rounded-2xl border px-4 py-3 text-left transition-all ${
                  selectedEvaluationId === item.surgeEvaluationRunId
                    ? 'border-accent/30 bg-accent/[0.04] shadow-[0_4px_16px_rgba(0,80,135,0.10)]'
                    : 'border-slate-200 bg-slate-50/70 hover:border-accent/20 hover:bg-white hover:shadow-sm'
                }`}
              >
                <div className="flex items-center justify-between gap-3">
                  <strong className={`${selectedEvaluationId === item.surgeEvaluationRunId ? 'text-accent' : 'text-ink'}`}>{formatEvaluationTitle(item.startedAt)}</strong>
                  <span className="text-xs uppercase tracking-wide text-slate-500">{formatRunStatus(item.status)}</span>
                </div>
                <div className="mt-2 text-sm text-slate-600">
                  {item.candidateCount} candidate{item.candidateCount === 1 ? '' : 's'} • {item.confirmedCount} confirmed
                </div>
                {item.failureSummary ? <div className="text-xs text-red-700">{item.failureSummary}</div> : null}
              </button>
            ))}
          </div>

          {sectionDivider('Recorded Surges')}

          <div className="grid max-h-80 gap-2 overflow-auto">
            {events.length === 0 ? <p className="text-sm text-slate-500">No surge notification events are available yet.</p> : null}
            {events.map((item) => (
              <button
                key={item.surgeNotificationEventId}
                type="button"
                onClick={() => {
                  void handleSelectEvent(item.surgeNotificationEventId);
                }}
                className={`group grid gap-1.5 rounded-2xl border px-4 py-3 text-left transition-all ${
                  selectedEventId === item.surgeNotificationEventId
                    ? 'border-accent/30 bg-accent/[0.04] shadow-[0_4px_16px_rgba(0,80,135,0.10)]'
                    : 'border-slate-200 bg-slate-50/70 hover:border-accent/20 hover:bg-white hover:shadow-sm'
                }`}
              >
                <div className="flex items-center justify-between gap-3">
                  <strong className={`${selectedEventId === item.surgeNotificationEventId ? 'text-accent' : 'text-ink'}`}>{item.serviceCategory}</strong>
                  <span className="text-xs uppercase tracking-wide text-slate-500">{STATUS_LABELS[item.overallDeliveryStatus]}</span>
                </div>
                <div className="mt-2 text-sm text-slate-600">Residual {item.residualValue} • z-score {item.residualZScore}</div>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="lg:sticky lg:top-7 lg:self-start">
        <Card className="overflow-hidden rounded-[28px] border-white/60 bg-white/85 shadow-[0_20px_60px_rgba(15,23,42,0.08)]">
          <div
            className="h-1.5"
            style={{
              background: selectedEvent
                ? 'linear-gradient(90deg, #f59e0b, #f97316, #ef4444)'
                : 'linear-gradient(90deg, #005087, #0081BC, #38bdf8)',
            }}
          />
          <CardHeader>
            <p className="m-0 text-[11px] font-semibold uppercase tracking-[0.22em] text-accent/80">Surge Inspector</p>
            <CardTitle className="text-2xl text-ink">Review Detail</CardTitle>
            <CardDescription>Inspect candidate metrics, confirmation decisions, and downstream delivery attempts.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-5">
            {selectedEvaluation ? (
              <div className="grid gap-4 rounded-2xl border border-[rgba(25,58,90,0.10)] p-4" style={{ background: 'linear-gradient(135deg, rgba(241,247,252,0.9) 0%, rgba(255,255,255,0.95) 100%)' }}>
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <p className="text-lg font-bold text-ink">{formatEvaluationTitle(selectedEvaluation.startedAt)}</p>
                    <p className="text-xs text-muted">
                      {selectedEvaluation.completedAt ? `Completed ${formatDateTime(selectedEvaluation.completedAt)}` : 'Waiting for completion'}
                    </p>
                  </div>
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-accent/15 bg-accent/5 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em] text-accent">
                    {formatRunStatus(selectedEvaluation.status)}
                  </span>
                </div>
                {selectedEvaluation.failureSummary ? (
                  <div className="rounded-xl border border-amber-200 bg-amber-50/60 px-4 py-3">
                    <p className="text-[11px] font-bold uppercase tracking-wider text-amber-700/70">Run Summary</p>
                    <p className="mt-1 text-sm font-medium text-amber-900">{selectedEvaluation.failureSummary}</p>
                  </div>
                ) : null}
                <div className="grid gap-3">
                  {selectedEvaluation.candidates.map((candidate) => (
                    <div
                      key={candidate.surgeCandidateId}
                      className="grid gap-2 rounded-[22px] border border-white/80 px-5 py-4 text-sm text-ink shadow-[0_8px_28px_rgba(15,23,42,0.06)]"
                      style={{ background: 'linear-gradient(135deg, rgba(255,255,255,0.98) 0%, rgba(241,247,252,0.95) 100%)' }}
                    >
                      <div className="flex flex-wrap items-start justify-between gap-3">
                        <div>
                          <p className="text-base font-bold leading-tight text-ink">{candidate.serviceCategory}</p>
                          <p className="text-sm text-muted">Actual {candidate.actualDemandValue} vs forecast {candidate.forecastP50Value ?? 'n/a'}</p>
                        </div>
                        <span className="inline-flex items-center gap-1.5 rounded-full border border-accent/15 bg-accent/5 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em] text-accent">
                          {candidate.candidateStatus.replaceAll('_', ' ')}
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-3 text-xs text-muted">
                        <span>Residual z-score <span className="font-semibold text-ink">{candidate.residualZScore ?? 'n/a'}</span></span>
                        <span className="text-slate-300">|</span>
                        <span>Percent above forecast <span className="font-semibold text-ink">{candidate.percentAboveForecast ?? 'n/a'}</span></span>
                      </div>
                      {candidate.confirmation ? (
                        <div className="text-sm text-slate-700">
                          Outcome: <span className="font-semibold">{candidate.confirmation.outcome.replaceAll('_', ' ')}</span>
                        </div>
                      ) : null}
                      {candidate.failureReason ? <div className="text-sm text-red-700">{candidate.failureReason}</div> : null}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3 py-10 text-center">
                <span className="text-5xl opacity-20">📋</span>
                <p className="text-sm font-medium text-muted">Select a surge evaluation to inspect detector and confirmation details.</p>
              </div>
            )}

            {selectedEvent ? (
              <div className="grid gap-4 rounded-2xl border border-[rgba(25,58,90,0.10)] p-4" style={{ background: 'linear-gradient(135deg, rgba(241,247,252,0.9) 0%, rgba(255,255,255,0.95) 100%)' }}>
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <p className="text-lg font-bold text-ink">{selectedEvent.serviceCategory}</p>
                    <p className="text-xs text-muted">Created {formatDateTime(selectedEvent.createdAt)}</p>
                  </div>
                  <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-[11px] font-bold uppercase tracking-[0.14em] text-emerald-800">
                    {STATUS_LABELS[selectedEvent.overallDeliveryStatus]}
                  </span>
                </div>
                <div className="flex flex-wrap gap-3 text-sm text-slate-700">
                  <span>Residual <span className="font-semibold text-ink">{selectedEvent.residualValue}</span></span>
                  <span className="text-slate-300">|</span>
                  <span>z-score <span className="font-semibold text-ink">{selectedEvent.residualZScore}</span></span>
                </div>
                {selectedEvent.followUpReason ? (
                  <div className="rounded-xl border border-amber-200 bg-amber-50/60 px-4 py-3">
                    <p className="text-[11px] font-bold uppercase tracking-wider text-amber-700/70">Follow-up Reason</p>
                    <p className="mt-1 text-sm font-medium text-amber-900">{selectedEvent.followUpReason}</p>
                  </div>
                ) : null}
                <div className="grid gap-3">
                  {selectedEvent.channelAttempts.map((attempt) => (
                    <div
                      key={`${attempt.channelType}-${attempt.attemptNumber}`}
                      className="grid gap-2 rounded-[22px] border border-white/80 px-5 py-4 text-sm text-ink shadow-[0_8px_28px_rgba(15,23,42,0.06)]"
                      style={{ background: 'linear-gradient(135deg, rgba(255,255,255,0.98) 0%, rgba(241,247,252,0.95) 100%)' }}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <strong>{attempt.channelType}</strong>
                        <span className="text-xs uppercase tracking-wide text-slate-500">{attempt.status}</span>
                      </div>
                      {attempt.failureReason ? <div className="text-red-700">{attempt.failureReason}</div> : null}
                    </div>
                  ))}
                </div>
              </div>
            ) : null}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
