import type { FeedbackSubmissionDetail as FeedbackSubmissionDetailType } from '../../../types/feedbackSubmissions';

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

function toLabel(value: string): string {
  return value.replace(/_/g, ' ');
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
    return <p className="text-sm text-muted">Select a submission to view the review timeline.</p>;
  }

  return (
    <div className="space-y-5">
      <div className="rounded-[24px] border border-slate-200 bg-white px-5 py-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-accent">{detail.reportType}</p>
            <h3 className="mt-2 text-2xl font-semibold text-ink">Submission detail</h3>
          </div>
          <div className="text-right text-sm text-muted">
            <p>{toLabel(detail.processingStatus)}</p>
            <p>{formatDate(detail.submittedAt)}</p>
          </div>
        </div>
        <p className="mt-4 rounded-[20px] bg-slate-50 px-4 py-4 text-sm leading-7 text-ink">{detail.description}</p>
        <div className="mt-4 grid gap-2 text-sm text-muted sm:grid-cols-2">
          <p>Submitter: {detail.submitterKind}</p>
          <p>Triage: {toLabel(detail.triageStatus)}</p>
          <p>Visibility: {toLabel(detail.visibilityStatus)}</p>
          <p>Contact: {detail.contactEmail ?? 'Not provided'}</p>
          <p className="sm:col-span-2">Issue tracker reference: {detail.externalReference ?? 'Not forwarded yet'}</p>
        </div>
      </div>

      <div className="rounded-[24px] border border-slate-200 bg-white px-5 py-5">
        <p className="text-xs uppercase tracking-[0.18em] text-accent">Status history</p>
        <div className="mt-4 space-y-3">
          {detail.statusEvents.map((event) => (
            <div key={`${event.eventType}-${event.recordedAt}`} className="rounded-[20px] bg-slate-50 px-4 py-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="text-sm font-semibold text-ink">{toLabel(event.eventType)}</p>
                <p className="text-xs text-muted">{formatDate(event.recordedAt)}</p>
              </div>
              {event.eventReason ? <p className="mt-2 text-sm text-muted">{event.eventReason}</p> : null}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
