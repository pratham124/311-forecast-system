import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ForecastAlertsPage } from './ForecastAlertsPage';
import { saveAuthSession } from '../lib/authSession';

describe('ForecastAlertsPage', () => {
  const fetchMock = vi.fn();
  const eventSummary = {
    notificationEventId: 'event-1',
    serviceCategory: 'Roads',
    geographyType: null,
    geographyValue: null,
    forecastWindowType: 'hourly',
    forecastWindowStart: '2026-04-07T10:00:00Z',
    forecastWindowEnd: '2026-04-07T11:00:00Z',
    forecastValue: 42,
    thresholdValue: 20,
    overallDeliveryStatus: 'delivered',
    createdAt: '2026-04-07T09:59:00Z',
  };
  const eventDetail = {
    notificationEventId: 'event-1',
    thresholdEvaluationRunId: 'run-1',
    thresholdConfigurationId: 'cfg-1',
    serviceCategory: 'Roads',
    geographyType: null,
    geographyValue: null,
    forecastWindowType: 'hourly',
    forecastWindowStart: '2026-04-07T10:00:00Z',
    forecastWindowEnd: '2026-04-07T11:00:00Z',
    forecastValue: 42,
    thresholdValue: 20,
    overallDeliveryStatus: 'delivered',
    followUpReason: null,
    createdAt: '2026-04-07T09:59:00Z',
    deliveredAt: '2026-04-07T09:59:02Z',
    failedChannelCount: 0,
    channelAttempts: [
      {
        channelType: 'email',
        attemptNumber: 1,
        attemptedAt: '2026-04-07T09:59:01Z',
        status: 'succeeded',
        failureReason: null,
        providerReference: 'local',
      },
    ],
  };

  const installApiMock = () => {
    fetchMock.mockImplementation((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.includes('/api/v1/forecast-alerts/threshold-configurations') && (init?.method ?? 'GET') === 'GET') {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              items: [
                {
                  thresholdConfigurationId: 'cfg-1',
                  serviceCategory: 'Roads',
                  forecastWindowType: 'daily',
                  thresholdValue: 20,
                  geographyType: null,
                  geographyValue: null,
                  operationalManagerId: 'test-user',
                  status: 'active',
                  effectiveFrom: '2026-04-07T09:00:00Z',
                  effectiveTo: null,
                },
              ],
            }),
            { status: 200 },
          ),
        );
      }
      if (url.endsWith('/api/v1/forecast-alerts/events')) {
        return Promise.resolve(new Response(JSON.stringify({ items: [eventSummary] }), { status: 200 }));
      }
      if (url.endsWith('/api/v1/forecast-alerts/events/event-1')) {
        return Promise.resolve(new Response(JSON.stringify(eventDetail), { status: 200 }));
      }
      if (url.includes('/api/v1/forecast-alerts/threshold-configurations') && init?.method === 'PUT') {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              thresholdConfigurationId: 'cfg-2',
              serviceCategory: 'Roads',
              forecastWindowType: 'daily',
              thresholdValue: 35.0,
              geographyType: null,
              geographyValue: null,
              operationalManagerId: 'test-user',
              status: 'active',
              effectiveFrom: '2026-04-07T10:30:00Z',
              effectiveTo: null,
            }),
            { status: 200 },
          ),
        );
      }
      return Promise.resolve(new Response('{}', { status: 404 }));
    });
  };

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

  it('renders alert list and detail view', async () => {
    installApiMock();

    render(<ForecastAlertsPage roles={['CityPlanner']} />);

    expect(await screen.findByText(/forecast alerts/i)).toBeInTheDocument();
    expect(await screen.findByText(/roads/i)).toBeInTheDocument();
    expect(await screen.findByText(/alert detail/i)).toBeInTheDocument();
    expect(await screen.findByText(/forecast value: 42.00/i)).toBeInTheDocument();
  });

  it('allows operational manager to update threshold from the alerts page', async () => {
    const user = userEvent.setup();
    installApiMock();

    render(<ForecastAlertsPage roles={['OperationalManager']} />);

    const input = await screen.findByLabelText(/threshold value/i);
    await waitFor(() => expect(input).toHaveValue(20));
    await user.clear(input);
    await user.type(input, '35');
    await user.click(screen.getByRole('button', { name: /update threshold/i }));

    expect(await screen.findByText(/threshold updated/i)).toBeInTheDocument();
    expect(
      fetchMock.mock.calls.some(
        (call) => String(call[0]).includes('/api/v1/forecast-alerts/threshold-configurations') && call[1]?.method === 'PUT',
      ),
    ).toBe(true);
  });
});
