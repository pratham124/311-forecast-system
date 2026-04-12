import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { ForecastAccuracyComparison } from '../components/ForecastAccuracyComparison';

describe('ForecastAccuracyComparison extra coverage', () => {
  it('renders the empty state when there are no aligned buckets', () => {
    render(<ForecastAccuracyComparison alignedBuckets={[]} />);
    expect(screen.getByText(/no aligned buckets to display/i)).toBeInTheDocument();
  });

  it('sorts by actual value and absolute error and hides the diff arrow when there is no difference', async () => {
    const user = userEvent.setup();

    render(
      <ForecastAccuracyComparison
        alignedBuckets={[
          {
            bucketStart: '2026-03-01T00:00:00Z',
            bucketEnd: '2026-03-01T01:00:00Z',
            serviceCategory: 'Roads',
            forecastValue: 5,
            actualValue: 5,
            absoluteErrorValue: 0,
          },
          {
            bucketStart: '2026-03-01T01:00:00Z',
            bucketEnd: '2026-03-01T02:00:00Z',
            serviceCategory: 'Waste',
            forecastValue: 10,
            actualValue: 1,
            absoluteErrorValue: 9,
          },
          {
            bucketStart: '2026-03-01T02:00:00Z',
            bucketEnd: '2026-03-01T03:00:00Z',
            serviceCategory: 'Transit',
            forecastValue: 4,
            actualValue: 8,
            absoluteErrorValue: 4,
          },
        ]}
      />,
    );

    const roadsCell = screen.getByText('Roads').closest('div');
    expect(roadsCell).not.toBeNull();
    expect(within(roadsCell as HTMLElement).queryByText('▲')).not.toBeInTheDocument();
    expect(within(roadsCell as HTMLElement).queryByText('▼')).not.toBeInTheDocument();
    expect(screen.queryByText('▼')).toBeInTheDocument();

    await user.click(screen.getByRole('button', { name: /actual: unsorted/i }));
    expect(screen.getAllByText(/^(Roads|Waste|Transit)$/).map((node) => node.textContent)).toEqual([
      'Waste',
      'Roads',
      'Transit',
    ]);

    await user.click(screen.getByRole('button', { name: /abs error: unsorted/i }));
    expect(screen.getAllByText(/^(Roads|Waste|Transit)$/).map((node) => node.textContent)).toEqual([
      'Roads',
      'Transit',
      'Waste',
    ]);
  });
});
