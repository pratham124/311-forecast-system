import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AlertReviewPage } from '../src/pages/AlertReviewPage';

describe('AlertReviewPage', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('lists alert events and supports threshold editing with dropdown fields', async () => {
    const user = userEvent.setup();
    fetchMock
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ items: ['Roads', 'Waste'] }), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            items: [
              {
                thresholdConfigurationId: 'threshold-1',
                serviceCategory: 'Roads',
                forecastWindowType: 'hourly',
                thresholdValue: 8,
                notificationChannels: ['email'],
                operationalManagerId: 'manager-1',
                status: 'active',
                effectiveFrom: '2026-03-19T00:00:00Z',
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
                notificationEventId: 'event-1',
                serviceCategory: 'Roads',
                forecastWindowType: 'hourly',
                forecastWindowStart: '2026-03-20T00:00:00Z',
                forecastWindowEnd: '2026-03-20T01:00:00Z',
                forecastValue: 12,
                thresholdValue: 8,
                overallDeliveryStatus: 'partial_delivery',
                createdAt: '2026-03-20T00:05:00Z',
              },
            ],
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            notificationEventId: 'event-1',
            thresholdEvaluationRunId: 'run-1',
            thresholdConfigurationId: 'config-1',
            serviceCategory: 'Roads',
            forecastWindowType: 'hourly',
            forecastWindowStart: '2026-03-20T00:00:00Z',
            forecastWindowEnd: '2026-03-20T01:00:00Z',
            forecastValue: 12,
            thresholdValue: 8,
            overallDeliveryStatus: 'partial_delivery',
            followUpReason: 'One or more channels failed',
            channelAttempts: [
              { channelType: 'email', attemptNumber: 1, status: 'succeeded', attemptedAt: '2026-03-20T00:05:10Z' },
              { channelType: 'sms', attemptNumber: 2, status: 'failed', failureReason: 'gateway timeout', attemptedAt: '2026-03-20T00:05:11Z' },
            ],
            createdAt: '2026-03-20T00:05:00Z',
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            thresholdConfigurationId: 'threshold-1',
            serviceCategory: 'Waste',
            forecastWindowType: 'daily',
            thresholdValue: 11,
            notificationChannels: ['dashboard'],
            operationalManagerId: 'manager-1',
            status: 'active',
            effectiveFrom: '2026-03-19T00:00:00Z',
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            notificationEventId: 'event-1',
            thresholdEvaluationRunId: 'run-1',
            thresholdConfigurationId: 'config-1',
            serviceCategory: 'Roads',
            forecastWindowType: 'hourly',
            forecastWindowStart: '2026-03-20T00:00:00Z',
            forecastWindowEnd: '2026-03-20T01:00:00Z',
            forecastValue: 12,
            thresholdValue: 8,
            overallDeliveryStatus: 'partial_delivery',
            followUpReason: 'One or more channels failed',
            channelAttempts: [
              { channelType: 'email', attemptNumber: 1, status: 'succeeded', attemptedAt: '2026-03-20T00:05:10Z' },
              { channelType: 'sms', attemptNumber: 2, status: 'failed', failureReason: 'gateway timeout', attemptedAt: '2026-03-20T00:05:11Z' },
            ],
            createdAt: '2026-03-20T00:05:00Z',
          }),
          { status: 200 },
        ),
      );

    render(<AlertReviewPage roles={['OperationalManager']} />);

    expect(await screen.findByText(/set thresholds and review alert outcomes/i)).toBeInTheDocument();
    expect(await screen.findByText(/one or more channels failed/i)).toBeInTheDocument();

    expect(screen.getByRole('button', { name: /service category/i })).toHaveTextContent('Select a category');

    await user.click(screen.getByRole('button', { name: /edit/i }));
    expect(screen.getByRole('button', { name: /service category/i })).toHaveTextContent('Roads');
    expect(screen.getByRole('button', { name: /forecast window/i })).toHaveTextContent('Hourly');

    await user.click(screen.getByRole('button', { name: /service category/i }));
    await user.click(screen.getByRole('button', { name: /^Waste$/i }));

    await user.click(screen.getByRole('button', { name: /forecast window/i }));
    await user.click(screen.getByRole('button', { name: /^Daily$/i }));

    await user.clear(screen.getByLabelText(/threshold value/i));
    await user.type(screen.getByLabelText(/threshold value/i), '11');

    await user.click(screen.getByRole('button', { name: /update threshold/i }));

    expect(await screen.findByText(/^11$/)).toBeInTheDocument();
    expect(screen.getByText(/^Waste$/)).toBeInTheDocument();
    expect(screen.getByText(/◷ daily/i)).toBeInTheDocument();
    expect(screen.queryByText(/inactive/i)).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /delete/i }));
    expect(await screen.findByText(/no thresholds configured yet/i)).toBeInTheDocument();
    expect(screen.queryByText(/^Waste$/)).not.toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /roads partial/i }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(7));
  });
});
