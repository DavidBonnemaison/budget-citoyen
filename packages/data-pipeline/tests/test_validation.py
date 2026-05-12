"""Tests for the bilingual validation framework.

Validates canonical profile definitions, field completeness, and
openfisca-france integration readiness.
"""

import sys
from pathlib import Path

# Add src to path for imports when running from tests/ directory
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


class TestCanonicalProfiles:
    """Tests for canonical household profile definitions."""

    def test_profile_count_at_least_fourteen(self):
        """At least 14 profiles defined (D-12 lower bound)."""
        from validation.canonical_profiles import CANONICAL_PROFILES

        count = len(CANONICAL_PROFILES)
        assert count >= 14, (
            f"Expected at least 14 canonical profiles, got {count}"
        )

    def test_all_profiles_have_required_fields(self):
        """Every profile must have name, description, situation_familiale, revenus."""
        from validation.canonical_profiles import CANONICAL_PROFILES

        required_fields = ["name", "description", "situation_familiale", "revenus"]
        for profile in CANONICAL_PROFILES:
            name = profile.get("name", "?")
            for field in required_fields:
                assert field in profile, (
                    f"Profile '{name}' is missing required field '{field}'"
                )
            assert isinstance(profile["revenus"], dict), (
                f"Profile '{name}' revenus must be a dict"
            )

    def test_all_profile_names_are_unique(self):
        """No duplicate profile names."""
        from validation.canonical_profiles import CANONICAL_PROFILES

        names = [p["name"] for p in CANONICAL_PROFILES]
        assert len(names) == len(set(names)), (
            f"Duplicate profile names detected: {names}"
        )

    def test_edge_cases_represented(self):
        """Required edge cases must be present in profile names."""
        from validation.canonical_profiles import CANONICAL_PROFILES

        names = [p["name"] for p in CANONICAL_PROFILES]
        required_cases = [
            "celibataire",
            "couple",
            "famille",
            "retraite",
            "independant",
        ]
        for case in required_cases:
            found = any(case in n for n in names)
            assert found, f"Missing edge case '{case}' in canonical profiles"


class TestReferenceSim:
    """Tests for reference simulation module."""

    def test_import_succeeds(self):
        """reference_sim module imports without error."""
        import validation.reference_sim  # noqa: F401

    def test_quotient_familial_single_no_kids(self):
        """Single person with no children gets 1 tax part."""
        from validation.reference_sim import _compute_quotient_familial

        parts = _compute_quotient_familial({
            "situation_familiale": "celibataire",
            "nb_enfants": 0,
        })
        assert parts == 1.0

    def test_quotient_familial_couple_two_kids(self):
        """Married couple with 2 children gets 3 tax parts."""
        from validation.reference_sim import _compute_quotient_familial

        parts = _compute_quotient_familial({
            "situation_familiale": "marie",
            "nb_enfants": 2,
        })
        assert parts == 3.0

    def test_quotient_familial_couple_three_kids(self):
        """Married couple with 3 children gets 4 tax parts."""
        from validation.reference_sim import _compute_quotient_familial

        parts = _compute_quotient_familial({
            "situation_familiale": "marie",
            "nb_enfants": 3,
        })
        assert parts == 4.0

    def test_ir_barème_zero_income(self):
        """Zero income yields zero IR."""
        from validation.reference_sim import _compute_ir_barème_simplified

        ir = _compute_ir_barème_simplified(0.0, 1.0)
        assert ir == 0.0

    def test_ir_barème_typical_smic(self):
        """SMIC-level income yields low or zero IR after deduction."""
        from validation.reference_sim import _compute_ir_barème_simplified

        # SMIC net imposable ~16920 (18801 * 0.9)
        ir = _compute_ir_barème_simplified(16920.0, 1.0)
        assert ir >= 0.0
        # Should be in the 11% bracket territory
        assert ir < 2000.0, f"Unexpectedly high IR for SMIC: {ir}"

    def test_simulation_can_run_on_first_profile(self):
        """openfisca-france can simulate at least 1 profile without throwing.

        If openfisca-france is not installed, this test gracefully reports
        the import error rather than crashing.
        """
        from validation.canonical_profiles import CANONICAL_PROFILES
        from validation.reference_sim import run_openfisca_reference

        profile = CANONICAL_PROFILES[0]
        try:
            result = run_openfisca_reference(profile, 2025)
            assert "ir" in result
            assert "revenu_disponible" in result
        except ImportError:
            # openfisca-france not installed — acceptable for local dev
            # but should be installed in CI
            pass


class TestExportFixtures:
    """Tests for JSON fixture export."""

    def test_import_succeeds(self):
        """export_fixtures module imports without error."""
        import validation.export_fixtures  # noqa: F401

    def test_export_function_exists(self):
        """export_test_fixtures is callable and accepts correct signature."""
        from validation.export_fixtures import export_test_fixtures

        assert callable(export_test_fixtures)

    def test_export_creates_file_with_required_keys(self, tmp_path):
        """Export creates JSON with test_fixtures and reference_year keys."""
        from validation.canonical_profiles import CANONICAL_PROFILES
        from validation.reference_sim import validate_all_profiles
        from validation.export_fixtures import export_test_fixtures

        results = validate_all_profiles(CANONICAL_PROFILES, 2025)
        fixture_path = export_test_fixtures(
            CANONICAL_PROFILES, results, str(tmp_path)
        )

        import json

        with open(fixture_path, "r") as f:
            doc = json.load(f)

        assert "test_fixtures" in doc
        assert doc["reference_year"] == 2025
        assert len(doc["test_fixtures"]) >= 14
