// webapp/src/state/__tests__/index-map.test.ts
//
// Unit tests for lever-to-parameter index mappings (D-08, D-12).
// Decision: validates structural integrity of all 5 citizen levers.

import { describe, it, expect } from 'vitest';
import { LEVER_MAPPINGS } from '../index-map';

// ── Structure ─────────────────────────────────────────────────────────────────

describe('LEVER_MAPPINGS structure', () => {
  it('has exactly 5 keys: ir, is, tva, cotisations, depenses', () => {
    const keys = Object.keys(LEVER_MAPPINGS);
    expect(keys).toHaveLength(5);
    expect(keys).toContain('ir');
    expect(keys).toContain('is');
    expect(keys).toContain('tva');
    expect(keys).toContain('cotisations');
    expect(keys).toContain('depenses');
  });

  it('each lever has a non-empty name string', () => {
    for (const key of Object.keys(LEVER_MAPPINGS)) {
      const mapping = LEVER_MAPPINGS[key];
      expect(typeof mapping.name).toBe('string');
      expect(mapping.name.length).toBeGreaterThan(0);
    }
  });

  it('each lever has rateFormat of "percent"', () => {
    for (const key of Object.keys(LEVER_MAPPINGS)) {
      expect(LEVER_MAPPINGS[key].rateFormat).toBe('percent');
    }
  });

  it('each lever has a non-negative baselineRate', () => {
    for (const key of Object.keys(LEVER_MAPPINGS)) {
      expect(LEVER_MAPPINGS[key].baselineRate).toBeGreaterThanOrEqual(0);
    }
  });
});

// ── Weights Integrity ─────────────────────────────────────────────────────────

describe('LEVER_MAPPINGS weights integrity', () => {
  it('each lever weights sum to 1.0', () => {
    for (const key of Object.keys(LEVER_MAPPINGS)) {
      const sum = LEVER_MAPPINGS[key].weights.reduce((a, b) => a + b, 0);
      expect(sum).toBeCloseTo(1.0, 10);
    }
  });

  it('each lever subParams length equals weights length', () => {
    for (const key of Object.keys(LEVER_MAPPINGS)) {
      const mapping = LEVER_MAPPINGS[key];
      expect(mapping.subParams.length).toBe(mapping.weights.length);
    }
  });

  it('all weights are positive', () => {
    for (const key of Object.keys(LEVER_MAPPINGS)) {
      for (const w of LEVER_MAPPINGS[key].weights) {
        expect(w).toBeGreaterThan(0);
      }
    }
  });
});

// ── Individual Lever Checks ───────────────────────────────────────────────────

describe('individual lever checks', () => {
  it('IR lever has 5 tranche sub-parameters', () => {
    const ir = LEVER_MAPPINGS['ir'];
    expect(ir.subParams).toHaveLength(5);
    expect(ir.subParams).toContain('ir.bareme.tranche1');
    expect(ir.subParams).toContain('ir.bareme.tranche5');
  });

  it('IS lever has exactly 1 sub-parameter with weight 1.0', () => {
    const is_ = LEVER_MAPPINGS['is'];
    expect(is_.subParams).toHaveLength(1);
    expect(is_.weights).toEqual([1.0]);
  });

  it('TVA lever has normal and reduced rate sub-parameters', () => {
    const tva = LEVER_MAPPINGS['tva'];
    expect(tva.subParams).toContain('tva.taux.normal');
    expect(tva.subParams).toContain('tva.taux.reduit');
    expect(tva.weights).toHaveLength(2);
  });
});
