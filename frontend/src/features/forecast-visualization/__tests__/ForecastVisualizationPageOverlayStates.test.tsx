import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ForecastVisualizationPage } from '../../../pages/ForecastVisualizationPage';

const useForecastVisualizationMock = vi.fn();
const useWeatherOverlayMock = vi.fn();

vi.mock('../hooks/useForecastVisualization', () => ({
  useForecastVisualization: () => useForecastVisualizationMock(),
}));

vi.mock('../../weather-overlay/hooks/useWeatherOverlay', () => ({
  useWeatherOverlay: (input: unknown) => useWeatherOverlayMock(input),
}));

const baseVisualizationHookState = {
  forecastProduct: 'daily_1_day' as const,
  setForecastProduct: vi.fn(),
  serviceCategories: [],
  setServiceCategories: vi.fn(),
  serviceCategoryOptions: ['Roads', 'Waste'],
  visualization: null,
  isLoading: false,
  error: null,
  reportRenderEvent: vi.fn(),
  reportConfidenceRenderEvent: vi.fn(),
};

const baseOverlayHookState = {
  overlay: null,
  isLoading: false,
  error: null,
  reportRenderSuccess: vi.fn(),
  reportRenderFailure: vi.fn(),
  clearOverlay: vi.fn(),
};

describe('ForecastVisualizationPage – overlay fallback states', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date('2026-04-11T12:00:00Z'));
    useForecastVisualizationMock.mockReset();
    useWeatherOverlayMock.mockReset();
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it('uses the current timestamp for overlay windows when visualization data is not loaded and surfaces overlay alerts', () => {
    useForecastVisualizationMock.mockReturnValue({
      ...baseVisualizationHookState,
      visualization: null,
    });
    useWeatherOverlayMock.mockReturnValue({
      ...baseOverlayHookState,
      isLoading: true,
      error: 'Overlay retrieval failed.',
    });

    render(<ForecastVisualizationPage />);

    expect(screen.getByText(/loading weather overlay/i)).toBeInTheDocument();
    expect(screen.getByText(/overlay retrieval failed\./i)).toBeInTheDocument();
    expect(useWeatherOverlayMock).toHaveBeenCalledWith(
      expect.objectContaining({
        timeRangeStart: '2026-04-11T12:00:00.000Z',
        timeRangeEnd: '2026-04-11T12:00:00.000Z',
      }),
    );
  });

  it('falls back to forecast windows for overlay requests and lets users change the weather measure', async () => {
    const visualization = {
      visualizationLoadId: 'load-overlay-state',
      forecastProduct: 'daily_1_day',
      forecastGranularity: 'daily',
      categoryFilter: { selectedCategory: null, selectedCategories: [] },
      historyWindowStart: undefined,
      historyWindowEnd: '2026-03-21T00:00:00Z',
      forecastWindowStart: '2026-03-20T00:00:00Z',
      forecastWindowEnd: undefined,
      lastUpdatedAt: '2026-03-20T00:00:00Z',
      historicalSeries: [],
      forecastSeries: [],
      uncertaintyBands: undefined,
      alerts: [],
      pipelineStatus: [],
      viewStatus: 'success',
    };

    useForecastVisualizationMock.mockReturnValue({
      ...baseVisualizationHookState,
      visualization,
    });
    useWeatherOverlayMock.mockReturnValue({
      ...baseOverlayHookState,
    });

    render(<ForecastVisualizationPage />);

    expect(useWeatherOverlayMock).toHaveBeenCalledWith(
      expect.objectContaining({
        timeRangeStart: '2026-03-20T00:00:00Z',
        timeRangeEnd: '2026-03-21T00:00:00Z',
        overlayEnabled: false,
        weatherMeasure: 'temperature',
      }),
    );

    fireEvent.click(screen.getByLabelText(/enable weather overlay/i));
    fireEvent.click(screen.getByRole('button', { name: /temperature/i }));
    fireEvent.click(screen.getByRole('button', { name: /snowfall/i }));

    expect(useWeatherOverlayMock).toHaveBeenLastCalledWith(
      expect.objectContaining({
        overlayEnabled: true,
        weatherMeasure: 'snowfall',
      }),
    );
  });
});
