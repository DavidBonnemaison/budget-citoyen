// WASM boundary layer for the microsimulation engine.
//
// Exposes the TaxBenefitSystem + SimulationState combo via typed
// #[wasm_bindgen] exports. Inputs cross the boundary as flat &[f64]
// slices (D-09 — zero serialization overhead). Outputs return as
// JsValue objects via serde-wasm-bindgen (D-10 — typed result structs).
//
// Decision D-02: All business logic stays in module files (system.rs,
//                simulation.rs, generated/). This file is a thin boundary.

use wasm_bindgen::prelude::*;
use serde_wasm_bindgen;

use budget_citoyen_core::types::Profile;
use budget_citoyen_core::parameters::Parameters;

use crate::system::TaxBenefitSystem;
use crate::simulation::SimulationState;

// ── Module declarations ────────────────────────────────────────────────────
//
// `generated` contains auto-generated formula functions from Plan 02-04.
// `system` is the TaxBenefitSystem dispatcher.
// `simulation` is the flat &[f64] SimulationState (D-09).

pub mod generated;
pub mod system;
pub mod simulation;

// ── WASM Exports ───────────────────────────────────────────────────────────

/// The microsimulation engine — typed WASM boundary.
///
/// Wraps the TaxBenefitSystem (business logic) and SimulationState (parameter
/// state) into a single #[wasm_bindgen] struct exported to JavaScript.
///
/// # Input contract (D-09)
/// - Simulation parameters arrive as a flat `&[f64]` slice with exactly
///   `NUM_SIMULATION_PARAMS` (16) elements.
/// - Profile index selects which household to compute for.
///
/// # Output contract (D-10)
/// - Results are serialized via `serde-wasm-bindgen::to_value` into typed
///   `JsValue` objects — no JSON.stringify overhead on the JS/WASM boundary.
#[wasm_bindgen]
#[derive(Debug)]
pub struct MicroEngine {
    system: TaxBenefitSystem,
    state: SimulationState,
}

#[wasm_bindgen]
impl MicroEngine {
    /// Initializes the microsimulation engine from JSON parameter data and a
    /// synthetic population JSON array.
    ///
    /// # D-12 — Data arrives via main thread transfer at init time
    ///
    /// All parameters and profiles are loaded once at initialization. After
    /// construction, slider interactions use only the flat `&[f64]` slice
    /// via `update_and_simulate`.
    ///
    /// # Validation (D-16)
    ///
    /// Every profile in the population is validated via `Profile::validate()`.
    /// If any profile fails validation, construction returns an error with
    /// the offending profile ID (category only — never raw data per T-02-24).
    ///
    /// # Errors
    ///
    /// Returns `JsValue` error strings for:
    /// - Malformed JSON (both parameters and population)
    /// - Version mismatch in parameter data
    /// - Profile validation failure (D-16)
    #[wasm_bindgen(constructor)]
    pub fn new(params_json: &str, population_json: &str) -> Result<MicroEngine, JsValue> {
        // Deserialize parameters
        let parameters = Parameters::load_from_json(params_json, "rules-v2025.1")
            .map_err(|e| JsValue::from_str(&e.to_string()))?;

        // Deserialize profiles
        let profiles: Vec<Profile> = serde_json::from_str(population_json)
            .map_err(|e| JsValue::from_str(&format!("Erreur de parsing JSON de la population : {}", e)))?;

        if profiles.is_empty() {
            return Err(JsValue::from_str("La population ne peut pas être vide"));
        }

        // D-16: Validate every profile before construction
        for profile in &profiles {
            profile.validate().map_err(|e| {
                JsValue::from_str(&format!(
                    "Échec de validation du profil '{}': {}",
                    profile.profile_id, e
                ))
            })?;
        }

        let system = TaxBenefitSystem::new(parameters, profiles)
            .map_err(|e| JsValue::from_str(&e))?;

        let state = SimulationState::new();

        Ok(MicroEngine { system, state })
    }

    /// Updates simulation parameters from a flat slice and computes taxes
    /// for the profile at `profile_index`.
    ///
    /// # D-09 — Zero-serialization input
    ///
    /// The `params` slice must contain exactly [`NUM_SIMULATION_PARAMS`] (16)
    /// elements. Each element is a multiplier relative to the reference
    /// parameter (1.0 = unchanged). The slice is copied into the simulation
    /// state in-place — no allocation, no serialization.
    ///
    /// # D-10 — Typed output
    ///
    /// The result is a [`MicroResult`] serialized via `serde-wasm-bindgen`
    /// into a `JsValue` object. JavaScript can access fields directly
    /// (e.g., `result.ir`, `result.revenu_disponible`) — no JSON parsing
    /// required on the JS side.
    ///
    /// # Errors
    ///
    /// Returns `JsValue` error string if:
    /// - `params.len() != NUM_SIMULATION_PARAMS` (T-02-11)
    /// - Any param is NaN, infinite, negative, or > 100x (bounds check)
    /// - `profile_index` is out of bounds (T-02-11)
    pub fn update_and_simulate(
        &mut self,
        params: &[f64],
        profile_index: usize,
    ) -> Result<JsValue, JsValue> {
        // T-02-11: Validate input bounds
        self.state.update_params(params)
            .map_err(|e| JsValue::from_str(e))?;

        // T-02-11: profile_index bounds check is done inside compute_all_taxes
        let result = self.system.compute_all_taxes(profile_index)
            .map_err(|e| JsValue::from_str(&e))?;

        // D-10: Serialize via serde-wasm-bindgen (typed JsValue, no JSON)
        serde_wasm_bindgen::to_value(&result)
            .map_err(|e| JsValue::from_str(&format!("Erreur de sérialisation du résultat : {}", e)))
    }
}

// ── Panic Hook (ASVS V7) ───────────────────────────────────────────────────

/// Initialize the panic hook with debug-aware behavior.
///
/// **ASVS V7 compliance:** Production builds (release) must NOT expose
/// panic messages to the browser console — a panic in WASM would dump
/// linear memory contents, potentially leaking sensitive profile data.
///
/// In debug builds, `console_error_panic_hook` provides readable stack
/// traces for development. In release builds, panics are silently caught
/// by a no-op hook — the engine fails closed with `Err(JsValue)` rather
/// than crashing.
#[wasm_bindgen(start)]
fn init_panic_hook() {
    if cfg!(debug_assertions) {
        console_error_panic_hook::set_once();
    } else {
        std::panic::set_hook(Box::new(|_info| {
            // Suppress all panic output in production (ASVS V7).
            // The JS caller will receive Err(JsValue) from the
            // Result-returning bound functions.
        }));
    }
}
