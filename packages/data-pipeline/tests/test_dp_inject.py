"""Tests for differential privacy injection and population export.

Replaces Wave 0 placeholder stub with real TDD tests.
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from synthetic_pop.dp_inject import prove_dp_guarantee, inject_dp_privacy, build_privacy_statement
from synthetic_pop.export import export_synthetic_population, compute_sha256
from synthetic_pop import export_with_dp


class TestProveDpGuarantee:
    """Tests for the formal DP proof via OpenDP .map(d_in=1)."""

    def test_within_budget_on_1000_values(self):
        """prove_dp_guarantee returns within_budget=True for reasonable data."""
        rng = np.random.default_rng(42)
        data = list(rng.uniform(10000, 80000, size=1000))
        result = prove_dp_guarantee(data, epsilon_target=1.0)
        assert result["within_budget"] is True
        assert result["actual_epsilon"] <= 1.0
        assert result["mechanism"] == "laplace"

    def test_returns_zero_epsilon_for_empty(self):
        """Empty data returns zero epsilon and within_budget."""
        result = prove_dp_guarantee([], epsilon_target=1.0)
        assert result["actual_epsilon"] == 0.0
        assert result["within_budget"] is True


class TestInjectDpPrivacy:
    """Tests for aggregate-level DP noise injection."""

    @pytest.fixture
    def sample_df(self):
        rng = np.random.default_rng(42)
        return pd.DataFrame({
            "profile_id": [f"p-{i}" for i in range(1000)],
            "age": rng.integers(18, 100, 1000).astype(float),
            "patrimoine": rng.lognormal(11.5, 1.2, 1000),
            "revenu_fiscal": rng.gamma(2.0, 15000, 1000),
            "situation_familiale": rng.choice(["celibataire", "marie"], 1000),
            "nombre_parts": rng.uniform(1.0, 4.0, 1000),
            "type_activite": rng.choice(["salarie", "retraite"], 1000),
            "zone_residence": rng.choice(["zone1", "zone2", "zone3"], 1000),
        })

    def test_returns_df_unmodified(self, sample_df):
        """inject_dp_privacy returns the original DataFrame unchanged (D-10)."""
        original = sample_df.copy()
        df_returned, _ = inject_dp_privacy(sample_df, epsilon_budget=1.0)
        # Check same columns, same values
        pd.testing.assert_frame_equal(original, df_returned, check_dtype=False)

    def test_dp_report_has_required_keys(self, sample_df):
        """dp_report has all required top-level keys."""
        _, report = inject_dp_privacy(sample_df, epsilon_budget=1.0)
        required = ["epsilon_budget", "mechanism", "composition", "aggregates",
                    "total_epsilon_consumed", "within_budget"]
        for key in required:
            assert key in report, f"Missing key: {key}"

    def test_budget_not_exceeded(self, sample_df):
        """total_epsilon_consumed <= epsilon_budget."""
        _, report = inject_dp_privacy(sample_df, epsilon_budget=1.0)
        assert report["total_epsilon_consumed"] <= report["epsilon_budget"]


class TestBuildPrivacyStatement:
    """Tests for the CNIL-compliant French privacy statement."""

    def test_contains_cnil_terminology(self):
        """Statement contains 'confidentialité différentielle'."""
        report = {
            "total_epsilon_consumed": 0.95,
            "mechanism": "laplace",
            "epsilon_budget": 1.0,
        }
        statement = build_privacy_statement(report)
        assert "confidentialité différentielle" in statement

    def test_includes_epsilon_and_mechanism(self):
        """Statement includes epsilon value and mechanism name."""
        report = {
            "total_epsilon_consumed": 0.78,
            "mechanism": "laplace",
            "epsilon_budget": 1.0,
        }
        statement = build_privacy_statement(report)
        assert "0.78" in statement or "0.7800" in statement
        assert "laplace" in statement.lower() or "Laplace" in statement


class TestExportMetaJson:
    """Tests for .meta.json sidecar with D-11 fields."""

    def test_meta_json_has_dp_fields(self):
        """export_synthetic_population writes .meta.json with D-11 fields."""
        import tempfile

        df = pd.DataFrame({
            "profile_id": ["p-1"],
            "age": [42.0],
            "patrimoine": [150000.0],
            "revenu_fiscal": [28000.0],
            "situation_familiale": ["marie"],
            "nombre_parts": [2.5],
            "type_activite": ["salarie"],
            "zone_residence": ["zone2"],
        })
        dp_report = {
            "total_epsilon_consumed": 0.95,
            "epsilon_budget": 1.0,
            "within_budget": True,
            "privacy_statement": "Test statement",
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = str(Path(tmpdir) / "population-v2025.1.json")
            export_synthetic_population(df, dp_report, output_path)

            meta_path = Path(output_path).with_suffix(".meta.json")
            assert meta_path.exists()

            import json
            with open(meta_path) as f:
                meta = json.load(f)

            # D-11 fields
            assert "dp_epsilon" in meta
            assert "dp_epsilon_budget" in meta
            assert "dp_within_budget" in meta
            assert "sha256" in meta
            assert "dp_proof_timestamp" in meta
            assert "dp_data_source" in meta
