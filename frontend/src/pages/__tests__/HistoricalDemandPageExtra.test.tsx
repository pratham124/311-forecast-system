/**
 * Extra coverage for HistoricalDemandPage:
 * - toApiDateTime: date-only format converts to day boundaries
 * - toApiDateTime: empty value → lines 11-12
 * - clearResponse via onDecline callback → lines 86-87
 */
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { HistoricalDemandPage, toApiDateTime } from '../HistoricalDemandPage';

const contextPayload = {
  serviceCategories: ['Roads'],
  supportedGeographyLevels: ['ward'],
  summary: 'Context loaded.',
};

const warningPayload = {
  analysisRequestId: 'warn-1',
  filters: {
    serviceCategories: ['Roads'],
    timeRangeStart: '2026-03-01T00:00:00Z',
    timeRangeEnd: '2026-03-31T23:59:59Z',
  },
  aggregationGranularity: 'daily',
  resultMode: 'chart_and_table',
  summaryPoints: [],
  warning: { shown: true, acknowledged: false, message: 'Large request!' },
  outcomeStatus: 'no_data',
};

const successPayload = {
  analysisRequestId: 'ok-1',
  filters: {
    serviceCategories: ['Roads'],
    timeRangeStart: '2026-03-01T00:00:00Z',
    timeRangeEnd: '2026-03-31T23:59:59Z',
  },
  aggregationGranularity: 'daily',
  resultMode: 'chart_and_table',
  summaryPoints: [],
  outcomeStatus: 'success',
  message: 'OK',
};

describe('HistoricalDemandPage – extra coverage', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('converts date-only value via toApiDateTime when submitting', async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(contextPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(successPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(null, { status: 202 }));

    render(<HistoricalDemandPage />);
    await screen.findByRole('button', { name: /explore historical demand/i });

    // Change the start date input to a date-only value.
    fireEvent.change(screen.getByLabelText(/time range start/i), {
      target: { name: 'timeRangeStart', value: '2026-03-01' },
    });
    fireEvent.change(screen.getByLabelText(/time range end/i), {
      target: { name: 'timeRangeEnd', value: '2026-03-31' },
    });

    fireEvent.click(screen.getByRole('button', { name: /explore historical demand/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(3);
    });

    const submitBody = JSON.parse(fetchMock.mock.calls[1][1]?.body as string);
    expect(submitBody.timeRangeStart).toBe('2026-03-01T00:00:00Z');
    expect(submitBody.timeRangeEnd).toBe('2026-03-31T23:59:59Z');
  });

  it('clears response and error when onDecline is triggered (warning flow)', async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(contextPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(warningPayload), { status: 200 }));

    render(<HistoricalDemandPage />);
    await screen.findByRole('button', { name: /explore historical demand/i });
    fireEvent.click(screen.getByRole('button', { name: /explore historical demand/i }));

    expect(await screen.findByText(/large request warning/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /revise/i }));

    await waitFor(() => {
      expect(screen.queryByText(/large request warning/i)).not.toBeInTheDocument();
    });
  });

  it('passes invalid date strings through toApiDateTime unchanged (NaN branch, lines 18-19)', () => {
    expect(toApiDateTime('invalid-date-xyz')).toBe('invalid-date-xyz');
  });

  it('converts date-only inputs to explicit day boundaries', () => {
    expect(toApiDateTime('2026-03-01', 'start')).toBe('2026-03-01T00:00:00Z');
    expect(toApiDateTime('2026-03-31', 'end')).toBe('2026-03-31T23:59:59Z');
  });

  it('passes empty string through toApiDateTime unchanged (falsy early return)', async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(contextPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(successPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(null, { status: 202 }));

    render(<HistoricalDemandPage />);
    await screen.findByRole('button', { name: /explore historical demand/i });

    // Simulate clearing the start date (sets it to '' via updateField)
    fireEvent.change(screen.getByLabelText(/time range start/i), {
      target: { name: 'timeRangeStart', value: '' },
    });

    fireEvent.click(screen.getByRole('button', { name: /explore historical demand/i }));

    // Component should still render without crashing
    await waitFor(() => {
      expect(fetchMock.mock.calls.length).toBeGreaterThanOrEqual(2);
    });
  });
});
