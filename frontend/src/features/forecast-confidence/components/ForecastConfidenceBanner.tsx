import { useEffect } from 'react';
import { Alert, AlertDescription, AlertTitle } from '../../../components/ui/alert';
import type { ForecastConfidence } from '../../../types/forecastVisualization';

interface ForecastConfidenceBannerProps {
  confidence: ForecastConfidence;
  onRendered?: () => void;
}

export function ForecastConfidenceBanner({ confidence, onRendered }: ForecastConfidenceBannerProps) {
  useEffect(() => {
    onRendered?.();
  }, [onRendered]);

  return (
    <Alert
      aria-label="forecast confidence banner"
      className="mt-5 border-amber-300 bg-amber-50 text-amber-950"
    >
      <AlertTitle>Forecast confidence is reduced</AlertTitle>
      <AlertDescription>{confidence.message}</AlertDescription>
    </Alert>
  );
}
