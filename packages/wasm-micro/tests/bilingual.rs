// Bilingual validation integration tests — WASM-engine context.
//
// These tests load the Phase 1 bilingual test fixtures, feed them through
// TaxBenefitSystem::compute_all_taxes(), and assert that Rust-computed values
// structurally match expectations. Full precision validation (≤1e-6) requires
// the generated formulas to be fully ported from OpenFisca Python.
//
// GREEN phase: TaxBenefitSystem and SimulationState are implemented.
//             Test infrastructure compiles and runs.

use budget_citoyen_core::test_fixtures;
use budget_citoyen_core::types::Profile;
use budget_citoyen_core::parameters::Parameters;
use budget_citoyen_wasm_micro::system::TaxBenefitSystem;
use budget_citoyen_wasm_micro::simulation::{SimulationState, NUM_SIMULATION_PARAMS};

/// Helper: create a minimal Parameters tree for testing.
fn test_parameters() -> Parameters {
    let json = r#"{
        "version": "test-v1",
        "parameters": {
            "impot_revenu/bareme_ir_depuis_1945/bareme": {
                "brackets": [
                    {"threshold": 10777.0, "rate": 0.0},
                    {"threshold": 27478.0, "rate": 0.11},
                    {"threshold": 78570.0, "rate": 0.30},
                    {"threshold": 168994.0, "rate": 0.41},
                    {"threshold": 999999.0, "rate": 0.45}
                ]
            }
        }
    }"#;
    Parameters::load_from_json(json, "test-v1").expect("test parameters should load")
}

/// Helper: create a Profile from the first test fixture.
fn test_profile() -> Profile {
    let doc = test_fixtures::load_fixtures();
    test_fixtures::profile_from_fixture(&doc.test_fixtures[0].input)
}

/// Helper: create a TaxBenefitSystem with one test profile.
fn test_system() -> TaxBenefitSystem {
    let params = test_parameters();
    let profile = test_profile();
    TaxBenefitSystem::new(params, vec![profile]).expect("should create system")
}

// ── Test 1: TaxBenefitSystem construction ──────────────────────────────────

#[test]
fn test_system_new_with_valid_data_succeeds() {
    let system = test_system();
    assert_eq!(system.profiles().len(), 1);
}

#[test]
fn test_system_new_with_empty_profiles_fails() {
    let params = test_parameters();
    let result = TaxBenefitSystem::new(params, vec![]);
    assert!(result.is_err());
    assert!(result.unwrap_err().contains("vide"));
}

// ── Test 2: compute_all_taxes basic behavior ──────────────────────────────

#[test]
fn test_compute_all_taxes_returns_result() {
    let system = test_system();
    let result = system.compute_all_taxes(0);
    assert!(result.is_ok(), "compute_all_taxes should succeed for valid index");
}

#[test]
fn test_compute_all_taxes_rejects_out_of_bounds() {
    let system = test_system();
    let result = system.compute_all_taxes(999);
    assert!(result.is_err());
    assert!(result.unwrap_err().contains("hors limites"));
}

#[test]
fn test_compute_all_taxes_rejects_exact_boundary() {
    let system = test_system();
    let result = system.compute_all_taxes(1); // only 1 profile (index 0)
    assert!(result.is_err());
}

// ── Test 3: MicroResult structure ─────────────────────────────────────────

#[test]
fn test_microresult_has_all_fields() {
    let system = test_system();
    let result = system.compute_all_taxes(0).unwrap();

    // All fields should be present and finite
    assert!(result.ir.is_finite());
    assert!(result.is_contribution.is_finite());
    assert!(result.tva_acquittee.is_finite());
    assert!(result.cotisations_salariales.is_finite());
    assert!(result.csg_crds.is_finite());
    assert!(result.revenu_disponible.is_finite());

    // Aides should have all sub-fields
    assert!(result.aides.rsa.is_finite());
    assert!(result.aides.apl.is_finite());
    assert!(result.aides.allocations_familiales.is_finite());
    assert!(result.aides.prime_activite.is_finite());
    assert!(result.aides.aah.is_finite());
    assert!(result.aides.aspa.is_finite());
    assert!(result.aides.total.is_finite());
}

#[test]
fn test_revenu_disponible_positive() {
    let system = test_system();
    let result = system.compute_all_taxes(0).unwrap();
    assert!(result.revenu_disponible >= 0.0, "revenu_disponible should be non-negative");
}

// ── Test 4: Bilingual fixture iteration ────────────────────────────────────

#[test]
fn test_all_fixtures_compute_without_panic() {
    let doc = test_fixtures::load_fixtures();
    let profiles: Vec<Profile> = doc.test_fixtures.iter()
        .map(|f| test_fixtures::profile_from_fixture(&f.input))
        .collect();

    let params = test_parameters();
    let system = TaxBenefitSystem::new(params, profiles).expect("should create system");

    for i in 0..doc.test_fixtures.len() {
        let result = system.compute_all_taxes(i);
        assert!(result.is_ok(), "Fixture '{}' should compute without error", doc.test_fixtures[i].name);
    }
}

// ── Test 5: SimulationState (D-09) ────────────────────────────────────────

#[test]
fn test_simulation_state_default_is_reference() {
    let state = SimulationState::new();
    let params = state.params();
    assert_eq!(params.len(), NUM_SIMULATION_PARAMS);
    for &p in params {
        assert!((p - 1.0).abs() < 1e-10, "Default params should be 1.0 (reference)");
    }
}

#[test]
fn test_simulation_state_update_exact_16_succeeds() {
    let mut state = SimulationState::new();
    let input: Vec<f64> = (0..16).map(|i| 0.5 + i as f64 * 0.05).collect();
    let result = state.update_params(&input);
    assert!(result.is_ok());
}

#[test]
fn test_simulation_state_update_wrong_length_fails() {
    let mut state = SimulationState::new();
    assert!(state.update_params(&[1.0; 15]).is_err());
    assert!(state.update_params(&[1.0; 17]).is_err());
    assert!(state.update_params(&[]).is_err());
}

#[test]
fn test_simulation_state_rejects_nan() {
    let mut state = SimulationState::new();
    let mut input = vec![1.0; 16];
    input[5] = f64::NAN;
    assert!(state.update_params(&input).is_err());
}

#[test]
fn test_simulation_state_rejects_negative() {
    let mut state = SimulationState::new();
    let mut input = vec![1.0; 16];
    input[3] = -0.1;
    assert!(state.update_params(&input).is_err());
}

#[test]
fn test_simulation_state_rejects_excessive() {
    let mut state = SimulationState::new();
    let mut input = vec![1.0; 16];
    input[0] = 200.0;
    assert!(state.update_params(&input).is_err());
}

#[test]
fn test_simulation_state_get_param() {
    let mut state = SimulationState::new();
    let input: Vec<f64> = vec![1.5; 16];
    state.update_params(&input).unwrap();

    assert!((state.get_param(5).unwrap() - 1.5).abs() < 1e-10);
    assert!(state.get_param(99).is_none());
}

// ── Test 6: Integration — compute with updated params ──────────────────────

#[test]
fn test_compute_with_updated_simulation_state() {
    let system = test_system();
    let mut state = SimulationState::new();

    // Default result
    let _default_result = system.compute_all_taxes(0).unwrap();

    // After updating state (currently stats doesn't affect TaxBenefitSystem
    // directly since formula dispatch reads from Parameters, not SimulationState.
    // Full integration in Plan 02-07 with WASM boundary.)
    let params = vec![1.0; 16];
    state.update_params(&params).unwrap();

    // State updated successfully, no panic
    assert!(state.params().len() == 16);
}
