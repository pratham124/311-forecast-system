export type ForecastWindowType = 'hourly' | 'daily';

export type OverallDeliveryStatus = 'delivered' | 'partial_delivery' | 'retry_pending' | 'manual_review_required';

export type NotificationChannelAttempt = {
  channelType: string;
  attemptNumber: number;
  attemptedAt: string;
  status: 'succeeded' | 'failed';
  failureReason?: string | null;
  providerReference?: string | null;
};

export type ThresholdAlertEventSummary = {
  notificationEventId: string;
  serviceCategory: string;
  geographyType?: string | null;
  geographyValue?: string | null;
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
  deliveredAt?: string | null;
  failedChannelCount: number;
  channelAttempts: NotificationChannelAttempt[];
};

export type ThresholdAlertEventListResponse = {
  items: ThresholdAlertEventSummary[];
};

export type ThresholdConfigurationUpdateRequest = {
  thresholdValue: number;
};

export type ThresholdConfiguration = {
  thresholdConfigurationId: string;
  serviceCategory: string;
  forecastWindowType: ForecastWindowType;
  thresholdValue: number;
  geographyType?: string | null;
  geographyValue?: string | null;
  operationalManagerId: string;
  status: string;
  effectiveFrom: string;
  effectiveTo?: string | null;
};

export type ThresholdConfigurationListResponse = {
  items: ThresholdConfiguration[];
};
