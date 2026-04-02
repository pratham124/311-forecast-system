import { afterEach, describe, expect, it } from 'vitest';
import {
  buildHeaders as buildEvaluationHeaders,
  contentTypeFromHeaders as evaluationContentTypeFromHeaders,
} from '../evaluations';
import {
  buildHeaders as buildForecastHeaders,
  contentTypeFromHeaders as forecastContentTypeFromHeaders,
} from '../forecastVisualizations';
import {
  buildHeaders as buildIngestionHeaders,
  contentTypeFromHeaders as ingestionContentTypeFromHeaders,
} from '../ingestion';

const STORAGE_KEY = 'forecast-system-auth-session';

afterEach(() => {
  window.localStorage.clear();
});

describe('API content-type helpers', () => {
  it('extracts content type from undefined, Headers, tuple arrays, and object maps', () => {
    expect(evaluationContentTypeFromHeaders(undefined)).toBeUndefined();
    expect(evaluationContentTypeFromHeaders(new Headers({ 'Content-Type': 'application/json' }))).toBe('application/json');
    expect(evaluationContentTypeFromHeaders(new Headers())).toBeUndefined();
    expect(evaluationContentTypeFromHeaders([['Content-Type', 'application/xml']])).toBe('application/xml');
    expect(evaluationContentTypeFromHeaders([['Accept', 'application/json']])).toBeUndefined();
    expect(evaluationContentTypeFromHeaders({ 'content-type': 'application/problem+json' })).toBe('application/problem+json');

    expect(forecastContentTypeFromHeaders([['Content-Type', 'text/plain']])).toBe('text/plain');
    expect(forecastContentTypeFromHeaders([['X-Request-Id', 'abc']])).toBeUndefined();
      expect(forecastContentTypeFromHeaders(new Headers({ 'Content-Type': 'text/plain' }))).toBe('text/plain');
      expect(forecastContentTypeFromHeaders(new Headers())).toBeUndefined();
    expect(forecastContentTypeFromHeaders({ 'content-type': 'text/csv' })).toBe('text/csv');

    expect(ingestionContentTypeFromHeaders({ 'content-type': 'application/problem+json' })).toBe('application/problem+json');
      expect(ingestionContentTypeFromHeaders([['Content-Type', 'application/json']])).toBe('application/json');
    expect(ingestionContentTypeFromHeaders([['Accept', 'text/plain']])).toBeUndefined();
    expect(ingestionContentTypeFromHeaders(new Headers())).toBeUndefined();
  });

  it('includes Authorization and Content-Type when building evaluation headers', () => {
    window.localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({
        accessToken: 'eval-token',
        user: { userAccountId: 'user-1', email: 'planner@example.com', roles: ['CityPlanner'] },
      }),
    );

    const headers = buildEvaluationHeaders('application/json');
    expect(headers.get('Authorization')).toBe('Bearer eval-token');
    expect(headers.get('Content-Type')).toBe('application/json');
  });

  it('sets only Content-Type when no token is stored', () => {
    const headers = buildIngestionHeaders('application/json');
    expect(headers.get('Authorization')).toBeNull();
    expect(headers.get('Content-Type')).toBe('application/json');
  });

  it('supports header extraction from forecast helper with uppercase object keys', () => {
    expect(forecastContentTypeFromHeaders({ 'Content-Type': 'application/json' })).toBe('application/json');
    const headers = buildForecastHeaders();
    expect(headers.get('Content-Type')).toBeNull();
  });
});
