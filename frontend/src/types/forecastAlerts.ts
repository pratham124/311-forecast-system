export type ForecastAlertProduct = 'daily' | 'weekly';
export type ForecastWindowType = 'hourly' | 'daily';
export type OverallDeliveryStatus = 'delivered' | 'partial_delivery' | 'retry_pending' | 'manual_review_required';

export type ThresholdEvaluationTriggerResponse = {
  thresholdEvaluationRunId: string;
  status: 'accepted';
  acceptedAt: string;
};

export type ThresholdConfiguration = {
  thresholdConfigurationId: string;
  serviceCategory: string;
  forecastWindowType: ForecastWindowType;
  thresholdValue: number;
  notificationChannels: string[];
  operationalManagerId: string;
  status: string;
  effectiveFrom: string;
  effectiveTo?: string | null;
};

export type ThresholdConfigurationWrite = {
  serviceCategory: string;
  forecastWindowType: ForecastWindowType;
  thresholdValue: number;
  notificationChannels: string[];
};

export type NotificationChannelAttempt = {
  channelType: string;
  attemptNumber: number;
  status: 'succeeded' | 'failed';
  attemptedAt: string;
  failureReason?: string | null;
  providerReference?: string | null;
};

export type ThresholdAlertEventSummary = {
  notificationEventId: string;
  serviceCategory: string;
  forecastWindowType: ForecastWindowType;
  forecastWindowStart: string;
  forecastWindowEnd: string;
  forecastValue: number;
  thresholdValue: number;
  overallDeliveryStatus: OverallDeliveryStatus;
  createdAt: string;
};

export type ThresholdAlertEvent = ThresholdAlertEventSummary & {
  thresholdEvaluationRunId: string;
  thresholdConfigurationId: string;
  followUpReason?: string | null;
  channelAttempts: NotificationChannelAttempt[];
};
