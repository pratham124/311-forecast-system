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