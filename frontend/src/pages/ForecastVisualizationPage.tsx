import { useEffect, useRef, useState } from 'react';
import { Alert, AlertDescription, AlertTitle } from '../components/ui/alert';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Label } from '../components/ui/label';
import { ChartErrorBoundary } from '../features/forecast-visualization/components/ChartErrorBoundary';
import { ForecastVisualizationChart } from '../features/forecast-visualization/components/ForecastVisualizationChart';
import { ServiceAreaMultiSelect } from '../features/forecast-visualization/components/ServiceAreaMultiSelect';
import { TimeRangeSelect } from '../features/forecast-visualization/components/TimeRangeSelect';
import { VisualizationFallbackBanner } from '../features/forecast-visualization/components/VisualizationFallbackBanner';
import { VisualizationStatusPanel } from '../features/forecast-visualization/components/VisualizationStatusPanel';
import { useForecastVisualization } from '../features/forecast-visualization/hooks/useForecastVisualization';
import { WeatherOverlayControls } from '../features/weather-overlay/components/WeatherOverlayControls';
import { WeatherOverlayStatus } from '../features/weather-overlay/components/WeatherOverlayStatus';
import { useWeatherOverlay } from '../features/weather-overlay/hooks/useWeatherOverlay';
import type { WeatherMeasure } from '../types/weatherOverlay';

export function formatUpdatedDateTime(value?: string | null): string {
  if (!value) return 'Not available';
  return new Date(value).toLocaleString([], {
    year: 'numeric',
    month: 'numeric',
    day: 'numeric',
    hour: 'numeric',
  });
}

export function ForecastVisualizationPage() {
  const [openDropdown, setOpenDropdown] = useState<'timeRange' | 'serviceAreas' | 'weatherMeasure' | null>(null);
  const [overlayEnabled, setOverlayEnabled] = useState(false);
  const [weatherMeasure, setWeatherMeasure] = useState<WeatherMeasure>('temperature');
  const timeRangeRef = useRef<HTMLDivElement>(null);
  const serviceAreasRef = useRef<HTMLDivElement>(null);
  const weatherMeasureRef = useRef<HTMLDivElement>(null);
  const {
    forecastProduct,
    setForecastProduct,
    serviceCategories,
    setServiceCategories,
    serviceCategoryOptions,
    visualization,
    isLoading,
    error,
    reportRenderEvent,
  } = useForecastVisualization();
  const overlayWindowStart = visualization?.forecastWindowStart ?? visualization?.historyWindowStart ?? new Date().toISOString();
  const overlayWindowEnd = visualization?.forecastWindowEnd ?? visualization?.historyWindowEnd ?? new Date().toISOString();
  const {
    overlay,
    isLoading: overlayLoading,
    error: overlayError,
    reportRenderSuccess,
    reportRenderFailure,
    clearOverlay,
  } = useWeatherOverlay({
    geographyId: 'citywide',
    timeRangeStart: overlayWindowStart,
    timeRangeEnd: overlayWindowEnd,
    overlayEnabled,
    weatherMeasure,
    requestEnabled: Boolean(visualization) && overlayEnabled,
  });

  useEffect(() => {
    if (!openDropdown) return;

    const handlePointerDown = (event: MouseEvent) => {
      const target = event.target;
      if (!(target instanceof Node)) return;
      if (timeRangeRef.current?.contains(target) || serviceAreasRef.current?.contains(target) || weatherMeasureRef.current?.contains(target)) return;
      setOpenDropdown(null);
    };

    document.addEventListener('mousedown', handlePointerDown);
    return () => document.removeEventListener('mousedown', handlePointerDown);
  }, [openDropdown]);

  useEffect(() => {
    if (!visualization) return;
    if (visualization.viewStatus === 'unavailable') return;
    void reportRenderEvent({ renderStatus: 'rendered' });
  }, [reportRenderEvent, visualization]);

  const handleRenderFailure = (chartError: Error) => {
    void reportRenderEvent({ renderStatus: 'render_failed', failureReason: chartError.message });
    void reportRenderFailure(chartError.message);
  };

  useEffect(() => {
    if (!overlay || overlay.overlayStatus !== 'visible') return;
    void reportRenderSuccess();
  }, [overlay, reportRenderSuccess]);

  return (
    <main className="mx-auto w-full max-w-6xl px-4 pb-14 pt-7 sm:px-6 lg:px-8">
      <Card className="relative z-20 grid gap-4 rounded-[28px] border-white/60 bg-white/85 p-2 shadow-[0_20px_60px_rgba(15,23,42,0.08)] md:grid-cols-[1.65fr_1fr] md:gap-6">
        <CardHeader className="gap-3 px-5 pb-5 pt-5 sm:px-6 sm:pt-6">
          <p className="m-0 text-[11px] font-semibold uppercase tracking-[0.22em] text-accent/80">311 Forecast Overview</p>
          <CardTitle className="m-0 max-w-3xl text-3xl leading-tight text-ink sm:text-4xl md:text-5xl md:leading-[1.02]">
            Expected demand for the next day or week
          </CardTitle>
          <CardDescription className="max-w-2xl text-sm leading-6 text-muted sm:text-[15px]">
            Review the latest forecast beside recent service request volumes.
          </CardDescription>
          <p className="max-w-2xl text-sm leading-6 text-muted">
            When some forecast data is unavailable, this page shows what can still be viewed and explains what is missing.
          </p>
        </CardHeader>
        <CardContent className="grid content-start gap-5 rounded-[24px] bg-slate-50/80 p-5 sm:p-6">
          <div className="space-y-1">
            <p className="text-sm font-semibold text-ink">Adjust the view</p>
            <p className="text-sm leading-6 text-muted">Choose a forecast window and the service areas you want to compare.</p>
          </div>
          <div className="grid gap-2.5">
            <Label htmlFor="forecast-product" className="text-sm font-medium text-ink">Time range</Label>
            <TimeRangeSelect
              value={forecastProduct}
              onChange={setForecastProduct}
              isOpen={openDropdown === 'timeRange'}
              onOpenChange={(isOpen) => setOpenDropdown(isOpen ? 'timeRange' : null)}
              containerRef={timeRangeRef}
            />
          </div>
          <div className="grid gap-2.5">
            <Label htmlFor="service-category" className="text-sm font-medium text-ink">Service areas</Label>
            <ServiceAreaMultiSelect
              options={serviceCategoryOptions}
              selectedValues={serviceCategories}
              onChange={setServiceCategories}
              isOpen={openDropdown === 'serviceAreas'}
              onOpenChange={(isOpen) => setOpenDropdown(isOpen ? 'serviceAreas' : null)}
              containerRef={serviceAreasRef}
            />
          </div>
          <WeatherOverlayControls
            enabled={overlayEnabled}
            selectedMeasure={weatherMeasure}
            onEnabledChange={(next) => {
              setOverlayEnabled(next);
              if (!next) {
                clearOverlay();
              }
            }}
            onMeasureChange={setWeatherMeasure}
            isOpen={openDropdown === 'weatherMeasure'}
            onOpenChange={(isOpen) => setOpenDropdown(isOpen ? 'weatherMeasure' : null)}
            containerRef={weatherMeasureRef}
          />
        </CardContent>
      </Card>

      {isLoading ? <Alert className="mt-5"><AlertDescription>Loading the forecast...</AlertDescription></Alert> : null}
      {error ? <Alert variant="destructive" className="mt-5"><AlertDescription>{error}</AlertDescription></Alert> : null}
      {overlayLoading ? <Alert className="mt-5"><AlertDescription>Loading weather overlay...</AlertDescription></Alert> : null}
      {overlayError ? <Alert variant="destructive" className="mt-5"><AlertDescription>{overlayError}</AlertDescription></Alert> : null}

      {visualization ? (
        <>
          {visualization.fallback ? <VisualizationFallbackBanner fallback={visualization.fallback} /> : null}
          <section className="mt-5 grid gap-4 md:grid-cols-3">
            <Card className="rounded-[22px]">
              <CardContent className="p-5">
                <span className="block text-sm text-muted">Updated</span>
                <strong className="mt-2 block text-lg text-ink">{formatUpdatedDateTime(visualization.lastUpdatedAt)}</strong>
              </CardContent>
            </Card>
            <Card className="rounded-[22px]">
              <CardContent className="p-5">
                <span className="block text-sm text-muted">Recent history shown</span>
                <strong className="mt-2 block text-lg text-ink">
                  {new Date(visualization.historyWindowStart).toLocaleDateString()} to {new Date(visualization.historyWindowEnd).toLocaleDateString()}
                </strong>
              </CardContent>
            </Card>
            <Card className="rounded-[22px]">
              <CardContent className="p-5">
                <span className="block text-sm text-muted">Current view</span>
                <strong className="mt-2 block text-lg capitalize text-ink">{visualization.viewStatus.replace('_', ' ')}</strong>
              </CardContent>
            </Card>
          </section>

          <VisualizationStatusPanel visualization={visualization} />
          <WeatherOverlayStatus overlay={overlay} />

          {visualization.viewStatus === 'unavailable' ? (
            <Alert variant="destructive" className="mt-5">
              <AlertTitle>Forecast view unavailable</AlertTitle>
              <AlertDescription>{visualization.summary ?? "We can't show this forecast right now."}</AlertDescription>
            </Alert>
          ) : (
            <ChartErrorBoundary
              onError={handleRenderFailure}
              fallback={
                <Alert variant="destructive" className="mt-5">
                  <AlertTitle>We couldn't display the chart</AlertTitle>
                  <AlertDescription>Please refresh the page and try again. We've recorded the problem.</AlertDescription>
                </Alert>
              }
            >
              <ForecastVisualizationChart visualization={visualization} overlay={overlay} />
            </ChartErrorBoundary>
          )}
        </>
      ) : null}
    </main>
  );
}
