import { useEffect, useState } from 'react';
import { getFeedbackSubmission, listFeedbackSubmissions } from '../../../api/feedbackSubmissions';
import type {
  FeedbackSubmissionDetail,
  FeedbackSubmissionSummary,
  ProcessingStatus,
  ReportType,
} from '../../../types/feedbackSubmissions';

export function useFeedbackReview(enabled = true) {
  const [reportTypeFilter, setReportTypeFilter] = useState<ReportType | 'all'>('all');
  const [processingStatusFilter, setProcessingStatusFilter] = useState<ProcessingStatus | 'all'>('all');
  const [items, setItems] = useState<FeedbackSubmissionSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<FeedbackSubmissionDetail | null>(null);
  const [isLoadingList, setIsLoadingList] = useState(true);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!enabled) {
      setItems([]);
      setSelectedId(null);
      setDetail(null);
      setError(null);
      setIsLoadingList(false);
      return;
    }
    const controller = new AbortController();
    setIsLoadingList(true);
    setError(null);
    listFeedbackSubmissions(
      {
        reportType: reportTypeFilter,
        processingStatus: processingStatusFilter,
      },
      controller.signal,
    )
      .then((response) => {
        if (controller.signal.aborted) {
          return;
        }
        setItems(response.items);
        setSelectedId((current) => {
          if (current && response.items.some((item) => item.feedbackSubmissionId === current)) {
            return current;
          }
          return response.items[0]?.feedbackSubmissionId ?? null;
        });
      })
      .catch((requestError: Error) => {
        if (controller.signal.aborted) {
          return;
        }
        setError(requestError.message);
        setItems([]);
        setSelectedId(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoadingList(false);
        }
      });
    return () => controller.abort();
  }, [enabled, processingStatusFilter, reportTypeFilter]);

  useEffect(() => {
    if (!enabled) {
      setIsLoadingDetail(false);
      return;
    }
    if (!selectedId) {
      setDetail(null);
      return;
    }
    const controller = new AbortController();
    setIsLoadingDetail(true);
    getFeedbackSubmission(selectedId, controller.signal)
      .then((response) => {
        if (!controller.signal.aborted) {
          setDetail(response);
        }
      })
      .catch((requestError: Error) => {
        if (!controller.signal.aborted) {
          setError(requestError.message);
          setDetail(null);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setIsLoadingDetail(false);
        }
      });
    return () => controller.abort();
  }, [enabled, selectedId]);

  return {
    reportTypeFilter,
    setReportTypeFilter,
    processingStatusFilter,
    setProcessingStatusFilter,
    items,
    selectedId,
    setSelectedId,
    detail,
    isLoadingList,
    isLoadingDetail,
    error,
  };
}
