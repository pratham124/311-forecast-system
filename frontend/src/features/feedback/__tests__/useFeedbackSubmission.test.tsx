import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useFeedbackSubmission } from '../hooks/useFeedbackSubmission';
import {
  FeedbackApiError,
  submitFeedbackSubmission,
} from '../../../api/feedbackSubmissions';

vi.mock('../../../api/feedbackSubmissions', async () => {
  const actual = await vi.importActual<typeof import('../../../api/feedbackSubmissions')>(
    '../../../api/feedbackSubmissions',
  );
  return {
    ...actual,
    submitFeedbackSubmission: vi.fn(),
  };
});

const submitFeedbackSubmissionMock = vi.mocked(submitFeedbackSubmission);

afterEach(() => {
  vi.clearAllMocks();
});

describe('useFeedbackSubmission', () => {
  it('updates field values even when there is no matching field error to clear', () => {
    const { result } = renderHook(() => useFeedbackSubmission());

    act(() => {
      result.current.setFieldValue('description', 'No validation error yet.');
    });

    expect(result.current.values.description).toBe('No validation error yet.');
    expect(result.current.errors).toEqual({});
  });

  it('validates fields locally and clears field errors as values change', async () => {
    const { result } = renderHook(() => useFeedbackSubmission());

    await act(async () => {
      const success = await result.current.submit();
      expect(success).toBe(false);
    });

    expect(result.current.errors).toMatchObject({
      reportType: 'Choose whether you are sending feedback or a bug report.',
      description: 'Describe the feedback or issue before submitting.',
    });

    act(() => {
      result.current.setFieldValue('reportType', 'Feedback');
      result.current.setFieldValue('description', '  Thanks for adding this view.  ');
      result.current.setFieldValue('contactEmail', 'bad-email');
    });

    await act(async () => {
      const success = await result.current.submit();
      expect(success).toBe(false);
    });

    expect(result.current.errors).toEqual({
      contactEmail: 'Enter a valid contact email or leave it blank.',
    });

    act(() => {
      result.current.setFieldValue('contactEmail', 'person@example.com');
    });

    expect(result.current.errors).toEqual({});
  });

  it('submits successfully and normalizes trimmed form values', async () => {
    submitFeedbackSubmissionMock.mockResolvedValueOnce({
      feedbackSubmissionId: 'fb-1',
      reportType: 'Feedback',
      processingStatus: 'forwarded',
      acceptedAt: '2026-04-10T18:00:00Z',
      userOutcome: 'accepted',
      statusMessage: 'Recorded.',
    });
    const { result } = renderHook(() => useFeedbackSubmission());

    act(() => {
      result.current.setFieldValue('reportType', 'Feedback');
      result.current.setFieldValue('description', '  Trim this description.  ');
      result.current.setFieldValue('contactEmail', '   ');
    });

    await act(async () => {
      const success = await result.current.submit();
      expect(success).toBe(true);
    });

    expect(submitFeedbackSubmissionMock).toHaveBeenCalledWith({
      reportType: 'Feedback',
      description: 'Trim this description.',
      contactEmail: null,
    });
    expect(result.current.result?.feedbackSubmissionId).toBe('fb-1');
    expect(result.current.errors).toEqual({});
    expect(result.current.isSubmitting).toBe(false);
  });

  it('shows API field errors without adding a form-level fallback', async () => {
    submitFeedbackSubmissionMock.mockRejectedValueOnce(
      new FeedbackApiError(422, 'Describe the feedback or issue before submitting.', {
        description: 'Describe the feedback or issue before submitting.',
      }),
    );
    const { result } = renderHook(() => useFeedbackSubmission());

    act(() => {
      result.current.setFieldValue('reportType', 'Bug Report');
      result.current.setFieldValue('description', 'The chart is blank');
      result.current.setFieldValue('contactEmail', 'person@example.com');
    });

    await act(async () => {
      const success = await result.current.submit();
      expect(success).toBe(false);
    });

    expect(result.current.errors).toEqual({
      description: 'Describe the feedback or issue before submitting.',
    });
    expect(result.current.result).toBeNull();
  });

  it('shows form errors for API failures without field details and for thrown errors', async () => {
    submitFeedbackSubmissionMock
      .mockRejectedValueOnce(new FeedbackApiError(500, 'Tracker offline'))
      .mockRejectedValueOnce(new Error('Network down'))
      .mockRejectedValueOnce('unexpected');
    const { result } = renderHook(() => useFeedbackSubmission());

    act(() => {
      result.current.setFieldValue('reportType', 'Feedback');
      result.current.setFieldValue('description', 'Please keep the queue stable.');
      result.current.setFieldValue('contactEmail', 'person@example.com');
    });

    await act(async () => {
      await result.current.submit();
    });
    expect(result.current.errors).toEqual({ form: 'Tracker offline' });

    await act(async () => {
      await result.current.submit();
    });
    expect(result.current.errors).toEqual({ form: 'Network down' });

    await act(async () => {
      await result.current.submit();
    });
    expect(result.current.errors).toEqual({ form: 'Feedback submission failed.' });
  });

  it('resets the form, errors, and result state', async () => {
    submitFeedbackSubmissionMock.mockResolvedValueOnce({
      feedbackSubmissionId: 'fb-2',
      reportType: 'Bug Report',
      processingStatus: 'deferred_for_retry',
      acceptedAt: '2026-04-10T18:05:00Z',
      userOutcome: 'accepted_with_delay',
      statusMessage: 'Saved locally.',
    });
    const { result } = renderHook(() => useFeedbackSubmission());

    act(() => {
      result.current.setFieldValue('reportType', 'Bug Report');
      result.current.setFieldValue('description', 'The alert banner overlaps the title.');
      result.current.setFieldValue('contactEmail', 'person@example.com');
    });

    await act(async () => {
      await result.current.submit();
    });

    expect(result.current.result?.feedbackSubmissionId).toBe('fb-2');

    act(() => {
      result.current.reset();
    });

    await waitFor(() => {
      expect(result.current.values).toEqual({
        reportType: '',
        description: '',
        contactEmail: '',
      });
    });
    expect(result.current.errors).toEqual({});
    expect(result.current.result).toBeNull();
  });
});
