import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../api/forecastAlerts', () => ({
  createThresholdConfiguration: vi.fn(),
  deleteThresholdConfiguration: vi.fn(),
  fetchThresholdAlertConfigurations: vi.fn(),
  fetchThresholdAlertEvents: vi.fn(),
  fetchThresholdServiceCategories: vi.fn(),
  updateThresholdConfiguration: vi.fn(),
}));

vi.mock('../../api/surgeAlerts', () => ({
  fetchSurgeEvents: vi.fn(),
}));

vi.mock('../../features/alert-details', () => ({
  AlertDetailPanel: ({ selectedAlert }: { selectedAlert: { serviceCategory?: string } | null }) => (
    <div>{selectedAlert ? `detail:${selectedAlert.serviceCategory}` : 'detail:none'}</div>
  ),
  useAlertDetail: () => ({
    detail: null,
    isLoading: false,
    error: null,
    reportRenderSuccess: vi.fn(),
    reportRenderFailure: vi.fn(),
  }),
}));

vi.mock('../../features/surge_alerts', () => ({
  SurgeAlertReview: () => <div>surge review mocked</div>,
}));

import {
  createThresholdConfiguration,
  deleteThresholdConfiguration,
  fetchThresholdAlertConfigurations,
  fetchThresholdAlertEvents,
  fetchThresholdServiceCategories,
  updateThresholdConfiguration,
} from '../../api/forecastAlerts';
import { fetchSurgeEvents } from '../../api/surgeAlerts';
import { AlertReviewPage } from '../AlertReviewPage';

describe('AlertReviewPage extra coverage', () => {
  beforeEach(() => {
    vi.mocked(fetchThresholdServiceCategories).mockResolvedValue(['Roads', 'Waste']);
    vi.mocked(fetchThresholdAlertConfigurations).mockResolvedValue([]);
    vi.mocked(fetchThresholdAlertEvents).mockResolvedValue([]);
    vi.mocked(fetchSurgeEvents).mockResolvedValue([]);
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('renders restricted access for non-reader roles', () => {
    render(<AlertReviewPage roles={['Guest']} />);
    expect(screen.getByText(/alert access is restricted/i)).toBeInTheDocument();
  });

  it('renders empty alert states for readers without write access and switches panels', async () => {
    const user = userEvent.setup();
    render(<AlertReviewPage roles={['CityPlanner']} />);

    expect(await screen.findByText(/no thresholds configured yet/i)).toBeInTheDocument();
    expect(screen.queryByText(/add threshold/i)).not.toBeInTheDocument();
    expect(screen.getByText(/no threshold or surge alerts have been recorded yet/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /surge evaluations/i }));
    expect(screen.getByText(/surge review mocked/i)).toBeInTheDocument();
  });

  it('shows threshold validation errors for writers', async () => {
    render(<AlertReviewPage roles={['OperationalManager']} />);
    await screen.findByText(/add threshold/i);

    fireEvent.click(screen.getByRole('button', { name: /save threshold/i }));
    expect(await screen.findByText(/select a service category\./i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /^service category$/i }));
    fireEvent.click(screen.getByRole('button', { name: /^roads$/i }));
    fireEvent.change(screen.getByLabelText(/threshold value/i), { target: { value: '0' } });
    fireEvent.click(screen.getByRole('button', { name: /save threshold/i }));
    expect(await screen.findByText(/enter a whole-number threshold value of at least 1\./i)).toBeInTheDocument();
  });

  it('supports edit, save, refresh, delete, and dropdown dismissal flows for writers', async () => {
    vi.mocked(fetchThresholdAlertConfigurations)
      .mockResolvedValueOnce([
        {
          thresholdConfigurationId: 'threshold-1',
          serviceCategory: 'Roads',
          forecastWindowType: 'hourly',
          thresholdValue: 8,
          status: 'active',
        } as never,
      ])
      .mockResolvedValueOnce([
        {
          thresholdConfigurationId: 'threshold-1',
          serviceCategory: 'Roads',
          forecastWindowType: 'daily',
          thresholdValue: 12,
          status: 'active',
        } as never,
      ]);
    vi.mocked(fetchThresholdAlertEvents)
      .mockResolvedValueOnce([
        {
          notificationEventId: 'event-1',
          serviceCategory: 'Roads',
          forecastWindowType: 'hourly',
          forecastWindowStart: '2026-03-01T00:00:00Z',
          forecastWindowEnd: '2026-03-01T01:00:00Z',
          forecastValue: 12,
          thresholdValue: 8,
          overallDeliveryStatus: 'delivered',
          createdAt: '2026-03-01T00:05:00Z',
        } as never,
      ])
      .mockResolvedValueOnce([])
      .mockResolvedValue([]);
    vi.mocked(fetchSurgeEvents).mockResolvedValue([]);
    vi.mocked(updateThresholdConfiguration).mockResolvedValue({
      thresholdConfigurationId: 'threshold-1',
      serviceCategory: 'Roads',
      forecastWindowType: 'daily',
      thresholdValue: 12,
      status: 'active',
    } as never);
    vi.mocked(deleteThresholdConfiguration).mockResolvedValue(undefined);

    render(<AlertReviewPage roles={['OperationalManager']} />);

    await screen.findByText(/alert at/i);

    fireEvent.click(screen.getByRole('button', { name: /edit/i }));
    expect(screen.getByRole('button', { name: /update threshold/i })).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /forecast window/i }));
    fireEvent.mouseDown(document.body);
    expect(screen.queryByRole('listbox', { name: /forecast window/i })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /forecast window/i }));
    fireEvent.click(screen.getByRole('button', { name: /^daily$/i }));
    fireEvent.change(screen.getByLabelText(/threshold value/i), { target: { value: '12' } });
    fireEvent.click(screen.getByRole('button', { name: /update threshold/i }));

    await waitFor(() => {
      expect(updateThresholdConfiguration).toHaveBeenCalledWith('threshold-1', expect.objectContaining({
        forecastWindowType: 'daily',
        thresholdValue: 12,
      }));
    });

    await new Promise((resolve) => setTimeout(resolve, 1100));

    await waitFor(() => {
      expect(fetchThresholdAlertEvents).toHaveBeenCalledTimes(2);
      expect(fetchSurgeEvents).toHaveBeenCalledTimes(2);
    });

    fireEvent.click(screen.getByRole('button', { name: /edit/i }));
    fireEvent.click(screen.getByRole('button', { name: /delete/i }));

    await waitFor(() => {
      expect(deleteThresholdConfiguration).toHaveBeenCalledWith('threshold-1');
    });
    expect(screen.getByRole('button', { name: /save threshold/i })).toBeInTheDocument();
  }, 15000);
});
