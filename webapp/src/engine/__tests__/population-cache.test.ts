// webapp/src/engine/__tests__/population-cache.test.ts
//
// Wave 0 placeholder tests for the PopulationCache class.
// TODO: Replace stubs with real TDD tests in Plan 02.2-05.

import { describe, it, expect } from 'vitest';
// TODO: import { PopulationCache } from '../population-cache';
// TODO: import type { Profile, PopulationDoc } from '../types';

describe('PopulationCache', () => {
  it('Wave 0 placeholder', () => {
    expect(true).toBe(true);
  });

  // TODO: Real tests to add in Plan 02.2-05:
  // - loads JSON via fromDoc() — constructs cache from PopulationDoc
  // - getProfile returns correct profile by profile_id
  // - getByDecile returns profiles grouped by income decile
  // - getByAgeGroup returns profiles grouped by age bracket
  // - getProfileCount returns 50000 for full population
  // - getMeta returns metadata (dp_epsilon, sha256, data_source)
});
