// webapp/src/state/interpolation.ts
//
// Inverse-distance-weighted scenario interpolation (D-01, D-02).
// Decision: IDW algorithm with exact-match shortcut for slider positions matching a precomputed scenario.
// Pattern 3 from RESEARCH.md: compute Euclidean distances → sort → top-k → inverse-distance weights → blend.

import type { SliderState, InterpolationResult } from './types';
import type { ScenarioDefinition, ScenarioResult } from '../engine/types';
import type { ScenarioCache } from '../engine/scenario-cache';

// ── Constants ─────────────────────────────────────────────────────────────────

export const DEFAULT_K = 3;
export const EXACT_MATCH_THRESHOLD = 1e-3;

// ── Distance Computation ──────────────────────────────────────────────────────

/**
 * Computes squared Euclidean distance between slider positions and a scenario's
 * parameter overrides across all 5 dimensions. Dimensions absent from parameterOverrides
 * are treated as 0.0.
 */
function squaredDistance(slider: SliderState, def: ScenarioDefinition): number {
  const fields: (keyof SliderState)[] = ['ir', 'is', 'tva', 'cotisations', 'depenses'];
  let sum = 0;
  for (const field of fields) {
    const sliderVal = slider[field];
    const scenarioVal = def.parameterOverrides[field] ?? 0;
    const diff = sliderVal - scenarioVal;
    sum += diff * diff;
  }
  return sum;
}

// ── Field Blend ───────────────────────────────────────────────────────────────

function blendResults(results: ScenarioResult[], weights: number[]): ScenarioResult {
  const fields: (keyof ScenarioResult)[] = ['ir', 'is', 'tva', 'cotisations', 'aides', 'revenuDisponible'];
  const blended: Partial<ScenarioResult> = {};
  for (const field of fields) {
    let sum = 0;
    for (let i = 0; i < results.length; i++) {
      sum += results[i][field] * weights[i];
    }
    blended[field] = sum;
  }
  return blended as ScenarioResult;
}

// ── Interpolation ─────────────────────────────────────────────────────────────

export function interpolateScenarios(
  sliderParams: SliderState,
  scenarioDefs: ScenarioDefinition[],
  scenarioCache: ScenarioCache,
  profileIndex: number,
  k: number = DEFAULT_K,
): InterpolationResult | null {
  // Guards
  if (scenarioDefs.length === 0) return null;
  if (profileIndex < 0) return null;
  if (k < 1) return null;

  // Compute distances and sort
  const distances = scenarioDefs.map((def, idx) => ({
    idx,
    def,
    dist: squaredDistance(sliderParams, def),
  }));
  distances.sort((a, b) => a.dist - b.dist);

  // Take top-k
  const topK = distances.slice(0, Math.min(k, distances.length));

  // Exact match check
  if (topK[0].dist < EXACT_MATCH_THRESHOLD) {
    const result = scenarioCache.lookup(topK[0].def.id, profileIndex);
    if (!result) return null;
    return {
      scenarioResult: result,
      sourceScenarios: [topK[0].def.id],
      weights: [1.0],
      isExact: true,
    };
  }

  // Inverse distance weighting
  const invDist = topK.map((item) => {
    // Avoid division by zero for very close but not exact matches
    const d = item.dist < 1e-12 ? 1e-12 : item.dist;
    return 1 / d;
  });
  const totalInv = invDist.reduce((a, b) => a + b, 0);
  const weights = invDist.map((w) => w / totalInv);

  // Lookup results and blend
  const ids: string[] = [];
  const results: ScenarioResult[] = [];
  for (const item of topK) {
    const result = scenarioCache.lookup(item.def.id, profileIndex);
    if (!result) return null;
    ids.push(item.def.id);
    results.push(result);
  }

  const blended = blendResults(results, weights);

  return {
    scenarioResult: blended,
    sourceScenarios: ids,
    weights,
    isExact: false,
  };
}
