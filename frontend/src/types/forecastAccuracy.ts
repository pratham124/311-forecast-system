export type ForecastAccuracyViewStatus =
  | 'rendered_with_metrics'
  | 'rendered_without_metrics'
  | 'unavailable'
  | 'error';

export type ForecastAccuracyMetricResolutionStatus =
  | 'retrieved_precomputed'
  | 'computed_on_demand'
  | 'unavailable'
  | 'failed';

export type ForecastAccuracyFilters = {
  timeRangeStart?: string;
  timeRangeEnd?: string;
  serviceCategory?: string;
};

export type ForecastAccuracyMetrics = {
  mae: number;
  rmse: number;
  mape: number;
};

export type ForecastAccuracyAlignedBucket = {
  bucketStart: string;
  bucketEnd: string;
  serviceCategory?: string | null;
  forecastValue: number;
  actualValue: number;
  absoluteErrorValue: number;
  percentageErrorValue?: number | null;
};

export type ForecastAccuracyResponse = {
  forecastAccuracyRequestId: string;
  forecastAccuracyResultId: string;
  correlationId?: string | null;
  timeRangeStart: string;
  timeRangeEnd: string;
  serviceCategory?: string | null;
  forecastProductName: 'daily_1_day';
  comparisonGranularity: 'hourly' | 'daily';
  viewStatus: ForecastAccuracyViewStatus;
  metricResolutionStatus?: ForecastAccuracyMetricResolutionStatus | null;
  statusMessage?: string | null;
  metrics?: ForecastAccuracyMetrics | null;
  alignedBuckets: ForecastAccuracyAlignedBucket[];
};

export type ForecastAccuracyRenderEvent = {
  renderStatus: 'rendered' | 'render_failed';
  failureReason?: string;
};

export type ForecastAccuracyRenderEventResponse = {
  forecastAccuracyRequestId: string;
  recordedOutcomeStatus: 'rendered' | 'render_failed';
  message: string;
};
