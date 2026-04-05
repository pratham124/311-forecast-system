import { cleanup, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { PublicForecastPage } from '../src/pages/PublicForecastPage';

describe('PublicForecastPage error states', () => {
  const fetchMock = vi.fn();

  beforeEach(() => {
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
    fetchMock.mockReset();
  });

  it('shows unavailable messaging from the API without posting a display event', async () => {
    fetchMock.mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          publicForecastRequestId: 'request-3',
          status: 'unavailable',
          statusMessage: 'No approved public forecast is currently available.',
        }),
        { status: 200 },
      ),
    );

    render(
      <MemoryRouter>
        <PublicForecastPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/public forecast unavailable/i)).toBeInTheDocument();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1));
  });

  it('shows request failures when the page load itself fails', async () => {
    fetchMock.mockResolvedValueOnce(new Response(null, { status: 500 }));

    render(
      <MemoryRouter>
        <PublicForecastPage />
      </MemoryRouter>,
    );

    expect(await screen.findByText(/public forecast request failed with status 500/i)).toBeInTheDocument();
  });
});
