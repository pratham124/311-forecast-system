import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PublicForecastPage } from '../src/pages/PublicForecastPage';

/** Mirrors `formatPublishedAt` in PublicForecastView so assertions match any host timezone. */
function formatPublishedAtForTest(iso: string): string {
  return new Date(iso).toLocaleString([], {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
  });
}

const availablePayload = {
  publicForecastRequestId: 'request-1',
  status: 'available',
  forecastWindowLabel: '2026-03-20 to 2026-03-21',
  publishedAt: '2026-03-20T00:00:00Z',
  coverageStatus: 'complete',
  sanitizationStatus: 'passed_as_is',
  categorySummaries: [
    { serviceCategory: 'Roads', forecastDemandValue: 22, demandLevelSummary: 'Moderate demand expected' },
    { serviceCategory: 'Waste', forecastDemandValue: 42, demandLevelSummary: 'Moderate demand expected' },
  ],
};

describe('PublicForecastPage success', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('loads the public forecast and reports a rendered event', async () => {
    const user = userEvent.setup();
    fetchMock
      .mockResolvedValueOnce(new Response(JSON.stringify(availablePayload), { status: 200 }))
      .mockResolvedValueOnce(new Response(null, { status: 202 }))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            ...availablePayload,
            publicForecastRequestId: 'request-2',
            forecastWindowLabel: '2026-03-23 to 2026-03-30',
          }),
          { status: 200 },
        ),
      )
      .mockResolvedValueOnce(new Response(null, { status: 202 }));

    render(
      <MemoryRouter>
        <PublicForecastPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/expected 311 demand by service category/i)).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: /public navigation/i })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /back/i })).toHaveAttribute('href', '/');
    expect(screen.getByRole('button', { name: /daily/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /weekly/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /highest demand/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /lowest demand/i })).toBeInTheDocument();
    expect(await screen.findByText('Roads')).toBeInTheDocument();
    expect(screen.getByText('Waste')).toBeInTheDocument();
    expect(screen.getByText(formatPublishedAtForTest(availablePayload.publishedAt))).toBeInTheDocument();
    expect(screen.getAllByRole('heading', { level: 2 }).map((node) => node.textContent)).toEqual(['Waste', 'Roads']);

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(String(fetchMock.mock.calls[0][0])).toContain('forecastProduct=daily');
    expect(String(fetchMock.mock.calls[1][0])).toContain('/display-events');

    await user.click(screen.getByRole('button', { name: /lowest demand/i }));
    expect(screen.getAllByRole('heading', { level: 2 }).map((node) => node.textContent)).toEqual(['Roads', 'Waste']);

    await user.click(screen.getByRole('button', { name: /weekly/i }));

    await waitFor(() => expect(String(fetchMock.mock.calls[2][0])).toContain('forecastProduct=weekly'));
    expect(await screen.findByText(/2026-03-23 to 2026-03-30/i)).toBeInTheDocument();
  });
});
