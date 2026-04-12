import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../../api/surgeAlerts', () => ({
  fetchSurgeEvaluation: vi.fn(),
  fetchSurgeEvaluations: vi.fn(),
  fetchSurgeEvent: vi.fn(),
  fetchSurgeEvents: vi.fn(),
}));

import {
  fetchSurgeEvaluation,
  fetchSurgeEvaluations,
  fetchSurgeEvent,
  fetchSurgeEvents,
} from '../../../api/surgeAlerts';
import { SurgeAlertReview } from '../surge_alert_review';

describe('SurgeAlertReview extra coverage', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('blocks users without read access', () => {
    render(<SurgeAlertReview roles={['Guest']} />);
    expect(screen.getByText(/does not include surge alert review access/i)).toBeInTheDocument();
  });

  it('renders empty states when no evaluations or events are available', async () => {
    vi.mocked(fetchSurgeEvaluations).mockResolvedValue([]);
    vi.mocked(fetchSurgeEvents).mockResolvedValue([]);

    render(<SurgeAlertReview roles={['CityPlanner']} />);

    expect(await screen.findByText(/no surge evaluations are available yet/i)).toBeInTheDocument();
    expect(screen.getByText(/no surge notification events are available yet/i)).toBeInTheDocument();
    expect(screen.getByText(/select a surge evaluation to inspect detector and confirmation details/i)).toBeInTheDocument();
  });

  it('shows fallback request errors for non-Error values', async () => {
    vi.mocked(fetchSurgeEvaluations).mockRejectedValue('boom');
    vi.mocked(fetchSurgeEvents).mockResolvedValue([]);

    render(<SurgeAlertReview roles={['OperationalManager']} />);

    expect(await screen.findByText(/unable to load surge alerts\./i)).toBeInTheDocument();
  });

  it('loads details, supports reselection, and renders optional fallbacks', async () => {
    const user = userEvent.setup();
    vi.mocked(fetchSurgeEvaluations).mockResolvedValue([
      {
        surgeEvaluationRunId: 'run-1',
        startedAt: '2026-04-01T10:00:00Z',
        status: 'running',
        candidateCount: 1,
        confirmedCount: 0,
      },
      {
        surgeEvaluationRunId: 'run-2',
        startedAt: '2026-04-02T10:00:00Z',
        status: 'completed',
        candidateCount: 2,
        confirmedCount: 1,
      },
    ] as never);
    vi.mocked(fetchSurgeEvents).mockResolvedValue([
      {
        surgeNotificationEventId: 'event-1',
        serviceCategory: 'Roads',
        residualValue: 4,
        residualZScore: 3.1,
        overallDeliveryStatus: 'delivered',
      },
      {
        surgeNotificationEventId: 'event-2',
        serviceCategory: 'Waste',
        residualValue: 5,
        residualZScore: 5.1,
        overallDeliveryStatus: 'manual_review_required',
      },
    ] as never);
    vi.mocked(fetchSurgeEvaluation)
      .mockResolvedValueOnce({
        surgeEvaluationRunId: 'run-1',
        startedAt: '2026-04-01T10:00:00Z',
        status: 'running',
        completedAt: null,
        candidates: [
          {
            surgeCandidateId: 'candidate-1',
            serviceCategory: 'Roads',
            actualDemandValue: 7,
            forecastP50Value: null,
            residualZScore: null,
            percentAboveForecast: null,
            candidateStatus: 'new_candidate',
            confirmation: null,
          },
        ],
      } as never)
      .mockResolvedValueOnce({
        surgeEvaluationRunId: 'run-2',
        startedAt: '2026-04-02T10:00:00Z',
        status: 'completed',
        completedAt: '2026-04-02T10:10:00Z',
        candidates: [],
      } as never);
    vi.mocked(fetchSurgeEvent)
      .mockResolvedValueOnce({
        surgeNotificationEventId: 'event-1',
        serviceCategory: 'Roads',
        residualValue: 4,
        residualZScore: 3.1,
        overallDeliveryStatus: 'delivered',
        createdAt: '2026-04-01T11:00:00Z',
        channelAttempts: [{ channelType: 'email', attemptNumber: 1, status: 'ok' }],
      } as never)
      .mockResolvedValueOnce({
        surgeNotificationEventId: 'event-2',
        serviceCategory: 'Waste',
        residualValue: 5,
        residualZScore: 5.1,
        overallDeliveryStatus: 'manual_review_required',
        createdAt: '2026-04-02T11:00:00Z',
        followUpReason: 'Needs a call',
        channelAttempts: [{ channelType: 'sms', attemptNumber: 2, status: 'failed', failureReason: 'timeout' }],
      } as never);

    render(<SurgeAlertReview roles={['OperationalManager']} />);

    expect(await screen.findByText(/waiting for completion/i)).toBeInTheDocument();
    expect(screen.getAllByText(/^n\/a$/i).length).toBeGreaterThan(0);

    await user.click(screen.getByRole('button', { name: /waste/i }));
    await waitFor(() => {
      expect(fetchSurgeEvent).toHaveBeenCalledWith('event-2');
    });
    expect(await screen.findByText(/needs a call/i)).toBeInTheDocument();
    expect(screen.getByText(/timeout/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /evaluation started apr 2, 2026/i }));
    await waitFor(() => {
      expect(fetchSurgeEvaluation).toHaveBeenCalledWith('run-2');
    });
  });
});
