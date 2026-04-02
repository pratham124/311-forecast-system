/**
 * Tests for error-path branches in API modules that use fetchWithAuthRetry
 * and parseApiError patterns.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import {
  fetchCurrentEvaluation,
  fetchEvaluationRunStatus,
  triggerEvaluationRun,
} from '../evaluations';
import {
  fetchCurrentForecastVisualization,
  fetchServiceCategoryOptions,
  submitVisualizationRenderEvent,
} from '../forecastVisualizations';
import {
  fetchHistoricalDemandContext,
  submitHistoricalDemandQuery,
  submitHistoricalDemandRenderEvent,
} from '../historicalDemand';
import {
  fetchIngestionRunStatus,
  triggerIngestionRun,
} from '../ingestion';
import {
  fetchDemandComparisonAvailability,
  submitDemandComparisonQuery,
  submitDemandComparisonRenderEvent,
} from '../demandComparisons';

const STORAGE_KEY = 'forecast-system-auth-session';

const fetchMock = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock);
  window.localStorage.clear();
});

afterEach(() => {
  vi.unstubAllGlobals();
  fetchMock.mockReset();
  window.localStorage.clear();
});

function okJson(body: unknown) {
  return new Response(JSON.stringify(body), { status: 200 });
}

function errJson(status: number, body?: unknown) {
  return new Response(body !== undefined ? JSON.stringify(body) : '', { status });
}

// ─── evaluations ────────────────────────────────────────────────────────────

describe('fetchCurrentEvaluation', () => {
  it('returns null on 404', async () => {
    fetchMock.mockResolvedValue(errJson(404));
    const result = await fetchCurrentEvaluation('daily_1_day');
    expect(result).toBeNull();
  });

  it('throws ApiError on other failure status', async () => {
    fetchMock.mockResolvedValue(errJson(500, { detail: 'Server error' }));
    await expect(fetchCurrentEvaluation('daily_1_day')).rejects.toMatchObject({
      status: 500,
      message: 'Server error',
    });
  });

  it('throws ApiError with fallback when body has no detail', async () => {
    fetchMock.mockResolvedValue(new Response('not json', { status: 500 }));
    await expect(fetchCurrentEvaluation('daily_1_day')).rejects.toMatchObject({
      status: 500,
    });
  });
});

describe('triggerEvaluationRun', () => {
  it('throws on failure', async () => {
    fetchMock.mockResolvedValue(errJson(403, { detail: 'Forbidden' }));
    await expect(triggerEvaluationRun('daily_1_day')).rejects.toMatchObject({ status: 403 });
  });
});

describe('fetchEvaluationRunStatus', () => {
  it('throws on failure', async () => {
    fetchMock.mockResolvedValue(errJson(500, { detail: 'DB error' }));
    await expect(fetchEvaluationRunStatus('run-1')).rejects.toMatchObject({ status: 500 });
  });
});

// ─── forecastVisualizations ──────────────────────────────────────────────────

describe('fetchCurrentForecastVisualization', () => {
  it('throws on non-ok response', async () => {
    fetchMock.mockResolvedValue(errJson(503));
    await expect(fetchCurrentForecastVisualization('daily_1_day')).rejects.toThrow(
      'Visualization request failed with status 503',
    );
  });
});

describe('fetchServiceCategoryOptions', () => {
  it('throws on non-ok response', async () => {
    fetchMock.mockResolvedValue(errJson(500));
    await expect(fetchServiceCategoryOptions('daily_1_day')).rejects.toThrow(
      'Service category request failed with status 500',
    );
  });
});

describe('submitVisualizationRenderEvent', () => {
  it('throws on non-ok response', async () => {
    fetchMock.mockResolvedValue(errJson(500));
    await expect(
      submitVisualizationRenderEvent('load-1', { renderStatus: 'rendered' }),
    ).rejects.toThrow('Render event submission failed with status 500');
  });

  it('resolves on success', async () => {
    fetchMock.mockResolvedValue(new Response('', { status: 202 }));
    await expect(
      submitVisualizationRenderEvent('load-1', { renderStatus: 'rendered' }),
    ).resolves.toBeUndefined();
  });
});

// ─── historicalDemand ────────────────────────────────────────────────────────

describe('fetchHistoricalDemandContext', () => {
  it('throws on non-ok response', async () => {
    fetchMock.mockResolvedValue(errJson(500));
    await expect(fetchHistoricalDemandContext()).rejects.toThrow(
      'Historical demand context request failed with status 500',
    );
  });
});

describe('submitHistoricalDemandQuery', () => {
  it('throws on non-ok response', async () => {
    fetchMock.mockResolvedValue(errJson(400));
    await expect(
      submitHistoricalDemandQuery({ serviceCategory: undefined, timeRangeStart: '', timeRangeEnd: '' }),
    ).rejects.toThrow('Historical demand request failed with status 400');
  });
});

describe('submitHistoricalDemandRenderEvent', () => {
  it('throws on non-ok response', async () => {
    fetchMock.mockResolvedValue(errJson(500));
    await expect(
      submitHistoricalDemandRenderEvent('req-1', { renderStatus: 'rendered' }),
    ).rejects.toThrow('Historical demand render event failed with status 500');
  });

  it('resolves on success', async () => {
    fetchMock.mockResolvedValue(new Response('', { status: 202 }));
    await expect(
      submitHistoricalDemandRenderEvent('req-1', { renderStatus: 'rendered' }),
    ).resolves.toBeUndefined();
  });
});

// ─── ingestion ───────────────────────────────────────────────────────────────

describe('triggerIngestionRun', () => {
  it('throws ApiError on failure', async () => {
    fetchMock.mockResolvedValue(errJson(403, { detail: 'Access denied' }));
    await expect(triggerIngestionRun()).rejects.toMatchObject({ status: 403 });
  });
});

describe('fetchIngestionRunStatus', () => {
  it('throws ApiError on failure', async () => {
    fetchMock.mockResolvedValue(errJson(500, { detail: 'Internal error' }));
    await expect(fetchIngestionRunStatus('run-1')).rejects.toMatchObject({ status: 500 });
  });
});

// ─── demandComparisons ───────────────────────────────────────────────────────

describe('submitDemandComparisonQuery', () => {
  it('throws on non-ok response', async () => {
    fetchMock.mockResolvedValue(errJson(400));
    await expect(
      submitDemandComparisonQuery({ serviceCategories: [], geographyValues: [], timeRangeStart: '', timeRangeEnd: '' }),
    ).rejects.toThrow('Demand comparison request failed with status 400');
  });
});

describe('submitDemandComparisonRenderEvent', () => {
  it('throws on non-ok response', async () => {
    fetchMock.mockResolvedValue(errJson(500));
    await expect(
      submitDemandComparisonRenderEvent('req-1', { renderStatus: 'rendered' }),
    ).rejects.toThrow('Demand comparison render event failed with status 500');
  });

  it('resolves on success', async () => {
    fetchMock.mockResolvedValue(okJson({ comparisonRequestId: 'req-1', recordedOutcomeStatus: 'rendered' }));
    await expect(
      submitDemandComparisonRenderEvent('req-1', { renderStatus: 'rendered' }),
    ).resolves.toBeDefined();
  });
});

describe('fetchDemandComparisonAvailability', () => {
  it('throws on non-ok response', async () => {
    fetchMock.mockResolvedValue(errJson(503));
    await expect(fetchDemandComparisonAvailability()).rejects.toThrow(
      'Demand comparison availability request failed with status 503',
    );
  });
});

// ─── auth retry (401 path) ───────────────────────────────────────────────────

describe('fetchWithAuthRetry 401 path', () => {
  it('retries after 401 using stored session', async () => {
    const session = { accessToken: 'tok', user: { id: '1', email: 'a@b.com', roles: [] } };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(session));

    // First call: 401. refreshSession: 200 with new token. Second call: 200.
    fetchMock
      .mockResolvedValueOnce(new Response('', { status: 401 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ accessToken: 'new-tok', user: { id: '1', email: 'a@b.com', roles: [] } }), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ categories: ['Roads'] }), { status: 200 }),
      );

    const result = await fetchServiceCategoryOptions('daily_1_day');
    expect(result.categories).toEqual(['Roads']);
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });
});
