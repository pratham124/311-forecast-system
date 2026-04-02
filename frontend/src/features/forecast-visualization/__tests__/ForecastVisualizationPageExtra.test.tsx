/**
 * Extra coverage for ForecastVisualizationPage:
 * - Dropdown closes when clicking outside (handlePointerDown)
 */
import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ForecastVisualizationPage } from '../../../pages/ForecastVisualizationPage';

const categoriesPayload = { forecastProduct: 'daily_1_day', categories: ['Roads'] };
const successPayload = {
  visualizationLoadId: 'load-1',
  forecastProduct: 'daily_1_day',
  forecastGranularity: 'daily',
  categoryFilter: { selectedCategory: 'Roads', selectedCategories: ['Roads'] },
  historyWindowStart: '2026-03-13T00:00:00Z',
  historyWindowEnd: '2026-03-20T00:00:00Z',
  forecastWindowStart: '2026-03-20T00:00:00Z',
  forecastWindowEnd: '2026-03-21T00:00:00Z',
  lastUpdatedAt: '2026-03-20T00:00:00Z',
  historicalSeries: [{ timestamp: '2026-03-19T00:00:00Z', value: 8 }],
  forecastSeries: [{ timestamp: '2026-03-20T00:00:00Z', pointForecast: 10 }],
  uncertaintyBands: { labels: ['P10', 'P90'], points: [{ timestamp: '2026-03-20T00:00:00Z', p10: 8, p50: 10, p90: 12 }] },
  alerts: [],
  pipelineStatus: [],
  viewStatus: 'success',
};

describe('ForecastVisualizationPage – extra coverage', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
    vi.restoreAllMocks();
  });

  it('closes dropdown when clicking outside (handlePointerDown path)', async () => {
    const user = userEvent.setup();
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(categoriesPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(successPayload), { status: 200 }))
      .mockResolvedValue(new Response(null, { status: 202 }));

    render(<ForecastVisualizationPage />);
    await screen.findByRole('img', { name: /demand forecast chart/i });

    // Open a dropdown
    await user.click(screen.getByRole('button', { name: /service areas/i }));
    expect(screen.getByRole('listbox', { name: /service areas/i })).toBeInTheDocument();

    // Click outside to close
    fireEvent.mouseDown(document.body);
    await waitFor(() => {
      expect(screen.queryByRole('listbox', { name: /service areas/i })).not.toBeInTheDocument();
    });
  });

  it('toggles the time-range dropdown open and closed via onOpenChange', async () => {
    const user = userEvent.setup();
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(categoriesPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(successPayload), { status: 200 }))
      .mockResolvedValue(new Response(null, { status: 202 }));

    render(<ForecastVisualizationPage />);
    await screen.findByRole('img', { name: /demand forecast chart/i });

    const timeRangeButton = document.getElementById('forecast-product') as HTMLButtonElement;
    expect(timeRangeButton).toBeTruthy();
    await user.click(timeRangeButton);
    expect(screen.getByRole('listbox', { name: /time range/i })).toBeInTheDocument();

    await user.click(timeRangeButton);
    await waitFor(() => {
      expect(screen.queryByRole('listbox', { name: /time range/i })).not.toBeInTheDocument();
    });
  });

  it('keeps dropdown open for inside pointer targets and closes for outside targets', async () => {
    const user = userEvent.setup();
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(categoriesPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(successPayload), { status: 200 }))
      .mockResolvedValue(new Response(null, { status: 202 }));

    render(<ForecastVisualizationPage />);
    await screen.findByRole('img', { name: /demand forecast chart/i });

    const serviceAreaButton = screen.getByRole('button', { name: /service areas/i });
    await user.click(serviceAreaButton);
    expect(screen.getByRole('listbox', { name: /service areas/i })).toBeInTheDocument();

    await user.click(serviceAreaButton);
    await waitFor(() => {
      expect(screen.queryByRole('listbox', { name: /service areas/i })).not.toBeInTheDocument();
    });

    await user.click(serviceAreaButton);
    expect(screen.getByRole('listbox', { name: /service areas/i })).toBeInTheDocument();

    fireEvent.mouseDown(serviceAreaButton);
    expect(screen.getByRole('listbox', { name: /service areas/i })).toBeInTheDocument();

    fireEvent.mouseDown(document.body);
    await waitFor(() => {
      expect(screen.queryByRole('listbox', { name: /service areas/i })).not.toBeInTheDocument();
    });
  });

  it('ignores non-Node pointer targets when dropdown handler runs', async () => {
    const user = userEvent.setup();
    const addListenerSpy = vi.spyOn(document, 'addEventListener');

    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(categoriesPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(successPayload), { status: 200 }))
      .mockResolvedValue(new Response(null, { status: 202 }));

    render(<ForecastVisualizationPage />);
    await screen.findByRole('img', { name: /demand forecast chart/i });

    const serviceAreaButton = screen.getByRole('button', { name: /service areas/i });
    await user.click(serviceAreaButton);
    expect(screen.getByRole('listbox', { name: /service areas/i })).toBeInTheDocument();

    const pointerHandler = addListenerSpy.mock.calls.find(([name]) => name === 'mousedown')?.[1] as
      | ((event: MouseEvent) => void)
      | undefined;
    expect(pointerHandler).toBeDefined();

    act(() => {
      pointerHandler?.({ target: window } as unknown as MouseEvent);
    });

    expect(screen.getByRole('listbox', { name: /service areas/i })).toBeInTheDocument();
    addListenerSpy.mockRestore();
  });

  it('renders unavailable fallback copy when summary is missing and no updated timestamp exists', async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(categoriesPayload), { status: 200 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            ...successPayload,
            viewStatus: 'unavailable',
            summary: null,
            lastUpdatedAt: null,
            historicalSeries: [],
            forecastSeries: [],
            uncertaintyBands: undefined,
          }),
          { status: 200 },
        ),
      );

    render(<ForecastVisualizationPage />);

    expect(await screen.findByText(/forecast view unavailable/i)).toBeInTheDocument();
    expect(screen.getAllByText(/we can't show this forecast right now\./i).length).toBeGreaterThan(0);
    expect(screen.getByText(/^Not available$/i)).toBeInTheDocument();
  });

  it('shows an error alert when visualization request fails', async () => {
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(categoriesPayload), { status: 200 }))
      .mockResolvedValueOnce(new Response('{}', { status: 500 }));

    render(<ForecastVisualizationPage />);
    expect(await screen.findByText(/visualization request failed with status 500/i)).toBeInTheDocument();
  });
});
