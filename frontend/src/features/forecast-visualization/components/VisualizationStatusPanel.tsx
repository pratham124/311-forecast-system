import { Card, CardContent } from '../../../components/ui/card';
import type { ForecastVisualization, StatusMessage } from '../../../types/forecastVisualization';
import { buildStatusSummary, groupStatusMessages } from '../../../utils/statusMessages';

interface VisualizationStatusPanelProps {
  visualization: ForecastVisualization;
}

const sectionTitles: Record<StatusMessage['level'], string> = {
  info: 'Good to know',
  warning: 'Needs attention',
  error: 'Issues',
};

const emptyCopy: Record<StatusMessage['level'], string> = {
  info: 'No extra notes right now.',
  warning: 'No warnings right now.',
  error: 'No issues right now.',
};

export function VisualizationStatusPanel({ visualization }: VisualizationStatusPanelProps) {
  const grouped = groupStatusMessages([...visualization.alerts, ...visualization.pipelineStatus]);

  return (
    <Card className="mt-5 rounded-[28px] p-6" aria-label="visualization status">
      <p className="m-0 text-base text-ink">{buildStatusSummary(visualization)}</p>
      <div className="mt-4 grid gap-4 md:grid-cols-3">
        {(['info', 'warning', 'error'] as const).map((level) => (
          <Card
            key={level}
            tone="muted"
            className={`rounded-3xl ${level === 'info' ? 'border-l-4 border-accent' : ''} ${level === 'warning' ? 'border-l-4 border-amber-700' : ''} ${level === 'error' ? 'border-l-4 border-red-700' : ''}`}
          >
            <CardContent className="p-4">
              <h3 className="m-0 text-sm font-semibold uppercase tracking-[0.16em] text-muted">{sectionTitles[level]}</h3>
              {grouped[level].length === 0 ? <p className="mb-0 mt-3 text-sm text-muted">{emptyCopy[level]}</p> : null}
              {grouped[level].map((message) => (
                <p key={`${level}-${message.code}`} className="mb-0 mt-3 text-sm text-muted">
                  {message.message}
                </p>
              ))}
            </CardContent>
          </Card>
        ))}
      </div>
    </Card>
  );
}
