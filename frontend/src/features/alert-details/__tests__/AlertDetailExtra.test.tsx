import { act, render, renderHook, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { AlertDetailPanel } from '../AlertDetailPanel';
import { useAlertDetail } from '../useAlertDetail';
import type { AlertSummary } from '../../../types/alertDetails';

vi.mock('../../../api/alertDetails', () => ({
  fetchAlertDetail: vi.fn(),
  submitAlertDetailRenderEvent: vi.fn(),
}));

import { fetchAlertDetail, submitAlertDetailRenderEvent } from '../../../api/alertDetails';

describe('alert detail extra coverage', () => {
  beforeEach(() => {
    vi.spyOn(console, 'error').mockImplementation(() => undefined);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders selected surge and geography details', () => {
    const onRenderSuccess = vi.fn();
    const onRenderFailure = vi.fn();

    render(
      <AlertDetailPanel
        selectedAlert={{
          alertId: 'alert-1',
          alertSource: 'surge_alert',
          sourceLabel: 'Surge',
          serviceCategory: 'Waste',
          windowStart: '2026-03-01T00:00:00Z',
          windowEnd: '2026-03-01T01:00:00Z',
          primaryMetricLabel: 'Actual',
          primaryMetricValue: 9,
          secondaryMetricLabel: 'Forecast',
          secondaryMetricValue: 3,
          overallDeliveryStatus: 'manual_review_required',
        } as never}
        detail={{
          alertDetailLoadId: 'detail-1',
          alertId: 'alert-1',
          alertSource: 'surge_alert',
          alertTriggeredAt: '2026-03-01T00:00:00Z',
          primaryMetricLabel: 'Actual',
          primaryMetricValue: 9,
          secondaryMetricLabel: 'Forecast',
          secondaryMetricValue: 3,
          overallDeliveryStatus: 'manual_review_required',
          windowStart: '2026-03-01T00:00:00Z',
          windowEnd: '2026-03-01T01:00:00Z',
          viewStatus: 'rendered',
          scope: { geographyType: null, geographyValue: 'Northwest', serviceCategory: 'Waste' },
          distribution: { status: 'unavailable', points: [], unavailableReason: 'No distribution' },
          drivers: { status: 'unavailable', drivers: [], unavailableReason: 'No drivers' },
          anomalies: {
            status: 'available',
            items: [
              {
                surgeCandidateId: 'candidate-1',
                evaluationWindowStart: '2026-03-01T00:00:00Z',
                evaluationWindowEnd: '2026-03-01T01:00:00Z',
                actualDemandValue: 9,
                forecastP50Value: null,
                residualZScore: null,
                percentAboveForecast: 50,
                candidateStatus: 'pending_review',
                confirmationOutcome: 'confirmed_surge',
                isSelectedAlert: true,
              },
            ],
          },
        } as never}
        isLoading={false}
        error={null}
        onRenderSuccess={onRenderSuccess}
        onRenderFailure={onRenderFailure}
      />,
    );

    expect(screen.getByText(/geography: northwest/i)).toBeInTheDocument();
    expect(screen.getByText(/selected surge/i)).toBeInTheDocument();
    expect(screen.getByText(/confirmed surge/i)).toBeInTheDocument();
    expect(screen.getAllByText(/^n\/a$/i)).toHaveLength(2);
    expect(onRenderSuccess).toHaveBeenCalledWith('detail-1');
    expect(onRenderFailure).not.toHaveBeenCalled();
  });

  it('shows placeholder and load errors when detail is unavailable', () => {
    const onRenderSuccess = vi.fn();
    const onRenderFailure = vi.fn();
    const { rerender } = render(
      <AlertDetailPanel
        selectedAlert={null}
        detail={null}
        isLoading={false}
        error={null}
        onRenderSuccess={onRenderSuccess}
        onRenderFailure={onRenderFailure}
      />,
    );

    expect(screen.getByText(/select an alert from the list/i)).toBeInTheDocument();

    rerender(
      <AlertDetailPanel
        selectedAlert={{
          alertId: 'alert-2',
          alertSource: 'threshold_alert',
          sourceLabel: 'Threshold',
          serviceCategory: 'Roads',
          windowStart: '2026-03-01T00:00:00Z',
          windowEnd: '2026-03-01T01:00:00Z',
          primaryMetricLabel: 'Forecast',
          primaryMetricValue: 11,
          secondaryMetricLabel: 'Threshold',
          secondaryMetricValue: 8,
          overallDeliveryStatus: 'partial_delivery',
        } as never}
        detail={null}
        isLoading
        error="request failed"
        onRenderSuccess={onRenderSuccess}
        onRenderFailure={onRenderFailure}
      />,
    );

    expect(screen.getByText(/loading alert detail while keeping the selected alert context visible/i)).toBeInTheDocument();
    expect(screen.getByText(/unable to load alert detail/i)).toBeInTheDocument();
    expect(screen.getByText(/request failed/i)).toBeInTheDocument();
  });

  it('resets state for a null alert and deduplicates render events', async () => {
    vi.mocked(fetchAlertDetail).mockResolvedValue({
      alertDetailLoadId: 'detail-2',
    } as never);
    vi.mocked(submitAlertDetailRenderEvent).mockRejectedValue(new Error('network'));

    const { result, rerender } = renderHook(
      ({ selectedAlert }) => useAlertDetail(selectedAlert),
      {
        initialProps: {
          selectedAlert: {
            alertId: 'alert-2',
            alertSource: 'threshold_alert',
          } as AlertSummary,
        },
      } as { initialProps: { selectedAlert: AlertSummary | null } },
    );

    await waitFor(() => {
      expect(result.current.detail?.alertDetailLoadId).toBe('detail-2');
    });

    act(() => {
      result.current.reportRenderSuccess('detail-2');
      result.current.reportRenderSuccess('detail-2');
      result.current.reportRenderFailure('boom');
    });

    expect(submitAlertDetailRenderEvent).toHaveBeenCalledTimes(1);

    rerender({ selectedAlert: null });
    expect(result.current.detail).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('uses the generic load error for non-Error rejections', async () => {
    vi.mocked(fetchAlertDetail).mockRejectedValue('unexpected');

    const { result } = renderHook(() =>
      useAlertDetail({
        alertId: 'alert-3',
        alertSource: 'threshold_alert',
      } as never),
    );

    await waitFor(() => {
      expect(result.current.error).toBe('Unable to load alert detail.');
    });
  });
});
