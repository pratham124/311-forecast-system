import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../auth', () => ({
  refreshStoredSession: vi.fn(),
}));

import { refreshStoredSession } from '../auth';
import { ApiError } from '../evaluations';
import {
  fetchAlertDetail,
  submitAlertDetailRenderEvent,
} from '../alertDetails';
import {
  fetchForecastAccuracy,
  submitForecastAccuracyRenderEvent,
} from '../forecastAccuracyApi';
import {
  createThresholdConfiguration,
  deleteThresholdConfiguration,
  fetchThresholdAlertConfigurations,
  fetchThresholdAlertEvent,
  fetchThresholdAlertEvents,
  fetchThresholdServiceCategories,
  triggerThresholdEvaluation,
  updateThresholdConfiguration,
} from '../forecastAlerts';
import {
  fetchCurrentPublicForecast,
  submitPublicForecastDisplayEvent,
} from '../publicForecastApi';
import {
  fetchSurgeEvaluation,
  fetchSurgeEvaluations,
  fetchSurgeEvent,
  fetchSurgeEvents,
  triggerSurgeEvaluation,
} from '../surgeAlerts';
import { fetchUserGuide, submitUserGuideRenderEvent } from '../userGuide';
import {
  fetchWeatherOverlay,
  submitWeatherOverlayRenderEvent,
} from '../weatherOverlayApi';

const originalFetch = global.fetch;
const fetchMock = vi.fn();

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), { status });
}

describe('extra api coverage', () => {
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

  it('covers alert detail fetch and render event failure branches', async () => {
    vi.mocked(refreshStoredSession).mockResolvedValue({} as never);
    fetchMock
      .mockResolvedValueOnce(new Response(null, { status: 401 }))
      .mockResolvedValueOnce(jsonResponse({ alertDetailLoadId: 'load-1' }))
      .mockResolvedValueOnce(jsonResponse({ detail: 'detail unavailable' }, 503))
      .mockResolvedValueOnce(new Response('not-json', { status: 500 }));

    await expect(fetchAlertDetail('threshold_alert', 'alert-1')).resolves.toEqual({ alertDetailLoadId: 'load-1' });
    await expect(submitAlertDetailRenderEvent('load-1', { renderStatus: 'rendered' })).rejects.toMatchObject({
      status: 503,
      message: 'detail unavailable',
    });
    await expect(
      submitAlertDetailRenderEvent('load-2', { renderStatus: 'render_failed', failureReason: 'chart failed' }),
    ).rejects.toMatchObject({
      status: 500,
      message: 'Alert detail render event failed with status 500',
    });

    expect(refreshStoredSession).toHaveBeenCalledTimes(1);
  });

  it('covers forecast accuracy fetch query building, retries, and errors', async () => {
    vi.mocked(refreshStoredSession).mockResolvedValue({} as never);
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ forecastAccuracyRequestId: 'fa-1' }))
      .mockResolvedValueOnce(new Response(null, { status: 401 }))
      .mockResolvedValueOnce(jsonResponse({ recordedOutcomeStatus: 'rendered' }));

    const signal = new AbortController().signal;
    await expect(
      fetchForecastAccuracy(
        {
          timeRangeStart: '2026-03-01T00:00:00Z',
          timeRangeEnd: '2026-03-31T00:00:00Z',
          serviceCategory: 'Roads',
        },
        signal,
      ),
    ).resolves.toEqual({ forecastAccuracyRequestId: 'fa-1' });

    expect(String(fetchMock.mock.calls[0][0])).toContain('timeRangeStart=2026-03-01T00%3A00%3A00Z');
    expect(String(fetchMock.mock.calls[0][0])).toContain('timeRangeEnd=2026-03-31T00%3A00%3A00Z');
    expect(String(fetchMock.mock.calls[0][0])).toContain('serviceCategory=Roads');
    expect(fetchMock.mock.calls[0][1]?.signal).toBe(signal);

    await expect(
      submitForecastAccuracyRenderEvent('fa-1', { renderStatus: 'rendered' }),
    ).resolves.toEqual({ recordedOutcomeStatus: 'rendered' });

    fetchMock.mockResolvedValueOnce(new Response(null, { status: 418 }));
    await expect(fetchForecastAccuracy({})).rejects.toThrow('Forecast accuracy request failed with status 418');
  });

  it('covers threshold alert api success paths', async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ evaluationRunId: 'run-1' }))
      .mockResolvedValueOnce(jsonResponse({ items: [{ notificationEventId: 'event-1' }] }))
      .mockResolvedValueOnce(jsonResponse({ items: [{ thresholdConfigurationId: 'threshold-1' }] }))
      .mockResolvedValueOnce(jsonResponse({ thresholdConfigurationId: 'threshold-2' }))
      .mockResolvedValueOnce(jsonResponse({ thresholdConfigurationId: 'threshold-3' }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
      .mockResolvedValueOnce(jsonResponse({ items: ['Roads', 'Waste'] }))
      .mockResolvedValueOnce(jsonResponse({ notificationEventId: 'event-2' }));

    await expect(
      triggerThresholdEvaluation({
        forecastReferenceId: 'forecast-1',
        forecastProduct: 'daily',
        triggerSource: 'manual_replay',
      }),
    ).resolves.toEqual({ evaluationRunId: 'run-1' });
    await expect(fetchThresholdAlertEvents()).resolves.toEqual([{ notificationEventId: 'event-1' }]);
    await expect(fetchThresholdAlertConfigurations()).resolves.toEqual([{ thresholdConfigurationId: 'threshold-1' }]);
    await expect(createThresholdConfiguration({} as never)).resolves.toEqual({ thresholdConfigurationId: 'threshold-2' });
    await expect(updateThresholdConfiguration('threshold-3', {} as never)).resolves.toEqual({ thresholdConfigurationId: 'threshold-3' });
    await expect(deleteThresholdConfiguration('threshold-4')).resolves.toBeUndefined();
    await expect(fetchThresholdServiceCategories()).resolves.toEqual(['Roads', 'Waste']);
    await expect(fetchThresholdAlertEvent('event-2')).resolves.toEqual({ notificationEventId: 'event-2' });
  });

  it('covers threshold alert api error parsing', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse({ detail: 'threshold broke' }, 400));
    await expect(
      triggerThresholdEvaluation({
        forecastReferenceId: 'forecast-2',
        forecastProduct: 'weekly',
        triggerSource: 'scheduled_recheck',
      }),
    ).rejects.toMatchObject({ status: 400, message: 'threshold broke' });
  });

  it('covers public forecast api success and failure branches', async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ publicForecastRequestId: 'public-1' }))
      .mockResolvedValueOnce(new Response(null, { status: 202 }))
      .mockResolvedValueOnce(new Response(null, { status: 500 }));

    await expect(fetchCurrentPublicForecast('daily')).resolves.toEqual({ publicForecastRequestId: 'public-1' });
    await expect(
      submitPublicForecastDisplayEvent('public-1', { renderStatus: 'rendered' } as never),
    ).resolves.toBeUndefined();
    await expect(fetchCurrentPublicForecast('weekly')).rejects.toThrow('Public forecast request failed with status 500');
  });

  it('covers surge alert api success and item fallback branches', async () => {
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ items: [{ surgeEvaluationRunId: 'run-1' }] }))
      .mockResolvedValueOnce(jsonResponse({ surgeEvaluationRunId: 'run-1', status: 'completed' }))
      .mockResolvedValueOnce(jsonResponse({ items: null }))
      .mockResolvedValueOnce(jsonResponse({ surgeNotificationEventId: 'event-1' }))
      .mockResolvedValueOnce(jsonResponse({ surgeEvaluationRunId: 'run-2' }));

    await expect(fetchSurgeEvaluations()).resolves.toEqual([{ surgeEvaluationRunId: 'run-1' }]);
    await expect(fetchSurgeEvaluation('run-1')).resolves.toEqual({ surgeEvaluationRunId: 'run-1', status: 'completed' });
    await expect(fetchSurgeEvents()).resolves.toEqual([]);
    await expect(fetchSurgeEvent('event-1')).resolves.toEqual({ surgeNotificationEventId: 'event-1' });
    await expect(
      triggerSurgeEvaluation({ forecastReferenceId: 'forecast-1', triggerSource: 'manual_replay' }),
    ).resolves.toEqual({ surgeEvaluationRunId: 'run-2' });
  });

  it('covers surge alert api errors', async () => {
    fetchMock.mockResolvedValueOnce(new Response('bad', { status: 502 }));
    await expect(fetchSurgeEvaluations()).rejects.toMatchObject({
      status: 502,
      message: 'Surge evaluation request failed with status 502',
    });
  });

  it('covers user guide fetch and render event branches', async () => {
    vi.mocked(refreshStoredSession).mockResolvedValue({} as never);
    fetchMock
      .mockResolvedValueOnce(new Response(null, { status: 401 }))
      .mockResolvedValueOnce(jsonResponse({ guideAccessEventId: 'guide-1' }))
      .mockResolvedValueOnce(new Response(null, { status: 202 }))
      .mockResolvedValueOnce(new Response(null, { status: 500 }));

    await expect(fetchUserGuide('alerts')).resolves.toEqual({ guideAccessEventId: 'guide-1' });
    expect(String(fetchMock.mock.calls[1][0])).toContain('entryPoint=alerts');
    await expect(
      submitUserGuideRenderEvent('guide-1', { renderStatus: 'rendered' } as never),
    ).resolves.toBeUndefined();
    await expect(fetchUserGuide('forecasts')).rejects.toThrow('User guide request failed with status 500');
  });

  it('covers weather overlay fetch and render submission branches', async () => {
    vi.mocked(refreshStoredSession).mockResolvedValue({} as never);
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ overlayRequestId: 'overlay-1' }))
      .mockResolvedValueOnce(new Response(null, { status: 401 }))
      .mockResolvedValueOnce(new Response(null, { status: 202 }))
      .mockResolvedValueOnce(new Response(null, { status: 500 }))
      .mockResolvedValueOnce(new Response(null, { status: 422 }));

    await expect(
      fetchWeatherOverlay({
        geographyId: 'citywide',
        timeRangeStart: '2026-03-01T00:00:00Z',
        timeRangeEnd: '2026-03-02T00:00:00Z',
        weatherMeasure: 'temperature',
      }),
    ).resolves.toEqual({ overlayRequestId: 'overlay-1' });
    expect(String(fetchMock.mock.calls[0][0])).toContain('weatherMeasure=temperature');

    await expect(
      submitWeatherOverlayRenderEvent({
        overlayRequestId: 'overlay-1',
        overlayStatus: 'visible',
        isLatestSelection: true,
        payload: { renderStatus: 'rendered', reportedAt: '2026-03-02T00:00:00Z' },
      }),
    ).resolves.toBeUndefined();

    await expect(
      submitWeatherOverlayRenderEvent({
        overlayRequestId: 'overlay-2',
        overlayStatus: 'visible',
        isLatestSelection: true,
        payload: { renderStatus: 'failed-to-render', reportedAt: '2026-03-02T00:00:00Z', failureReason: 'boom' },
      }),
    ).rejects.toThrow('Weather overlay render event failed with status 500');

    await expect(
      fetchWeatherOverlay({
        geographyId: 'citywide',
        timeRangeStart: '2026-03-01T00:00:00Z',
        timeRangeEnd: '2026-03-02T00:00:00Z',
      }),
    ).rejects.toThrow('Weather overlay request failed with status 422');
  });
});
