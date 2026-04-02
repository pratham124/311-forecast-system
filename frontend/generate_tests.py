import os
import textwrap

tests_dir = "frontend/src/features/demand-comparisons/__tests__"
os.makedirs(tests_dir, exist_ok=True)

filters_test = """\
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ComparisonFilters } from '../components/ComparisonFilters';
import type { DemandComparisonContext, DemandComparisonFilters } from '../../../types/demandComparisons';

describe('ComparisonFilters', () => {
  const mockContext: DemandComparisonContext = {
    serviceCategories: ['Category A', 'Category B'],
    geographyLevels: ['borocd', 'precinct'],
    geographyOptions: {
      borocd: ['Bronx 1', 'Bronx 2'],
      precinct: ['001', '002']
    }
  };

  const defaultFilters: DemandComparisonFilters = {
    serviceCategories: [],
    geographyValues: [],
    timeRangeStart: '2023-01-01T00:00:00.000Z',
    timeRangeEnd: '2023-01-08T00:00:00.000Z'
  };

  it('renders with empty context and disabled state', () => {
    const onChange = vi.fn();
    const onSubmit = vi.fn();
    render(<ComparisonFilters context={null} filters={defaultFilters} onChange={onChange} onSubmit={onSubmit} disabled={true} />);
    expect(screen.getByText('Service categories')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Compare demand' })).toBeDisabled();
  });

  it('toggles service categories correctly', () => {
    const onChange = vi.fn();
    const onSubmit = vi.fn();
    const { rerender } = render(
      <ComparisonFilters context={mockContext} filters={defaultFilters} onChange={onChange} onSubmit={onSubmit} />
    );

    // Initial click -> add
    const btnA = screen.getByRole('button', { name: 'Category A' });
    fireEvent.click(btnA);
    expect(onChange).toHaveBeenCalledWith({ ...defaultFilters, serviceCategories: ['Category A'] });

    // Rerender with Category A checked to test unchecking
    rerender(
      <ComparisonFilters context={mockContext} filters={{ ...defaultFilters, serviceCategories: ['Category A', 'Category B'] }} onChange={onChange} onSubmit={onSubmit} />
    );
    const btnAChecked = screen.getByRole('button', { name: 'Category A' });
    fireEvent.click(btnAChecked);
    expect(onChange).toHaveBeenCalledWith({ ...defaultFilters, serviceCategories: ['Category B'] });
  });

  it('handles geography level changes', () => {
    const onChange = vi.fn();
    render(<ComparisonFilters context={mockContext} filters={defaultFilters} onChange={onChange} onSubmit={vi.fn()} />);
    
    const select = screen.getByLabelText('Geography level');
    fireEvent.change(select, { target: { value: 'borocd' } });
    expect(onChange).toHaveBeenCalledWith({ ...defaultFilters, geographyLevel: 'borocd', geographyValues: [] });

    fireEvent.change(select, { target: { value: '' } });
    expect(onChange).toHaveBeenCalledWith({ ...defaultFilters, geographyLevel: undefined, geographyValues: [] });
  });

  it('toggles geography values correctly when level is selected', () => {
    const onChange = vi.fn();
    const filtersWithGeo: DemandComparisonFilters = { ...defaultFilters, geographyLevel: 'borocd' };
    const { rerender } = render(
      <ComparisonFilters context={mockContext} filters={filtersWithGeo} onChange={onChange} onSubmit={vi.fn()} />
    );

    const btnBronx1 = screen.getByRole('button', { name: 'Bronx 1' });
    fireEvent.click(btnBronx1);
    expect(onChange).toHaveBeenCalledWith({ ...filtersWithGeo, geographyValues: ['Bronx 1'] });

    rerender(
      <ComparisonFilters context={mockContext} filters={{ ...filtersWithGeo, geographyValues: ['Bronx 1', 'Bronx 2'] }} onChange={onChange} onSubmit={vi.fn()} />
    );
    const btnBronx1Checked = screen.getByRole('button', { name: 'Bronx 1' });
    fireEvent.click(btnBronx1Checked);
    expect(onChange).toHaveBeenCalledWith({ ...filtersWithGeo, geographyValues: ['Bronx 2'] });
  });

  it('handles date range changes', () => {
    const onChange = vi.fn();
    render(<ComparisonFilters context={mockContext} filters={defaultFilters} onChange={onChange} onSubmit={vi.fn()} />);

    const startInput = screen.getByLabelText('Start');
    fireEvent.change(startInput, { target: { value: '2023-01-02T10:00' } });
    expect(onChange).toHaveBeenCalledWith({ ...defaultFilters, timeRangeStart: new Date('2023-01-02T10:00').toISOString() });

    const endInput = screen.getByLabelText('End');
    fireEvent.change(endInput, { target: { value: '2023-01-09T10:00' } });
    expect(onChange).toHaveBeenCalledWith({ ...defaultFilters, timeRangeEnd: new Date('2023-01-09T10:00').toISOString() });
  });

  it('submits correctly', () => {
    const onSubmit = vi.fn();
    render(<ComparisonFilters context={mockContext} filters={{ ...defaultFilters, serviceCategories: ['A'] }} onChange={vi.fn()} onSubmit={onSubmit} />);
    
    const submitBtn = screen.getByRole('button', { name: 'Compare demand' });
    expect(submitBtn).not.toBeDisabled();
    fireEvent.click(submitBtn);
    expect(onSubmit).toHaveBeenCalled();
  });
});
"""

outcome_test = """\
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ComparisonOutcomeState } from '../components/ComparisonOutcomeState';
import type { DemandComparisonResponse } from '../../../types/demandComparisons';

describe('ComparisonOutcomeState', () => {
  it('renders loading state', () => {
    render(<ComparisonOutcomeState isLoading={true} error={null} response={null} onProceed={vi.fn()} onDecline={vi.fn()} />);
    expect(screen.getByText('Comparing historical and forecast demand...')).toBeInTheDocument();
  });

  it('renders error state', () => {
    render(<ComparisonOutcomeState isLoading={false} error="Test Error" response={null} onProceed={vi.fn()} onDecline={vi.fn()} />);
    expect(screen.getByText('Test Error')).toBeInTheDocument();
  });

  it('returns null if no response', () => {
    const { container } = render(<ComparisonOutcomeState isLoading={false} error={null} response={null} onProceed={vi.fn()} onDecline={vi.fn()} />);
    expect(container).toBeEmptyDOMElement();
  });

  it('renders warning_required state', () => {
    const onProceed = vi.fn();
    const onDecline = vi.fn();
    const response: DemandComparisonResponse = { outcomeStatus: 'warning_required', message: 'Proceed?', series: [] };
    render(<ComparisonOutcomeState isLoading={false} error={null} response={response} onProceed={onProceed} onDecline={onDecline} />);
    
    expect(screen.getByText('Large request warning')).toBeInTheDocument();
    expect(screen.getByText('Proceed?')).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: 'Proceed' }));
    expect(onProceed).toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
    expect(onDecline).toHaveBeenCalled();
  });

  it('renders failure states', () => {
    ['historical_retrieval_failed', 'forecast_retrieval_failed', 'alignment_failed'].forEach((status) => {
      const response = { outcomeStatus: status as any, message: `Failed: ${status}`, series: [] };
      const { unmount } = render(<ComparisonOutcomeState isLoading={false} error={null} response={response} onProceed={vi.fn()} onDecline={vi.fn()} />);
      expect(screen.getByText(`Failed: ${status}`)).toBeInTheDocument();
      unmount();
    });
  });

  it('renders standard response message for success', () => {
    const response: DemandComparisonResponse = { outcomeStatus: 'success', message: 'Success message', series: [] };
    render(<ComparisonOutcomeState isLoading={false} error={null} response={response} onProceed={vi.fn()} onDecline={vi.fn()} />);
    expect(screen.getByText('Success message')).toBeInTheDocument();
  });
});
"""

result_view_test = """\
import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ComparisonResultView } from '../components/ComparisonResultView';
import type { DemandComparisonResponse } from '../../../types/demandComparisons';

describe('ComparisonResultView', () => {
  it('renders basic summary and handles undefined optional fields', () => {
    const response: DemandComparisonResponse = {
      outcomeStatus: 'success',
      message: 'Done',
      series: []
    };
    render(<ComparisonResultView response={response} />);
    expect(screen.getByText('Comparison summary')).toBeInTheDocument();
    expect(screen.getByText('success')).toBeInTheDocument();
    expect(screen.getByText('daily')).toBeInTheDocument(); // fallback when missing
    expect(screen.getByText('0')).toBeInTheDocument(); // series length
    expect(screen.queryByText('Missing combinations')).not.toBeInTheDocument();
  });

  it('renders with full data', () => {
    const response: DemandComparisonResponse = {
      outcomeStatus: 'success',
      comparisonGranularity: 'weekly',
      message: 'Done',
      missingCombinations: [
        { serviceCategory: 'Miss1', geographyKey: 'geo1', message: 'Err1' },
      ],
      series: [
        {
          seriesType: 'historical',
          serviceCategory: 'Cat1',
          geographyKey: 'geo1',
          points: [{ bucketStart: '2023-01-01', bucketEnd: '2023-01-02', value: 10 }]
        },
        {
          seriesType: 'forecast',
          serviceCategory: 'Cat2',
          geographyKey: undefined,
          points: []
        }
      ]
    };
    render(<ComparisonResultView response={response} />);
    expect(screen.getByText('weekly')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // series length

    expect(screen.getByText('Missing combinations')).toBeInTheDocument();
    expect(screen.getByText('Err1')).toBeInTheDocument();

    expect(screen.getByText('Series table')).toBeInTheDocument();
    expect(screen.getByText('historical')).toBeInTheDocument();
    expect(screen.getByText('Cat1')).toBeInTheDocument();
    expect(screen.getByText('geo1')).toBeInTheDocument();
    expect(screen.getByText('2023-01-01 - 10')).toBeInTheDocument();

    expect(screen.getByText('forecast')).toBeInTheDocument();
    expect(screen.getByText('Cat2')).toBeInTheDocument();
    expect(screen.getAllByText('All selected')).toHaveLength(1); // fallback mapped
  });
});
"""

hooks_test = """\
import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useDemandComparisons } from '../hooks/useDemandComparisons';
import * as api from '../../../api/demandComparisons';

vi.mock('../../../api/demandComparisons');

describe('useDemandComparisons', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('initializes context and handles abort correctly', async () => {
    const mockContext = { serviceCategories: ['Cat A'], geographyLevels: ['Level 1'], geographyOptions: {} };
    let resolveContext: any;
    vi.mocked(api.fetchDemandComparisonContext).mockReturnValue(new Promise((resolve) => {
      resolveContext = resolve;
    }));

    const { result, unmount } = renderHook(() => useDemandComparisons());
    expect(result.current.isLoadingContext).toBe(true);

    act(() => {
      resolveContext(mockContext);
    });

    await act(async () => {
      await new Promise(r => setTimeout(r, 0));
    });

    expect(result.current.isLoadingContext).toBe(false);
    expect(result.current.context).toEqual(mockContext);
    expect(result.current.filters.serviceCategories).toEqual(['Cat A']);
    expect(result.current.filters.geographyLevel).toBe('Level 1');

    unmount(); // Test abort block execution
  });

  it('handles fetchDemandComparisonContext error gracefully unless aborted', async () => {
    vi.mocked(api.fetchDemandComparisonContext).mockRejectedValue(new Error('Fetch Error'));
    const { result } = renderHook(() => useDemandComparisons());

    await act(async () => {
      await new Promise(r => setTimeout(r, 0));
    });

    expect(result.current.isLoadingContext).toBe(false);
    expect(result.current.error).toBe('Fetch Error');
  });

  it('handles abort properly on unmount during fetch', async () => {
    vi.mocked(api.fetchDemandComparisonContext).mockImplementation((signal) => {
      return new Promise((_, reject) => {
         signal.addEventListener('abort', () => reject(new Error('AbortError')));
      });
    });
    const { result, unmount } = renderHook(() => useDemandComparisons());
    unmount(); // Aborts the signal immediately
    
    await act(async () => {
      await new Promise(r => setTimeout(r, 10));
    });

    // Error should not be set because signal was aborted
    expect(result.current.error).toBeNull();
  });

  it('submits query and updates states successfully', async () => {
    vi.mocked(api.fetchDemandComparisonContext).mockResolvedValue({ serviceCategories: [], geographyLevels: [], geographyOptions: {} });
    const mockResponse = { outcomeStatus: 'success', comparisonRequestId: 'req-1', message: 'Ok', series: [] };
    vi.mocked(api.submitDemandComparisonQuery).mockResolvedValue(mockResponse as any);

    const { result } = renderHook(() => useDemandComparisons());

    let promise: any;
    act(() => {
      promise = result.current.submit({ serviceCategories: ['New Cat'] }, true);
    });

    expect(result.current.isSubmitting).toBe(true);
    expect(result.current.filters.serviceCategories).toEqual(['New Cat']);

    const res = await act(async () => promise);
    expect(res).toEqual(mockResponse);
    expect(result.current.response).toEqual(mockResponse);
    expect(result.current.isSubmitting).toBe(false);
  });

  it('submits query and handles error', async () => {
    vi.mocked(api.fetchDemandComparisonContext).mockResolvedValue({ serviceCategories: [], geographyLevels: [], geographyOptions: {} });
    vi.mocked(api.submitDemandComparisonQuery).mockRejectedValue(new Error('Submit Error'));

    const { result } = renderHook(() => useDemandComparisons());

    const res = await act(async () => result.current.submit());

    expect(res).toBeNull();
    expect(result.current.error).toBe('Submit Error');
    expect(result.current.response).toBeNull();
    expect(result.current.isSubmitting).toBe(false);
  });

  it('submits query falling back to generic error', async () => {
    vi.mocked(api.fetchDemandComparisonContext).mockResolvedValue({ serviceCategories: [], geographyLevels: [], geographyOptions: {} });
    vi.mocked(api.submitDemandComparisonQuery).mockRejectedValue('String Error');

    const { result } = renderHook(() => useDemandComparisons());
    await act(async () => { await result.current.submit(); });
    expect(result.current.error).toBe('Unable to compare demand.');
  });

  it('handles race conditions via lastRequestToken', async () => {
    vi.mocked(api.fetchDemandComparisonContext).mockResolvedValue({ serviceCategories: [], geographyLevels: [], geographyOptions: {} });
    
    let resolveFirst: any;
    const promise1 = new Promise((r) => { resolveFirst = r; });
    const mockResponse2 = { outcomeStatus: 'success', message: 'Second', series: [] };

    vi.mocked(api.submitDemandComparisonQuery)
      .mockReturnValueOnce(promise1 as any)
      .mockResolvedValueOnce(mockResponse2 as any);

    const { result } = renderHook(() => useDemandComparisons());

    let submit1: any;
    let submit2: any;
    act(() => {
      submit1 = result.current.submit();
      submit2 = result.current.submit();
    });

    // submit2 resolves immediately
    await act(async () => { await submit2; });
    expect(result.current.response).toEqual(mockResponse2);
    expect(result.current.isSubmitting).toBe(false);

    // resolve submit1 now
    await act(async () => { resolveFirst({ outcomeStatus: 'success', message: 'First', series: [] }); await submit1; });
    // State should remain for submit2
    expect(result.current.response).toEqual(mockResponse2);
  });

  it('handles race condition for errors', async () => {
    vi.mocked(api.fetchDemandComparisonContext).mockResolvedValue({ serviceCategories: [], geographyLevels: [], geographyOptions: {} });
    
    let rejectFirst: any;
    const promise1 = new Promise((_, r) => { rejectFirst = r; });
    const mockResponse2 = { outcomeStatus: 'success', message: 'Second', series: [] };

    vi.mocked(api.submitDemandComparisonQuery)
      .mockReturnValueOnce(promise1 as any)
      .mockResolvedValueOnce(mockResponse2 as any);

    const { result } = renderHook(() => useDemandComparisons());

    let submit1: any;
    let submit2: any;
    act(() => {
      submit1 = result.current.submit();
      submit2 = result.current.submit();
    });

    await act(async () => { await submit2; });
    await act(async () => {
      rejectFirst(new Error('First Error'));
      try { await submit1; } catch (e) {}
    });
    
    // Should not inherit the error from the earlier stale request
    expect(result.current.error).toBeNull();
  });

  it('reports render event correctly and prevents duplicates', async () => {
    vi.mocked(api.fetchDemandComparisonContext).mockResolvedValue({ serviceCategories: [], geographyLevels: [], geographyOptions: {} });
    vi.mocked(api.submitDemandComparisonQuery).mockResolvedValue({ comparisonRequestId: 'test-req', outcomeStatus: 'success', message: 'Ok', series: [] } as any);

    const { result } = renderHook(() => useDemandComparisons());

    await act(async () => { await result.current.submit(); });

    await act(async () => {
      await result.current.reportRenderEvent({ renderStatus: 'rendered' } as any);
    });
    expect(api.submitDemandComparisonRenderEvent).toHaveBeenCalledWith('test-req', { renderStatus: 'rendered' });

    // Calling it again with same values shouldn't resubmit
    vi.mocked(api.submitDemandComparisonRenderEvent).mockClear();
    await act(async () => {
      await result.current.reportRenderEvent({ renderStatus: 'rendered' } as any);
    });
    expect(api.submitDemandComparisonRenderEvent).not.toHaveBeenCalled();
  });

  it('bails out of reportRenderEvent if no comparisonRequestId', async () => {
    vi.mocked(api.fetchDemandComparisonContext).mockResolvedValue({ serviceCategories: [], geographyLevels: [], geographyOptions: {} });
    vi.mocked(api.submitDemandComparisonQuery).mockResolvedValue({ outcomeStatus: 'success', message: 'Ok', series: [] } as any);

    const { result } = renderHook(() => useDemandComparisons());
    await act(async () => { await result.current.submit(); });

    await act(async () => {
      await result.current.reportRenderEvent({ renderStatus: 'rendered' } as any);
    });
    expect(api.submitDemandComparisonRenderEvent).not.toHaveBeenCalled();
  });

  it('handles reportRenderEvent error', async () => {
    vi.mocked(api.fetchDemandComparisonContext).mockResolvedValue({ serviceCategories: [], geographyLevels: [], geographyOptions: {} });
    vi.mocked(api.submitDemandComparisonQuery).mockResolvedValue({ comparisonRequestId: 'test-err', outcomeStatus: 'success', message: 'Ok', series: [] } as any);
    vi.mocked(api.submitDemandComparisonRenderEvent).mockRejectedValue(new Error('Render Event Error'));

    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    const { result } = renderHook(() => useDemandComparisons());
    await act(async () => { await result.current.submit(); });

    await act(async () => {
      await result.current.reportRenderEvent({ renderStatus: 'rendered' } as any);
    });

    expect(consoleSpy).toHaveBeenCalledWith('Failed to submit demand comparison render event', expect.any(Error));
    consoleSpy.mockRestore();
  });

  it('clears response and error', async () => {
    vi.mocked(api.fetchDemandComparisonContext).mockResolvedValue({ serviceCategories: [], geographyLevels: [], geographyOptions: {} });
    const { result } = renderHook(() => useDemandComparisons());

    act(() => { result.current.clearResponse(); });

    expect(result.current.response).toBeNull();
    expect(result.current.error).toBeNull();
  });
});
"""

files_to_write = {
    "ComparisonFilters.test.tsx": filters_test,
    "ComparisonOutcomeState.test.tsx": outcome_test,
    "ComparisonResultView.test.tsx": result_view_test,
    "useDemandComparisons.test.ts": hooks_test,
}

for filename, content in files_to_write.items():
    path = os.path.join(tests_dir, filename)
    with open(path, "w") as f:
        f.write(textwrap.dedent(content).strip() + "\\n")
    print(f"Wrote file {path}")

print("\\nSuccess! Tests injected.")