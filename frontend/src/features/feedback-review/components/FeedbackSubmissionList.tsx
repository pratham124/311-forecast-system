import type { FeedbackSubmissionSummary } from '../../../types/feedbackSubmissions';

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

function reportTypeStyles(value: FeedbackSubmissionSummary['reportType']): string {
  return value === 'Bug Report'
    ? 'border-rose-200 bg-rose-50 text-rose-700'
    : 'border-sky-200 bg-sky-50 text-sky-700';
}

function processingStatusStyles(value: FeedbackSubmissionSummary['processingStatus']): string {
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

type FeedbackSubmissionListProps = {
  items: FeedbackSubmissionSummary[];
  selectedId: string | null;
  onSelect: (feedbackSubmissionId: string) => void;
};

export function FeedbackSubmissionList({ items, selectedId, onSelect }: FeedbackSubmissionListProps) {
  if (items.length === 0) {
    return (
      <div className="rounded-[24px] border border-dashed border-slate-300 bg-slate-50/80 px-5 py-10 text-center">
        <p className="text-sm font-semibold text-ink">No matching submissions</p>
        <p className="mt-2 text-sm text-muted">No feedback submissions match the current filters.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3 px-1">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-accent/80">Inbox</p>
          <p className="mt-1 text-sm text-muted">Select a submission to inspect its full history.</p>
        </div>
        <div className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-500">
          Sorted by newest
        </div>
      </div>

      {items.map((item) => (
        <button
          key={item.feedbackSubmissionId}
          type="button"
          onClick={() => onSelect(item.feedbackSubmissionId)}
          className={`w-full rounded-[24px] border px-4 py-4 text-left transition ${
            selectedId === item.feedbackSubmissionId
              ? 'border-accent bg-[linear-gradient(135deg,rgba(240,249,255,0.95),rgba(255,255,255,1))] shadow-[0_18px_40px_rgba(14,116,144,0.12)]'
              : 'border-slate-200 bg-white hover:border-accent/40 hover:shadow-[0_14px_30px_rgba(15,23,42,0.06)]'
          }`}
        >
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-2">
                <span className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] ${reportTypeStyles(item.reportType)}`}>
                  {item.reportType}
                </span>
                <span className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] ${processingStatusStyles(item.processingStatus)}`}>
                  {toLabel(item.processingStatus)}
                </span>
              </div>
              <div>
                <p className="text-base font-semibold text-ink">
                  {item.reportType === 'Bug Report' ? 'Product issue reported' : 'Product feedback received'}
                </p>
                <p className="mt-1 text-sm text-muted">
                  {item.submitterKind} submitter · triage {toLabel(item.triageStatus)}
                </p>
              </div>
            </div>

            <div className="text-right">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400">Received</p>
              <p className="mt-1 text-sm font-medium text-slate-600">{formatDate(item.submittedAt)}</p>
            </div>
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-slate-100 pt-3">
            <span className="text-xs font-medium text-slate-400">
              {item.submitterKind} reporter
            </span>
            <span className="text-xs font-medium text-accent">{selectedId === item.feedbackSubmissionId ? 'Opened in detail panel' : 'Open submission'}</span>
          </div>
        </button>
      ))}
    </div>
  );
}
