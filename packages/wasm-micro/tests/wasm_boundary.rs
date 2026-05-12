// WASM boundary round-trip tests for the microsimulation engine.
//
// Validates that JS↔WASM communication works correctly:
// - Engine construction from JSON parameter and population data
// - Flat &[f64] slice input (D-09)
// - Typed JsValue output via serde-wasm-bindgen (D-10)
// - Error handling for invalid inputs
//
// These tests run in a headless browser via `wasm-pack test --headless`.

use wasm_bindgen_test::*;
use budget_citoyen_wasm_micro::MicroEngine;

wasm_bindgen_test_configure!(run_in_browser);

// ── Helper: valid parameters JSON (simplified format) ──────────────────────

fn valid_params_json() -> String {
    r#"{
        "version": "rules-v2025.1",
        "parameters": {
            "test.scalar": { "value": 1.0 }
        }
    }"#
    .to_string()
}

// ── Helper: valid single-profile population JSON ───────────────────────────

fn valid_population_json() -> String {
    r#"[
        {
            "profile_id": "test-citoyen-1",
            "age": 35,
            "patrimoine": 100000.0,
            "revenu_fiscal": 50000.0,
            "situation_familiale": "Celibataire",
            "nombre_parts": 1.0,
            "type_activite": "Salarie",
            "nb_enfants": 0
        }
    ]"#
    .to_string()
}

// ── Helper: invalid profile (negative wealth) ─────────────────────────────

fn invalid_population_json() -> String {
    r#"[
        {
            "profile_id": "test-bad-wealth",
            "age": 30,
            "patrimoine": -1.0,
            "revenu_fiscal": 50000.0,
            "situation_familiale": "Celibataire",
            "nombre_parts": 1.0,
            "type_activite": "Salarie",
            "nb_enfants": 0
        }
    ]"#
    .to_string()
}

// ── Test 1: Round-trip simulation with default (reference) parameters ──────

#[wasm_bindgen_test]
fn test_round_trip_simulation() {
    let mut engine = MicroEngine::new(
        &valid_params_json(),
        &valid_population_json(),
    ).expect("MicroEngine construction should succeed with valid data");

    // All multipliers at reference values (1.0 = no reform applied)
    let params: Vec<f64> = vec![1.0; 16];

    let result = engine
        .update_and_simulate(&params, 0)
        .expect("update_and_simulate should succeed with valid params");

    // D-10: Result should be a typed JsValue object
    assert!(result.is_object(), "Result should be a JsValue object (not null, not undefined)");

    // Verify expected fields from MicroResult exist
    let ir = js_sys::Reflect::get(&result, &"ir".into())
        .expect("ir field should be present");
    assert!(ir.as_f64().is_some(), "IR should be a number");

    let revenu_disponible = js_sys::Reflect::get(&result, &"revenu_disponible".into())
        .expect("revenu_disponible should be present");
    assert!(revenu_disponible.as_f64().is_some(), "revenu_disponible should be a number");

    // With all stubs returning 0.0, revenu_disponible = revenu_fiscal (50000.0)
    // minus all taxes (0.0) plus all aides (0.0) = 50000.0
    let rd_val = revenu_disponible.as_f64().unwrap();
    assert!((rd_val - 50000.0).abs() < 1e-6,
        "revenu_disponible should be ~50000.0 with all stubs at 0, got {}", rd_val);
}

// ── Test 2: Out-of-bounds profile index returns Err ────────────────────────

#[wasm_bindgen_test]
fn test_invalid_profile_index() {
    let mut engine = MicroEngine::new(
        &valid_params_json(),
        &valid_population_json(),
    ).expect("construction should succeed");

    let params: Vec<f64> = vec![1.0; 16];

    // Profile index 999 is out of bounds (we only have 1 profile)
    let result = engine.update_and_simulate(&params, 999);
    assert!(result.is_err(), "Out-of-bounds profile index should return Err");

    let err = result.unwrap_err();
    let err_str = err.as_string().expect("Error should be a string");
    assert!(err_str.contains("hors limites") || err_str.contains("out of bounds") || err_str.contains("Index"),
        "Error message should mention bounds: '{}'", err_str);
}

// ── Test 3: Invalid profile data returns Err from constructor (D-16) ───────

#[wasm_bindgen_test]
fn test_invalid_profile_data_rejected() {
    let result = MicroEngine::new(
        &valid_params_json(),
        &invalid_population_json(),
    );
    assert!(result.is_err(), "Negative wealth profile should be rejected by D-16 validation");

    let err = result.unwrap_err();
    let err_str = err.as_string().expect("Error should be a string");
    assert!(err_str.contains("validation") || err_str.contains("Négatif") || err_str.contains("patrimoine") || err_str.contains("test-bad-wealth"),
        "Error should reference validation failure: '{}'", err_str);
}

// ── Test 4: Malformed JSON returns Err ─────────────────────────────────────

#[wasm_bindgen_test]
fn test_malformed_json_rejected() {
    let result = MicroEngine::new(
        "not valid json {{{",
        &valid_population_json(),
    );
    assert!(result.is_err(), "Malformed JSON should return Err");
}

// ── Test 5: Wrong-size params array returns Err ────────────────────────────

#[wasm_bindgen_test]
fn test_wrong_size_params_rejected() {
    let mut engine = MicroEngine::new(
        &valid_params_json(),
        &valid_population_json(),
    ).expect("construction should succeed");

    // Only 3 elements instead of 16
    let params: Vec<f64> = vec![1.0, 1.0, 1.0];

    let result = engine.update_and_simulate(&params, 0);
    assert!(result.is_err(), "Wrong-size params should return Err");

    let err = result.unwrap_err();
    let err_str = err.as_string().expect("Error should be a string");
    assert!(err_str.contains("taille") || err_str.contains("16") || err_str.contains("length"),
        "Error should reference size mismatch: '{}'", err_str);
}
