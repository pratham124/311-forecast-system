import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { WeatherOverlayStatus } from '../components/WeatherOverlayStatus';

describe('WeatherOverlayStatus', () => {
  it('renders non-visible status message and hides visible state', () => {
    const { rerender } = render(
      <WeatherOverlayStatus
        overlay={{
          overlayRequestId: 'req-1',
          geographyId: 'citywide',
          timeRangeStart: '2026-03-20T00:00:00Z',
          timeRangeEnd: '2026-03-20T01:00:00Z',
          weatherMeasure: 'temperature',
          overlayStatus: 'misaligned',
          statusMessage: 'Unsupported geography',
          baseForecastPreserved: true,
          userVisible: true,
          observations: [],
          stateSource: 'overlay-assembly',
        }}
      />,
    );
    expect(screen.getByRole('status')).toHaveTextContent('Unsupported geography');

    rerender(
      <WeatherOverlayStatus
        overlay={{
          overlayRequestId: 'req-2',
          geographyId: 'citywide',
          timeRangeStart: '2026-03-20T00:00:00Z',
          timeRangeEnd: '2026-03-20T01:00:00Z',
          weatherMeasure: 'temperature',
          overlayStatus: 'visible',
          baseForecastPreserved: true,
          userVisible: true,
          observations: [{ timestamp: '2026-03-20T00:00:00Z', value: 3 }],
          stateSource: 'overlay-assembly',
        }}
      />,
    );
    expect(screen.queryByRole('status')).toBeNull();
  });
});
