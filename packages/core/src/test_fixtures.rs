// Bilingual validation fixture loader.
//
// Parses the Phase 1 bilingual_test_fixtures.json at compile time via
// `include_str!`, deserializes fixture profiles and expected outputs,
// and provides precision comparison helpers.
//
// Decision D-02: All loading logic lives in the core crate — testable via
//                `cargo test` without a browser.
// Decision D-13: Profile struct is flat — fixture input fields map directly.
//
// Threat T-02-37 mitigation: Fixtures are embedded at compile time — runtime
// cannot swap fixtures. CI version-check gate (Plan 02-08) verifies fixture
// file hash.

use serde::Deserialize;

use crate::types::{Profile, SituationFamiliale, TypeActivite};
// MicroResult and AidesResult used in GREEN phase bilingual validation

// ── Fixture Document ─────────────────────────────────────────────────────────

/// Represents the complete bilingual test fixture document embedded at
/// compile time via include_str!.
#[derive(Debug, Deserialize)]
pub struct FixtureDoc {
    pub test_fixtures: Vec<Fixture>,
    pub reference_year: u16,
    #[serde(default)]
    pub generated_at: String,
    #[serde(default)]
    pub openfisca_version: String,
    #[serde(default)]
    pub total_fixtures: usize,
}

/// A single bilingual validation test case.
#[derive(Debug, Deserialize)]
pub struct Fixture {
    /// Unique, human-readable name (e.g., "celibataire_smic").
    pub name: String,
    /// Optional prose description of the test case.
    #[serde(default)]
    pub description: String,
    /// Household input data.
    pub input: FixtureInput,
    /// Expected computation results from OpenFisca Python reference.
    pub expected: FixtureExpected,
}

/// Household-level input for a single fixture (Phase 1 flat format).
#[derive(Debug, Deserialize)]
pub struct FixtureInput {
    pub situation_familiale: String,
    pub nb_enfants: u8,
    pub revenus: FixtureRevenus,
    pub patrimoine: FixturePatrimoine,
    pub zone_residence: String,
}

/// Revenue breakdown per income category.
#[derive(Debug, Deserialize)]
pub struct FixtureRevenus {
    #[serde(default)]
    pub salaires: Vec<f64>,
    #[serde(default)]
    pub pensions: Vec<f64>,
    #[serde(default)]
    pub bnc: Vec<f64>,
    #[serde(default)]
    pub fonciers: Vec<f64>,
}

/// Patrimoine breakdown.
#[derive(Debug, Deserialize)]
pub struct FixturePatrimoine {
    pub immobilier: f64,
    pub financier: f64,
}

/// Expected outputs from OpenFisca Python reference computation.
#[derive(Debug, Deserialize)]
pub struct FixtureExpected {
    pub ir: f64,
    pub cotisations_salariales: f64,
    pub csg_crds: f64,
    pub aides: FixtureAides,
    pub revenu_disponible: f64,
}

/// Expected aides decomposition.
#[derive(Debug, Deserialize)]
pub struct FixtureAides {
    pub rsa: f64,
    pub apl: f64,
    pub allocations_familiales: f64,
    pub prime_activite: f64,
}

// ── Precision Constants ─────────────────────────────────────────────────────

/// Bilingual validation precision threshold (D-13, ROADMAP.md success
/// criterion 1): 1e-6 relative precision.
pub const PRECISION: f64 = 1e-6;

// ── Fixture Loading ──────────────────────────────────────────────────────────

/// Loads the bilingual test fixtures at compile time via include_str!.
///
/// The fixture JSON is embedded in the binary — no runtime I/O needed.
/// This ensures that tests cannot be tampered with after compilation
/// (T-02-37 mitigation).
///
/// # Panics
///
/// Panics if the embedded JSON cannot be deserialized (compile-time data
/// integrity error).
pub fn load_fixtures() -> FixtureDoc {
    let json_str = include_str!("../../data-pipeline/dist/bilingual_test_fixtures.json");
    serde_json::from_str(json_str).expect("Failed to parse bilingual_test_fixtures.json")
}

// ── Profile Conversion ──────────────────────────────────────────────────────

/// Converts a `FixtureInput` (Phase 1 flat JSON format) into a `Profile`
/// struct (core crate type used by all engines).
///
/// # Mapping
///
/// | Fixture field               | Profile field           |
/// |-----------------------------|-------------------------|
/// | `situation_familiale`       | `situation_familiale`   |
/// | `revenus.salaires[0]` (sum) | `revenu_fiscal`         |
/// | `patrimoine.immobilier + financier` | `patrimoine`    |
/// | `nb_enfants`                | `nb_enfants`            |
/// | (derived)                   | `type_activite`         |
///
/// # Revenue calculation
///
/// Revenue is the sum of all income categories (salaires, pensions, bnc,
/// fonciers). The fixture profile is flat — all income is aggregated into
/// `revenu_fiscal`.
///
/// # Number of parts (quotient familial)
///
/// Simplified derivation from `situation_familiale` and `nb_enfants`:
/// - "celibataire" / "divorce" / "veuf": 1 + 0.5 * min(nb_enfants, 2)
/// - "marie" / "pacse": 2 + 0.5 * min(nb_enfants, 2)
pub fn profile_from_fixture(input: &FixtureInput) -> Profile {
    let total_revenu: f64 = input.revenus.salaires.iter().sum::<f64>()
        + input.revenus.pensions.iter().sum::<f64>()
        + input.revenus.bnc.iter().sum::<f64>()
        + input.revenus.fonciers.iter().sum::<f64>();

    let patrimoine = input.patrimoine.immobilier + input.patrimoine.financier;

    let situation = match input.situation_familiale.as_str() {
        "celibataire" => SituationFamiliale::Celibataire,
        "marie" | "mariee" => SituationFamiliale::Marie,
        "pacse" | "pacsee" => SituationFamiliale::Pacse,
        "veuf" | "veuve" => SituationFamiliale::Veuf,
        "divorce" | "divorcee" => SituationFamiliale::Divorce,
        _ => SituationFamiliale::Celibataire, // safe default
    };

    // Simplified quotient familial calculation
    let adult_parts: f64 = match input.situation_familiale.as_str() {
        "marie" | "mariee" | "pacse" | "pacsee" => 2.0,
        _ => 1.0,
    };
    let enfant_parts = 0.5 * (input.nb_enfants as f64).min(2.0);
    let nombre_parts = adult_parts + enfant_parts;

    // Determine activity type from income sources
    let type_activite = if !input.revenus.salaires.is_empty() {
        TypeActivite::Salarie
    } else if !input.revenus.pensions.is_empty() {
        TypeActivite::Retraite
    } else if !input.revenus.bnc.is_empty() || !input.revenus.fonciers.is_empty() {
        TypeActivite::Independant
    } else {
        TypeActivite::Inactif
    };

    Profile {
        profile_id: input.situation_familiale.clone(),
        age: 35, // simplified default; fixtures don't specify age
        patrimoine,
        revenu_fiscal: total_revenu,
        situation_familiale: situation,
        nombre_parts,
        type_activite,
        nb_enfants: input.nb_enfants,
    }
}

// ── Precision Assertion Helper ──────────────────────────────────────────────

/// Asserts that a Rust-computed value matches an OpenFisca Python reference
/// value within the precision threshold.
///
/// # Formula
///
/// `|actual - expected| < PRECISION * max(|expected|, 1.0)`
///
/// This ensures that small values are compared with an absolute tolerance of
/// at least `PRECISION` (1e-6), while larger values use a relative tolerance.
///
/// # Panics
///
/// Panics with a descriptive message if the precision threshold is exceeded.
/// The message includes the label, actual value, expected value, and the
/// computed delta.
pub fn assert_precision(actual: f64, expected: f64, label: &str) {
    let delta = (actual - expected).abs();
    let threshold = PRECISION * expected.abs().max(1.0);

    assert!(
        delta < threshold,
        "Bilingual validation failed for '{}': Rust={}, Python={}, delta={:.3e} (threshold={:.3e})",
        label,
        actual,
        expected,
        delta,
        threshold,
    );
}
