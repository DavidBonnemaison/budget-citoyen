// WASM boundary round-trip tests for the macroeconomic shock matrix engine.
//
// Validates that JS↔WASM communication works correctly:
// - Engine construction from postcard-encoded binary data
// - Interpolation returns typed JsValue for in-bounds queries (D-10)
// - Interpolation returns JsValue::NULL for out-of-bounds queries (Pitfall 2)
// - Trajectory projection returns multi-year vectors
//
// These tests run in a headless browser via `wasm-pack test --headless`.

use wasm_bindgen_test::*;
use budget_citoyen_wasm_macro::MacroEngine;

wasm_bindgen_test_configure!(run_in_browser);

// ── Helper: Build synthetic postcard-encoded ShockMatrixData ────────────────
//
// Creates a minimal 3×3×2 grid (tax × spend × horizon):
//   tax_bp     = [0.5, 1.0, 2.0]
//   spend_bp   = [0.7, 1.0, 1.5]
//   horizon_bp = [1.0, 2.0]
//   grid       = 72 f64 values (3 × 3 × 2 × 4 outputs) — sequential 0.0, 0.1, ...
//   hull       = bounding box with 6 faces

fn build_test_matrix_bytes() -> Vec<u8> {
    use serde::Serialize;

    #[derive(Serialize)]
    struct ShockMatrixData {
        tax_bp: Vec<f64>,
        spend_bp: Vec<f64>,
        horizon_bp: Vec<f64>,
        grid: Vec<f64>,
        hull_equations: Vec<Vec<f64>>,
    }

    let tax_bp = vec![0.5, 1.0, 2.0];
    let spend_bp = vec![0.7, 1.0, 1.5];
    let horizon_bp = vec![1.0, 2.0];

    // 3 tax × 3 spend × 2 horizon × 4 outputs = 72 elements
    let grid: Vec<f64> = (0..72).map(|i| i as f64 * 0.1).collect();

    // Convex hull: simple axis-aligned bounding box
    // Half-space representation: a1*tax + a2*spend + a3*horizon + b ≤ 0
    let hull_equations = vec![
        vec![-1.0, 0.0, 0.0, 0.5],  // tax ≥ 0.5  → -tax + 0.5 ≤ 0
        vec![1.0, 0.0, 0.0, -2.0],   // tax ≤ 2.0  → tax - 2.0 ≤ 0
        vec![0.0, -1.0, 0.0, 0.7],   // spend ≥ 0.7
        vec![0.0, 1.0, 0.0, -1.5],   // spend ≤ 1.5
        vec![0.0, 0.0, -1.0, 1.0],   // horizon ≥ 1.0
        vec![0.0, 0.0, 1.0, -2.0],   // horizon ≤ 2.0
    ];

    let data = ShockMatrixData {
        tax_bp,
        spend_bp,
        horizon_bp,
        grid,
        hull_equations,
    };

    postcard::to_allocvec(&data).expect("postcard serialization of test matrix should succeed")
}

// ── Test 1: Interpolation returns a value for in-bounds parameters ──────────

#[wasm_bindgen_test]
fn test_interpolate_returns_value() {
    let matrix_bytes = build_test_matrix_bytes();
    let engine = MacroEngine::new(&matrix_bytes)
        .expect("MacroEngine construction should succeed with valid test data");

    // Query at the center of the grid (in-bounds)
    let result = engine.interpolate(1.0, 1.0, 1.5);

    // Should NOT be null — point is inside convex hull
    assert!(!result.is_null(), "In-bounds interpolation should return a value, not null");
    assert!(result.is_object(), "Result should be a JsValue object");

    // Verify expected MacroResult fields exist
    let gdp = js_sys::Reflect::get(&result, &"gdp_growth_trajectory".into())
        .expect("gdp_growth_trajectory should be present");
    assert!(gdp.is_array(), "gdp_growth_trajectory should be an array");

    let deficit = js_sys::Reflect::get(&result, &"deficit_trajectory".into())
        .expect("deficit_trajectory should be present");
    assert!(deficit.is_array(), "deficit_trajectory should be an array");
}

// ── Test 2: Out-of-bounds interpolation returns null (Pitfall 2) ────────────

#[wasm_bindgen_test]
fn test_interpolate_out_of_bounds_returns_null() {
    let matrix_bytes = build_test_matrix_bytes();
    let engine = MacroEngine::new(&matrix_bytes)
        .expect("MacroEngine construction should succeed");

    // Tax multiplier of 10.0 is far outside the [0.5, 2.0] range
    let result = engine.interpolate(10.0, 1.0, 1.5);

    // Pitfall 2: Must return null, NOT silently extrapolated values
    assert!(result.is_null(),
        "Out-of-bounds interpolation must return null (Pitfall 2 — no silent extrapolation). Got: {:?}",
        result
    );
}

// ── Test 3: NaN input returns null ─────────────────────────────────────────

#[wasm_bindgen_test]
fn test_interpolate_nan_returns_null() {
    let matrix_bytes = build_test_matrix_bytes();
    let engine = MacroEngine::new(&matrix_bytes)
        .expect("MacroEngine construction should succeed");

    let result = engine.interpolate(f64::NAN, 1.0, 1.5);
    assert!(result.is_null(), "NaN input should return null (T-02-14 defense-in-depth)");
}

// ── Test 4: Project trajectory returns multi-year result ────────────────────

#[wasm_bindgen_test]
fn test_project_returns_trajectory() {
    let matrix_bytes = build_test_matrix_bytes();
    let engine = MacroEngine::new(&matrix_bytes)
        .expect("MacroEngine construction should succeed");

    // Project 2 years at grid center
    let result = engine.project(1.0, 1.0, 2);

    assert!(!result.is_null(), "In-bounds projection should return a value");
    assert!(result.is_object(), "Result should be a JsValue object");

    // Verify trajectory vectors have length 2
    let gdp = js_sys::Reflect::get(&result, &"gdp_growth_trajectory".into())
        .expect("gdp_growth_trajectory should be present");
    let gdp_arr = js_sys::Array::from(&gdp);
    assert_eq!(gdp_arr.length(), 2, "gdp_growth_trajectory should have 2 elements for 2-year projection");

    let deficit = js_sys::Reflect::get(&result, &"deficit_trajectory".into())
        .expect("deficit_trajectory should be present");
    let deficit_arr = js_sys::Array::from(&deficit);
    assert_eq!(deficit_arr.length(), 2, "deficit_trajectory should have 2 elements");

    // is_out_of_bounds should be false for in-bounds projection
    let oob = js_sys::Reflect::get(&result, &"is_out_of_bounds".into())
        .expect("is_out_of_bounds should be present");
    assert_eq!(oob.as_bool(), Some(false), "is_out_of_bounds should be false for in-bounds projection");
}

// ── Test 5: Out-of-bounds project returns null ──────────────────────────────

#[wasm_bindgen_test]
fn test_project_out_of_bounds_returns_null() {
    let matrix_bytes = build_test_matrix_bytes();
    let engine = MacroEngine::new(&matrix_bytes)
        .expect("MacroEngine construction should succeed");

    // Tax = 0.1 is below the 0.5 minimum
    let result = engine.project(0.1, 1.0, 2);
    assert!(result.is_null(), "Out-of-bounds projection must return null");
}

// ── Test 6: Malformed binary data returns Err ───────────────────────────────

#[wasm_bindgen_test]
fn test_malformed_binary_rejected() {
    let bad_bytes: Vec<u8> = vec![0xFF, 0xFF, 0xFF, 0xFF];  // Invalid postcard
    let result = MacroEngine::new(&bad_bytes);
    assert!(result.is_err(), "Malformed binary data should return Err from constructor");
}
