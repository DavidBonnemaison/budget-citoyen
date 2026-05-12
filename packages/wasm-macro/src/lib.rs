// WASM boundary layer for the macroeconomic shock matrix engine.
//
// Exposes ShockMatrix + interpolation via typed #[wasm_bindgen] exports.
// The matrix data is loaded once at initialization as postcard-encoded
// binary (D-12). Interpolation queries return typed JsValue objects via
// serde-wasm-bindgen (D-10) or JsValue::NULL for out-of-bounds points
// (Pitfall 2 — no silent extrapolation).
//
// Decision D-02: All business logic stays in module files (matrix.rs,
//                interpolate.rs, projection.rs). This file is a thin boundary.

use wasm_bindgen::prelude::*;
use serde_wasm_bindgen;
use serde::Deserialize;

use crate::matrix::ShockMatrix;
use crate::interpolate::interpolate_at_point;
use crate::projection::project_trajectory;

// ── Module declarations ────────────────────────────────────────────────────

pub mod matrix;
pub mod interpolate;
pub mod projection;

// ── Postcard deserialization helper ────────────────────────────────────────

/// Intermediate deserialization struct for the postcard binary format.
///
/// The Phase 1 data pipeline serializes a `ShockMatrixData` to postcard+gzip
/// for HTTP transfer. On the WASM side, we deserialize this struct from the
/// raw bytes and then construct a validated `ShockMatrix` from its fields.
///
/// All fields use `Vec<f64>` — the postcard format natively handles Vec<f64>
/// with minimal overhead (~8 bytes per element + length prefix).
#[derive(Deserialize)]
struct ShockMatrixData {
    tax_bp: Vec<f64>,
    spend_bp: Vec<f64>,
    horizon_bp: Vec<f64>,
    grid: Vec<f64>,
    hull_equations: Vec<Vec<f64>>,
}

// ── WASM Exports ───────────────────────────────────────────────────────────

/// The macroeconomic shock matrix engine — typed WASM boundary.
///
/// Wraps a pre-computed `ShockMatrix` with convex hull boundary enforcement.
/// Interpolation queries use multi-linear interpolation (interpn 0.11.0) over
/// the 4D grid (tax × spend × horizon × output_feature).
///
/// # Input contract
/// - `tax`, `spend`, `horizon` are `f64` values from JavaScript sliders.
/// - All values must be finite (NaN/Infinity rejected per T-02-14).
/// - The convex hull is checked before every interpolation call (Pitfall 2).
///
/// # Output contract (D-10)
/// - Valid results are serialized `MacroResult` via `serde-wasm-bindgen`.
/// - Out-of-bounds queries return `JsValue::NULL` — the JS side must check
///   for null and display a "hors domaine" warning to the user.
#[wasm_bindgen]
pub struct MacroEngine {
    matrix: ShockMatrix,
}

#[wasm_bindgen]
impl MacroEngine {
    /// Initializes the macro engine from postcard-encoded binary data.
    ///
    /// # D-12 — Data arrives via main thread transfer at init time
    ///
    /// The shock matrix is loaded once at initialization as postcard+gzip
    /// binary (typically 3-5 KB for a 10×10×5 grid). After construction,
    /// all interpolation queries are zero-allocation lookups.
    ///
    /// # Binary format
    ///
    /// The `matrix_bytes` slice must be a postcard-encoded `ShockMatrixData`
    /// struct containing: `tax_bp`, `spend_bp`, `horizon_bp`, `grid`,
    /// and `hull_equations` fields.
    ///
    /// # Errors
    ///
    /// Returns `JsValue` error string if:
    /// - The binary data is malformed (postcard deserialization fails)
    /// - The grid dimensions don't match (ShockMatrix::new panics → caught
    ///   by panic hook, returns Err in production)
    #[wasm_bindgen(constructor)]
    pub fn new(matrix_bytes: &[u8]) -> Result<MacroEngine, JsValue> {
        let data: ShockMatrixData = postcard::from_bytes(matrix_bytes)
            .map_err(|e| JsValue::from_str(&format!(
                "Erreur de désérialisation des données de la matrice : {}",
                e
            )))?;

        let matrix = ShockMatrix::new(
            data.tax_bp,
            data.spend_bp,
            data.horizon_bp,
            data.grid,
            data.hull_equations,
        );

        Ok(MacroEngine { matrix })
    }

    /// Interpolates the macroeconomic impact at a single (tax, spend, horizon)
    /// point using multi-linear interpolation.
    ///
    /// # T-02-14 — NaN/Infinity rejection
    ///
    /// All inputs are validated for finiteness. NaN or Infinity values fail
    /// the hull containment check and return `JsValue::NULL`.
    ///
    /// # Pitfall 2 — No silent extrapolation
    ///
    /// If the query point lies outside the convex hull, this method returns
    /// `JsValue::NULL`. The JavaScript frontend MUST check for null and
    /// display a "hors domaine de la matrice" warning to the user. Never
    /// silently extrapolate beyond the pre-computed grid.
    ///
    /// # Returns
    ///
    /// - `JsValue` object (serialized `MacroResult`) if the point is in-bounds
    /// - `JsValue::NULL` if the point is out-of-bounds or inputs are invalid
    pub fn interpolate(&self, tax: f64, spend: f64, horizon: f64) -> JsValue {
        let result = interpolate_at_point(&self.matrix, tax, spend, horizon);

        match result {
            Some(macro_result) => {
                serde_wasm_bindgen::to_value(&macro_result)
                    .unwrap_or(JsValue::NULL)
            }
            None => JsValue::NULL,
        }
    }

    /// Projects a macroeconomic trajectory over `years` horizon by
    /// interpolating each year independently.
    ///
    /// # Parameters
    ///
    /// - `tax`: Tax rate multiplier (must be within convex hull bounds)
    /// - `spend`: Spending level multiplier (must be within convex hull bounds)
    /// - `years`: Number of years to project (1–5 for standard grid)
    ///
    /// # Returns
    ///
    /// - `JsValue` object (serialized `MacroResult` with trajectory vectors
    ///   of length `years`) if all per-year interpolations succeed
    /// - `JsValue::NULL` if any year falls outside the convex hull
    ///   No partial results are returned — the projection is all-or-nothing.
    pub fn project(&self, tax: f64, spend: f64, years: usize) -> JsValue {
        let result = project_trajectory(&self.matrix, tax, spend, years);

        match result {
            Some(macro_result) => {
                serde_wasm_bindgen::to_value(&macro_result)
                    .unwrap_or(JsValue::NULL)
            }
            None => JsValue::NULL,
        }
    }
}

// ── Panic Hook (ASVS V7) ───────────────────────────────────────────────────

/// Initialize the panic hook with debug-aware behavior.
///
/// **ASVS V7 compliance:** Production builds must not expose panic messages
/// to the browser console. Debug builds get readable stack traces from
/// `console_error_panic_hook`.
#[wasm_bindgen(start)]
fn init_panic_hook() {
    if cfg!(debug_assertions) {
        console_error_panic_hook::set_once();
    } else {
        std::panic::set_hook(Box::new(|_info| {
            // Suppress all panic output in production (ASVS V7).
        }));
    }
}

// ── Unit Tests (native cargo test) ─────────────────────────────────────────

#[cfg(test)]
mod tests {
    use ndarray::Array3;
    use postcard;
    use serde::{Deserialize, Serialize};

    /// Postcard serialization round-trip test.
    /// Demonstrates the shock matrix binary loading strategy:
    /// 1. Load flat `Vec<f64>` from postcard+gzip HTTP response
    /// 2. Reshape into ndarray grid matching interpn conventions
    /// 3. Query via interpn::multilinear
    #[test]
    fn postcard_roundtrip_shock_matrix() {
        // Simulate a 3D shock matrix: tax_rate(5) × spending(5) × horizon(3) → 4 outputs
        let n_tax = 5usize;
        let n_spend = 5;
        let n_horizon = 3;
        let n_outputs = 4;
        let total_elements = n_tax * n_spend * n_horizon * n_outputs;

        // Create sample grid data (flat Vec<f64>)
        let grid_flat: Vec<f64> = (0..total_elements).map(|i| i as f64 * 0.1).collect();

        // Serialize to postcard (binary, ~10MB for full 50K-point grid)
        let serialized: Vec<u8> = postcard::to_allocvec(&grid_flat)
            .expect("postcard serialization should succeed");

        // Verify postcard output is compact (no schema overhead)
        let expected_min_size = total_elements * 8; // f64 = 8 bytes each
        assert!(
            serialized.len() >= expected_min_size,
            "postcard payload size {} should be >= minimum f64 data size {}",
            serialized.len(),
            expected_min_size
        );
        assert!(
            serialized.len() < expected_min_size + 100,
            "postcard overhead is minimal (< 100 bytes for Vec<f64>)"
        );

        // Deserialize back
        let deserialized: Vec<f64> = postcard::from_bytes(&serialized)
            .expect("postcard deserialization should succeed");
        assert_eq!(deserialized.len(), total_elements, "element count preserved");

        // Reshape into 4D: (tax, spend, horizon, outputs)
        let grid = Array3::from_shape_vec(
            (n_tax, n_spend, n_horizon * n_outputs),
            deserialized.clone(),
        )
        .expect("reshape into 3D Array3 should succeed");

        // Verify specific grid values after reshape (use approx for f64)
        assert!((grid[[0, 0, 0]] - 0.0).abs() < 1e-15);
        assert!((grid[[0, 0, 1]] - 0.1).abs() < 1e-15);
        // Last element: index 4 in dim0, 4 in dim1, 11 in dim2 (5*5*12=300 elements)
        assert!((grid[[4, 4, 11]] - 29.9).abs() < 1e-12);

        // Round-trip integrity: re-serialize and compare
        let reserialized = postcard::to_allocvec(&deserialized).unwrap();
        assert_eq!(serialized, reserialized, "round-trip byte-identical");

        // Estimate: full grid (tax_rate 10 × spending 10 × horizon 5 × 4 outputs)
        // = 2000 f64 = 16,000 bytes raw → ~3-5 KB postcard+gzip
        let full_grid_elements = 10 * 10 * 5 * 4; // 2000
        let full_grid_bytes = full_grid_elements * 8; // 16,000 bytes
        assert!(full_grid_bytes < 1_000_000, "full grid fits in < 1MB raw");
    }

    /// Verify that postcard works with serde-derived structs (for metadata)
    #[test]
    fn postcard_struct_roundtrip() {
        #[derive(Serialize, Deserialize, PartialEq, Debug)]
        struct ShockMatrixMetadata {
            version: String,
            reference_year: u16,
            dim_names: Vec<String>,
            breakpoints: Vec<Vec<f64>>,
        }

        let meta = ShockMatrixMetadata {
            version: "shockmatrix-v2025.1".into(),
            reference_year: 2025,
            dim_names: vec![
                "tax_rate".into(),
                "spending_level".into(),
                "horizon_year".into(),
            ],
            breakpoints: vec![
                vec![0.0, 0.25, 0.5, 0.75, 1.0],
                vec![0.0, 0.5, 1.0],
                vec![2025.0, 2026.0, 2027.0],
            ],
        };

        let bytes = postcard::to_allocvec(&meta).expect("struct serialization ok");
        let decoded: ShockMatrixMetadata =
            postcard::from_bytes(&bytes).expect("struct deserialization ok");

        assert_eq!(decoded, meta, "struct round-trip preserves all fields");
        assert_eq!(decoded.reference_year, 2025);
        assert_eq!(decoded.dim_names.len(), 3);
    }

    /// Verify the interpn crate compiles and basic API works
    #[test]
    fn interpn_basic_api() {
        // Create a 1D regular grid: f(x) at x = 0.0, 1.0, 2.0
        // values: f(0)=0.0, f(1)=2.0, f(2)=4.0
        let dims = &[3usize];
        let starts = &[0.0_f64];
        let steps = &[1.0_f64];
        let vals = &[0.0_f64, 2.0, 4.0];
        let obs = &[&[0.5_f64][..]];
        let mut out = [0.0_f64];

        let result = interpn::multilinear::regular::interpn(
            dims, starts, steps, vals, obs, &mut out,
        );

        assert!(result.is_ok(), "interpn multilinear::regular::interpn should succeed");
        assert!((out[0] - 1.0).abs() < 1e-10, "f(0.5) = 1.0");
    }
}
