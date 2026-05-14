// webapp/src/__tests__/a11y.spec.ts
//
// Axe-core Playwright accessibility audit tests (A11Y-01 through A11Y-06).
// Decision: runs axe on preselect, scenario_displaying, and error states.

import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test.describe('accessibility — preselect state', () => {
  test('axe-core finds no violations on preselect', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('button[aria-pressed]', { timeout: 30000 });

    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
  });
});

test.describe('accessibility — scenario displaying', () => {
  test('axe-core finds no violations after scenario selection', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('button[aria-pressed]', { timeout: 30000 });
    const firstCard = page.locator('button[aria-pressed]').first();
    await firstCard.click();

    await page.waitForTimeout(2000);
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
  });
});

test.describe('Slider ARIA attributes (A11Y-05)', () => {
  test('slider has required ARIA attributes', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('button[aria-pressed]', { timeout: 30000 });
    const firstCard = page.locator('button[aria-pressed]').first();
    await firstCard.click();

    const slider = page.getByRole('slider').first();
    await expect(slider).toHaveAttribute('aria-valuemin', '-30');
    await expect(slider).toHaveAttribute('aria-valuemax', '30');
    await expect(slider).toHaveAttribute('aria-valuenow');
  });
});

test.describe('Chart ARIA (A11Y-01)', () => {
  test('chart containers have role="img"', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('button[aria-pressed]', { timeout: 30000 });
    const firstCard = page.locator('button[aria-pressed]').first();
    await firstCard.click();

    await page.waitForTimeout(2000);
    const imgs = page.locator('[role="img"]');
    const count = await imgs.count();
    expect(count).toBeGreaterThanOrEqual(4);
  });

  test('chart figures have aria-labelledby', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('button[aria-pressed]', { timeout: 30000 });
    const firstCard = page.locator('button[aria-pressed]').first();
    await firstCard.click();

    await page.waitForTimeout(2000);
    const labelled = page.locator('[role="img"][aria-labelledby]');
    const count = await labelled.count();
    expect(count).toBeGreaterThanOrEqual(4);
  });
});

test.describe('Chart table fallback (A11Y-02)', () => {
  test('each chart has a screen-reader table with th scope', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('button[aria-pressed]', { timeout: 30000 });
    const firstCard = page.locator('button[aria-pressed]').first();
    await firstCard.click();

    await page.waitForTimeout(2000);
    const headerCells = page.locator('th[scope="col"]');
    const count = await headerCells.count();
    expect(count).toBeGreaterThan(0);
  });
});

test.describe('Slider keyboard navigation (A11Y-05)', () => {
  test('keyboard ArrowRight updates aria-valuenow', async ({ page }) => {
    await page.goto('/');
    await page.waitForSelector('button[aria-pressed]', { timeout: 30000 });
    const firstCard = page.locator('button[aria-pressed]').first();
    await firstCard.click();

    const slider = page.getByRole('slider').first();
    const before = await slider.getAttribute('aria-valuenow');
    await slider.focus();
    await page.keyboard.press('ArrowRight');
    const after = await slider.getAttribute('aria-valuenow');
    expect(before).not.toBe(after);
  });
});

test.describe('Pattern fills (A11Y-03)', () => {
  test('SVG pattern defs use deuteranopia-safe Wong 2011 color palette', async ({ page }) => {
    // The app auto-selects baseline on init. Wait for displaying state.
    await page.goto('/');

    // Wait for displaying state with charts rendered
    await expect(page.getByText('Projections macroéconomiques')).toBeVisible({ timeout: 30000 });

    // The hidden SVG defs should exist in the DOM
    const svgDefs = page.locator('svg[aria-hidden="true"] defs');
    await expect(svgDefs).toHaveCount(1);

    // All four pattern elements should be present
    const patterns = svgDefs.locator('pattern');
    await expect(patterns).toHaveCount(4);

    // Verify the four pattern IDs match CHART_PATTERNS_SVG definitions
    const patternIds = await svgDefs.locator('pattern').evaluateAll((els) =>
      els.map((el) => el.getAttribute('id')),
    );
    expect(patternIds).toContain('pattern-deficit');
    expect(patternIds).toContain('pattern-debt');
    expect(patternIds).toContain('pattern-gdp');
    expect(patternIds).toContain('pattern-employment');

    // Verify deuteranopia-safe Wong 2011 colors are present in SVG content
    const svgContent = await svgDefs.evaluate((el) => el.innerHTML);
    expect(svgContent).toContain('#0072B2'); // pattern-deficit (blue)
    expect(svgContent).toContain('#E69F00'); // pattern-debt (orange)
    expect(svgContent).toContain('#009E73'); // pattern-gdp (green)
    expect(svgContent).toContain('#CC79A7'); // pattern-employment (pink)
  });

  test('pattern defs are present even before scenario selection (empty chart state)', async ({ page }) => {
    await page.goto('/');

    // The ChartGrid renders its hidden SVG patterns regardless of macroResult.
    // Wait for the page to reach a stable state where ChartGrid is mounted.
    // Use the methodology link in Footer as a signal the page is loaded.
    await expect(page.getByRole('link', { name: 'Méthodologie et sources' })).toBeVisible({ timeout: 30000 });

    // Find the hidden SVG with pattern definitions
    const svgDefs = page.locator('svg[aria-hidden="true"] defs');
    await expect(svgDefs).toHaveCount(1);

    const patterns = svgDefs.locator('pattern');
    await expect(patterns).toHaveCount(4);
  });
});

test.describe('Methodology page accessibility', () => {
  test('axe-core finds no violations on methodology page', async ({ page }) => {
    await page.goto('/methodologie');
    const results = await new AxeBuilder({ page }).analyze();
    expect(results.violations).toEqual([]);
  });
});
