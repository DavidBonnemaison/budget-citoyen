// webapp/src/workers/orchestrator.ts
//
// WorkerOrchestrator — coordinates citizen and macro Web Workers, dispatches
// requests with correlation IDs, and discards stale responses from rapid
// slider interactions.
//
// D-11: Typed message protocol with correlation IDs.
//   - Each request carries a unique `crypto.randomUUID()` ID.
//   - Responses echo the request ID back.
//   - If a newer request supersedes a pending one, stale responses are discarded.
//
// D-12: Workers never touch the network — all data arrives via postMessage
//   with Transferable ArrayBuffers (zero-copy).
//
// Updated for Plan 02-10: Hybrid architecture with pure TypeScript engines.
//   - citizen-worker.ts replaces micro-worker.ts (scenario cache lookups)
//   - macro-worker.ts handles INTERPOLATE/PROJECT with TS trilinear interpolation
//   - Zero WASM imports in any worker

import type {
  WorkerRequest,
  WorkerResponse,
  MacroResult,
  ScenarioResult,
  MacroWorkerResult,
} from '../engine/types';

// ── Pending Request Tracking ───────────────────────────────────────────

interface PendingEntry {
  resolve: (value: unknown) => void;
  reject: (reason: unknown) => void;
  timestamp: number;
}

// ── WorkerOrchestrator ─────────────────────────────────────────────────

export class WorkerOrchestrator {
  private citizenWorker: Worker;
  private macroWorker: Worker;
  private pending = new Map<string, PendingEntry>();
  private latestCitizenId: string | null = null;
  private latestMacroId: string | null = null;
  private citizenReady = false;
  private macroReady = false;

  constructor() {
    this.citizenWorker = new Worker(
      new URL('./citizen-worker.ts', import.meta.url),
      { type: 'module' },
    );
    this.macroWorker = new Worker(
      new URL('./macro-worker.ts', import.meta.url),
      { type: 'module' },
    );

    this.citizenWorker.onmessage = (e: MessageEvent<WorkerResponse>) =>
      this.handleResponse(e.data, 'citizen');
    this.macroWorker.onmessage = (e: MessageEvent<WorkerResponse>) =>
      this.handleResponse(e.data, 'macro');
  }

  // ── Response Handler (D-11 — stale response discarding) ────────────

  private handleResponse(
    response: WorkerResponse,
    source: 'citizen' | 'macro',
  ): void {
    const latest =
      source === 'citizen' ? this.latestCitizenId : this.latestMacroId;

    // D-11: Discard stale responses when a newer request superseded them.
    // This handles rapid slider dragging (60 req/s) — only the latest
    // response matters for the UI update.
    if (latest !== null && response.id !== latest) {
      if (import.meta.env.DEV) {
        console.debug(`Discarding stale ${source} response: ${response.id}`);
      }
      return;
    }

    // Track READY state for init coordination
    if (response.type === 'READY') {
      if (source === 'citizen') this.citizenReady = true;
      else this.macroReady = true;
    }

    const pending = this.pending.get(response.id);
    if (pending) {
      if (response.type === 'ERROR') {
        pending.reject(new Error(String(response.payload)));
      } else {
        pending.resolve(response.payload);
      }
      this.pending.delete(response.id);
    }
  }

  // ── Public API ──────────────────────────────────────────────────────

  /**
   * Initialize both workers with their respective data payloads.
   *
   * D-12: The main thread fetches all static assets (scenario JSON,
   * shock matrix binary) during initial load and transfers them to
   * workers via postMessage — workers never touch the network.
   *
   * @param scenariosJson - Pre-computed scenario results as JSON string
   * @param matrixBytes   - Shock matrix as binary (ArrayBuffer), transferred zero-copy
   */
  async init(
    scenariosJson: string,
    matrixBytes: ArrayBuffer,
  ): Promise<void> {
    const citizenId = crypto.randomUUID();
    const macroId = crypto.randomUUID();

    this.latestCitizenId = citizenId;
    this.latestMacroId = macroId;

    const citizenInit = new Promise<void>((resolve, reject) => {
      this.pending.set(citizenId, {
        resolve: () => resolve(),
        reject,
        timestamp: Date.now(),
      });
      this.citizenWorker.postMessage({
        id: citizenId,
        type: 'INIT',
        payload: { scenariosJson },
      } satisfies WorkerRequest);
    });

    const macroInit = new Promise<void>((resolve, reject) => {
      this.pending.set(macroId, {
        resolve: () => resolve(),
        reject,
        timestamp: Date.now(),
      });
      // Transfer the ArrayBuffer for zero-copy (D-12)
      this.macroWorker.postMessage(
        {
          id: macroId,
          type: 'INIT',
          payload: { matrixBytes },
        } satisfies WorkerRequest,
        [matrixBytes],
      );
    });

    await Promise.all([citizenInit, macroInit]);
  }

  /**
   * Send a SIMULATE request to the citizen worker.
   *
   * Looks up a pre-computed scenario result by scenario ID and profile index.
   * O(1) HashMap lookup — no computation performed in the worker.
   *
   * @param scenarioId   - Pre-computed scenario identifier
   * @param profileIndex - Profile index in the synthetic population (0-49999)
   */
  async simulate(
    scenarioId: string,
    profileIndex: number,
  ): Promise<ScenarioResult> {
    const id = crypto.randomUUID();
    this.latestCitizenId = id;

    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject, timestamp: Date.now() });
      this.citizenWorker.postMessage({
        id,
        type: 'SIMULATE',
        payload: { scenarioId, profileIndex },
      } satisfies WorkerRequest);
    });
  }

  /**
   * Send an INTERPOLATE request to the macro worker (single-point).
   *
   * Performs trilinear interpolation over the shock matrix at
   * a single (tax, spend, horizon) point. Returns null if the
   * point is outside the convex hull.
   */
  async interpolate(
    tax: number,
    spend: number,
    horizon: number,
  ): Promise<MacroWorkerResult> {
    const id = crypto.randomUUID();
    this.latestMacroId = id;

    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject, timestamp: Date.now() });
      this.macroWorker.postMessage({
        id,
        type: 'INTERPOLATE',
        payload: { tax, spend, horizon, subType: 'interpolate' },
      } satisfies WorkerRequest);
    });
  }

  /**
   * Send a PROJECT request to the macro worker (multi-year).
   *
   * Projects a macroeconomic trajectory over multiple years by
   * interpolating each year independently. Returns null if any
   * year falls outside the convex hull (all-or-nothing).
   */
  async project(
    tax: number,
    spend: number,
    years: number,
  ): Promise<MacroWorkerResult> {
    const id = crypto.randomUUID();
    this.latestMacroId = id;

    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject, timestamp: Date.now() });
      this.macroWorker.postMessage({
        id,
        type: 'PROJECT',
        payload: {
          tax,
          spend,
          years,
        },
      } satisfies WorkerRequest);
    });
  }

  /**
   * Terminate both workers and clean up pending requests.
   * Call when the simulation page is unmounted.
   */
  terminate(): void {
    this.citizenWorker.terminate();
    this.macroWorker.terminate();
    this.pending.forEach((entry) => {
      entry.reject(new Error('Orchestrator terminated'));
    });
    this.pending.clear();
  }
}
