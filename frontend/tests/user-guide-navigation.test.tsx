import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { UserGuideHostPage } from '../src/pages/UserGuideHostPage';

const availableGuide = {
  guideAccessEventId: 'guide-2',
  status: 'available',
  title: 'Operations Analytics User Guide',
  publishedAt: '2026-03-13T15:00:00Z',
  body: 'Shared body content.',
  entryPoint: 'app_user_guide_page',
  sections: [
    { sectionId: 'overview', label: 'Overview', orderIndex: 0, contentExcerpt: 'System layout and entry points.' },
    { sectionId: 'troubleshooting', label: 'Troubleshooting', orderIndex: 1, contentExcerpt: 'Refresh once and confirm your session.' },
  ],
};

describe('user guide navigation', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('switches sections without reopening the guide', async () => {
    const user = userEvent.setup();
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(availableGuide), { status: 200 }))
      .mockResolvedValueOnce(new Response(null, { status: 202 }));

    render(
      <MemoryRouter>
        <UserGuideHostPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/system layout and entry points/i)).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: /troubleshooting/i }));
    expect(await screen.findByText(/refresh once and confirm your session/i)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
