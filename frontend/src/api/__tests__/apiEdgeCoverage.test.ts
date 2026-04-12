import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../auth', () => ({
  refreshStoredSession: vi.fn(),
}));

import { refreshStoredSession } from '../auth';
import { ApiError } from '../evaluations';
import { fetchAlertDetail } from '../alertDetails';
import { fetchThresholdAlertEvents, triggerThresholdEvaluation } from '../forecastAlerts';
import { fetchSurgeEvaluations, fetchSurgeEvents, fetchSurgeEvent } from '../surgeAlerts';

const originalFetch = global.fetch;
const fetchMock = vi.fn();

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), { status });
}

describe('api edge coverage', () => {
  beforeEach(() => {
    window.localStorage.setItem(
      'forecast-system-auth-session',
      JSON.stringify({
        accessToken: 'token-1',
        user: { userAccountId: 'user-1', email: 'planner@example.com', roles: ['CityPlanner'] },
      }),
    );
    global.fetch = fetchMock as unknown as typeof fetch;
  });

  afterEach(() => {
    global.fetch = originalFetch;
    window.localStorage.clear();
    fetchMock.mockReset();
    vi.clearAllMocks();
  });

  it('uses fallback api messages when detail is absent or invalid', async () => {
    vi.mocked(refreshStoredSession).mockResolvedValue({ accessToken: 'token-2' } as never);
    fetchMock
      .mockResolvedValueOnce(jsonResponse({}, 418))
      .mockResolvedValueOnce(new Response(null, { status: 401 }))
      .mockResolvedValueOnce(new Response('not-json', { status: 502 }))
      .mockResolvedValueOnce(new Response(null, { status: 401 }))
      .mockResolvedValueOnce(new Response('still-not-json', { status: 503 }));

    await expect(fetchAlertDetail('threshold_alert', 'alert-1')).rejects.toMatchObject<ApiError>({
      status: 418,
      message: 'Alert detail request failed with status 418',
    });
    await expect(fetchThresholdAlertEvents()).rejects.toMatchObject<ApiError>({
      status: 502,
      message: 'Alert event request failed with status 502',
    });
    await expect(fetchSurgeEvaluations()).rejects.toMatchObject<ApiError>({
      status: 503,
      message: 'Surge evaluation request failed with status 503',
    });

    expect(refreshStoredSession).toHaveBeenCalledTimes(2);
  });

  it('covers missing-detail and surge-event error branches', async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse({}, 422))
      .mockResolvedValueOnce(jsonResponse({ detail: 'surge events failed' }, 500))
      .mockResolvedValueOnce(jsonResponse({}, 409));

    await expect(
      triggerThresholdEvaluation({
        forecastReferenceId: 'forecast-1',
        forecastProduct: 'daily',
        triggerSource: 'manual_replay',
      }),
    ).rejects.toMatchObject<ApiError>({
      status: 422,
      message: 'Threshold evaluation failed with status 422',
    });

    await expect(fetchSurgeEvents()).rejects.toMatchObject<ApiError>({
      status: 500,
      message: 'surge events failed',
    });

    await expect(fetchSurgeEvent('event-2')).rejects.toMatchObject<ApiError>({
      status: 409,
      message: 'Surge alert detail request failed with status 409',
    });
  });
});
