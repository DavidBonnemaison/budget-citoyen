// Bilingual validation integration tests for the fixture loader.
//
// These tests validate that bilingual_test_fixtures.json can be loaded,
// deserialized, and converted to core Profile types. The full bilingual
// computation validation (comparing Rust TaxBenefitSystem output against
// OpenFisca Python reference) lives in wasm-micro/tests/bilingual.rs.
//
// GREEN phase: All tests pass. FixtureDoc loads, profiles convert.

use budget_citoyen_core::test_fixtures::*;
use budget_citoyen_core::types::SituationFamiliale;

// ── Test 1: Fixture loading ────────────────────────────────────────────────

#[test]
fn test_load_fixtures_parses_successfully() {
    let doc = load_fixtures();
    assert!(!doc.test_fixtures.is_empty(), "Fixture document should have test fixtures");
    assert_eq!(doc.reference_year, 2025, "Reference year should be 2025");
    assert_eq!(doc.test_fixtures.len(), 32, "Should have 32 canonical fixtures");
}

// ── Test 2: Profile conversion ─────────────────────────────────────────────

#[test]
fn test_profile_from_fixture_celibataire_smic() {
    let doc = load_fixtures();
    let celib = doc.test_fixtures.iter()
        .find(|f| f.name == "celibataire_smic")
        .expect("celibataire_smic fixture should exist");
    let profile = profile_from_fixture(&celib.input);
    assert_eq!(profile.situation_familiale, SituationFamiliale::Celibataire);
    assert_eq!(profile.nb_enfants, 0);
    assert!(profile.revenu_fiscal > 0.0);
    assert!(profile.patrimoine >= 0.0);
}

// ── Test 3: All 32 fixtures convert without error ──────────────────────────

#[test]
fn test_all_fixtures_convert_to_profiles() {
    let doc = load_fixtures();
    for fixture in &doc.test_fixtures {
        let profile = profile_from_fixture(&fixture.input);
        profile.validate().expect(&format!("Profile '{}' should validate", fixture.name));
    }
}

// ── Test 4: Precision assertion helper ─────────────────────────────────────

#[test]
fn test_assert_precision_passes_for_equal_values() {
    assert_precision(1000.0, 1000.0, "exact_match");
}

#[test]
#[should_panic(expected = "Bilingual validation failed")]
fn test_assert_precision_panics_on_large_delta() {
    assert_precision(100.0, 200.0, "large_delta");
}

#[test]
fn test_assert_precision_small_tolerance() {
    assert_precision(1_000_000.0 + 0.5e-6, 1_000_000.0, "tiny_delta");
}

// ── Test 5: Fixture diversity and integrity ────────────────────────────────

#[test]
fn test_fixture_situation_familiale_diversity() {
    let doc = load_fixtures();
    let situations: std::collections::HashSet<&str> = doc.test_fixtures.iter()
        .map(|f| f.input.situation_familiale.as_str())
        .collect();
    assert!(situations.len() >= 3, "Should have diverse household types");
}

#[test]
fn test_fixture_expected_values_present() {
    let doc = load_fixtures();
    for fixture in &doc.test_fixtures {
        let exp = &fixture.expected;
        assert!(exp.ir.is_finite(), "IR should be finite for '{}'", fixture.name);
        assert!(exp.revenu_disponible.is_finite(), "Revenu disponible should be finite");
        assert!(exp.revenu_disponible > 0.0, "Revenu disponible should be positive for '{}'", fixture.name);
    }
}
