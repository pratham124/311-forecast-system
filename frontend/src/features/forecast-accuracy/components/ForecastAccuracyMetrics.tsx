import type { ForecastAccuracyMetrics as Metrics } from '../../../types/forecastAccuracy';

export function ForecastAccuracyMetrics({ metrics }: { metrics: Metrics }) {
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <span className="block text-xs uppercase tracking-[0.14em] text-muted">MAE</span>
        <strong className="mt-2 block text-lg text-ink">{metrics.mae.toFixed(4)}</strong>
      </div>
      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <span className="block text-xs uppercase tracking-[0.14em] text-muted">RMSE</span>
        <strong className="mt-2 block text-lg text-ink">{metrics.rmse.toFixed(4)}</strong>
      </div>
      <div className="rounded-2xl border border-slate-200 bg-white p-4">
        <span className="block text-xs uppercase tracking-[0.14em] text-muted">MAPE</span>
        <strong className="mt-2 block text-lg text-ink">{metrics.mape.toFixed(4)}</strong>
      </div>
    </div>
  );
}
