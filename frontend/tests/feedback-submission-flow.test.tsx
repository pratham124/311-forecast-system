import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { FeedbackSubmissionPage } from '../src/pages/FeedbackSubmissionPage';

describe('feedback submission flow', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('shows client-side validation errors before sending the request', async () => {
    const user = userEvent.setup();

    render(
      <MemoryRouter>
        <FeedbackSubmissionPage isAuthenticated={false} />
      </MemoryRouter>,
    );

    await user.click(screen.getByRole('button', { name: /submit feedback/i }));

    expect(await screen.findByText(/choose whether you are sending feedback or a bug report/i)).toBeInTheDocument();
    expect(screen.getByText(/describe the feedback or issue before submitting/i)).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('submits a report successfully and shows the saved confirmation', async () => {
    const user = userEvent.setup();
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          feedbackSubmissionId: 'fb-1',
          reportType: 'Bug Report',
          processingStatus: 'forwarded',
          acceptedAt: '2026-04-09T18:00:00Z',
          userOutcome: 'accepted',
          statusMessage: 'Your report was received, recorded, and forwarded for team review.',
        }),
        { status: 201 },
      ),
    );

    render(
      <MemoryRouter>
        <FeedbackSubmissionPage isAuthenticated={false} />
      </MemoryRouter>,
    );

    await user.selectOptions(screen.getByLabelText(/report type/i), 'Bug Report');
    await user.type(screen.getByLabelText(/details/i), 'The chart crashes after switching categories.');
    await user.type(screen.getByLabelText(/contact email/i), 'person@example.com');
    await user.click(screen.getByRole('button', { name: /submit feedback/i }));

    expect(await screen.findByText(/report received/i)).toBeInTheDocument();
    expect(screen.getByText(/submission id fb-1/i)).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [, requestInit] = fetchMock.mock.calls[0];
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/v1/feedback-submissions');
    expect(JSON.parse(String(requestInit?.body))).toEqual({
      reportType: 'Bug Report',
      description: 'The chart crashes after switching categories.',
      contactEmail: 'person@example.com',
    });
  });

  it('shows a delayed-processing confirmation when forwarding is unavailable', async () => {
    const user = userEvent.setup();
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          feedbackSubmissionId: 'fb-2',
          reportType: 'Feedback',
          processingStatus: 'deferred_for_retry',
          acceptedAt: '2026-04-09T18:05:00Z',
          userOutcome: 'accepted_with_delay',
          statusMessage: 'Your report was received and saved. Developer review may be delayed while the issue tracker recovers.',
        }),
        { status: 201 },
      ),
    );

    render(
      <MemoryRouter>
        <FeedbackSubmissionPage isAuthenticated={false} />
      </MemoryRouter>,
    );

    await user.selectOptions(screen.getByLabelText(/report type/i), 'Feedback');
    await user.type(screen.getByLabelText(/details/i), 'The issue form should explain the delayed state.');
    await user.click(screen.getByRole('button', { name: /submit feedback/i }));

    expect(await screen.findByText(/report received with delayed processing/i)).toBeInTheDocument();
    expect(screen.getByText(/developer review may be delayed/i)).toBeInTheDocument();
  });
});
