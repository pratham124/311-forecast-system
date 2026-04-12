import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import type { AlertDistributionPoint } from '../../types/alertDetails';

function formatValue(value: unknown): string {
  return typeof value === 'number' ? value.toFixed(1) : String(value ?? '');
}

function formatAxisLabel(value: unknown): string {
  if (typeof value !== 'string') return '';
  try {
    const date = new Date(value);
    if (isNaN(date.getTime())) return value;
    return date.toLocaleString([], {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
    });
  } catch {
    return value;
  }
}

export function AlertDistributionChart({ points }: { points: AlertDistributionPoint[] }) {
  const data = points.map((point) => ({
    ...point,
    marker: point.isAlertedBucket ? point.p50 : null,
  }));

  return (
    <figure className="grid gap-3" aria-labelledby="alert-distribution-chart-title">
      <figcaption id="alert-distribution-chart-title" className="text-sm font-semibold uppercase tracking-[0.18em] text-accent">
        Forecast distribution
      </figcaption>
      <div role="img" aria-label="Alert distribution chart" className="h-[320px] w-full overflow-hidden rounded-[24px] bg-slate-50/90 p-3 shadow-inner">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 12, right: 18, left: 0, bottom: 12 }}>
            <CartesianGrid strokeDasharray="4 4" stroke="#d8e3ee" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fill: '#4b6277', fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              minTickGap={30}
              tickFormatter={formatAxisLabel}
            />
            <YAxis tick={{ fill: '#4b6277', fontSize: 11 }} tickLine={false} axisLine={false} />
            <Tooltip
              labelFormatter={formatAxisLabel}
              formatter={(value, name) => [formatValue(value), String(name ?? '').toUpperCase()]}
              contentStyle={{ borderRadius: 18, border: 'none', boxShadow: '0 20px 50px rgba(15,23,42,0.15)', background: 'rgba(255,255,255,0.96)' }}
            />
            <Area type="monotone" dataKey="p90" stroke="#dbeafe" fill="#dbeafe" fillOpacity={0.28} />
            <Area type="monotone" dataKey="p10" stroke="#ffffff" fill="#ffffff" fillOpacity={1} />
            <Line type="monotone" dataKey="p50" stroke="#005087" strokeWidth={3} dot={{ r: 3, fill: '#005087' }} activeDot={{ r: 5 }} />
            <Line type="monotone" dataKey="marker" stroke="#c2410c" strokeWidth={0} dot={{ r: 6, fill: '#c2410c', stroke: '#fff', strokeWidth: 2 }} activeDot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2 flex flex-wrap gap-x-6 gap-y-3 px-1 text-[11px] font-bold uppercase tracking-wider text-muted/80" aria-label="distribution legend">
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full border-2 border-[#005087] bg-white" />
          <span>P50 forecast</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-8 rounded-sm bg-blue-100" />
          <span>Uncertainty band</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full border-2 border-white bg-[#c2410c]" />
          <span>Alerted bucket</span>
        </div>
      </div>
    </figure>
  );
}
