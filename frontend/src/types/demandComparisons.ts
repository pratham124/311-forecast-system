export interface DateConstraints {
  historicalMin?: string;
  historicalMax?: string;
  forecastMin?: string;
  forecastMax?: string;
  overlapStart?: string;
  overlapEnd?: string;
}

export interface DatePreset {
  label: string;
  timeRangeStart: string;
  timeRangeEnd: string;
}

export interface CategoryGeographyAvailability {
  geographyLevels: string[];
  geographyOptions: Record<string, string[]>;
}

export interface DemandComparisonAvailability {
  serviceCategories: string[];
  byCategoryGeography: Record<string, CategoryGeographyAvailability>;
  dateConstraints: DateConstraints;
  presets: DatePreset[];
  forecastProduct?: string;
  summary?: string;
}

export type DemandComparisonOutcomeStatus =
  | 'warning_required'
  | 'success'
  | 'historical_only'
  | 'forecast_only'
  | 'partial_forecast_missing'
  | 'historical_retrieval_failed'
  | 'forecast_retrieval_failed'
  | 'alignment_failed';

export type DemandComparisonRenderStatus = 'rendered' | 'render_failed';
export type DemandComparisonGranularity = 'hourly' | 'daily' | 'weekly';

export interface DemandComparisonContext {
  serviceCategories: string[];
  geographyLevels: string[];
  geographyOptions: Record<string, string[]>;
  summary?: string;
}

export interface DemandComparisonFilters {
  serviceCategories: string[];
  geographyLevel?: string;
  geographyValues: string[];
  timeRangeStart: string;
  timeRangeEnd: string;
}

export interface HighVolumeWarning {
  shown: boolean;
  acknowledged: boolean;
  message?: string;
}

export interface DemandComparisonPoint {
  bucketStart: string;
  bucketEnd: string;
  value: number;
}

export interface DemandComparisonSeries {
  seriesType: 'historical' | 'forecast';
  serviceCategory: string;
  geographyKey?: string;
  points: DemandComparisonPoint[];
}

export interface MissingCombination {
  serviceCategory: string;
  geographyKey?: string;
  missingSource: 'forecast';
  message: string;
}

export interface DemandComparisonResponse {
  comparisonRequestId: string;
  filters: DemandComparisonFilters;
  outcomeStatus: DemandComparisonOutcomeStatus;
  warning?: HighVolumeWarning;
  resultMode?: 'chart' | 'table' | 'chart_and_table';
  comparisonGranularity?: DemandComparisonGranularity;
  forecastProduct?: 'daily_1_day' | 'weekly_7_day';
  forecastGranularity?: 'hourly' | 'daily';
  sourceCleanedDatasetVersionId?: string;
  sourceForecastVersionId?: string;
  sourceWeeklyForecastVersionId?: string;
  series?: DemandComparisonSeries[];
  missingCombinations?: MissingCombination[];
  message?: string;
  summary?: string;
}

export interface DemandComparisonRenderEvent {
  renderStatus: DemandComparisonRenderStatus;
  failureReason?: string;
}

export interface DemandComparisonRenderEventResponse {
  comparisonRequestId: string;
  recordedOutcomeStatus: DemandComparisonRenderStatus;
  message?: string;
}
