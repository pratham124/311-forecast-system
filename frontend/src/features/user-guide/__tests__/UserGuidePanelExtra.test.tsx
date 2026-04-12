import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../../api/userGuide', () => ({
  fetchUserGuide: vi.fn(),
  submitUserGuideRenderEvent: vi.fn(),
}));

import { fetchUserGuide, submitUserGuideRenderEvent } from '../../../api/userGuide';
import { UserGuidePanel } from '../UserGuidePanel';

describe('UserGuidePanel extra coverage', () => {
  beforeEach(() => {
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('renders request failures and null-guide fallback states', async () => {
    vi.mocked(fetchUserGuide).mockRejectedValueOnce(new Error('guide failed'));
    render(<UserGuidePanel entryPoint="alerts" />);
    expect(await screen.findByText(/user guide request failed/i)).toBeInTheDocument();
    expect(screen.getByText(/guide failed/i)).toBeInTheDocument();
  });

  it('renders default unavailable, error, and missing-content fallbacks', async () => {
    vi.mocked(fetchUserGuide)
      .mockResolvedValueOnce({
        guideAccessEventId: 'guide-1',
        status: 'unavailable',
      } as never)
      .mockResolvedValueOnce({
        guideAccessEventId: 'guide-2',
        status: 'error',
      } as never)
      .mockResolvedValueOnce({
        guideAccessEventId: 'guide-3',
        status: 'available',
        title: 'Guide',
        body: '',
        entryPoint: 'alerts',
        sections: [],
      } as never);

    const { rerender } = render(<UserGuidePanel entryPoint="alerts" />);
    expect(await screen.findByText(/the guide is unavailable\./i)).toBeInTheDocument();

    rerender(<UserGuidePanel entryPoint="forecasts" />);
    expect(await screen.findByText(/the guide could not be displayed\./i)).toBeInTheDocument();

    rerender(<UserGuidePanel entryPoint="history" />);
    expect(await screen.findByText(/the guide is missing readable content\./i)).toBeInTheDocument();
  });

  it('renders published-at fallback and reports successful renders', async () => {
    vi.mocked(fetchUserGuide).mockResolvedValue({
      guideAccessEventId: 'guide-4',
      status: 'available',
      title: 'Guide',
      publishedAt: null,
      body: 'Body text',
      entryPoint: 'app_user_guide_page',
      sections: [{ sectionId: 'overview', label: 'Overview', orderIndex: 0 }],
    } as never);

    render(<UserGuidePanel entryPoint="app_user_guide_page" />);

    expect(await screen.findByText(/published not available/i)).toBeInTheDocument();
    expect(screen.getAllByText('Body text')).toHaveLength(2);
    await waitFor(() => {
      expect(submitUserGuideRenderEvent).toHaveBeenCalledWith('guide-4', { renderOutcome: 'rendered' });
    });
  });
});
