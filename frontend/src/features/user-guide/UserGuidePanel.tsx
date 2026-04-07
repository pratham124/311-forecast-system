import { useEffect, useMemo, useState, type ReactNode } from 'react';
import { fetchUserGuide, submitUserGuideRenderEvent } from '../../api/userGuide';
import { ChartErrorBoundary } from '../forecast-visualization/components/ChartErrorBoundary';
import type { GuideSection, UserGuideView } from '../../types/userGuide';
import { UserGuideErrorState } from './UserGuideErrorState';
import { UserGuideLoadingState } from './UserGuideLoadingState';
import { UserGuideNavigation } from './UserGuideNavigation';

type UserGuidePanelProps = {
  entryPoint: string;
  bodyRenderer?: (body: string, section: GuideSection) => ReactNode;
};

function UserGuideBody({
  body,
  section,
  bodyRenderer,
}: {
  body: string;
  section: GuideSection;
  bodyRenderer: (body: string, section: GuideSection) => ReactNode;
}) {
  return <>{bodyRenderer(body, section)}</>;
}

function formatPublishedAt(value?: string | null) {
  if (!value) return 'Not available';
  return new Date(value).toLocaleString([], {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
  });
}

function defaultBodyRenderer(body: string, section: GuideSection) {
  return (
    <>
      <h2 className="text-2xl font-semibold text-ink">{section.label}</h2>
      <p className="mt-3 text-sm leading-7 text-muted">{section.contentExcerpt ?? body}</p>
      <div className="mt-5 rounded-[20px] bg-slate-50 px-4 py-4 text-sm leading-7 text-ink">{body}</div>
    </>
  );
}

export function UserGuidePanel({ entryPoint, bodyRenderer = defaultBodyRenderer }: UserGuidePanelProps) {
  const [guide, setGuide] = useState<UserGuideView | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [requestError, setRequestError] = useState<string | null>(null);
  const [activeSectionId, setActiveSectionId] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    setIsLoading(true);
    setRequestError(null);
    fetchUserGuide(entryPoint, controller.signal)
      .then((response) => {
        if (controller.signal.aborted) return;
        setGuide(response);
        const firstSection = response.sections?.[0]?.sectionId ?? null;
        setActiveSectionId(firstSection);
      })
      .catch((error: Error) => {
        if (controller.signal.aborted) return;
        setRequestError(error.message);
        setGuide(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      });
    return () => controller.abort();
  }, [entryPoint]);

  useEffect(() => {
    if (!guide) return;
    if (guide.status !== 'available') return;
    void submitUserGuideRenderEvent(guide.guideAccessEventId, { renderOutcome: 'rendered' });
  }, [guide]);

  const activeSection = useMemo(() => {
    if (!guide?.sections?.length) return null;
    return guide.sections.find((section) => section.sectionId === activeSectionId) ?? guide.sections[0];
  }, [activeSectionId, guide]);

  const handleRenderFailure = (error: Error) => {
    if (!guide) return;
    void submitUserGuideRenderEvent(guide.guideAccessEventId, {
      renderOutcome: 'render_failed',
      failureMessage: error.message,
    });
  };

  if (isLoading) {
    return <UserGuideLoadingState />;
  }

  if (requestError) {
    return <UserGuideErrorState title="User guide request failed" message={requestError} />;
  }

  if (!guide) {
    return <UserGuideErrorState title="User guide unavailable" message="The guide could not be loaded." />;
  }

  if (guide.status === 'unavailable') {
    return <UserGuideErrorState title="User guide unavailable" message={guide.statusMessage ?? 'The guide is unavailable.'} />;
  }

  if (guide.status === 'error') {
    return <UserGuideErrorState title="User guide error" message={guide.statusMessage ?? 'The guide could not be displayed.'} />;
  }

  if (!activeSection || !guide.body) {
    return <UserGuideErrorState title="User guide error" message="The guide is missing readable content." />;
  }

  return (
    <section className="mt-6 grid gap-5 lg:grid-cols-[280px_1fr]">
      <aside className="rounded-[28px] border border-slate-200 bg-white px-4 py-4 shadow-[0_16px_40px_rgba(15,23,42,0.05)]">
        <p className="text-xs uppercase tracking-[0.22em] text-accent">Sections</p>
        <h2 className="mt-3 text-lg font-semibold text-ink">{guide.title}</h2>
        <p className="mt-2 text-sm text-muted">Published {formatPublishedAt(guide.publishedAt)}</p>
        <div className="mt-5">
          <UserGuideNavigation sections={guide.sections ?? []} activeSectionId={activeSection.sectionId} onSelect={setActiveSectionId} />
        </div>
      </aside>

      <ChartErrorBoundary
        onError={handleRenderFailure}
        fallback={
          <UserGuideErrorState
            title="We couldn't display the user guide"
            message="Please refresh and try again. We've recorded the problem."
          />
        }
      >
        <article className="rounded-[30px] border border-white/70 bg-white/90 px-6 py-6 shadow-[0_24px_80px_rgba(15,23,42,0.08)]">
          <p className="text-xs uppercase tracking-[0.22em] text-accent">{guide.entryPoint.replace(/_/g, ' ')}</p>
          <div className="mt-4">
            <UserGuideBody body={guide.body} section={activeSection} bodyRenderer={bodyRenderer} />
          </div>
        </article>
      </ChartErrorBoundary>
    </section>
  );
}
