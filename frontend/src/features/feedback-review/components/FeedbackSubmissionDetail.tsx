import type { FeedbackSubmissionDetail as FeedbackSubmissionDetailType } from '../../../types/feedbackSubmissions';

function formatDate(value: string): string {
  return new Intl.DateTimeFormat([], {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: 'numeric',
  }).format(new Date(value));
}

function toLabel(value: string): string {
  return value.replace(/_/g, ' ');
}

function reportTypeStyles(value: FeedbackSubmissionDetailType['reportType']): string {
  return value === 'Bug Report'
    ? 'border-rose-200 bg-rose-50 text-rose-700'
    : 'border-sky-200 bg-sky-50 text-sky-700';
}

function processingStatusStyles(value: FeedbackSubmissionDetailType['processingStatus']): string {
  switch (value) {
    case 'accepted':
      return 'border-emerald-200 bg-emerald-50 text-emerald-700';
    case 'forwarded':
      return 'border-cyan-200 bg-cyan-50 text-cyan-700';
    case 'deferred_for_retry':
      return 'border-amber-200 bg-amber-50 text-amber-700';
    case 'forward_failed':
      return 'border-rose-200 bg-rose-50 text-rose-700';
  }
}

function timelineDotStyles(eventType: string): string {
  if (eventType === 'accepted') return 'bg-emerald-500';
  if (eventType === 'forwarded') return 'bg-cyan-500';
  if (eventType === 'deferred_for_retry') return 'bg-amber-500';
  if (eventType === 'forward_failed') return 'bg-rose-500';
  return 'bg-slate-400';
}

function detailField(label: string, value: string) {
  return (
    <div className="border-b border-slate-100 py-3 last:border-b-0">
      <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">{label}</p>
      <p className="mt-1 text-sm text-ink">{value}</p>
    </div>
  );
}

type FeedbackSubmissionDetailProps = {
  detail: FeedbackSubmissionDetailType | null;
  isLoading: boolean;
};

export function FeedbackSubmissionDetail({ detail, isLoading }: FeedbackSubmissionDetailProps) {
  if (isLoading) {
    return <p className="text-sm text-muted">Loading submission details...</p>;
  }
  if (!detail) {
    return (
      <div className="rounded-[24px] border border-dashed border-slate-300 bg-slate-50/80 px-5 py-10 text-center">
        <p className="text-sm font-semibold text-ink">No submission selected</p>
        <p className="mt-2 text-sm text-muted">Select a submission to view the review timeline.</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <section className="rounded-[24px] border border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-5 py-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] ${reportTypeStyles(detail.reportType)}`}>
                  {detail.reportType}
                </span>
                <span className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] ${processingStatusStyles(detail.processingStatus)}`}>
                  {toLabel(detail.processingStatus)}
                </span>
              </div>
              <h3 className="mt-3 text-xl font-semibold text-ink">Opened submission</h3>
              <p className="mt-1 text-sm text-muted">
                Submitted {formatDate(detail.submittedAt)}
              </p>
            </div>

            <div className="min-w-[180px] text-sm text-slate-500">
              <div className="rounded-[18px] border border-slate-200 bg-slate-50/80 px-4 py-3">
                <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">Current review state</p>
                <div className="mt-3 space-y-2">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Triage</span>
                    <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-700">
                      {toLabel(detail.triageStatus)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-400">Visibility</span>
                    <span className="rounded-full border border-slate-200 bg-white px-2.5 py-1 text-xs font-medium text-slate-700">
                      {toLabel(detail.visibilityStatus)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-0 lg:grid-cols-[1.3fr_0.9fr]">
          <div className="px-5 py-5">
            <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-slate-400">Reporter notes</p>
            <p className="mt-3 text-sm leading-7 text-ink">{detail.description}</p>
          </div>

          <div className="border-t border-slate-200 px-5 py-5 lg:border-l lg:border-t-0">
            {detailField('Submitter', detail.submitterKind)}
            {detailField('Contact', detail.contactEmail ?? 'Not provided')}
            {detailField('Issue tracker reference', detail.externalReference ?? 'Not forwarded yet')}
          </div>
        </div>
      </section>

      <section className="rounded-[24px] border border-slate-200 bg-white px-5 py-5">
        <div>
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-accent">Status history</p>
            <p className="mt-1 text-sm text-muted">Timeline of review and forwarding updates for this submission.</p>
          </div>
        </div>

        <div className="mt-5 space-y-3">
          {detail.statusEvents.map((event) => (
            <div key={`${event.eventType}-${event.recordedAt}`} className="rounded-[18px] border border-slate-200 bg-slate-50/70 px-4 py-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <span className={`mt-1 inline-block h-3 w-3 rounded-full ${timelineDotStyles(event.eventType)}`} />
                  <div>
                    <p className="text-sm font-semibold text-ink">{toLabel(event.eventType)}</p>
                    {event.eventReason ? <p className="mt-2 text-sm leading-6 text-muted">{event.eventReason}</p> : null}
                  </div>
                </div>
                <p className="text-xs font-medium text-slate-500">{formatDate(event.recordedAt)}</p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
