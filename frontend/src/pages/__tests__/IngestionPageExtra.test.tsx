/**
 * Extra coverage for IngestionPage:
 * - No-access (restricted) state
 * - Error state after API failure
 * - Trigger error fallback and running-poll wait path
 */
import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { IngestionPage } from '../IngestionPage';

const fetchMock = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  fetchMock.mockReset();
});

const noAccessDataset = null;

describe('IngestionPage – restricted access', () => {
  it('shows access-restricted alert when role has no read access', () => {
    render(<IngestionPage roles={[]} />);
    expect(screen.getByText(/311 ingestion access is restricted/i)).toBeInTheDocument();
  });

  it('shows access-restricted alert for non-reader role', () => {
    render(<IngestionPage roles={['DataEngineer']} />);
    expect(screen.getByText(/311 ingestion access is restricted/i)).toBeInTheDocument();
  });
});

describe('IngestionPage – error state', () => {
  it('shows error alert when dataset fetch fails', async () => {
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ detail: 'Dataset unavailable' }), { status: 500 }),
    );

    render(<IngestionPage roles={['CityPlanner']} />);
    expect(await screen.findByText(/ingestion request failed/i)).toBeInTheDocument();
  });

    it('shows load fallback copy when initial dataset request rejects with a non-Error value', async () => {
      fetchMock.mockRejectedValueOnce('boom');

      render(<IngestionPage roles={['CityPlanner']} />);
      expect(await screen.findByText(/unable to load the current dataset\./i)).toBeInTheDocument();
    });

    it('does not set load error after unmount aborts the initial dataset request', async () => {
      fetchMock.mockImplementation(
        (_input, init?: RequestInit) =>
          new Promise((_resolve, reject) => {
            const signal = init?.signal;
            signal?.addEventListener('abort', () => {
              reject(new DOMException('Aborted', 'AbortError'));
            });
          }),
      );

      const view = render(<IngestionPage roles={['CityPlanner']} />);
      view.unmount();

      await waitFor(() => {
        expect(fetchMock).toHaveBeenCalledTimes(1);
      });
    });

  it('shows generic trigger failure when a non-Error is thrown', async () => {
    const user = userEvent.setup();
    fetchMock
      .mockResolvedValueOnce(new Response('null', { status: 404 }))
      .mockRejectedValueOnce('unexpected trigger failure');

    render(<IngestionPage roles={['OperationalManager']} />);
    expect(await screen.findByText(/no current dataset yet/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /trigger 311 ingestion/i }));
    expect(await screen.findByText(/unable to trigger 311 ingestion\./i)).toBeInTheDocument();
  });

    it('shows ApiError detail when trigger returns a structured API failure', async () => {
      const user = userEvent.setup();
      fetchMock
        .mockResolvedValueOnce(new Response('null', { status: 404 }))
        .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'Trigger blocked by policy' }), { status: 500 }));

      render(<IngestionPage roles={['OperationalManager']} />);
      expect(await screen.findByText(/no current dataset yet/i)).toBeInTheDocument();

      await user.click(screen.getByRole('button', { name: /trigger 311 ingestion/i }));
      expect(await screen.findByText(/trigger blocked by policy/i)).toBeInTheDocument();
    });

    it('shows Error.message when trigger throws a standard Error', async () => {
      const user = userEvent.setup();
      fetchMock
        .mockResolvedValueOnce(new Response('null', { status: 404 }))
        .mockRejectedValueOnce(new Error('network down'));

      render(<IngestionPage roles={['OperationalManager']} />);
      expect(await screen.findByText(/no current dataset yet/i)).toBeInTheDocument();

      await user.click(screen.getByRole('button', { name: /trigger 311 ingestion/i }));
      expect(await screen.findByText(/network down/i)).toBeInTheDocument();
    });

  it('waits between running polls and refreshes dataset after completion', async () => {
    const user = userEvent.setup();

    fetchMock
      .mockResolvedValueOnce(new Response('null', { status: 404 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ run_id: 'run-poll', status: 'running' }), { status: 202 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            run_id: 'run-poll',
            status: 'running',
            started_at: '2026-03-26T16:00:00Z',
            cursor_advanced: true,
            result_type: null,
            records_received: null,
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            run_id: 'run-poll',
            status: 'success',
            started_at: '2026-03-26T16:00:00Z',
            cursor_advanced: true,
            result_type: 'new_data_applied',
            records_received: 42,
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            source_name: 'edmonton_311',
            dataset_version_id: 'dataset-poll',
            updated_at: '2026-03-26T16:00:00Z',
            updated_by_run_id: 'run-poll',
            record_count: 321,
            latest_requested_at: '2026-03-26T15:45:00Z',
          }),
          { status: 200 },
        ),
      );

    render(<IngestionPage roles={['OperationalManager']} />);
    expect(await screen.findByText(/no current dataset yet/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /trigger 311 ingestion/i }));

    await waitFor(() => {
      expect(screen.getByText(/latest run status/i)).toBeInTheDocument();
    }, { timeout: 4000 });
    expect(await screen.findByText(/latest 311 requested_at in stored data/i, {}, { timeout: 4000 })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(5);
  });

    it('renders failed run status tone and non-triggerable no-dataset message branches', async () => {
      const user = userEvent.setup();
      fetchMock
        .mockResolvedValueOnce(new Response('null', { status: 404 }))
        .mockResolvedValueOnce(new Response(JSON.stringify({ run_id: 'run-failed', status: 'running' }), { status: 202 }))
        .mockResolvedValueOnce(
          new Response(
            JSON.stringify({
              run_id: 'run-failed',
              status: 'failed',
              started_at: '2026-03-26T16:00:00Z',
              completed_at: '2026-03-26T16:01:00Z',
              cursor_advanced: false,
              result_type: 'stored_partial',
              records_received: 0,
              failure_reason: 'Validation failed',
            }),
            { status: 200 },
          ),
        )
        .mockResolvedValueOnce(
          new Response(
            JSON.stringify({
              source_name: 'edmonton_311',
              dataset_version_id: 'dataset-failed',
              updated_at: '2026-03-26T16:01:00Z',
              updated_by_run_id: 'run-failed',
              record_count: 123,
              latest_requested_at: '2026-03-26T15:45:00Z',
            }),
            { status: 200 },
          ),
        );

      render(<IngestionPage roles={['OperationalManager']} />);
      expect(await screen.findByText(/no current dataset yet/i)).toBeInTheDocument();
      await user.click(screen.getByRole('button', { name: /trigger 311 ingestion/i }));

      expect(await screen.findByText(/latest run status/i)).toBeInTheDocument();
      expect(screen.getByText(/^failed$/i)).toBeInTheDocument();

      cleanup();
      fetchMock.mockReset();
      fetchMock.mockResolvedValueOnce(new Response('null', { status: 404 }));
      render(<IngestionPage roles={['CityPlanner']} />);
      expect(await screen.findByText(/no current dataset yet/i)).toBeInTheDocument();
      expect(screen.getByText(/an operational manager must trigger the first ingestion run\./i)).toBeInTheDocument();
    });
});
