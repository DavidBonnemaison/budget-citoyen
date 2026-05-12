"""Bilingual validation framework for Budget Citoyen tax rules.

Validates all three Phase 1 data artifacts (tax rules, synthetic population,
shock matrix) against an openfisca-france Python reference implementation,
producing JSON test fixtures for Phase 2 cargo test / wasm-pack test consumption.

Per D-12, D-13, D-14:
  - 10-20 canonical household profiles covering all edge cases (D-12)
  - 1e-6 relative precision threshold between Python reference and WASM output (D-13)
  - JSON test fixtures export for bilingual validation in CI (D-14)

Exports:
    CANONICAL_PROFILES: List of canonical household profile dictionaries.
    run_validation: Entry point for running all validation checks.
    export_test_fixtures: Exports JSON test fixtures for Phase 2 consumption.
"""

from .canonical_profiles import CANONICAL_PROFILES
from .reference_sim import run_openfisca_reference, validate_all_profiles
from .export_fixtures import export_test_fixtures

__all__ = [
    "CANONICAL_PROFILES",
    "run_openfisca_reference",
    "validate_all_profiles",
    "export_test_fixtures",
]
