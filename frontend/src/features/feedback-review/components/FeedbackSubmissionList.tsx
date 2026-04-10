import type { FeedbackSubmissionSummary } from '../../../types/feedbackSubmissions';

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

function toLabel(value: string): string {
  return value.replace(/_/g, ' ');
}

type FeedbackSubmissionListProps = {
  items: FeedbackSubmissionSummary[];
  selectedId: string | null;
  onSelect: (feedbackSubmissionId: string) => void;
};

export function FeedbackSubmissionList({ items, selectedId, onSelect }: FeedbackSubmissionListProps) {
  if (items.length === 0) {
    return <p className="text-sm text-muted">No feedback submissions match the current filters.</p>;
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <button
          key={item.feedbackSubmissionId}
          type="button"
          onClick={() => onSelect(item.feedbackSubmissionId)}
          className={`w-full rounded-[24px] border px-4 py-4 text-left transition ${
            selectedId === item.feedbackSubmissionId
              ? 'border-accent bg-slate-50 shadow-[0_10px_30px_rgba(0,80,135,0.08)]'
              : 'border-slate-200 bg-white hover:border-accent/50'
          }`}
        >
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-semibold text-ink">{item.reportType}</p>
            <p className="text-xs uppercase tracking-[0.16em] text-accent">{toLabel(item.processingStatus)}</p>
          </div>
          <p className="mt-2 text-xs text-muted">
            {item.submitterKind} submitter · triage {toLabel(item.triageStatus)} · {formatDate(item.submittedAt)}
          </p>
        </button>
      ))}
    </div>
  );
}
