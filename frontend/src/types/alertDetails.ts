import type { OverallDeliveryStatus } from './forecastAlerts';

export type AlertSource = 'threshold_alert' | 'surge_alert';
export type AlertComponentStatus = 'available' | 'unavailable' | 'failed';
export type AlertDetailViewStatus = 'rendered' | 'partial' | 'unavailable' | 'error';

export type AlertSummary = {
  alertSource: AlertSource;
  alertId: string;
  sourceLabel: 'Threshold' | 'Surge';
  serviceCategory: string;
  createdAt: string;
  windowStart: string;
  windowEnd: string;
  forecastWindowType: 'hourly' | 'daily';
  overallDeliveryStatus: OverallDeliveryStatus;
  primaryMetricLabel: string;
  primaryMetricValue: number;
  secondaryMetricLabel: string;
  secondaryMetricValue: number;
};

export type AlertScope = {
  serviceCategory: string;
  geographyType?: string | null;
  geographyValue?: string | null;
};

export type AlertDistributionPoint = {
  label: string;
  bucketStart?: string | null;
  bucketEnd?: string | null;
  forecastDateLocal?: string | null;
  p10: number;
  p50: number;
  p90: number;
  isAlertedBucket: boolean;
};

export type AlertDistributionComponent = {
  status: AlertComponentStatus;
  granularity?: 'hourly' | 'daily' | null;
  summaryValue?: number | null;
  points: AlertDistributionPoint[];
  unavailableReason?: string | null;
  failureReason?: string | null;
};

export type AlertDriver = {
  label: string;
  contribution: number;
  direction: 'increase' | 'decrease';
};

export type AlertDriversComponent = {
  status: AlertComponentStatus;
  drivers: AlertDriver[];
  unavailableReason?: string | null;
  failureReason?: string | null;
};

export type AlertAnomalyContextItem = {
  surgeCandidateId: string;
  surgeNotificationEventId?: string | null;
  evaluationWindowStart: string;
  evaluationWindowEnd: string;
  actualDemandValue: number;
  forecastP50Value?: number | null;
  residualZScore?: number | null;
  percentAboveForecast?: number | null;
  candidateStatus: string;
  confirmationOutcome?: string | null;
  isSelectedAlert: boolean;
};

export type AlertAnomaliesComponent = {
  status: AlertComponentStatus;
  items: AlertAnomalyContextItem[];
  unavailableReason?: string | null;
  failureReason?: string | null;
};

export type AlertDetail = {
  alertDetailLoadId: string;
  alertSource: AlertSource;
  alertId: string;
  correlationId?: string | null;
  alertTriggeredAt: string;
  overallDeliveryStatus: OverallDeliveryStatus;
  forecastProduct?: 'daily' | 'weekly' | null;
  forecastReferenceId?: string | null;
  forecastWindowType?: 'hourly' | 'daily' | null;
  windowStart: string;
  windowEnd: string;
  primaryMetricLabel: string;
  primaryMetricValue: number;
  secondaryMetricLabel: string;
  secondaryMetricValue: number;
  scope: AlertScope;
  viewStatus: AlertDetailViewStatus;
  failureReason?: string | null;
  distribution: AlertDistributionComponent;
  drivers: AlertDriversComponent;
  anomalies: AlertAnomaliesComponent;
};

export type AlertDetailRenderEvent = {
  renderStatus: 'rendered' | 'render_failed';
  failureReason?: string;
};
