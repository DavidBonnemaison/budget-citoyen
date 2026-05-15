"""Wave 0 placeholder tests for shock matrix calibration.

TODO: Replace stubs with real TDD tests in Plan 02.2-03.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

# Add src to path for imports when running from tests/ directory
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from shock_matrix.calibrate import calibrate_shock_matrix  # noqa: F401
    CALIBRATE_AVAILABLE = True
except ImportError:
    CALIBRATE_AVAILABLE = False


def test_wave0_placeholder():
    """Wave 0 stub — always passes."""
    pass


# TODO: Real tests to add in Plan 02.2-03:
# - calibrate_shock_matrix produces grid with expected shape (12×12×12×4)
# - non-null values at all grid points (no NaN holes)
# - breakpoint ranges match D-09 defaults (tax: -10 to +10, spend: -20 to +20, horizon: 1-5)
# - convex hull covers all grid points
# - elasticity signs correct (positive IR → positive GDP elasticity, etc.)
