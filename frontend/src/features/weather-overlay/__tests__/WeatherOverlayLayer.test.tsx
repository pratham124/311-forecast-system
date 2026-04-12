import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { WeatherOverlayLayer } from '../components/WeatherOverlayLayer';

describe('WeatherOverlayLayer', () => {
  it('renders visible overlays with observation details', () => {
    render(
      <WeatherOverlayLayer
        overlay={{
          overlayRequestId: 'overlay-1',
          geographyId: 'citywide',
          timeRangeStart: '2026-03-01T00:00:00Z',
          timeRangeEnd: '2026-03-01T02:00:00Z',
          weatherMeasure: 'temperature',
          overlayStatus: 'visible',
          baseForecastPreserved: true,
          userVisible: true,
          measurementUnit: 'C',
          stateSource: 'overlay-assembly',
          observations: [
            { timestamp: '2026-03-01T00:00:00Z', value: 1.25 },
            { timestamp: '2026-03-01T01:00:00Z', value: 2.5 },
          ],
        }}
      />,
    );

    expect(screen.getByLabelText(/weather overlay layer/i)).toBeInTheDocument();
    expect(screen.getByText(/2 aligned points, latest 2.5 C/i)).toBeInTheDocument();
    expect(screen.getByText('1.3 C')).toBeInTheDocument();
    expect(screen.getByText('2.5 C')).toBeInTheDocument();
  });

  it('renders nothing when the overlay is not visible', () => {
    const view = render(
      <WeatherOverlayLayer
        overlay={{
          overlayRequestId: 'overlay-2',
          geographyId: 'citywide',
          timeRangeStart: '2026-03-01T00:00:00Z',
          timeRangeEnd: '2026-03-01T02:00:00Z',
          weatherMeasure: 'snowfall',
          overlayStatus: 'disabled',
          baseForecastPreserved: true,
          userVisible: true,
          stateSource: 'overlay-assembly',
          observations: [],
        }}
      />,
    );

    expect(view.container).toBeEmptyDOMElement();
  });

  it('renders visible overlays without a latest point suffix when there are no observations', () => {
    render(
      <WeatherOverlayLayer
        overlay={{
          overlayRequestId: 'overlay-3',
          geographyId: 'citywide',
          timeRangeStart: '2026-03-01T00:00:00Z',
          timeRangeEnd: '2026-03-01T02:00:00Z',
          weatherMeasure: 'precipitation',
          overlayStatus: 'visible',
          baseForecastPreserved: true,
          userVisible: true,
          stateSource: 'overlay-assembly',
          observations: [],
        }}
      />,
    );

    expect(screen.getByText(/^0 aligned points$/i)).toBeInTheDocument();
  });
});
