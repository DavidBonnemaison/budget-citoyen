// Profile validation property-based tests.
// RED phase: these tests MUST fail because the types module and Profile
// struct do not exist yet.

use budget_citoyen_core::types::{LoadError, Profile, SituationFamiliale, TypeActivite};
use proptest::prelude::*;

// Helper to create a valid Profile for tests
fn valid_profile(age: u8, patrimoine: f64, revenu_fiscal: f64, nombre_parts: f64) -> Profile {
    Profile {
        profile_id: format!("test-{}", age),
        age,
        patrimoine,
        revenu_fiscal,
        situation_familiale: SituationFamiliale::Celibataire,
        nombre_parts,
        type_activite: TypeActivite::Salarie,
        nb_enfants: 0,
    }
}

// --- Test 1: All profiles with valid fields pass validate() ---
proptest! {
    #[test]
    fn valid_profiles_pass_validation(
        age in 0u8..=120u8,
        patrimoine in (0.0f64..1_000_000_000.0),
        revenu_fiscal in (0.0f64..1_000_000_000.0),
        nombre_parts in (1.0f64..5.0),
    ) {
        let profile = valid_profile(age, patrimoine, revenu_fiscal, nombre_parts);
        prop_assert!(profile.validate().is_ok());
    }

    // --- Test 2: Age > 120 must fail ---
    #[test]
    fn age_above_120_fails_validation(
        age in 121u8..u8::MAX,
        patrimoine in (0.0f64..100_000.0),
        revenu_fiscal in (0.0f64..100_000.0),
        nombre_parts in (1.0f64..5.0),
    ) {
        let profile = valid_profile(age, patrimoine, revenu_fiscal, nombre_parts);
        let result = profile.validate();
        prop_assert!(result.is_err());
        match result.unwrap_err() {
            LoadError::InvalidAge(got) => prop_assert_eq!(got, age),
            _ => prop_assert!(false, "expected InvalidAge, got different error"),
        }
    }

    // --- Test 3: Negative wealth fails ---
    #[test]
    fn negative_wealth_fails_validation(
        age in 0u8..=120u8,
        patrimoine in (f64::MIN..0.0),
        revenu_fiscal in (0.0f64..100_000.0),
        nombre_parts in (1.0f64..5.0),
    ) {
        let profile = valid_profile(age, patrimoine, revenu_fiscal, nombre_parts);
        let result = profile.validate();
        prop_assert!(result.is_err());
        match result.unwrap_err() {
            LoadError::NegativeWealth(got) => prop_assert_eq!(got, patrimoine),
            _ => prop_assert!(false, "expected NegativeWealth, got different error"),
        }
    }

    // --- Test 4: Negative income fails ---
    #[test]
    fn negative_income_fails_validation(
        age in 0u8..=120u8,
        patrimoine in (0.0f64..100_000.0),
        revenu_fiscal in (f64::MIN..0.0),
        nombre_parts in (1.0f64..5.0),
    ) {
        let profile = valid_profile(age, patrimoine, revenu_fiscal, nombre_parts);
        let result = profile.validate();
        prop_assert!(result.is_err());
        match result.unwrap_err() {
            LoadError::NegativeIncome(got) => prop_assert_eq!(got, revenu_fiscal),
            _ => prop_assert!(false, "expected NegativeIncome, got different error"),
        }
    }

    // --- Test 5: Invalid quotient familial parts fails ---
    #[test]
    fn invalid_parts_fails_validation(
        age in 0u8..=120u8,
        patrimoine in (0.0f64..100_000.0),
        revenu_fiscal in (0.0f64..100_000.0),
        nombre_parts in (f64::MIN..1.0),
    ) {
        let profile = valid_profile(age, patrimoine, revenu_fiscal, nombre_parts);
        let result = profile.validate();
        prop_assert!(result.is_err());
        match result.unwrap_err() {
            LoadError::InvalidParts(got) => prop_assert_eq!(got, nombre_parts),
            _ => prop_assert!(false, "expected InvalidParts, got different error"),
        }
    }

    // --- Test 6: Round-trip serde serialization ---
    #[test]
    fn profile_serde_roundtrip(
        age in 0u8..=120u8,
        patrimoine in (0.0f64..1_000_000_000.0),
        revenu_fiscal in (0.0f64..1_000_000_000.0),
        nombre_parts in (1.0f64..5.0),
    ) {
        let profile = valid_profile(age, patrimoine, revenu_fiscal, nombre_parts);
        let json = serde_json::to_string(&profile).unwrap();
        let deserialized: Profile = serde_json::from_str(&json).unwrap();
        prop_assert_eq!(profile.profile_id, deserialized.profile_id);
        prop_assert_eq!(profile.age, deserialized.age);
        // Use relative tolerance for f64 round-trip: serde_json serializes
        // f64 as text with limited precision; large values may differ by
        // more than absolute epsilon.
        prop_assert!(
            (profile.patrimoine - deserialized.patrimoine).abs()
                <= f64::EPSILON * profile.patrimoine.abs().max(1.0) * 10.0
        );
        prop_assert!(
            (profile.revenu_fiscal - deserialized.revenu_fiscal).abs()
                <= f64::EPSILON * profile.revenu_fiscal.abs().max(1.0) * 10.0
        );
        prop_assert!(
            (profile.nombre_parts - deserialized.nombre_parts).abs()
                <= f64::EPSILON * profile.nombre_parts.abs().max(1.0) * 10.0
        );
        prop_assert_eq!(profile.nb_enfants, deserialized.nb_enfants);
    }
}
