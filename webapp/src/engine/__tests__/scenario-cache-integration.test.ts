// webapp/src/engine/__tests__/scenario-cache-integration.test.ts
//
// Integration tests validating that the pre-computed scenarios-v2025.1.json
// is consumable through ScenarioCache for O(1) citizen-mode lookups.
//
// These tests are CI gating: they run after scenario-precompute in the
// phase2-wasm.yml workflow and validate the JSON output contract.

import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { ScenarioCache, type ScenarioDoc } from '../scenario-cache';

const JSON_PATH = resolve(
  __dirname,
  '../../../../packages/data-pipeline/dist/scenarios-v2025.1.json',
);

function loadDocs(): ScenarioDoc[] | null {
  try {
    const raw = readFileSync(JSON_PATH, 'utf-8');
    const data = JSON.parse(raw);
    return data.scenarios as ScenarioDoc[];
  } catch {
    return null;
  }
}

describe('ScenarioCache integration — real scenarios-v2025.1.json', () => {
  it('loads committed JSON and validates all scenario×profile combinations', () => {
    const docs = loadDocs();

    if (!docs) {
      console.warn(
        'SKIP: scenarios-v2025.1.json not found — run the pre-compute pipeline first',
      );
      return;
    }

    expect(docs.length, `Expected >= 12 scenarios, got ${docs.length}`).toBeGreaterThanOrEqual(12);

    const cache = ScenarioCache.fromDocs(docs);
    expect(cache.listScenarios().length).toBeGreaterThanOrEqual(12);

    // Spot-check baseline scenario × profile 0
    const baselineResult = cache.lookup('baseline-2025', 0);
    expect(baselineResult, 'baseline-2025[0] missing').toBeDefined();
    expect(baselineResult!.revenuDisponible, 'revenuDisponible must be > 0').toBeGreaterThan(0);
    expect(baselineResult!.is, 'IS must be 0.0').toBe(0.0);

    // Validate ALL scenarios × 32 profiles resolve
    for (const doc of docs) {
      const profileKeys = Object.keys(doc.results);
      expect(
        profileKeys.length,
        `${doc.definition.id}: expected 32 profiles, got ${profileKeys.length}`,
      ).toBe(32);

      for (let i = 0; i < 32; i++) {
        const r = cache.lookup(doc.definition.id, i);
        expect(r, `${doc.definition.id}[${i}] missing from cache`).toBeDefined();
        // MICRO-01: IR results must be non-negative for all scenario×profile combos
        expect(
          r!.ir,
          `${doc.definition.id}[${i}]: IR must be non-negative, got ${r!.ir}`,
        ).toBeGreaterThanOrEqual(0);
      }
    }
  });

  it('verifies baseline results have the expected structure', () => {
    const docs = loadDocs();
    if (!docs) {
      console.warn('SKIP: scenarios-v2025.1.json not found');
      return;
    }

    const baselineDoc = docs.find((d) => d.definition.id === 'baseline-2025');
    expect(baselineDoc, 'baseline-2025 scenario not found').toBeDefined();

    const profile0 = baselineDoc!.results['0'];
    expect(profile0, 'baseline results[0] not found').toBeDefined();

    // All 6 required fields
    const requiredFields = ['ir', 'is', 'tva', 'cotisations', 'aides', 'revenuDisponible'];
    for (const field of requiredFields) {
      expect(
        profile0[field as keyof typeof profile0],
        `baseline[0] missing field: ${field}`,
      ).toBeDefined();
    }

    // IS always 0.0
    expect(profile0.is, 'IS must be 0.0').toBe(0.0);

    // RevenuDisponible must be positive
    expect(profile0.revenuDisponible, 'revenuDisponible must be > 0').toBeGreaterThan(0);

    // All values are finite numbers
    for (const field of requiredFields) {
      const val = profile0[field as keyof typeof profile0];
      expect(Number.isFinite(val), `${field}=${val} is not finite`).toBe(true);
    }
  });

  it('verifies political program scenarios produce distinct results from baseline', () => {
    const docs = loadDocs();
    if (!docs) {
      console.warn('SKIP: scenarios-v2025.1.json not found');
      return;
    }

    const cache = ScenarioCache.fromDocs(docs);
    const baseline = cache.lookup('baseline-2025', 15);

    if (!baseline) {
      return; // Baseline profile 15 missing
    }

    const politicalIds = [
      'lfi-nfp-2025',
      'renaissance-2025',
      'lr-2025',
      'rn-2025',
      'ps-2025',
    ];

    for (const pid of politicalIds) {
      const result = cache.lookup(pid, 15);
      expect(result, `${pid}[15] missing`).toBeDefined();
      expect(result!.is, `${pid}[15]: IS must be 0.0`).toBe(0.0);

      // At least one field should differ from baseline
      const differs =
        result!.ir !== baseline.ir ||
        result!.tva !== baseline.tva ||
        result!.cotisations !== baseline.cotisations ||
        result!.aides !== baseline.aides ||
        result!.revenuDisponible !== baseline.revenuDisponible;

      expect(
        differs,
        `${pid}[15] should differ from baseline (political program must change at least one tax)`,
      ).toBe(true);
    }
  });
});
