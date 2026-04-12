import { expect, test } from '@playwright/test';

const STORAGE_KEY = 'forecast-system-auth-session';

const authenticatedUser = {
  userAccountId: 'user-1',
  email: 'manager@example.com',
  roles: ['OperationalManager'],
};

function buildVisualizationResponse({
  visualizationLoadId,
  forecastProduct,
  forecastGranularity,
  forecastConfidence,
}: {
  visualizationLoadId: string;
  forecastProduct: 'daily_1_day' | 'weekly_7_day';
  forecastGranularity: 'hourly' | 'daily';
  forecastConfidence: {
    assessmentStatus: 'degraded_confirmed' | 'dismissed' | 'signals_missing';
    indicatorState: 'display_required' | 'not_required';
    reasonCategories: string[];
    supportingSignals: string[];
    message: string;
  };
}) {
  return {
    visualizationLoadId,
    forecastProduct,
    forecastGranularity,
    categoryFilter: {
      selectedCategory: 'Roads',
      selectedCategories: ['Roads', 'Waste', 'Transit'],
    },
    historyWindowStart: '2026-04-01T00:00:00Z',
    historyWindowEnd: '2026-04-08T00:00:00Z',
    forecastWindowStart: '2026-04-08T00:00:00Z',
    forecastWindowEnd: '2026-04-09T00:00:00Z',
    forecastBoundary: '2026-04-08T00:00:00Z',
    lastUpdatedAt: '2026-04-08T00:00:00Z',
    historicalSeries: [
      { timestamp: '2026-04-07T00:00:00Z', value: 8 },
      { timestamp: '2026-04-07T01:00:00Z', value: 10 },
    ],
    forecastSeries: [
      { timestamp: '2026-04-08T00:00:00Z', pointForecast: 12 },
      { timestamp: '2026-04-08T01:00:00Z', pointForecast: 14 },
    ],
    uncertaintyBands: {
      labels: ['P10', 'P50', 'P90'],
      points: [
        { timestamp: '2026-04-08T00:00:00Z', p10: 10, p50: 12, p90: 14 },
        { timestamp: '2026-04-08T01:00:00Z', p10: 12, p50: 14, p90: 16 },
      ],
    },
    alerts: [],
    pipelineStatus: [{ code: 'forecast_loaded', level: 'info', message: 'Loaded daily forecast data.' }],
    forecastConfidence,
    viewStatus: 'success',
    summary: 'Visualization is available.',
  };
}

test.describe('UC-16 forecast confidence', () => {
  test('degraded, dismissed, and signals-missing flows behave correctly', async ({ page }) => {
    const chartRenderEvents: Array<{ loadId: string; renderStatus: string }> = [];
    const confidenceRenderEvents: Array<{ loadId: string; renderStatus: string }> = [];

    await page.addInitScript(
      ({ storageKey, session }) => {
        window.localStorage.setItem(storageKey, JSON.stringify(session));
      },
      {
        storageKey: STORAGE_KEY,
        session: {
          accessToken: 'playwright-access-token',
          user: authenticatedUser,
        },
      },
    );

    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({ json: authenticatedUser });
    });

    await page.route('**/api/v1/forecast-visualizations/service-categories?*', async (route) => {
      const forecastProduct = new URL(route.request().url()).searchParams.get('forecastProduct') ?? 'daily_1_day';
      await route.fulfill({
        json: {
          forecastProduct,
          categories: ['Roads', 'Waste', 'Transit'],
        },
      });
    });

    await page.route('**/api/v1/forecast-visualizations/current?*', async (route) => {
      const url = new URL(route.request().url());
      const forecastProduct = (url.searchParams.get('forecastProduct') ?? 'daily_1_day') as 'daily_1_day' | 'weekly_7_day';
      const selectedCategories = url.searchParams.getAll('serviceCategory');

      if (forecastProduct === 'weekly_7_day') {
        await route.fulfill({
          json: buildVisualizationResponse({
            visualizationLoadId: 'load-signals-missing',
            forecastProduct,
            forecastGranularity: 'daily',
            forecastConfidence: {
              assessmentStatus: 'signals_missing',
              indicatorState: 'not_required',
              reasonCategories: [],
              supportingSignals: ['confidence_signal_unavailable'],
              message: 'Forecast confidence could not be fully assessed with the currently available signals.',
            },
          }),
        });
        return;
      }

      if (selectedCategories.includes('Waste')) {
        await route.fulfill({
          json: buildVisualizationResponse({
            visualizationLoadId: 'load-dismissed',
            forecastProduct,
            forecastGranularity: 'hourly',
            forecastConfidence: {
              assessmentStatus: 'dismissed',
              indicatorState: 'not_required',
              reasonCategories: ['anomaly'],
              supportingSignals: ['filtered_surge_candidate'],
              message: 'Recent confidence warnings were reviewed and dismissed for the current selection.',
            },
          }),
        });
        return;
      }

      await route.fulfill({
        json: buildVisualizationResponse({
          visualizationLoadId: 'load-degraded',
          forecastProduct,
          forecastGranularity: 'hourly',
          forecastConfidence: {
            assessmentStatus: 'degraded_confirmed',
            indicatorState: 'display_required',
            reasonCategories: ['anomaly'],
            supportingSignals: ['recent_confirmed_surge'],
            message: 'Forecast confidence is reduced because recent surge conditions were confirmed for the selected service areas.',
          },
        }),
      });
    });

    await page.route('**/api/v1/forecast-visualizations/*/confidence-render-events', async (route) => {
      const pathParts = new URL(route.request().url()).pathname.split('/');
      const loadId = pathParts[pathParts.length - 2];
      const payload = route.request().postDataJSON() as { renderStatus: string };
      confidenceRenderEvents.push({ loadId, renderStatus: payload.renderStatus });
      await route.fulfill({ status: 202, body: '' });
    });

    await page.route('**/api/v1/forecast-visualizations/*/render-events', async (route) => {
      const pathParts = new URL(route.request().url()).pathname.split('/');
      const loadId = pathParts[pathParts.length - 2];
      const payload = route.request().postDataJSON() as { renderStatus: string };
      chartRenderEvents.push({ loadId, renderStatus: payload.renderStatus });
      await route.fulfill({ status: 202, body: '' });
    });

    await page.goto('/app/forecasts');

    await expect(page.getByText('311 Forecast Overview')).toBeVisible();
    await expect(page.getByLabel('forecast confidence banner')).toBeVisible();
    await expect(page.getByText(/recent surge conditions were confirmed/i)).toBeVisible();
    await expect(page.getByRole('img', { name: /demand forecast chart/i })).toBeVisible();
    await expect.poll(() => confidenceRenderEvents.length).toBe(1);
    expect(confidenceRenderEvents[0]).toEqual({ loadId: 'load-degraded', renderStatus: 'rendered' });

    await page.locator('#service-category').click();
    await page.getByRole('listbox', { name: 'Service areas' }).getByRole('button', { name: 'Waste' }).click();

    await expect(page.getByLabel('forecast confidence banner')).toHaveCount(0);
    await expect(page.getByText(/reviewed and dismissed/i)).toBeVisible();
    await expect(page.getByRole('img', { name: /demand forecast chart/i })).toBeVisible();
    await expect.poll(() => confidenceRenderEvents.length).toBe(1);

    await page.locator('#forecast-product').click();
    await page.getByRole('listbox', { name: 'Time range' }).getByRole('button', { name: 'Next 7 days' }).click();

    await expect(page.getByLabel('forecast confidence banner')).toHaveCount(0);
    await expect(page.getByText(/could not be fully assessed/i)).toBeVisible();
    await expect(page.getByRole('img', { name: /demand forecast chart/i })).toBeVisible();
    await expect.poll(() => chartRenderEvents.length).toBeGreaterThanOrEqual(3);
    await expect.poll(() => confidenceRenderEvents.length).toBe(1);
  });
});
