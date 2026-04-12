import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { FeedbackSubmissionDetail } from '../components/FeedbackSubmissionDetail';
import { FeedbackSubmissionList } from '../components/FeedbackSubmissionList';

describe('Feedback review components extra coverage', () => {
  it('renders alternate styling branches and unknown timeline events', () => {
    render(
      <>
        <FeedbackSubmissionList
          items={[
            {
              feedbackSubmissionId: 'fb-1',
              reportType: 'Feedback',
              submitterKind: 'anonymous',
              processingStatus: 'forwarded',
              submittedAt: '2026-04-10T18:00:00Z',
              triageStatus: 'resolved',
            },
          ]}
          selectedId={null}
          onSelect={() => undefined}
        />
        <FeedbackSubmissionDetail
          isLoading={false}
          detail={{
            feedbackSubmissionId: 'fb-2',
            reportType: 'Feedback',
            description: 'Looks fine.',
            contactEmail: 'person@example.com',
            submitterKind: 'authenticated',
            processingStatus: 'forwarded',
            externalReference: 'ABC-123',
            submittedAt: '2026-04-10T18:05:00Z',
            triageStatus: 'resolved',
            visibilityStatus: 'hidden',
            statusEvents: [
              {
                eventType: 'forward_failed',
                eventReason: 'Something custom happened.',
                recordedAt: '2026-04-10T18:05:00Z',
              },
            ],
          }}
        />
      </>,
    );

    expect(screen.getByText(/product feedback received/i)).toBeInTheDocument();
    expect(screen.getAllByText(/forwarded/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/resolved/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/hidden/i)).toBeInTheDocument();
    expect(screen.getByText(/abc-123/i)).toBeInTheDocument();
    expect(screen.getByText(/something custom happened\./i)).toBeInTheDocument();
  });
});
