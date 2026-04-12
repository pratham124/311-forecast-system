import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { ForecastAccuracyComparison } from '../components/ForecastAccuracyComparison';

describe('ForecastAccuracyComparison', () => {
  it('sorts rows by selected columns and toggles direction', async () => {
    const user = userEvent.setup();

    render(
      <ForecastAccuracyComparison
        alignedBuckets={[
          {
            bucketStart: '2026-03-02T00:00:00Z',
            bucketEnd: '2026-03-02T01:00:00Z',
            serviceCategory: 'Waste',
            forecastValue: 8,
            actualValue: 6,
            absoluteErrorValue: 2,
          },
          {
            bucketStart: '2026-03-01T00:00:00Z',
            bucketEnd: '2026-03-01T01:00:00Z',
            serviceCategory: 'Roads',
            forecastValue: 4,
            actualValue: 3,
            absoluteErrorValue: 1,
          },
          {
            bucketStart: '2026-03-03T00:00:00Z',
            bucketEnd: '2026-03-03T01:00:00Z',
            serviceCategory: 'Bees/Wasps',
            forecastValue: 2,
            actualValue: 5,
            absoluteErrorValue: 3,
          },
        ]}
      />,
    );

    expect(screen.getAllByText(/^(Waste|Roads|Bees\/Wasps)$/).map((node) => node.textContent)).toEqual([
      'Roads',
      'Waste',
      'Bees/Wasps',
    ]);

    await user.click(screen.getByRole('button', { name: /service category: unsorted/i }));
    expect(screen.getAllByText(/^(Waste|Roads|Bees\/Wasps)$/).map((node) => node.textContent)).toEqual([
      'All categories',
      'Bees/Wasps',
      'Roads',
      'Waste',
    ].filter((label) => label !== 'All categories'));

    await user.click(screen.getByRole('button', { name: /forecast: unsorted/i }));
    expect(screen.getAllByText(/^(Waste|Roads|Bees\/Wasps)$/).map((node) => node.textContent)).toEqual([
      'Bees/Wasps',
      'Roads',
      'Waste',
    ]);

    await user.click(screen.getByRole('button', { name: /forecast: sorted ascending/i }));
    expect(screen.getAllByText(/^(Waste|Roads|Bees\/Wasps)$/).map((node) => node.textContent)).toEqual([
      'Waste',
      'Roads',
      'Bees/Wasps',
    ]);
  });
});
