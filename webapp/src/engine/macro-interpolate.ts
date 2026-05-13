// webapp/src/engine/macro-interpolate.ts
//
// Pure TypeScript multi-linear interpolation engine for the macroeconomic
// shock matrix. Replaces the deleted wasm-macro crate (Rust + interpn 0.11.0)
// with zero WASM dependencies.
//
// D-12: This module performs CPU-bound computation only — no fetch(),
// no network access, no WASM imports.
//
// Algorithm: trilinear interpolation on a 4D grid (tax × spend × horizon × feature)
// with convex hull boundary enforcement. Out-of-bounds points return null
// (never silently extrapolate — PITFALLS.md Pitfall 2).

import type { MacroResult, ShockMatrixData } from './types';

// ── Constants ───────────────────────────────────────────────────────────────

/** Tolerance for convex hull boundary check (1e-10). */
const HULL_TOLERANCE = 1e-10;

/** Number of feature dimensions in the shock matrix grid. */
const NUM_FEATURES = 4;

// ── Private Helpers ─────────────────────────────────────────────────────────

/**
 * Binary search to find the lower index of the interval containing `x`
 * in the sorted breakpoints array.
 *
 * Returns the index `i` such that `bp[i] <= x <= bp[i+1]`.
 * For `x` exactly equal to `bp[bp.length-1]`, returns `bp.length-2`
 * (the last valid interval).
 *
 * Assumes `x` is within the breakpoint range (validated by hull check).
 */
function findInterval(bp: Float64Array, x: number): number {
  let lo = 0;
  let hi = bp.length - 1;
  while (lo < hi) {
    const mid = Math.floor((lo + hi + 1) / 2);
    if (bp[mid] <= x) lo = mid;
    else hi = mid - 1;
  }
  // lo is the largest index where bp[lo] <= x
  // Clamp to last valid interval for points exactly on the top breakpoint
  return lo >= bp.length - 1 ? bp.length - 2 : lo;
}

// ── Public API ──────────────────────────────────────────────────────────────

/**
 * Checks whether a point (tax, spend, horizon) lies inside the convex hull
 * defined by the hyperplane equations.
 *
 * Each hyperplane is stored as 4 consecutive Float64 values:
 * `[a1, a2, a3, b]` representing the inequality `a1*tax + a2*spend + a3*horizon + b ≤ 0`.
 *
 * The point is inside the hull only if ALL equations are satisfied within
 * the tolerance.
 *
 * @param tax       - Tax rate slider value
 * @param spend     - Spending level slider value
 * @param horizon   - Horizon year
 * @param equations - Flat Float64Array of hyperplane coefficients (stride 4)
 * @returns true if the point is inside or on the hull boundary
 */
export function isInsideHull(
  tax: number,
  spend: number,
  horizon: number,
  equations: Float64Array,
): boolean {
  for (let i = 0; i < equations.length; i += 4) {
    const a1 = equations[i];
    const a2 = equations[i + 1];
    const a3 = equations[i + 2];
    const b = equations[i + 3];
    const dot = a1 * tax + a2 * spend + a3 * horizon + b;
    if (dot > HULL_TOLERANCE) {
      return false;
    }
  }
  return true;
}

/**
 * Performs multi-linear (trilinear) interpolation on the shock matrix at a
 * single (tax, spend, horizon) point.
 *
 * Grid layout (row-major / C-order):
 * ```
 * index = ((taxIdx * nSpend + spendIdx) * nHorizon + horizonIdx) * NUM_FEATURES + featureIdx
 * ```
 * where feature order is: 0=gdp_growth, 1=employment, 2=deficit, 3=debt.
 *
 * Algorithm:
 * 1. Validate inputs (finite, positive, within horizon range)
 * 2. Gate against convex hull — return null if outside
 * 3. Binary search on breakpoints for surrounding grid cell
 * 4. Compute fractional weights for each dimension
 * 5. Extract 2³ = 8 corner grid values for each feature
 * 6. Trilinear blend: weighted average of 8 corners per feature
 *
 * @param matrix  - Pre-computed shock matrix with grid and hull equations
 * @param tax     - Tax rate slider value
 * @param spend   - Spending level slider value
 * @param horizon - Horizon year (1-5)
 * @returns MacroResult with single-element trajectory arrays, or null if out of bounds
 */
export function interpolateAtPoint(
  matrix: ShockMatrixData,
  tax: number,
  spend: number,
  horizon: number,
): MacroResult | null {
  // Input validation — defense-in-depth (threat T-02-30)
  if (!isFinite(tax) || !isFinite(spend) || !isFinite(horizon)) {
    return null;
  }
  if (tax <= 0 || spend <= 0) {
    return null;
  }
  if (horizon < 1 || horizon > 5) {
    return null;
  }

  // Convex hull gating
  if (!isInsideHull(tax, spend, horizon, matrix.hullEquations)) {
    return null;
  }

  // Binary search for surrounding grid cell indices
  const ti = findInterval(matrix.taxBp, tax);
  const si = findInterval(matrix.spendBp, spend);
  const hi = findInterval(matrix.horizonBp, horizon);

  // Fractional weights per dimension
  const fracT =
    (tax - matrix.taxBp[ti]) / (matrix.taxBp[ti + 1] - matrix.taxBp[ti]);
  const fracS =
    (spend - matrix.spendBp[si]) / (matrix.spendBp[si + 1] - matrix.spendBp[si]);
  const fracH =
    (horizon - matrix.horizonBp[hi]) /
    (matrix.horizonBp[hi + 1] - matrix.horizonBp[hi]);

  const wT0 = 1 - fracT;
  const wT1 = fracT;
  const wS0 = 1 - fracS;
  const wS1 = fracS;
  const wH0 = 1 - fracH;
  const wH1 = fracH;

  // Pre-compute grid strides
  const nSpend = matrix.spendBp.length;
  const nHorizon = matrix.horizonBp.length;
  const strideT = nSpend * nHorizon * NUM_FEATURES;
  const strideS = nHorizon * NUM_FEATURES;
  const strideH = NUM_FEATURES;

  // Base index for cell corner (ti, si, hi, 0)
  const baseIdx = ((ti * nSpend + si) * nHorizon + hi) * NUM_FEATURES;

  // Trilinear interpolation for each of 4 features
  const results: number[] = [];
  for (let f = 0; f < NUM_FEATURES; f++) {
    const c000 = matrix.grid[baseIdx + f];
    const c001 = matrix.grid[baseIdx + strideH + f];
    const c010 = matrix.grid[baseIdx + strideS + f];
    const c011 = matrix.grid[baseIdx + strideS + strideH + f];
    const c100 = matrix.grid[baseIdx + strideT + f];
    const c101 = matrix.grid[baseIdx + strideT + strideH + f];
    const c110 = matrix.grid[baseIdx + strideT + strideS + f];
    const c111 = matrix.grid[baseIdx + strideT + strideS + strideH + f];

    const val =
      wT0 * wS0 * wH0 * c000 +
      wT0 * wS0 * wH1 * c001 +
      wT0 * wS1 * wH0 * c010 +
      wT0 * wS1 * wH1 * c011 +
      wT1 * wS0 * wH0 * c100 +
      wT1 * wS0 * wH1 * c101 +
      wT1 * wS1 * wH0 * c110 +
      wT1 * wS1 * wH1 * c111;

    results.push(val);
  }

  // Feature order: results[0]=gdp_growth, results[1]=employment,
  //                 results[2]=deficit, results[3]=debt
  return {
    deficitTrajectory: [results[2]],
    debtTrajectory: [results[3]],
    gdpGrowthTrajectory: [results[0]],
    employmentTrajectory: [results[1]],
    isOutOfBounds: false,
    warningMessage: null,
  };
}

/**
 * Projects a macroeconomic trajectory over multiple years by interpolating
 * each year independently.
 *
 * For each year `y` from 1 to `years`, calls `interpolateAtPoint` with
 * `horizon = y`. Accumulates results into trajectory arrays.
 *
 * All-or-nothing semantics: if any year falls outside the convex hull,
 * the entire projection returns null.
 *
 * @param matrix - Pre-computed shock matrix
 * @param tax    - Tax rate slider value
 * @param spend  - Spending level slider value
 * @param years  - Number of years to project
 * @returns MacroResult with N-element trajectory arrays, or null
 */
export function projectTrajectory(
  matrix: ShockMatrixData,
  tax: number,
  spend: number,
  years: number,
): MacroResult | null {
  const deficits: number[] = [];
  const debts: number[] = [];
  const gdps: number[] = [];
  const employments: number[] = [];

  for (let y = 1; y <= years; y++) {
    const result = interpolateAtPoint(matrix, tax, spend, y);
    if (result === null) {
      return null;
    }
    deficits.push(result.deficitTrajectory[0]);
    debts.push(result.debtTrajectory[0]);
    gdps.push(result.gdpGrowthTrajectory[0]);
    employments.push(result.employmentTrajectory[0]);
  }

  return {
    deficitTrajectory: deficits,
    debtTrajectory: debts,
    gdpGrowthTrajectory: gdps,
    employmentTrajectory: employments,
    isOutOfBounds: false,
    warningMessage: null,
  };
}
