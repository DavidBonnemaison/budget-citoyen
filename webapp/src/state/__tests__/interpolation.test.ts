// webapp/src/state/__tests__/interpolation.test.ts
//
// Unit tests for scenario-to-scenario interpolation (D-01, D-02).
// Decision: requires a helper ScenarioCache builder for synthetic test scenarios.

import { describe, it, expect } from 'vitest';
import { interpolateScenarios, DEFAULT_K, EXACT_MATCH_THRESHOLD } from '../interpolation';
import type { SliderState } from '../types';
import type { ScenarioDefinition, ScenarioResult } from '../../engine/types';
import { ScenarioCache } from '../../engine/scenario-cache';

// ── Test Helpers ──────────────────────────────────────────────────────────────

function makeResult(ir: number, is: number, tva: number, cotisations: number, aides: number, revenuDisponible: number): ScenarioResult {
  return { ir, is, tva, cotisations, aides, revenuDisponible };
}

function makeDef(id: string, overrides: Record<string, number>): ScenarioDefinition {
  return {
    id,
    name: `Scenario ${id}`,
    description: `Test scenario ${id}`,
    parameterOverrides: overrides,
  };
}

/**
 * Builds a ScenarioCache with synthetic scenarios.
 * Each scenario has pre-computed results for profile index 0.
 *
 * Scenario layout (5-dimensional parameter space):
 *   baseline: all 0
 *   reformA:  ir=10, others 0
 *   reformB:  is=10, others 0
 *   reformC:  ir=5, is=5, others 0
 */
function makeTestCache(): ScenarioCache {
  const cache = new ScenarioCache();

  cache.addScenario({
    definition: makeDef('baseline', { ir: 0, is: 0, tva: 0, cotisations: 0, depenses: 0 }),
    results: { '0': makeResult(1000, 500, 200, 300, 100, 25000) },
  });

  cache.addScenario({
    definition: makeDef('reformA', { ir: 10, is: 0, tva: 0, cotisations: 0, depenses: 0 }),
    results: { '0': makeResult(800, 500, 200, 300, 100, 25200) },
  });

  cache.addScenario({
    definition: makeDef('reformB', { ir: 0, is: 10, tva: 0, cotisations: 0, depenses: 0 }),
    results: { '0': makeResult(1000, 400, 200, 300, 100, 25400) },
  });

  cache.addScenario({
    definition: makeDef('reformC', { ir: 5, is: 5, tva: 0, cotisations: 0, depenses: 0 }),
    results: { '0': makeResult(900, 450, 200, 300, 100, 25300) },
  });

  return cache;
}

// ── Exact Match ───────────────────────────────────────────────────────────────

describe('interpolateScenarios — exact match', () => {
  it('returns exact match when slider positions exactly match a scenario', () => {
    const cache = makeTestCache();
    const sliderParams: SliderState = { ir: 10, is: 0, tva: 0, cotisations: 0, depenses: 0 };
    const defs = cache.listScenarios();

    const result = interpolateScenarios(sliderParams, defs, cache, 0);

    expect(result).not.toBeNull();
    expect(result!.isExact).toBe(true);
    expect(result!.sourceScenarios).toEqual(['reformA']);
    expect(result!.weights).toEqual([1.0]);
    expect(result!.scenarioResult.ir).toBe(800);
  });

  it('isExact is true for exact match, false for blended result', () => {
    const cache = makeTestCache();
    const defs = cache.listScenarios();

    const exactResult = interpolateScenarios(
      { ir: 0, is: 0, tva: 0, cotisations: 0, depenses: 0 },
      defs, cache, 0,
    );
    expect(exactResult!.isExact).toBe(true);

    const blendedResult = interpolateScenarios(
      { ir: 7, is: 3, tva: 0, cotisations: 0, depenses: 0 },
      defs, cache, 0,
    );
    expect(blendedResult!.isExact).toBe(false);
  });
});

// ── Weighted Blend ────────────────────────────────────────────────────────────

describe('interpolateScenarios — weighted blend', () => {
  it('weights sum to 1.0 for between-scenario positions', () => {
    const cache = makeTestCache();
    const sliderParams: SliderState = { ir: 3, is: 7, tva: 0, cotisations: 0, depenses: 0 };
    const defs = cache.listScenarios();

    const result = interpolateScenarios(sliderParams, defs, cache, 0);

    expect(result).not.toBeNull();
    const sum = result!.weights.reduce((a, b) => a + b, 0);
    expect(sum).toBeCloseTo(1.0, 10);
  });

  it('closer scenario gets higher weight than farther scenario', () => {
    const cache = makeTestCache();
    // Position closer to reformC (ir=5,is=5) than to baseline (ir=0,is=0)
    const sliderParams: SliderState = { ir: 4, is: 4, tva: 0, cotisations: 0, depenses: 0 };
    const defs = cache.listScenarios();

    const result = interpolateScenarios(sliderParams, defs, cache, 0);

    expect(result).not.toBeNull();
    // reformC weight should be > baseline weight
    const idxC = result!.sourceScenarios.indexOf('reformC');
    const idxBase = result!.sourceScenarios.indexOf('baseline');
    expect(idxC).not.toBe(-1);
    expect(idxBase).not.toBe(-1);
    expect(result!.weights[idxC]).toBeGreaterThan(result!.weights[idxBase]);
  });

  it('all ScenarioResult fields are blended correctly', () => {
    const cache = makeTestCache();
    // Midpoint between baseline and reformA should give average
    const sliderParams: SliderState = { ir: 5, is: 0, tva: 0, cotisations: 0, depenses: 0 };
    const defs = cache.listScenarios();

    const result = interpolateScenarios(sliderParams, defs, cache, 0);

    expect(result).not.toBeNull();
    // baseline ir=1000, reformA ir=800 — midpoint should be ~900
    expect(result!.scenarioResult.ir).toBeCloseTo(900, -1);
  });
});

// ── k=1 ──────────────────────────────────────────────────────────────────────

describe('interpolateScenarios — k=1', () => {
  it('returns the single nearest scenario without blending', () => {
    const cache = makeTestCache();
    const sliderParams: SliderState = { ir: 7, is: 3, tva: 0, cotisations: 0, depenses: 0 };
    const defs = cache.listScenarios();

    const result = interpolateScenarios(sliderParams, defs, cache, 0, 1);

    expect(result).not.toBeNull();
    expect(result!.sourceScenarios.length).toBe(1);
    expect(result!.weights).toEqual([1.0]);
  });
});

// ── Edge Cases ────────────────────────────────────────────────────────────────

describe('interpolateScenarios — edge cases', () => {
  it('returns null for empty scenario list', () => {
    const cache = new ScenarioCache();
    const sliderParams: SliderState = { ir: 0, is: 0, tva: 0, cotisations: 0, depenses: 0 };

    const result = interpolateScenarios(sliderParams, [], cache, 0);
    expect(result).toBeNull();
  });

  it('returns null for negative profileIndex', () => {
    const cache = makeTestCache();
    const sliderParams: SliderState = { ir: 0, is: 0, tva: 0, cotisations: 0, depenses: 0 };
    const defs = cache.listScenarios();

    const result = interpolateScenarios(sliderParams, defs, cache, -1);
    expect(result).toBeNull();
  });

  it('returns null when k < 1', () => {
    const cache = makeTestCache();
    const sliderParams: SliderState = { ir: 0, is: 0, tva: 0, cotisations: 0, depenses: 0 };
    const defs = cache.listScenarios();

    const result = interpolateScenarios(sliderParams, defs, cache, 0, 0);
    expect(result).toBeNull();
  });
});
