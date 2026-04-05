import { Alert, AlertDescription } from '../../../components/ui/alert';

export function PublicForecastLoadingState() {
  return (
    <Alert className="mt-6 rounded-[24px] border-slate-200 bg-white/90">
      <AlertDescription>Loading the current public forecast...</AlertDescription>
    </Alert>
  );
}
