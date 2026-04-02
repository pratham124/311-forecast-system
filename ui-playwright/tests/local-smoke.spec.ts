/**
 * Local UI smoke: login → forecasts (time range) → comparisons → historical (dates + submit)
 * → evaluations → ingestion → forecasts. Screenshots: test-results/ui-smoke/*.png
 *
 * Env:
 *   E2E_EMAIL, E2E_PASSWORD — planner/manager account (allowlist + registered)
 *   E2E_BASE_URL — default http://127.0.0.1:5173
 *   E2E_TRIGGER_INGESTION=1 — click "Trigger 311 ingestion" (long-running; optional)
 */
import * as fs from 'node:fs';
import * as path from 'node:path';

import { expect, test } from '@playwright/test';

const SHOT_DIR = path.join(process.cwd(), 'test-results', 'ui-smoke');

function shotPath(name: string): string {
  return path.join(SHOT_DIR, `${name}.png`);
}

async function fullShot(page: import('@playwright/test').Page, name: string): Promise<void> {
  fs.mkdirSync(SHOT_DIR, { recursive: true });
  await page.screenshot({ path: shotPath(name), fullPage: true });
}

test.describe('local smoke (screenshots + checks)', () => {
  test('forecasts, historical dates, ingestion UI', async ({ page }) => {
    const email = process.env.E2E_EMAIL;
    const password = process.env.E2E_PASSWORD;
    test.skip(!email || !password, 'Set E2E_EMAIL and E2E_PASSWORD for local UI smoke');

    await page.goto('/');
    await fullShot(page, '01-entry');

    await page.getByLabel('Email', { exact: true }).fill(email!);
    await page.getByLabel('Password', { exact: true }).fill(password!);
    await page.locator('form').getByRole('button', { name: 'Sign in' }).click();

    await page.waitForURL(/\/app\/forecasts/, { timeout: 60_000 });
    await expect(page.getByText('311 Forecast Overview')).toBeVisible();
    await fullShot(page, '02-forecasts-initial');

    await page.locator('#forecast-product').click();
    await page.getByRole('listbox', { name: 'Time range' }).getByRole('button', { name: 'Next 7 days' }).click();
    const loading = page.getByText('Loading the forecast...');
    await loading.waitFor({ state: 'hidden', timeout: 90_000 }).catch(() => undefined);
    await page.waitForTimeout(400);
    await fullShot(page, '03-forecasts-weekly-window');

    await page.getByRole('navigation', { name: 'internal navigation' }).getByRole('link', { name: 'Comparisons' }).click();
    await page.waitForURL(/\/app\/demand-comparisons/);
    await expect(page.getByRole('main', { name: 'demand comparison page' })).toBeVisible();
    await page.getByText('Loading available comparison filters').waitFor({ state: 'hidden', timeout: 90_000 }).catch(() => undefined);
    await page.waitForTimeout(400);
    await fullShot(page, '10-demand-comparisons');

    await page.getByRole('navigation', { name: 'internal navigation' }).getByRole('link', { name: 'Historical' }).click();
    await page.waitForURL(/\/app\/historical-demand/);
    await expect(page.getByRole('main', { name: 'historical demand page' })).toBeVisible();
    await fullShot(page, '04-historical-initial');

    const startInput = page.locator('#time-range-start');
    const endInput = page.locator('#time-range-end');
    await startInput.fill('2026-01-01T00:00');
    await endInput.fill('2026-01-31T23:59');
    await fullShot(page, '05-historical-dates-changed');

    await page.getByRole('button', { name: 'Explore historical demand' }).click();
    await page.waitForTimeout(2000);
    await fullShot(page, '06-historical-after-submit');

    const evalLink = page.getByRole('navigation', { name: 'internal navigation' }).getByRole('link', { name: 'Evaluations' });
    await expect(evalLink).toBeVisible();
    await evalLink.click();
    await page.waitForURL(/\/app\/evaluations/);
    await expect(page.getByRole('main', { name: 'evaluation page' })).toBeVisible();
    await page.getByText('Loading the current evaluation').waitFor({ state: 'hidden', timeout: 90_000 }).catch(() => undefined);
    await page.waitForTimeout(400);
    await fullShot(page, '11-evaluations');

    await page.getByRole('navigation', { name: 'internal navigation' }).getByRole('link', { name: 'Ingestion' }).click();
    await page.waitForURL(/\/app\/ingestion/);
    await expect(page.getByRole('main', { name: 'ingestion page' })).toBeVisible();
    await fullShot(page, '07-ingestion-page');

    if (process.env.E2E_TRIGGER_INGESTION === '1') {
      const trigger = page.getByRole('button', { name: /Trigger 311 ingestion/i });
      if (await trigger.isEnabled().catch(() => false)) {
        await trigger.click();
        await fullShot(page, '08-ingestion-trigger-clicked');
      } else {
        await fullShot(page, '08-ingestion-trigger-disabled');
      }
    }

    await page.getByRole('navigation', { name: 'internal navigation' }).getByRole('link', { name: 'Forecasts' }).click();
    await expect(page.getByText('311 Forecast Overview')).toBeVisible();
    await fullShot(page, '09-back-to-forecasts');
  });
});
