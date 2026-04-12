import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { saveAuthSession } from '../lib/authSession';
import { formatIngestionResultType, formatUpdatedDateTime, IngestionPage } from './IngestionPage';

const currentDataset = {
  source_name: 'edmonton_311',
  dataset_version_id: 'dataset-1',
  updated_at: '2026-03-26T16:00:00Z',
  updated_by_run_id: 'run-1',
  record_count: 321,
  latest_requested_at: '2026-03-26T15:45:00Z',
};

describe('IngestionPage', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    saveAuthSession({
      accessToken: 'token-1',
      user: { userAccountId: 'user-1', email: 'manager@example.com', roles: ['OperationalManager'] },
    });
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    window.localStorage.clear();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('loads the current dataset for planner access and hides the trigger button', async () => {
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify(currentDataset), { status: 200 }));

    render(<IngestionPage roles={['CityPlanner']} />);

    expect(await screen.findByText(/record count/i)).toBeInTheDocument();
    expect(await screen.findByText(String(currentDataset.record_count))).toBeInTheDocument();
    expect(screen.getByText(/latest source activity/i)).toBeInTheDocument();
    expect(screen.getByText(formatUpdatedDateTime(currentDataset.latest_requested_at))).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /trigger 311 ingestion/i })).not.toBeInTheDocument();
    expect(String(fetchMock.mock.calls[0][0])).toContain('/api/v1/datasets/current');
  });

  it('triggers a run for operational managers, polls status, and refreshes the current dataset', async () => {
    const user = userEvent.setup();
    fetchMock
      .mockResolvedValueOnce(new Response('null', { status: 404 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ run_id: 'run-2', status: 'running' }), { status: 202 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({
        run_id: 'run-2',
        status: 'success',
        result_type: 'new_data_applied',
        started_at: '2026-03-26T16:00:00Z',
        completed_at: '2026-03-26T16:03:00Z',
        cursor_used: 'cursor-1',
        cursor_advanced: true,
        candidate_dataset_id: 'candidate-1',
        dataset_version_id: 'dataset-2',
        records_received: 42,
        failure_reason: null,
      }), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ ...currentDataset, dataset_version_id: 'dataset-2', updated_by_run_id: 'run-2', latest_requested_at: '2026-03-26T16:02:00Z' }), { status: 200 }));

    render(<IngestionPage roles={['OperationalManager']} />);
    expect(await screen.findByText(/no current dataset yet/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /trigger 311 ingestion/i }));

    await waitFor(() => {
      expect(screen.getByText(/latest run status/i)).toBeInTheDocument();
    });
    expect(screen.getByText(formatIngestionResultType('new_data_applied'))).toBeInTheDocument();
    expect(await screen.findByText(String(currentDataset.record_count))).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(4);
    expect(String(fetchMock.mock.calls[1][0])).toContain('/api/v1/ingestion-runs/311/trigger');
    expect(String(fetchMock.mock.calls[2][0])).toContain('/api/v1/ingestion-runs/run-2');
  });
});
