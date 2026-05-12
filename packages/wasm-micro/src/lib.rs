use wasm_bindgen::prelude::*;

// ── Module declarations ────────────────────────────────────────────────────
//
// `generated` contains auto-generated formula functions from Plan 02-04.
// `system` is the TaxBenefitSystem dispatcher.
// `simulation` is the flat &[f64] SimulationState (D-09).

pub mod generated;
pub mod system;
pub mod simulation;
