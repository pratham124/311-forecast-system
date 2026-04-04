import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { saveAuthSession } from '../lib/authSession';
import { EvaluationPage } from './EvaluationPage';

const currentEvaluation = {
  evaluationResultId: 'eval-result-1',
  forecastProduct: 'daily_1_day',
  sourceCleanedDatasetVersionId: 'cleaned-1',
  sourceForecastVersionId: 'forecast-1',
  sourceWeeklyForecastVersionId: null,
  evaluationWindowStart: '2026-03-20T00:00:00Z',
  evaluationWindowEnd: '2026-03-20T03:00:00Z',
  comparisonStatus: 'partial',
  baselineMethods: ['seasonal_naive', 'moving_average'],
  metricSet: ['mae', 'rmse', 'mape'],
  fairComparison: {
    evaluationWindowStart: '2026-03-20T00:00:00Z',
    evaluationWindowEnd: '2026-03-20T03:00:00Z',
    productScope: 'daily_1_day',
    segmentCoverage: ['overall', 'Roads'],
  },
  updatedAt: '2026-03-25T10:05:00Z',
  updatedByRunId: 'eval-run-1',
  summary: 'Evaluation stored for daily_1_day across 6 comparison rows',
  comparisonSummary: 'The forecasting engine matched the strongest included baseline for the evaluated scope.',
  segments: [
    {
      segmentType: 'overall',
      segmentKey: 'overall',
      segmentStatus: 'partial',
      comparisonRowCount: 6,
      excludedMetricCount: 3,
      notes: 'Some metrics were excluded because one or more comparison rows had zero actual demand.',
      methodMetrics: [
        {
          methodName: 'Forecast Engine',
          metrics: [
            { metricName: 'mae', metricValue: 1, isExcluded: false },
            { metricName: 'rmse', metricValue: 1.118, isExcluded: false },
            { metricName: 'mape', metricValue: null, isExcluded: true, exclusionReason: 'MAPE cannot be computed when actual demand includes zero values' },
          ],
        },
      ],
    },
  ],
};

describe('EvaluationPage', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    saveAuthSession({
      accessToken: 'token-1',
      user: { userAccountId: 'user-1', email: 'planner@example.com', roles: ['CityPlanner'] },
    });
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    window.localStorage.clear();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('loads the current evaluation for planner access and hides the trigger button', async () => {
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify(currentEvaluation), { status: 200 }));

    render(<EvaluationPage roles={['CityPlanner']} />);

    expect(await screen.findByText(/current official evaluation/i)).toBeInTheDocument();
    expect(screen.getByText(/matched the strongest included baseline/i)).toBeInTheDocument();
    expect(screen.queryByText(/current sources/i)).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /trigger daily evaluation/i })).not.toBeInTheDocument();
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/v1/evaluations/current?forecastProduct=daily_1_day');
  });

  it('triggers a run for operational managers, polls status, and refreshes the current evaluation', async () => {
    const user = userEvent.setup();
    fetchMock
      .mockResolvedValueOnce(new Response('null', { status: 404 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ evaluationRunId: 'eval-run-2', status: 'running' }), { status: 202 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        evaluationRunId: 'eval-run-2',
        triggerType: 'on_demand',
        forecastProduct: 'daily_1_day',
        evaluationWindowStart: '2026-03-20T00:00:00Z',
        evaluationWindowEnd: '2026-03-20T03:00:00Z',
        status: 'success',
        resultType: 'stored_partial',
        evaluationResultId: 'eval-result-1',
        startedAt: '2026-03-25T10:00:00Z',
        completedAt: '2026-03-25T10:05:00Z',
        summary: 'Evaluation stored for daily_1_day across 6 comparison rows',
      }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(currentEvaluation), { status: 200 }));

    render(<EvaluationPage roles={['OperationalManager']} />);
    expect(await screen.findByText(/no current evaluation yet/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /trigger daily evaluation/i }));

    await waitFor(() => {
      expect(screen.getByText(/latest run status/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/stored partial/i)).toBeInTheDocument();
    expect(screen.getByText(/current official evaluation/i)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(4);
    expect(String(fetchMock.mock.calls[1][0])).toContain('/api/v1/evaluation-runs/trigger');
    expect(String(fetchMock.mock.calls[2][0])).toContain('/api/v1/evaluation-runs/eval-run-2');
  });
});
