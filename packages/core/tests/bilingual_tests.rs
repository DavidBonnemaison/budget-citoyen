// Bilingual validation integration tests for the fixture loader.
//
// These tests validate that bilingual_test_fixtures.json can be loaded,
// deserialized, and converted to core Profile types. The full bilingual
// computation validation (comparing Rust TaxBenefitSystem output against
// OpenFisca Python reference) lives in wasm-micro/tests/bilingual.rs.
//
// RED phase: Tests 2-5 reference compute_all_taxes() which does NOT exist
//            yet — these will fail to compile, proving the RED gate.

use budget_citoyen_core::test_fixtures::*;

// ── Test 1: Fixture loading ────────────────────────────────────────────────

#[test]
fn test_load_fixtures_parses_successfully() {
    let doc = load_fixtures();
    assert!(!doc.test_fixtures.is_empty(), "Fixture document should have test fixtures");
    assert_eq!(doc.reference_year, 2025, "Reference year should be 2025");
}

// ── Test 2: Profile conversion ─────────────────────────────────────────────

#[test]
fn test_profile_from_fixture_celibataire_smic() {
    let doc = load_fixtures();
    let celib = doc.test_fixtures.iter()
        .find(|f| f.name == "celibataire_smic")
        .expect("celibataire_smic fixture should exist");

    let profile = profile_from_fixture(&celib.input);

    assert_eq!(profile.situation_familiale, budget_citoyen_core::types::SituationFamiliale::Celibataire);
    assert_eq!(profile.nb_enfants, 0);
    assert!(profile.revenu_fiscal > 0.0, "Revenu fiscal should be positive");
    assert!(profile.patrimoine >= 0.0, "Patrimoine should be non-negative");
}

// ── Test 3: All 32 fixtures convert without error ──────────────────────────

#[test]
fn test_all_fixtures_convert_to_profiles() {
    let doc = load_fixtures();
    assert_eq!(doc.test_fixtures.len(), 32, "Should have 32 canonical fixtures");

    for fixture in &doc.test_fixtures {
        let profile = profile_from_fixture(&fixture.input);
        // Basic sanity: profile must validate
        profile.validate().expect(&format!(
            "Profile '{}' should validate",
            fixture.name
        ));
    }
}

// ── Test 4: Precision assertion helper ─────────────────────────────────────

#[test]
fn test_assert_precision_passes_for_equal_values() {
    assert_precision(1000.0, 1000.0, "exact_match");
    // Should not panic
}

#[test]
#[should_panic(expected = "Bilingual validation failed")]
fn test_assert_precision_panics_on_large_delta() {
    assert_precision(100.0, 200.0, "large_delta");
}

#[test]
fn test_assert_precision_small_tolerance() {
    // Difference of 0.5e-6 should pass (within 1e-6 tolerance for value ~1M)
    assert_precision(1_000_000.0 + 0.5e-6, 1_000_000.0, "tiny_delta");
}

// ═══════════════════════════════════════════════════════════════════════════
// RED GATE: Tests below reference compute_all_taxes() which does NOT exist
// yet in the TaxBenefitSystem (system.rs not yet written). These tests MUST
// fail to compile — proving the RED gate for the TDD cycle.
// ═══════════════════════════════════════════════════════════════════════════

// RED: This import will fail — system module doesn't exist.
// Wrapped in a module that won't compile (RED phase).
// UNCOMMENT DURING GREEN PHASE: use budget_citoyen_wasm_micro::system::TaxBenefitSystem;

// ═══════════════════════════════════════════════════════════════════════════
// RED GATE: The function compute_all_taxes does NOT exist yet because
// TaxBenefitSystem (packages/wasm-micro/src/system.rs) has not been
// implemented. This test MUST fail to compile — proving the RED phase.
//
// On the GREEN phase, this test will be replaced with actual imports from
// budget_citoyen_wasm_micro::system::TaxBenefitSystem.
// ═══════════════════════════════════════════════════════════════════════════

/// RED Gate Test: Bilingual validation requires TaxBenefitSystem.
///
/// This deliberately calls a non-existent function `compute_all_taxes`.
/// The compilation error "cannot find function `compute_all_taxes`" proves
/// the TDD RED gate — the system under test does not yet exist.
///
/// In GREEN phase, this test is replaced with the actual bilingual
/// validation test that calls `TaxBenefitSystem::compute_all_taxes()`.
#[test]
fn red_gate_bilingual_validation_requires_tax_benefit_system() {
    let doc = load_fixtures();
    let fixture = &doc.test_fixtures[0];
    let _profile = profile_from_fixture(&fixture.input);

    // RED: This call WILL fail to compile — compute_all_taxes doesn't exist yet.
    // The compilation failure IS the RED gate signal.
    let _result = compute_all_taxes();
}
