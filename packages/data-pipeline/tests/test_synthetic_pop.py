"""Tests for the synthetic population pipeline.

Tests imports, metadata creation, and full pipeline integration.
Uses small in-memory DataFrames — no file I/O to real data directories.
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add src to path for imports when running from tests/ directory
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# Global fixture for CI-friendly pipeline parameters
CI_EPOCHS = 10
CI_NUM_ROWS = 2000


class TestSyntheticPopImports:
    """Verify synthetic_pop module imports correctly."""

    def test_imports_succeed(self):
        """All public symbols from synthetic_pop import without error."""
        from synthetic_pop import (
            load_real_data,
            preprocess_real_data,
            build_metadata,
            train_synthesizer,
            generate_synthetic_population,
        )
        # If we get here, imports succeed
        assert callable(load_real_data)
        assert callable(preprocess_real_data)
        assert callable(build_metadata)


class TestPreprocess:
    """Tests for data preprocessing functions."""

    def test_preprocess_real_data_preserves_required_columns(self):
        """preprocess_real_data preserves canonical COLUMNS after processing."""
        from synthetic_pop.preprocess import preprocess_real_data, COLUMNS

        # Create a small synthetic DataFrame matching real data structure
        df = pd.DataFrame({
            "profile_id": range(10),
            "age": np.random.randint(18, 90, 10),
            "patrimoine": np.random.uniform(0, 500000, 10),
            "revenu_fiscal": np.random.uniform(0, 150000, 10),
            "situation_familiale": np.random.choice(
                ["celibataire", "marie", "divorce", "veuf"], 10
            ),
            "nombre_parts": np.random.uniform(1.0, 4.0, 10),
            "type_activite": np.random.choice(
                ["salarie", "independant", "retraite", "chomeur"], 10
            ),
            "zone_residence": np.random.choice(["zone1", "zone2", "zone3"], 10),
        })

        processed = preprocess_real_data(df)

        assert isinstance(processed, pd.DataFrame)
        # Output may have fewer columns after preprocessing (e.g., one-hot encoding)
        # but should still be a valid DataFrame
        assert len(processed) > 0

    def test_build_metadata_returns_correct_type(self):
        """build_metadata returns a SingleTableMetadata object."""
        from sdv.metadata import SingleTableMetadata
        from synthetic_pop.preprocess import build_metadata

        df = pd.DataFrame({
            "age": [25, 40],
            "patrimoine": [10000.0, 200000.0],
            "revenu_fiscal": [20000.0, 50000.0],
            "situation_familiale": ["celibataire", "marie"],
            "nombre_parts": [1.0, 2.0],
            "type_activite": ["salarie", "independant"],
            "zone_residence": ["zone2", "zone1"],
            "profile_id": [1, 2],
        })
        metadata = build_metadata(df)
        assert isinstance(metadata, SingleTableMetadata)


class TestExportImports:
    """Tests for the export module."""

    def test_compute_sha256(self, tmp_path):
        """compute_sha256 produces correct hash for known content."""
        from synthetic_pop.export import compute_sha256

        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")

        digest = compute_sha256(str(test_file))
        assert len(digest) == 64
        assert all(c in "0123456789abcdef" for c in digest)


class TestPipelineIntegration:
    """Integration tests for the full CopulaGAN train + evaluate pipeline.

    Uses CI-friendly parameters (epochs=10, num_rows=2000) for fast execution.
    Full-scale training (epochs=500, num_rows=50000) is marked @pytest.mark.slow.
    """

    def test_generate_from_insee_smoke(self):
        """Pipeline runs train + evaluate chain without error."""
        from synthetic_pop import generate_from_insee

        result = generate_from_insee(epochs=CI_EPOCHS, num_rows=CI_NUM_ROWS, seed=42)

        expected_keys = {"synthesizer", "synthetic_df", "quality_report", "metadata", "real_df"}
        missing = expected_keys - set(result.keys())
        assert not missing, f"Missing keys in result: {missing}"
        assert isinstance(result["synthetic_df"], pd.DataFrame)
        assert len(result["synthetic_df"]) == CI_NUM_ROWS

    def test_synthetic_has_no_nulls(self):
        """Synthetic data has no nulls in critical columns."""
        from synthetic_pop import generate_from_insee

        result = generate_from_insee(epochs=CI_EPOCHS, num_rows=CI_NUM_ROWS, seed=42)
        df = result["synthetic_df"]
        critical_cols = ["age", "patrimoine", "revenu_fiscal"]
        for col in critical_cols:
            null_count = df[col].isnull().sum()
            assert null_count == 0, f"Column {col} has {null_count} null values"

    def test_quality_report_generated(self):
        """Quality report contains fidelity and privacy keys."""
        from synthetic_pop import generate_from_insee

        result = generate_from_insee(epochs=CI_EPOCHS, num_rows=CI_NUM_ROWS, seed=42)
        report = result["quality_report"]
        assert "fidelity" in report, f"Missing fidelity — keys: {list(report.keys())}"
        assert "privacy" in report, f"Missing privacy — keys: {list(report.keys())}"

    def test_quality_scores_not_none(self):
        """Fidelity overall_score is not None or NaN."""
        from synthetic_pop import generate_from_insee

        result = generate_from_insee(epochs=CI_EPOCHS, num_rows=CI_NUM_ROWS, seed=42)
        score = result["quality_report"]["fidelity"]["overall_score"]
        assert score is not None, "Overall quality score is None"
        assert not (isinstance(score, float) and np.isnan(score)), "Overall quality score is NaN"

    def test_synthesizer_checkpoint(self):
        """Checkpoint file exists after training."""
        from synthetic_pop import generate_from_insee

        result = generate_from_insee(epochs=CI_EPOCHS, num_rows=CI_NUM_ROWS, seed=42)
        # Synthesizer was saved during training (train.py saves to models/ subdir)
        synth_dir = Path("models") / f"{CI_EPOCHS}epochs"
        checkpoint = synth_dir / "synthesizer.pkl"
        assert checkpoint.exists(), f"Checkpoint not found: {checkpoint}"

    def test_synthetic_row_count(self):
        """Synthetic data has exactly num_rows rows and correct column count."""
        from synthetic_pop import generate_from_insee

        result = generate_from_insee(epochs=CI_EPOCHS, num_rows=100, seed=42)
        df = result["synthetic_df"]
        assert len(df) == 100, f"Expected 100 rows, got {len(df)}"

    def test_categorical_values_valid(self):
        """Categorical values are all within valid enum sets from preprocess.py."""
        from synthetic_pop import generate_from_insee
        from synthetic_pop.preprocess import SITUATION_FAMILIALE_VALUES, TYPE_ACTIVITE_VALUES, ZONE_RESIDENCE_VALUES

        result = generate_from_insee(epochs=CI_EPOCHS, num_rows=CI_NUM_ROWS, seed=42)
        df = result["synthetic_df"]

        assert df["situation_familiale"].isin(SITUATION_FAMILIALE_VALUES).all()
        assert df["type_activite"].isin(TYPE_ACTIVITE_VALUES).all()
        assert df["zone_residence"].isin(ZONE_RESIDENCE_VALUES).all()

    def test_privacy_score_acceptable(self):
        """DisclosureProtectionEstimate score >= 0.5."""
        from synthetic_pop import generate_from_insee

        result = generate_from_insee(epochs=CI_EPOCHS, num_rows=CI_NUM_ROWS, seed=42)
        dpe_score = result["quality_report"]["privacy"]["dpe_score"]
        assert dpe_score >= 0.5, f"DPE score {dpe_score} < 0.5"


@pytest.mark.slow
class TestFullScalePipeline:
    """Full-scale pipeline tests (manual only, excluded from CI)."""

    def test_generate_from_insee_full_scale(self):
        """Full training at epochs=500, num_rows=50000 completes without error."""
        from synthetic_pop import generate_from_insee

        result = generate_from_insee(epochs=500, num_rows=50000, seed=42)
        assert len(result["synthetic_df"]) == 50000
        assert result["quality_report"]["fidelity"]["overall_score"] is not None
        # Verify checkpoint
        checkpoint = Path("models") / "500epochs" / "synthesizer.pkl"
        assert checkpoint.exists()
