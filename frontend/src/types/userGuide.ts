export type UserGuideStatus = 'available' | 'unavailable' | 'error';
export type UserGuideRenderOutcome = 'rendered' | 'render_failed';

export type GuideSection = {
  sectionId: string;
  label: string;
  orderIndex: number;
  anchorTarget?: string | null;
  contentExcerpt?: string | null;
};

export type UserGuideView = {
  guideAccessEventId: string;
  status: UserGuideStatus;
  title?: string | null;
  publishedAt?: string | null;
  body?: string | null;
  sections?: GuideSection[] | null;
  statusMessage?: string | null;
  entryPoint: string;
};

export type GuideRenderOutcomeRequest = {
  renderOutcome: UserGuideRenderOutcome;
  failureMessage?: string | null;
};
