import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { FeedbackSubmissionDetail } from '../components/FeedbackSubmissionDetail';
import { FeedbackSubmissionList } from '../components/FeedbackSubmissionList';

afterEach(() => {
  cleanup();
});

describe('Feedback review components', () => {
  it('renders the empty queue state', () => {
    render(<FeedbackSubmissionList items={[]} selectedId={null} onSelect={vi.fn()} />);
    expect(screen.getByText(/no feedback submissions match the current filters/i)).toBeInTheDocument();
  });

  it('renders queue items, selection styling, and click handling', async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();

    render(
      <FeedbackSubmissionList
        items={[
          {
            feedbackSubmissionId: 'fb-1',
            reportType: 'Feedback',
            submitterKind: 'anonymous',
            processingStatus: 'accepted',
            submittedAt: '2026-04-10T18:00:00Z',
            triageStatus: 'new',
          },
          {
            feedbackSubmissionId: 'fb-2',
            reportType: 'Bug Report',
            submitterKind: 'authenticated',
            processingStatus: 'deferred_for_retry',
            submittedAt: '2026-04-10T18:05:00Z',
            triageStatus: 'in_review',
          },
        ]}
        selectedId="fb-1"
        onSelect={onSelect}
      />,
    );

    const buttons = screen.getAllByRole('button');
    expect(buttons[0]?.className).toContain('border-accent');
    expect(buttons[1]?.className).toContain('hover:border-accent/40');
    expect(screen.getByText(/deferred for retry/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /bug report/i }));
    expect(onSelect).toHaveBeenCalledWith('fb-2');
  });

  it('renders detail loading and empty states', () => {
    const { rerender } = render(<FeedbackSubmissionDetail detail={null} isLoading />);
    expect(screen.getByText(/loading submission details/i)).toBeInTheDocument();

    rerender(<FeedbackSubmissionDetail detail={null} isLoading={false} />);
    expect(screen.getByText(/select a submission to view the review timeline/i)).toBeInTheDocument();
  });

  it('renders detail fallbacks when contact info, external reference, and event reasons are missing', () => {
    render(
      <FeedbackSubmissionDetail
        isLoading={false}
        detail={{
          feedbackSubmissionId: 'fb-2',
          reportType: 'Bug Report',
          description: 'The chart freezes after switching filters.',
          contactEmail: null,
          submitterKind: 'authenticated',
          processingStatus: 'forward_failed',
          externalReference: null,
          submittedAt: '2026-04-10T18:05:00Z',
          triageStatus: 'in_review',
          visibilityStatus: 'visible',
          statusEvents: [
            {
              eventType: 'forward_failed',
              eventReason: null,
              recordedAt: '2026-04-10T18:05:00Z',
            },
            {
              eventType: 'accepted',
              eventReason: 'Saved locally for retry.',
              recordedAt: '2026-04-10T18:00:00Z',
            },
          ],
        }}
      />,
    );

    expect(screen.getByText('Contact')).toBeInTheDocument();
    expect(screen.getByText('Not provided')).toBeInTheDocument();
    expect(screen.getByText('Issue tracker reference')).toBeInTheDocument();
    expect(screen.getByText('Not forwarded yet')).toBeInTheDocument();
    expect(screen.getByText(/saved locally for retry\./i)).toBeInTheDocument();
    expect(screen.getAllByText(/forward failed/i)).toHaveLength(2);
  });
});
