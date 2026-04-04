import { Alert, AlertDescription } from '../../../components/ui/alert';
import type { DemandComparisonResponse } from '../../../types/demandComparisons';

interface ComparisonOutcomeStateProps {
  error: string | null;
  isLoading: boolean;
  response: DemandComparisonResponse | null;
  onProceed: () => void;
  onDecline: () => void;
}

export function ComparisonOutcomeState({ error, isLoading, response, onProceed, onDecline }: ComparisonOutcomeStateProps) {
  if (isLoading) {
    return <Alert><AlertDescription>Loading comparison options...</AlertDescription></Alert>;
  }
  if (error) {
    return <Alert><AlertDescription>{error}</AlertDescription></Alert>;
  }
  if (!response) {
    return null;
  }
  if (response.outcomeStatus === 'warning_required') {
    return (
      <Alert>
        <AlertDescription>
          <div className="grid gap-3">
            <p className="font-semibold">Large request warning</p>
            <p>{response.message}</p>
            <div className="flex gap-2">
              <button type="button" onClick={onProceed} className="rounded-2xl bg-accent px-4 py-2 text-sm font-semibold text-white">Proceed</button>
              <button type="button" onClick={onDecline} className="rounded-2xl border border-slate-300 px-4 py-2 text-sm font-semibold text-ink">Revise filters</button>
            </div>
          </div>
        </AlertDescription>
      </Alert>
    );
  }
  if (response.outcomeStatus === 'historical_retrieval_failed' || response.outcomeStatus === 'forecast_retrieval_failed' || response.outcomeStatus === 'alignment_failed') {
    return <Alert><AlertDescription>{response.message}</AlertDescription></Alert>;
  }
  return (
    <Alert>
      <AlertDescription>{response.message}</AlertDescription>
    </Alert>
  );
}
