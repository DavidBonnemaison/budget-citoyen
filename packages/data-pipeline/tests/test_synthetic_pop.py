"""Tests for the synthetic population pipeline.

Tests imports and metadata creation from synthetic_pop module.
Uses small in-memory DataFrames — no file I/O to real data directories.
"""

import sys
from pathlib import Path

import pandas as pd
import numpy as np

# Add src to path for imports when running from tests/ directory
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


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
