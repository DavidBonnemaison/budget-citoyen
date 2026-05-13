"""Scenario pre-compute pipeline for Budget Citoyen.

Generates pre-computed scenario results that feed the TypeScript ScenarioCache
engine. Replaces the deprecated codegen pipeline (Plan 02-04) in the hybrid
architecture — all microsimulation computation runs here via openfisca-france
and is exported as static JSON for O(1) client-side lookups.

Architecture (Plan 02-11):
  - scenario_definitions.py: 3+ candidate reform scenarios using openfisca-france
  - precompute.py: runs openfisca-france for each scenario × profile, exports JSON
  - Output: packages/data-pipeline/dist/scenarios-v2025.1.json

Exports:
    ScenarioDefinition: Reform scenario parameter set dataclass.
    get_scenario_definitions: Returns list of candidate scenario definitions.
    precompute_scenarios: Runs pre-computation pipeline and exports JSON.
"""

from .scenario_definitions import ScenarioDefinition, get_scenario_definitions
from .precompute import precompute_scenarios

__all__ = [
    "ScenarioDefinition",
    "get_scenario_definitions",
    "precompute_scenarios",
]
