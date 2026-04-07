import { cleanup, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { UserGuideHostPage } from '../src/pages/UserGuideHostPage';

describe('user guide lifecycle smoke', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('shows loading before success content appears', async () => {
    let resolveFetch: (value: Response) => void = () => undefined;
    fetchMock.mockImplementationOnce(
      () =>
        new Promise<Response>((resolve) => {
          resolveFetch = resolve;
        }),
    );

    render(
      <MemoryRouter>
        <UserGuideHostPage />
      </MemoryRouter>,
    );

    expect(screen.getByText(/loading the user guide/i)).toBeInTheDocument();

    resolveFetch(
      new Response(
        JSON.stringify({
          guideAccessEventId: 'guide-5',
          status: 'available',
          title: 'Guide',
          publishedAt: '2026-03-13T15:00:00Z',
          body: 'Body',
          entryPoint: 'app_user_guide_page',
          sections: [{ sectionId: 'overview', label: 'Overview', orderIndex: 0, contentExcerpt: 'Overview text' }],
        }),
        { status: 200 },
      ),
    );
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 202 }));

    expect(await screen.findByText('Guide')).toBeInTheDocument();
  });
});
