// Parameter loading, bracket access, scalar access, date resolution,
// and version validation tests.
// RED phase: these tests MUST fail because the parameters module and
// Parameters struct do not exist yet.

use budget_citoyen_core::parameters::{Bracket, ParameterValue, Parameters};
use budget_citoyen_core::types::LoadError;
use chrono::NaiveDate;

// ── Helper JSON constructors ────────────────────────────────────────────────

fn valid_parameters_json() -> String {
    r#"{
        "version": "rules-v2025.1",
        "parameters": {
            "test.key": { "value": 42.0 }
        }
    }"#
    .to_string()
}

fn mismatched_version_json() -> String {
    r#"{
        "version": "rules-v2024.1",
        "parameters": {
            "test.key": { "value": 42.0 }
        }
    }"#
    .to_string()
}

fn brackets_json() -> String {
    r#"{
        "version": "rules-v2025.1",
        "parameters": {
            "ir.bareme": {
                "brackets": [
                    {"threshold": 0, "rate": 0.0},
                    {"threshold": 11497, "rate": 0.11},
                    {"threshold": 29315, "rate": 0.30},
                    {"threshold": 83823, "rate": 0.41},
                    {"threshold": 180648, "rate": 0.45}
                ]
            }
        }
    }"#
    .to_string()
}

fn scalars_json() -> String {
    r#"{
        "version": "rules-v2025.1",
        "parameters": {
            "tva.taux.normal": { "value": 0.20 },
            "tva.taux.reduit": { "value": 0.10 },
            "tva.taux.super_reduit": { "value": 0.055 },
            "tva.taux.particulier": { "value": 0.021 }
        }
    }"#
    .to_string()
}

fn temporal_json() -> String {
    r#"{
        "version": "rules-v2025.1",
        "parameters": {
            "some.temporal.param": {
                "values": {
                    "2024-01-01": { "value": 100.0 },
                    "2025-01-01": { "value": 105.0 },
                    "2026-01-01": { "value": 110.0 }
                }
            }
        }
    }"#
    .to_string()
}

// ── Test 1: Valid JSON loads successfully ───────────────────────────────────

#[test]
fn load_valid_json_returns_ok() {
    let params = Parameters::load_from_json(&valid_parameters_json(), "rules-v2025.1");
    assert!(params.is_ok(), "Expected Ok, got: {:?}", params.err());
    let params = params.unwrap();
    assert_eq!(params.version(), "rules-v2025.1");
}

// ── Test 2: Version mismatch returns error ──────────────────────────────────

#[test]
fn mismatched_version_returns_error() {
    let result = Parameters::load_from_json(&mismatched_version_json(), "rules-v2025.1");
    assert!(result.is_err());
    match result.unwrap_err() {
        LoadError::VersionMismatch { expected, actual } => {
            assert_eq!(expected, "rules-v2025.1");
            assert_eq!(actual, "rules-v2024.1");
        }
        other => panic!("Expected VersionMismatch, got: {:?}", other),
    }
}

// ── Test 3: Malformed JSON returns ParseError ───────────────────────────────

#[test]
fn malformed_json_returns_parse_error() {
    let json = r#"{"version": "rules-v2025.1", "parameters":{"#; // missing closing braces
    let result = Parameters::load_from_json(json, "rules-v2025.1");
    assert!(result.is_err());
    match result.unwrap_err() {
        LoadError::ParseError(_) => {} // expected
        other => panic!("Expected ParseError, got: {:?}", other),
    }
}

// ── Test 4: Empty JSON object returns MissingField ──────────────────────────

#[test]
fn empty_json_returns_missing_field() {
    let json = "{}";
    let result = Parameters::load_from_json(json, "rules-v2025.1");
    assert!(result.is_err());
    match result.unwrap_err() {
        LoadError::MissingField { field: _ } => {} // expected
        other => panic!("Expected MissingField, got: {:?}", other),
    }
}

// ── Test 5: version() returns correct string ────────────────────────────────

#[test]
fn version_returns_correct_string() {
    let params = Parameters::load_from_json(&valid_parameters_json(), "rules-v2025.1").unwrap();
    assert_eq!(params.version(), "rules-v2025.1");
}

// ── Test 6: get_brackets returns brackets sorted by threshold ───────────────

#[test]
fn get_brackets_returns_sorted_by_threshold() {
    let params = Parameters::load_from_json(&brackets_json(), "rules-v2025.1").unwrap();
    let brackets = params.get_brackets("ir.bareme").unwrap();
    assert_eq!(brackets.len(), 5);
    // Verify sorted by threshold ascending
    for window in brackets.windows(2) {
        assert!(
            window[0].threshold <= window[1].threshold,
            "Brackets not sorted: {} > {}",
            window[0].threshold,
            window[1].threshold
        );
    }
    assert_eq!(brackets[0].threshold, 0.0);
    assert_eq!(brackets[0].rate, 0.0);
    assert_eq!(brackets[4].threshold, 180648.0);
    assert_eq!(brackets[4].rate, 0.45);
}

// ── Test 7: get_brackets for nonexistent key returns KeyNotFound ────────────

#[test]
fn get_brackets_nonexistent_key_returns_error() {
    let params = Parameters::load_from_json(&brackets_json(), "rules-v2025.1").unwrap();
    let result = params.get_brackets("nonexistent.key");
    assert!(result.is_err());
    match result.unwrap_err() {
        LoadError::KeyNotFound(key) => {
            assert!(key.contains("nonexistent"), "Expected key in error, got: {}", key);
        }
        other => panic!("Expected KeyNotFound, got: {:?}", other),
    }
}

// ── Test 8: Each Bracket has valid threshold >= 0.0 and rate >= 0.0 ─────────

#[test]
fn brackets_have_valid_threshold_and_rate() {
    let params = Parameters::load_from_json(&brackets_json(), "rules-v2025.1").unwrap();
    let brackets = params.get_brackets("ir.bareme").unwrap();
    for bracket in &brackets {
        assert!(
            bracket.threshold >= 0.0,
            "Negative threshold: {}",
            bracket.threshold
        );
        assert!(
            bracket.rate >= 0.0,
            "Negative rate: {}",
            bracket.rate
        );
        assert!(
            bracket.threshold.is_finite(),
            "Non-finite threshold: {}",
            bracket.threshold
        );
        assert!(
            bracket.rate.is_finite(),
            "Non-finite rate: {}",
            bracket.rate
        );
    }
}

// ── Test 9: get_scalar returns correct flat rate ────────────────────────────

#[test]
fn get_scalar_returns_correct_value() {
    let params = Parameters::load_from_json(&scalars_json(), "rules-v2025.1").unwrap();
    // TVA normal rate from test data
    let tva_normal = params.get_scalar("tva.taux.normal").unwrap();
    assert!((tva_normal - 0.20).abs() < 1e-10);
    // TVA reduced rate
    let tva_reduit = params.get_scalar("tva.taux.reduit").unwrap();
    assert!((tva_reduit - 0.10).abs() < 1e-10);
}

// ── Test 10: get_scalar for nonexistent key returns error ───────────────────

#[test]
fn get_scalar_nonexistent_key_returns_error() {
    let params = Parameters::load_from_json(&scalars_json(), "rules-v2025.1").unwrap();
    let result = params.get_scalar("nonexistent.key");
    assert!(result.is_err());
    match result.unwrap_err() {
        LoadError::KeyNotFound(key) => {
            assert!(key.contains("nonexistent"), "Expected key in error, got: {}", key);
        }
        other => panic!("Expected KeyNotFound, got: {:?}", other),
    }
}

// ── Test 11: Date-based lookup returns closest-past-date value ──────────────

#[test]
fn temporal_resolution_closest_past_date() {
    let params = Parameters::load_from_json(&temporal_json(), "rules-v2025.1").unwrap();
    let param_value = params
        .get("some.temporal.param")
        .expect("Should find temporal param");

    // Query exactly on 2025-01-01 → get the 2025-01-01 value
    let date_2025 = NaiveDate::from_ymd_opt(2025, 1, 1).unwrap();
    let value = param_value
        .get_at_date(date_2025)
        .expect("Should find value for 2025-01-01");
    assert!((value - 105.0).abs() < 1e-10);

    // Query June 2025 → closest past date is still 2025-01-01 (105.0)
    let date_jun_2025 = NaiveDate::from_ymd_opt(2025, 6, 15).unwrap();
    let value = param_value
        .get_at_date(date_jun_2025)
        .expect("Should find closest past date value");
    assert!((value - 105.0).abs() < 1e-10);

    // Query 2026-01-01 → get the 2026-01-01 value
    let date_2026 = NaiveDate::from_ymd_opt(2026, 1, 1).unwrap();
    let value = param_value
        .get_at_date(date_2026)
        .expect("Should find value for 2026-01-01");
    assert!((value - 110.0).abs() < 1e-10);
}

// ── Test 12: Query before earliest date returns earliest value ──────────────

#[test]
fn temporal_before_earliest_returns_earliest() {
    let params = Parameters::load_from_json(&temporal_json(), "rules-v2025.1").unwrap();
    let param_value = params
        .get("some.temporal.param")
        .expect("Should find temporal param");

    // Query 2023-06-01 → before earliest (2024-01-01) → returns earliest (100.0)
    let date_2023 = NaiveDate::from_ymd_opt(2023, 6, 1).unwrap();
    let value = param_value
        .get_at_date(date_2023)
        .expect("Should find earliest value when querying before any date");
    assert!((value - 100.0).abs() < 1e-10);
}

// ── Test 13: Real parameters-v2025.1.json loads without error ───────────────

#[test]
fn real_parameters_file_loads() {
    let real_json =
        include_str!("../../data-pipeline/dist/parameters-v2025.1.json");
    let params = Parameters::load_from_json(real_json, "rules-v2025.1")
        .expect("Real parameters file must load without error");

    // Check that expected top-level tax domains are present
    let has_ir = params.has_key_prefix("ir");
    let has_is = params.has_key_prefix("is");
    let has_tva = params.has_key_prefix("tva");
    let has_cotisations = params.has_key_prefix("cotisations");
    let has_aides = params.has_key_prefix("aides");

    assert!(has_ir, "Expected IR parameters to be present");
    assert!(has_is, "Expected IS parameters to be present");
    assert!(has_tva, "Expected TVA parameters to be present");
    assert!(has_cotisations, "Expected cotisations parameters to be present");
    assert!(has_aides, "Expected aides parameters to be present");
}
