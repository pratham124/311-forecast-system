import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { FeedbackReviewPage } from '../src/pages/FeedbackReviewPage';

describe('feedback review page', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('loads the feedback queue and selected detail for authorized reviewers', async () => {
    fetchMock
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            items: [
              {
                feedbackSubmissionId: 'fb-1',
                reportType: 'Bug Report',
                submitterKind: 'authenticated',
                processingStatus: 'forwarded',
                submittedAt: '2026-04-09T18:00:00Z',
                triageStatus: 'new',
              },
            ],
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            feedbackSubmissionId: 'fb-1',
            reportType: 'Bug Report',
            description: 'The queue detail view should show the timeline.',
            submitterKind: 'authenticated',
            processingStatus: 'forwarded',
            externalReference: 'FB-00001',
            submittedAt: '2026-04-09T18:00:00Z',
            triageStatus: 'new',
            visibilityStatus: 'visible',
            statusEvents: [
              { eventType: 'accepted', recordedAt: '2026-04-09T18:00:00Z' },
              { eventType: 'forwarded', recordedAt: '2026-04-09T18:00:05Z' },
            ],
          }),
          { status: 200 },
        ),
      );

    render(
      <MemoryRouter>
        <FeedbackReviewPage roles={['CityPlanner']} />
      </MemoryRouter>,
    );

    expect(await screen.findByRole('heading', { name: /feedback and bug reports/i })).toBeInTheDocument();
    expect(await screen.findByText(/issue tracker reference: FB-00001/i)).toBeInTheDocument();
    expect(screen.getByText(/status history/i)).toBeInTheDocument();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  });

  it('shows an access warning for non-reviewer roles', async () => {
    render(
      <MemoryRouter>
        <FeedbackReviewPage roles={['Viewer']} />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/feedback review access is restricted/i)).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
