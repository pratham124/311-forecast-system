import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../auth', () => ({
  refreshStoredSession: vi.fn(),
}));

import { refreshStoredSession } from '../auth';
import { ApiError } from '../evaluations';
import { fetchAlertDetail } from '../alertDetails';
import { submitForecastAccuracyRenderEvent } from '../forecastAccuracyApi';
import {
  createThresholdConfiguration,
  deleteThresholdConfiguration,
  fetchThresholdAlertConfigurations,
  fetchThresholdAlertEvent,
  fetchThresholdAlertEvents,
  fetchThresholdServiceCategories,
  updateThresholdConfiguration,
} from '../forecastAlerts';
import { submitPublicForecastDisplayEvent } from '../publicForecastApi';
import {
  fetchSurgeEvaluation,
  fetchSurgeEvent,
  triggerSurgeEvaluation,
} from '../surgeAlerts';
import { submitUserGuideRenderEvent } from '../userGuide';

const originalFetch = global.fetch;
const fetchMock = vi.fn();

function jsonResponse(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), { status });
}

describe('more api coverage', () => {
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

  it('covers remaining auth-retry and error branches across api helpers', async () => {
    vi.mocked(refreshStoredSession).mockResolvedValue({} as never);

    fetchMock
      .mockResolvedValueOnce(jsonResponse({ detail: 'not found' }, 404))
      .mockResolvedValueOnce(new Response(null, { status: 401 }))
      .mockResolvedValueOnce(new Response(null, { status: 500 }))
      .mockResolvedValueOnce(jsonResponse({ detail: 'save failed' }, 400))
      .mockResolvedValueOnce(jsonResponse({ detail: 'update failed' }, 400))
      .mockResolvedValueOnce(jsonResponse({ detail: 'delete failed' }, 400))
      .mockResolvedValueOnce(jsonResponse({ detail: 'events failed' }, 400))
      .mockResolvedValueOnce(jsonResponse({ detail: 'configs failed' }, 400))
      .mockResolvedValueOnce(jsonResponse({ detail: 'categories failed' }, 400))
      .mockResolvedValueOnce(jsonResponse({ detail: 'event failed' }, 400))
      .mockResolvedValueOnce(new Response(null, { status: 500 }))
      .mockResolvedValueOnce(jsonResponse({ detail: 'surge detail failed' }, 400))
      .mockResolvedValueOnce(jsonResponse({ detail: 'surge event failed' }, 400))
      .mockResolvedValueOnce(jsonResponse({ detail: 'surge trigger failed' }, 400))
      .mockResolvedValueOnce(new Response(null, { status: 500 }));

    await expect(fetchAlertDetail('threshold_alert', 'missing')).rejects.toMatchObject<ApiError>({ status: 404, message: 'not found' });
    await expect(submitForecastAccuracyRenderEvent('fa-1', { renderStatus: 'rendered' })).rejects.toThrow(
      'Forecast accuracy render event failed with status 500',
    );
    await expect(createThresholdConfiguration({} as never)).rejects.toMatchObject<ApiError>({ message: 'save failed' });
    await expect(updateThresholdConfiguration('id-1', {} as never)).rejects.toMatchObject<ApiError>({ message: 'update failed' });
    await expect(deleteThresholdConfiguration('id-1')).rejects.toMatchObject<ApiError>({ message: 'delete failed' });
    await expect(fetchThresholdAlertEvents()).rejects.toMatchObject<ApiError>({ message: 'events failed' });
    await expect(fetchThresholdAlertConfigurations()).rejects.toMatchObject<ApiError>({ message: 'configs failed' });
    await expect(fetchThresholdServiceCategories()).rejects.toMatchObject<ApiError>({ message: 'categories failed' });
    await expect(fetchThresholdAlertEvent('event-1')).rejects.toMatchObject<ApiError>({ message: 'event failed' });
    await expect(submitPublicForecastDisplayEvent('public-1', { displayOutcome: 'rendered' } as never)).rejects.toThrow(
      'Public forecast render event submission failed with status 500',
    );
    await expect(fetchSurgeEvaluation('run-1')).rejects.toMatchObject<ApiError>({ message: 'surge detail failed' });
    await expect(fetchSurgeEvent('event-1')).rejects.toMatchObject<ApiError>({ message: 'surge event failed' });
    await expect(triggerSurgeEvaluation({ forecastReferenceId: 'forecast-1', triggerSource: 'ingestion_completion' })).rejects.toMatchObject<ApiError>({ message: 'surge trigger failed' });
    await expect(submitUserGuideRenderEvent('guide-1', { renderOutcome: 'rendered' } as never)).rejects.toThrow(
      'User guide render event failed with status 500',
    );

    expect(refreshStoredSession).toHaveBeenCalledTimes(1);
  });
});
