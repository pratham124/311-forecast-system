import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AlertReviewPage } from '../src/pages/AlertReviewPage';

describe('AlertReviewPage surge panel', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('renders surge evaluation and event details', async () => {
    const user = userEvent.setup();
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [] }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ items: [] }), { status: 200 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            items: [
              {
                surgeEvaluationRunId: 'run-1',
                ingestionRunId: 'ingestion-1',
                triggerSource: 'ingestion_completion',
                status: 'completed_with_failures',
                evaluatedScopeCount: 1,
                candidateCount: 1,
                confirmedCount: 0,
                notificationCreatedCount: 0,
                startedAt: '2026-04-01T10:05:00Z',
                completedAt: '2026-04-01T10:06:00Z',
                failureSummary: 'Roads: insufficient historical observations',
              },
            ],
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            items: [
              {
                surgeNotificationEventId: 'event-1',
                surgeEvaluationRunId: 'run-2',
                surgeCandidateId: 'candidate-2',
                serviceCategory: 'Waste',
                evaluationWindowStart: '2026-04-01T11:00:00Z',
                evaluationWindowEnd: '2026-04-01T12:00:00Z',
                actualDemandValue: 6,
                forecastP50Value: 2,
                residualValue: 4,
                residualZScore: 4.5,
                percentAboveForecast: 200,
                overallDeliveryStatus: 'partial_delivery',
                createdAt: '2026-04-01T11:05:00Z',
              },
            ],
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            surgeEvaluationRunId: 'run-1',
            ingestionRunId: 'ingestion-1',
            triggerSource: 'ingestion_completion',
            status: 'completed_with_failures',
            evaluatedScopeCount: 1,
            candidateCount: 1,
            confirmedCount: 0,
            notificationCreatedCount: 0,
            startedAt: '2026-04-01T10:05:00Z',
            completedAt: '2026-04-01T10:06:00Z',
            failureSummary: 'Roads: insufficient historical observations',
            candidates: [
              {
                surgeCandidateId: 'candidate-1',
                serviceCategory: 'Roads',
                evaluationWindowStart: '2026-04-01T10:00:00Z',
                evaluationWindowEnd: '2026-04-01T11:00:00Z',
                actualDemandValue: 5,
                forecastP50Value: 2,
                residualValue: null,
                residualZScore: null,
                percentAboveForecast: null,
                rollingBaselineMean: null,
                rollingBaselineStddev: null,
                candidateStatus: 'detector_failed',
                detectedAt: '2026-04-01T10:05:00Z',
                failureReason: 'Insufficient historical observations for surge baseline',
                confirmation: {
                  surgeConfirmationOutcomeId: 'confirmation-1',
                  outcome: 'failed',
                  confirmedAt: '2026-04-01T10:05:01Z',
                  failureReason: 'Insufficient historical observations for surge baseline',
                },
              },
            ],
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            surgeNotificationEventId: 'event-1',
            surgeEvaluationRunId: 'run-2',
            surgeCandidateId: 'candidate-2',
            surgeDetectionConfigurationId: 'config-1',
            serviceCategory: 'Waste',
            evaluationWindowStart: '2026-04-01T11:00:00Z',
            evaluationWindowEnd: '2026-04-01T12:00:00Z',
            actualDemandValue: 6,
            forecastP50Value: 2,
            residualValue: 4,
            residualZScore: 4.5,
            percentAboveForecast: 200,
            overallDeliveryStatus: 'partial_delivery',
            createdAt: '2026-04-01T11:05:00Z',
            followUpReason: 'One or more channels failed',
            channelAttempts: [
              { channelType: 'email', attemptNumber: 1, status: 'succeeded', attemptedAt: '2026-04-01T11:05:01Z' },
              { channelType: 'sms', attemptNumber: 2, status: 'failed', attemptedAt: '2026-04-01T11:05:02Z', failureReason: 'gateway timeout' },
            ],
          }),
          { status: 200 },
        ),
      );

    render(<AlertReviewPage roles={['OperationalManager']} />);

    await user.click(screen.getByRole('button', { name: /surge alerts/i }));

    expect(await screen.findByText(/review surge evaluations and notifications/i)).toBeInTheDocument();
    expect((await screen.findAllByText(/roads: insufficient historical observations/i)).length).toBeGreaterThan(0);
    expect((await screen.findAllByText(/partial delivery/i)).length).toBeGreaterThan(0);
    expect(await screen.findByText(/gateway timeout/i)).toBeInTheDocument();
    expect((await screen.findAllByText(/evaluation started/i)).length).toBeGreaterThan(0);
    expect(screen.queryByText('ingestion-1')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /run surge evaluation/i })).not.toBeInTheDocument();
    expect(screen.queryByLabelText(/ingestion run id/i)).not.toBeInTheDocument();
  });
});
