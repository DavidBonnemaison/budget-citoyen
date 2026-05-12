// webapp/src/workers/orchestrator.ts
//
// WorkerOrchestrator — coordinates micro and macro Web Workers, dispatches
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

// ── Message Protocol Types (D-11) ──────────────────────────────────────

export interface WorkerRequest {
  id: string; // crypto.randomUUID() — correlation ID
  type: 'INIT' | 'SIMULATE' | 'INTERPOLATE';
  payload: unknown;
}

export interface WorkerResponse<T = unknown> {
  id: string; // Echoes the request ID
  type: 'READY' | 'MICRO_RESULT' | 'MACRO_RESULT' | 'ERROR';
  payload: T | null;
}

export interface SimulatePayload {
  params: number[];
  profileIndex: number;
}

export interface InitPayload {
  paramsJson: string;
  populationJson: string;
}

export interface MacroInitPayload {
  matrixBytes: ArrayBuffer;
}

export interface InterpolatePayload {
  tax: number;
  spend: number;
  horizon: number;
  subType?: 'interpolate';
}

export interface ProjectPayload {
  tax: number;
  spend: number;
  years: number;
  subType: 'project';
}

// ── Result Types (D-10 — serialized by serde-wasm-bindgen) ────────────

export interface MicroResult {
  ir: number;
  is: number;
  tva: number;
  cotisations_salariales: number;
  cotisations_patronales: number;
  csg: number;
  crds: number;
  revenu_disponible: number;
  revenu_imposable: number;
}

export interface MacroResult {
  deficit: number[];
  dette: number[];
  pib: number[];
  emploi: number[];
  deficit_ratio: number[];
  dette_ratio: number[];
}

// ── Pending Request Tracking ───────────────────────────────────────────

interface PendingEntry {
  resolve: (value: unknown) => void;
  reject: (reason: unknown) => void;
  timestamp: number;
}

// ── WorkerOrchestrator ─────────────────────────────────────────────────

export class WorkerOrchestrator {
  private microWorker: Worker;
  private macroWorker: Worker;
  private pending = new Map<string, PendingEntry>();
  private latestMicroId: string | null = null;
  private latestMacroId: string | null = null;
  private microReady = false;
  private macroReady = false;

  constructor() {
    this.microWorker = new Worker(
      new URL('./micro-worker.ts', import.meta.url),
      { type: 'module' },
    );
    this.macroWorker = new Worker(
      new URL('./macro-worker.ts', import.meta.url),
      { type: 'module' },
    );

    this.microWorker.onmessage = (e: MessageEvent<WorkerResponse>) =>
      this.handleResponse(e.data, 'micro');
    this.macroWorker.onmessage = (e: MessageEvent<WorkerResponse>) =>
      this.handleResponse(e.data, 'macro');
  }

  // ── Response Handler (D-11 — stale response discarding) ────────────

  private handleResponse(
    response: WorkerResponse,
    source: 'micro' | 'macro',
  ): void {
    const latest =
      source === 'micro' ? this.latestMicroId : this.latestMacroId;

    // D-11: Discard stale responses when a newer request superseded them.
    // This handles rapid slider dragging (60 req/s) — only the latest
    // response matters for the UI update.
    if (latest !== null && response.id !== latest) {
      console.debug(`Discarding stale ${source} response: ${response.id}`);
      return;
    }

    // Track READY state for init coordination
    if (response.type === 'READY') {
      if (source === 'micro') this.microReady = true;
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
   * D-12: The main thread fetches all static assets (tax rules JSON,
   * population JSON, shock matrix binary) during initial load and
   * transfers them to workers via postMessage — workers never touch
   * the network.
   *
   * @param paramsJson  - Tax rules as JSON string (parameters-v2025.1.json)
   * @param populationJson - Synthetic population as JSON string
   * @param matrixBytes - Shock matrix as postcard-encoded binary (ArrayBuffer)
   */
  async init(
    paramsJson: string,
    populationJson: string,
    matrixBytes: ArrayBuffer,
  ): Promise<void> {
    const microId = crypto.randomUUID();
    const macroId = crypto.randomUUID();

    this.latestMicroId = microId;
    this.latestMacroId = macroId;

    const microInit = new Promise<void>((resolve, reject) => {
      this.pending.set(microId, {
        resolve: () => resolve(),
        reject,
        timestamp: Date.now(),
      });
      this.microWorker.postMessage(
        {
          id: microId,
          type: 'INIT',
          payload: { paramsJson, populationJson },
        } satisfies WorkerRequest,
      );
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

    await Promise.all([microInit, macroInit]);
  }

  /**
   * Send a SIMULATE request to the micro worker.
   *
   * Updates simulation parameters from slider positions and computes
   * fiscal impact for the specified household profile.
   */
  async simulate(
    params: number[],
    profileIndex: number,
  ): Promise<MicroResult> {
    const id = crypto.randomUUID();
    this.latestMicroId = id;

    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject, timestamp: Date.now() });
      this.microWorker.postMessage({
        id,
        type: 'SIMULATE',
        payload: { params, profileIndex } satisfies SimulatePayload,
      } satisfies WorkerRequest);
    });
  }

  /**
   * Send an INTERPOLATE request to the macro worker (single-point).
   *
   * Performs multi-linear interpolation over the shock matrix at
   * a single (tax, spend, horizon) point. Returns null if the
   * point is outside the convex hull.
   */
  async interpolate(
    tax: number,
    spend: number,
    horizon: number,
  ): Promise<MacroResult | null> {
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
   * Send an INTERPOLATE (project) request to the macro worker (multi-year).
   *
   * Projects a macroeconomic trajectory over multiple years by
   * interpolating each year independently. Returns null if any
   * year falls outside the convex hull (all-or-nothing).
   */
  async project(
    tax: number,
    spend: number,
    years: number,
  ): Promise<MacroResult | null> {
    const id = crypto.randomUUID();
    this.latestMacroId = id;

    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject, timestamp: Date.now() });
      this.macroWorker.postMessage({
        id,
        type: 'INTERPOLATE',
        payload: {
          tax,
          spend,
          years,
          subType: 'project',
        } satisfies ProjectPayload,
      } satisfies WorkerRequest);
    });
  }

  /**
   * Terminate both workers and clean up pending requests.
   * Call when the simulation page is unmounted.
   */
  terminate(): void {
    this.microWorker.terminate();
    this.macroWorker.terminate();
    this.pending.forEach((entry) => {
      entry.reject(new Error('Orchestrator terminated'));
    });
    this.pending.clear();
  }
}
