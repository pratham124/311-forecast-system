export type ForecastProduct = 'daily_1_day' | 'weekly_7_day';
export type ViewStatus = 'success' | 'degraded' | 'fallback_shown' | 'unavailable' | 'render_failed';
export type DegradationType = 'history_missing' | 'uncertainty_missing';
export type RenderStatus = 'rendered' | 'render_failed';
export type ForecastConfidenceAssessmentStatus = 'degraded_confirmed' | 'normal' | 'signals_missing' | 'dismissed';
export type ForecastConfidenceIndicatorState = 'display_required' | 'not_required' | 'render_failed';
export type ForecastConfidenceReasonCategory = 'missing_inputs' | 'anomaly' | 'shock';

export interface CategoryFilter {
  selectedCategory: string | null;
  selectedCategories: string[];
}

export interface ServiceCategoryOptions {
  forecastProduct: ForecastProduct;
  categories: string[];
}

export interface VisualizationPoint {
  timestamp: string;
  value: number;
}

export interface VisualizationForecastPoint {
  timestamp: string;
  pointForecast: number;
}

export interface UncertaintyPoint {
  timestamp: string;
  p10: number;
  p50: number;
  p90: number;
}

export interface UncertaintyBands {
  labels: Array<'P10' | 'P50' | 'P90'>;
  points: UncertaintyPoint[];
}

export interface StatusMessage {
  code: string;
  level: 'info' | 'warning' | 'error';
  message: string;
}

export interface FallbackMetadata {
  snapshotId: string;
  createdAt: string;
  expiresAt: string;
}

export interface ForecastConfidence {
  assessmentStatus: ForecastConfidenceAssessmentStatus;
  indicatorState: ForecastConfidenceIndicatorState;
  reasonCategories: ForecastConfidenceReasonCategory[];
  supportingSignals: string[];
  message: string;
}

export interface ForecastVisualization {
  visualizationLoadId: string;
  forecastProduct: ForecastProduct;
  forecastGranularity: 'hourly' | 'daily';
  categoryFilter: CategoryFilter;
  historyWindowStart: string;
  historyWindowEnd: string;
  forecastWindowStart?: string;
  forecastWindowEnd?: string;
  forecastBoundary?: string;
  lastUpdatedAt?: string;
  sourceCleanedDatasetVersionId?: string;
  sourceForecastVersionId?: string;
  sourceWeeklyForecastVersionId?: string;
  historicalSeries: VisualizationPoint[];
  forecastSeries: VisualizationForecastPoint[];
  uncertaintyBands?: UncertaintyBands;
  alerts: StatusMessage[];
  pipelineStatus: StatusMessage[];
  fallback?: FallbackMetadata;
  forecastConfidence?: ForecastConfidence;
  viewStatus: ViewStatus;
  degradationType?: DegradationType;
  summary?: string;
}

export interface VisualizationRenderEvent {
  renderStatus: RenderStatus;
  failureReason?: string;
}
