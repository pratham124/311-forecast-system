import { Card, CardContent } from '../../../components/ui/card';
import type { FallbackMetadata } from '../../../types/forecastVisualization';

interface VisualizationFallbackBannerProps {
  fallback: FallbackMetadata;
}

export function VisualizationFallbackBanner({ fallback }: VisualizationFallbackBannerProps) {
  return (
    <Card
      tone="accent"
      className="mt-5 rounded-[28px] bg-[linear-gradient(135deg,rgba(0,80,135,0.14),rgba(244,208,67,0.2),rgba(225,133,62,0.12))]"
      aria-label="fallback snapshot banner"
    >
      <CardContent className="p-5">
        <p className="m-0 text-sm font-medium text-ink">You&apos;re seeing the most recent saved view while the latest forecast is unavailable.</p>
        <p className="mb-0 mt-2 text-sm text-muted">
          Saved {new Date(fallback.createdAt).toLocaleString()} and available until {new Date(fallback.expiresAt).toLocaleString()}.
        </p>
      </CardContent>
    </Card>
  );
}
