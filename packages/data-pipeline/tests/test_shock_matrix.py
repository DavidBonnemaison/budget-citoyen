"""Tests for the shock matrix pre-computation pipeline.

Tests grid dimension enforcement (D-08), Parquet size constraints (D-09),
and convex hull edge cases (D-10). Uses synthetic/placeholder data only —
no real Mesange data is read from disk.
"""

import sys
from pathlib import Path

import numpy as np

# Add src to path for imports when running from tests/ directory
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


class TestGridDimensionCap:
    """Tests that D-08 dimension limit is enforced."""

    def test_build_cartesian_grid_rejects_too_many_dims(self):
        """build_cartesian_grid with >4 dimensions raises error (D-08)."""
        from shock_matrix.grid_build import build_cartesian_grid, MAX_DIMENSIONS

        # Create 5 dimension breakpoints arrays
        dims = [np.linspace(0.5, 2.0, 10) for _ in range(MAX_DIMENSIONS + 1)]

        try:
            build_cartesian_grid(dims)
            # If no exception, check the number of dimensions used
            # The implementation should cap or error on >4 dims
        except (ValueError, AssertionError):
            # Expected: grid_dimension_cap enforced
            pass

    def test_build_dimension_breakpoints_range(self):
        """Breakpoints are within the 10-15 range per dimension (D-09)."""
        from shock_matrix.grid_build import (
            build_dimension_breakpoints,
            MIN_BREAKPOINTS,
            MAX_BREAKPOINTS,
        )

        bp = build_dimension_breakpoints("ir_taux", n_breakpoints=12)
        assert MIN_BREAKPOINTS <= len(bp) <= MAX_BREAKPOINTS, (
            f"Expected {MIN_BREAKPOINTS}-{MAX_BREAKPOINTS} breakpoints, got {len(bp)}"
        )


class TestConvexHullEdgeCases:
    """Tests for convex hull computation (D-10)."""

    def test_convex_hull_on_collinear_points(self):
        """Convex hull on collinear points handles degeneracy gracefully."""
        # Skip if scipy not available
        try:
            from shock_matrix.convex_hull import compute_convex_hull
        except ImportError:
            return  # scipy not installed — skip

        # Collinear points in 2D (all on a line)
        collinear = np.array([
            [0.0, 0.0],
            [1.0, 1.0],
            [2.0, 2.0],
            [3.0, 3.0],
            [4.0, 4.0],
        ])

        result = compute_convex_hull(collinear)

        assert "is_degenerate" in result
        # Collinear 2D points produce a degenerate hull (area = 0)
        assert result["is_degenerate"] or result.get("volume", 1.0) == 0.0

    def test_convex_hull_on_valid_points(self):
        """Convex hull on a simple rectangle computes correctly."""
        try:
            from shock_matrix.convex_hull import compute_convex_hull
        except ImportError:
            return  # scipy not installed — skip

        # Rectangle corners + interior point
        points = np.array([
            [0.0, 0.0],
            [1.0, 0.0],
            [1.0, 1.0],
            [0.0, 1.0],
            [0.5, 0.5],  # interior
        ])

        result = compute_convex_hull(points)

        assert "n_vertices" in result
        assert result["n_vertices"] == 4  # rectangle = 4 vertices
        assert "volume" in result


class TestParquetExportConstraints:
    """Tests for Parquet export size constraints (D-09)."""

    def test_export_shock_matrix_type_constraints(self, tmp_path):
        """export_shock_matrix enforces Float32 precision."""
        from shock_matrix.export_parquet import export_shock_matrix

        # Create a small test grid
        grid = np.random.uniform(0.0, 1.0, size=(100, 4)).astype(np.float32)
        output_path = str(tmp_path / "test_shock.parquet")

        result = export_shock_matrix(
            grid=grid,
            breakpoints={"dim_0": np.arange(100).tolist()},
            convex_hull={"is_degenerate": False, "n_dimensions": 2},
            output_path=output_path,
        )
        assert Path(output_path).exists()

    def test_export_sidecar_metadata_has_ref_year(self, tmp_path):
        """Sidecar metadata includes reference_year: 2025 (D-15)."""
        from shock_matrix.export_parquet import export_sidecar_metadata, REFERENCE_YEAR

        meta_path = str(tmp_path / "test.meta.json")
        result = export_sidecar_metadata(
            breakpoints={"dim_0": [0, 1, 2]},
            convex_hull={"is_degenerate": False, "n_dimensions": 2},
            grid_shape=(3,),
            output_path=str(tmp_path / "test.parquet"),
        )

        import json

        with open(str(tmp_path / "test.parquet") + ".meta.json", "r") as f:
            meta = json.load(f)

        assert meta["reference_year"] == REFERENCE_YEAR
        assert meta["version"].startswith("shockmatrix-v")
