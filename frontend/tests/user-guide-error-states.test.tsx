import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { UserGuideHostPage } from '../src/pages/UserGuideHostPage';
import { UserGuidePanel } from '../src/features/user-guide';

describe('user guide error states', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('shows the unavailable state when the backend returns an unavailable guide', async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          guideAccessEventId: 'guide-3',
          status: 'unavailable',
          statusMessage: 'The user guide is unavailable right now.',
          entryPoint: 'app_user_guide_page',
        }),
        { status: 200 },
      ),
    );

    render(
      <MemoryRouter>
        <UserGuideHostPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/user guide unavailable/i)).toBeInTheDocument();
  });

  it('reports render failure and shows the fallback when guide rendering crashes', async () => {
    fetchMock
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            guideAccessEventId: 'guide-4',
            status: 'available',
            title: 'Guide',
            publishedAt: '2026-03-13T15:00:00Z',
            body: 'Body',
            entryPoint: 'app_user_guide_page',
            sections: [{ sectionId: 'overview', label: 'Overview', orderIndex: 0 }],
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(new Response(null, { status: 202 }))
      .mockResolvedValueOnce(new Response(null, { status: 202 }));

    const renderBody = () => {
      throw new Error('Renderer crashed');
    };

    render(
      <MemoryRouter>
        <UserGuidePanel entryPoint="app_user_guide_page" bodyRenderer={renderBody} />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/we couldn't display the user guide/i)).toBeInTheDocument();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(3));
    expect(String(fetchMock.mock.calls[2][0])).toContain('/render-events');
  });
});
