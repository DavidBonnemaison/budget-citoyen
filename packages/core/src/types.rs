// Core types for Budget Citoyen microsimulation.
//
// Contains the Profile struct (the universal data contract consumed by the
// micro engine, macro engine, and Web Worker boundary), supporting enumerations,
// validation error types, and output structs for both micro and macro simulation
// results.
//
// Decision D-02: All types live in the core crate with zero WASM dependencies.
// Decision D-16: Every Profile must pass validate() before consumption.

use serde::{Deserialize, Serialize};

// ── Enumerations ────────────────────────────────────────────────────────────

/// Situation familiale du foyer fiscal (quotient familial).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum SituationFamiliale {
    Celibataire,
    Marie,
    Pacse,
    Veuf,
    Divorce,
}

/// Type d'activité professionnelle du déclarant principal.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub enum TypeActivite {
    Salarie,
    Independant,
    Retraite,
    Chomeur,
    Inactif,
}

// ── Profile ─────────────────────────────────────────────────────────────────

/// Représentation plate (D-13) d'un foyer fiscal OpenFisca.
///
/// Les champs cross-entités (Individu, Famille, FoyerFiscal, Ménage) sont
/// résolus par le générateur de code (D-15). Cette structure contient les
/// champs fondamentaux nécessaires à tous les calculs fiscaux.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Profile {
    /// Identifiant unique issu de la population synthétique.
    pub profile_id: String,
    /// Âge du déclarant principal (0-120).
    pub age: u8,
    /// Patrimoine total (immobilier + financier), >= 0.
    pub patrimoine: f64,
    /// Revenu fiscal de référence, >= 0.
    pub revenu_fiscal: f64,
    /// Situation familiale pour le quotient familial.
    pub situation_familiale: SituationFamiliale,
    /// Nombre de parts fiscales (>= 1.0, typiquement 1.0-5.0).
    pub nombre_parts: f64,
    /// Type d'activité professionnelle.
    pub type_activite: TypeActivite,
    /// Nombre d'enfants à charge (0-20).
    pub nb_enfants: u8,
}

// ── Validation ──────────────────────────────────────────────────────────────

/// Erreur de validation d'un profil (D-16).
///
/// Chaque variante correspond à une règle de validation distincte.
/// Les messages d'erreur sont en français pour correspondre à la langue du projet.
/// T-02-24 : seules les catégories d'échec sont exposées, jamais les données brutes.
/// T-02-25 : MissingField enregistre le nom du champ (structuré), pas la valeur.
#[derive(thiserror::Error, Debug, PartialEq)]
pub enum LoadError {
    /// L'âge dépasse la limite maximale de 120 ans.
    #[error("Âge invalide : {0} (doit être compris entre 0 et 120)")]
    InvalidAge(u8),

    /// Le patrimoine est négatif.
    #[error("Patrimoine négatif : {0}")]
    NegativeWealth(f64),

    /// Le revenu fiscal est négatif.
    #[error("Revenu fiscal négatif : {0}")]
    NegativeIncome(f64),

    /// Le nombre de parts fiscales est inférieur à 1.0.
    #[error("Nombre de parts invalide : {0} (doit être >= 1.0)")]
    InvalidParts(f64),

    /// Un champ obligatoire est absent lors de la désérialisation.
    #[error("Champ obligatoire manquant : {field}")]
    MissingField { field: String },

    /// La version du fichier de paramètres ne correspond pas à la version attendue.
    #[error("Version mismatch: expected '{expected}', got '{actual}'")]
    VersionMismatch { expected: String, actual: String },

    /// Une clé de paramètre demandée n'existe pas dans l'arbre chargé.
    #[error("Parameter key not found: {0}")]
    KeyNotFound(String),

    /// Erreur de parsing JSON lors du chargement des paramètres.
    #[error("JSON parse error: {0}")]
    ParseError(String),
}

impl Profile {
    /// Valide que tous les champs du profil sont dans les bornes acceptables.
    ///
    /// Retourne `Ok(())` si le profil est valide, ou une variante de `LoadError`
    /// décrivant la première règle violée.
    pub fn validate(&self) -> Result<(), LoadError> {
        if self.age > 120 {
            return Err(LoadError::InvalidAge(self.age));
        }
        if self.patrimoine < 0.0 {
            return Err(LoadError::NegativeWealth(self.patrimoine));
        }
        if self.revenu_fiscal < 0.0 {
            return Err(LoadError::NegativeIncome(self.revenu_fiscal));
        }
        if self.nombre_parts < 1.0 {
            return Err(LoadError::InvalidParts(self.nombre_parts));
        }
        Ok(())
    }
}

// ── Simulation Output Types (D-10) ──────────────────────────────────────────

/// Résultat d'une simulation microéconomique pour un profil.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MicroResult {
    /// Impôt sur le revenu.
    pub ir: f64,
    /// Impôt sur les sociétés (contribution).
    pub is_contribution: f64,
    /// TVA acquittée.
    pub tva_acquittee: f64,
    /// Cotisations sociales salariales.
    pub cotisations_salariales: f64,
    /// CSG / CRDS.
    pub csg_crds: f64,
    /// Aides sociales reçues.
    pub aides: AidesResult,
    /// Revenu disponible après impôts et transferts.
    pub revenu_disponible: f64,
}

/// Détail des aides sociales perçues.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AidesResult {
    /// Revenu de Solidarité Active.
    pub rsa: f64,
    /// Aide Personnalisée au Logement.
    pub apl: f64,
    /// Allocations familiales.
    pub allocations_familiales: f64,
    /// Prime d'activité.
    pub prime_activite: f64,
    /// Allocation aux Adultes Handicapés.
    pub aah: f64,
    /// Allocation de Solidarité aux Personnes Âgées.
    pub aspa: f64,
    /// Total des aides.
    pub total: f64,
}

/// Résultat d'une projection macroéconomique.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct MacroResult {
    /// Trajectoire du déficit public (points de PIB par année).
    pub deficit_trajectory: Vec<f64>,
    /// Trajectoire de la dette publique (% du PIB par année).
    pub debt_trajectory: Vec<f64>,
    /// Trajectoire de la croissance du PIB (% par année).
    pub gdp_growth_trajectory: Vec<f64>,
    /// Trajectoire de l'emploi (milliers par année).
    pub employment_trajectory: Vec<f64>,
    /// Indique si les paramètres de la simulation sortent du domaine de
    /// validité de la matrice des chocs.
    pub is_out_of_bounds: bool,
    /// Message d'avertissement optionnel lorsque is_out_of_bounds est true.
    pub warning_message: Option<String>,
}
