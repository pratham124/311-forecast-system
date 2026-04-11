export type OverallDeliveryStatus = 'delivered' | 'partial_delivery' | 'retry_pending' | 'manual_review_required';
export type SurgeRunStatus = 'running' | 'completed' | 'completed_with_failures';
export type CandidateStatus = 'flagged' | 'below_candidate_threshold' | 'detector_failed';
export type ConfirmationOutcome = 'confirmed' | 'filtered' | 'suppressed_active_surge' | 'failed';

export type SurgeConfirmation = {
  surgeConfirmationOutcomeId: string;
  outcome: ConfirmationOutcome;
  zScoreCheckPassed?: boolean | null;
  percentFloorCheckPassed?: boolean | null;
  surgeNotificationEventId?: string | null;
  confirmedAt: string;
  failureReason?: string | null;
};

export type SurgeCandidate = {
  surgeCandidateId: string;
  serviceCategory: string;
  evaluationWindowStart: string;
  evaluationWindowEnd: string;
  actualDemandValue: number;
  forecastP50Value?: number | null;
  residualValue?: number | null;
  residualZScore?: number | null;
  percentAboveForecast?: number | null;
  rollingBaselineMean?: number | null;
  rollingBaselineStddev?: number | null;
  candidateStatus: CandidateStatus;
  detectedAt: string;
  failureReason?: string | null;
  confirmation?: SurgeConfirmation | null;
};

export type SurgeEvaluationRunSummary = {
  surgeEvaluationRunId: string;
  ingestionRunId: string;
  triggerSource: 'ingestion_completion' | 'manual_replay';
  status: SurgeRunStatus;
  evaluatedScopeCount: number;
  candidateCount: number;
  confirmedCount: number;
  notificationCreatedCount: number;
  startedAt: string;
  completedAt?: string | null;
  failureSummary?: string | null;
};

export type SurgeEvaluationRunDetail = SurgeEvaluationRunSummary & {
  candidates: SurgeCandidate[];
};

export type SurgeEvaluationTriggerResponse = {
  surgeEvaluationRunId: string;
  status: 'accepted';
  acceptedAt: string;
};

export type SurgeNotificationChannelAttempt = {
  channelType: string;
  attemptNumber: number;
  status: 'succeeded' | 'failed';
  attemptedAt: string;
  failureReason?: string | null;
  providerReference?: string | null;
};

export type SurgeAlertEventSummary = {
  surgeNotificationEventId: string;
  surgeEvaluationRunId: string;
  surgeCandidateId: string;
  serviceCategory: string;
  evaluationWindowStart: string;
  evaluationWindowEnd: string;
  actualDemandValue: number;
  forecastP50Value: number;
  residualValue: number;
  residualZScore: number;
  percentAboveForecast?: number | null;
  overallDeliveryStatus: OverallDeliveryStatus;
  createdAt: string;
};

export type SurgeAlertEvent = SurgeAlertEventSummary & {
  surgeDetectionConfigurationId: string;
  followUpReason?: string | null;
  correlationId?: string | null;
  channelAttempts: SurgeNotificationChannelAttempt[];
};
