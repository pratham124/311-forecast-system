export function ForecastAccuracyUnavailable({ message }: { message: string }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-muted">
      {message}
    </div>
  );
}
