"""Candidate reform scenario definitions using the openfisca-france reform API.

Defines 14 scenarios — status quo, fiscal expansion, fiscal consolidation,
five political programs, three pedagogical scenarios, and three single-axis
variants — each as a ScenarioDefinition with openfisca-france parameter
overrides.

Each scenario includes:
  - id: unique identifier for the scenario (e.g., "baseline-2025")
  - name: human-readable French name
  - description: prose description of the reform
  - parameter_overrides: mapping of openfisca parameter paths → new values
  - build_reform(): constructs the openfisca-france Reform instance

Per D-22: scenarios-v2025.1 is the canonical scenario set, version-locked
to the 2025 reference year.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type


@dataclass
class ScenarioDefinition:
    """A fiscal reform scenario with openfisca-france parameter overrides.

    Each scenario corresponds to a combination of budget sliders for which
    microsimulation results are pre-computed in the CI pipeline.

    Attributes:
        id: Unique scenario identifier (kebab-case, e.g. "baseline-2025").
        name: Human-readable French name.
        description: Prose description of the reform and its expected effects.
        parameter_overrides: Mapping of openfisca-france parameter paths to
            new values. Paths follow the legislation hierarchy (e.g.,
            "impot_revenu.bareme").
        reform_class: The openfisca-france Reform subclass for this scenario.
    """

    id: str
    name: str
    description: str
    parameter_overrides: Dict[str, Any] = field(default_factory=dict)
    _reform_class: Optional[Type[Reform]] = field(default=None, repr=False)

    def build_reform(self):
        """Build (or return cached) openfisca-france Reform class.

        Lazily imports openfisca-france and openfisca_core.reforms to allow
        importing scenario definitions in environments where openfisca is not
        installed (e.g., linting, type-checking).

        Returns a subclass of FranceTaxBenefitSystem with this scenario's
        parameter overrides applied via the Reform.apply() mechanism.

        Returns:
            A FranceTaxBenefitSystem subclass with overridden parameters.

        Raises:
            ImportError: If openfisca-france is not installed.
        """
        from openfisca_core.reforms import Reform  # noqa: PLC0415
        from openfisca_france import FranceTaxBenefitSystem  # noqa: PLC0415

        if self._reform_class is not None:
            return self._reform_class

        overrides = dict(self.parameter_overrides)
        scenario_id = self.id

        class ScenarioReform(Reform):
            name = f"Scénario {scenario_id}"
            key = scenario_id

            def apply(self):
                for param_path, new_value in overrides.items():
                    self.modify_parameters(
                        parameter_name=param_path,
                        period="year:2025:2025",
                        new_value=new_value,
                    )

        self._reform_class = ScenarioReform(FranceTaxBenefitSystem)
        return self._reform_class


# ── Candidate Scenario Definitions ────────────────────────────────────────────
#
# Per Plan 02-11 must_haves: "At least 3 candidate scenarios defined with
# distinct reform parameter sets (status quo, expansion, consolidation)"
#
# Each scenario uses the openfisca-france reform API via ScenarioDefinition.
# The parameter paths reference the openfisca-france parameter hierarchy:
#   - impot_revenu.* : IR bareme + decote + plafonds
#   - csg.* : CSG rates
#   - prestations_sociales.* : social benefits (RSA, APL, AF, PA)
#   - tva.* : VAT rates (if available in the openfisca-france model)


def get_scenario_definitions() -> List[ScenarioDefinition]:
    """Return the list of candidate reform scenario definitions.

    Returns 14 scenarios:
      1. baseline-2025: Status quo — current law, no parameter changes.
      2. expansion-2025: Fiscal expansion — reduced income tax + increased
         social benefits.
      3. consolidation-2025: Fiscal consolidation — increased VAT + reduced
         spending.
      4-8. Five political programs (LFI/NFP, Renaissance, LR, RN, PS).
      9-11. Three pedagogical scenarios (transition écologique, revenu
         universel, équilibre budgétaire).
      12-14. Three single-axis variants (IR seul, TVA seule, dépenses seules).

    Each scenario uses the openfisca-france reform API via
    ScenarioDefinition.build_reform().

    Returns:
        List of ScenarioDefinition instances.
    """
    return [
        # ── Scenario 1: Status Quo (baseline) ──────────────────────────
        ScenarioDefinition(
            id="baseline-2025",
            name="Statut Quo — Droit en vigueur 2025",
            description=(
                "Scénario de référence: aucun changement fiscal par rapport "
                "au droit en vigueur au 1er janvier 2025. Les paramètres "
                "fiscaux (barème IR, taux de CSG, prestations sociales) "
                "conservent leurs valeurs législatives actuelles. Ce scénario "
                "sert de point de comparaison pour toutes les réformes."
            ),
            parameter_overrides={
                # No overrides — baseline uses default openfisca-france parameters
            },
        ),

        # ── Scenario 2: Fiscal Expansion ──────────────────────────────
        ScenarioDefinition(
            id="expansion-2025",
            name="Expansion Budgétaire — Baisse d'impôts & hausse des aides",
            description=(
                "Scénario expansionniste combinant une baisse de l'impôt sur "
                "le revenu (barème réduit de 10% sur toutes les tranches, "
                "décote renforcée) et une revalorisation des prestations "
                "sociales (RSA socle +5%, prime d'activité bonifiée de 10%). "
                "Impact attendu : hausse du revenu disponible des ménages "
                "modestes et moyens, creusement du déficit public à court terme."
            ),
            parameter_overrides={
                # IR: reduce all bracket rates by 10%
                "impot_revenu.bareme": {
                    "brackets": [
                        {"rate": 0.00, "threshold": 0},        # 0% (unchanged)
                        {"rate": 0.099, "threshold": 11497},   # 9.9% (was 11%)
                        {"rate": 0.27, "threshold": 29315},    # 27% (was 30%)
                        {"rate": 0.369, "threshold": 83823},   # 36.9% (was 41%)
                        {"rate": 0.405, "threshold": 180648},  # 40.5% (was 45%)
                    ]
                },
                # RSA socle majoré de 5%
                "prestations_sociales.rsa.socle": 1.05,
                # Prime d'activité bonifiée de 10%
                "prestations_sociales.prime_activite.montant_base": 1.10,
            },
        ),

        # ── Scenario 3: Fiscal Consolidation ──────────────────────────
        ScenarioDefinition(
            id="consolidation-2025",
            name="Consolidation Budgétaire — Hausse TVA & maîtrise des dépenses",
            description=(
                "Scénario de consolidation des finances publiques combinant "
                "une hausse de la TVA (taux normal porté à 22%, taux "
                "intermédiaire à 11%) et une modération des prestations "
                "sociales (allocations familiales divisées par 2 pour les "
                "ménages au-dessus du plafond intermédiaire, APL gelées). "
                "Impact attendu : réduction du déficit, baisse du pouvoir "
                "d'achat des ménages consommateurs, effet régressif sur les "
                "bas revenus."
            ),
            parameter_overrides={
                # TVA: taux normal 22% (was 20%), taux intermédiaire 11% (was 10%)
                "tva.taux_normal": 0.22,
                "tva.taux_intermediaire": 0.11,
                # Allocations familiales: coefficient de modulation (0.5 = half)
                "prestations_sociales.allocations_familiales.modulation": 0.5,
                # APL gelées: pas de revalorisation
                "prestations_sociales.apl.revalorisation": 0.0,
            },
        ),

        # ── Scenario 4: LFI/NFP — Programme fiscal 2027 ─────────────────
        ScenarioDefinition(
            id="lfi-nfp-2025",
            name="LFI/NFP — Programme fiscal 2027",
            description=(
                "Proposition LFI/NFP : refonte du barème IR (14 tranches, "
                "taux marginal 90% au-delà de 400K€ pour les couples), "
                "hausse du SMIC à 1600€ net, rétablissement d'un ISF "
                "climatique, sortie des traités de libre-échange. Transferts "
                "sociaux renforcés — RSA socle +30%, prime d'activité "
                "augmentée de 50%, APL revalorisées. Planification écologique "
                "financée par l'emprunt et la taxation du capital."
            ),
            parameter_overrides={
                "impot_revenu.bareme": {
                    "brackets": [
                        {"rate": 0.00, "threshold": 0},
                        {"rate": 0.01, "threshold": 5000},
                        {"rate": 0.05, "threshold": 10000},
                        {"rate": 0.10, "threshold": 15000},
                        {"rate": 0.15, "threshold": 25000},
                        {"rate": 0.20, "threshold": 40000},
                        {"rate": 0.30, "threshold": 60000},
                        {"rate": 0.40, "threshold": 90000},
                        {"rate": 0.50, "threshold": 130000},
                        {"rate": 0.60, "threshold": 180000},
                        {"rate": 0.70, "threshold": 250000},
                        {"rate": 0.80, "threshold": 325000},
                        {"rate": 0.85, "threshold": 400000},
                        {"rate": 0.90, "threshold": 500000},
                    ]
                },
                "prestations_sociales.rsa.socle": 1.30,
                "prestations_sociales.prime_activite.montant_base": 1.50,
                "prestations_sociales.apl.revalorisation": 1.0,
            },
        ),

        # ── Scenario 5: Renaissance — Simplification fiscale 2027 ──────
        ScenarioDefinition(
            id="renaissance-2025",
            name="Renaissance — Simplification fiscale 2027",
            description=(
                "Proposition Renaissance : simplification du barème IR "
                "(4 tranches au lieu de 5), fusion de la CSG et de l'IR "
                "dans un prélèvement unique, suppression de la CVAE "
                "résiduelle, maintien du crédit d'impôt recherche. Baisse "
                "des cotisations sociales salariales de 2 points pour les "
                "salaires jusqu'à 2,5 SMIC. Prime d'activité revalorisée "
                "de 15% pour les travailleurs à bas revenus. Stabilité "
                "globale de la pression fiscale — recentrage sur l'activité "
                "et l'innovation."
            ),
            parameter_overrides={
                "impot_revenu.bareme": {
                    "brackets": [
                        {"rate": 0.00, "threshold": 0},
                        {"rate": 0.11, "threshold": 12000},
                        {"rate": 0.30, "threshold": 50000},
                        {"rate": 0.45, "threshold": 180000},
                    ]
                },
                "prestations_sociales.prime_activite.montant_base": 1.15,
                "cotisations.scale": 0.90,
            },
        ),

        # ── Scenario 6: LR — Retour à l'équilibre budgétaire ───────────
        ScenarioDefinition(
            id="lr-2025",
            name="LR — Retour à l'équilibre budgétaire",
            description=(
                "Proposition LR : baisse de 10% des dépenses publiques hors "
                "régalien, réduction du nombre de fonctionnaires "
                "(non-remplacement d'un départ sur deux), report de l'âge "
                "légal de départ à 65 ans. Baisse de l'impôt sur les "
                "sociétés (taux normal à 20%), suppression de l'IFI "
                "(remplacé par un abattement renforcé sur la résidence "
                "principale). Allocations familiales réservées aux ménages "
                "sous 60K€ de revenus. TVA augmentée à 22% pour financer "
                "la transition énergétique."
            ),
            parameter_overrides={
                "impot_revenu.bareme": {
                    "brackets": [
                        {"rate": 0.00, "threshold": 0},
                        {"rate": 0.10, "threshold": 12000},
                        {"rate": 0.27, "threshold": 30000},
                        {"rate": 0.37, "threshold": 85000},
                        {"rate": 0.40, "threshold": 180000},
                    ]
                },
                "prestations_sociales.allocations_familiales.modulation": 0.50,
                "prestations_sociales.apl.revalorisation": 0.0,
                "tva.taux_normal": 0.22,
                "cotisations.scale": 1.0,
            },
        ),

        # ── Scenario 7: RN — Pouvoir d'achat & priorité nationale ──────
        ScenarioDefinition(
            id="rn-2025",
            name="RN — Pouvoir d'achat & priorité nationale",
            description=(
                "Proposition RN : baisse de la TVA sur les produits de "
                "première nécessité (taux réduit à 2,1% sur 100 produits "
                "essentiels), baisse de l'IR pour les ménages modestes "
                "(rehaussement des seuils de 15%), suppression de l'AME "
                "(Aide Médicale d'État). Baisse des cotisations sociales "
                "sur les bas salaires (exonération charges patronales "
                "jusqu'à 2 SMIC). Indexation des retraites sur l'inflation. "
                "Réduction de la contribution française au budget de l'UE."
            ),
            parameter_overrides={
                "impot_revenu.bareme": {
                    "brackets": [
                        {"rate": 0.00, "threshold": 0},
                        {"rate": 0.09, "threshold": 13000},
                        {"rate": 0.24, "threshold": 34000},
                        {"rate": 0.35, "threshold": 96000},
                        {"rate": 0.41, "threshold": 210000},
                    ]
                },
                "tva.taux_normal": 0.20,
                "prestations_sociales.rsa.socle": 1.0,
                "cotisations.scale": 0.85,
            },
        ),

        # ── Scenario 8: PS/Gauche sociale-démocrate ────────────────────
        ScenarioDefinition(
            id="ps-2025",
            name="PS/Gauche sociale-démocrate — Réformes structurelles",
            description=(
                "Proposition social-démocrate : réforme de la CSG (taux "
                "progressif : 0% jusqu'à 1,2 SMIC, 6,6% jusqu'à 2 SMIC, "
                "9,2% au-delà), création de 4 nouvelles tranches d'IR "
                "au-delà de 200K€ (45→50→55→60%), conditionnalité des "
                "aides aux entreprises (CIR, CII) à des engagements "
                "emploi/écologiques. Investissement massif dans la "
                "transition écologique (50Md€/an sur 5 ans) financé par "
                "un ISF climatique et un impôt européen sur les GAFA."
            ),
            parameter_overrides={
                "impot_revenu.bareme": {
                    "brackets": [
                        {"rate": 0.00, "threshold": 0},
                        {"rate": 0.11, "threshold": 11500},
                        {"rate": 0.30, "threshold": 30000},
                        {"rate": 0.41, "threshold": 85000},
                        {"rate": 0.45, "threshold": 180000},
                        {"rate": 0.50, "threshold": 250000},
                        {"rate": 0.55, "threshold": 400000},
                        {"rate": 0.60, "threshold": 800000},
                    ]
                },
                "prestations_sociales.rsa.socle": 1.15,
                "prestations_sociales.prime_activite.montant_base": 1.15,
                "prestations_sociales.apl.revalorisation": 1.0,
            },
        ),

        # ── Pedagogical Scenario 1: Transition Écologique ───────────────
        ScenarioDefinition(
            id="transition-ecologique-2025",
            name="Financement de la transition écologique",
            description=(
                "Scénario pédagogique : introduction d'une taxe carbone "
                "progressive (110€/tCO2 en 2025, +10€/an), augmentation "
                "de la TVA sur les produits carbonés (taux normal porté "
                "à 25%), et investissements verts massifs (rénovation "
                "thermique, transports publics). Les recettes nouvelles "
                "sont intégralement redistribuées aux ménages modestes "
                "via une augmentation du RSA socle (+40%) et de la prime "
                "d'activité (+30%), avec un bonus APL pour les logements "
                "rénovés. Ce scénario illustre une transition fiscalement "
                "neutre pour les bas revenus."
            ),
            parameter_overrides={
                "tva.taux_normal": 0.25,
                "prestations_sociales.rsa.socle": 1.40,
                "prestations_sociales.prime_activite.montant_base": 1.30,
                "prestations_sociales.apl.revalorisation": 1.0,
                "cotisations.scale": 1.0,
            },
        ),

        # ── Pedagogical Scenario 2: Revenu Universel ────────────────────
        ScenarioDefinition(
            id="revenu-universel-2025",
            name="Revenu universel — 800€ par mois",
            description=(
                "Scénario pédagogique : instauration d'un revenu universel "
                "mensuel de 800€ (9 600€/an) pour tout citoyen majeur, en "
                "remplacement du RSA et de la prime d'activité. Maintien "
                "des autres prestations (APL, allocations familiales) et "
                "du barème progressif de l'IR (qui s'applique désormais "
                "sur le revenu total y compris le RU, mais avec un "
                "abattement forfaitaire équivalent). Financement par une "
                "augmentation de la CSG de 9,7% à 15% et une suppression "
                "de niches fiscales. Scénario illustrant les effets d'un "
                "filet de sécurité universel."
            ),
            parameter_overrides={
                "revenu_universel.montant_mensuel": 800.00,
                "revenu_universel.remplace_aides": True,
                "cotisations.scale": 1.55,
            },
        ),

        # ── Pedagogical Scenario 3: Équilibre Budgétaire ────────────────
        ScenarioDefinition(
            id="equilibre-budgetaire-2025",
            name="Retour à l'équilibre budgétaire — 3% de déficit",
            description=(
                "Scénario pédagogique : retour à un déficit public de 3% "
                "du PIB en combinant hausses d'impôts généralisées (IR "
                "+20% sur toutes les tranches, TVA à 25%, CSG à 11%) et "
                "baisse des dépenses (RSA socle -15%, allocations "
                "familiales gelées pour tous les ménages au-dessus de "
                "40K€, APL gelées). Scénario illustrant l'effort "
                "nécessaire pour un retour rapide aux critères de "
                "Maastricht — à but pédagogique, non rattaché à un "
                "programme politique spécifique."
            ),
            parameter_overrides={
                "impot_revenu.bareme": {
                    "brackets": [
                        {"rate": 0.00, "threshold": 0},
                        {"rate": 0.132, "threshold": 11497},
                        {"rate": 0.36, "threshold": 29315},
                        {"rate": 0.492, "threshold": 83823},
                        {"rate": 0.54, "threshold": 180648},
                    ]
                },
                "tva.taux_normal": 0.25,
                "prestations_sociales.rsa.socle": 0.85,
                "prestations_sociales.allocations_familiales.modulation": 0.0,
                "prestations_sociales.apl.revalorisation": 0.0,
                "cotisations.scale": 1.13,
            },
        ),

        # ── Single-Axis Variant 1: IR seul ─────────────────────────────
        ScenarioDefinition(
            id="ir-seul-2025",
            name="Variante IR seul — Baisse de 15%",
            description=(
                "Variante isolée: seule l'impôt sur le revenu est modifié "
                "(baisse de 15% sur toutes les tranches hors tranche à "
                "0%). Tous les autres paramètres (TVA, cotisations, "
                "prestations sociales) restent au niveau du droit en "
                "vigueur 2025. Cette variante permet de remplir l'espace "
                "d'interpolation pour la dimension IR."
            ),
            parameter_overrides={
                "impot_revenu.bareme": {
                    "brackets": [
                        {"rate": 0.00, "threshold": 0},
                        {"rate": 0.0935, "threshold": 11497},
                        {"rate": 0.255, "threshold": 29315},
                        {"rate": 0.3485, "threshold": 83823},
                        {"rate": 0.3825, "threshold": 180648},
                    ]
                },
            },
        ),

        # ── Single-Axis Variant 2: TVA seule ───────────────────────────
        ScenarioDefinition(
            id="tva-seule-2025",
            name="Variante TVA seule — Hausse de 3 points",
            description=(
                "Variante isolée: seul le taux normal de TVA est modifié "
                "(passage de 20% à 23%). Tous les autres paramètres "
                "restent au droit en vigueur 2025. Cette variante remplit "
                "l'espace d'interpolation pour la dimension TVA."
            ),
            parameter_overrides={
                "tva.taux_normal": 0.23,
            },
        ),

        # ── Single-Axis Variant 3: Dépenses seules ─────────────────────
        ScenarioDefinition(
            id="depenses-seules-2025",
            name="Variante dépenses seules — Hausse de 10%",
            description=(
                "Variante isolée: seules les prestations sociales sont "
                "modifiées (hausse de 10% du RSA socle + prime "
                "d'activité). Tous les autres paramètres restent au droit "
                "en vigueur 2025. Cette variante remplit l'espace "
                "d'interpolation pour la dimension dépenses publiques. "
                "Note: la variation de dépenses publiques est partiellement "
                "capturée via les aides sociales dans le calcul micro — "
                "l'impact complet sur les dépenses de l'État est modélisé "
                "via le curseur macro."
            ),
            parameter_overrides={
                "prestations_sociales.rsa.socle": 1.10,
                "prestations_sociales.prime_activite.montant_base": 1.10,
            },
        ),
    ]
