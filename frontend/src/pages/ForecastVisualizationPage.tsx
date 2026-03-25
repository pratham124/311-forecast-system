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

export function ForecastVisualizationPage() {
  const [openDropdown, setOpenDropdown] = useState<'timeRange' | 'serviceAreas' | null>(null);
  const timeRangeRef = useRef<HTMLDivElement>(null);
  const serviceAreasRef = useRef<HTMLDivElement>(null);
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

  useEffect(() => {
    if (!openDropdown) return;

    const handlePointerDown = (event: MouseEvent) => {
      const target = event.target;
      if (!(target instanceof Node)) return;
      if (timeRangeRef.current?.contains(target) || serviceAreasRef.current?.contains(target)) return;
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
  };

  return (
    <main className="mx-auto w-full max-w-6xl px-4 pb-14 pt-7 sm:px-6 lg:px-8">
      <Card className="relative z-20 grid gap-6 rounded-[28px] p-1 md:grid-cols-[1.6fr_1fr]">
        <CardHeader className="pb-6">
          <p className="mb-3 mt-0 text-xs uppercase tracking-[0.18em] text-accent">311 Forecast Overview</p>
          <CardTitle className="m-0 text-4xl leading-[0.95] text-ink md:text-6xl">
            See expected demand for the next day or week.
          </CardTitle>
          <CardDescription className="mt-4 max-w-2xl text-base leading-7 text-muted">
            Compare the latest forecast with recent request volumes. If some data is missing, this page will explain what is still available.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid content-start gap-4 p-7 pl-6 pt-7">
          <div className="grid gap-2">
            <Label htmlFor="forecast-product">Time range</Label>
            <TimeRangeSelect
              value={forecastProduct}
              onChange={setForecastProduct}
              isOpen={openDropdown === 'timeRange'}
              onOpenChange={(isOpen) => setOpenDropdown(isOpen ? 'timeRange' : null)}
              containerRef={timeRangeRef}
            />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="service-category">Service areas</Label>
            <ServiceAreaMultiSelect
              options={serviceCategoryOptions}
              selectedValues={serviceCategories}
              onChange={setServiceCategories}
              isOpen={openDropdown === 'serviceAreas'}
              onOpenChange={(isOpen) => setOpenDropdown(isOpen ? 'serviceAreas' : null)}
              containerRef={serviceAreasRef}
            />
          </div>
        </CardContent>
      </Card>

      {isLoading ? <Alert className="mt-5"><AlertDescription>Loading the forecast...</AlertDescription></Alert> : null}
      {error ? <Alert variant="destructive" className="mt-5"><AlertDescription>{error}</AlertDescription></Alert> : null}

      {visualization ? (
        <>
          {visualization.fallback ? <VisualizationFallbackBanner fallback={visualization.fallback} /> : null}
          <section className="mt-5 grid gap-4 md:grid-cols-3">
            <Card className="rounded-[22px]">
              <CardContent className="p-5">
                <span className="block text-sm text-muted">Updated</span>
                <strong className="mt-2 block text-lg text-ink">{visualization.lastUpdatedAt ? new Date(visualization.lastUpdatedAt).toLocaleString() : 'Not available'}</strong>
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
              <ForecastVisualizationChart visualization={visualization} />
            </ChartErrorBoundary>
          )}
        </>
      ) : null}
    </main>
  );
}
