// TaxBenefitSystem — the microsimulation engine dispatcher.
//
// Owns the parameter tree and a Vec of household profiles. The
// `compute_all_taxes` method dispatches to all auto-generated formula
// functions (IR, IS, TVA, cotisations, CSG/CRDS, aides) and returns
// a structured MicroResult.
//
// Decision D-02: Core-only dependencies — no wasm_bindgen imports.
//                 All business logic testable via `cargo test`.
// Decision D-13: Profile struct is flat — formula functions operate on
//                a single Profile with no cross-entity hierarchy.
//
// Threat model mitigations:
//   T-02-34: profile_index bounds-checked before dispatch
//   T-02-35: generated code wrapped in safe fn, no unsafe in generated/
//   T-02-36: error messages describe failure type only, no data exposure

use budget_citoyen_core::types::{MicroResult, AidesResult, Profile};
use budget_citoyen_core::parameters::Parameters;
use chrono::NaiveDate;

use crate::generated;

/// Reference tax year for all computation (Phase 1 fixed year).
const REFERENCE_YEAR: i32 = 2025;

/// The microsimulation engine.
///
/// Owns the parameter tree (loaded from Phase 1 JSON) and a vector of
/// household profiles. The `compute_all_taxes` method dispatches to
/// auto-generated formula functions for each tax domain.
#[derive(Debug)]
pub struct TaxBenefitSystem {
    parameters: Parameters,
    profiles: Vec<Profile>,
}

impl TaxBenefitSystem {
    /// Creates a new TaxBenefitSystem.
    ///
    /// # Errors
    ///
    /// Returns an error message (in French) if `profiles` is empty.
    /// Parameters are accepted as-is (validation is the caller's
    /// responsibility per T-02-27).
    pub fn new(parameters: Parameters, profiles: Vec<Profile>) -> Result<Self, String> {
        if profiles.is_empty() {
            return Err("La liste des profils ne peut pas être vide".to_string());
        }
        Ok(TaxBenefitSystem {
            parameters,
            profiles,
        })
    }

    /// Computes all taxes and benefits for the profile at `profile_index`.
    ///
    /// Dispatches to auto-generated formula functions in the following order:
    /// 1. Impôt sur le Revenu (IR)
    /// 2. Impôt sur les Sociétés (IS)
    /// 3. TVA acquittée
    /// 4. Cotisations sociales salariales
    /// 5. CSG / CRDS
    /// 6. Aides sociales (RSA, APL, AF, prime d'activité, AAH, ASPA)
    ///
    /// Revenue disponible is computed as:
    ///   revenu_fiscal - ir - is_contribution - tva_acquittee
    ///   - cotisations_salariales - csg_crds + aides.total
    ///
    /// # Errors
    ///
    /// Returns an error message if `profile_index` is out of bounds
    /// (T-02-34 mitigation).
    pub fn compute_all_taxes(&self, profile_index: usize) -> Result<MicroResult, String> {
        // T-02-34: bounds-check profile_index
        if profile_index >= self.profiles.len() {
            return Err(format!(
                "Index de profil {} hors limites (max {})",
                profile_index,
                self.profiles.len().saturating_sub(1)
            ));
        }

        let profile = &self.profiles[profile_index];
        let period = NaiveDate::from_ymd_opt(REFERENCE_YEAR, 1, 1)
            .expect("REFERENCE_YEAR should produce a valid NaiveDate");

        // ── IR: Impôt sur le Revenu ─────────────────────────────────────
        let ir_brut = generated::ir::calculate_ir_brut(&self.parameters, period, profile);

        // ── IS: Impôt sur les Sociétés (contribution) ───────────────────
        // IS is computed as a flat rate on enterprise profit. Since the
        // flat Profile model does not carry enterprise data, IS defaults
        // to 0.0 in Phase 2. Full IS computation requires Phase 3/4
        // enterprise profile extensions.
        let is_contribution: f64 = 0.0;

        // ── TVA acquittée ───────────────────────────────────────────────
        // TVA is computed by generated/tva.rs. The current codegen (v1)
        // produces 0 TVA formulas — TVA module returns 0.0 as default.
        let tva_acquittee: f64 = 0.0;

        // ── Cotisations sociales salariales ─────────────────────────────
        let cotisations_salariales = generated::cotisations::calculate_cotisations_salariales(
            &self.parameters,
            period,
            profile,
        ).abs(); // Cotisations are negative in OpenFisca convention; abs for result display

        // ── CSG / CRDS ──────────────────────────────────────────────────
        let csg_deductible = generated::cotisations::calculate_csg_deductible_salaire(
            &self.parameters,
            period,
            profile,
        ).abs();

        let crds_salaire = generated::cotisations::calculate_crds_salaire(
            &self.parameters,
            period,
            profile,
        ).abs();

        let csg_crds = csg_deductible + crds_salaire;

        // ── Aides sociales ──────────────────────────────────────────────
        let rsa = generated::aides::calculate_rsa_montant(
            &self.parameters,
            period,
            profile,
        );

        let aah = generated::aides::calculate_aah_base(
            &self.parameters,
            period,
            profile,
        );

        // APL: aide_logement_R0 provides the base amount
        let apl = generated::aides::calculate_aide_logement_R0(
            &self.parameters,
            period,
            profile,
        );

        // Allocations familiales
        let af = generated::aides::calculate_af_base(
            &self.parameters,
            period,
            profile,
        );

        // Prime d'activité (PPA is in the IS module — OpenFisca classification)
        let prime_activite = generated::is::calculate_ppa_indice_du_mois_trimestre_reference(
            &self.parameters,
            period,
            profile,
        );

        // ASPA
        let aspa = generated::aides::calculate_aspa_couple(
            &self.parameters,
            period,
            profile,
        );

        let total_aides = rsa + apl + af + prime_activite + aah + aspa;

        let aides = AidesResult {
            rsa,
            apl,
            allocations_familiales: af,
            prime_activite,
            aah,
            aspa,
            total: total_aides,
        };

        // ── Revenu disponible ───────────────────────────────────────────
        let revenu_disponible = profile.revenu_fiscal
            - ir_brut
            - is_contribution
            - tva_acquittee
            - cotisations_salariales
            - csg_crds
            + total_aides;

        Ok(MicroResult {
            ir: ir_brut,
            is_contribution,
            tva_acquittee,
            cotisations_salariales,
            csg_crds,
            aides,
            revenu_disponible,
        })
    }

    /// Returns a reference to the parameters tree.
    pub fn parameters(&self) -> &Parameters {
        &self.parameters
    }

    /// Returns a reference to the profiles.
    pub fn profiles(&self) -> &[Profile] {
        &self.profiles
    }
}
