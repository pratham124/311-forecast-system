import { useEffect, useRef, useState } from 'react';
import { fetchAlertDetail, submitAlertDetailRenderEvent } from '../../api/alertDetails';
import type { AlertDetail, AlertSummary } from '../../types/alertDetails';

export function useAlertDetail(selectedAlert: AlertSummary | null) {
  const [detail, setDetail] = useState<AlertDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const reportedLoadIdsRef = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!selectedAlert) {
      setDetail(null);
      setIsLoading(false);
      setError(null);
      return;
    }

    let isActive = true;
    setDetail(null);
    setIsLoading(true);
    setError(null);

    void fetchAlertDetail(selectedAlert.alertSource, selectedAlert.alertId)
      .then((response) => {
        if (!isActive) return;
        setDetail(response);
      })
      .catch((requestError) => {
        if (!isActive) return;
        setError(requestError instanceof Error ? requestError.message : 'Unable to load alert detail.');
      })
      .finally(() => {
        if (!isActive) return;
        setIsLoading(false);
      });

    return () => {
      isActive = false;
    };
  }, [selectedAlert?.alertId, selectedAlert?.alertSource]);

  function reportRenderSuccess(alertDetailLoadId: string): void {
    if (reportedLoadIdsRef.current.has(alertDetailLoadId)) {
      return;
    }
    reportedLoadIdsRef.current.add(alertDetailLoadId);
    void submitAlertDetailRenderEvent(alertDetailLoadId, { renderStatus: 'rendered' }).catch(() => undefined);
  }

  function reportRenderFailure(reason: string): void {
    const alertDetailLoadId = detail?.alertDetailLoadId;
    if (!alertDetailLoadId || reportedLoadIdsRef.current.has(alertDetailLoadId)) {
      return;
    }
    reportedLoadIdsRef.current.add(alertDetailLoadId);
    void submitAlertDetailRenderEvent(alertDetailLoadId, {
      renderStatus: 'render_failed',
      failureReason: reason,
    }).catch(() => undefined);
  }

  return {
    detail,
    isLoading,
    error,
    reportRenderSuccess,
    reportRenderFailure,
  };
}
