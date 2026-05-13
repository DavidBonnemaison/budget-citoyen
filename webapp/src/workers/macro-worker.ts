// webapp/src/workers/macro-worker.ts
//
// PRIVACY GUARANTEE (D-12): This worker NEVER calls fetch() or XMLHttpRequest.
// All data arrives via postMessage from the main thread.
//
// Macroeconomic engine Web Worker — replaces the deleted WASM macro-worker.ts
// with pure TypeScript trilinear interpolation. No WASM imports.
//
// Architecture: The orchestrator (main thread) fetches the shock matrix binary,
// and transfers the ArrayBuffer to this worker via postMessage (zero-copy).
// The worker parses the binary into a ShockMatrixData structure and handles
// INTERPOLATE/PROJECT requests using the pure TS interpolation engine.
//
// Message protocol (D-11):
//   INIT        → parse binary matrix, respond READY
//   INTERPOLATE → interpolateAtPoint() or projectTrajectory(), respond MACRO_RESULT
//   PROJECT     → projectTrajectory(), respond MACRO_RESULT
//   ERROR       → caught exceptions respond with ERROR type

import { interpolateAtPoint, projectTrajectory } from '../engine/macro-interpolate';
import type {
  ShockMatrixData,
  WorkerRequest,
  WorkerResponse,
  MacroInitPayload,
  InterpolatePayload,
  ProjectPayload,
  MacroResult,
} from '../engine/types';

// ── Worker State ────────────────────────────────────────────────────────────

let matrix: ShockMatrixData | null = null;

// ── Binary Matrix Parser ────────────────────────────────────────────────────

/**
 * Parses the shock matrix from a binary ArrayBuffer.
 *
 * Binary layout (all multi-byte values little-endian):
 * ```
 * Offset  Size    Field
 * 0       4       numTax (uint32)
 * 4       4       numSpend (uint32)
 * 8       4       numHorizon (uint32)
 * 12      4       numHullEq (uint32) — number of hull hyperplanes
 * 16      N*8     taxBp (numTax f64 values)
 * *       M*8     spendBp (numSpend f64 values)
 * *       H*8     horizonBp (numHorizon f64 values)
 * *       E*8     hullEquations (numHullEq * 4 f64 values, stride 4 per eq)
 * *       G*8     grid (numTax * numSpend * numHorizon * 4 f64 values)
 * ```
 *
 * The Float64Arrays returned are subarray views into the same ArrayBuffer
 * (zero-copy) — no data duplication.
 */
function parseMatrixBytes(buffer: ArrayBuffer): ShockMatrixData {
  const headerView = new DataView(buffer, 0, 16);
  const numTax = headerView.getUint32(0, true);
  const numSpend = headerView.getUint32(4, true);
  const numHorizon = headerView.getUint32(8, true);
  const numHullEq = headerView.getUint32(12, true);

  // Float64 data starts at byte offset 16
  const f64 = new Float64Array(buffer, 16);
  let offset = 0;

  const taxBp = new Float64Array(f64.buffer, f64.byteOffset + offset * 8, numTax);
  offset += numTax;

  const spendBp = new Float64Array(
    f64.buffer,
    f64.byteOffset + offset * 8,
    numSpend,
  );
  offset += numSpend;

  const horizonBp = new Float64Array(
    f64.buffer,
    f64.byteOffset + offset * 8,
    numHorizon,
  );
  offset += numHorizon;

  const hullEqLen = numHullEq * 4; // 4 coefficients per hyperplane
  const hullEquations = new Float64Array(
    f64.buffer,
    f64.byteOffset + offset * 8,
    hullEqLen,
  );
  offset += hullEqLen;

  const gridSize = numTax * numSpend * numHorizon * 4; // 4 features per point
  const grid = new Float64Array(
    f64.buffer,
    f64.byteOffset + offset * 8,
    gridSize,
  );

  return { grid, taxBp, spendBp, horizonBp, hullEquations };
}

// ── Message Handler ─────────────────────────────────────────────────────────

self.onmessage = (e: MessageEvent<WorkerRequest>) => {
  const { id, type, payload } = e.data;

  try {
    switch (type) {
      case 'INIT': {
        const initPayload = payload as MacroInitPayload;
        matrix = parseMatrixBytes(initPayload.matrixBytes);
        const response: WorkerResponse = { id, type: 'READY', payload: null };
        self.postMessage(response);
        break;
      }

      case 'INTERPOLATE': {
        if (!matrix) {
          self.postMessage({
            id,
            type: 'ERROR',
            payload: 'Matrix not initialized — send INIT first',
          } satisfies WorkerResponse);
          return;
        }

        // Check subType to distinguish single-point from projection
        const interpPayload = payload as InterpolatePayload & {
          subType?: string;
          years?: number;
        };

        let result: MacroResult | null;

        if (interpPayload.subType === 'project') {
          // Multi-year trajectory projection
          const years = (payload as ProjectPayload).years;
          result = projectTrajectory(matrix, interpPayload.tax, interpPayload.spend, years);
        } else {
          // Single-point interpolation
          result = interpolateAtPoint(
            matrix,
            interpPayload.tax,
            interpPayload.spend,
            interpPayload.horizon,
          );
        }

        self.postMessage({
          id,
          type: 'MACRO_RESULT',
          payload: result,
        } satisfies WorkerResponse<MacroResult | null>);
        break;
      }

      case 'PROJECT': {
        if (!matrix) {
          self.postMessage({
            id,
            type: 'ERROR',
            payload: 'Matrix not initialized — send INIT first',
          } satisfies WorkerResponse);
          return;
        }

        const projPayload = payload as ProjectPayload;
        const result = projectTrajectory(
          matrix,
          projPayload.tax,
          projPayload.spend,
          projPayload.years,
        );

        self.postMessage({
          id,
          type: 'MACRO_RESULT',
          payload: result,
        } satisfies WorkerResponse<MacroResult | null>);
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
    self.postMessage({
      id,
      type: 'ERROR',
      payload: err instanceof Error ? err.message : String(err),
    } satisfies WorkerResponse);
  }
};
