// webapp/src/__tests__/simulator.spec.ts
//
// Playwright E2E tests: full citizen user flow (UI-01 through UI-08).
// Decision: covers splash→preselect→scenario→slider→reset→URL→methodology→mobile.

import { test, expect } from '@playwright/test';

test.describe('Splash & Init', () => {
  test('displays splash screen on initial load', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Chargement du simulateur')).toBeVisible({ timeout: 30000 });
    await expect(page.getByText('Budget Citoyen')).toBeVisible();
  });

  test('transitions from splash to preselect', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Choisissez un scénario')).toBeVisible({ timeout: 30000 });
  });
});

test.describe('Scenario Selection', () => {
  test('displays scenario cards in preselect state', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('button[aria-pressed]');
    const cards = page.locator('button[aria-pressed]');
    const count = await cards.count();
    expect(count).toBeGreaterThanOrEqual(9);
  });

  test('selecting a scenario displays impact', async ({ page }) => {
    await page.goto('/');
    const firstCard = page.locator('button[aria-pressed]').first();
    await firstCard.click({ timeout: 10000 });
    await expect(page.getByText('Foyer modeste')).toBeVisible();
    await expect(page.getByText('Impact sur votre foyer')).toBeVisible();
  });
});

test.describe('Slider Interaction', () => {
  test('sliders become enabled after scenario selection', async ({ page }) => {
    await page.goto('/');
    const firstCard = page.locator('button[aria-pressed]').first();
    await firstCard.click();
    const slider = page.getByRole('slider').first();
    await expect(slider).toBeEnabled({ timeout: 10000 });
  });

  test('keyboard adjusts slider value', async ({ page }) => {
    await page.goto('/');
    const firstCard = page.locator('button[aria-pressed]').first();
    await firstCard.click();
    const slider = page.getByRole('slider').first();
    await slider.focus();
    await page.keyboard.press('ArrowRight');
    await expect(slider).toHaveAttribute('aria-valuenow', /[1-9]/);
  });
});

test.describe('Reset', () => {
  test('Réinitialiser returns to preselect', async ({ page }) => {
    await page.goto('/');
    const firstCard = page.locator('button[aria-pressed]').first();
    await firstCard.click();
    await page.getByText('Réinitialiser').click();
    await expect(page.getByText('Choisissez un scénario')).toBeVisible();
  });
});

test.describe('URL Sharing', () => {
  test('URL contains state parameter after slider drag', async ({ page }) => {
    await page.goto('/');
    const firstCard = page.locator('button[aria-pressed]').first();
    await firstCard.click();
    const slider = page.getByRole('slider').first();
    await slider.focus();
    await page.keyboard.press('ArrowRight');
    await page.waitForTimeout(500);
    const url = page.url();
    expect(url).toContain('state=');
  });
});

test.describe('Methodology Page', () => {
  test('methodology page renders with source attribution', async ({ page }) => {
    await page.goto('/methodologie');
    await expect(page.getByText('Méthodologie')).toBeVisible();
    await expect(page.getByText('Insee')).toBeVisible();
    await expect(page.getByText('budget.gouv.fr')).toBeVisible();
    await expect(page.getByText('Mésange')).toBeVisible();
  });
});

test.describe('Mobile Layout', () => {
  test('mobile viewport shows accordion', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/');
    await expect(page.getByText('Réglages')).toBeVisible({ timeout: 30000 });
  });
});
