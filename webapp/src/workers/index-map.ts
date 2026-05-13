// webapp/src/workers/index-map.ts
// Hybrid architecture (Plan 02-11): WASM interop layer removed.
// These constants remain for reference but are no longer synced with a Rust crate.
//
// D-09: Constants shared between Rust and TypeScript.
// Each slider in the UI maps to an index in the flat &[f64] simulation
// parameter array. The Rust side uses identical constant values to index
// into the SimulationState struct in-place.

export const PARAM_INDICES = {
  IR_BRACKET_1_RATE: 0,
  IR_BRACKET_2_RATE: 1,
  IR_BRACKET_3_RATE: 2,
  IR_BRACKET_4_RATE: 3,
  IR_BRACKET_5_RATE: 4,
  IS_RATE: 5,
  TVA_NORMAL: 6,
  TVA_REDUCED: 7,
  CSG_DEDUCTIBLE: 8,
  CRDS: 9,
  COTIS_SALARIALES: 10,
  COTIS_PATRONALES: 11,
  SPEND_LEVEL: 12,
  EFFECTIFS_ETAT: 13,
} as const;

export const NUM_SIMULATION_PARAMS = 16;
