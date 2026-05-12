"""Shock matrix pre-computation pipeline for Budget Citoyen.

DATA-04 — VAR bootstrap estimation, 3D/4D grid construction,
convex hull bounds documentation, and Parquet/Zstd compressed export.

This is an offline batch pipeline. Output is consumed by the Phase 2
WASM macro engine (static Parquet binary with sidecar metadata).
"""

from .bootstrap import run_var_bootstrap, generate_placeholder_shocks, compute_confidence_bounds
from .grid_build import build_dimension_breakpoints, build_cartesian_grid, build_smolyak_grid

__all__ = [
    "run_var_bootstrap",
    "generate_placeholder_shocks",
    "compute_confidence_bounds",
    "build_dimension_breakpoints",
    "build_cartesian_grid",
    "build_smolyak_grid",
]

# convex_hull and export_parquet — these require scipy and pyarrow
# respectively. Both are standard offline pipeline dependencies.
try:
    from .convex_hull import compute_convex_hull, identify_out_of_bounds, build_bounds_report

    __all__.extend(
        ["compute_convex_hull", "identify_out_of_bounds", "build_bounds_report"]
    )
except ImportError as e:
    import warnings

    warnings.warn(f"convex_hull module unavailable: {e}")

try:
    from .export_parquet import export_shock_matrix, export_sidecar_metadata

    __all__.extend(["export_shock_matrix", "export_sidecar_metadata"])
except ImportError as e:
    import warnings

    warnings.warn(
        f"export_parquet module unavailable: {e}. "
        f"Install pyarrow for Parquet export support."
    )
