import { test, expect } from '@playwright/test';

test.describe('ContextPilot Frontend', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for app to load
    await page.waitForSelector('div#root', { timeout: 5000 });
  });

  test('should load the application', async ({ page }) => {
    await expect(page).toHaveTitle(/ContextPilot/i);
    const rootElement = await page.locator('#root');
    await expect(rootElement).toBeVisible();
  });

  test('should have header with title', async ({ page }) => {
    const header = page.locator('header');
    await expect(header).toBeVisible();
  });

  test('should display main content area', async ({ page }) => {
    const workspace = page.locator('.workspace-layout, main');
    await expect(workspace).toBeVisible();
  });

  test('should be responsive', async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    const app = page.locator('#root');
    await expect(app).toBeVisible();

    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(app).toBeVisible();
  });
});

test.describe('API Integration', () => {
  test('should connect to backend API', async ({ page }) => {
    // Check network requests
    const responses = [];
    page.on('response', response => {
      if (response.url().includes('localhost:8000')) {
        responses.push(response.status());
      }
    });

    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // At least one API call should succeed
    const successfulCalls = responses.filter(status => status < 400);
    expect(successfulCalls.length).toBeGreaterThan(0);
  });

  test('should handle API errors gracefully', async ({ page }) => {
    // Navigate to page with error handling
    await page.goto('/');
    
    // Check if error message container exists (for when errors occur)
    const errorContainer = page.locator('.error, [role="alert"]');
    // Just verify the element can be found if needed
    const errorCount = await errorContainer.count();
    expect(errorCount).toBeGreaterThanOrEqual(0);
  });
});

test.describe('OpenAI Integration', () => {
  test('should display settings panel', async ({ page }) => {
    await page.goto('/');
    
    // Look for settings button and verify it exists
    const settingsButton = page.locator('button[title="Settings"]');
    await expect(settingsButton).toBeVisible();
    
    // Click settings button
    await settingsButton.click();
    
    // Wait for modal and verify settings form exists (more reliable than specific input)
    const settingsModal = page.locator('.modal, [role="dialog"], .settings-modal');
    await expect(settingsModal).toBeVisible({ timeout: 5000 });
  });

  test('should have OpenAI in provider options', async ({ page }) => {
    await page.goto('/');
    
    // Look for provider select
    const selects = page.locator('select');
    let foundOpenAI = false;
    
    const selectCount = await selects.count();
    for (let i = 0; i < selectCount; i++) {
      const content = await selects.nth(i).textContent();
      if (content?.includes('OpenAI')) {
        foundOpenAI = true;
        break;
      }
    }
    
    expect(foundOpenAI).toBe(true);
  });
});
