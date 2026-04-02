/**
 * Coverage for:
 * - 401 retry paths in demandComparisons, historicalDemand, evaluations, ingestion
 * - buildHeaders with accessToken and contentType
 * - buildQuery with falsy/empty categories (forecastVisualizations)
 * - fetchDemandComparisonContext
 * - parseApiError catch branch (non-JSON body) in ingestion
 * - formatValidationMessage: null when loc last element is not a string
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fetchDemandComparisonAvailability, fetchDemandComparisonContext, submitDemandComparisonQuery } from '../demandComparisons';
import { fetchCurrentEvaluation, fetchEvaluationRunStatus, triggerEvaluationRun } from '../evaluations';
import { fetchCurrentForecastVisualization, fetchServiceCategoryOptions } from '../forecastVisualizations';
import { fetchHistoricalDemandContext, submitHistoricalDemandQuery } from '../historicalDemand';
import { fetchCurrentDataset, fetchIngestionRunStatus, triggerIngestionRun } from '../ingestion';
import { loginUser } from '../auth';

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

const storedSession = { accessToken: 'tok', user: { id: '1', email: 'a@b.com', roles: [] } };
const refreshedSession = { accessToken: 'new-tok', user: { id: '1', email: 'a@b.com', roles: [] } };

// ─── demandComparisons.ts: 401 retry (covers line 31) ────────────────────────

describe('demandComparisons: 401 retry path', () => {
  it('retries after 401 for fetchDemandComparisonAvailability', async () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(storedSession));

    fetchMock
      .mockResolvedValueOnce(new Response('', { status: 401 }))
      .mockResolvedValueOnce(okJson(refreshedSession))
      .mockResolvedValueOnce(okJson({
        serviceCategories: ['Roads'],
        byCategoryGeography: {},
        dateConstraints: {},
        presets: [],
        forecastProduct: 'daily_1_day',
      }));

    const result = await fetchDemandComparisonAvailability();
    expect(result.serviceCategories).toEqual(['Roads']);
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it('retries after 401 for submitDemandComparisonQuery', async () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(storedSession));

    fetchMock
      .mockResolvedValueOnce(new Response('', { status: 401 }))
      .mockResolvedValueOnce(okJson(refreshedSession))
      .mockResolvedValueOnce(okJson({
        comparisonRequestId: 'cmp-1',
        outcomeStatus: 'success',
        filters: {},
        resultMode: 'chart_and_table',
        series: [],
      }));

    const result = await submitDemandComparisonQuery({ serviceCategories: [], geographyValues: [], timeRangeStart: '', timeRangeEnd: '' });
    expect(result.comparisonRequestId).toBe('cmp-1');
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });
});

// ─── demandComparisons.ts: fetchDemandComparisonContext ───────────────────────

describe('fetchDemandComparisonContext', () => {
  it('returns context data on success', async () => {
    fetchMock.mockResolvedValue(okJson({ serviceCategories: ['Waste'], dateRange: {} }));
    const result = await fetchDemandComparisonContext();
    expect(result).toMatchObject({ serviceCategories: ['Waste'] });
  });

  it('throws on non-ok response', async () => {
    fetchMock.mockResolvedValue(new Response('', { status: 503 }));
    await expect(fetchDemandComparisonContext()).rejects.toThrow(
      'Demand comparison context request failed with status 503',
    );
  });

  it('retries after 401', async () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(storedSession));
    fetchMock
      .mockResolvedValueOnce(new Response('', { status: 401 }))
      .mockResolvedValueOnce(okJson(refreshedSession))
      .mockResolvedValueOnce(okJson({ contextData: 'ok' }));
    const result = await fetchDemandComparisonContext();
    expect(result).toEqual({ contextData: 'ok' });
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });
});

// ─── demandComparisons.ts: buildHeaders with accessToken ─────────────────────

describe('demandComparisons: buildHeaders includes Authorization when token stored', () => {
  it('sends Authorization header for fetchDemandComparisonAvailability', async () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(storedSession));
    fetchMock.mockResolvedValue(okJson({ serviceCategories: [], byCategoryGeography: {}, dateConstraints: {}, presets: [], forecastProduct: 'daily_1_day' }));
    await fetchDemandComparisonAvailability();
    const initArg = fetchMock.mock.calls[0][1] as RequestInit;
    expect((initArg.headers as Headers).get('Authorization')).toBe('Bearer tok');
  });

  it('sends Content-Type when body present (submitDemandComparisonQuery)', async () => {
    fetchMock.mockResolvedValue(okJson({ comparisonRequestId: 'c1', outcomeStatus: 'success', filters: {}, resultMode: 'chart_and_table', series: [] }));
    await submitDemandComparisonQuery({ serviceCategories: [], geographyValues: [], timeRangeStart: '', timeRangeEnd: '' });
    const initArg = fetchMock.mock.calls[0][1] as RequestInit;
    expect((initArg.headers as Headers).get('Content-Type')).toBe('application/json');
  });
});

// ─── evaluations.ts: 401 retry path ──────────────────────────────────────────

describe('evaluations: 401 retry path', () => {
  it('retries after 401 for fetchEvaluationRunStatus', async () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(storedSession));

    fetchMock
      .mockResolvedValueOnce(new Response('', { status: 401 }))
      .mockResolvedValueOnce(okJson(refreshedSession))
      .mockResolvedValueOnce(okJson({
        evaluationRunId: 'run-1', status: 'completed', resultType: null,
        completedAt: null, failureReason: null, summary: null,
      }));

    const result = await fetchEvaluationRunStatus('run-1');
    expect(result.status).toBe('completed');
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it('retries after 401 for triggerEvaluationRun', async () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(storedSession));

    fetchMock
      .mockResolvedValueOnce(new Response('', { status: 401 }))
      .mockResolvedValueOnce(okJson(refreshedSession))
      .mockResolvedValueOnce(okJson({ evaluationRunId: 'run-2', status: 'accepted' }));

    const result = await triggerEvaluationRun('daily_1_day');
    expect(result.evaluationRunId).toBe('run-2');
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it('retries after 401 for fetchCurrentEvaluation', async () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(storedSession));

    fetchMock
      .mockResolvedValueOnce(new Response('', { status: 401 }))
      .mockResolvedValueOnce(okJson(refreshedSession))
      .mockResolvedValueOnce(okJson({
        comparisonStatus: 'pass', segments: [], baselineMethods: ['seasonal_naive'],
        fairComparison: { segmentCoverage: [], evaluationWindowStart: '', evaluationWindowEnd: '' },
        updatedAt: '2026-01-01T00:00:00Z',
        comparisonSummary: null, sourceCleanedDatasetVersionId: null,
      }));

    const result = await fetchCurrentEvaluation('daily_1_day');
    expect(result?.comparisonStatus).toBe('pass');
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });
});

// ─── evaluations.ts: buildHeaders with accessToken ───────────────────────────

describe('evaluations: buildHeaders with accessToken', () => {
  it('sends Authorization header when token is stored', async () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(storedSession));
    fetchMock.mockResolvedValue(new Response('', { status: 404 }));
    await fetchCurrentEvaluation('daily_1_day');
    const initArg = fetchMock.mock.calls[0][1] as RequestInit;
    expect((initArg.headers as Headers).get('Authorization')).toBe('Bearer tok');
  });

  it('sends Content-Type when body present (triggerEvaluationRun)', async () => {
    fetchMock.mockResolvedValue(okJson({ evaluationRunId: 'r1', status: 'accepted' }));
    await triggerEvaluationRun('daily_1_day');
    const initArg = fetchMock.mock.calls[0][1] as RequestInit;
    expect((initArg.headers as Headers).get('Content-Type')).toBe('application/json');
  });
});

describe('evaluations: parseApiError detail fallback', () => {
  it('uses fallback message when detail is missing in JSON error body', async () => {
    fetchMock.mockResolvedValue(new Response(JSON.stringify({}), { status: 500 }));

    await expect(fetchCurrentEvaluation('daily_1_day')).rejects.toMatchObject({
      status: 500,
      message: 'Evaluation request failed with status 500',
    });
  });
});

// ─── forecastVisualizations.ts: buildQuery with falsy categories ─────────────

describe('forecastVisualizations: buildQuery skips falsy categories', () => {
  it('does not include empty string categories in query string', async () => {
    fetchMock.mockResolvedValue(okJson({
      visualizationLoadId: 'v1', forecastProduct: 'daily_1_day', forecastGranularity: 'daily',
      historyWindowStart: '2026-01-01', historyWindowEnd: '2026-01-07',
      forecastWindowStart: '2026-01-07', forecastWindowEnd: '2026-01-08',
      historicalSeries: [], forecastSeries: [], alerts: [], pipelineStatus: [], viewStatus: 'success',
    }));
    await fetchCurrentForecastVisualization('daily_1_day', ['', 'Roads'], ['', 'Waste']);
    const calledUrl = fetchMock.mock.calls[0][0] as string;
    expect(calledUrl).toContain('serviceCategory=Roads');
    expect(calledUrl).not.toMatch(/serviceCategory=&|serviceCategory=$/);
    expect(calledUrl).toContain('excludeServiceCategory=Waste');
  });
});

// ─── forecastVisualizations.ts: 401 retry path ───────────────────────────────

describe('forecastVisualizations: 401 retry path', () => {
  it('retries after 401 for fetchCurrentForecastVisualization', async () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(storedSession));

    fetchMock
      .mockResolvedValueOnce(new Response('', { status: 401 }))
      .mockResolvedValueOnce(okJson(refreshedSession))
      .mockResolvedValueOnce(okJson({
        visualizationLoadId: 'v1', forecastProduct: 'daily_1_day', forecastGranularity: 'daily',
        historyWindowStart: '2026-01-01', historyWindowEnd: '2026-01-07',
        forecastWindowStart: '2026-01-07', forecastWindowEnd: '2026-01-08',
        historicalSeries: [], forecastSeries: [], alerts: [], pipelineStatus: [], viewStatus: 'success',
      }));

    const result = await fetchCurrentForecastVisualization('daily_1_day');
    expect(result.viewStatus).toBe('success');
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });
});

// ─── forecastVisualizations.ts: buildHeaders with accessToken ────────────────

describe('forecastVisualizations: buildHeaders with accessToken', () => {
  it('sends Authorization header when token stored', async () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(storedSession));
    fetchMock.mockResolvedValue(okJson({ forecastProduct: 'daily_1_day', categories: [] }));
    await fetchServiceCategoryOptions('daily_1_day');
    const initArg = fetchMock.mock.calls[0][1] as RequestInit;
    expect((initArg.headers as Headers).get('Authorization')).toBe('Bearer tok');
  });
});

// ─── historicalDemand.ts: 401 retry path (line 29-30) ────────────────────────

describe('historicalDemand: 401 retry path', () => {
  it('retries after 401 for fetchHistoricalDemandContext', async () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(storedSession));

    fetchMock
      .mockResolvedValueOnce(new Response('', { status: 401 }))
      .mockResolvedValueOnce(okJson(refreshedSession))
      .mockResolvedValueOnce(okJson({ serviceCategories: ['Roads'], supportedGeographyLevels: ['ward'], summary: 'OK' }));

    const result = await fetchHistoricalDemandContext();
    expect(result.serviceCategories).toEqual(['Roads']);
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it('retries after 401 for submitHistoricalDemandQuery', async () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(storedSession));

    fetchMock
      .mockResolvedValueOnce(new Response('', { status: 401 }))
      .mockResolvedValueOnce(okJson(refreshedSession))
      .mockResolvedValueOnce(okJson({
        analysisRequestId: 'req-1', outcomeStatus: 'success',
        filters: {}, aggregationGranularity: 'daily', resultMode: 'chart_and_table', summaryPoints: [],
      }));

    const result = await submitHistoricalDemandQuery({ serviceCategories: [], timeRangeStart: '', timeRangeEnd: '' });
    expect(result.outcomeStatus).toBe('success');
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });
});

// ─── historicalDemand.ts: buildHeaders with accessToken and contentType ──────

describe('historicalDemand: buildHeaders', () => {
  it('sends Authorization header when token stored', async () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(storedSession));
    fetchMock.mockResolvedValue(okJson({ serviceCategories: [], supportedGeographyLevels: [], summary: '' }));
    await fetchHistoricalDemandContext();
    const initArg = fetchMock.mock.calls[0][1] as RequestInit;
    expect((initArg.headers as Headers).get('Authorization')).toBe('Bearer tok');
  });

  it('sends Content-Type when body present', async () => {
    fetchMock.mockResolvedValue(okJson({ analysisRequestId: 'r1', outcomeStatus: 'success', filters: {}, aggregationGranularity: 'daily', resultMode: 'chart_and_table', summaryPoints: [] }));
    await submitHistoricalDemandQuery({ serviceCategories: [], timeRangeStart: '', timeRangeEnd: '' });
    const initArg = fetchMock.mock.calls[0][1] as RequestInit;
    expect((initArg.headers as Headers).get('Content-Type')).toBe('application/json');
  });
});

// ─── ingestion.ts: 401 retry path ────────────────────────────────────────────

describe('ingestion: 401 retry path', () => {
  it('retries after 401 for fetchCurrentDataset', async () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(storedSession));

    const datasetPayload = {
      source_name: '311', dataset_version_id: 'v1', updated_at: '2026-01-01',
      updated_by_run_id: 'run-1', record_count: 100,
    };

    fetchMock
      .mockResolvedValueOnce(new Response('', { status: 401 }))
      .mockResolvedValueOnce(okJson(refreshedSession))
      .mockResolvedValueOnce(okJson(datasetPayload));

    const result = await fetchCurrentDataset();
    expect(result?.sourceName).toBe('311');
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it('retries after 401 for triggerIngestionRun', async () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(storedSession));

    fetchMock
      .mockResolvedValueOnce(new Response('', { status: 401 }))
      .mockResolvedValueOnce(okJson(refreshedSession))
      .mockResolvedValueOnce(okJson({ run_id: 'run-3', status: 'accepted' }));

    const result = await triggerIngestionRun();
    expect(result.runId).toBe('run-3');
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it('retries after 401 for fetchIngestionRunStatus', async () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(storedSession));

    fetchMock
      .mockResolvedValueOnce(new Response('', { status: 401 }))
      .mockResolvedValueOnce(okJson(refreshedSession))
      .mockResolvedValueOnce(okJson({
        run_id: 'run-4', status: 'completed', started_at: '2026-01-01', cursor_advanced: false,
      }));

    const result = await fetchIngestionRunStatus('run-4');
    expect(result.runId).toBe('run-4');
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });
});

// ─── ingestion.ts: buildHeaders with accessToken ─────────────────────────────

describe('ingestion: buildHeaders with accessToken', () => {
  it('sends Authorization header when token stored', async () => {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(storedSession));
    fetchMock.mockResolvedValue(new Response('', { status: 404 }));
    await fetchCurrentDataset();
    const initArg = fetchMock.mock.calls[0][1] as RequestInit;
    expect((initArg.headers as Headers).get('Authorization')).toBe('Bearer tok');
  });
});

// ─── ingestion.ts: parseApiError catch branch (non-JSON body) ────────────────

describe('ingestion: parseApiError with non-JSON response', () => {
  it('falls back to generic message when response body is not valid JSON', async () => {
    fetchMock.mockResolvedValue(new Response('not json', { status: 500 }));
    await expect(fetchCurrentDataset()).rejects.toMatchObject({
      status: 500,
      message: 'Current dataset request failed with status 500',
    });
  });

  it('falls back for triggerIngestionRun with non-JSON error', async () => {
    fetchMock.mockResolvedValue(new Response('bad gateway', { status: 502 }));
    await expect(triggerIngestionRun()).rejects.toMatchObject({
      status: 502,
      message: 'Ingestion trigger failed with status 502',
    });
  });

  it('uses fallback message when JSON error has no detail field', async () => {
    fetchMock.mockResolvedValue(new Response(JSON.stringify({}), { status: 500 }));

    await expect(fetchCurrentDataset()).rejects.toMatchObject({
      status: 500,
      message: 'Current dataset request failed with status 500',
    });
  });
});

// ─── auth.ts: formatValidationMessage null branch ─────────────────────────────

describe('auth: formatValidationMessage returns null when loc last element is not a string', () => {
  it('falls back to generic message when all validation messages are null', async () => {
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          detail: [
            { loc: ['body', 42], type: 'some_error' },
          ],
        }),
        { status: 422 },
      ),
    );
    // loc last element is 42 (a number, not string), so field=null
    // No msg field → formatValidationMessage returns null
    // All null messages → 'Please check your details and try again.'
    await expect(loginUser('a@b.com', 'x')).rejects.toThrow('Please check your details and try again.');
  });
});
