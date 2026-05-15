"""Tests for the INSEE aggregate data loader (InseeAggregateLoader).

TDD: RED phase — these tests will FAIL until insee_loader.py is implemented.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# Add src to path for imports when running from tests/ directory
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from synthetic_pop.insee_loader import InseeAggregateLoader, build_insee_dataframe
from synthetic_pop.preprocess import COLUMNS, SITUATION_FAMILIALE_VALUES, TYPE_ACTIVITE_VALUES, ZONE_RESIDENCE_VALUES


class TestInseeAggregateLoader:
    """Tests for the InseeAggregateLoader class (D-03 tabular interface)."""

    def test_columns_match_preprocess(self):
        """Loader returns DataFrame with exactly the 8 canonical COLUMNS."""
        loader = InseeAggregateLoader(seed=42, num_rows=100)
        df = loader.load()
        assert list(df.columns) == COLUMNS, f"Expected {COLUMNS}, got {list(df.columns)}"
        assert len(df.columns) == len(COLUMNS)

    def test_default_produces_50000_rows(self):
        """Default generation produces exactly 50,000 rows."""
        loader = InseeAggregateLoader(seed=42)  # default num_rows=50000
        df = loader.load()
        assert len(df) == 50000, f"Expected 50000 rows, got {len(df)}"

    def test_required_fields_non_null(self):
        """All required JSON Schema fields are present and non-null."""
        loader = InseeAggregateLoader(seed=42, num_rows=500)
        df = loader.load()
        required_fields = ["profile_id", "age", "patrimoine", "revenu_fiscal",
                           "situation_familiale", "nombre_parts"]
        for field in required_fields:
            assert field in df.columns, f"Missing required field: {field}"
            assert df[field].notna().all(), f"Null values in {field}"

    def test_categorical_values_valid(self):
        """Categorical fields contain only valid enum values."""
        loader = InseeAggregateLoader(seed=42, num_rows=500)
        df = loader.load()
        assert df["situation_familiale"].isin(SITUATION_FAMILIALE_VALUES).all(), \
            f"Invalid situation_familiale values: {set(df['situation_familiale']) - set(SITUATION_FAMILIALE_VALUES)}"
        assert df["type_activite"].isin(TYPE_ACTIVITE_VALUES).all(), \
            f"Invalid type_activite values"
        assert df["zone_residence"].isin(ZONE_RESIDENCE_VALUES).all(), \
            f"Invalid zone_residence values"

    def test_numeric_ranges_valid(self):
        """Numeric fields are in valid ranges."""
        loader = InseeAggregateLoader(seed=42, num_rows=500)
        df = loader.load()
        assert (df["age"] >= 18).all() and (df["age"] <= 100).all(), \
            f"age out of range: {df['age'].min()}-{df['age'].max()}"
        assert (df["patrimoine"] >= 0).all(), \
            f"patrimoine has negative values: {df['patrimoine'].min()}"
        assert (df["revenu_fiscal"] >= 0).all(), \
            f"revenu_fiscal has negative values"
        assert (df["nombre_parts"] >= 1.0).all() and (df["nombre_parts"] <= 20.0).all(), \
            f"nombre_parts out of range: {df['nombre_parts'].min()}-{df['nombre_parts'].max()}"

    def test_profile_ids_unique(self):
        """profile_id values are unique (no duplicates)."""
        loader = InseeAggregateLoader(seed=42, num_rows=500)
        df = loader.load()
        assert df["profile_id"].is_unique, "profile_id has duplicates"

    def test_missing_source_graceful(self):
        """Handler for missing source returns a DataFrame (no crash)."""
        loader = InseeAggregateLoader(seed=42, num_rows=100)
        df = loader.load(source_path="/nonexistent/path/insee_data.csv")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 100
        assert list(df.columns) == COLUMNS

    def test_plausible_statistics(self):
        """Generated data has plausible statistical properties (wide tolerances)."""
        loader = InseeAggregateLoader(seed=42, num_rows=5000)
        df = loader.load()
        mean_age = df["age"].mean()
        mean_revenu = df["revenu_fiscal"].mean()
        # Wide tolerance for aggregate-derived synthetic data
        assert 30 < mean_age < 60, f"Mean age {mean_age:.1f} outside plausible range 30-60"
        assert 15000 < mean_revenu < 50000, f"Mean revenu {mean_revenu:.0f} outside plausible range 15K-50K"


class TestBuildInseeDataFrame:
    """Tests for the standalone build_insee_dataframe() function."""

    def test_build_dataframe_defaults(self):
        """build_insee_dataframe with defaults returns 50K rows × 8 columns."""
        df = build_insee_dataframe(num_rows=100, seed=42)
        assert len(df) == 100
        assert list(df.columns) == COLUMNS
        assert df["profile_id"].is_unique

    def test_build_dataframe_reproducible(self):
        """Same seed produces identical output."""
        df1 = build_insee_dataframe(num_rows=100, seed=42)
        df2 = build_insee_dataframe(num_rows=100, seed=42)
        pd.testing.assert_frame_equal(df1, df2)

    def test_build_dataframe_different_seeds(self):
        """Different seeds produce different output."""
        df1 = build_insee_dataframe(num_rows=100, seed=42)
        df2 = build_insee_dataframe(num_rows=100, seed=123)
        assert not df1.equals(df2), "Different seeds should produce different data"
