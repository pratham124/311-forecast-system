import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { UserGuideHostPage } from '../src/pages/UserGuideHostPage';

const availableGuide = {
  guideAccessEventId: 'guide-1',
  status: 'available',
  title: 'Operations Analytics User Guide',
  publishedAt: '2026-03-13T15:00:00Z',
  body: 'Read the forecasts and comparison pages from the main navigation.',
  entryPoint: 'app_user_guide_page',
  sections: [
    { sectionId: 'overview', label: 'Overview', orderIndex: 0, contentExcerpt: 'System layout and entry points.' },
    { sectionId: 'forecasts', label: 'Forecasts', orderIndex: 1, contentExcerpt: 'Review current demand and fallback messaging.' },
  ],
};

describe('user guide open flow', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('loads and displays the current guide and reports a rendered event', async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(availableGuide), { status: 200 }))
      .mockResolvedValueOnce(new Response(null, { status: 202 }));

    render(
      <MemoryRouter>
        <UserGuideHostPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/current user guide/i)).toBeInTheDocument();
    expect(await screen.findByText('Operations Analytics User Guide')).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: /user guide sections/i })).toBeInTheDocument();
    expect(screen.getByText(/Read the forecasts and comparison pages/i)).toBeInTheDocument();

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/v1/help/user-guide');
    expect(String(fetchMock.mock.calls[1][0])).toContain('/render-events');
  });
});
