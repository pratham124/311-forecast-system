export type ForecastProduct = 'daily_1_day' | 'weekly_7_day';
export type EvaluationTriggerType = 'on_demand';
export type EvaluationRunLifecycleStatus = 'running' | 'success' | 'failed';
export type EvaluationResultType =
  | 'stored_complete'
  | 'stored_partial'
  | 'missing_input_data'
  | 'missing_forecast_output'
  | 'baseline_failure'
  | 'storage_failure';
export type EvaluationComparisonStatus = 'complete' | 'partial';
export type EvaluationSegmentStatus = 'complete' | 'partial';

export type EvaluationRunAccepted = {
  evaluationRunId: string;
  status: 'running';
};

export type EvaluationRunStatus = {
  evaluationRunId: string;
  triggerType: 'scheduled' | 'on_demand';
  forecastProduct: ForecastProduct;
  sourceCleanedDatasetVersionId?: string | null;
  sourceForecastVersionId?: string | null;
  sourceWeeklyForecastVersionId?: string | null;
  evaluationWindowStart: string;
  evaluationWindowEnd: string;
  status: EvaluationRunLifecycleStatus;
  resultType?: EvaluationResultType | null;
  evaluationResultId?: string | null;
  startedAt: string;
  completedAt?: string | null;
  failureReason?: string | null;
  summary?: string | null;
};

export type MetricValue = {
  metricName: 'mae' | 'rmse' | 'mape';
  metricValue?: number | null;
  isExcluded: boolean;
  exclusionReason?: string | null;
};

export type MethodMetricSummary = {
  methodName: string;
  metrics: MetricValue[];
};

export type EvaluationSegment = {
  segmentType: 'overall' | 'service_category' | 'time_period';
  segmentKey: string;
  segmentStatus: EvaluationSegmentStatus;
  comparisonRowCount: number;
  excludedMetricCount: number;
  notes?: string | null;
  methodMetrics: MethodMetricSummary[];
};

export type FairComparisonMetadata = {
  evaluationWindowStart: string;
  evaluationWindowEnd: string;
  productScope: ForecastProduct;
  segmentCoverage: string[];
};

export type CurrentEvaluation = {
  evaluationResultId: string;
  forecastProduct: ForecastProduct;
  sourceCleanedDatasetVersionId?: string | null;
  sourceForecastVersionId?: string | null;
  sourceWeeklyForecastVersionId?: string | null;
  evaluationWindowStart: string;
  evaluationWindowEnd: string;
  comparisonStatus: EvaluationComparisonStatus;
  baselineMethods: string[];
  metricSet: Array<'mae' | 'rmse' | 'mape'>;
  fairComparison: FairComparisonMetadata;
  updatedAt: string;
  updatedByRunId: string;
  summary?: string | null;
  comparisonSummary?: string | null;
  segments: EvaluationSegment[];
};
