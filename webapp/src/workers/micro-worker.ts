// webapp/src/workers/micro-worker.ts
//
// PRIVACY GUARANTEE (D-12): This worker NEVER calls fetch() or XMLHttpRequest.
// All data arrives via postMessage from the main thread.
//
// Microsimulation engine Web Worker — imports WASM, handles SIMULATE messages
// for computing fiscal impact on individual household profiles.
//
// Message protocol (D-11):
//   INIT     → await init(), construct MicroEngine, respond READY
//   SIMULATE → update_and_simulate(params, profileIndex), respond MICRO_RESULT
//   ERROR    → caught exceptions respond with ERROR type

import init, { MicroEngine } from '../../../packages/wasm-micro/pkg';

let engine: MicroEngine | null = null;

self.onmessage = async (e: MessageEvent) => {
  const { id, type, payload } = e.data;

  try {
    switch (type) {
      case 'INIT': {
        await init();
        engine = new MicroEngine(payload.paramsJson, payload.populationJson);
        self.postMessage({ id, type: 'READY', payload: null });
        break;
      }

      case 'SIMULATE': {
        if (!engine) {
          self.postMessage({
            id,
            type: 'ERROR',
            payload: 'Engine not initialized — send INIT first',
          });
          return;
        }

        const result = engine.update_and_simulate(
          new Float64Array(payload.params),
          payload.profileIndex,
        );
        self.postMessage({ id, type: 'MICRO_RESULT', payload: result });
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
