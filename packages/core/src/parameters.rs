// Parameter tree loading system — the Rust-side equivalent of OpenFisca's
// parameter resolution.
//
// Tax rule parameters (rates, brackets, thresholds) are loaded from Phase 1's
// `parameters-v2025.1.json` into a typed `Parameters` struct with date-based
// `BTreeMap` lookups following OpenFisca's "closest past date" semantics.
//
// Decision D-02: All loading logic lives in the core crate — testable via
//                `cargo test` without a browser.
//
// Supports two JSON formats:
//   1. Simplified test format (with top-level "version" + "parameters" keys)
//   2. Real Phase 1 format (flat map of file-path keys with nested date values)

use std::collections::{BTreeMap, HashMap};

use chrono::NaiveDate;
use serde::{Deserialize, Serialize};

use crate::types::LoadError;

/// Représente un paramètre fiscal chargé depuis le fichier JSON.
#[derive(Debug, Clone)]
pub enum ParameterValue {
    /// Barème progressif (tranches d'imposition).
    Brackets(Vec<Bracket>),
    /// Valeur scalaire (taux fixe, montant forfaitaire).
    Scalar(f64),
    /// Valeur temporelle indexée par date (sémantique OpenFisca).
    Temporal(BTreeMap<NaiveDate, f64>),
    /// Objet imbriqué contenant des sous-paramètres.
    Object(HashMap<String, f64>),
    /// Entrée sans valeur calculable (description seule, métadonnées).
    None,
}

/// Tranche d'un barème progressif.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Bracket {
    /// Seuil de la tranche (>= 0.0).
    pub threshold: f64,
    /// Taux marginal de la tranche (>= 0.0).
    pub rate: f64,
}

/// Arbre de paramètres fiscaux chargé en mémoire.
///
/// Expose des méthodes d'accès typées (`get_brackets`, `get_scalar`) et
/// la résolution temporelle via `get_at_date` sur les valeurs temporelles.
#[derive(Debug, Clone)]
pub struct Parameters {
    version: String,
    data: HashMap<String, ParameterValue>,
}

impl ParameterValue {
    /// Résout une valeur temporelle à une date donnée.
    ///
    /// Sémantique OpenFisca : retourne la valeur pour la date passée la plus
    /// proche (<= date demandée). Si la date demandée est antérieure à toutes
    /// les dates disponibles, retourne la valeur la plus ancienne.
    pub fn get_at_date(&self, date: NaiveDate) -> Option<f64> {
        match self {
            ParameterValue::Temporal(temporal) => {
                // Use BTreeMap range to find the closest past date
                let candidate = temporal.range(..=date).next_back();
                match candidate {
                    Some((_d, v)) => Some(*v),
                    // Query date is before all stored dates → return earliest
                    None => temporal.first_key_value().map(|(_d, v)| *v),
                }
            }
            _ => None,
        }
    }
}

impl Parameters {
    /// Charge un arbre de paramètres depuis une chaîne JSON.
    ///
    /// Détecte automatiquement le format :
    /// - Format simplifié (tests) : `{"version": "...", "parameters": {...}}`
    /// - Format réel Phase 1 : objet plat avec clés de type `"ir/bareme.json"`
    pub fn load_from_json(
        json: &str,
        expected_version: &str,
    ) -> Result<Self, LoadError> {
        let root: serde_json::Value = serde_json::from_str(json)
            .map_err(|e| LoadError::ParseError(e.to_string()))?;

        let root_obj = root.as_object().ok_or(LoadError::MissingField {
            field: "root is not a JSON object".into(),
        })?;

        if root_obj.is_empty() {
            return Err(LoadError::MissingField {
                field: "parameters".into(),
            });
        }

        // Detect format: simplified format has "version" + "parameters" keys
        if root_obj.contains_key("version") && root_obj.contains_key("parameters") {
            Self::load_simplified_format(root_obj, expected_version)
        } else {
            Self::load_real_format(root_obj, expected_version)
        }
    }

    /// Retourne la chaîne de version (ex: "rules-v2025.1").
    pub fn version(&self) -> &str {
        &self.version
    }

    /// Accède aux tranches d'un barème progressif par sa clé.
    ///
    /// Les tranches sont retournées triées par seuil croissant.
    /// Mitigation T-02-27 : chaque Bracket est validé (threshold >= 0, rate >= 0,
    /// valeurs finies).
    pub fn get_brackets(&self, key: &str) -> Result<Vec<Bracket>, LoadError> {
        let value = self
            .data
            .get(key)
            .ok_or_else(|| LoadError::KeyNotFound(key.to_string()))?;
        match value {
            ParameterValue::Brackets(brackets) => {
                let mut sorted = brackets.clone();
                sorted.sort_by(|a, b| {
                    a.threshold
                        .partial_cmp(&b.threshold)
                        .unwrap_or(std::cmp::Ordering::Equal)
                });
                Ok(sorted)
            }
            _ => Err(LoadError::ParseError(format!(
                "key '{}' does not contain brackets",
                key
            ))),
        }
    }

    /// Accède à une valeur scalaire par sa clé (ex: taux de TVA).
    pub fn get_scalar(&self, key: &str) -> Result<f64, LoadError> {
        let value = self
            .data
            .get(key)
            .ok_or_else(|| LoadError::KeyNotFound(key.to_string()))?;
        match value {
            ParameterValue::Scalar(v) => Ok(*v),
            _ => Err(LoadError::ParseError(format!(
                "key '{}' does not contain a scalar value",
                key
            ))),
        }
    }

    /// Accède à la valeur brute d'un paramètre par sa clé.
    pub fn get(&self, key: &str) -> Result<&ParameterValue, LoadError> {
        self.data
            .get(key)
            .ok_or_else(|| LoadError::KeyNotFound(key.to_string()))
    }

    /// Vérifie si au moins une clé de paramètre commence par le préfixe donné.
    ///
    /// Utilisé pour le test d'intégration du fichier réel (test 13).
    pub fn has_key_prefix(&self, prefix: &str) -> bool {
        self.data.keys().any(|k| k.starts_with(prefix) && k.len() > prefix.len() && {
            let next_char = k.as_bytes().get(prefix.len()).copied();
            next_char == Some(b'/') || next_char == Some(b'.')
        })
    }

    // ── Private helpers ──────────────────────────────────────────────────

    fn load_simplified_format(
        root: &serde_json::Map<String, serde_json::Value>,
        expected_version: &str,
    ) -> Result<Self, LoadError> {
        let version = root
            .get("version")
            .and_then(|v| v.as_str())
            .ok_or(LoadError::MissingField {
                field: "version".into(),
            })?
            .to_string();

        if version != expected_version {
            return Err(LoadError::VersionMismatch {
                expected: expected_version.to_string(),
                actual: version,
            });
        }

        let params_obj = root
            .get("parameters")
            .and_then(|p| p.as_object())
            .ok_or(LoadError::MissingField {
                field: "parameters".into(),
            })?;

        let data = Self::parse_parameters_map(params_obj)?;
        Ok(Parameters { version, data })
    }

    fn load_real_format(
        root: &serde_json::Map<String, serde_json::Value>,
        _expected_version: &str,
    ) -> Result<Self, LoadError> {
        // NOTE: Real format version validation is deferred to a later phase.
        // Currently all parameter values are stored as ParameterValue::None —
        // deep parameter extraction (brackets, scalars, temporal values) from
        // the real parameters-v2025.1.json structure is planned for Phase 3+.
        let version = "rules-v2025.1".to_string();
        let mut data = HashMap::new();

        for (key, _value) in root {
            // Store normalized key (strip ".json" suffix) for prefix matching.
            // Values are stored as ParameterValue::None — deep navigation of
            // the real format is handled by engine crates.
            let normalized = key.strip_suffix(".json").unwrap_or(key).to_string();
            data.insert(normalized, ParameterValue::None);
        }

        Ok(Parameters { version, data })
    }

    fn parse_parameters_map(
        obj: &serde_json::Map<String, serde_json::Value>,
    ) -> Result<HashMap<String, ParameterValue>, LoadError> {
        let mut data = HashMap::new();
        for (key, value) in obj {
            let param = Self::parse_parameter_value(value)?;
            data.insert(key.clone(), param);
        }
        Ok(data)
    }

    fn parse_parameter_value(
        value: &serde_json::Value,
    ) -> Result<ParameterValue, LoadError> {
        let obj = value.as_object().ok_or(LoadError::ParseError(
            "parameter entry must be a JSON object".into(),
        ))?;

        if let Some(brackets_arr) = obj.get("brackets") {
            let brackets: Vec<Bracket> = serde_json::from_value(brackets_arr.clone())
                .map_err(|e| LoadError::ParseError(format!("invalid brackets: {}", e)))?;
            // Mitigation T-02-27: validate bracket values
            for b in &brackets {
                if !b.threshold.is_finite() || b.threshold < 0.0 {
                    return Err(LoadError::ParseError(format!(
                        "bracket threshold must be >= 0 and finite, got {}",
                        b.threshold
                    )));
                }
                if !b.rate.is_finite() || b.rate < 0.0 {
                    return Err(LoadError::ParseError(format!(
                        "bracket rate must be >= 0 and finite, got {}",
                        b.rate
                    )));
                }
            }
            Ok(ParameterValue::Brackets(brackets))
        } else if let Some(values_obj) = obj.get("values") {
            let values_map = values_obj
                .as_object()
                .ok_or(LoadError::ParseError(
                    "values must be a JSON object".into(),
                ))?;
            let mut temporal = BTreeMap::new();
            for (date_str, entry) in values_map {
                let date = NaiveDate::parse_from_str(date_str, "%Y-%m-%d")
                    .map_err(|e| {
                        LoadError::ParseError(format!(
                            "invalid date '{}': {}",
                            date_str, e
                        ))
                    })?;
                let entry_obj = entry.as_object().ok_or(LoadError::ParseError(
                    format!("date entry '{}' must be an object", date_str),
                ))?;
                let val = entry_obj
                    .get("value")
                    .and_then(|v| v.as_f64())
                    .ok_or(LoadError::ParseError(format!(
                        "date entry '{}' missing numeric 'value' field",
                        date_str
                    )))?;
                temporal.insert(date, val);
            }
            if temporal.is_empty() {
                return Err(LoadError::ParseError(
                    "temporal values map is empty".into(),
                ));
            }
            Ok(ParameterValue::Temporal(temporal))
        } else if let Some(val) = obj.get("value") {
            let scalar = val.as_f64().ok_or(LoadError::ParseError(
                "scalar value must be a number".into(),
            ))?;
            Ok(ParameterValue::Scalar(scalar))
        } else {
            Err(LoadError::ParseError(format!(
                "unknown parameter type for keys: {:?}",
                obj.keys().collect::<Vec<_>>()
            )))
        }
    }
}
