/**
 * UC-16 Forecast Confidence — per-AT scenario tests (mocked APIs).
 *
 * Each test maps to one or more acceptance tests from docs/UC-16-AT.md.
 * APIs are mocked via page.route() so every confidence state is deterministic.
 */
import { expect, test } from '@playwright/test';

/* ------------------------------------------------------------------ */
/*  Shared constants & helpers                                        */
/* ------------------------------------------------------------------ */

const STORAGE_KEY = 'forecast-system-auth-session';

const authenticatedUser = {
  userAccountId: 'user-scenario',
  email: 'manager@example.com',
  roles: ['OperationalManager'],
};

function injectAuth(page: import('@playwright/test').Page) {
  return page.addInitScript(
    ({ storageKey, session }) => {
      window.localStorage.setItem(storageKey, JSON.stringify(session));
    },
    {
      storageKey: STORAGE_KEY,
      session: { accessToken: 'playwright-scenario-token', user: authenticatedUser },
    },
  );
}

function mockAuthMe(page: import('@playwright/test').Page) {
  return page.route('**/api/v1/auth/me', (route) =>
    route.fulfill({ json: authenticatedUser }),
  );
}

function mockServiceCategories(page: import('@playwright/test').Page) {
  return page.route('**/api/v1/forecast-visualizations/service-categories?*', (route) =>
    route.fulfill({
      json: { forecastProduct: 'daily_1_day', categories: ['Roads', 'Waste', 'Transit'] },
    }),
  );
}

function mockRenderEvents(page: import('@playwright/test').Page) {
  return page.route('**/api/v1/forecast-visualizations/*/render-events', (route) =>
    route.fulfill({ status: 202, body: '' }),
  );
}

interface ConfidenceOverride {
  assessmentStatus: 'degraded_confirmed' | 'normal' | 'dismissed' | 'signals_missing';
  indicatorState: 'display_required' | 'not_required';
  reasonCategories: string[];
  supportingSignals: string[];
  message: string;
}

function buildVisualizationResponse(confidence: ConfidenceOverride, loadId = 'load-scenario') {
  return {
    visualizationLoadId: loadId,
    forecastProduct: 'daily_1_day',
    forecastGranularity: 'hourly',
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
    forecastConfidence: confidence,
    viewStatus: 'success',
    summary: 'Visualization is available.',
  };
}

/* ------------------------------------------------------------------ */
/*  AT-03 / AT-04 / AT-05 — Degraded confidence banner displayed      */
/* ------------------------------------------------------------------ */

test.describe('UC-16 scenario: degraded confidence (AT-03/04/05)', () => {
  test('shows amber banner alongside the forecast chart', async ({ page }) => {
    await injectAuth(page);
    await mockAuthMe(page);
    await mockServiceCategories(page);
    await mockRenderEvents(page);
    await page.route('**/api/v1/forecast-visualizations/*/confidence-render-events', (route) =>
      route.fulfill({ status: 202, body: '' }),
    );
    await page.route('**/api/v1/forecast-visualizations/current?*', (route) =>
      route.fulfill({
        json: buildVisualizationResponse({
          assessmentStatus: 'degraded_confirmed',
          indicatorState: 'display_required',
          reasonCategories: ['anomaly'],
          supportingSignals: ['recent_confirmed_surge'],
          message: 'Forecast confidence is reduced because recent surge conditions were confirmed for the selected service areas.',
        }),
      }),
    );

    await page.goto('/app/forecasts');

    // AT-03: degraded confidence detected — banner visible
    const banner = page.getByLabel('forecast confidence banner');
    await expect(banner).toBeVisible();

    // AT-04: indicator prepared with correct content (FR-008 + FR-008a)
    await expect(page.getByRole('heading', { name: 'Forecast confidence is reduced' })).toBeVisible();
    await expect(page.getByText(/recent surge conditions were confirmed/i)).toBeVisible();

    // AT-05: forecast chart visible alongside banner (FR-007, FR-008)
    await expect(page.getByRole('img', { name: /demand forecast chart/i })).toBeVisible();
  });
});

/* ------------------------------------------------------------------ */
/*  AT-06 — Confidence render event sent after display (FR-009/015)    */
/* ------------------------------------------------------------------ */

test.describe('UC-16 scenario: render event logging (AT-06)', () => {
  test('sends exactly one confidence render event with correct payload', async ({ page }) => {
    const confidenceRenderEvents: Array<{ url: string; body: { renderStatus: string } }> = [];

    await injectAuth(page);
    await mockAuthMe(page);
    await mockServiceCategories(page);
    await mockRenderEvents(page);

    await page.route('**/api/v1/forecast-visualizations/*/confidence-render-events', async (route) => {
      const body = route.request().postDataJSON() as { renderStatus: string };
      confidenceRenderEvents.push({ url: route.request().url(), body });
      await route.fulfill({ status: 202, body: '' });
    });

    await page.route('**/api/v1/forecast-visualizations/current?*', (route) =>
      route.fulfill({
        json: buildVisualizationResponse(
          {
            assessmentStatus: 'degraded_confirmed',
            indicatorState: 'display_required',
            reasonCategories: ['anomaly'],
            supportingSignals: ['recent_confirmed_surge'],
            message: 'Forecast confidence is reduced because recent surge conditions were confirmed for the selected service areas.',
          },
          'load-render-event',
        ),
      }),
    );

    await page.goto('/app/forecasts');
    await expect(page.getByLabel('forecast confidence banner')).toBeVisible();

    // AT-06: render event sent
    await expect.poll(() => confidenceRenderEvents.length).toBe(1);
    expect(confidenceRenderEvents[0].body.renderStatus).toBe('rendered');

    // FR-015: URL contains the visualization load id for correlation
    expect(confidenceRenderEvents[0].url).toContain('load-render-event');

    // Verify deduplication — wait briefly and confirm no duplicate
    await page.waitForTimeout(500);
    expect(confidenceRenderEvents.length).toBe(1);
  });
});

/* ------------------------------------------------------------------ */
/*  AT-07 — Signals missing: no banner, neutral copy (FR-010/012)      */
/* ------------------------------------------------------------------ */

test.describe('UC-16 scenario: signals missing (AT-07)', () => {
  test('hides banner and shows neutral messaging', async ({ page }) => {
    const confidenceRenderEvents: Array<{ renderStatus: string }> = [];

    await injectAuth(page);
    await mockAuthMe(page);
    await mockServiceCategories(page);
    await mockRenderEvents(page);

    await page.route('**/api/v1/forecast-visualizations/*/confidence-render-events', async (route) => {
      confidenceRenderEvents.push(route.request().postDataJSON() as { renderStatus: string });
      await route.fulfill({ status: 202, body: '' });
    });

    await page.route('**/api/v1/forecast-visualizations/current?*', (route) =>
      route.fulfill({
        json: buildVisualizationResponse({
          assessmentStatus: 'signals_missing',
          indicatorState: 'not_required',
          reasonCategories: [],
          supportingSignals: ['confidence_signal_unavailable'],
          message: 'Forecast confidence could not be fully assessed with the currently available signals.',
        }),
      }),
    );

    await page.goto('/app/forecasts');

    // AT-07: no degradation banner
    await expect(page.getByLabel('forecast confidence banner')).toHaveCount(0);

    // FR-010: neutral messaging shown (not a warning)
    await expect(page.getByText(/could not be fully assessed/i)).toBeVisible();

    // Forecast chart is displayed
    await expect(page.getByRole('img', { name: /demand forecast chart/i })).toBeVisible();

    // No confidence render event sent (banner was not rendered)
    await page.waitForTimeout(500);
    expect(confidenceRenderEvents.length).toBe(0);
  });
});

/* ------------------------------------------------------------------ */
/*  AT-08 — Dismissed signal: no banner, dismissed copy (FR-011/012)    */
/* ------------------------------------------------------------------ */

test.describe('UC-16 scenario: dismissed signal (AT-08)', () => {
  test('hides banner and shows dismissed messaging', async ({ page }) => {
    const confidenceRenderEvents: Array<{ renderStatus: string }> = [];

    await injectAuth(page);
    await mockAuthMe(page);
    await mockServiceCategories(page);
    await mockRenderEvents(page);

    await page.route('**/api/v1/forecast-visualizations/*/confidence-render-events', async (route) => {
      confidenceRenderEvents.push(route.request().postDataJSON() as { renderStatus: string });
      await route.fulfill({ status: 202, body: '' });
    });

    await page.route('**/api/v1/forecast-visualizations/current?*', (route) =>
      route.fulfill({
        json: buildVisualizationResponse({
          assessmentStatus: 'dismissed',
          indicatorState: 'not_required',
          reasonCategories: ['anomaly'],
          supportingSignals: ['filtered_surge_candidate'],
          message: 'Recent confidence warnings were reviewed and dismissed for the current selection.',
        }),
      }),
    );

    await page.goto('/app/forecasts');

    // AT-08: no degradation banner
    await expect(page.getByLabel('forecast confidence banner')).toHaveCount(0);

    // FR-011: dismissed copy shown
    await expect(page.getByText(/reviewed and dismissed/i)).toBeVisible();

    // Forecast chart is displayed normally
    await expect(page.getByRole('img', { name: /demand forecast chart/i })).toBeVisible();

    // No confidence render event sent
    await page.waitForTimeout(500);
    expect(confidenceRenderEvents.length).toBe(0);
  });
});

/* ------------------------------------------------------------------ */
/*  AT-09 — Render failure baseline (FR-013/014)                       */
/*  Note: React error boundary crashes cannot be reliably triggered    */
/*  from Playwright. Full AT-09 coverage comes from:                  */
/*    - ForecastVisualizationPageConfidenceCrash.test.tsx (frontend)   */
/*    - test_confidence_render_events_persist_without_changing_chart_  */
/*      status (integration)                                           */
/*  This test validates the success-path render event as a baseline.  */
/* ------------------------------------------------------------------ */

test.describe('UC-16 scenario: render failure baseline (AT-09)', () => {
  test('rendered event is sent on success — failure path covered by unit/integration tests', async ({ page }) => {
    const renderEvents: Array<{ renderStatus: string; failureReason?: string }> = [];

    await injectAuth(page);
    await mockAuthMe(page);
    await mockServiceCategories(page);
    await mockRenderEvents(page);

    await page.route('**/api/v1/forecast-visualizations/*/confidence-render-events', async (route) => {
      renderEvents.push(route.request().postDataJSON() as { renderStatus: string; failureReason?: string });
      await route.fulfill({ status: 202, body: '' });
    });

    await page.route('**/api/v1/forecast-visualizations/current?*', (route) =>
      route.fulfill({
        json: buildVisualizationResponse({
          assessmentStatus: 'degraded_confirmed',
          indicatorState: 'display_required',
          reasonCategories: ['anomaly'],
          supportingSignals: ['recent_confirmed_surge'],
          message: 'Forecast confidence is reduced because recent surge conditions were confirmed for the selected service areas.',
        }),
      }),
    );

    await page.goto('/app/forecasts');
    await expect(page.getByLabel('forecast confidence banner')).toBeVisible();

    // Success path: rendered event sent
    await expect.poll(() => renderEvents.length).toBe(1);
    expect(renderEvents[0].renderStatus).toBe('rendered');
    expect(renderEvents[0].failureReason).toBeUndefined();
  });
});

/* ------------------------------------------------------------------ */
/*  Combined degradation: missing_inputs + anomaly                     */
/* ------------------------------------------------------------------ */

test.describe('UC-16 scenario: combined degradation', () => {
  test('shows banner with combined message for missing inputs and anomaly', async ({ page }) => {
    await injectAuth(page);
    await mockAuthMe(page);
    await mockServiceCategories(page);
    await mockRenderEvents(page);
    await page.route('**/api/v1/forecast-visualizations/*/confidence-render-events', (route) =>
      route.fulfill({ status: 202, body: '' }),
    );

    await page.route('**/api/v1/forecast-visualizations/current?*', (route) =>
      route.fulfill({
        json: buildVisualizationResponse({
          assessmentStatus: 'degraded_confirmed',
          indicatorState: 'display_required',
          reasonCategories: ['missing_inputs', 'anomaly'],
          supportingSignals: ['history_missing', 'recent_confirmed_surge'],
          message: 'Forecast confidence is reduced because some visualization inputs are missing and recent surge conditions were confirmed for the selected service areas.',
        }),
      }),
    );

    await page.goto('/app/forecasts');

    await expect(page.getByLabel('forecast confidence banner')).toBeVisible();
    await expect(page.getByText(/some visualization inputs are missing/i)).toBeVisible();
    await expect(page.getByText(/surge conditions were confirmed/i)).toBeVisible();
    await expect(page.getByRole('img', { name: /demand forecast chart/i })).toBeVisible();
  });
});

/* ------------------------------------------------------------------ */
/*  Normal confidence: no banner or special messaging                  */
/* ------------------------------------------------------------------ */

test.describe('UC-16 scenario: normal confidence', () => {
  test('shows no banner or warning text when confidence is normal', async ({ page }) => {
    await injectAuth(page);
    await mockAuthMe(page);
    await mockServiceCategories(page);
    await mockRenderEvents(page);

    await page.route('**/api/v1/forecast-visualizations/current?*', (route) =>
      route.fulfill({
        json: buildVisualizationResponse({
          assessmentStatus: 'normal',
          indicatorState: 'not_required',
          reasonCategories: [],
          supportingSignals: [],
          message: 'Forecast confidence is normal for the current selection.',
        }),
      }),
    );

    await page.goto('/app/forecasts');

    // No banner
    await expect(page.getByLabel('forecast confidence banner')).toHaveCount(0);

    // No warning/dismissed/missing text
    await expect(page.getByText(/could not be fully assessed/i)).toHaveCount(0);
    await expect(page.getByText(/reviewed and dismissed/i)).toHaveCount(0);

    // Chart renders normally
    await expect(page.getByRole('img', { name: /demand forecast chart/i })).toBeVisible();
  });
});
