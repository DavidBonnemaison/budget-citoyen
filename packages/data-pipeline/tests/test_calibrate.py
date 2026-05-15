"""Tests for shock matrix calibration (calibrate.py).

TDD: RED phase — these tests will FAIL until calibrate.py is implemented.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# Add src to path for imports when running from tests/ directory
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from shock_matrix.calibrate import build_calibrated_grid, calibrate_and_export


class TestBuildCalibratedGrid:
    """Tests for the build_calibrated_grid() function."""

    def test_grid_shape(self):
        """Grid has shape (12, 12, 5, 4) — 12 tax × 12 spend × 5 horizon × 4 features."""
        grid, breakpoints, convex_hull, metadata = build_calibrated_grid(seed=42)
        assert grid.shape == (12, 12, 5, 4), f"Expected (12,12,5,4), got {grid.shape}"

    def test_grid_nonzero(self):
        """Grid values are non-zero (unlike the zero placeholder)."""
        grid, _, _, _ = build_calibrated_grid(seed=42)
        assert np.any(np.abs(grid) > 1e-10), "Grid is all near-zero — should have real calibrated values"

    def test_grid_finite_no_nan(self):
        """Grid values are finite and not NaN."""
        grid, _, _, _ = build_calibrated_grid(seed=42)
        assert np.all(np.isfinite(grid)), "Grid contains NaN or Inf values"

    def test_breakpoint_ranges(self):
        """Breakpoint ranges match D-09 defaults."""
        _, breakpoints, _, _ = build_calibrated_grid(seed=42)
        # Tax
        assert "tax_rate" in breakpoints
        assert breakpoints["tax_rate"][0] >= 0.5, f"Tax min {breakpoints['tax_rate'][0]} < 0.5"
        assert breakpoints["tax_rate"][-1] <= 2.0, f"Tax max {breakpoints['tax_rate'][-1]} > 2.0"
        assert len(breakpoints["tax_rate"]) == 12
        # Spend
        assert "spend_level" in breakpoints
        assert breakpoints["spend_level"][0] >= 0.7, f"Spend min {breakpoints['spend_level'][0]} < 0.7"
        assert breakpoints["spend_level"][-1] <= 1.5, f"Spend max {breakpoints['spend_level'][-1]} > 1.5"
        assert len(breakpoints["spend_level"]) == 12
        # Horizon
        assert "horizon_year" in breakpoints
        assert breakpoints["horizon_year"][0] == 1.0
        assert breakpoints["horizon_year"][-1] == 5.0
        assert len(breakpoints["horizon_year"]) == 5

    def test_grid_center_plausible(self):
        """Grid-center point (tax=1.0, spend=1.0, horizon=3) has plausible values."""
        grid, _, _, _ = build_calibrated_grid(seed=42)
        # Horizons [1,2,3,4,5] → horizon=3 is index 2
        # Center: tax=6, spend=6, horizon=2
        values = grid[6, 6, 2, :]
        gdp_growth = values[0]
        employment = values[1]
        deficit = values[2]
        debt = values[3]
        # Order-of-magnitude checks with wide tolerance (±50%)
        assert 0.006 < gdp_growth < 0.018, f"GDP growth {gdp_growth} outside plausible range [0.006, 0.018]"
        assert -0.075 < deficit < -0.025, f"Deficit {deficit} outside plausible range [-0.075, -0.025]"
        assert 0.55 < debt < 1.65, f"Debt {debt} outside plausible range [0.55, 1.65]"

    def test_convex_hull_nonempty(self):
        """Convex hull equations are non-empty with valid values."""
        _, _, convex_hull, _ = build_calibrated_grid(seed=42)
        assert "hyperplanes" in convex_hull, "Missing hyperplanes in convex_hull dict"
        planes = convex_hull["hyperplanes"]
        assert planes is not None and len(planes) > 0, "Convex hull hyperplanes are empty"
        assert np.all(np.isfinite(planes)), "Hyperplanes contain NaN/Inf"

    def test_row_major_convention(self):
        """Grid follows row-major C-order convention matching macro-interpolate.ts."""
        grid, breakpoints, _, _ = build_calibrated_grid(seed=42)
        n_tax = len(breakpoints["tax_rate"])
        n_spend = len(breakpoints["spend_level"])
        n_horizon = len(breakpoints["horizon_year"])
        NUM_FEATURES = 4

        # Flatten row-major (C-order)
        flat = grid.flatten()

        # Check: flat[taxIdx * nSpend * nHorizon * 4 + spendIdx * nHorizon * 4 + horizonIdx * 4 + feat]
        for feat in range(NUM_FEATURES):
            expected = grid[0, 0, 0, feat]
            actual = flat[0 * n_spend * n_horizon * 4 + 0 * n_horizon * 4 + 0 * 4 + feat]
            assert np.isclose(expected, actual), \
                f"Row-major mismatch at (0,0,0,{feat}): grid={expected}, flat={actual}"

    def test_export_writes_parquet_and_meta(self):
        """calibrate_and_export() writes Parquet file and sidecar .meta.json."""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            dist_dir = Path(tmpdir) / "dist"
            dist_dir.mkdir(parents=True)
            result_path = calibrate_and_export(output_dir=str(Path(tmpdir)), seed=42)
            # Check Parquet file exists
            parquet_path = Path(result_path)
            assert parquet_path.exists(), f"Parquet file not found: {result_path}"
            # Check under 5 MB
            size = os.path.getsize(result_path)
            assert size < 5_000_000, f"Parquet size {size} exceeds 5MB limit"
            # Check .meta.json sidecar
            meta_path = parquet_path.with_suffix(".meta.json")
            assert meta_path.exists(), f"Meta file not found: {meta_path}"
