export type ReportType = 'Feedback' | 'Bug Report';
export type ProcessingStatus = 'accepted' | 'deferred_for_retry' | 'forwarded' | 'forward_failed';
export type SubmitterKind = 'anonymous' | 'authenticated';
export type TriageStatus = 'new' | 'in_review' | 'resolved' | 'closed';
export type VisibilityStatus = 'visible' | 'hidden' | 'archived';
export type UserOutcome = 'accepted' | 'accepted_with_delay' | 'failed';

export type FeedbackSubmissionField = 'reportType' | 'description' | 'contactEmail' | 'form';

export type FeedbackSubmissionCreateRequest = {
  reportType: ReportType;
  description: string;
  contactEmail?: string | null;
};

export type FeedbackSubmissionCreateResponse = {
  feedbackSubmissionId: string;
  reportType: ReportType;
  processingStatus: ProcessingStatus;
  acceptedAt: string;
  userOutcome: UserOutcome;
  statusMessage: string;
};

export type SubmissionStatusEvent = {
  eventType: 'accepted' | ProcessingStatus;
  eventReason?: string | null;
  recordedAt: string;
  correlationId?: string | null;
};

export type FeedbackSubmissionSummary = {
  feedbackSubmissionId: string;
  reportType: ReportType;
  submitterKind: SubmitterKind;
  processingStatus: ProcessingStatus;
  submittedAt: string;
  triageStatus: TriageStatus;
};

export type FeedbackSubmissionListResponse = {
  items: FeedbackSubmissionSummary[];
};

export type FeedbackSubmissionDetail = {
  feedbackSubmissionId: string;
  reportType: ReportType;
  description: string;
  contactEmail?: string | null;
  submitterKind: SubmitterKind;
  processingStatus: ProcessingStatus;
  externalReference?: string | null;
  submittedAt: string;
  triageStatus: TriageStatus;
  visibilityStatus: VisibilityStatus;
  statusEvents: SubmissionStatusEvent[];
};

export type FeedbackSubmissionFieldErrors = Partial<Record<FeedbackSubmissionField, string>>;
