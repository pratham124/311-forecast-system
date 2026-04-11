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
      <div role="img" aria-label="Alert distribution chart" className="h-[280px] w-full overflow-hidden rounded-[24px] bg-slate-50/90 p-3">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 12, right: 18, left: 0, bottom: 12 }}>
            <CartesianGrid strokeDasharray="4 4" stroke="#d8e3ee" vertical={false} />
            <XAxis dataKey="label" tick={{ fill: '#4b6277', fontSize: 12 }} tickLine={false} axisLine={false} minTickGap={18} />
            <YAxis tick={{ fill: '#4b6277', fontSize: 12 }} tickLine={false} axisLine={false} />
            <Tooltip
              formatter={(value, name) => [formatValue(value), String(name ?? '').toUpperCase()]}
              contentStyle={{ borderRadius: 18, border: '1px solid rgba(25,58,90,0.12)', boxShadow: '0 16px 40px rgba(15,23,42,0.12)' }}
            />
            <Area type="monotone" dataKey="p90" stroke="#dbeafe" fill="#dbeafe" fillOpacity={0.28} />
            <Area type="monotone" dataKey="p10" stroke="#ffffff" fill="#ffffff" fillOpacity={1} />
            <Line type="monotone" dataKey="p50" stroke="#005087" strokeWidth={3} dot={{ r: 3, fill: '#005087' }} activeDot={{ r: 5 }} />
            <Line type="monotone" dataKey="marker" stroke="#c2410c" strokeWidth={0} dot={{ r: 5, fill: '#c2410c' }} activeDot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <div className="flex flex-wrap gap-4 text-sm text-muted" aria-label="distribution legend">
        <span>P50 forecast</span>
        <span>Uncertainty band</span>
        <span>Alerted bucket</span>
      </div>
    </figure>
  );
}
