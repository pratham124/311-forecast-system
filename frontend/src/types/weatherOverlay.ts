export type WeatherMeasure = 'temperature' | 'snowfall' | 'precipitation';
export type WeatherOverlayStatus =
  | 'disabled'
  | 'loading'
  | 'visible'
  | 'unavailable'
  | 'retrieval-failed'
  | 'misaligned'
  | 'superseded'
  | 'failed-to-render';

export interface WeatherObservationPoint {
  timestamp: string;
  value: number;
}

export interface WeatherOverlaySource {
  provider: 'msc_geomet';
  stationId?: string | null;
  alignmentStatus: 'aligned' | 'misaligned' | 'not-applicable';
}

export interface WeatherOverlayResponse {
  overlayRequestId: string;
  geographyId: string;
  matchedGeographyId?: string | null;
  timeRangeStart: string;
  timeRangeEnd: string;
  weatherMeasure?: WeatherMeasure | null;
  measurementUnit?: string;
  overlayStatus: WeatherOverlayStatus;
  statusMessage?: string;
  baseForecastPreserved: true;
  userVisible: true;
  observationGranularity?: 'hourly' | 'daily';
  observations: WeatherObservationPoint[];
  source?: WeatherOverlaySource;
  failureCategory?: 'weather-missing' | 'retrieval-failed' | 'misaligned' | 'failed-to-render' | 'superseded';
  stateSource: 'selection-read-model' | 'overlay-assembly' | 'render-event';
  renderedAt?: string;
}

export interface WeatherOverlayRenderEvent {
  renderStatus: 'rendered' | 'failed-to-render';
  reportedAt: string;
  failureReason?: string;
}
