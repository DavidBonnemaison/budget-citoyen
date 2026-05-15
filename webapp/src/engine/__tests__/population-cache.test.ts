// webapp/src/engine/__tests__/population-cache.test.ts
//
// TDD tests for the PopulationCache class — O(1) HashMap lookup for
// synthetic household profiles. Replaces Wave 0 placeholder stub.
//
// RED phase: these tests will FAIL until population-cache.ts is implemented.

import { describe, it, expect, beforeEach } from 'vitest';
import { PopulationCache, type PopulationDoc } from '../population-cache';
import type { Profile } from '../types';

// ── Test Fixtures ───────────────────────────────────────────────────────────

function makeProfile(overrides: Partial<Profile> = {}): Profile {
  return {
    profile_id: 'p-001',
    age: 42,
    patrimoine: 150000,
    revenu_fiscal: 28000,
    situation_familiale: 'marie',
    nombre_parts: 2.5,
    type_activite: 'salarie',
    zone_residence: 'zone2',
    ...overrides,
  };
}

function makePopulationDoc(profiles: Profile[]): PopulationDoc {
  return {
    version: 'population-v2025.1',
    reference_year: 2025,
    profiles,
    meta: {
      dp_epsilon: 0.95,
      dp_data_source: 'INSEE ERFS 2025 via agregation et CopulaGAN',
      dp_proof_timestamp: '2025-05-15T10:00:00Z',
      sha256: 'abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
    },
  };
}

function makeFiftyKProfiles(): Profile[] {
  const profiles: Profile[] = [];
  for (let i = 0; i < 50000; i++) {
    profiles.push(makeProfile({
      profile_id: `p-${String(i).padStart(5, '0')}`,
      revenu_fiscal: 15000 + Math.random() * 85000,
      age: 18 + Math.floor(Math.random() * 82),
    }));
  }
  return profiles;
}

// ── Tests ───────────────────────────────────────────────────────────────────

describe('PopulationCache', () => {
  describe('empty cache', () => {
    it('getProfile returns undefined for empty cache', () => {
      const cache = PopulationCache.fromDoc(makePopulationDoc([]));
      expect(cache.getProfile('any-id')).toBeUndefined();
    });

    it('getProfileCount returns 0 for empty cache', () => {
      const cache = PopulationCache.fromDoc(makePopulationDoc([]));
      expect(cache.getProfileCount()).toBe(0);
    });

    it('getMeta returns metadata even for empty cache', () => {
      const cache = PopulationCache.fromDoc(makePopulationDoc([]));
      const meta = cache.getMeta();
      expect(meta).not.toBeNull();
      expect(meta!.dp_epsilon).toBe(0.95);
      expect(meta!.sha256).toBeDefined();
    });
  });

  describe('profile lookups', () => {
    let cache: PopulationCache;

    beforeEach(() => {
      const profiles = [
        makeProfile({ profile_id: 'p-001', revenu_fiscal: 28000, age: 42 }),
        makeProfile({ profile_id: 'p-002', revenu_fiscal: 45000, age: 28 }),
        makeProfile({ profile_id: 'p-003', revenu_fiscal: 18000, age: 67 }),
        makeProfile({ profile_id: 'p-004', revenu_fiscal: 62000, age: 55 }),
        makeProfile({ profile_id: 'p-005', revenu_fiscal: 95000, age: 31 }),
      ];
      cache = PopulationCache.fromDoc(makePopulationDoc(profiles));
    });

    it('getProfile returns correct Profile for valid id', () => {
      const profile = cache.getProfile('p-002');
      expect(profile).toBeDefined();
      expect(profile!.profile_id).toBe('p-002');
      expect(profile!.revenu_fiscal).toBe(45000);
      expect(profile!.age).toBe(28);
    });

    it('getProfile returns undefined for non-existent id', () => {
      expect(cache.getProfile('p-999')).toBeUndefined();
    });

    it('getProfileCount returns correct count', () => {
      expect(cache.getProfileCount()).toBe(5);
    });
  });

  describe('decile accessors', () => {
    let cache: PopulationCache;

    beforeEach(() => {
      const profiles: Profile[] = [];
      for (let i = 0; i < 200; i++) {
        profiles.push(makeProfile({
          profile_id: `p-${String(i).padStart(5, '0')}`,
          revenu_fiscal: 10000 + i * 500,
        }));
      }
      cache = PopulationCache.fromDoc(makePopulationDoc(profiles));
    });

    it('getProfilesByDecile returns non-empty array for valid decile', () => {
      const decile5 = cache.getProfilesByDecile(5);
      expect(decile5.length).toBeGreaterThan(0);
    });

    it('getProfilesByDecile returns empty array for out-of-range decile', () => {
      expect(cache.getProfilesByDecile(0).length).toBe(0);
      expect(cache.getProfilesByDecile(11).length).toBe(0);
      expect(cache.getProfilesByDecile(99).length).toBe(0);
    });

    it('getProfilesByDecile returns a copy (mutation safe)', () => {
      const original = cache.getProfilesByDecile(5);
      const originalLength = original.length;
      original.pop();
      const after = cache.getProfilesByDecile(5);
      expect(after.length).toBe(originalLength);
    });
  });

  describe('age group accessors', () => {
    let cache: PopulationCache;

    beforeEach(() => {
      const profiles = [
        makeProfile({ profile_id: 'p-jeune-1', age: 22, revenu_fiscal: 12000 }),
        makeProfile({ profile_id: 'p-jeune-2', age: 28, revenu_fiscal: 18000 }),
        makeProfile({ profile_id: 'p-actif-1', age: 42, revenu_fiscal: 35000 }),
        makeProfile({ profile_id: 'p-senior-1', age: 58, revenu_fiscal: 55000 }),
        makeProfile({ profile_id: 'p-retraite-1', age: 72, revenu_fiscal: 30000 }),
        makeProfile({ profile_id: 'p-retraite-2', age: 80, revenu_fiscal: 28000 }),
      ];
      cache = PopulationCache.fromDoc(makePopulationDoc(profiles));
    });

    it('getProfilesByAgeGroup returns jeunes (age < 35) correctly', () => {
      const jeunes = cache.getProfilesByAgeGroup('jeune');
      const ids = jeunes.map(p => p.profile_id);
      expect(ids).toContain('p-jeune-1');
      expect(ids).toContain('p-jeune-2');
      expect(ids).not.toContain('p-senior-1');
    });

    it('getProfilesByAgeGroup returns retraites (age >= 65) correctly', () => {
      const retraites = cache.getProfilesByAgeGroup('retraite');
      const ids = retraites.map(p => p.profile_id);
      expect(ids).toContain('p-retraite-1');
      expect(ids).toContain('p-retraite-2');
      for (const p of retraites) {
        expect(p.age).toBeGreaterThanOrEqual(65);
      }
    });

    it('getProfilesByAgeGroup returns empty array for invalid label', () => {
      expect(cache.getProfilesByAgeGroup('unknown').length).toBe(0);
    });

    it('getProfilesByAgeGroup returns a copy (mutation safe)', () => {
      const original = cache.getProfilesByAgeGroup('retraite');
      const originalLength = original.length;
      original.pop();
      const after = cache.getProfilesByAgeGroup('retraite');
      expect(after.length).toBe(originalLength);
    });
  });

  describe('metadata accessor', () => {
    it('getMeta returns full metadata', () => {
      const profiles = [makeProfile()];
      const cache = PopulationCache.fromDoc(makePopulationDoc(profiles));
      const meta = cache.getMeta();
      expect(meta).not.toBeNull();
      expect(meta!.dp_epsilon).toBe(0.95);
      expect(meta!.dp_data_source).toBeDefined();
      expect(meta!.sha256).toBeDefined();
      expect(meta!.dp_proof_timestamp).toBe('2025-05-15T10:00:00Z');
    });
  });

  describe('performance', () => {
    it('profile lookup completes in <1ms on 50K-profile cache', () => {
      const profiles = makeFiftyKProfiles();
      const cache = PopulationCache.fromDoc(makePopulationDoc(profiles));
      expect(cache.getProfileCount()).toBe(50000);

      const start = performance.now();
      const result = cache.getProfile('p-25000');
      const elapsed = performance.now() - start;
      expect(result).toBeDefined();
      expect(elapsed).toBeLessThan(1.0);
    }, 5000);
  });
});
