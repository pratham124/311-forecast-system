export function ForecastAccuracyMetricsUnavailable({ message }: { message: string }) {
  return (
    <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
      {message}
    </div>
  );
}
