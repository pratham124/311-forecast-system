import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ForecastAccuracyError } from '../components/ForecastAccuracyError';

describe('ForecastAccuracyError', () => {
  it('renders the provided message', () => {
    render(<ForecastAccuracyError message="comparison failed" />);
    expect(screen.getByText(/comparison failed/i)).toBeInTheDocument();
  });
});
