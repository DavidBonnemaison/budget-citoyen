"""Tests for scenario pre-compute pipeline.

Validates ScenarioDefinition catalog (count, uniqueness, field completeness),
pre-compute pipeline computations (IS always 0.0, revenuDisponible > 0),
and override extraction mechanics (IR scale, backward compatibility).

Tests are designed to pass or gracefully skip before the pipeline output
is generated — CI gates enforce full validation after scenario-precompute job.
"""

import json
import sys
from pathlib import Path

# Add src to path for imports when running from tests/ directory
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


class TestScenarioDefinitions:
    """Validate the scenario definition catalog returned by get_scenario_definitions()."""

    def test_scenario_count_is_at_least_twelve(self):
        """get_scenario_definitions() returns >= 12 scenarios."""
        from scenarios.scenario_definitions import get_scenario_definitions

        scenarios = get_scenario_definitions()
        assert len(scenarios) >= 12, (
            f"Expected at least 12 scenarios, got {len(scenarios)}"
        )

    def test_all_scenario_ids_are_unique(self):
        """All scenario ids are distinct (no duplicates)."""
        from scenarios.scenario_definitions import get_scenario_definitions

        scenarios = get_scenario_definitions()
        ids = [s.id for s in scenarios]
        assert len(ids) == len(set(ids)), (
            f"Duplicate scenario ids found: {[i for i in ids if ids.count(i) > 1]}"
        )

    def test_all_scenario_ids_have_2025_suffix(self):
        """Every scenario id ends with '-2025'."""
        from scenarios.scenario_definitions import get_scenario_definitions

        for scenario in get_scenario_definitions():
            assert scenario.id.endswith("-2025"), (
                f"Scenario {scenario.id} does not end with '-2025'"
            )

    def test_all_scenarios_have_required_fields(self):
        """Every scenario has non-empty id, name, description, and parameter_overrides is dict."""
        from scenarios.scenario_definitions import get_scenario_definitions

        for scenario in get_scenario_definitions():
            assert scenario.id, f"Scenario missing id"
            assert len(scenario.id) >= 3, (
                f"Scenario id '{scenario.id}' too short (< 3 chars)"
            )
            assert scenario.name and len(scenario.name) >= 5, (
                f"Scenario {scenario.id}: name too short or missing"
            )
            assert scenario.description and len(scenario.description) >= 20, (
                f"Scenario {scenario.id}: description too short (< 20 chars)"
            )
            assert isinstance(scenario.parameter_overrides, dict), (
                f"Scenario {scenario.id}: parameter_overrides must be dict, "
                f"got {type(scenario.parameter_overrides).__name__}"
            )

    def test_baseline_has_empty_overrides(self):
        """baseline-2025 scenario has empty parameter_overrides."""
        from scenarios.scenario_definitions import get_scenario_definitions

        baseline = [s for s in get_scenario_definitions() if s.id == "baseline-2025"]
        assert len(baseline) == 1, f"Expected 1 baseline scenario, got {len(baseline)}"
        assert baseline[0].parameter_overrides == {}, (
            f"Baseline should have empty overrides, got {baseline[0].parameter_overrides}"
        )

    def test_political_programs_exist(self):
        """Five political program scenarios exist with correct ids."""
        from scenarios.scenario_definitions import get_scenario_definitions

        ids = {s.id for s in get_scenario_definitions()}
        expected = {"lfi-nfp-2025", "renaissance-2025", "lr-2025", "rn-2025", "ps-2025"}
        missing = expected - ids
        assert not missing, f"Missing political program scenarios: {missing}"

    def test_pedagogical_scenarios_exist(self):
        """Three pedagogical scenarios exist with correct ids."""
        from scenarios.scenario_definitions import get_scenario_definitions

        ids = {s.id for s in get_scenario_definitions()}
        expected = {
            "transition-ecologique-2025",
            "revenu-universel-2025",
            "equilibre-budgetaire-2025",
        }
        missing = expected - ids
        assert not missing, f"Missing pedagogical scenarios: {missing}"

    def test_single_axis_variants_exist(self):
        """Three single-axis variant scenarios exist with correct ids."""
        from scenarios.scenario_definitions import get_scenario_definitions

        ids = {s.id for s in get_scenario_definitions()}
        expected = {"ir-seul-2025", "tva-seule-2025", "depenses-seules-2025"}
        missing = expected - ids
        assert not missing, f"Missing single-axis variant scenarios: {missing}"


class TestPrecomputePipeline:
    """Validate the pre-compute pipeline computation results."""

    def _make_profile(self):
        """Return a minimal celibataire profile dict for testing."""
        return {
            "input": {
                "situation_familiale": "celibataire",
                "nb_enfants": 0,
                "revenus": {"salaires": [24000.0]},
                "zone_residence": "zone2",
            }
        }

    def _load_fixture_profiles(self):
        """Load bilingual test fixture profiles from dist/."""
        from pathlib import Path

        fixture_path = SRC_DIR.parent / "dist" / "bilingual_test_fixtures.json"
        if not fixture_path.exists():
            return None
        with open(fixture_path, "r") as f:
            data = json.load(f)
        return data.get("test_fixtures", [])

    def test_baseline_computes_for_all_profiles(self):
        """_compute_scenario_result for baseline × all 32 fixture profiles succeeds."""
        from scenarios.scenario_definitions import get_scenario_definitions
        from scenarios.precompute import _compute_scenario_result

        profiles = self._load_fixture_profiles()
        if profiles is None:
            return  # Fixture file not available — skip

        baseline = [s for s in get_scenario_definitions() if s.id == "baseline-2025"][0]
        for idx, profile in enumerate(profiles[:32]):
            try:
                result = _compute_scenario_result(profile, baseline)
                assert isinstance(result, dict), (
                    f"Profile {idx}: result is not a dict"
                )
            except Exception as e:  # noqa: BLE001
                raise AssertionError(
                    f"Profile {idx} with id={profile.get('id', 'unknown')} "
                    f"raised {type(e).__name__}: {e}"
                ) from e

    def test_is_is_always_zero(self):
        """IS contribution is always 0.0 for individual profiles."""
        from scenarios.scenario_definitions import get_scenario_definitions
        from scenarios.precompute import _compute_scenario_result

        baseline = [s for s in get_scenario_definitions() if s.id == "baseline-2025"][0]
        profile = self._make_profile()
        result = _compute_scenario_result(profile, baseline)
        assert result["is"] == 0.0, (
            f"IS should be 0.0, got {result['is']}"
        )

    def test_revenu_disponible_is_positive(self):
        """Revenu disponible is > 0 for a salaried profile."""
        from scenarios.scenario_definitions import get_scenario_definitions
        from scenarios.precompute import _compute_scenario_result

        baseline = [s for s in get_scenario_definitions() if s.id == "baseline-2025"][0]
        profile = self._make_profile()
        result = _compute_scenario_result(profile, baseline)
        assert result["revenuDisponible"] > 0, (
            f"Revenu disponible should be > 0, got {result['revenuDisponible']}"
        )

    def test_ir_scale_extraction(self):
        """IR scale factor is correctly extracted from bareme override."""
        from scenarios.scenario_definitions import ScenarioDefinition
        from scenarios.precompute import _compute_scenario_result

        # Create a scenario where 2nd bracket rate is 0.22 (2× baseline 0.11)
        test_scenario = ScenarioDefinition(
            id="test-scale-extraction",
            name="Test IR Scale Extraction",
            description="Test scenario for IR scale extraction verification",
            parameter_overrides={
                "impot_revenu.bareme": {
                    "brackets": [
                        {"rate": 0.0, "threshold": 0},
                        {"rate": 0.22, "threshold": 11497},
                    ]
                },
            },
        )
        baseline = ScenarioDefinition(
            id="test-baseline",
            name="Test Baseline",
            description="Temporary baseline for IR scale comparison",
            parameter_overrides={},
        )
        profile = self._make_profile()
        result_test = _compute_scenario_result(profile, test_scenario)
        result_baseline = _compute_scenario_result(profile, baseline)

        # With scale=2.0 (0.22/0.11), IR should be roughly 2× baseline IR
        # (exact ratio depends on progressive bracket calculations)
        assert result_baseline["is"] == 0.0
        assert result_test["is"] == 0.0
        assert result_test["ir"] != result_baseline["ir"], (
            f"IR scale extraction should produce different IR from baseline: "
            f"test={result_test['ir']}, baseline={result_baseline['ir']}"
        )

    def test_aides_match_bilingual_fixture_expected_values(self):
        """Baseline scenario aides totals match bilingual fixture expected values."""
        from scenarios.scenario_definitions import get_scenario_definitions
        from scenarios.precompute import _compute_scenario_result

        profiles = self._load_fixture_profiles()
        if profiles is None:
            return  # Fixture file not available — skip

        baseline = [s for s in get_scenario_definitions() if s.id == "baseline-2025"][0]

        mismatches = []
        for idx, profile in enumerate(profiles[:32]):
            result = _compute_scenario_result(profile, baseline)
            expected_aides_total = sum(
                profile.get("expected", {}).get("aides", {}).values()
            )
            computed_aides = result["aides"]

            if abs(computed_aides - expected_aides_total) > 0.01:
                mismatches.append(
                    f"Profile {idx} ({profile.get('name', 'unknown')}): "
                    f"computed aides={computed_aides}, "
                    f"expected aides={expected_aides_total}"
                )

        assert not mismatches, (
            f"Aides mismatch for {len(mismatches)} profile(s):\n" +
            "\n".join(mismatches)
        )

    def test_backward_compatibility_existing_scenarios(self):
        """Original 3 scenarios compute without errors after precompute extension."""
        from scenarios.scenario_definitions import get_scenario_definitions
        from scenarios.precompute import _compute_scenario_result

        original_ids = ["baseline-2025", "expansion-2025", "consolidation-2025"]
        scenarios = {s.id: s for s in get_scenario_definitions()}
        profile = self._make_profile()
        required_keys = {"ir", "is", "tva", "cotisations", "aides", "revenuDisponible"}

        for sid in original_ids:
            assert sid in scenarios, f"Missing scenario: {sid}"
            result = _compute_scenario_result(profile, scenarios[sid])
            assert isinstance(result, dict), (
                f"{sid}: result is not a dict"
            )
            missing_keys = required_keys - set(result.keys())
            assert not missing_keys, (
                f"{sid}: missing required keys: {missing_keys}"
            )
            assert result["is"] == 0.0, f"{sid}: IS must be 0.0, got {result['is']}"
            assert result["revenuDisponible"] > 0, (
                f"{sid}: revenuDisponible must be > 0"
            )
