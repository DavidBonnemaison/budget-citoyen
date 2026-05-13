"""Candidate reform scenario definitions using the openfisca-france reform API.

Defines at least 3 scenarios — status quo, fiscal expansion, and fiscal
consolidation — each as a Reform subclass that modifies openfisca-france
parameter values.

Each scenario includes:
  - id: unique identifier for the scenario (e.g., "baseline-2025")
  - name: human-readable French name
  - description: prose description of the reform
  - parameter_overrides: mapping of openfisca parameter paths → new values
  - build_reform(): constructs the openfisca-france Reform instance

Per D-22: scenarios-v2025.1 is the canonical scenario set, version-locked
to the 2025 reference year.
"""

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

    Returns at least 3 scenarios:
      1. baseline-2025: Status quo — current law, no parameter changes.
      2. expansion-2025: Fiscal expansion — reduced income tax + increased
         social benefits.
      3. consolidation-2025: Fiscal consolidation — increased VAT + reduced
         spending (lowered social benefit thresholds).

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
                        {"rate": 0.405, "threshold": 180294},  # 40.5% (was 45%)
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
    ]
