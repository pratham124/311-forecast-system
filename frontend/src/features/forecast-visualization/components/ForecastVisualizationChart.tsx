import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { ForecastVisualization } from '../../../types/forecastVisualization';
import type { WeatherOverlayResponse } from '../../../types/weatherOverlay';

type ChartDatum = {
  timestamp: string;
  label: string;
  history?: number;
  forecast?: number;
  p10?: number;
  p90?: number;
  overlay?: number;
};

interface ForecastVisualizationChartProps {
  visualization: ForecastVisualization;
  overlay?: WeatherOverlayResponse | null;
}

export function formatTick(timestamp: string, granularity: ForecastVisualization['forecastGranularity']): string {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return timestamp;
  return granularity === 'hourly'
    ? date.toLocaleString('en-CA', { month: 'short', day: 'numeric', hour: 'numeric' })
    : date.toLocaleDateString('en-CA', { month: 'short', day: 'numeric' });
}

export function formatTooltipLabel(label: unknown): string {
  return typeof label === 'string' ? label : 'Chart point';
}

export function buildChartData(visualization: ForecastVisualization, overlay?: WeatherOverlayResponse | null): ChartDatum[] {
  const byTimestamp = new Map<string, ChartDatum>();

  for (const point of visualization.historicalSeries) {
    byTimestamp.set(point.timestamp, {
      ...(byTimestamp.get(point.timestamp) ?? {
        timestamp: point.timestamp,
        label: formatTick(point.timestamp, visualization.forecastGranularity),
      }),
      history: point.value,
    });
  }

  for (const point of visualization.forecastSeries) {
    byTimestamp.set(point.timestamp, {
      ...(byTimestamp.get(point.timestamp) ?? {
        timestamp: point.timestamp,
        label: formatTick(point.timestamp, visualization.forecastGranularity),
      }),
      forecast: point.pointForecast,
    });
  }

  for (const point of visualization.uncertaintyBands?.points ?? []) {
    byTimestamp.set(point.timestamp, {
      ...(byTimestamp.get(point.timestamp) ?? {
        timestamp: point.timestamp,
        label: formatTick(point.timestamp, visualization.forecastGranularity),
      }),
      p10: point.p10,
      p90: point.p90,
    });
  }

  if (overlay && overlay.overlayStatus === 'visible') {
    for (const point of overlay.observations) {
      byTimestamp.set(point.timestamp, {
        ...(byTimestamp.get(point.timestamp) ?? {
          timestamp: point.timestamp,
          label: formatTick(point.timestamp, visualization.forecastGranularity),
        }),
        overlay: point.value,
      });
    }
  }

  return Array.from(byTimestamp.values()).sort((left, right) => left.timestamp.localeCompare(right.timestamp));
}

export function ForecastVisualizationChart({ visualization, overlay }: ForecastVisualizationChartProps) {
  const data = buildChartData(visualization, overlay);

  return (
    <figure className="glass-panel mt-5 rounded-[28px] p-6" aria-labelledby="chart-title">
      <figcaption id="chart-title" className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-accent">
        Forecast and recent demand
      </figcaption>
      <div role="img" aria-label="Demand forecast chart" className="h-[360px] w-full overflow-hidden rounded-[24px] bg-white/70 p-3">
        <ResponsiveContainer width="100%" height="100%" minWidth={320} minHeight={320}>
          <ComposedChart data={data} margin={{ top: 20, right: 16, bottom: 20, left: 35 }}>
            <CartesianGrid stroke="rgba(25,58,90,0.12)" strokeDasharray="4 4" vertical={false} />
            <XAxis
              dataKey="label"
              minTickGap={28}
              tick={{ fill: '#5a6172', fontSize: 12 }}
              axisLine={{ stroke: 'rgba(25,58,90,0.2)' }}
              tickLine={{ stroke: 'rgba(25,58,90,0.2)' }}
            />
            <YAxis
              yAxisId="left"
              tick={{ fill: '#5a6172', fontSize: 12 }}
              axisLine={false}
              tickLine={false}
              allowDecimals={false}
              width={35}
              label={{ value: '# of 311 Requests', angle: -90, position: 'insideLeft', offset: -10, fill: '#193A5A', fontSize: 13, fontWeight: 600 }}
            />
            {overlay && overlay.overlayStatus === 'visible' ? (
              <YAxis
                yAxisId="right"
                orientation="right"
                tick={{ fill: '#0369a1', fontSize: 12 }} // sky-700
                axisLine={false}
                tickLine={false}
                allowDecimals={false}
                width={40}
                domain={['auto', 'auto']}
              />
            ) : null}
            <Tooltip
              labelFormatter={formatTooltipLabel}
              contentStyle={{
                borderRadius: '16px',
                border: '1px solid rgba(25,58,90,0.14)',
                backgroundColor: 'rgba(255,255,255,0.96)',
                boxShadow: '0 20px 40px rgba(0,80,135,0.12)',
              }}
            />
            {visualization.forecastBoundary ? (
              <ReferenceLine
                x={formatTick(visualization.forecastBoundary, visualization.forecastGranularity)}
                stroke="#005087"
                strokeDasharray="8 8"
              />
            ) : null}
            <Area
              type="monotone"
              dataKey="p90"
              stroke="transparent"
              fill="rgba(244, 208, 67, 0.3)"
              connectNulls
              legendType="none"
              activeDot={false}
            />
            <Area
              type="monotone"
              dataKey="p10"
              stroke="transparent"
              fill="rgba(255, 255, 255, 0.95)"
              connectNulls
              legendType="none"
              activeDot={false}
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="history"
              stroke="#193A5A"
              strokeWidth={3}
              dot={false}
              connectNulls
              isAnimationActive={false}
            />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="forecast"
              stroke="#0081BC"
              strokeWidth={3}
              dot={false}
              connectNulls
              isAnimationActive={false}
            />
            {overlay && overlay.overlayStatus === 'visible' ? (
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="overlay"
                stroke="#38bdf8"
                strokeWidth={2}
                dot={false}
                opacity={0.8}
                connectNulls
                isAnimationActive={false}
              />
            ) : null}
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 flex flex-wrap gap-4 text-sm text-muted" aria-label="chart legend">
        <span><i className="mr-2 inline-block h-3.5 w-3.5 rounded-full bg-history align-middle" />Recent demand</span>
        <span><i className="mr-2 inline-block h-3.5 w-3.5 rounded-full bg-forecast align-middle" />Forecast</span>
        <span><i className="mr-2 inline-block h-3.5 w-3.5 rounded-full border border-forecast bg-[rgba(217,95,2,0.2)] align-middle" />Range</span>
        {overlay && overlay.overlayStatus === 'visible' ? (
          <span><i className="mr-2 inline-block h-3.5 w-3.5 rounded-full bg-sky-400 align-middle" /><span className="capitalize">{overlay.weatherMeasure}</span> ({overlay.measurementUnit})</span>
        ) : null}
      </div>
    </figure>
  );
}
