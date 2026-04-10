import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { FeedbackSubmissionForm } from '../components/FeedbackSubmissionForm';

afterEach(() => {
  cleanup();
});

describe('FeedbackSubmissionForm', () => {
  it('submits the form and renders the non-error state', () => {
    const onChange = vi.fn();
    const onSubmit = vi.fn();

    render(
      <FeedbackSubmissionForm
        values={{ reportType: 'Feedback', description: 'Looks good.', contactEmail: '' }}
        errors={{}}
        isSubmitting={false}
        onChange={onChange}
        onSubmit={onSubmit}
      />,
    );

    expect(screen.queryByText(/we couldn't submit your report/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/choose whether you are sending feedback/i)).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: /submit feedback/i })).toHaveTextContent('Submit report');

    fireEvent.submit(screen.getByRole('button', { name: /submit feedback/i }).closest('form') as HTMLFormElement);
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it('renders form-level and field-level errors while submitting', () => {
    render(
      <FeedbackSubmissionForm
        values={{ reportType: '', description: '', contactEmail: 'bad-email' }}
        errors={{
          form: 'Tracker offline',
          reportType: 'Choose whether you are sending feedback or a bug report.',
          description: 'Describe the feedback or issue before submitting.',
          contactEmail: 'Enter a valid contact email or leave it blank.',
        }}
        isSubmitting
        onChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );

    expect(screen.getByText(/we couldn't submit your report/i)).toBeInTheDocument();
    expect(screen.getByText(/tracker offline/i)).toBeInTheDocument();
    expect(screen.getByText(/choose whether you are sending feedback or a bug report/i)).toBeInTheDocument();
    expect(screen.getByText(/describe the feedback or issue before submitting/i)).toBeInTheDocument();
    expect(screen.getByText(/enter a valid contact email or leave it blank/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /submit feedback/i })).toBeDisabled();
    expect(screen.getByRole('button', { name: /submit feedback/i })).toHaveTextContent('Submitting...');
  });
});
