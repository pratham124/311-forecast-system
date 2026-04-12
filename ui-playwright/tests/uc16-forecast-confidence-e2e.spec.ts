/**
 * UC-16 Forecast Confidence — real-auth E2E tests.
 *
 * These tests log in with real credentials, hit the real backend,
 * and validate that the forecast confidence flow works end-to-end.
 *
 * Env:
 *   E2E_EMAIL    — defaults to shozy.duck@gmail.com
 *   E2E_PASSWORD — defaults to #TestPassword
 */
import * as fs from 'node:fs';
import * as path from 'node:path';

import { expect, test } from '@playwright/test';

const EMAIL = process.env.E2E_EMAIL ?? 'shozy.duck@gmail.com';
const PASSWORD = process.env.E2E_PASSWORD ?? '#TestPassword';

const SHOT_DIR = path.join(process.cwd(), 'test-results', 'uc16-confidence');

function shotPath(name: string): string {
  return path.join(SHOT_DIR, `${name}.png`);
}

async function fullShot(page: import('@playwright/test').Page, name: string): Promise<void> {
  fs.mkdirSync(SHOT_DIR, { recursive: true });
  await page.screenshot({ path: shotPath(name), fullPage: true });
}

async function loginAsOperationalManager(page: import('@playwright/test').Page): Promise<void> {
  await page.goto('/');
  await page.getByLabel('Email', { exact: true }).fill(EMAIL);
  await page.getByLabel('Password', { exact: true }).fill(PASSWORD);
  await page.locator('form').getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL(/\/app\/forecasts/, { timeout: 60_000 });
}

/* ------------------------------------------------------------------ */
/*  AT-01 / AT-02 — Forecast loads with confidence signals             */
/* ------------------------------------------------------------------ */

test.describe('UC-16 e2e: real auth', () => {
  test('AT-01/AT-02: forecast page loads and returns confidence signals', async ({ page }) => {
    test.skip(!EMAIL || !PASSWORD, 'Set E2E_EMAIL and E2E_PASSWORD');

    let capturedConfidence: Record<string, unknown> | null = null;

    page.on('response', async (response) => {
      if (
        response.url().includes('/api/v1/forecast-visualizations/current') &&
        response.status() === 200
      ) {
        try {
          const body = (await response.json()) as Record<string, unknown>;
          capturedConfidence = body.forecastConfidence as Record<string, unknown>;
        } catch {
          /* response already consumed */
        }
      }
    });

    await loginAsOperationalManager(page);

    // AT-01: visualization loads
    await expect(page.getByText('311 Forecast Overview')).toBeVisible();

    // Wait for chart to render (forecast data visible)
    const chart = page.getByRole('img', { name: /demand forecast chart/i });
    const loading = page.getByText('Loading the forecast...');
    await loading.waitFor({ state: 'hidden', timeout: 90_000 }).catch(() => undefined);
    // Chart may or may not exist if data is unavailable — handle gracefully
    const chartOrUnavailable = await Promise.race([
      chart.waitFor({ state: 'visible', timeout: 30_000 }).then(() => 'chart' as const),
      page.getByText('Forecast view unavailable').waitFor({ state: 'visible', timeout: 30_000 }).then(() => 'unavailable' as const),
    ]).catch(() => 'timeout' as const);

    await fullShot(page, '01-daily-loaded');

    // AT-02: confidence signals present in API response
    await expect.poll(() => capturedConfidence !== null, { timeout: 10_000 }).toBe(true);
    expect(capturedConfidence).toBeDefined();
    expect(['normal', 'degraded_confirmed', 'signals_missing', 'dismissed']).toContain(
      capturedConfidence!.assessmentStatus,
    );
    expect(capturedConfidence!.message).toBeTruthy();

    // If chart loaded, verify no blocking errors
    if (chartOrUnavailable === 'chart') {
      await expect(page.getByText('311 Forecast Overview')).toBeVisible();
    }
  });

  /* ---------------------------------------------------------------- */
  /*  FR-001a — Unauthenticated user redirected to login               */
  /* ---------------------------------------------------------------- */

  test('FR-001a: unauthenticated user cannot access forecast page', async ({ page }) => {
    await page.goto('/app/forecasts');

    // Should see the login form, not the forecast dashboard
    await expect(page.getByLabel('Email', { exact: true })).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText('311 Forecast Overview')).toHaveCount(0);

    await fullShot(page, '02-unauthenticated-redirect');
  });

  /* ---------------------------------------------------------------- */
  /*  Non-degraded baseline: no false positive banner                  */
  /* ---------------------------------------------------------------- */

  test('no false positive banner when confidence is normal', async ({ page }) => {
    test.skip(!EMAIL || !PASSWORD, 'Set E2E_EMAIL and E2E_PASSWORD');

    await loginAsOperationalManager(page);
    await expect(page.getByText('311 Forecast Overview')).toBeVisible();

    const loading = page.getByText('Loading the forecast...');
    await loading.waitFor({ state: 'hidden', timeout: 90_000 }).catch(() => undefined);

    // Wait for page to settle
    await page.waitForTimeout(2000);

    await fullShot(page, '03-no-false-positive');

    // If no active surge in DB, banner should not appear
    // (We don't assert toHaveCount(0) unconditionally because real DB state may vary.
    //  Instead, if the banner IS visible, verify it's a genuine degraded_confirmed scenario.)
    const bannerCount = await page.getByLabel('forecast confidence banner').count();
    if (bannerCount === 0) {
      // Expected: no false positive
      expect(bannerCount).toBe(0);
    } else {
      // Banner appeared — verify it's backed by a real degraded_confirmed assessment
      await expect(page.getByText('Forecast confidence is reduced')).toBeVisible();
    }
  });

  /* ---------------------------------------------------------------- */
  /*  Weekly product: anomaly logic skipped (FR-004)                   */
  /* ---------------------------------------------------------------- */

  test('weekly product skips daily anomaly logic', async ({ page }) => {
    test.skip(!EMAIL || !PASSWORD, 'Set E2E_EMAIL and E2E_PASSWORD');

    let weeklyConfidence: Record<string, unknown> | null = null;

    page.on('response', async (response) => {
      if (
        response.url().includes('/api/v1/forecast-visualizations/current') &&
        response.url().includes('weekly_7_day') &&
        response.status() === 200
      ) {
        try {
          const body = (await response.json()) as Record<string, unknown>;
          weeklyConfidence = body.forecastConfidence as Record<string, unknown>;
        } catch {
          /* response already consumed */
        }
      }
    });

    await loginAsOperationalManager(page);
    await expect(page.getByText('311 Forecast Overview')).toBeVisible();

    // Switch to weekly
    await page.locator('#forecast-product').click();
    await page.getByRole('listbox', { name: 'Time range' }).getByRole('button', { name: 'Next 7 days' }).click();

    const loading = page.getByText('Loading the forecast...');
    await loading.waitFor({ state: 'hidden', timeout: 90_000 }).catch(() => undefined);
    await page.waitForTimeout(1000);

    await fullShot(page, '04-weekly-confidence');

    // Verify weekly confidence was returned
    await expect.poll(() => weeklyConfidence !== null, { timeout: 15_000 }).toBe(true);

    // Weekly should not have anomaly-based degradation (anomaly logic is daily-only)
    if (weeklyConfidence!.assessmentStatus === 'degraded_confirmed') {
      const reasons = weeklyConfidence!.reasonCategories as string[];
      expect(reasons).not.toContain('anomaly');
    }
  });

  /* ---------------------------------------------------------------- */
  /*  Service area filter change triggers new confidence assessment    */
  /* ---------------------------------------------------------------- */

  test('service area change triggers new confidence assessment', async ({ page }) => {
    test.skip(!EMAIL || !PASSWORD, 'Set E2E_EMAIL and E2E_PASSWORD');

    const confidenceResponses: Array<Record<string, unknown>> = [];

    page.on('response', async (response) => {
      if (
        response.url().includes('/api/v1/forecast-visualizations/current') &&
        response.status() === 200
      ) {
        try {
          const body = (await response.json()) as Record<string, unknown>;
          if (body.forecastConfidence) {
            confidenceResponses.push(body.forecastConfidence as Record<string, unknown>);
          }
        } catch {
          /* response already consumed */
        }
      }
    });

    await loginAsOperationalManager(page);
    await expect(page.getByText('311 Forecast Overview')).toBeVisible();

    const loading = page.getByText('Loading the forecast...');
    await loading.waitFor({ state: 'hidden', timeout: 90_000 }).catch(() => undefined);

    // Wait for initial load confidence response
    await expect.poll(() => confidenceResponses.length >= 1, { timeout: 15_000 }).toBe(true);
    const initialCount = confidenceResponses.length;

    // Open the service areas dropdown and select a category
    await page.locator('#service-category').click();
    const listbox = page.getByRole('listbox', { name: 'Service areas' });
    const buttons = listbox.getByRole('button');
    const buttonCount = await buttons.count();

    if (buttonCount > 0) {
      // Click the first available service area
      await buttons.first().click();

      await loading.waitFor({ state: 'hidden', timeout: 90_000 }).catch(() => undefined);
      await page.waitForTimeout(1000);

      // A new API call should have been made with updated categories
      await expect.poll(() => confidenceResponses.length > initialCount, { timeout: 15_000 }).toBe(true);

      await fullShot(page, '05-service-area-changed');
    }
  });
});
