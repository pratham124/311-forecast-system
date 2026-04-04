import React from 'react';
import { render, screen, cleanup } from '@testing-library/react';
import { describe, it, expect, afterEach } from 'vitest';
import { ComparisonResultView } from '../components/ComparisonResultView';
import type { DemandComparisonResponse } from '../../../types/demandComparisons';

describe('ComparisonResultView', () => {
  afterEach(() => {
    cleanup();
  });

  it('renders basic summary and handles undefined optional fields', () => {
    const response = {
      outcomeStatus: 'success',
      message: 'Done'
    } as unknown as DemandComparisonResponse;
    render(<ComparisonResultView response={response as any} />);
    expect(screen.getByText('Comparison summary')).toBeInTheDocument();
    expect(screen.getAllByText('success').length).toBeGreaterThan(0);
    expect(screen.getByText('daily')).toBeInTheDocument(); // fallback when missing
    expect(screen.getByText('0')).toBeInTheDocument(); // series length
    expect(screen.queryByText('Missing combinations')).not.toBeInTheDocument();
  });

  it('renders with full data', () => {
    const response = {
      outcomeStatus: 'success',
      comparisonGranularity: 'weekly',
      message: 'Done',
      missingCombinations: [
        { serviceCategory: 'Miss1', geographyKey: 'geo1', message: 'Err1', missingSource: 'forecast' },
         { serviceCategory: 'Miss2', geographyKey: undefined, message: 'Err2', missingSource: 'forecast' }
      ],
      series: [
        {
          seriesType: 'historical',
          serviceCategory: 'Cat1',
          geographyKey: 'geo1',
          points: [{ bucketStart: '2023-01-01T00:00:00Z', bucketEnd: '2023-01-02T00:00:00Z', value: 10 }]
        },
        {
          seriesType: 'forecast',
          serviceCategory: 'Cat2',
          geographyKey: undefined,
          points: [{ bucketStart: '2023-01-01T00:00:00Z', bucketEnd: '2023-01-02T00:00:00Z', value: 12 }]
        }
      ]
    };
    render(<ComparisonResultView response={response as any} />);
    expect(screen.getByText('weekly')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // series length

    expect(screen.getByText('Missing combinations')).toBeInTheDocument();
    expect(screen.getByText('Err1')).toBeInTheDocument();
    expect(screen.getByText('Err2')).toBeInTheDocument();

    expect(screen.getByText('Series table')).toBeInTheDocument();
    expect(screen.getByText('historical')).toBeInTheDocument();
    expect(screen.getByText('Cat1')).toBeInTheDocument();
    expect(screen.getAllByText('2023-01-01').length).toBeGreaterThan(0);
    expect(screen.getByText('10')).toBeInTheDocument();

    expect(screen.getByText('forecast')).toBeInTheDocument();
    expect(screen.getByText('Cat2')).toBeInTheDocument();
    expect(screen.getByText('Comparison Chart')).toBeInTheDocument();
    expect(screen.queryByText('Geography')).not.toBeInTheDocument();
  });
});
