/**
 * Tests for submitVisualizationRenderEvent when renderEventSubmission is disabled.
 * Kept in a separate file so the env mock doesn't affect other API tests.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

const mockEnv = vi.hoisted(() => ({
  env: {
    apiBaseUrl: 'http://localhost:8000',
    dashboardDefaultProduct: 'daily_1_day' as const,
    renderEventSubmission: 'disabled' as 'enabled' | 'disabled',
  },
}));

vi.mock('../../config/env', () => mockEnv);

const fetchMock = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
  fetchMock.mockReset();
});

describe('submitVisualizationRenderEvent with renderEventSubmission=disabled', () => {
  it('returns immediately without making a network request', async () => {
    const { submitVisualizationRenderEvent } = await import('../forecastVisualizations');
    const result = await submitVisualizationRenderEvent('load-1', { renderStatus: 'rendered' });
    expect(fetchMock).not.toHaveBeenCalled();
    expect(result).toBeUndefined();
  });
});
