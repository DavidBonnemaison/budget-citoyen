"""Parquet/Zstd export for the Mesange-derived shock matrix.

D-09: Total compressed output MUST be under 5 MB. Achieved through:
  - Zstd compression at level 9 (maximum compression)
  - Columnar storage (PyArrow Parquet) with row_group_size=10000
  - Float32 precision (sufficient for macro projections)

D-16: All artifacts versioned with "shockmatrix-v2025.1" tag.
D-15: Reference year locked to 2025.

The output is consumed by the Phase 2 WASM macro engine as a static
compressed binary with sidecar metadata.
"""

import json
import os
from pathlib import Path
from typing import Optional, Union

import numpy as np

try:
    import pyarrow as pa
    import pyarrow.parquet as pq

    _HAS_PYARROW = True
except ImportError:
    _HAS_PYARROW = False
    pa = None  # type: ignore[misc]
    pq = None  # type: ignore[misc]

# D-09: Hard size cap
MAX_COMPRESSED_SIZE = 5_000_000  # 5 MB

# D-15: Reference year
REFERENCE_YEAR = 2025

# D-16: Version tag
VERSION_TAG = "shockmatrix-v2025.1"

# Compression parameters per RESEARCH.md Pattern 5
COMPRESSION = "zstd"
COMPRESSION_LEVEL = 9
ROW_GROUP_SIZE = 10000


def export_shock_matrix(
    grid: np.ndarray,
    breakpoints: dict,
    convex_hull: dict,
    output_path: str,
    reference_year: int = REFERENCE_YEAR,
) -> str:
    """Export shock matrix as Parquet/Zstd with sidecar metadata.

    Flattens the 4D grid (or Smolyak sparse grid) into a PyArrow table
    with columns: [tax_rate, spend_level, horizon_year, gdp_growth,
    employment_change, deficit_change, debt_to_gdp_ratio].

    Uses RESEARCH.md Pattern 5 (lines 474-535) as template.
    Writes via pyarrow.parquet.write_table() with compression='zstd',
    compression_level=9, row_group_size=10000.

    Per D-09: Asserts compressed_size < 5_000_000 bytes after writing.

    Args:
        grid: np.ndarray of shock matrix values. Can be two formats:
            - Cartesian: shape (n_bp_0, n_bp_1, ..., n_outputs)
            - Smolyak: shape (n_points, n_dims + n_outputs)
        breakpoints: dict mapping dimension name → list of breakpoint values.
            Must include dimension names matching the grid axes.
        convex_hull: dict from compute_convex_hull().
        output_path: str — file path for the .parquet output.
        reference_year: int — reference year (default 2025, per D-15).

    Returns:
        str — absolute path to the written Parquet file.

    Raises:
        ImportError: If pyarrow is not installed.
        AssertionError: If compressed file size exceeds 5_000_000 bytes (D-09).
        ValueError: If grid format is unrecognized.
    """
    if not _HAS_PYARROW:
        raise ImportError(
            "pyarrow is required for Parquet export. "
            "Install with: pip install pyarrow==24.0.0\n"
            "Note: pyarrow requires Python >= 3.10."
        )

    output_path = str(Path(output_path).resolve())

    # Determine grid format and flatten
    grid_shape = grid.shape
    grid_ndim = len(grid_shape)

    if grid_ndim >= 3:
        # Cartesian grid: (dim0, dim1, ..., dim_k, n_outputs)
        # where we have k spatial dimensions + 1 output dimension
        n_spatial_dims = grid_ndim - 1
        n_outputs = grid_shape[-1]

        # Get breakpoint arrays in order
        bp_keys = list(breakpoints.keys())
        if len(bp_keys) < n_spatial_dims:
            # Try to match: find dimension keys
            # Convention: breakpoints has "tax_rate", "spend_level", "horizon_year"
            bp_arrays = []
            bp_names = []

            # First try to match by key order
            for key in bp_keys:
                bp_arrays.append(np.array(breakpoints[key], dtype=np.float32))
                bp_names.append(key)

            # If we need more dims, use grid shape indices
            while len(bp_arrays) < n_spatial_dims:
                dim_idx = len(bp_arrays)
                bp_arrays.append(
                    np.arange(grid_shape[dim_idx], dtype=np.float32)
                )
                bp_names.append(f"dim_{dim_idx}")
        else:
            bp_names = bp_keys[:n_spatial_dims]
            bp_arrays = [
                np.array(breakpoints[name], dtype=np.float32)
                for name in bp_names
            ]

        # Build records by iterating over all grid cells
        records = _flatten_cartesian(grid, bp_arrays, bp_names, n_spatial_dims, n_outputs)

    elif grid_ndim == 2:
        # Smolyak format: (n_points, n_dims + n_outputs)
        n_total_cols = grid_shape[1]
        # Heuristic: assume 4 output variables if grid is Smolyak
        # (gdp_growth, employment_change, deficit_change, debt_to_gdp_ratio)
        n_outputs = min(4, n_total_cols)
        n_spatial_dims = n_total_cols - n_outputs

        records = _flatten_smolyak(grid, n_spatial_dims, n_outputs)
        bp_names = [f"dim_{d}" for d in range(n_spatial_dims)]

    else:
        raise ValueError(
            f"Unrecognized grid format: shape {grid_shape}. "
            f"Expected Cartesian (3+D) or Smolyak (2D) format."
        )

    # Build PyArrow table
    table = pa.Table.from_pylist(records)

    # Write with Zstd compression
    pq.write_table(
        table,
        output_path,
        compression=COMPRESSION,
        compression_level=COMPRESSION_LEVEL,
        row_group_size=ROW_GROUP_SIZE,
    )

    # D-09: Enforce size constraint
    compressed_size = Path(output_path).stat().st_size
    assert compressed_size < MAX_COMPRESSED_SIZE, (
        f"Shock matrix exceeds 5 MB limit (D-09): "
        f"{compressed_size:,} bytes ({compressed_size / 1_000_000:.2f} MB). "
        f"Reduce breakpoints (currently {grid_shape}) or use Smolyak sparse grid."
    )

    return output_path


def _flatten_cartesian(
    grid: np.ndarray,
    bp_arrays: list[np.ndarray],
    bp_names: list[str],
    n_spatial_dims: int,
    n_outputs: int,
) -> list[dict]:
    """Flatten Cartesian grid into list of record dicts."""
    import itertools

    records = []

    # Iterate over all combinations of breakpoint indices
    idx_ranges = [range(len(bp)) for bp in bp_arrays]

    for indices in itertools.product(*idx_ranges):
        # Get the grid cell values
        cell = grid[indices]  # shape: (n_outputs,)

        record = {}
        for d, idx in enumerate(indices):
            record[bp_names[d]] = float(bp_arrays[d][idx])

        # Map output variables (always use the standard 4)
        output_names = [
            "gdp_growth",
            "employment_change",
            "deficit_change",
            "debt_to_gdp_ratio",
        ]

        for o in range(min(n_outputs, 4)):
            val = float(cell[o]) if o < n_outputs else float("nan")
            val = (
                0.0 if np.isnan(val) or np.isinf(val) else val
            )
            record[output_names[o]] = val

        records.append(record)

    return records


def _flatten_smolyak(
    grid: np.ndarray,
    n_spatial_dims: int,
    n_outputs: int,
) -> list[dict]:
    """Flatten Smolyak sparse grid into list of record dicts."""
    records = []

    output_names = [
        "gdp_growth",
        "employment_change",
        "deficit_change",
        "debt_to_gdp_ratio",
    ]

    for i in range(grid.shape[0]):
        record = {}

        for d in range(n_spatial_dims):
            record[f"dim_{d}"] = float(grid[i, d])

        for o in range(min(n_outputs, 4)):
            val = float(grid[i, n_spatial_dims + o]) if n_spatial_dims + o < grid.shape[1] else float("nan")
            val = 0.0 if np.isnan(val) or np.isinf(val) else val
            record[output_names[o]] = val

        records.append(record)

    return records


def export_sidecar_metadata(
    breakpoints: dict,
    convex_hull: dict,
    grid_shape: tuple,
    output_path: str,
    reference_year: int = REFERENCE_YEAR,
) -> str:
    """Export sidecar metadata JSON for the shock matrix Parquet file.

    Writes {output_path}.meta.json with full metadata including:
      - reference_year=2025 (D-15)
      - version="shockmatrix-v2025.1" (D-16)
      - All dimension breakpoints
      - Convex hull metadata (vertices, volume, bounds report)
      - Grid shape and dimensions
      - Compression parameters and achieved size

    Args:
        breakpoints: dict mapping dimension name → list of breakpoint values.
        convex_hull: dict from compute_convex_hull().
        grid_shape: tuple — shape of the exported grid.
        output_path: str — path to the Parquet file (used to compute
            .meta.json path and read compressed size).
        reference_year: int — reference year (default 2025, per D-15).

    Returns:
        str — absolute path to the written .meta.json file.
    """
    parquet_path = Path(output_path)

    # Compute compressed size
    if parquet_path.exists():
        compressed_size = parquet_path.stat().st_size
    else:
        compressed_size = 0

    # Build dimension metadata
    dimension_list = []
    for name, bp_values in breakpoints.items():
        dim_entry = {
            "name": name,
            "n_breakpoints": len(bp_values),
            "breakpoints": (
                bp_values.tolist()
                if hasattr(bp_values, "tolist")
                else list(bp_values)
            ),
            "min": float(min(bp_values)),
            "max": float(max(bp_values)),
        }
        dimension_list.append(dim_entry)

    # Prepare convex hull metadata (strip numpy arrays for JSON)
    hull_meta = {}
    for key in convex_hull:
        val = convex_hull[key]
        if hasattr(val, "tolist"):
            hull_meta[key] = val.tolist()
        elif isinstance(val, (np.integer,)):
            hull_meta[key] = int(val)
        elif isinstance(val, (np.floating,)):
            hull_meta[key] = float(val)
        else:
            hull_meta[key] = val

    # Determine output variables
    output_variables = [
        "gdp_growth",
        "employment_change",
        "deficit_change",
        "debt_to_gdp_ratio",
    ]

    metadata = {
        "version": VERSION_TAG,
        "reference_year": reference_year,
        "dimensions": dimension_list,
        "output_variables": output_variables,
        "breakpoints": {
            name: (
                bp_values.tolist()
                if hasattr(bp_values, "tolist")
                else list(bp_values)
            )
            for name, bp_values in breakpoints.items()
        },
        "convex_hull": hull_meta,
        "grid_shape": list(grid_shape),
        "compression": COMPRESSION,
        "compression_level": COMPRESSION_LEVEL,
        "compressed_size_bytes": compressed_size,
        "compressed_size_mb": round(compressed_size / 1_000_000, 2),
        "size_limit_bytes": MAX_COMPRESSED_SIZE,
        "size_limit_mb": MAX_COMPRESSED_SIZE / 1_000_000,
    }

    # Write sidecar metadata
    meta_path = str(parquet_path) + ".meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return meta_path
