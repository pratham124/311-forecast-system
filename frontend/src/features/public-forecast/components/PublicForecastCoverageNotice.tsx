import { Alert, AlertDescription, AlertTitle } from '../../../components/ui/alert';

type PublicForecastCoverageNoticeProps = {
  coverageMessage?: string | null;
  sanitizationSummary?: string | null;
};

export function PublicForecastCoverageNotice({ coverageMessage, sanitizationSummary }: PublicForecastCoverageNoticeProps) {
  if (!coverageMessage && !sanitizationSummary) {
    return null;
  }

  return (
    <Alert className="mt-6 rounded-[24px] border-amber-200 bg-amber-50 text-amber-950">
      <AlertTitle>Public forecast notes</AlertTitle>
      <AlertDescription className="space-y-2">
        {coverageMessage ? <p>{coverageMessage}</p> : null}
        {sanitizationSummary ? <p>{sanitizationSummary}</p> : null}
      </AlertDescription>
    </Alert>
  );
}
