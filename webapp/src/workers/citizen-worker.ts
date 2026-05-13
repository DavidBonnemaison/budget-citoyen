// webapp/src/workers/citizen-worker.ts
//
// PRIVACY GUARANTEE (D-12): This worker NEVER calls fetch() or XMLHttpRequest.
// All data arrives via postMessage from the main thread.
//
// Citizen microsimulation Web Worker — replaces the deleted micro-worker.ts
// (WASM-based) with pure TypeScript O(1) scenario cache lookups.
//
// Architecture: The orchestrator (main thread) fetches pre-computed scenario
// JSON, parses it, and transfers ScenarioDoc[] to this worker via postMessage.
// The worker constructs a ScenarioCache and handles SIMULATE requests with
// O(1) HashMap lookups — no computation, no WASM.
//
// Message protocol (D-11):
//   INIT     → construct ScenarioCache from scenarios JSON, respond READY
//   SIMULATE → lookup(scenarioId, profileIndex), respond CITIZEN_RESULT
//   ERROR    → caught exceptions respond with ERROR type

import { ScenarioCache, type ScenarioDoc } from '../engine/scenario-cache';
import type {
  WorkerRequest,
  WorkerResponse,
  SimulatePayload,
  CitizenInitPayload,
  ScenarioResult,
} from '../engine/types';

// ── Worker State ────────────────────────────────────────────────────────────

let cache: ScenarioCache | null = null;

// ── Message Handler ─────────────────────────────────────────────────────────

self.onmessage = (e: MessageEvent<WorkerRequest>) => {
  const { id, type, payload } = e.data;

  try {
    switch (type) {
      case 'INIT': {
        const initPayload = payload as CitizenInitPayload;
        const docs: ScenarioDoc[] = JSON.parse(initPayload.scenariosJson);
        cache = ScenarioCache.fromDocs(docs);
        const response: WorkerResponse = { id, type: 'READY', payload: null };
        self.postMessage(response);
        break;
      }

      case 'SIMULATE': {
        if (!cache) {
          const response: WorkerResponse = {
            id,
            type: 'ERROR',
            payload: 'Cache not initialized — send INIT first',
          };
          self.postMessage(response);
          return;
        }

        const simPayload = payload as SimulatePayload;
        const result = cache.lookup(
          simPayload.scenarioId,
          simPayload.profileIndex,
        );

        if (!result) {
          const response: WorkerResponse = {
            id,
            type: 'ERROR',
            payload: `Scenario '${simPayload.scenarioId}' or profile index ${simPayload.profileIndex} not found in cache`,
          };
          self.postMessage(response);
          return;
        }

        const response: WorkerResponse<ScenarioResult> = {
          id,
          type: 'CITIZEN_RESULT',
          payload: result,
        };
        self.postMessage(response);
        break;
      }

      default:
        self.postMessage({
          id,
          type: 'ERROR',
          payload: `Unknown message type: ${type}`,
        } satisfies WorkerResponse);
    }
  } catch (err) {
    const response: WorkerResponse = {
      id,
      type: 'ERROR',
      payload: err instanceof Error ? err.message : String(err),
    };
    self.postMessage(response);
  }
};
