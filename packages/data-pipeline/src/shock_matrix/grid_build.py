"""Grid construction for the Mesange-derived shock matrix.

D-08: Maximum 4 interactive fiscal dimensions to avoid curse of dimensionality.
D-09: 10-15 breakpoints per dimension, stored as compressed Float32Array.
D-10: Smolyak sparse grids preferred; Cartesian fallback with convex hull documentation.

Total compressed output MUST be under 5 MB. Check PyArrow export size after
compression_level=9.
"""

import numpy as np
from typing import Optional, Union


# D-08: Hard cap at 4 interactive dimensions
MAX_DIMENSIONS = 4

# D-09: Breakpoint range
MIN_BREAKPOINTS = 10
MAX_BREAKPOINTS = 15
DEFAULT_BREAKPOINTS = 12

# Default dimension bounds (as fractions of reference rate)
# D-09: Tax: [0.5, 2.0], Spend: [0.7, 1.5]
DEFAULT_TAX_BOUNDS = (0.5, 2.0)
DEFAULT_SPEND_BOUNDS = (0.7, 1.5)


def build_dimension_breakpoints(
    dim_name: str,
    n_breakpoints: int = DEFAULT_BREAKPOINTS,
    bounds: Optional[tuple[float, float]] = None,
) -> np.ndarray:
    """Build evenly spaced breakpoints for a fiscal dimension.

    Per D-09: 10-15 breakpoints per dimension. Default is 12.
    Tax dimensions: evenly spaced in [0.5, 2.0] of reference rate
      (from 50% reduction to 100% increase of the reference rate).
    Spend dimension: evenly spaced in [0.7, 1.5] of reference spend level
      (from 30% reduction to 50% increase of the reference spend level).

    Args:
        dim_name: Dimension identifier (e.g. "ir", "tva", "is", "spend").
            Used to select default bounds if bounds is None.
        n_breakpoints: Number of breakpoints (default 12, range 10-15).
        bounds: Optional (min, max) tuple as fraction of reference value.
            If None, auto-selected based on dim_name.

    Returns:
        np.ndarray of shape (n_breakpoints,) with breakpoint values.

    Raises:
        ValueError: If n_breakpoints is outside the allowed range [10, 15].
    """
    if n_breakpoints < MIN_BREAKPOINTS or n_breakpoints > MAX_BREAKPOINTS:
        raise ValueError(
            f"n_breakpoints must be between {MIN_BREAKPOINTS} and "
            f"{MAX_BREAKPOINTS} per D-09. Got {n_breakpoints}."
        )

    if bounds is None:
        dim_lower = dim_name.lower()
        if "spend" in dim_lower or "depense" in dim_lower:
            bounds = DEFAULT_SPEND_BOUNDS
        else:
            bounds = DEFAULT_TAX_BOUNDS

    low, high = bounds
    breakpoints = np.linspace(low, high, n_breakpoints, dtype=np.float32)

    return breakpoints


def build_cartesian_grid(
    dimensions: list[dict],
) -> tuple[np.ndarray, dict]:
    """Build Cartesian product grid from dimension definitions.

    Constructs the full Cartesian product of all dimension breakpoints.
    Per D-08: MAX 4 dimensions. Grid growth is O(n_breakpoints^dims) —
    without the cap, grid size explodes beyond the 5 MB limit.

    Args:
        dimensions: List of dicts, each with:
            - "name" (str): Dimension name (e.g. "ir_rate", "spend_level")
            - "breakpoints" (np.ndarray): 1D array of breakpoint values
            - "outputs" (list[str], optional): Output variables mapped to
              this dimension. Default empty list.

    Returns:
        tuple of (grid_nd: np.ndarray, metadata: dict).
        grid_nd has shape (n_bp_0, n_bp_1, ..., n_outputs) where the
        last axis indexes output variables. The metadata dict contains
        dimension information and grid construction parameters.

    Raises:
        AssertionError: If len(dimensions) > MAX_DIMENSIONS (D-08 enforcement).
        ValueError: If any dimension has no breakpoints.
    """
    n_dims = len(dimensions)
    # D-08: Hard cap at 4 dimensions. Both assertion forms are checked
    # for grep-based CI enforcement.
    assert len(dimensions) <= 4, (
        f"Maximum 4 interactive dimensions allowed (D-08). "
        f"Got {len(dimensions)}. Remaining parameters must use fixed reference values."
    )
    assert n_dims <= MAX_DIMENSIONS, (
        f"Maximum {MAX_DIMENSIONS} interactive dimensions allowed (D-08). "
        f"Got {n_dims}. Remaining parameters must use fixed reference values."
    )

    # Validate dimensions
    for i, dim in enumerate(dimensions):
        if "breakpoints" not in dim or len(dim["breakpoints"]) == 0:
            raise ValueError(
                f"Dimension {i} ('{dim.get('name', 'unnamed')}') has no breakpoints."
            )

    # Determine output variables (union across all dimensions)
    all_outputs = []
    seen_outputs = set()
    for dim in dimensions:
        for output_name in dim.get("outputs", []):
            if output_name not in seen_outputs:
                all_outputs.append(output_name)
                seen_outputs.add(output_name)

    n_outputs = max(len(all_outputs), 1)  # At least 1 output slot

    # Build shape
    bp_lengths = [len(dim["breakpoints"]) for dim in dimensions]
    grid_shape = tuple(bp_lengths + [n_outputs])

    # Estimate memory footprint
    n_cells = 1
    for s in bp_lengths:
        n_cells *= s
    n_cells *= n_outputs
    estimated_bytes = n_cells * 4  # Float32 = 4 bytes
    estimated_mb = estimated_bytes / 1_000_000

    # Initialize grid (all NaN = not yet computed)
    grid = np.full(grid_shape, np.nan, dtype=np.float32)

    # Build metadata
    metadata = {
        "grid_type": "cartesian",
        "n_dimensions": n_dims,
        "dimension_names": [d["name"] for d in dimensions],
        "breakpoints": {
            d["name"]: d["breakpoints"].tolist() for d in dimensions
        },
        "breakpoint_counts": bp_lengths,
        "output_variables": all_outputs,
        "grid_shape": list(grid_shape),
        "estimated_size_bytes": estimated_bytes,
        "estimated_size_mb": round(estimated_mb, 2),
        "max_dimensions": MAX_DIMENSIONS,
        "construction_note": (
            f"Cartesian grid. For production, consider Smolyak sparse grid "
            f"(build_smolyak_grid) to reduce cells while maintaining accuracy."
        ),
    }

    return grid, metadata


def build_smolyak_grid(
    dimensions: list[dict],
    level: int = 2,
) -> tuple[np.ndarray, dict]:
    """Build Smolyak sparse grid for the shock matrix.

    D-10: Smolyak sparse grids preferred as alternative to uniform Cartesian.
    The Smolyak construction uses a sparse tensor product of 1D quadrature
    rules, which grows as O(N * log(N)^{d-1}) instead of O(N^d) for the full
    Cartesian product.

    This implementation uses Clenshaw-Curtis nodes (Chebyshev extrema) as the
    1D quadrature rule, which is the standard choice for Smolyak grids.

    If sparse grid construction fails, falls back to Cartesian grid.

    Args:
        dimensions: List of dicts, same format as build_cartesian_grid.
        level: Smolyak level parameter (default 2). Higher levels add more
            points. Level 1 = 1 point, Level 2 = 3 points, Level 3 = 5 points
            per dimension (before Smolyak combination).

    Returns:
        tuple of (sparse_points: np.ndarray, metadata: dict).
        sparse_points has shape (n_sparse_points, n_dims_output) where the
        last axis indexes output variables. metadata includes grid_type
        and construction parameters.
    """
    n_dims = len(dimensions)
    assert n_dims <= MAX_DIMENSIONS, (
        f"Maximum {MAX_DIMENSIONS} interactive dimensions allowed (D-08). "
        f"Got {n_dims}."
    )

    # Validate
    for i, dim in enumerate(dimensions):
        if "breakpoints" not in dim or len(dim["breakpoints"]) == 0:
            raise ValueError(
                f"Dimension {i} ('{dim.get('name', 'unnamed')}') has no breakpoints."
            )

    # Determine output variables
    all_outputs = []
    seen_outputs = set()
    for dim in dimensions:
        for output_name in dim.get("outputs", []):
            if output_name not in seen_outputs:
                all_outputs.append(output_name)
                seen_outputs.add(output_name)
    n_outputs = max(len(all_outputs), 1)

    # Get breakpoint arrays
    bp_arrays = [dim["breakpoints"] for dim in dimensions]
    bp_counts = [len(bp) for bp in bp_arrays]

    # Smolyak construction using Clenshaw-Curtis nodes
    try:
        sparse_points, grid_type = _smolyak_clenshaw_curtis(
            bp_arrays, level, n_dims, n_outputs
        )
    except Exception:
        # Fallback to Cartesian if Smolyak construction fails
        grid, meta = build_cartesian_grid(dimensions)
        meta["grid_type"] = "cartesian_fallback"
        meta["smolyak_fallback_reason"] = (
            "Smolyak construction failed; using Cartesian grid as fallback."
        )
        return grid, meta

    metadata = {
        "grid_type": grid_type,
        "smolyak_level": level,
        "n_dimensions": n_dims,
        "dimension_names": [d["name"] for d in dimensions],
        "breakpoints": {
            d["name"]: d["breakpoints"].tolist() for d in dimensions
        },
        "breakpoint_counts": bp_counts,
        "n_sparse_points": len(sparse_points),
        "output_variables": all_outputs,
        "grid_shape": list(sparse_points.shape),
        "estimated_size_bytes": sparse_points.nbytes,
        "estimated_size_mb": round(sparse_points.nbytes / 1_000_000, 2),
        "max_dimensions": MAX_DIMENSIONS,
        "construction_note": (
            f"Smolyak sparse grid (level {level}) with Clenshaw-Curtis nodes. "
            f"Provides dimension-adaptive accuracy with asymptotically fewer "
            f"points than Cartesian product ({len(sparse_points)} vs "
            f"{np.prod(bp_counts)})."
        ),
    }

    return sparse_points, metadata


def _smolyak_clenshaw_curtis(
    bp_arrays: list[np.ndarray],
    level: int,
    n_dims: int,
    n_outputs: int,
) -> tuple[np.ndarray, str]:
    """Internal: Smolyak sparse grid construction using Clenshaw-Curtis nodes.

    The Smolyak (sparse grid) formula:
        A(q, d) = sum_{q-d+1 ≤ |i| ≤ q} (-1)^{q-|i|} * C(d-1, q-|i|) * (U^{i_1} ⊗ ... ⊗ U^{i_d})

    where q = n_dims + level, |i| = sum of index vector, C is binomial coefficient,
    U^{i_k} is the 1D quadrature rule at level i_k.

    Args:
        bp_arrays: List of 1D breakpoint arrays for each dimension.
        level: Smolyak level.
        n_dims: Number of dimensions.
        n_outputs: Number of output variables.

    Returns:
        tuple of (points: np.ndarray, grid_type: str).
    """
    from math import comb

    q = n_dims + level  # Smolyak parameterization

    # Map normalized index to breakpoint values for each dimension
    def cc_nodes_1d(n_nodes: int, bp: np.ndarray) -> np.ndarray:
        """Clenshaw-Curtis nodes mapped to breakpoint range."""
        if n_nodes <= 1:
            return np.array([bp[len(bp) // 2]], dtype=np.float32)

        n = n_nodes - 1  # degree
        # Clenshaw-Curtis: x_k = -cos(k*pi/n) for k = 0,...,n  →  [-1, 1]
        k = np.arange(n_nodes)
        cc = -np.cos(np.pi * k / n)  # in [-1, 1]

        # Map from [-1, 1] to breakpoint range [bp[0], bp[-1]]
        a, b = float(bp[0]), float(bp[-1])
        mapped = 0.5 * (b - a) * (cc + 1.0) + a

        return mapped.astype(np.float32)

    # Number of nodes at level i: n(i) = 2^{i-1} + 1 for i >= 2, n(1) = 1
    def n_nodes_at_level(i: int) -> int:
        if i <= 1:
            return 1
        return (1 << (i - 1)) + 1  # 2^{i-1} + 1

    # Collect all unique points
    points_set = set()

    # Iterate over all index vectors with sum between q-d+1 and q
    # For practical use: level 2 with 4 dims → q=6, index sums 3..6
    min_sum = max(n_dims, q - n_dims + 1)
    max_sum = q

    # Generate all index vectors recursively
    def gen_indices(d: int, remaining: int, current: list[int]):
        if d == n_dims:
            if min_sum <= sum(current) <= max_sum:
                yield tuple(current)
            return
        # i_k ranges from 1 to level+1
        for ik in range(1, level + 2):
            if sum(current) + ik + (n_dims - d - 1) > max_sum:
                break
            yield from gen_indices(d + 1, remaining - ik, current + [ik])

    # Collect unique grid points
    all_points_list = []

    for idx_vec in gen_indices(0, max_sum, []):
        idx_sum = sum(idx_vec)
        if idx_sum < min_sum or idx_sum > max_sum:
            continue

        # Smolyak coefficient: (-1)^{q - |i|} * C(d-1, q - |i|)
        coeff_sign = 1 if (q - idx_sum) % 2 == 0 else -1
        comb_val = comb(n_dims - 1, q - idx_sum)
        weight = coeff_sign * comb_val

        if weight == 0:
            continue

        # Build 1D node sets for each dimension
        node_sets = []
        for d, i_k in enumerate(idx_vec):
            nk = n_nodes_at_level(i_k)
            nodes = cc_nodes_1d(nk, bp_arrays[d])
            node_sets.append(nodes)

        # Cartesian product of node sets (small, since i_k is small)
        # Use meshgrid for efficient combination
        if n_dims == 1:
            for n0 in node_sets[0]:
                point = (float(n0),)
                all_points_list.append(point)
        elif n_dims == 2:
            for n0 in node_sets[0]:
                for n1 in node_sets[1]:
                    all_points_list.append((float(n0), float(n1)))
        elif n_dims == 3:
            for n0 in node_sets[0]:
                for n1 in node_sets[1]:
                    for n2 in node_sets[2]:
                        all_points_list.append((float(n0), float(n1), float(n2)))
        elif n_dims == 4:
            for n0 in node_sets[0]:
                for n1 in node_sets[1]:
                    for n2 in node_sets[2]:
                        for n3 in node_sets[3]:
                            all_points_list.append(
                                (float(n0), float(n1), float(n2), float(n3))
                            )

    # Deduplicate (Smolyak formula can produce duplicates from different combinations)
    unique_points = sorted(set(all_points_list))

    if not unique_points:
        # Fallback: return midpoints
        midpoints = tuple(bp[len(bp) // 2] for bp in bp_arrays)
        unique_points = [midpoints]

    n_sparse = len(unique_points)

    # Build output array: (n_sparse_points, n_dims + n_outputs)
    # First n_dims columns = coordinate, last n_outputs = NaN (to be filled)
    result = np.full((n_sparse, n_dims + n_outputs), np.nan, dtype=np.float32)
    for i, pt in enumerate(unique_points):
        result[i, :n_dims] = pt

    grid_type = f"smolyak_level_{level}"

    return result, grid_type
