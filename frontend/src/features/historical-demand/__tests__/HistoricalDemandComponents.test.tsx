/**
 * Covers uncovered branches in HistoricalDemandFilters and HistoricalDemandStatus.
 */
import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { HistoricalDemandFilters } from '../components/HistoricalDemandFilters';
import { HistoricalDemandResults } from '../components/HistoricalDemandResults';
import { HistoricalDemandStatus } from '../components/HistoricalDemandStatus';
import type { HistoricalDemandFilters as FiltersType, HistoricalDemandResponse } from '../../../types/historicalDemand';

afterEach(cleanup);

// ─── HistoricalDemandFilters ──────────────────────────────────────────────────

const baseFilters: FiltersType = {
  serviceCategory: undefined,
  timeRangeStart: '2026-03-01T00:00:00Z',
  timeRangeEnd: '2026-03-31T23:59:59Z',
};

describe('HistoricalDemandFilters – nullish timeRangeEnd fallback', () => {
  it('renders correctly when timeRangeEnd is undefined (?? empty string branch)', () => {
    const filtersWithNoEnd: FiltersType = {
      serviceCategory: undefined,
      timeRangeStart: '2026-03-01T00:00:00Z',
      timeRangeEnd: undefined as unknown as string,
    };
    render(
      <HistoricalDemandFilters
        context={null}
        filters={filtersWithNoEnd}
        onChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    // timeRangeEnd is undefined → ?? '' → ''.replace('Z', '') = '' → input value is ''
    const endInput = screen.getByLabelText(/^end$/i) as HTMLInputElement;
    expect(endInput.value).toBe('');
  });
});

describe('HistoricalDemandFilters – updateField', () => {
  it('calls onChange with the new value when a field changes', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <HistoricalDemandFilters
        context={{ serviceCategories: ['Roads', 'Waste'], supportedGeographyLevels: ['ward'], summary: '' }}
        filters={baseFilters}
        onChange={onChange}
        onSubmit={vi.fn()}
      />,
    );
    await user.click(screen.getByRole('button', { name: /service category/i }));
    await user.click(screen.getByRole('button', { name: /^Roads$/i }));
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ serviceCategory: 'Roads' }));
  });

  it('calls onChange with undefined when an empty value is selected', async () => {
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(
      <HistoricalDemandFilters
        context={{ serviceCategories: ['Roads'], supportedGeographyLevels: [], summary: '' }}
        filters={{ ...baseFilters, serviceCategory: 'Roads' }}
        onChange={onChange}
        onSubmit={vi.fn()}
      />,
    );
    await user.click(screen.getByRole('button', { name: /service category/i }));
    await user.click(screen.getByRole('button', { name: /all categories/i }));
    expect(onChange).toHaveBeenCalledWith(expect.objectContaining({ serviceCategory: undefined }));
  });

  it('prevents selecting future dates via max=today on date inputs', () => {
    render(
      <HistoricalDemandFilters
        context={null}
        filters={baseFilters}
        onChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    const expectedMax = new Date().toISOString().slice(0, 10);
    expect(screen.getByLabelText(/^start$/i)).toHaveAttribute('max', '2026-03-31');
    expect(screen.getByLabelText(/^end$/i)).toHaveAttribute('max', expectedMax);
    expect(screen.getByLabelText(/^end$/i)).toHaveAttribute('min', '2026-03-01');
  });

  it('disables submit and shows guidance when the end date is before the start date', () => {
    render(
      <HistoricalDemandFilters
        context={null}
        filters={{ ...baseFilters, timeRangeStart: '2026-03-31T00:00:00Z', timeRangeEnd: '2026-03-01T00:00:00Z' }}
        onChange={vi.fn()}
        onSubmit={vi.fn()}
      />,
    );
    expect(screen.getByText(/select a valid start and end date/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /explore historical demand/i })).toBeDisabled();
  });
});

// ─── HistoricalDemandStatus ───────────────────────────────────────────────────

describe('HistoricalDemandStatus', () => {
  it('shows loading state', () => {
    render(<HistoricalDemandStatus isLoading={true} error={null} response={null} onProceed={vi.fn()} onDecline={vi.fn()} />);
    expect(screen.getByText(/loading historical demand/i)).toBeInTheDocument();
  });

  it('shows error state', () => {
    render(<HistoricalDemandStatus isLoading={false} error="Something broke" response={null} onProceed={vi.fn()} onDecline={vi.fn()} />);
    expect(screen.getByText('Something broke')).toBeInTheDocument();
  });

  it('shows warning state with proceed/decline buttons', () => {
    const response = {
      warning: { shown: true, acknowledged: false, message: 'Big request!' },
      outcomeStatus: 'success',
    } as unknown as HistoricalDemandResponse;
    const onProceed = vi.fn();
    const onDecline = vi.fn();
    render(<HistoricalDemandStatus isLoading={false} error={null} response={response} onProceed={onProceed} onDecline={onDecline} />);
    expect(screen.getByText('Big request!')).toBeInTheDocument();
    screen.getByRole('button', { name: /proceed/i }).click();
    expect(onProceed).toHaveBeenCalled();
    screen.getByRole('button', { name: /revise/i }).click();
    expect(onDecline).toHaveBeenCalled();
  });

  it('shows no data state', () => {
    const response = { outcomeStatus: 'no_data', message: 'Nothing found.' } as unknown as HistoricalDemandResponse;
    render(<HistoricalDemandStatus isLoading={false} error={null} response={response} onProceed={vi.fn()} onDecline={vi.fn()} />);
    expect(screen.getByText('Nothing found.')).toBeInTheDocument();
  });

  it('shows retrieval_failed state', () => {
    const response = { outcomeStatus: 'retrieval_failed', summary: 'Could not fetch data.' } as unknown as HistoricalDemandResponse;
    render(<HistoricalDemandStatus isLoading={false} error={null} response={response} onProceed={vi.fn()} onDecline={vi.fn()} />);
    expect(screen.getByText('Could not fetch data.')).toBeInTheDocument();
  });

  it('shows render_failed state', () => {
    const response = { outcomeStatus: 'render_failed', message: 'Render failed.' } as unknown as HistoricalDemandResponse;
    render(<HistoricalDemandStatus isLoading={false} error={null} response={response} onProceed={vi.fn()} onDecline={vi.fn()} />);
    expect(screen.getByText('Render failed.')).toBeInTheDocument();
  });

  it('returns null when no relevant state', () => {
    const { container } = render(<HistoricalDemandStatus isLoading={false} error={null} response={null} onProceed={vi.fn()} onDecline={vi.fn()} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('shows no_data without message (uses fallback text)', () => {
    // Covers line 34: response?.message ?? 'No historical demand data matched...'
    const response = { outcomeStatus: 'no_data' } as unknown as HistoricalDemandResponse;
    render(<HistoricalDemandStatus isLoading={false} error={null} response={response} onProceed={vi.fn()} onDecline={vi.fn()} />);
    expect(screen.getByText(/no historical demand data matched/i)).toBeInTheDocument();
  });

  it('shows retrieval_failed without summary (uses message ?? fallback)', () => {
    // Covers line 37: response.summary ?? response.message ?? 'We could not display...'
    const response = { outcomeStatus: 'retrieval_failed' } as unknown as HistoricalDemandResponse;
    render(<HistoricalDemandStatus isLoading={false} error={null} response={response} onProceed={vi.fn()} onDecline={vi.fn()} />);
    expect(screen.getByText(/we could not display historical demand data/i)).toBeInTheDocument();
  });
});

// ─── HistoricalDemandResults ──────────────────────────────────────────────────

describe('HistoricalDemandResults', () => {
  it('returns null when summaryPoints is empty', () => {
    const response = {
      summaryPoints: [],
    } as unknown as HistoricalDemandResponse;
    const { container } = render(<HistoricalDemandResults response={response} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders stable date labels without showing a geography column', () => {
    const response = {
      summaryPoints: [
        {
          bucketStart: '2026-03-05T00:00:00Z',
          serviceCategory: 'Roads',
          geographyKey: null,
          demandCount: 5,
        },
      ],
    } as unknown as HistoricalDemandResponse;
    render(<HistoricalDemandResults response={response} />);
    expect(screen.getByText(/historical demand pattern/i)).toBeInTheDocument();
    expect(screen.getByText(/demand count/i)).toBeInTheDocument();
    expect(screen.queryByText('Ward 1')).not.toBeInTheDocument();
    expect(screen.getAllByText('2026-03-05').length).toBeGreaterThan(0);
  });
});
