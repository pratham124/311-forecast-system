/**
 * Extra coverage for EvaluationPage:
 * - No-access (restricted) state
 * - Error state when API call fails
 * - Product picker pointer-down close behavior
 * - Trigger error fallback and running-poll wait path
 */
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { EvaluationPage } from '../EvaluationPage';

const fetchMock = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock);
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  fetchMock.mockReset();
});

describe('EvaluationPage – restricted access', () => {
  it('renders access-restricted alert when role has no read access', () => {
    render(<EvaluationPage roles={[]} />);
    expect(screen.getByText(/evaluation access is restricted/i)).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /trigger/i })).not.toBeInTheDocument();
  });

  it('renders restricted alert for non-reader role', () => {
    render(<EvaluationPage roles={['DataEngineer']} />);
    expect(screen.getByText(/evaluation access is restricted/i)).toBeInTheDocument();
  });
});

describe('EvaluationPage – error state', () => {
  it('shows error alert when evaluation fetch fails', async () => {
    fetchMock.mockResolvedValue(new Response(JSON.stringify({ detail: 'DB unavailable' }), { status: 500 }));

    render(<EvaluationPage roles={['CityPlanner']} />);
    expect(await screen.findByText(/DB unavailable/i)).toBeInTheDocument();
  });

  it('closes the product picker on outside pointer down and keeps it open for inside clicks', async () => {
    const user = userEvent.setup();
    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          comparisonStatus: 'partial',
          baselineMethods: ['seasonal_naive'],
          fairComparison: {
            evaluationWindowStart: '2026-03-20T00:00:00Z',
            evaluationWindowEnd: '2026-03-20T03:00:00Z',
            segmentCoverage: [],
          },
          updatedAt: '2026-03-25T10:05:00Z',
          segments: [],
          comparisonSummary: null,
          summary: null,
          sourceCleanedDatasetVersionId: null,
          sourceForecastVersionId: null,
          sourceWeeklyForecastVersionId: null,
        }),
        { status: 200 },
      ),
    );

    render(<EvaluationPage roles={['OperationalManager']} />);
    await screen.findByText(/current official evaluation/i);

    const pickerButton = document.getElementById('forecast-product') as HTMLButtonElement;
    expect(pickerButton).toBeTruthy();
    await user.click(pickerButton);
    expect(screen.getByRole('listbox', { name: /time range/i })).toBeInTheDocument();

    fireEvent.mouseDown(pickerButton);
    expect(screen.getByRole('listbox', { name: /time range/i })).toBeInTheDocument();

    fireEvent.mouseDown(document.body);
    await waitFor(() => {
      expect(screen.queryByRole('listbox', { name: /time range/i })).not.toBeInTheDocument();
    });
  });

  it('ignores non-Node pointer targets for the product picker handler', async () => {
    const user = userEvent.setup();
    const addListenerSpy = vi.spyOn(document, 'addEventListener');

    fetchMock.mockResolvedValue(
      new Response(
        JSON.stringify({
          comparisonStatus: 'partial',
          baselineMethods: ['seasonal_naive'],
          fairComparison: {
            evaluationWindowStart: '2026-03-20T00:00:00Z',
            evaluationWindowEnd: '2026-03-20T03:00:00Z',
            segmentCoverage: [],
          },
          updatedAt: '2026-03-25T10:05:00Z',
          segments: [],
          comparisonSummary: null,
          summary: null,
          sourceCleanedDatasetVersionId: null,
          sourceForecastVersionId: null,
          sourceWeeklyForecastVersionId: null,
        }),
        { status: 200 },
      ),
    );

    render(<EvaluationPage roles={['OperationalManager']} />);
    await screen.findByText(/current official evaluation/i);

    const pickerButton = document.getElementById('forecast-product') as HTMLButtonElement;
    await user.click(pickerButton);
    expect(screen.getByRole('listbox', { name: /time range/i })).toBeInTheDocument();

    const pointerHandler = addListenerSpy.mock.calls.find(([name]) => name === 'mousedown')?.[1] as
      | ((event: MouseEvent) => void)
      | undefined;
    expect(pointerHandler).toBeDefined();

    act(() => {
      pointerHandler?.({ target: window } as unknown as MouseEvent);
    });

    expect(screen.getByRole('listbox', { name: /time range/i })).toBeInTheDocument();
    addListenerSpy.mockRestore();
  });

  it('shows load fallback copy when initial fetch rejects with a non-Error value', async () => {
    fetchMock.mockRejectedValueOnce('boom');

    render(<EvaluationPage roles={['CityPlanner']} />);
    expect(await screen.findByText(/unable to load the current evaluation\./i)).toBeInTheDocument();
  });

  it('does not set a load error after unmount aborts the initial request', async () => {
    fetchMock.mockImplementation(
      (_input, init?: RequestInit) =>
        new Promise((_resolve, reject) => {
          const signal = init?.signal;
          signal?.addEventListener('abort', () => {
            reject(new DOMException('Aborted', 'AbortError'));
          });
        }),
    );

    const view = render(<EvaluationPage roles={['CityPlanner']} />);
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

    render(<EvaluationPage roles={['OperationalManager']} />);
    expect(await screen.findByText(/no current evaluation yet/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /trigger daily evaluation/i }));
    expect(await screen.findByText(/unable to trigger the evaluation\./i)).toBeInTheDocument();
  });

  it('shows ApiError detail when trigger returns a structured API failure', async () => {
    const user = userEvent.setup();
    fetchMock
      .mockResolvedValueOnce(new Response('null', { status: 404 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'Trigger blocked by policy' }), { status: 500 }));

    render(<EvaluationPage roles={['OperationalManager']} />);
    expect(await screen.findByText(/no current evaluation yet/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /trigger daily evaluation/i }));
    expect(await screen.findByText(/trigger blocked by policy/i)).toBeInTheDocument();
  });

  it('shows Error.message when trigger throws a standard Error', async () => {
    const user = userEvent.setup();
    fetchMock
      .mockResolvedValueOnce(new Response('null', { status: 404 }))
      .mockRejectedValueOnce(new Error('network down'));

    render(<EvaluationPage roles={['OperationalManager']} />);
    expect(await screen.findByText(/no current evaluation yet/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /trigger daily evaluation/i }));
    expect(await screen.findByText(/network down/i)).toBeInTheDocument();
  });

  it('waits between running polls and refreshes the evaluation after success', async () => {
    const user = userEvent.setup();

    fetchMock
      .mockResolvedValueOnce(new Response('null', { status: 404 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ evaluationRunId: 'eval-run-poll', status: 'running' }), { status: 202 }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            evaluationRunId: 'eval-run-poll',
            status: 'running',
            resultType: null,
            completedAt: null,
            failureReason: null,
            summary: null,
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            evaluationRunId: 'eval-run-poll',
            status: 'success',
            resultType: 'stored_partial',
            completedAt: '2026-03-25T10:05:00Z',
            failureReason: null,
            summary: 'finished',
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            comparisonStatus: 'partial',
            baselineMethods: ['seasonal_naive'],
            fairComparison: {
              evaluationWindowStart: '2026-03-20T00:00:00Z',
              evaluationWindowEnd: '2026-03-20T03:00:00Z',
              segmentCoverage: [],
            },
            updatedAt: '2026-03-25T10:05:00Z',
            segments: [],
            comparisonSummary: 'done',
            summary: null,
            sourceCleanedDatasetVersionId: null,
            sourceForecastVersionId: null,
            sourceWeeklyForecastVersionId: null,
          }),
          { status: 200 },
        ),
      );

    render(<EvaluationPage roles={['OperationalManager']} />);
    expect(await screen.findByText(/no current evaluation yet/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /trigger daily evaluation/i }));

    await waitFor(() => {
      expect(screen.getByText(/latest run status/i)).toBeInTheDocument();
    }, { timeout: 4000 });
    expect(await screen.findByText(/current official evaluation/i, {}, { timeout: 4000 })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledTimes(5);
  });

  it('renders failed run status and metric fallbacks for null values', async () => {
    const user = userEvent.setup();
    fetchMock
      .mockResolvedValueOnce(new Response('null', { status: 404 }))
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ evaluationRunId: 'eval-run-failed', status: 'running' }), { status: 202 }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            evaluationRunId: 'eval-run-failed',
            status: 'failed',
            resultType: 'stored_partial',
            completedAt: '2026-03-25T10:05:00Z',
            failureReason: 'Validation failed',
            summary: null,
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            comparisonStatus: 'partial',
            baselineMethods: ['seasonal_naive'],
            fairComparison: {
              evaluationWindowStart: '2026-03-20T00:00:00Z',
              evaluationWindowEnd: '2026-03-20T03:00:00Z',
              segmentCoverage: ['overall'],
            },
            updatedAt: '2026-03-25T10:05:00Z',
            comparisonSummary: null,
            summary: null,
            sourceCleanedDatasetVersionId: null,
            sourceForecastVersionId: null,
            sourceWeeklyForecastVersionId: null,
            segments: [
              {
                segmentType: 'overall',
                segmentKey: 'overall',
                segmentStatus: 'partial',
                comparisonRowCount: 1,
                excludedMetricCount: 0,
                notes: null,
                methodMetrics: [
                  {
                    methodName: 'Forecast Engine',
                    metrics: [
                      { metricName: 'mae', metricValue: null, isExcluded: false },
                    ],
                  },
                ],
              },
            ],
          }),
          { status: 200 },
        ),
      );

    render(<EvaluationPage roles={['OperationalManager']} />);
    expect(await screen.findByText(/no current evaluation yet/i)).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /trigger daily evaluation/i }));
    expect(await screen.findByText(/latest run status/i)).toBeInTheDocument();
    expect(screen.getAllByText(/^failed$/i).length).toBeGreaterThan(0);
    expect((await screen.findAllByText(/not available/i)).length).toBeGreaterThan(0);
  });

  it('shows non-triggerable no-evaluation message for reader-only roles', async () => {
    fetchMock.mockResolvedValueOnce(new Response('null', { status: 404 }));

    render(<EvaluationPage roles={['CityPlanner']} />);
    expect(await screen.findByText(/no current evaluation yet/i)).toBeInTheDocument();
    expect(screen.getByText(/an operational manager must trigger the first run\./i)).toBeInTheDocument();
  });
});
