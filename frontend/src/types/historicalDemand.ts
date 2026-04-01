export type HistoricalOutcomeStatus = 'success' | 'no_data' | 'retrieval_failed' | 'render_failed';
export type HistoricalAggregationGranularity = 'daily' | 'weekly' | 'monthly';
export type HistoricalResultMode = 'chart' | 'table' | 'chart_and_table';
export type HistoricalRenderStatus = 'rendered' | 'render_failed';

export interface HistoricalDemandContext {
  serviceCategories: string[];
  supportedGeographyLevels: string[];
  summary?: string;
}

export interface HistoricalDemandFilters {
  serviceCategory?: string;
  timeRangeStart: string;
  timeRangeEnd: string;
  geographyLevel?: string;
  geographyValue?: string;
}

export interface HighVolumeWarning {
  shown: boolean;
  acknowledged: boolean;
  message?: string;
}

export interface HistoricalDemandSummaryPoint {
  bucketStart: string;
  bucketEnd: string;
  serviceCategory: string;
  geographyKey?: string;
  demandCount: number;
}

export interface HistoricalDemandResponse {
  analysisRequestId: string;
  filters: HistoricalDemandFilters;
  warning?: HighVolumeWarning;
  aggregationGranularity?: HistoricalAggregationGranularity;
  resultMode?: HistoricalResultMode;
  summaryPoints: HistoricalDemandSummaryPoint[];
  outcomeStatus: HistoricalOutcomeStatus;
  message?: string;
  summary?: string;
}

export interface HistoricalDemandRenderEvent {
  renderStatus: HistoricalRenderStatus;
  failureReason?: string;
}
