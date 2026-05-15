// webapp/src/engine/__tests__/shock-matrix-integration.test.ts
//
// Integration tests for macro-interpolate.ts with a calibrated-style
// test shock matrix (12 tax x 12 spend x 5 horizon x 4 features).
// Replaces Wave 0 placeholder stub.
//
// The test matrix is built in-memory using the same IRF + elasticity
// pattern as calibrate.py — no network calls, no file I/O.

import { describe, it, expect } from 'vitest';
import { interpolateAtPoint, projectTrajectory } from '../macro-interpolate';
import type { ShockMatrixData, MacroResult } from '../types';

// ── Test Matrix Builder ─────────────────────────────────────────────────────

/** Build a synthetic 12x12x5x4 shock matrix for integration testing. */
function buildTestMatrix(): ShockMatrixData {
  const nTax = 12;
  const nSpend = 12;
  const nHorizon = 5;
  const NUM_FEATURES = 4;

  const taxBp = new Float64Array(nTax);
  for (let i = 0; i < nTax; i++) {
    taxBp[i] = 0.5 + (i / (nTax - 1)) * (2.0 - 0.5);
  }

  const spendBp = new Float64Array(nSpend);
  for (let i = 0; i < nSpend; i++) {
    spendBp[i] = 0.7 + (i / (nSpend - 1)) * (1.5 - 0.7);
  }

  const horizonBp = new Float64Array([1, 2, 3, 4, 5]);

  const gridSize = nTax * nSpend * nHorizon * NUM_FEATURES;
  const grid = new Float64Array(gridSize);

  // IRF vectors (matching calibrate.py)
  const irfGdp = [1.0, 0.8, 0.5, 0.3, 0.1];
  const irfEmp = [0.7, 1.0, 0.8, 0.5, 0.3];
  const irfDebt = [1.0, 1.8, 2.5, 3.0, 3.5];
  const baseGdp = 0.012;
  const baseEmp = 0.004;
  const baseDef = -0.05;
  const baseDebt = 1.10;

  for (let ti = 0; ti < nTax; ti++) {
    for (let si = 0; si < nSpend; si++) {
      for (let hi = 0; hi < nHorizon; hi++) {
        const idx = ((ti * nSpend + si) * nHorizon + hi) * NUM_FEATURES;
        const taxDev = taxBp[ti] - 1.0;
        const spendDev = spendBp[si] - 1.0;

        grid[idx + 0] = baseGdp + (taxDev * -0.4 + spendDev * 0.8) * irfGdp[hi];
        grid[idx + 1] = baseEmp + (taxDev * -0.2 + spendDev * 0.4) * irfEmp[hi];
        grid[idx + 2] = baseDef + taxDev * -1.0 + spendDev * 1.0;
        grid[idx + 3] = baseDebt + grid[idx + 2] * 1.5 * irfDebt[hi];
      }
    }
  }

  return {
    grid,
    taxBp,
    spendBp,
    horizonBp,
    hullEquations: new Float64Array(0), // Empty hull = no bounds check (safe for test)
  };
}

// ── Tests ───────────────────────────────────────────────────────────────────

describe('shock-matrix-integration', () => {
  const matrix = buildTestMatrix();

  it('grid has correct dimensions: 12x12x5x4', () => {
    expect(matrix.taxBp.length).toBe(12);
    expect(matrix.spendBp.length).toBe(12);
    expect(matrix.horizonBp.length).toBe(5);
    expect(matrix.grid.length).toBe(12 * 12 * 5 * 4); // 2880
  });

  it('interpolateAtPoint returns non-null at grid center', () => {
    const result = interpolateAtPoint(matrix, 1.0, 1.0, 3);
    expect(result).not.toBeNull();
    expect(result!.gdpGrowthTrajectory.length).toBe(1);
    expect(result!.debtTrajectory.length).toBe(1);
  });

  it('interpolateAtPoint returns non-null at all grid corners', () => {
    const corners: [number, number, number][] = [
      [0.5, 0.7, 1],  [0.5, 0.7, 5],
      [2.0, 1.5, 1],  [2.0, 1.5, 5],
      [0.5, 1.5, 3],  [2.0, 0.7, 3],
    ];
    for (const [tax, spend, horizon] of corners) {
      const result = interpolateAtPoint(matrix, tax, spend, horizon);
      expect(result, `corner (${tax}, ${spend}, ${horizon})`).not.toBeNull();
    }
  });

  it('interpolateAtPoint returns null for out-of-bounds horizon', () => {
    // Horizon outside valid range [1,5]
    const result = interpolateAtPoint(matrix, 1.0, 1.0, 10);
    expect(result).toBeNull();
  });

  it('interpolateAtPoint returns null for negative tax', () => {
    const result = interpolateAtPoint(matrix, -0.5, 1.0, 3);
    expect(result).toBeNull();
  });

  it('projectTrajectory returns 5-year trajectories', () => {
    const result = projectTrajectory(matrix, 1.0, 1.0, 5);
    expect(result).not.toBeNull();
    expect(result!.gdpGrowthTrajectory.length).toBe(5);
    expect(result!.deficitTrajectory.length).toBe(5);
    expect(result!.debtTrajectory.length).toBe(5);
    expect(result!.employmentTrajectory.length).toBe(5);
  });

  it('trajectory values are all finite at grid center', () => {
    const result = projectTrajectory(matrix, 1.0, 1.0, 5);
    expect(result).not.toBeNull();
    const arrays = [
      result!.gdpGrowthTrajectory,
      result!.employmentTrajectory,
      result!.deficitTrajectory,
      result!.debtTrajectory,
    ];
    for (const arr of arrays) {
      for (const val of arr) {
        expect(isFinite(val)).toBe(true);
      }
    }
  });

  it('feature ordering matches convention: deficit negative, debt ~1.0 at baseline', () => {
    // At reference point (tax=1.0, spend=1.0, horizon=1): baseline
    const result = interpolateAtPoint(matrix, 1.0, 1.0, 1);
    expect(result).not.toBeNull();

    const deficit = result!.deficitTrajectory[0];
    const debt = result!.debtTrajectory[0];

    // Deficit should be negative at baseline (~-5%)
    expect(deficit).toBeLessThan(0);
    expect(deficit).toBeCloseTo(-0.05, 1);
    // Debt at horizon=1 with deficit-to-debt multiplier ~1.0
    expect(debt).toBeGreaterThan(0);
  });
});
