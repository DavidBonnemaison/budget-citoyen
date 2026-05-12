// SimulationState — flat &[f64] parameter update interface (D-09).
//
// All simulation parameters cross the WASM boundary as a single &[f64]
// slice. This module provides the constant index mapping, the
// SimulationState struct, and in-place parameter updates with bounds
// validation.
//
// Decision D-09: Input is flat &[f64] slice — zero serialization overhead
//                per slider interaction. Index-based setters update a
//                pre-allocated array in-place.
//
// INDEX MAPPING (shared contract with TypeScript frontend):
//
// Index 0-4  : IR bracket rates (fraction of reference, 5 brackets)
// Index 5    : IS rate
// Index 6-7  : TVA normal / TVA reduced rate
// Index 8-9  : CSG deductible / CRDS rate
// Index 10-11: Cotisations salariales / patronales rates
// Index 12   : Dépenses publiques level
// Index 13   : Effectifs de l'État factor
// Index 14-15: Reserved for Phase 3/4 extensions

/// Number of simulation parameters in the flat &[f64] array (D-09).
pub const NUM_SIMULATION_PARAMS: usize = 16;

/// Holds the current simulation parameter values as a flat array of
/// multipliers (1.0 = reference value). Updated in-place from WASM
/// boundary on every slider interaction.
#[derive(Debug)]
pub struct SimulationState {
    params: [f64; NUM_SIMULATION_PARAMS],
}

impl Default for SimulationState {
    fn default() -> Self {
        SimulationState {
            params: [1.0_f64; NUM_SIMULATION_PARAMS],
        }
    }
}

impl SimulationState {
    /// Creates a new SimulationState with all parameters at reference
    /// values (1.0 = no reform applied).
    pub fn new() -> Self {
        Self::default()
    }

    /// Updates all simulation parameters from a flat slice.
    ///
    /// Called from the WASM boundary on every slider interaction.
    /// Each value is a multiplier relative to the reference parameter
    /// (1.0 = unchanged, 0.5 = halved, 2.0 = doubled).
    ///
    /// # Validation
    ///
    /// - Input slice must have exactly `NUM_SIMULATION_PARAMS` elements
    /// - All values must be finite (not NaN or infinite)
    /// - All values must be non-negative (rates and levels)
    ///
    /// # Errors
    ///
    /// Returns a descriptive error if validation fails.
    pub fn update_params(&mut self, input: &[f64]) -> Result<(), &'static str> {
        if input.len() != NUM_SIMULATION_PARAMS {
            return Err("La taille du tableau d'entrée doit être exactement 16");
        }

        // Validate all values before updating
        for (_i, &val) in input.iter().enumerate() {
            if !val.is_finite() {
                return Err("Les paramètres doivent être des nombres finis (pas NaN ou infini)");
            }
            if val < 0.0 {
                return Err("Les paramètres doivent être positifs ou nuls");
            }
            // Reasonable upper bound to prevent overflow
            if val > 100.0 {
                return Err("Les paramètres ne peuvent pas dépasser 100x la valeur de référence");
            }
        }

        self.params.copy_from_slice(input);
        Ok(())
    }

    /// Returns the current parameter values as a slice.
    pub fn params(&self) -> &[f64] {
        &self.params
    }

    /// Accesses a specific parameter by index.
    pub fn get_param(&self, index: usize) -> Option<f64> {
        self.params.get(index).copied()
    }
}

// ── Named Index Constants ──────────────────────────────────────────────────

/// Index constants for the flat parameter array.
/// These are shared with the TypeScript frontend via documentation.
pub mod indices {
    pub const IR_BRACKET_1_RATE: usize = 0;
    pub const IR_BRACKET_2_RATE: usize = 1;
    pub const IR_BRACKET_3_RATE: usize = 2;
    pub const IR_BRACKET_4_RATE: usize = 3;
    pub const IR_BRACKET_5_RATE: usize = 4;
    pub const IS_RATE: usize = 5;
    pub const TVA_NORMAL: usize = 6;
    pub const TVA_REDUCED: usize = 7;
    pub const CSG_DEDUCTIBLE: usize = 8;
    pub const CRDS_RATE: usize = 9;
    pub const COTIS_SALARIALES: usize = 10;
    pub const COTIS_PATRONALES: usize = 11;
    pub const SPEND_LEVEL: usize = 12;
    pub const EFFECTIFS_ETAT: usize = 13;
    // Indices 14-15: Reserved for Phase 3/4 extensions
}
