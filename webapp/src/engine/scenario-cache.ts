// webapp/src/engine/scenario-cache.ts
//
// Pure TypeScript scenario cache for O(1) microsimulation result lookups.
// Replaces the deleted wasm-micro crate (Rust + WASM formula engine) with
// pre-computed JSON lookups in the hybrid architecture.
//
// Architecture (Plan 02-10 context):
//   - The orchestrator (main thread) fetches pre-computed scenario JSON
//     and transfers it to the citizen worker via postMessage.
//   - The citizen worker constructs a ScenarioCache from the JSON and
//     handles SIMULATE requests with O(1) HashMap lookups.
//   - D-12: The worker never calls fetch() — data arrives via postMessage.

import type { ScenarioDefinition, ScenarioResult } from './types';

/**
 * JSON structure of a pre-computed scenario document.
 *
 * Contains scenario metadata and results for all 50,000 synthetic profiles
 * under that scenario's parameter configuration.
 */
export interface ScenarioDoc {
  /** Scenario metadata. */
  definition: ScenarioDefinition;
  /** Pre-computed results indexed by profile index (0-49999) as string keys from JSON. */
  results: Record<string, ScenarioResult>;
}

/**
 * O(1) scenario cache for microsimulation lookups.
 *
 * Internal structure: Map<scenarioId, Map<profileIndex, ScenarioResult>>
 * - Outer key: scenario ID (e.g., "baseline-2025")
 * - Inner key: profile index (0-49999)
 * - Value: pre-computed ScenarioResult
 *
 * This replaces the WASM MicroEngine.update_and_simulate() with a simple
 * HashMap lookup — the computation was moved to the pre-compute pipeline
 * (Plan 02-11).
 */
export class ScenarioCache {
  /** Scenario definitions for listing available scenarios. */
  private definitions: ScenarioDefinition[] = [];

  /** O(1) lookup: scenarioId → profileIndex → ScenarioResult. */
  private cache = new Map<string, Map<number, ScenarioResult>>();

  /**
   * Looks up a pre-computed scenario result by scenario ID and profile index.
   *
   * O(1) average case (HashMap double lookup).
   *
   * @param scenarioId   - Scenario identifier (e.g., "baseline-2025")
   * @param profileIndex - Profile index in the synthetic population (0-49999)
   * @returns The pre-computed ScenarioResult, or undefined if not found
   */
  lookup(scenarioId: string, profileIndex: number): ScenarioResult | undefined {
    const scenarioMap = this.cache.get(scenarioId);
    if (!scenarioMap) {
      return undefined;
    }
    return scenarioMap.get(profileIndex);
  }

  /**
   * Returns the list of available scenario definitions.
   *
   * Used by the UI to populate scenario selectors.
   */
  listScenarios(): ScenarioDefinition[] {
    return [...this.definitions];
  }

  /**
   * Adds a scenario document to the cache.
   *
   * Typically called during worker initialization — the orchestrator
   * transfers scenario JSON, and the worker calls this method to populate
   * the cache. Results are stored as a nested Map for O(1) access.
   *
   * @param doc - A pre-computed scenario document
   */
  addScenario(doc: ScenarioDoc): void {
    this.definitions.push(doc.definition);

    const profileMap = new Map<number, ScenarioResult>();
    for (const [key, value] of Object.entries(doc.results)) {
      profileMap.set(Number(key), value);
    }
    this.cache.set(doc.definition.id, profileMap);
  }

  /**
   * Constructs a ScenarioCache from an array of scenario documents.
   *
   * This is the primary constructor used by the citizen worker:
   * the orchestrator fetches JSON on the main thread, parses it, and
   * transfers the parsed objects via postMessage. The worker then
   * calls this static method to build the cache.
   *
   * @param docs - Array of pre-computed scenario documents
   * @returns A fully populated ScenarioCache
   */
  static fromDocs(docs: ScenarioDoc[]): ScenarioCache {
    const cache = new ScenarioCache();
    for (const doc of docs) {
      cache.addScenario(doc);
    }
    return cache;
  }

  /**
   * Static factory: loads scenario cache from a JSON URL.
   *
   * **Intended for main-thread use only (orchestrator).**
   * The worker must NEVER call this method (D-12: no fetch() in workers).
   *
   * The orchestrator fetches the pre-computed scenario data, then transfers
   * the parsed ScenarioDoc[] to the worker via postMessage. The worker
   * constructs the cache using `ScenarioCache.fromDocs()`.
   *
   * @param url - URL to the pre-computed scenarios JSON file
   * @returns A fully populated ScenarioCache
   */
  static async loadFromJSON(url: string): Promise<ScenarioCache> {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(
        `Failed to load scenario data: ${response.status} ${response.statusText}`,
      );
    }
    const docs: ScenarioDoc[] = await response.json();
    return ScenarioCache.fromDocs(docs);
  }
}
