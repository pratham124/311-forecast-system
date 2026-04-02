import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ChartErrorBoundary } from '../components/ChartErrorBoundary';

function ThrowingChild({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error('Chart render error');
  }
  return <div>Chart rendered OK</div>;
}

// Suppress React error boundary console.error output in tests
const originalError = console.error;
beforeEach(() => {
  console.error = vi.fn();
});
afterEach(() => {
  console.error = originalError;
  cleanup();
});

describe('ChartErrorBoundary', () => {
  it('renders children when no error occurs', () => {
    const onError = vi.fn();
    render(
      <ChartErrorBoundary onError={onError} fallback={<div>Fallback</div>}>
        <ThrowingChild shouldThrow={false} />
      </ChartErrorBoundary>,
    );
    expect(screen.getByText('Chart rendered OK')).toBeInTheDocument();
    expect(screen.queryByText('Fallback')).not.toBeInTheDocument();
    expect(onError).not.toHaveBeenCalled();
  });

  it('renders fallback and calls onError when child throws', () => {
    const onError = vi.fn();
    render(
      <ChartErrorBoundary onError={onError} fallback={<div>Fallback</div>}>
        <ThrowingChild shouldThrow={true} />
      </ChartErrorBoundary>,
    );
    expect(screen.getByText('Fallback')).toBeInTheDocument();
    expect(screen.queryByText('Chart rendered OK')).not.toBeInTheDocument();
    expect(onError).toHaveBeenCalledWith(expect.any(Error));
    expect(onError.mock.calls[0][0].message).toBe('Chart render error');
  });
});
