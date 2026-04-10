import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { useFeedbackReview } from '../hooks/useFeedbackReview';
import {
  getFeedbackSubmission,
  listFeedbackSubmissions,
} from '../../../api/feedbackSubmissions';

vi.mock('../../../api/feedbackSubmissions', () => ({
  listFeedbackSubmissions: vi.fn(),
  getFeedbackSubmission: vi.fn(),
}));

const listFeedbackSubmissionsMock = vi.mocked(listFeedbackSubmissions);
const getFeedbackSubmissionMock = vi.mocked(getFeedbackSubmission);

const firstItem = {
  feedbackSubmissionId: 'fb-1',
  reportType: 'Feedback' as const,
  submitterKind: 'anonymous' as const,
  processingStatus: 'accepted' as const,
  submittedAt: '2026-04-10T18:00:00Z',
  triageStatus: 'new' as const,
};

const secondItem = {
  feedbackSubmissionId: 'fb-2',
  reportType: 'Bug Report' as const,
  submitterKind: 'authenticated' as const,
  processingStatus: 'forwarded' as const,
  submittedAt: '2026-04-10T18:05:00Z',
  triageStatus: 'in_review' as const,
};

afterEach(() => {
  vi.clearAllMocks();
});

describe('useFeedbackReview', () => {
  it('resets state immediately when disabled', () => {
    const { result } = renderHook(() => useFeedbackReview(false));

    expect(result.current.items).toEqual([]);
    expect(result.current.selectedId).toBeNull();
    expect(result.current.detail).toBeNull();
    expect(result.current.error).toBeNull();
    expect(result.current.isLoadingList).toBe(false);
    expect(result.current.isLoadingDetail).toBe(false);
    expect(listFeedbackSubmissionsMock).not.toHaveBeenCalled();
  });

  it('loads the list, chooses the first item by default, and preserves a selected item on refresh', async () => {
    listFeedbackSubmissionsMock
      .mockResolvedValueOnce({ items: [firstItem, secondItem] })
      .mockResolvedValueOnce({ items: [secondItem] });
    getFeedbackSubmissionMock.mockImplementation(async (feedbackSubmissionId) => ({
      feedbackSubmissionId,
      reportType: feedbackSubmissionId === 'fb-2' ? 'Bug Report' : 'Feedback',
      description: `Detail for ${feedbackSubmissionId}`,
      submitterKind: feedbackSubmissionId === 'fb-2' ? 'authenticated' : 'anonymous',
      processingStatus: feedbackSubmissionId === 'fb-2' ? 'forwarded' : 'accepted',
      submittedAt: '2026-04-10T18:00:00Z',
      triageStatus: 'new',
      visibilityStatus: 'visible',
      statusEvents: [{ eventType: 'accepted', recordedAt: '2026-04-10T18:00:00Z' }],
    }));

    const { result } = renderHook(() => useFeedbackReview());

    await waitFor(() => {
      expect(result.current.items).toHaveLength(2);
      expect(result.current.selectedId).toBe('fb-1');
    });

    act(() => {
      result.current.setSelectedId('fb-2');
    });

    await waitFor(() => {
      expect(result.current.detail?.feedbackSubmissionId).toBe('fb-2');
    });

    act(() => {
      result.current.setProcessingStatusFilter('forwarded');
    });

    await waitFor(() => {
      expect(listFeedbackSubmissionsMock).toHaveBeenCalledTimes(2);
      expect(result.current.selectedId).toBe('fb-2');
      expect(result.current.items).toEqual([secondItem]);
    });
  });

  it('handles queue failures by clearing the list and selection', async () => {
    listFeedbackSubmissionsMock.mockRejectedValueOnce(new Error('Queue offline'));

    const { result } = renderHook(() => useFeedbackReview());

    await waitFor(() => {
      expect(result.current.error).toBe('Queue offline');
    });
    expect(result.current.items).toEqual([]);
    expect(result.current.selectedId).toBeNull();
    expect(result.current.isLoadingList).toBe(false);
  });

  it('leaves detail empty when there is no selected submission', async () => {
    listFeedbackSubmissionsMock.mockResolvedValueOnce({ items: [] });

    const { result } = renderHook(() => useFeedbackReview());

    await waitFor(() => {
      expect(result.current.items).toEqual([]);
    });
    expect(result.current.selectedId).toBeNull();
    expect(result.current.detail).toBeNull();
    expect(getFeedbackSubmissionMock).not.toHaveBeenCalled();
  });

  it('handles detail failures without keeping stale detail data', async () => {
    listFeedbackSubmissionsMock.mockResolvedValueOnce({ items: [firstItem] });
    getFeedbackSubmissionMock.mockRejectedValueOnce(new Error('Detail offline'));

    const { result } = renderHook(() => useFeedbackReview());

    await waitFor(() => {
      expect(result.current.error).toBe('Detail offline');
    });
    expect(result.current.detail).toBeNull();
    expect(result.current.isLoadingDetail).toBe(false);
  });

  it('ignores list resolution after the request is aborted on unmount', async () => {
    let resolveList: ((value: { items: typeof firstItem[] }) => void) | undefined;
    listFeedbackSubmissionsMock.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveList = resolve;
        }),
    );

    const view = renderHook(() => useFeedbackReview());
    view.unmount();

    await act(async () => {
      resolveList?.({ items: [firstItem] });
      await Promise.resolve();
    });

    expect(getFeedbackSubmissionMock).not.toHaveBeenCalled();
  });

  it('ignores list rejection after the request is aborted on unmount', async () => {
    let rejectList: ((reason?: unknown) => void) | undefined;
    listFeedbackSubmissionsMock.mockImplementation(
      () =>
        new Promise((_resolve, reject) => {
          rejectList = reject;
        }),
    );

    const view = renderHook(() => useFeedbackReview());
    view.unmount();

    await act(async () => {
      rejectList?.(new Error('Queue offline'));
      await Promise.resolve();
    });

    expect(getFeedbackSubmissionMock).not.toHaveBeenCalled();
  });
});
