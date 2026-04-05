import { cleanup, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PublicForecastPage } from '../src/pages/PublicForecastPage';

describe('PublicForecastPage sanitized states', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('shows incomplete coverage and sanitization notes', async () => {
    fetchMock
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            publicForecastRequestId: 'request-2',
            status: 'available',
            forecastWindowLabel: '2026-03-20 to 2026-03-21',
            publishedAt: '2026-03-20T00:00:00Z',
            coverageStatus: 'incomplete',
            coverageMessage: 'Some categories are not shown in this public forecast: Transit.',
            sanitizationStatus: 'sanitized',
            sanitizationSummary: 'Removed 1 restricted forecast detail records before publication.',
            categorySummaries: [{ serviceCategory: 'Roads', forecastDemandValue: 22, demandLevelSummary: 'Moderate demand expected' }],
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

    expect(await screen.findByText(/public forecast notes/i)).toBeInTheDocument();
    expect(screen.getByText(/Transit/)).toBeInTheDocument();
    expect(screen.getByText(/Removed 1 restricted forecast detail records/)).toBeInTheDocument();
  });
});
