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
      <Card className="rounded-[30px] border-white/70 bg-white/90 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
        <CardHeader className="gap-4">
          <p className="text-xs uppercase tracking-[0.22em] text-accent">Review queue</p>
          <CardTitle className="text-4xl text-ink">Feedback and bug reports</CardTitle>
        </CardHeader>
        <CardContent className="space-y-5">
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

          {error ? (
            <Alert variant="destructive">
              <AlertTitle>Feedback queue request failed</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}

          <div className="grid gap-5 lg:grid-cols-[0.95fr_1.05fr]">
            <div className="rounded-[28px] border border-slate-200 bg-white px-5 py-5">
              {isLoadingList ? (
                <p className="text-sm text-muted">Loading feedback submissions...</p>
              ) : (
                <FeedbackSubmissionList items={items} selectedId={selectedId} onSelect={setSelectedId} />
              )}
            </div>
            <div className="rounded-[28px] border border-slate-200 bg-white px-5 py-5">
              <FeedbackSubmissionDetail detail={detail} isLoading={isLoadingDetail} />
            </div>
          </div>
        </CardContent>
      </Card>
    </main>
  );
}
