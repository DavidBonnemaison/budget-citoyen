// webapp/src/workers/macro-worker.ts
//
// PRIVACY GUARANTEE (D-12): This worker NEVER calls fetch() or XMLHttpRequest.
// All data arrives via postMessage from the main thread.
//
// Macroeconomic engine Web Worker — imports WASM, handles INTERPOLATE messages
// for projecting deficit, debt, GDP growth, and employment trajectories.
//
// Message protocol (D-11):
//   INIT        → await init(), construct MacroEngine from binary matrix, respond READY
//   INTERPOLATE → engine.interpolate(tax, spend, horizon) or engine.project(tax, spend, years),
//                 respond MACRO_RESULT or null (out-of-bounds)
//   ERROR       → caught exceptions respond with ERROR type

import init, { MacroEngine } from '../../../packages/wasm-macro/pkg';

let engine: MacroEngine | null = null;

self.onmessage = async (e: MessageEvent) => {
  const { id, type, payload } = e.data;

  try {
    switch (type) {
      case 'INIT': {
        await init();
        // MacroEngine constructor accepts postcard-encoded binary data (Uint8Array).
        // The main thread fetches the shock matrix, decompresses it, and transfers
        // the ArrayBuffer via postMessage (D-12: zero-copy transfer).
        engine = new MacroEngine(new Uint8Array(payload.matrixBytes));
        self.postMessage({ id, type: 'READY', payload: null });
        break;
      }

      case 'INTERPOLATE': {
        if (!engine) {
          self.postMessage({
            id,
            type: 'ERROR',
            payload: 'Engine not initialized — send INIT first',
          });
          return;
        }

        let result: unknown;

        if (payload.subType === 'project') {
          // Multi-year trajectory projection
          result = engine.project(payload.tax, payload.spend, payload.years);
        } else {
          // Single-point interpolation (D-09)
          result = engine.interpolate(payload.tax, payload.spend, payload.horizon);
        }

        // result is MacroResult (JsValue) if in-bounds, JsValue::NULL if out-of-bounds.
        // D-09: Out-of-bounds returns null — JS side must display "hors domaine" warning.
        self.postMessage({ id, type: 'MACRO_RESULT', payload: result });
        break;
      }

      default:
        self.postMessage({
          id,
          type: 'ERROR',
          payload: `Unknown message type: ${type}`,
        });
    }
  } catch (err) {
    self.postMessage({
      id,
      type: 'ERROR',
      payload: err instanceof Error ? err.message : String(err),
    });
  }
};
