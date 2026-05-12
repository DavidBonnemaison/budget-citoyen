"""Canonical household profiles for bilingual validation (D-12).

Defines 16 edge-case household profiles covering all socio-fiscal situations
required for validating the microsimulation engine against openfisca-france
and the impots.gouv.fr official simulator.

Each profile includes:
  - Demographic data (situation familiale, children, residence zone)
  - Income streams (salaries, pensions, self-employed, rental)
  - Assets (real estate, financial)
  - Expected results stub (to be filled from impots.gouv.fr validation)

Per D-12: 10-20 profiles covering single, couple, families, retirees,
self-employed, multi-property households.
"""

from typing import Any, Dict, List

CANONICAL_PROFILES: List[Dict[str, Any]] = [
    # ── Single individuals ──────────────────────────────────────────
    {
        "name": "celibataire_smic",
        "description": "Célibataire au SMIC, sans patrimoine — référence de base pour le bas de l'échelle des revenus",
        "situation_familiale": "celibataire",
        "nb_enfants": 0,
        "revenus": {
            "salaires": [18801.0],  # SMIC annuel brut 2025 (≈1 567 €/mois × 12)
            "pensions": [],
            "bnc": [],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 0.0,
            "financier": 0.0,
        },
        "zone_residence": "zone2",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    {
        "name": "celibataire_cadre",
        "description": "Cadre célibataire à 80K, épargne financière — test du taux marginal supérieur et CSG/CRDS",
        "situation_familiale": "celibataire",
        "nb_enfants": 0,
        "revenus": {
            "salaires": [80000.0],
            "pensions": [],
            "bnc": [],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 0.0,
            "financier": 50000.0,
        },
        "zone_residence": "zone1",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    {
        "name": "celibataire_retraite",
        "description": "Retraité célibataire, pension 24K, propriétaire de sa résidence — test de l'abattement 10 % et taxe foncière",
        "situation_familiale": "celibataire",
        "nb_enfants": 0,
        "revenus": {
            "salaires": [],
            "pensions": [24000.0],
            "bnc": [],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 200000.0,  # résidence principale
            "financier": 30000.0,
        },
        "zone_residence": "zone2",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    {
        "name": "etudiant",
        "description": "Étudiant avec job à temps partiel 8K, sans patrimoine — test exonération IR et non-assujettissement TH",
        "situation_familiale": "celibataire",
        "nb_enfants": 0,
        "revenus": {
            "salaires": [8000.0],
            "pensions": [],
            "bnc": [],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 0.0,
            "financier": 0.0,
        },
        "zone_residence": "zone2",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    {
        "name": "chomeur",
        "description": "Chômeur percevant 18K d'allocations — test du traitement fiscal des allocations chômage et RSA",
        "situation_familiale": "celibataire",
        "nb_enfants": 0,
        "revenus": {
            "salaires": [0.0],
            "pensions": [],
            "bnc": [],
            "fonciers": [],
            "allocations_chomage": 18000.0,
        },
        "patrimoine": {
            "immobilier": 0.0,
            "financier": 2000.0,
        },
        "zone_residence": "zone2",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    # ── Couples ──────────────────────────────────────────────────────
    {
        "name": "couple_bi_actif",
        "description": "Couple marié bi-actif avec 2 enfants (40K + 35K) — test quotient familial (2.5 parts)",
        "situation_familiale": "marie",
        "nb_enfants": 2,
        "revenus": {
            "salaires": [40000.0, 35000.0],
            "pensions": [],
            "bnc": [],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 250000.0,  # résidence principale
            "financier": 20000.0,
        },
        "zone_residence": "zone2",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    {
        "name": "couple_mono_actif",
        "description": "Couple marié mono-actif avec 3 enfants (55K) — test quotient familial (3 parts) et demi-part supplémentaire",
        "situation_familiale": "marie",
        "nb_enfants": 3,
        "revenus": {
            "salaires": [55000.0],
            "pensions": [],
            "bnc": [],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 220000.0,
            "financier": 15000.0,
        },
        "zone_residence": "zone3",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    {
        "name": "couple_retraite",
        "description": "Couple de retraités, pension combinée 45K — test abattement couple et décote éventuelle",
        "situation_familiale": "marie",
        "nb_enfants": 0,
        "revenus": {
            "salaires": [],
            "pensions": [25000.0, 20000.0],
            "bnc": [],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 300000.0,
            "financier": 80000.0,
        },
        "zone_residence": "zone1",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    {
        "name": "pacse_sans_enfant",
        "description": "Couple pacsé bi-actif sans enfant — test imposition commune PACS et absence de parts enfants",
        "situation_familiale": "pacse",
        "nb_enfants": 0,
        "revenus": {
            "salaires": [50000.0, 42000.0],
            "pensions": [],
            "bnc": [],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 350000.0,
            "financier": 45000.0,
        },
        "zone_residence": "zone1",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    # ── Families ─────────────────────────────────────────────────────
    {
        "name": "famille_nombreuse",
        "description": "Famille nombreuse : couple marié, 4 enfants, revenu unique 30K — test allocations familiales, RSA, prime d'activité, quotient familial",
        "situation_familiale": "marie",
        "nb_enfants": 4,
        "revenus": {
            "salaires": [30000.0],
            "pensions": [],
            "bnc": [],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 150000.0,
            "financier": 5000.0,
        },
        "zone_residence": "zone2",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    {
        "name": "famille_monoparentale",
        "description": "Parent divorcé avec 2 enfants, revenu 18K — test demi-part parent isolé, ASF, RSA majoré",
        "situation_familiale": "divorce",
        "nb_enfants": 2,
        "revenus": {
            "salaires": [18000.0],
            "pensions": [],
            "bnc": [],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 0.0,
            "financier": 1000.0,
        },
        "zone_residence": "zone3",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    # ── Self-employed ─────────────────────────────────────────────────
    {
        "name": "independant_bnc",
        "description": "Indépendant BNC (profession libérale), revenu variable 60K — test régime micro-BNC, abattement 34 %, cotisations",
        "situation_familiale": "marie",
        "nb_enfants": 1,
        "revenus": {
            "salaires": [],
            "pensions": [],
            "bnc": [60000.0],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 280000.0,
            "financier": 35000.0,
        },
        "zone_residence": "zone1",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    {
        "name": "independant_bic",
        "description": "Indépendant BIC (commerçant), revenu 45K — test régime micro-BIC, abattement 50 %, cotisations",
        "situation_familiale": "celibataire",
        "nb_enfants": 0,
        "revenus": {
            "salaires": [],
            "pensions": [],
            "bnc": [],
            "fonciers": [],
            "bic": 45000.0,
        },
        "patrimoine": {
            "immobilier": 0.0,
            "financier": 20000.0,
        },
        "zone_residence": "zone2",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    # ── Asset-heavy ───────────────────────────────────────────────────
    {
        "name": "multi_proprietaire",
        "description": "Couple avec 3 propriétés (revenus fonciers + résidence principale) — test régime réel, IFI, déficit foncier",
        "situation_familiale": "marie",
        "nb_enfants": 2,
        "revenus": {
            "salaires": [70000.0, 45000.0],
            "pensions": [],
            "bnc": [],
            "fonciers": [18000.0, 12000.0],  # deux biens locatifs
        },
        "patrimoine": {
            "immobilier": 800000.0,  # résidence + 2 investissements locatifs
            "financier": 120000.0,
        },
        "zone_residence": "zone1",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    # ── Edge cases ───────────────────────────────────────────────────
    {
        "name": "etranger_resident",
        "description": "Résident fiscal non-citoyen — test résidence fiscale, convention bilatérale, pas de différence théorique avec citoyen",
        "situation_familiale": "marie",
        "nb_enfants": 1,
        "revenus": {
            "salaires": [55000.0, 48000.0],
            "pensions": [],
            "bnc": [],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 350000.0,
            "financier": 60000.0,
        },
        "zone_residence": "zone1",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    {
        "name": "haut_revenu",
        "description": "Très haut revenu 500K — test CEHR (contribution exceptionnelle sur les hauts revenus), taux marginal maximal",
        "situation_familiale": "marie",
        "nb_enfants": 2,
        "revenus": {
            "salaires": [500000.0],
            "pensions": [],
            "bnc": [],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 1200000.0,
            "financier": 500000.0,
        },
        "zone_residence": "zone1",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    # ── Expanded profiles (gap closure #2: +16 profiles for dimensional coverage) ──
    # ── Income stratification (threshold gaps at CEHR and IR boundaries) ─────────
    {
        "name": "fam_monoparentale_1_enfant",
        "description": "Parent isolé avec 1 enfant à charge — configuration monoparentale la plus courante en France, test 1.5 parts QF et allocations",
        "situation_familiale": "divorce",
        "nb_enfants": 1,
        "revenus": {
            "salaires": [22000.0],
            "pensions": [],
            "bnc": [],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 0.0,
            "financier": 2000.0,
        },
        "zone_residence": "zone2",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    {
        "name": "celibataire_250k_cehr",
        "description": "Seuil exact CEHR 3% célibataire — test déclenchement contribution exceptionnelle hauts revenus (D-12)",
        "situation_familiale": "celibataire",
        "nb_enfants": 0,
        "revenus": {
            "salaires": [250000.0],
            "pensions": [],
            "bnc": [],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 500000.0,
            "financier": 200000.0,
        },
        "zone_residence": "zone1",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    {
        "name": "couple_1_enfant",
        "description": "Couple bi-actif avec 1 enfant — test 2.5 parts QF, plafonnement QF non déclenché",
        "situation_familiale": "marie",
        "nb_enfants": 1,
        "revenus": {
            "salaires": [45000.0, 35000.0],
            "pensions": [],
            "bnc": [],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 280000.0,
            "financier": 25000.0,
        },
        "zone_residence": "zone2",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    {
        "name": "couple_500k_cehr",
        "description": "Seuil exact CEHR 4% couple — test plafonnement QF et taux marginal maximal couple",
        "situation_familiale": "marie",
        "nb_enfants": 0,
        "revenus": {
            "salaires": [250000.0, 250000.0],
            "pensions": [],
            "bnc": [],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 800000.0,
            "financier": 400000.0,
        },
        "zone_residence": "zone1",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    # ── Zone residence (zone3 coverage at multiple income points) ──────────────
    {
        "name": "celibataire_smic_zone3",
        "description": "SMIC en zone détendue — test différentiel APL zone3 vs zone2, taux d'effort logement",
        "situation_familiale": "celibataire",
        "nb_enfants": 0,
        "revenus": {
            "salaires": [18801.0],
            "pensions": [],
            "bnc": [],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 0.0,
            "financier": 0.0,
        },
        "zone_residence": "zone3",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    {
        "name": "retraite_modeste_zone3",
        "description": "Petite retraite en zone3 — test ASPA éligibilité, taxe foncière modeste, exonération TH",
        "situation_familiale": "celibataire",
        "nb_enfants": 0,
        "revenus": {
            "salaires": [],
            "pensions": [15000.0],
            "bnc": [],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 120000.0,
            "financier": 8000.0,
        },
        "zone_residence": "zone3",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    {
        "name": "independant_bic_zone3",
        "description": "Commerçant en zone rurale — test cotisations minimales, différentiel CFE zone3, micro-BIC",
        "situation_familiale": "celibataire",
        "nb_enfants": 0,
        "revenus": {
            "salaires": [],
            "pensions": [],
            "bnc": [],
            "fonciers": [],
            "bic": 35000.0,
        },
        "patrimoine": {
            "immobilier": 80000.0,
            "financier": 15000.0,
        },
        "zone_residence": "zone3",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    # ── Asset profiles (IFI/big wealth, pure financial wealth) ─────────────────
    {
        "name": "rentier_foncier",
        "description": "Gros patrimoine immobilier locatif — test IFI, revenus fonciers au réel, déficit foncier imputation",
        "situation_familiale": "marie",
        "nb_enfants": 1,
        "revenus": {
            "salaires": [70000.0],
            "pensions": [],
            "bnc": [],
            "fonciers": [25000.0, 15000.0, 10000.0],
        },
        "patrimoine": {
            "immobilier": 1500000.0,
            "financier": 150000.0,
        },
        "zone_residence": "zone1",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    {
        "name": "jeune_patrimoine_financier",
        "description": "Jeune cadre avec patrimoine financier uniquement — test flat tax (30% PFU), prélèvements sociaux sur revenus du capital",
        "situation_familiale": "celibataire",
        "nb_enfants": 0,
        "revenus": {
            "salaires": [50000.0],
            "pensions": [],
            "bnc": [],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 0.0,
            "financier": 200000.0,
        },
        "zone_residence": "zone1",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    # ── Profession types (agricole, micro-entrepreneur) ─────────────────────────
    {
        "name": "agriculteur_zone3",
        "description": "Exploitant agricole — test régime BA (bénéfice agricole), cotisations MSA, moyenne triennale",
        "situation_familiale": "celibataire",
        "nb_enfants": 0,
        "revenus": {
            "salaires": [],
            "pensions": [],
            "bnc": [],
            "fonciers": [],
            "benefice_agricole": [28000.0],
        },
        "patrimoine": {
            "immobilier": 180000.0,
            "financier": 12000.0,
        },
        "zone_residence": "zone3",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    {
        "name": "auto_entrepreneur",
        "description": "Micro-entrepreneur — test versement libératoire IR, micro-social, chiffre d'affaires vs bénéfice",
        "situation_familiale": "celibataire",
        "nb_enfants": 0,
        "revenus": {
            "salaires": [],
            "pensions": [],
            "bnc": [],
            "fonciers": [],
            "micro_bic": 25000.0,
            "versement_liberatoire": True,
        },
        "patrimoine": {
            "immobilier": 0.0,
            "financier": 5000.0,
        },
        "zone_residence": "zone2",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    # ── Social benefit edge cases ─────────────────────────────────────────────
    {
        "name": "handicape_aah",
        "description": "Bénéficiaire AAH à taux plein — test allocation adulte handicapé, couverture santé solidaire, exonération taxe habitation",
        "situation_familiale": "celibataire",
        "nb_enfants": 0,
        "revenus": {
            "salaires": [0.0],
            "pensions": [0.0],
            "bnc": [],
            "fonciers": [],
            "allocations_chomage": 0.0,
            "aa_h": 12192.0,
        },
        "patrimoine": {
            "immobilier": 0.0,
            "financier": 1000.0,
        },
        "zone_residence": "zone2",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    {
        "name": "senior_aspa",
        "description": "Bénéficiaire ASPA seul — test minimum vieillesse, couverture maladie universelle, récupération sur succession potentielle (ASPA = complément différentiel, ressources portées à 12 144 €)",
        "situation_familiale": "veuf",
        "nb_enfants": 0,
        "revenus": {
            "salaires": [],
            "pensions": [5000.0],
            "bnc": [],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 80000.0,
            "financier": 3000.0,
        },
        "zone_residence": "zone3",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    {
        "name": "jeune_precaire",
        "description": "Jeune en emploi partiel + chômage — test cumul salaire-ARE, prime d'activité jeunes, RSA jeune actif (< 25 ans, condition d'activité)",
        "situation_familiale": "celibataire",
        "nb_enfants": 0,
        "revenus": {
            "salaires": [10000.0],
            "pensions": [],
            "bnc": [],
            "fonciers": [],
            "allocations_chomage": 8000.0,
        },
        "patrimoine": {
            "immobilier": 0.0,
            "financier": 500.0,
        },
        "zone_residence": "zone2",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    # ── Cross-category combinations ──────────────────────────────────────────
    {
        "name": "retraite_proprietaire_modeste",
        "description": "Couple retraité propriétaire modeste — test croisé retraite × patrimoine, décote IR, exonération taxe foncière (âge)",
        "situation_familiale": "marie",
        "nb_enfants": 0,
        "revenus": {
            "salaires": [],
            "pensions": [18000.0, 12000.0],
            "bnc": [],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 200000.0,
            "financier": 30000.0,
        },
        "zone_residence": "zone2",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
    {
        "name": "independant_famille_3enfants",
        "description": "Croisé indépendant × famille nombreuse en zone détendue — test cumul allocations familiales, ARS, Paje, crédits d'impôt garde + scolarité, et cotisations minimales",
        "situation_familiale": "marie",
        "nb_enfants": 3,
        "revenus": {
            "salaires": [],
            "pensions": [],
            "bnc": [45000.0],
            "fonciers": [],
        },
        "patrimoine": {
            "immobilier": 220000.0,
            "financier": 20000.0,
        },
        "zone_residence": "zone3",
        "expected_results": {
            "impots_gouv_fr": {},
            "openfisca_reference": {},
        },
    },
]


def get_profile(name: str) -> Dict[str, Any]:
    """Retrieve a canonical profile by name.

    Args:
        name: The name of the profile to retrieve.

    Returns:
        The profile dictionary.

    Raises:
        KeyError: If the profile name is not found.
    """
    for profile in CANONICAL_PROFILES:
        if profile["name"] == name:
            return profile
    raise KeyError(f"Canonical profile not found: {name}")


def list_profile_names() -> List[str]:
    """Return the list of all canonical profile names."""
    return [p["name"] for p in CANONICAL_PROFILES]
