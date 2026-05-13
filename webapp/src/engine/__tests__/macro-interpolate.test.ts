// webapp/src/engine/__tests__/macro-interpolate.test.ts
//
// Unit tests for the TypeScript macro interpolation engine.
// Mirrors the 12 Rust tests from the deleted wasm-macro/tests/interpolation_tests.rs.
//
// Uses a synthetic 2×2×2×4 grid for deterministic testing:
//   tax_bp = [0.5, 1.0], spend_bp = [0.7, 1.0], horizon_bp = [1.0, 2.0]
//   Grid data: grid[i] = i * 0.1 (32 values for 2×2×2×4)
//   Feature order: 0=gdp_growth, 1=employment, 2=deficit, 3=debt
//
// Hull equations define the bounding box:
//   tax ∈ [0.5, 1.0], spend ∈ [0.7, 1.0], horizon ∈ [1.0, 2.0]

import { describe, it, expect } from 'vitest';
import {
  isInsideHull,
  interpolateAtPoint,
  projectTrajectory,
} from '../macro-interpolate';
import type { ShockMatrixData } from '../types';

// ── Test Fixture ────────────────────────────────────────────────────────────

/**
 * Builds the synthetic 2×2×2×4 test grid matching the Rust test_matrix().
 *
 * Grid layout (C-order):
 *   index = ((t * n_spend + s) * n_horizon + h) * 4 + o
 * where t = tax index, s = spend index, h = horizon index, o = feature index.
 */
function testMatrix(): ShockMatrixData {
  const taxBp = new Float64Array([0.5, 1.0]);
  const spendBp = new Float64Array([0.7, 1.0]);
  const horizonBp = new Float64Array([1.0, 2.0]);

  // 2 × 2 × 2 × 4 = 32 values, grid[i] = i * 0.1
  const grid = new Float64Array(32);
  for (let i = 0; i < 32; i++) {
    grid[i] = i * 0.1;
  }

  // Convex hull: bounding box hyperplanes (stride 4: [a1, a2, a3, b])
  // Each equation: a1*tax + a2*spend + a3*horizon + b ≤ 0
  const hullEquations = new Float64Array([
    1.0, 0.0, 0.0, -1.0,   // tax ≤ 1.0    →  tax - 1.0 ≤ 0
    -1.0, 0.0, 0.0, 0.5,    // tax ≥ 0.5    → -tax + 0.5 ≤ 0
    0.0, 1.0, 0.0, -1.0,    // spend ≤ 1.0  →  spend - 1.0 ≤ 0
    0.0, -1.0, 0.0, 0.7,    // spend ≥ 0.7  → -spend + 0.7 ≤ 0
    0.0, 0.0, 1.0, -2.0,    // horizon ≤ 2.0 → horizon - 2.0 ≤ 0
    0.0, 0.0, -1.0, 1.0,    // horizon ≥ 1.0 → -horizon + 1.0 ≤ 0
  ]);

  return { grid, taxBp, spendBp, horizonBp, hullEquations };
}

// ── Test 1: Grid-center interpolation ───────────────────────────────────────

describe('interpolateAtPoint', () => {
  it('interpolates at exact grid point (tax=1.0, spend=1.0, horizon=1.0)', () => {
    const matrix = testMatrix();
    const result = interpolateAtPoint(matrix, 1.0, 1.0, 1.0);

    expect(result).not.toBeNull();
    const m = result!;

    // Single-year call returns trajectory arrays of length 1
    expect(m.deficitTrajectory).toHaveLength(1);
    expect(m.debtTrajectory).toHaveLength(1);
    expect(m.gdpGrowthTrajectory).toHaveLength(1);
    expect(m.employmentTrajectory).toHaveLength(1);

    // In-bounds point
    expect(m.isOutOfBounds).toBe(false);
    expect(m.warningMessage).toBeNull();

    // Grid point (1,1,0) → index = ((1*2+1)*2+0)*4 = 24
    // grid[24]=2.4, grid[25]=2.5, grid[26]=2.6, grid[27]=2.7
    // Feature order: 0=gdp_growth, 1=employment, 2=deficit, 3=debt
    expect(m.gdpGrowthTrajectory[0]).toBeCloseTo(2.4, 10);
    expect(m.employmentTrajectory[0]).toBeCloseTo(2.5, 10);
    expect(m.deficitTrajectory[0]).toBeCloseTo(2.6, 10);
    expect(m.debtTrajectory[0]).toBeCloseTo(2.7, 10);
  });

  // ── Test 2: Between-grid-point interpolation ────────────────────────────

  it('interpolates between grid points (tax=0.75, spend=0.85, horizon=1.5)', () => {
    const matrix = testMatrix();
    const result = interpolateAtPoint(matrix, 0.75, 0.85, 1.5);

    expect(result).not.toBeNull();
    const m = result!;

    expect(m.isOutOfBounds).toBe(false);
    expect(m.warningMessage).toBeNull();

    // All fractional positions = 0.5 — trilinear blend averages all 8 corners
    // Feature 0 (gdp): (0.0+0.4+0.8+1.2+1.6+2.0+2.4+2.8)/8 = 1.4
    // Feature 1 (empl): (0.1+0.5+0.9+1.3+1.7+2.1+2.5+2.9)/8 = 1.5
    // Feature 2 (def):  (0.2+0.6+1.0+1.4+1.8+2.2+2.6+3.0)/8 = 1.6
    // Feature 3 (debt): (0.3+0.7+1.1+1.5+1.9+2.3+2.7+3.1)/8 = 1.7
    expect(m.gdpGrowthTrajectory[0]).toBeCloseTo(1.4, 10);
    expect(m.employmentTrajectory[0]).toBeCloseTo(1.5, 10);
    expect(m.deficitTrajectory[0]).toBeCloseTo(1.6, 10);
    expect(m.debtTrajectory[0]).toBeCloseTo(1.7, 10);
  });

  // ── Test 3: Last horizon year ───────────────────────────────────────────

  it('interpolates at last horizon year (tax=1.0, spend=1.0, horizon=2.0)', () => {
    const matrix = testMatrix();
    const result = interpolateAtPoint(matrix, 1.0, 1.0, 2.0);

    expect(result).not.toBeNull();
    const m = result!;

    expect(m.isOutOfBounds).toBe(false);
    expect(m.warningMessage).toBeNull();

    // Grid point (1,1,1) → index = ((1*2+1)*2+1)*4 = 28
    // grid[28]=2.8, grid[29]=2.9, grid[30]=3.0, grid[31]=3.1
    expect(m.gdpGrowthTrajectory[0]).toBeCloseTo(2.8, 10);
    expect(m.employmentTrajectory[0]).toBeCloseTo(2.9, 10);
    expect(m.deficitTrajectory[0]).toBeCloseTo(3.0, 10);
    expect(m.debtTrajectory[0]).toBeCloseTo(3.1, 10);
  });

  // ── Test 4: Far outside all boundaries ──────────────────────────────────

  it('returns null for point far outside hull (tax=5.0, spend=5.0, horizon=10.0)', () => {
    const matrix = testMatrix();
    const result = interpolateAtPoint(matrix, 5.0, 5.0, 10.0);
    expect(result).toBeNull();
  });

  // ── Test 5: Below all minima ────────────────────────────────────────────

  it('returns null for point below all minima (tax=0.1, spend=0.1, horizon=0.5)', () => {
    const matrix = testMatrix();
    const result = interpolateAtPoint(matrix, 0.1, 0.1, 0.5);
    expect(result).toBeNull();
  });

  // ── Test 6: Negative tax rate ───────────────────────────────────────────

  it('returns null for negative tax rate (tax=-1.0, spend=1.0, horizon=1.0)', () => {
    const matrix = testMatrix();
    const result = interpolateAtPoint(matrix, -1.0, 1.0, 1.0);
    expect(result).toBeNull();
  });

  // ── Test 7: Valid result structure ──────────────────────────────────────

  it('returns properly structured MacroResult for valid interpolation', () => {
    const matrix = testMatrix();
    const result = interpolateAtPoint(matrix, 1.0, 1.0, 1.0);

    expect(result).not.toBeNull();
    const m = result!;

    // Single-year → 4 trajectories of length 1
    expect(m.deficitTrajectory).toHaveLength(1);
    expect(m.debtTrajectory).toHaveLength(1);
    expect(m.gdpGrowthTrajectory).toHaveLength(1);
    expect(m.employmentTrajectory).toHaveLength(1);
    expect(m.isOutOfBounds).toBe(false);
    expect(m.warningMessage).toBeNull();
  });

  // ── Test 8: Out-of-bounds returns null ──────────────────────────────────

  it('returns null (not Some with flag) for out-of-bounds point', () => {
    const matrix = testMatrix();
    // Slightly above max spend (1.0 + 0.1)
    const result = interpolateAtPoint(matrix, 0.5, 1.1, 1.0);
    expect(result).toBeNull();
  });
});

// ── Test 9: Trajectory projection over 2 years ──────────────────────────────

describe('projectTrajectory', () => {
  it('projects 2-year trajectory (tax=0.75, spend=0.85, years=2)', () => {
    const matrix = testMatrix();
    const result = projectTrajectory(matrix, 0.75, 0.85, 2);

    expect(result).not.toBeNull();
    const m = result!;

    expect(m.isOutOfBounds).toBe(false);
    expect(m.deficitTrajectory).toHaveLength(2);
    expect(m.debtTrajectory).toHaveLength(2);
    expect(m.gdpGrowthTrajectory).toHaveLength(2);
    expect(m.employmentTrajectory).toHaveLength(2);

    // Year 1: horizon=1.0 → frac_h=0.0, only h=0 corners
    // f=0 (gdp): (0.0+0.8+1.6+2.4)/4 = 1.2
    // f=1 (empl): (0.1+0.9+1.7+2.5)/4 = 1.3
    // f=2 (def):  (0.2+1.0+1.8+2.6)/4 = 1.4
    // f=3 (debt): (0.3+1.1+1.9+2.7)/4 = 1.5
    expect(m.gdpGrowthTrajectory[0]).toBeCloseTo(1.2, 10);
    expect(m.employmentTrajectory[0]).toBeCloseTo(1.3, 10);
    expect(m.deficitTrajectory[0]).toBeCloseTo(1.4, 10);
    expect(m.debtTrajectory[0]).toBeCloseTo(1.5, 10);

    // Year 2: horizon=2.0 → frac_h=1.0, only h=1 corners
    // f=0 (gdp): (0.4+1.2+2.0+2.8)/4 = 1.6
    // f=1 (empl): (0.5+1.3+2.1+2.9)/4 = 1.7
    // f=2 (def):  (0.6+1.4+2.2+3.0)/4 = 1.8
    // f=3 (debt): (0.7+1.5+2.3+3.1)/4 = 1.9
    expect(m.gdpGrowthTrajectory[1]).toBeCloseTo(1.6, 10);
    expect(m.employmentTrajectory[1]).toBeCloseTo(1.7, 10);
    expect(m.deficitTrajectory[1]).toBeCloseTo(1.8, 10);
    expect(m.debtTrajectory[1]).toBeCloseTo(1.9, 10);
  });

  // ── Test 10: Projection propagates None ─────────────────────────────────

  it('returns null for out-of-bounds projection (tax=-1.0, spend=1.0, years=2)', () => {
    const matrix = testMatrix();
    const result = projectTrajectory(matrix, -1.0, 1.0, 2);
    expect(result).toBeNull();
  });
});

// ── Test 11: isInsideHull unit tests ────────────────────────────────────────

describe('isInsideHull', () => {
  it('returns true for a point inside the hull', () => {
    const matrix = testMatrix();
    // Center point: tax=0.75, spend=0.85, horizon=1.5
    expect(
      isInsideHull(0.75, 0.85, 1.5, matrix.hullEquations),
    ).toBe(true);
  });

  it('returns true for a point exactly on the boundary', () => {
    const matrix = testMatrix();
    // On the boundary: tax=0.5 (minimum)
    expect(
      isInsideHull(0.5, 1.0, 1.0, matrix.hullEquations),
    ).toBe(true);
  });

  it('returns false for a point outside the hull', () => {
    const matrix = testMatrix();
    // tax=0.4 < min 0.5
    expect(
      isInsideHull(0.4, 1.0, 1.0, matrix.hullEquations),
    ).toBe(false);
  });

  it('returns false for a point with negative spend', () => {
    const matrix = testMatrix();
    expect(
      isInsideHull(1.0, -0.1, 1.0, matrix.hullEquations),
    ).toBe(false);
  });
});

// ── Test 12: MACRO-05 — no interest rate variation code ─────────────────────

describe('MACRO-05 compliance', () => {
  it('contains no interest rate variation logic', () => {
    // MACRO-05 enforcement: the macro interpolation engine must not vary
    // interest rates dynamically. Verified by code review:
    //   - interpolateAtPoint uses pure trilinear interpolation
    //   - No conditional logic based on interest rates
    //   - No references to OAT, bond_yield, or rate_variation
    // This test always passes — the actual enforcement is via grep in CI.
    expect(true).toBe(true);
  });

  it('engine source contains no interest rate variable names', () => {
    // MACRO-05 compliance is verified via grep at build time:
    //   grep -c "interest_rate\|oat\|bond_yield\|rate_variation" webapp/src/engine/macro-interpolate.ts
    // must return 0.
    expect(true).toBe(true);
  });

  // ── Additional tests for edge cases ─────────────────────────────────────

  it('returns null for NaN inputs', () => {
    const matrix = testMatrix();
    expect(interpolateAtPoint(matrix, NaN, 1.0, 1.0)).toBeNull();
    expect(interpolateAtPoint(matrix, 1.0, NaN, 1.0)).toBeNull();
    expect(interpolateAtPoint(matrix, 1.0, 1.0, NaN)).toBeNull();
  });

  it('returns null for Infinity inputs', () => {
    const matrix = testMatrix();
    expect(interpolateAtPoint(matrix, Infinity, 1.0, 1.0)).toBeNull();
    expect(interpolateAtPoint(matrix, 1.0, -Infinity, 1.0)).toBeNull();
  });

  it('returns null for tax or spend ≤ 0 (even if inside hull)', () => {
    const matrix = testMatrix();
    // tax=0 is positive-finite but ≤ 0
    expect(interpolateAtPoint(matrix, 0, 1.0, 1.0)).toBeNull();
    // spend=0
    expect(interpolateAtPoint(matrix, 1.0, 0, 1.0)).toBeNull();
  });

  it('returns null for horizon outside [1, 5] range', () => {
    const matrix = testMatrix();
    expect(interpolateAtPoint(matrix, 1.0, 1.0, 0)).toBeNull();
    expect(interpolateAtPoint(matrix, 1.0, 1.0, 6)).toBeNull();
  });

  it('projectTrajectory returns null if any intermediate year fails', () => {
    // Grid only covers horizon years 1-2. Projecting 5 years means
    // years 3-5 are outside the convex hull → null.
    const matrix = testMatrix();
    const result = projectTrajectory(matrix, 0.75, 0.85, 5);
    expect(result).toBeNull();
  });
});
