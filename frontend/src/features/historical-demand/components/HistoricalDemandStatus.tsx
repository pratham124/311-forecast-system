import { Alert, AlertDescription, AlertTitle } from '../../../components/ui/alert';
import type { HistoricalDemandResponse } from '../../../types/historicalDemand';

type HistoricalDemandStatusProps = {
  isLoading: boolean;
  error: string | null;
  response: HistoricalDemandResponse | null;
  onProceed: () => void;
  onDecline: () => void;
};

export function HistoricalDemandStatus({ isLoading, error, response, onProceed, onDecline }: HistoricalDemandStatusProps) {
  if (isLoading) {
    return <Alert><AlertDescription>Loading historical demand data...</AlertDescription></Alert>;
  }
  if (error) {
    return <Alert variant="destructive"><AlertTitle>Historical demand request failed</AlertTitle><AlertDescription>{error}</AlertDescription></Alert>;
  }
  if (response?.warning?.shown && !response.warning.acknowledged) {
    return (
      <Alert>
        <AlertTitle>Large request warning</AlertTitle>
        <AlertDescription className="grid gap-3">
          <span>{response.warning.message}</span>
          <div className="flex gap-3">
            <button type="button" onClick={onProceed} className="rounded-2xl bg-accent px-4 py-2 text-sm font-semibold text-white">Proceed</button>
            <button type="button" onClick={onDecline} className="rounded-2xl border border-slate-300 px-4 py-2 text-sm font-semibold text-ink">Revise filters</button>
          </div>
        </AlertDescription>
      </Alert>
    );
  }
  if (response?.outcomeStatus === 'no_data') {
    return <Alert><AlertTitle>No data found</AlertTitle><AlertDescription>{response.message ?? 'No historical demand data matched the selected filters.'}</AlertDescription></Alert>;
  }
  if (response?.outcomeStatus === 'retrieval_failed' || response?.outcomeStatus === 'render_failed') {
    return <Alert variant="destructive"><AlertTitle>Historical demand unavailable</AlertTitle><AlertDescription>{response.summary ?? response.message ?? 'We could not display historical demand data.'}</AlertDescription></Alert>;
  }
  return null;
}
