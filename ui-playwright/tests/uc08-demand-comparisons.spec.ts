import { test, expect } from '@playwright/test';

// Constants for mock responses
const contextResponse = {
  serviceCategories: ['Sanitation', 'Roads', 'Forestry', 'Parks', 'Water'],
  geographyLevels: ['ward', 'district'],
  geographyOptions: {
    ward: ['Ward 1', 'Ward 2', 'Ward 3'],
    district: ['District A', 'District B']
  }
};

const standardQueryResponse = {
  comparisonRequestId: 'req-standard',
  filters: {
    serviceCategories: ['Sanitation', 'Roads'],
    geographyLevel: 'ward',
    geographyValues: ['Ward 1', 'Ward 2'],
    timeRangeStart: '2026-03-01T00:00:00Z',
    timeRangeEnd: '2026-03-31T23:59:59Z'
  },
  outcomeStatus: 'success',
  comparisonGranularity: 'daily',
  series: [
    {
      seriesType: 'historical',
      serviceCategory: 'Sanitation',
      geographyKey: 'Ward 1',
      points: [{ bucketStart: '2026-03-01', bucketEnd: '2026-03-02', value: 120 }]
    },
    {
      seriesType: 'forecast',
      serviceCategory: 'Sanitation',
      geographyKey: 'Ward 1',
      points: [{ bucketStart: '2026-03-01', bucketEnd: '2026-03-02', value: 125 }]
    }
  ],
  message: 'Comparison complete.'
};

test.describe('UC-08 Demand Comparisons', () => {

  test.beforeEach(async ({ page }) => {
    // Authenticate as a planner before navigating
    const email = process.env.E2E_EMAIL || 'planner@example.com';
    const password = process.env.E2E_PASSWORD || 'local-password';

    // Route for login if needed
    // The smoketest actually does a real login. We will try to rely on the same env variables
    // or just mock the context and queries. Since the app checks the token, we can just intercept
    // the auth endpoint or perform a real login if the environment variables are present.

    // If E2E_EMAIL is set, do a real login (typical for playwright in this repo)
    if (process.env.E2E_EMAIL && process.env.E2E_PASSWORD) {
      await page.goto('/');
      await page.getByLabel('Email', { exact: true }).fill(process.env.E2E_EMAIL);
      await page.getByLabel('Password', { exact: true }).fill(process.env.E2E_PASSWORD);
      await page.locator('form').getByRole('button', { name: 'Sign in' }).click();
      await page.waitForURL(/\/app\/forecasts/);
    }
    
    // Mock the Demand Comparison Context
    await page.route('**/api/v1/demand-comparisons/context', async route => {
      await route.fulfill({ json: contextResponse });
    });

    // Mock Render Events (Always succeed)
    await page.route('**/api/v1/demand-comparisons/*/render-events', async route => {
      await route.fulfill({ status: 202, json: { recordedOutcomeStatus: 'rendered' } });
    });
  });

  test('AT-01: Interface loads and shows filters', async ({ page }) => {
    await page.goto('/app/demand-comparisons');
    
    // Default headings
    await expect(page.getByRole('heading', { name: /Compare approved history/i })).toBeVisible();
    
    // Filter controls present
    await expect(page.getByText('Service categories')).toBeVisible();
    await expect(page.getByLabel('Geography level')).toBeVisible();
    await expect(page.getByLabel('Start')).toBeVisible();
    await expect(page.getByLabel('End')).toBeVisible();
    
    // Context populated categories
    await expect(page.getByRole('button', { name: 'Sanitation' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Roads' })).toBeVisible();
  });

  test('AT-02: Retrieve and visualize comparison with historical and forecast data', async ({ page }) => {
    await page.route('**/api/v1/demand-comparisons/queries', async route => {
      await route.fulfill({ json: standardQueryResponse });
    });

    await page.goto('/app/demand-comparisons');
    
    // Add Category
    await page.getByRole('button', { name: 'Roads' }).click();
    
    // Ensure button is enabled
    const submitBtn = page.getByRole('button', { name: 'Compare demand' });
    await expect(submitBtn).toBeEnabled();
    
    // Submit
    await submitBtn.click();
    
    // Verify results render
    await expect(page.getByRole('heading', { name: 'Comparison summary' })).toBeVisible();
    await expect(page.getByText('Outcome: success')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Series table' })).toBeVisible();
    await expect(page.getByText('2026-03-01 - 120')).toBeVisible();
    await expect(page.getByText('2026-03-01 - 125')).toBeVisible();
  });

  test('AT-04: High-volume request triggers warning and proceeds on acknowledgment', async ({ page }) => {
    let warningShown = false;
    await page.route('**/api/v1/demand-comparisons/queries', async route => {
      const payload = route.request().postDataJSON();
      if (!warningShown) {
        warningShown = true;
        // First request returns warning
        await route.fulfill({ 
          json: { 
            comparisonRequestId: 'req-warning',
            outcomeStatus: 'warning_required',
            message: 'Large scope detected',
            warning: { message: 'Large scope detected', shown: true, acknowledged: false },
            series: [] 
          }
        });
      } else {
        // Second request (proceed) returns success
        await route.fulfill({ json: standardQueryResponse });
      }
    });

    await page.goto('/app/demand-comparisons');
    await page.getByRole('button', { name: 'Forestry' }).click();
    await page.getByRole('button', { name: 'Compare demand' }).click();

    // Verify Warning Modal
    await expect(page.getByText('Large request warning')).toBeVisible();
    await expect(page.getByText('Large scope detected')).toBeVisible();

    // Proceed
    await page.getByRole('button', { name: 'Proceed' }).click();
    
    // Validate it loaded
    await expect(page.getByRole('heading', { name: 'Comparison summary' })).toBeVisible();
    await expect(page.getByText('Outcome: success')).toBeVisible();
  });

  test('AT-05 & AT-06: Partial combinations / Missing data UI states', async ({ page }) => {
    await page.route('**/api/v1/demand-comparisons/queries', async route => {
      await route.fulfill({ 
        json: {
          comparisonRequestId: 'req-partial',
          outcomeStatus: 'partial_forecast_missing',
          series: [],
          missingCombinations: [
            { category: 'Roads', message: 'Forecast missing for Roads' }
          ]
        }
      });
    });

    await page.goto('/app/demand-comparisons');
    await page.getByRole('button', { name: 'Roads' }).click();
    await page.getByRole('button', { name: 'Compare demand' }).click();

    // Missing data message rendered
    await expect(page.getByRole('heading', { name: 'Missing combinations' })).toBeVisible();
    await expect(page.getByText('Forecast missing for Roads')).toBeVisible();
    await expect(page.getByText('Outcome: partial_forecast_missing')).toBeVisible();
  });

  test('AT-08: Data alignment issue prevents comparison', async ({ page }) => {
    await page.route('**/api/v1/demand-comparisons/queries', async route => {
      await route.fulfill({ 
        json: {
          comparisonRequestId: 'req-err',
          outcomeStatus: 'alignment_failed',
          message: 'Historical and forecast demands could not be aligned.',
          series: []
        }
      });
    });

    await page.goto('/app/demand-comparisons');
    await page.getByRole('button', { name: 'Parks' }).click();
    await page.getByRole('button', { name: 'Compare demand' }).click();

    // Error component rendered
    await expect(page.getByText(/could not be aligned/)).toBeVisible();
  });
});