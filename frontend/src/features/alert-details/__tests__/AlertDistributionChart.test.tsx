import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { AlertDistributionChart } from '../AlertDistributionChart';

describe('AlertDistributionChart', () => {
  it('renders chart framing and legend content', () => {
    render(
      <AlertDistributionChart
        points={[
          {
            label: 'not-a-date',
            bucketStart: '2026-03-01T00:00:00Z',
            bucketEnd: '2026-03-01T01:00:00Z',
            p10: 8,
            p50: 10,
            p90: 14,
            isAlertedBucket: true,
          },
        ]}
      />,
    );

    expect(screen.getByRole('img', { name: /alert distribution chart/i })).toBeInTheDocument();
    expect(screen.getByText(/forecast distribution/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/distribution legend/i)).toHaveTextContent(/p50 forecast/i);
    expect(screen.getByLabelText(/distribution legend/i)).toHaveTextContent(/uncertainty band/i);
    expect(screen.getByLabelText(/distribution legend/i)).toHaveTextContent(/alerted bucket/i);
  });
});
