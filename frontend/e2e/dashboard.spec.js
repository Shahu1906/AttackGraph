import { test, expect } from '@playwright/test';

test.describe('AttackGraphX Smoke Test Suite', () => {
  test('User login -> view dashboard -> execute what-if simulation', async ({ page }) => {
    // 1. Navigate to Login Page
    await page.goto('http://localhost:3000/login');
    await expect(page.locator('h1')).toContainText('AttackGraphX');

    // 2. Fill Admin Credentials and Sign In
    await page.fill('input[type="text"]', 'admin');
    await page.fill('input[type="password"]', 'admin123');
    await page.click('button[type="submit"]');

    // 3. Verify Navigation to Executive Dashboard
    await page.waitForURL('http://localhost:3000/');
    await expect(page.locator('text=Total Attack Paths')).toBeVisible();
    await expect(page.locator('text=Critical Risk Paths')).toBeVisible();

    // 4. Navigate to What-If Simulation Tab
    await page.click('button:has-text("What-If Engine")');
    await expect(page.locator('text=What-If Remediation Simulator')).toBeVisible();

    // 5. Select Vulnerability to Remediate
    const vulnSelect = page.locator('select');
    await vulnSelect.selectOption({ index: 1 });

    // 6. Click Simulate Fix Button
    await page.click('button:has-text("Simulate Fix")');

    // 7. Assert Updated Metric Numbers and Delta Badges Render
    await expect(page.locator('text=Remediation Impact Analysis')).toBeVisible();
    await expect(page.locator('text=Total Attack Paths')).toBeVisible();
    await expect(page.locator('text=paths')).toBeVisible();
  });
});
