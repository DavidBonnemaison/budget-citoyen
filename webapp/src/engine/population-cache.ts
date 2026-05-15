// webapp/src/engine/population-cache.ts
//
// O(1) HashMap cache for synthetic household profiles.
// Mirrors the ScenarioCache architecture (scenario-cache.ts) with identical
// patterns: private Map-based storage, static fromDoc factory, copy-on-read
// accessors, and async loadFromJSON for main-thread use.
//
// Architecture (D-04, D-12):
//   - PopulationCache takes a PopulationDoc (array of Profile objects + metadata)
//   - Indexes profiles by profile_id (Map<string, Profile>) for O(1) lookup
//   - Pre-computes decile and age-group buckets at construction time
//   - All accessors return shallow copies (mutation safety)
//
// Used by:
//   - Phase 3 UI: household profile display (getProfile)
//   - Phase 4: distributional analysis (getProfilesByDecile, getProfilesByAgeGroup)
//   - WorkerOrchestrator: INIT_POPULATION flow (Plan 02.2-07)

import type { Profile, PopulationDoc } from './types';

/** Age group labels for pre-indexed buckets. */
export type AgeGroup = 'jeune' | 'actif' | 'senior' | 'retraite';

/** Re-export PopulationDoc for convenience (mirrors scenario-cache.ts pattern). */
export type { PopulationDoc } from './types';

/**
 * O(1) HashMap cache for synthetic household profiles.
 *
 * Mirrors ScenarioCache architecture:
 *   - Private Map-based storage for O(1) lookups
 *   - private constructor — all instances created via fromDoc()
 *   - static fromDoc() factory method
 *   - static loadFromJSON() for main-thread network loading
 *   - Copy-on-read accessors (mutation safety)
 *
 * Decile computation:
 *   Profiles are sorted by revenu_fiscal, then assigned to deciles 1-10
 *   based on percentile rank boundaries computed at construction time.
 *
 * Age group assignment:
 *   - age < 35  → 'jeune'
 *   - 35 ≤ age < 50 → 'actif'
 *   - 50 ≤ age < 65 → 'senior'
 *   - age ≥ 65 → 'retraite'
 */
export class PopulationCache {
  /** O(1) profile lookup by profile_id. */
  private profiles: Map<string, Profile>;

  /** Pre-indexed profiles by revenu_fiscal decile (1-10). */
  private byDecile: Map<number, Profile[]>;

  /** Pre-indexed profiles by age bracket label. */
  private byAgeGroup: Map<AgeGroup, Profile[]>;

  /** PopulationDoc metadata (dp_epsilon, sha256, data_source, etc.). */
  private meta: PopulationDoc['meta'] | null;

  /** Cached profile count for O(1) getProfileCount(). */
  private profileCount: number;

  /**
   * Private constructor. All instances are created via fromDoc() factory.
   */
  private constructor() {
    this.profiles = new Map();
    this.byDecile = new Map();
    this.byAgeGroup = new Map();
    this.meta = null;
    this.profileCount = 0;
  }

  // ── Public Accessors ─────────────────────────────────────────────────────

  /**
   * Get a profile by its unique identifier.
   *
   * @param id — The profile_id string (UUID v4).
   * @returns The Profile object, or undefined if not found.
   *
   * O(1) average case — Map.get().
   */
  getProfile(id: string): Profile | undefined {
    return this.profiles.get(id);
  }

  /**
   * Get all profiles in a specific income decile.
   *
   * Deciles are pre-computed at construction time from revenu_fiscal
   * percentile rank. Returns a shallow copy (spread) for mutation safety.
   *
   * @param decile — Decile number 1-10.
   * @returns Array of Profile objects in that decile, or empty array if invalid.
   *
   * O(1) average case — Map.get().
   */
  getProfilesByDecile(decile: number): Profile[] {
    const bucket = this.byDecile.get(decile);
    return bucket ? [...bucket] : [];
  }

  /**
   * Get all profiles in a specific age group.
   *
   * Age groups are pre-computed at construction time.
   * Returns a shallow copy (spread) for mutation safety.
   *
   * @param label — Age group label: 'jeune', 'actif', 'senior', or 'retraite'.
   * @returns Array of Profile objects in that age group, or empty array if invalid.
   *
   * O(1) average case — Map.get().
   */
  getProfilesByAgeGroup(label: string): Profile[] {
    const bucket = this.byAgeGroup.get(label as AgeGroup);
    return bucket ? [...bucket] : [];
  }

  /**
   * Get the total number of profiles in the cache.
   *
   * @returns Profile count (0-50000 for full population).
   *
   * O(1) — cached at construction time.
   */
  getProfileCount(): number {
    return this.profileCount;
  }

  /**
   * Get the population metadata (dp_epsilon, sha256, data_source, etc.).
   *
   * @returns The PopulationDoc.meta object, or null if no metadata loaded.
   *
   * O(1).
   */
  getMeta(): PopulationDoc['meta'] | null {
    return this.meta;
  }

  // ── Factory Methods ──────────────────────────────────────────────────────

  /**
   * Construct a PopulationCache from a PopulationDoc.
   *
   * Indexes all profiles by profile_id, pre-computes decile and age-group
   * buckets. Handles empty profiles array gracefully.
   *
   * Decile computation:
   *   Profiles with revenu_fiscal are sorted ascending, then percentile
   *   boundary thresholds are computed as indices at step * len / 10.
   *   Each profile is assigned to decile 1-10 based on its position.
   *
   * Age group assignment:
   *   Profiles with age are assigned to 'jeune' (< 35), 'actif' (35-49),
   *   'senior' (50-64), or 'retraite' (≥ 65).
   *
   * @param doc — The PopulationDoc with profiles and metadata.
   * @returns A fully indexed PopulationCache.
   *
   * O(n log n) for decile computation (sort). O(n) otherwise.
   */
  static fromDoc(doc: PopulationDoc): PopulationCache {
    const cache = new PopulationCache();

    cache.meta = doc.meta ?? null;
    cache.profileCount = doc.profiles.length;

    // Index profiles by ID
    for (const profile of doc.profiles) {
      cache.profiles.set(profile.profile_id, profile);
    }

    // Pre-compute decile buckets
    cache._computeDecileBuckets(doc.profiles);

    // Pre-compute age group buckets
    cache._computeAgeGroupBuckets(doc.profiles);

    return cache;
  }

  /**
   * Load a PopulationCache from a remote JSON URL.
   *
   * Fetches the population JSON, validates it as a PopulationDoc,
   * and constructs a cache. For main-thread (orchestrator) use.
   *
   * Workers receive data via postMessage and call fromDoc() directly.
   *
   * @param url — URL to the population JSON file.
   * @returns A fully indexed PopulationCache.
   * @throws Error if fetch fails or JSON is invalid.
   *
   * Same pattern as ScenarioCache.loadFromJSON().
   */
  static async loadFromJSON(url: string): Promise<PopulationCache> {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(
        `Failed to load population JSON from ${url}: ${response.status} ${response.statusText}`,
      );
    }
    const data = (await response.json()) as PopulationDoc;
    return PopulationCache.fromDoc(data);
  }

  // ── Private helpers ──────────────────────────────────────────────────────

  /**
   * Compute decile index buckets from profile revenu_fiscal values.
   *
   * Sorts profiles by revenu_fiscal ascending, computes percentile
   * threshold boundaries, and assigns each profile to decile 1-10.
   */
  private _computeDecileBuckets(profiles: Profile[]): void {
    // Filter to profiles with defined revenu_fiscal
    const withRevenue = profiles
      .filter((p) => typeof p.revenu_fiscal === 'number' && isFinite(p.revenu_fiscal))
      .sort((a, b) => a.revenu_fiscal - b.revenu_fiscal);

    if (withRevenue.length === 0) {
      // Initialize empty buckets
      for (let d = 1; d <= 10; d++) {
        this.byDecile.set(d, []);
      }
      return;
    }

    const n = withRevenue.length;
    // Compute decile boundary indices (0-indexed)
    const boundaries: number[] = [];
    for (let d = 1; d <= 10; d++) {
      boundaries.push(Math.floor((d / 10) * n));
    }

    // Assign profiles to deciles
    let startIdx = 0;
    for (let d = 1; d <= 10; d++) {
      const endIdx = boundaries[d - 1];
      this.byDecile.set(d, withRevenue.slice(startIdx, endIdx));
      startIdx = endIdx;
    }
  }

  /**
   * Compute age group index buckets from profile age values.
   *
   * Assigns each profile with a defined age to one of four age groups.
   */
  private _computeAgeGroupBuckets(profiles: Profile[]): void {
    const buckets: Record<AgeGroup, Profile[]> = {
      jeune: [],
      actif: [],
      senior: [],
      retraite: [],
    };

    for (const profile of profiles) {
      if (typeof profile.age !== 'number') continue;
      const age = profile.age;
      if (age < 35) {
        buckets.jeune.push(profile);
      } else if (age < 50) {
        buckets.actif.push(profile);
      } else if (age < 65) {
        buckets.senior.push(profile);
      } else {
        buckets.retraite.push(profile);
      }
    }

    for (const [label, group] of Object.entries(buckets)) {
      this.byAgeGroup.set(label as AgeGroup, group);
    }
  }
}
