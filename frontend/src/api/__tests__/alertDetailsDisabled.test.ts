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

describe('alertDetails api with render events disabled', () => {
  it('returns early without posting render events', async () => {
    const { submitAlertDetailRenderEvent } = await import('../alertDetails');
    await expect(
      submitAlertDetailRenderEvent('detail-1', { renderStatus: 'rendered' } as never),
    ).resolves.toBeUndefined();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
