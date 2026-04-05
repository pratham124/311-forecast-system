export type PublicForecastStatus = 'available' | 'unavailable' | 'error';
export type PublicForecastCoverageStatus = 'complete' | 'incomplete';
export type PublicForecastSanitizationStatus = 'passed_as_is' | 'sanitized' | 'blocked' | 'failed';
export type PublicForecastDisplayOutcome = 'rendered' | 'render_failed';

export type PublicForecastCategorySummary = {
  serviceCategory: string;
  forecastDemandValue?: number | null;
  demandLevelSummary?: string | null;
};

export type PublicForecastView = {
  publicForecastRequestId: string;
  status: PublicForecastStatus;
  forecastWindowLabel?: string | null;
  publishedAt?: string | null;
  coverageStatus?: PublicForecastCoverageStatus | null;
  coverageMessage?: string | null;
  sanitizationStatus?: PublicForecastSanitizationStatus | null;
  sanitizationSummary?: string | null;
  categorySummaries?: PublicForecastCategorySummary[] | null;
  statusMessage?: string | null;
  clientCorrelationId?: string | null;
};

export type PublicForecastDisplayEventRequest = {
  displayOutcome: PublicForecastDisplayOutcome;
  failureReason?: string | null;
};
