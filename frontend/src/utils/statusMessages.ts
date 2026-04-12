import type { DegradationType, ForecastVisualization, StatusMessage } from '../types/forecastVisualization';

const degradationCopy: Record<DegradationType, string> = {
  history_missing: 'Recent history is not available right now, so the chart only shows the forecast.',
  uncertainty_missing: 'The shaded range is not available right now, but the forecast line is still shown.',
};

export function buildStatusSummary(visualization: ForecastVisualization): string {
  if (visualization.viewStatus === 'fallback_shown') {
    return appendConfidenceSummary(
      "You're seeing the most recent saved view because the latest forecast is not available right now.",
      visualization,
    );
  }
  if (visualization.viewStatus === 'unavailable') {
    return visualization.summary ?? "We can't show this forecast right now.";
  }
  if (visualization.degradationType) {
    return degradationCopy[visualization.degradationType];
  }
  return appendConfidenceSummary('This view shows the latest forecast alongside recent demand.', visualization);
}

export function groupStatusMessages(messages: StatusMessage[]): Record<StatusMessage['level'], StatusMessage[]> {
  return messages.reduce(
    (acc, message) => {
      acc[message.level].push(message);
      return acc;
    },
    { info: [], warning: [], error: [] } as Record<StatusMessage['level'], StatusMessage[]>,
  );
}

function appendConfidenceSummary(base: string, visualization: ForecastVisualization): string {
  const confidence = visualization.forecastConfidence;
  if (!confidence) {
    return base;
  }
  if (confidence.assessmentStatus !== 'signals_missing' && confidence.assessmentStatus !== 'dismissed') {
    return base;
  }
  return `${base} ${confidence.message}`;
}
