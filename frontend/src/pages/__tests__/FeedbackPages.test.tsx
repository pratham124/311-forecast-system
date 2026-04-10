import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { FeedbackReviewPage } from '../FeedbackReviewPage';
import { FeedbackSubmissionPage } from '../FeedbackSubmissionPage';
import { useFeedbackSubmission } from '../../features/feedback/hooks/useFeedbackSubmission';
import { useFeedbackReview } from '../../features/feedback-review/hooks/useFeedbackReview';

vi.mock('../../features/feedback/hooks/useFeedbackSubmission', () => ({
  useFeedbackSubmission: vi.fn(),
}));

vi.mock('../../features/feedback-review/hooks/useFeedbackReview', () => ({
  useFeedbackReview: vi.fn(),
}));

const useFeedbackSubmissionMock = vi.mocked(useFeedbackSubmission);
const useFeedbackReviewMock = vi.mocked(useFeedbackReview);

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe('Feedback pages', () => {
  it('shows authenticated navigation and reset affordances on the submission page', async () => {
    const user = userEvent.setup();
    const reset = vi.fn();

    useFeedbackSubmissionMock.mockReturnValue({
      values: { reportType: 'Feedback', description: 'Looks good.', contactEmail: '' },
      errors: {},
      result: {
        feedbackSubmissionId: 'fb-1',
        reportType: 'Feedback',
        processingStatus: 'forwarded',
        acceptedAt: '2026-04-10T18:00:00Z',
        userOutcome: 'accepted',
        statusMessage: 'Recorded.',
      },
      isSubmitting: false,
      setFieldValue: vi.fn(),
      submit: vi.fn(),
      reset,
    });

    render(
      <MemoryRouter>
        <FeedbackSubmissionPage isAuthenticated />
      </MemoryRouter>,
    );

    expect(screen.getByRole('link', { name: /back to dashboard/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /open feedback inbox/i })).toBeInTheDocument();
    expect(screen.getByText(/report received/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /submit another report/i }));
    expect(reset).toHaveBeenCalledTimes(1);
  });

  it('renders feedback review loading and error states for authorized reviewers', () => {
    useFeedbackReviewMock
      .mockReturnValueOnce({
        reportTypeFilter: 'all',
        setReportTypeFilter: vi.fn(),
        processingStatusFilter: 'all',
        setProcessingStatusFilter: vi.fn(),
        items: [],
        selectedId: null,
        setSelectedId: vi.fn(),
        detail: null,
        isLoadingList: true,
        isLoadingDetail: true,
        error: null,
      })
      .mockReturnValueOnce({
        reportTypeFilter: 'all',
        setReportTypeFilter: vi.fn(),
        processingStatusFilter: 'all',
        setProcessingStatusFilter: vi.fn(),
        items: [],
        selectedId: null,
        setSelectedId: vi.fn(),
        detail: null,
        isLoadingList: false,
        isLoadingDetail: false,
        error: 'Queue offline',
      });

    const { rerender } = render(
      <MemoryRouter>
        <FeedbackReviewPage roles={['CityPlanner']} />
      </MemoryRouter>,
    );

    expect(screen.getByText(/loading feedback submissions/i)).toBeInTheDocument();
    expect(screen.getByText(/loading submission details/i)).toBeInTheDocument();

    rerender(
      <MemoryRouter>
        <FeedbackReviewPage roles={['OperationalManager']} />
      </MemoryRouter>,
    );

    expect(screen.getByText(/feedback queue request failed/i)).toBeInTheDocument();
    expect(screen.getByText(/queue offline/i)).toBeInTheDocument();
    expect(screen.getByText(/no feedback submissions match the current filters/i)).toBeInTheDocument();
  });
});
