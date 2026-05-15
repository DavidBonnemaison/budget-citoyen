// webapp/src/engine/__tests__/scenario-cache.test.ts
//
// Unit tests for the ScenarioCache class — O(1) HashMap lookups for
// pre-computed microsimulation results.

import { describe, it, expect, beforeEach } from 'vitest';
import { ScenarioCache, type ScenarioDoc } from '../scenario-cache';
import type { ScenarioDefinition, ScenarioResult } from '../types';

// ── Test Fixtures ───────────────────────────────────────────────────────────

function makeScenarioResult(
  ir: number,
  is: number,
  tva: number,
  cotisations: number,
  aides: number,
  revenuDisponible: number,
): ScenarioResult {
  return { ir, is, tva, cotisations, aides, revenuDisponible };
}

function makeDefinition(
  id: string,
  name: string,
  description: string,
): ScenarioDefinition {
  return { id, name, description, parameterOverrides: {} };
}

function makeDoc(
  definition: ScenarioDefinition,
  results: Record<number, ScenarioResult>,
): ScenarioDoc {
  return { definition, results };
}

// ── Tests ───────────────────────────────────────────────────────────────────

describe('ScenarioCache', () => {
  let cache: ScenarioCache;

  beforeEach(() => {
    cache = new ScenarioCache();
  });

  describe('lookup()', () => {
    it('returns undefined for an empty cache', () => {
      expect(cache.lookup('nonexistent', 0)).toBeUndefined();
    });

    it('returns undefined for a missing scenario ID', () => {
      const doc = makeDoc(makeDefinition('baseline', 'Baseline', 'Default'), {
        0: makeScenarioResult(1000, 200, 500, 300, 150, 22000),
      });
      cache = ScenarioCache.fromDocs([doc]);

      expect(cache.lookup('nonexistent', 0)).toBeUndefined();
    });

    it('returns undefined for a missing profile index', () => {
      const doc = makeDoc(makeDefinition('baseline', 'Baseline', 'Default'), {
        0: makeScenarioResult(1000, 200, 500, 300, 150, 22000),
      });
      cache = ScenarioCache.fromDocs([doc]);

      expect(cache.lookup('baseline', 999)).toBeUndefined();
    });

    it('returns the correct ScenarioResult for a valid lookup', () => {
      const expected = makeScenarioResult(1200, 250, 550, 320, 200, 23500);
      const doc = makeDoc(makeDefinition('reform-tva', 'TVA 22%', 'TVA reform'), {
        42: expected,
      });
      cache = ScenarioCache.fromDocs([doc]);

      const result = cache.lookup('reform-tva', 42);
      expect(result).toBeDefined();
      expect(result!.ir).toBe(expected.ir);
      expect(result!.is).toBe(expected.is);
      expect(result!.tva).toBe(expected.tva);
      expect(result!.cotisations).toBe(expected.cotisations);
      expect(result!.aides).toBe(expected.aides);
      expect(result!.revenuDisponible).toBe(expected.revenuDisponible);
    });

    it('returns the correct result for profile index 0', () => {
      const expected = makeScenarioResult(800, 150, 400, 250, 300, 18000);
      const doc = makeDoc(makeDefinition('baseline', 'Baseline', 'Default'), {
        0: expected,
      });
      cache = ScenarioCache.fromDocs([doc]);

      const result = cache.lookup('baseline', 0);
      expect(result).toBeDefined();
      expect(result!.ir).toBe(800);
    });

    it('returns the correct result for profile index 49999 (max)', () => {
      const expected = makeScenarioResult(5000, 800, 1200, 600, 0, 95000);
      const doc = makeDoc(makeDefinition('baseline', 'Baseline', 'Default'), {
        49999: expected,
      });
      cache = ScenarioCache.fromDocs([doc]);

      const result = cache.lookup('baseline', 49999);
      expect(result).toBeDefined();
      expect(result!.revenuDisponible).toBe(95000);
    });

    it('handles multiple scenarios correctly', () => {
      const r1 = makeScenarioResult(1000, 200, 500, 300, 150, 22000);
      const r2 = makeScenarioResult(1100, 220, 520, 310, 140, 21800);

      const doc1 = makeDoc(makeDefinition('baseline', 'Baseline', 'Base'), {
        0: r1,
      });
      const doc2 = makeDoc(
        makeDefinition('reform-ir', 'IR Reform', 'IR changes'),
        { 0: r2 },
      );

      cache = ScenarioCache.fromDocs([doc1, doc2]);

      const result1 = cache.lookup('baseline', 0);
      const result2 = cache.lookup('reform-ir', 0);

      expect(result1!.ir).toBe(1000);
      expect(result2!.ir).toBe(1100);
    });
  });

  describe('listScenarios()', () => {
    it('returns empty array for an empty cache', () => {
      expect(cache.listScenarios()).toEqual([]);
    });

    it('returns all scenario definitions', () => {
      const doc1 = makeDoc(makeDefinition('baseline', 'Baseline', 'Default'), {
        0: makeScenarioResult(1000, 200, 500, 300, 150, 22000),
      });
      const doc2 = makeDoc(
        makeDefinition('reform-tva', 'TVA Reform', 'Changes to TVA'),
        { 0: makeScenarioResult(1100, 220, 600, 320, 140, 21500) },
      );

      cache = ScenarioCache.fromDocs([doc1, doc2]);

      const scenarios = cache.listScenarios();
      expect(scenarios).toHaveLength(2);
      expect(scenarios[0].id).toBe('baseline');
      expect(scenarios[1].id).toBe('reform-tva');
    });

    it('returns a copy, not the internal array', () => {
      const doc = makeDoc(makeDefinition('baseline', 'Baseline', 'Default'), {
        0: makeScenarioResult(1000, 200, 500, 300, 150, 22000),
      });
      cache = ScenarioCache.fromDocs([doc]);

      const scenarios = cache.listScenarios();
      scenarios.push(makeDefinition('hacked', 'Hacked', 'Not real'));

      // Internal list should be unchanged
      expect(cache.listScenarios()).toHaveLength(1);
    });
  });

  describe('fromDocs()', () => {
    it('creates a cache from an array of scenario documents', () => {
      const doc = makeDoc(makeDefinition('baseline', 'Baseline', 'Default'), {
        0: makeScenarioResult(1000, 200, 500, 300, 150, 22000),
        1: makeScenarioResult(1200, 250, 550, 320, 100, 23000),
      });

      cache = ScenarioCache.fromDocs([doc]);

      expect(cache.lookup('baseline', 0)).toBeDefined();
      expect(cache.lookup('baseline', 1)).toBeDefined();
      expect(cache.lookup('baseline', 2)).toBeUndefined();
    });

    it('creates an empty cache from an empty array', () => {
      cache = ScenarioCache.fromDocs([]);
      expect(cache.listScenarios()).toHaveLength(0);
      expect(cache.lookup('anything', 0)).toBeUndefined();
    });
  });

  describe('lookup() performance', () => {
    it('completes a lookup in under 1ms on a realistic cache', () => {
      // Build a realistic cache: 14 scenarios × 32 profiles
      const scenarioCount = 14;
      const profileCount = 32;
      const docs: ScenarioDoc[] = [];

      for (let s = 0; s < scenarioCount; s++) {
        const results: Record<number, ScenarioResult> = {};
        for (let p = 0; p < profileCount; p++) {
          // Vary values per profile to avoid trivial hash collisions
          results[p] = makeScenarioResult(
            500 + p * 100,       // ir
            0.0,                  // is
            300 + (p % 10) * 50, // tva
            400 + (p % 5) * 80,  // cotisations
            200 + (s % 3) * 70,  // aides
            15000 + p * 500,     // revenuDisponible
          );
        }
        docs.push(
          makeDoc(
            makeDefinition(
              `scenario-${s}`,
              `Scenario ${s}`,
              `Description for scenario ${s} with enough length`,
            ),
            results,
          ),
        );
      }

      const cache = ScenarioCache.fromDocs(docs);

      // Warm up once (ensure JIT doesn't distort measurement of first call)
      cache.lookup('scenario-7', 15);

      // Measure: worst-case scenario (last scenario, highest profile index)
      const start = performance.now();
      const result = cache.lookup('scenario-13', 31);
      const elapsed = performance.now() - start;

      expect(result, 'lookup should return a result').toBeDefined();
      expect(
        elapsed,
        `lookup took ${elapsed.toFixed(3)}ms, expected < 1ms`,
      ).toBeLessThan(1);
    });
  });

  describe('addScenario()', () => {
    it('adds a new scenario incrementally', () => {
      const doc1 = makeDoc(makeDefinition('baseline', 'Baseline', 'Default'), {
        0: makeScenarioResult(1000, 200, 500, 300, 150, 22000),
      });
      const doc2 = makeDoc(
        makeDefinition('reform', 'Reform', 'Reform scenario'),
        { 0: makeScenarioResult(1100, 220, 520, 310, 140, 21800) },
      );

      cache.addScenario(doc1);
      expect(cache.listScenarios()).toHaveLength(1);

      cache.addScenario(doc2);
      expect(cache.listScenarios()).toHaveLength(2);
      expect(cache.lookup('reform', 0)).toBeDefined();
    });
  });
});
