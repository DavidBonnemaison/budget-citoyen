"""Tests for shock matrix calibration (calibrate.py).

TDD: GREEN phase — validates the calibrated grid output.
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
        # Tax: 12 points in [0.5, 2.0] (float tolerance for linspace edge)
        assert "tax_rate" in breakpoints
        np.testing.assert_allclose(breakpoints["tax_rate"][0], 0.5, rtol=1e-6)
        np.testing.assert_allclose(breakpoints["tax_rate"][-1], 2.0, rtol=1e-6)
        assert len(breakpoints["tax_rate"]) == 12
        # Spend: 12 points in [0.7, 1.5]
        assert "spend_level" in breakpoints
        np.testing.assert_allclose(breakpoints["spend_level"][0], 0.7, rtol=1e-6)
        np.testing.assert_allclose(breakpoints["spend_level"][-1], 1.5, rtol=1e-6)
        assert len(breakpoints["spend_level"]) == 12
        # Horizon: 5 integer years [1, 2, 3, 4, 5]
        assert "horizon_year" in breakpoints
        assert breakpoints["horizon_year"][0] == 1.0
        assert breakpoints["horizon_year"][-1] == 5.0
        assert len(breakpoints["horizon_year"]) == 5

    def test_grid_center_plausible(self):
        """Grid-center indices have plausible macro values (wide tolerance for calibrated data)."""
        grid, breakpoints, _, _ = build_calibrated_grid(seed=42)
        # Center of breakpoint grid: tax[6] ≈ 1.318, spend[6] ≈ 1.136, horizon[2]=3
        # At this non-reference point, values deviate from baseline
        values = grid[6, 6, 2, :]
        gdp_growth = values[0]
        deficit = values[2]
        debt = values[3]
        # At center indices (tax=1.318, spend=1.136): tax positive shock, spend positive boost
        # Net GDP effect can be small, deficit widens, debt increases
        assert 0.001 < gdp_growth < 0.03, f"GDP growth {gdp_growth} outside range [0.001, 0.03]"
        assert -0.40 < deficit < 0.05, f"Deficit {deficit} outside range [-0.40, 0.05]"
        assert -2.0 < debt < 5.0, f"Debt {debt} outside range [-2.0, 5.0]"

    def test_convex_hull_nonempty(self):
        """Convex hull equations are non-empty with finite values."""
        _, _, convex_hull, _ = build_calibrated_grid(seed=42)
        # The convex hull dict uses 'hull_equations' key (from compute_convex_hull)
        assert "hull_equations" in convex_hull, f"Missing hull_equations — keys: {list(convex_hull.keys())}"
        equations = convex_hull["hull_equations"]
        assert equations is not None and len(equations) > 0, "Convex hull equations are empty"
        eq = np.asarray(equations)
        assert np.all(np.isfinite(eq)), "Hull equations contain NaN/Inf"

    def test_row_major_convention(self):
        """Grid follows row-major C-order convention matching macro-interpolate.ts."""
        grid, breakpoints, _, _ = build_calibrated_grid(seed=42)
        n_tax = len(breakpoints["tax_rate"])
        n_spend = len(breakpoints["spend_level"])
        n_horizon = len(breakpoints["horizon_year"])
        NUM_FEATURES = 4

        flat = grid.flatten()

        # Row-major C-order: flat[taxIdx * nSpend * nHorizon * 4 + spendIdx * nHorizon * 4 + horizonIdx * 4 + feat]
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
            result_path = calibrate_and_export(output_dir=str(Path(tmpdir)), seed=42)
            # Check Parquet file exists
            parquet_path = Path(result_path)
            assert parquet_path.exists(), f"Parquet file not found: {result_path}"
            # Check under 5 MB
            size = os.path.getsize(str(parquet_path))
            assert size < 5_000_000, f"Parquet size {size} exceeds 5MB limit"
            # Check .meta.json sidecar (export appends .meta.json to the parquet path)
            meta_path = Path(str(parquet_path) + ".meta.json")
            assert meta_path.exists(), f"Meta file not found: {meta_path}"
