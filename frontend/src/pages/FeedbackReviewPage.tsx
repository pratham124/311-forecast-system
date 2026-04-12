import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Select } from '../components/ui/select';
import { FeedbackSubmissionDetail } from '../features/feedback-review/components/FeedbackSubmissionDetail';
import { FeedbackSubmissionList } from '../features/feedback-review/components/FeedbackSubmissionList';
import { useFeedbackReview } from '../features/feedback-review/hooks/useFeedbackReview';
import type { ProcessingStatus, ReportType } from '../types/feedbackSubmissions';

const READER_ROLES = new Set(['CityPlanner', 'OperationalManager']);

type FeedbackReviewPageProps = {
  roles: string[];
};

function canReadFeedbackReview(roles: string[]): boolean {
  return roles.some((role) => READER_ROLES.has(role));
}

export function FeedbackReviewPage({ roles }: FeedbackReviewPageProps) {
  const readable = canReadFeedbackReview(roles);
  const {
    reportTypeFilter,
    setReportTypeFilter,
    processingStatusFilter,
    setProcessingStatusFilter,
    items,
    selectedId,
    setSelectedId,
    detail,
    isLoadingList,
    isLoadingDetail,
    error,
  } = useFeedbackReview(readable);

  if (!readable) {
    return (
      <main className="mx-auto w-full max-w-6xl px-4 pb-14 pt-7 sm:px-6 lg:px-8">
        <Alert variant="destructive">
          <AlertTitle>Feedback review access is restricted</AlertTitle>
          <AlertDescription>Your current role does not include reviewer access for submitted reports.</AlertDescription>
        </Alert>
      </main>
    );
  }

  return (
    <main className="mx-auto w-full max-w-6xl px-4 pb-14 pt-7 sm:px-6 lg:px-8" aria-label="feedback review page">
      <Card className="overflow-hidden rounded-[30px] border-white/70 bg-white/90 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
        <CardHeader className="gap-4 bg-[linear-gradient(135deg,rgba(12,74,110,0.08),rgba(255,255,255,0.96)_45%,rgba(14,116,144,0.08))] pb-7">
          <p className="text-xs uppercase tracking-[0.22em] text-accent">Review queue</p>
          <CardTitle className="text-4xl text-ink">Feedback and bug reports</CardTitle>
          <p className="max-w-2xl text-sm leading-6 text-muted">
            Review the latest submissions, inspect forwarding state, and open the full report timeline without leaving the queue.
          </p>
        </CardHeader>
        <CardContent className="space-y-6 p-6 sm:p-7">
          <div className="rounded-[26px] border border-slate-200/80 bg-[linear-gradient(180deg,rgba(248,250,252,0.92),rgba(255,255,255,0.98))] p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)] sm:p-5">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.18em] text-accent/80">Filters</p>
                <p className="mt-1 text-sm text-muted">Narrow the inbox by report type and current processing state.</p>
              </div>
              <div className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-500">
                {items.length} {items.length === 1 ? 'submission' : 'submissions'}
              </div>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              <div className="grid gap-2">
                <label className="text-sm font-semibold text-ink" htmlFor="feedback-review-report-type">Report type filter</label>
                <Select
                  id="feedback-review-report-type"
                  value={reportTypeFilter}
                  onChange={(event) => setReportTypeFilter(event.target.value as ReportType | 'all')}
                >
                  <option value="all">All report types</option>
                  <option value="Feedback">Feedback</option>
                  <option value="Bug Report">Bug Report</option>
                </Select>
              </div>
              <div className="grid gap-2">
                <label className="text-sm font-semibold text-ink" htmlFor="feedback-review-processing-status">Processing status filter</label>
                <Select
                  id="feedback-review-processing-status"
                  value={processingStatusFilter}
                  onChange={(event) => setProcessingStatusFilter(event.target.value as ProcessingStatus | 'all')}
                >
                  <option value="all">All processing states</option>
                  <option value="accepted">Accepted</option>
                  <option value="forwarded">Forwarded</option>
                  <option value="deferred_for_retry">Deferred for retry</option>
                  <option value="forward_failed">Forward failed</option>
                </Select>
              </div>
            </div>
          </div>

          {error ? (
            <Alert variant="destructive">
              <AlertTitle>Feedback queue request failed</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}

          <div className="grid gap-5 lg:grid-cols-[0.95fr_1.05fr]">
            <div className="rounded-[28px] border border-slate-200 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,252,0.92))] p-5">
              {isLoadingList ? (
                <p className="text-sm text-muted">Loading feedback submissions...</p>
              ) : (
                <FeedbackSubmissionList items={items} selectedId={selectedId} onSelect={setSelectedId} />
              )}
            </div>
            <div className="rounded-[28px] border border-slate-200 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(248,250,252,0.92))] p-5">
              <FeedbackSubmissionDetail detail={detail} isLoading={isLoadingDetail} />
            </div>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
