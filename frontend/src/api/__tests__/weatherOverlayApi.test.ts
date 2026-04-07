import { afterEach, describe, expect, it, vi } from 'vitest';

import { submitWeatherOverlayRenderEvent } from '../weatherOverlayApi';

const originalFetch = global.fetch;

describe('weatherOverlayApi', () => {
  afterEach(() => {
    global.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it('does not submit events for disabled or superseded requests', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 202 });
    global.fetch = fetchMock as unknown as typeof fetch;

    await submitWeatherOverlayRenderEvent({
      overlayRequestId: 'req-disabled',
      overlayStatus: 'disabled',
      isLatestSelection: true,
      payload: { renderStatus: 'rendered', reportedAt: new Date().toISOString() },
    });

    await submitWeatherOverlayRenderEvent({
      overlayRequestId: 'req-superseded',
      overlayStatus: 'superseded',
      isLatestSelection: true,
      payload: { renderStatus: 'rendered', reportedAt: new Date().toISOString() },
    });

    await submitWeatherOverlayRenderEvent({
      overlayRequestId: 'req-stale',
      overlayStatus: 'visible',
      isLatestSelection: false,
      payload: { renderStatus: 'rendered', reportedAt: new Date().toISOString() },
    });

    expect(fetchMock).not.toHaveBeenCalled();
  });
});
