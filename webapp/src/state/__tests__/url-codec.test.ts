// webapp/src/state/__tests__/url-codec.test.ts
//
// Unit tests for URLState encoding/decoding (D-23).
// Decision: vitest describe/it/expect conventions per PATTERNS.md.

import { describe, it, expect } from 'vitest';
import { encodeState, decodeState } from '../url-codec';
import type { URLState } from '../types';

// ── Test Fixtures ─────────────────────────────────────────────────────────────

function makeFullState(): URLState {
  return {
    s: 'baseline-2025',
    p: { ir: 2.5, is: -1.0, tva: 0.0, cotisations: 3.0, depenses: 1.5 },
    f: 1,
    a: false,
  };
}

function makeNullScenarioState(): URLState {
  return {
    s: null,
    p: { ir: 0.0, is: 0.0, tva: 0.0, cotisations: 0.0, depenses: 0.0 },
    f: 0,
    a: false,
  };
}

// ── encodeState ───────────────────────────────────────────────────────────────

describe('encodeState', () => {
  it('produces a valid base64 string', () => {
    const state = makeFullState();
    const encoded = encodeState(state);
    expect(typeof encoded).toBe('string');
    expect(encoded.length).toBeGreaterThan(0);
    // Verify it's valid base64 (only legal chars)
    expect(encoded).toMatch(/^[A-Za-z0-9+/]+=*$/);
  });

  it('encodes state with null scenarioId correctly', () => {
    const state = makeNullScenarioState();
    const encoded = encodeState(state);
    const decoded = decodeState(encoded);
    expect(decoded).not.toBeNull();
    expect(decoded!.s).toBeNull();
  });
});

// ── decodeState ───────────────────────────────────────────────────────────────

describe('decodeState', () => {
  it('returns null for an obviously invalid string', () => {
    const result = decodeState('!!!not-valid!!!');
    expect(result).toBeNull();
  });

  it('returns null for valid base64 that does not match URLState shape (missing f field)', () => {
    // Create a base64 of JSON without the required 'f' field
    const missingF = btoa(encodeURIComponent(JSON.stringify({ s: 'test', p: { ir: 0, is: 0, tva: 0, cotisations: 0, depenses: 0 }, a: false })));
    // base64 decode + JSON.parse will work, but type validation should reject
    const result = decodeState(missingF);
    expect(result).toBeNull();
  });

  it('decodes an empty string to null', () => {
    const result = decodeState('');
    expect(result).toBeNull();
  });
});

// ── Round-trip ────────────────────────────────────────────────────────────────

describe('round-trip encode → decode', () => {
  it('preserves a full state with all 5 sliders non-zero', () => {
    const original = makeFullState();
    const encoded = encodeState(original);
    const decoded = decodeState(encoded);
    expect(decoded).not.toBeNull();
    expect(decoded!.s).toBe(original.s);
    expect(decoded!.p.ir).toBe(original.p.ir);
    expect(decoded!.p.is).toBe(original.p.is);
    expect(decoded!.p.tva).toBe(original.p.tva);
    expect(decoded!.p.cotisations).toBe(original.p.cotisations);
    expect(decoded!.p.depenses).toBe(original.p.depenses);
    expect(decoded!.f).toBe(original.f);
    expect(decoded!.a).toBe(original.a);
  });

  it('handles scenarioId=null round-trip correctly', () => {
    const original = makeNullScenarioState();
    const encoded = encodeState(original);
    const decoded = decodeState(encoded);
    expect(decoded).not.toBeNull();
    expect(decoded!.s).toBeNull();
    expect(decoded!.f).toBe(0);
    expect(decoded!.a).toBe(false);
  });

  it('handles extreme slider values', () => {
    const original: URLState = {
      s: 'reform-extreme',
      p: { ir: 100.0, is: -50.0, tva: 20.0, cotisations: 0.001, depenses: 999.999 },
      f: 2,
      a: true,
    };
    const encoded = encodeState(original);
    const decoded = decodeState(encoded);
    expect(decoded).not.toBeNull();
    expect(decoded!.p.ir).toBeCloseTo(100.0, 10);
    expect(decoded!.p.depenses).toBeCloseTo(999.999, 10);
  });
});
