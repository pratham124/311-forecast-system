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
    return <Alert className="animate-in fade-in slide-in-from-top-4 duration-500"><AlertDescription>Loading historical demand data...</AlertDescription></Alert>;
  }
  if (error) {
    return <Alert variant="destructive" className="animate-in fade-in slide-in-from-top-4 duration-500"><AlertTitle>Historical demand request failed</AlertTitle><AlertDescription>{error}</AlertDescription></Alert>;
  }
  if (response?.warning?.shown && !response.warning.acknowledged) {
    return (
      <Alert className="animate-in fade-in slide-in-from-top-4 duration-500 border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50">
        <AlertTitle className="text-amber-900 font-bold">Large request warning</AlertTitle>
        <AlertDescription className="grid gap-3 text-amber-800">
          <span>{response.warning.message}</span>
          <div className="flex gap-3">
            <button type="button" onClick={onProceed} className="rounded-2xl bg-amber-600 px-4 py-2 text-sm font-bold text-white shadow-sm transition hover:bg-amber-700 hover:scale-105">Proceed</button>
            <button type="button" onClick={onDecline} className="rounded-2xl border border-amber-300 bg-white/50 px-4 py-2 text-sm font-bold text-amber-900 shadow-sm transition hover:bg-white hover:scale-105">Revise filters</button>
          </div>
        </AlertDescription>
      </Alert>
    );
  }
  if (response?.outcomeStatus === 'no_data') {
    return <Alert className="animate-in fade-in slide-in-from-top-4 duration-500"><AlertTitle>No data found</AlertTitle><AlertDescription>{response.message ?? 'No historical demand data matched the selected filters.'}</AlertDescription></Alert>;
  }
  if (response?.outcomeStatus === 'retrieval_failed' || response?.outcomeStatus === 'render_failed') {
    return <Alert variant="destructive" className="animate-in fade-in slide-in-from-top-4 duration-500"><AlertTitle>Historical demand unavailable</AlertTitle><AlertDescription>{response.summary ?? response.message ?? 'We could not display historical demand data.'}</AlertDescription></Alert>;
  }
  return null;
}
