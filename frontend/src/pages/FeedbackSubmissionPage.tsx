import { Link } from 'react-router-dom';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { FeedbackSubmissionForm } from '../features/feedback/components/FeedbackSubmissionForm';
import { useFeedbackSubmission } from '../features/feedback/hooks/useFeedbackSubmission';

type FeedbackSubmissionPageProps = {
  isAuthenticated: boolean;
};

export function FeedbackSubmissionPage({ isAuthenticated }: FeedbackSubmissionPageProps) {
  const { values, errors, result, isSubmitting, setFieldValue, submit, reset } = useFeedbackSubmission();

  const handleSubmit = () => {
    void submit();
  };

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.97),_rgba(240,246,252,0.93)_34%,_rgba(210,225,236,0.88)_100%)] px-4 py-10 sm:px-6 lg:px-8">
      <div className="mx-auto w-full max-w-6xl">
        <header className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-[28px] border border-white/70 bg-white/72 px-5 py-4 shadow-[0_18px_50px_rgba(15,23,42,0.08)] backdrop-blur">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.24em] text-accent/80">Support & Feedback</p>
            <p className="mt-1 text-sm text-muted">Report technical issues or suggest system improvements</p>
          </div>
          <nav className="flex flex-wrap items-center gap-2" aria-label="feedback navigation">
            <Link
              to={isAuthenticated ? '/app/forecasts' : '/'}
              className="inline-flex min-h-10 items-center justify-center rounded-2xl border border-slate-300 bg-white px-4 text-sm font-semibold text-ink transition hover:border-accent hover:text-accent"
            >
              {isAuthenticated ? 'Back to dashboard' : 'Back'}
            </Link>
            {isAuthenticated ? (
              <Link
                to="/app/feedback-review"
                className="inline-flex min-h-10 items-center justify-center rounded-2xl border border-slate-300 bg-white px-4 text-sm font-semibold text-ink transition hover:border-accent hover:text-accent"
              >
                Open feedback inbox
              </Link>
            ) : null}
          </nav>
        </header>

        <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <Card className="rounded-[32px] border-white/70 bg-white/90 shadow-[0_24px_80px_rgba(15,23,42,0.10)] backdrop-blur">
            <CardHeader className="gap-4 pb-4">
              <p className="text-xs uppercase tracking-[0.24em] text-accent">Feedback intake</p>
              <CardTitle className="max-w-4xl text-4xl leading-tight text-ink sm:text-5xl">
                Help us improve the 311 Forecast System
              </CardTitle>
              <CardDescription className="max-w-3xl text-base leading-7 text-muted">
                Share product feedback or report a bug. You can submit anonymously, and contact details are optional.
              </CardDescription>
            </CardHeader>
            <CardContent className="pb-6">
              {result ? (
                <Alert>
                  <AlertTitle>{result.userOutcome === 'accepted' ? 'Report received' : 'Report received with delayed processing'}</AlertTitle>
                  <AlertDescription>{result.statusMessage}</AlertDescription>
                </Alert>
              ) : null}

              <div className="mt-6">
                <FeedbackSubmissionForm
                  values={values}
                  errors={errors}
                  isSubmitting={isSubmitting}
                  onChange={setFieldValue}
                  onSubmit={handleSubmit}
                />
              </div>

              {result ? (
                <div className="mt-4">
                  <button
                    type="button"
                    onClick={reset}
                    className="inline-flex min-h-11 items-center justify-center rounded-2xl border border-slate-300 bg-white px-4 text-sm font-semibold text-ink transition hover:border-accent hover:text-accent"
                  >
                    Submit another report
                  </button>
                </div>
              ) : null}
            </CardContent>
          </Card>

          <div className="space-y-6">
            <Card className="rounded-[30px] border-white/70 bg-white/88 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
              <CardHeader className="pb-3">
                <p className="text-xs uppercase tracking-[0.22em] text-accent">What to include</p>
                <CardTitle className="text-2xl text-ink">Give the team a fast path to reproduce the issue</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-3 text-sm leading-7 text-muted">
                <p>Choose “Feedback” for product suggestions and “Bug Report” for broken behavior.</p>
                <p>Describe what you were doing, what you expected, and what actually happened.</p>
                <p>Leave contact details only if you want the team to follow up directly.</p>
              </CardContent>
            </Card>

            <Card className="rounded-[30px] border-white/70 bg-white/88 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
              <CardHeader className="pb-3">
                <p className="text-xs uppercase tracking-[0.22em] text-accent">Reliability</p>
                <CardTitle className="text-2xl text-ink">Accepted reports stay reviewable</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-3 text-sm leading-7 text-muted">
                <p>If the external issue tracker is temporarily unavailable, the system still saves your report locally.</p>
                <p>Signed-in planners and operational managers can review the feedback inbox and track forwarding status.</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </main>
  );
}
