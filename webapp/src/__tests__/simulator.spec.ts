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
    await expect(page.getByRole('heading', { name: 'Choisissez un scénario pour' }).first()).toBeVisible({ timeout: 30000 });
  });
});

test.describe('Scenario Selection', () => {
  test('displays scenario cards in preselect state', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('button[aria-pressed]:visible');
    const cards = page.locator('button[aria-pressed]:visible');
    const count = await cards.count();
    expect(count).toBeGreaterThanOrEqual(9);
  });

  test('selecting a scenario displays impact', async ({ page }) => {
    await page.goto('/');
    const firstCard = page.locator('button[aria-pressed]:visible').first();
    await firstCard.click({ timeout: 10000 });
    await expect(page.getByText('Foyer modeste')).toBeVisible();
    await expect(page.getByText('Impact sur votre foyer')).toBeVisible();
  });
});

test.describe('Slider Interaction', () => {
  test('sliders become enabled after scenario selection', async ({ page }) => {
    await page.goto('/');
    const firstCard = page.locator('button[aria-pressed]:visible').first();
    await firstCard.click();
    const slider = page.getByRole('slider').first();
    await expect(slider).toBeEnabled({ timeout: 10000 });
  });

  test('keyboard adjusts slider value', async ({ page }) => {
    await page.goto('/');
    const firstCard = page.locator('button[aria-pressed]:visible').first();
    await firstCard.click();
    const slider = page.getByRole('slider').first();
    await slider.focus();
    await page.keyboard.press('ArrowRight');
    await expect(slider).toHaveAttribute('value', /[1-9]/);
  });
});

test.describe('Reset', () => {
  test('Réinitialiser returns to preselect', async ({ page }) => {
    await page.goto('/');
    const firstCard = page.locator('button[aria-pressed]:visible').first();
    await firstCard.click();
    await page.getByRole('button', { name: 'Réinitialiser' }).first().click();
    await expect(page.getByRole('heading', { name: 'Choisissez un scénario pour' }).first()).toBeVisible();
  });
});

test.describe('URL Sharing', () => {
  test('URL contains state parameter after slider drag', async ({ page }) => {
    await page.goto('/');
    const firstCard = page.locator('button[aria-pressed]:visible').first();
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
    await expect(page.getByRole('heading', { name: 'Méthodologie' })).toBeVisible();
    await expect(page.locator('strong').getByText('Insee', { exact: true })).toBeVisible();
    await expect(page.getByText('budget.gouv.fr')).toBeVisible();
    await expect(page.getByText('Mésange')).toBeVisible();
  });
});

test.describe('Loading Indicator (UI-07)', () => {
  test('loading pulse visible on slider track during computation', async ({ page }) => {
    // The app auto-selects baseline on init. Wait for displaying state to appear.
    await page.goto('/');

    // Wait for the splash screen to show (proves page is loading)
    await expect(page.getByText('Chargement du simulateur')).toBeVisible({ timeout: 30000 });

    // Wait for displaying state — charts and impact should render after auto-init
    await expect(page.getByText('Impact sur votre foyer')).toBeVisible({ timeout: 30000 });
    await expect(page.getByText('Projections macroéconomiques')).toBeVisible({ timeout: 30000 });

    // Sliders should be enabled in displaying state
    const slider = page.getByRole('slider').first();
    await expect(slider).toBeEnabled({ timeout: 10000 });

    // Trigger slider value change + drag-end (ArrowRight then Tab to blur)
    await slider.focus();
    await page.keyboard.press('ArrowRight');
    await page.keyboard.press('Tab'); // triggers React Aria onChangeEnd → handleDragEnd

    // After drag-end, LeverSlider wraps onChangeEnd in startTransition,
    // causing animate-pulse class on the slider track during the transition batch.
    // Check for any element with animate-pulse in the DOM right after interaction.
    const pulseLocator = page.locator('.animate-pulse');
    const hasPulse = (await pulseLocator.count()) > 0;

    // The requirement UI-07 demands a CSS opacity pulse visible during
    // worker computation. The LeverSlider track has animate-pulse during
    // its useTransition wrapping of onChangeEnd, which kicks off the
    // macro computation via handleDragEnd → orchestrator.project().
    expect(hasPulse).toBe(true);
  });
});

test.describe('Mobile Layout', () => {
  test('mobile viewport shows accordion', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto('/');
    await expect(page.getByText('Réglages')).toBeVisible({ timeout: 30000 });
  });
});
