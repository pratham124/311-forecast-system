import type { ForecastVisualization, UncertaintyPoint, VisualizationForecastPoint, VisualizationPoint } from '../../../types/forecastVisualization';

export interface CartesianPoint {
  x: number;
  y: number;
}

const WIDTH = 960;
const HEIGHT = 420;
const PADDING = { top: 28, right: 28, bottom: 38, left: 56 };

const toMillis = (value: string) => new Date(value).getTime();

export function computeChartGeometry(visualization: ForecastVisualization) {
  const timestamps = [
    ...visualization.historicalSeries.map((point) => toMillis(point.timestamp)),
    ...visualization.forecastSeries.map((point) => toMillis(point.timestamp)),
  ];
  if (timestamps.length === 0) {
    throw new Error('No chart points available to render.');
  }

  const values = [
    ...visualization.historicalSeries.map((point) => point.value),
    ...visualization.forecastSeries.map((point) => point.pointForecast),
    ...(visualization.uncertaintyBands?.points.flatMap((point) => [point.p10, point.p90]) ?? []),
  ];
  const minX = Math.min(...timestamps);
  const maxX = Math.max(...timestamps);
  const maxY = Math.max(...values, 1);
  const innerWidth = WIDTH - PADDING.left - PADDING.right;
  const innerHeight = HEIGHT - PADDING.top - PADDING.bottom;

  const scaleX = (timestamp: number) =>
    PADDING.left + ((timestamp - minX) / Math.max(maxX - minX, 1)) * innerWidth;
  const scaleY = (value: number) => HEIGHT - PADDING.bottom - (value / maxY) * innerHeight;

  return {
    width: WIDTH,
    height: HEIGHT,
    padding: PADDING,
    historyLine: mapSeries(visualization.historicalSeries, scaleX, scaleY),
    forecastLine: mapForecastSeries(visualization.forecastSeries, scaleX, scaleY),
    bandArea: visualization.uncertaintyBands ? mapBandArea(visualization.uncertaintyBands.points, scaleX, scaleY) : '',
    boundaryX: visualization.forecastBoundary ? scaleX(toMillis(visualization.forecastBoundary)) : null,
    axisTicks: buildTicks(minX, maxX, scaleX),
  };
}

function mapSeries(series: VisualizationPoint[], scaleX: (timestamp: number) => number, scaleY: (value: number) => number) {
  return series.map((point) => ({ x: scaleX(toMillis(point.timestamp)), y: scaleY(point.value) }));
}

function mapForecastSeries(series: VisualizationForecastPoint[], scaleX: (timestamp: number) => number, scaleY: (value: number) => number) {
  return series.map((point) => ({ x: scaleX(toMillis(point.timestamp)), y: scaleY(point.pointForecast) }));
}

function mapBandArea(points: UncertaintyPoint[], scaleX: (timestamp: number) => number, scaleY: (value: number) => number) {
  if (points.length === 0) return '';
  const upper = points.map((point) => `${scaleX(toMillis(point.timestamp))},${scaleY(point.p90)}`);
  const lower = [...points]
    .reverse()
    .map((point) => `${scaleX(toMillis(point.timestamp))},${scaleY(point.p10)}`);
  return [...upper, ...lower].join(' ');
}

function buildTicks(minX: number, maxX: number, scaleX: (timestamp: number) => number) {
  const steps = 4;
  return Array.from({ length: steps + 1 }, (_, index) => {
    const time = minX + ((maxX - minX) / steps) * index;
    return { x: scaleX(time), label: new Date(time).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }) };
  });
}

export function linePath(points: CartesianPoint[]) {
  return points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${point.x} ${point.y}`).join(' ');
}
