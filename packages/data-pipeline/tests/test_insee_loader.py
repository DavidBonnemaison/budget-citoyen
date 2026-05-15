"""Wave 0 placeholder tests for the INSEE aggregate data loader.

TODO: Replace stubs with real TDD tests in Plan 02.2-02.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

# Add src to path for imports when running from tests/ directory
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

try:
    from synthetic_pop.insee_loader import InseeAggregateLoader  # noqa: F401
    LOADER_AVAILABLE = True
except ImportError:
    LOADER_AVAILABLE = False


def test_wave0_placeholder():
    """Wave 0 stub — always passes."""
    pass


# TODO: Real tests to add in Plan 02.2-02:
# - constructs DataFrame with canonical COLUMNS
# - produces 50000 rows from INSEE aggregate tables
# - handles missing source data gracefully (no crash)
# - all required schema fields present (profile_id, age, revenu_fiscal, etc.)
# - column dtypes match expected schema
