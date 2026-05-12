"""Convex hull computation for shock matrix bounds documentation.

D-10: Convex hull bounds are computed via scipy.spatial.ConvexHull and
documented in metadata. Out-of-bounds regions are explicitly identified.

NEVER hand-roll a gift-wrapping algorithm — scipy's Qhull implementation
is battle-tested, handles degenerate cases (collinear points), and provides
volume/bounds verification (RESEARCH.md anti-pattern).
"""

import numpy as np
from typing import Optional, Union

# scipy.spatial.ConvexHull — the ONLY acceptable convex hull implementation
from scipy.spatial import ConvexHull


def compute_convex_hull(grid_points: np.ndarray) -> dict:
    """Compute convex hull of grid points.

    Uses scipy.spatial.ConvexHull (Qhull) — NEVER a hand-rolled algorithm.
    scipy's implementation handles degenerate cases (collinear/coplanar points),
    provides volume computation, and is validated by decades of scientific use.

    Args:
        grid_points: NxD array of grid coordinates (N points, D dimensions).
            For the shock matrix, D is typically 2-4 (interactive fiscal dims).

    Returns:
        dict with keys:
            - "hull_vertices": np.ndarray of vertex indices forming the hull
            - "hull_equations": np.ndarray of hyperplane equations [A, b]
              where A·x + b <= 0 for interior points
            - "hull_points": np.ndarray of hull vertex coordinates
            - "volume": float — hull volume (area in 2D, volume in 3D, etc.)
            - "volume_unit": str — dimension-appropriate unit label
            - "n_dimensions": int — dimensionality of the input
            - "n_vertices": int — number of hull vertices
            - "n_input_points": int — total input points
            - "is_degenerate": bool — True if hull is degenerate
              (all points collinear/coplanar)
            - "degenerate_reason": str or None — explanation if degenerate

    Raises:
        ValueError: If grid_points has fewer than D+1 points (minimum for
            a D-dimensional convex hull).
    """
    n_points, n_dims = grid_points.shape

    if n_points < n_dims + 1:
        raise ValueError(
            f"Need at least {n_dims + 1} points to form a "
            f"{n_dims}-dimensional convex hull. Got {n_points} points."
        )

    # Check for edge cases
    is_degenerate = False
    degenerate_reason = None

    if n_dims == 1:
        # 1D convex hull is just [min, max]
        hull_vertices = np.array([np.argmin(grid_points), np.argmax(grid_points)])
        hull_points = grid_points[hull_vertices]
        hull_equations = np.array([
            [-1.0, grid_points.min()],   # x >= min  →  -x + min <= 0
            [1.0, -grid_points.max()],    # x <= max  →  x - max <= 0
        ])
        volume = float(grid_points.max() - grid_points.min())
        volume_unit = "length"
    else:
        try:
            hull = ConvexHull(grid_points, qhull_options="QJ")
            # QJ option: joggle input to avoid precision issues with
            # nearly-degenerate point sets. Standard practice for numerical
            # stability in fiscal parameter grids.

            hull_vertices = hull.vertices
            hull_points = hull.points[hull_vertices]
            hull_equations = hull.equations
            volume = float(hull.volume)
        except Exception as e:
            # Handle degenerate cases
            is_degenerate = True
            degenerate_reason = (
                f"ConvexHull computation failed: {e}. "
                f"Points may be collinear or coplanar. "
                f"Consider reducing dimensionality or adding jitter."
            )

            # Fallback: use bounding box as approximate hull
            mins = grid_points.min(axis=0)
            maxs = grid_points.max(axis=0)
            # Build bounding box vertices (2^n_dims corners)
            corners = []
            for i in range(2**n_dims):
                corner = []
                for d in range(n_dims):
                    bit = (i >> d) & 1
                    corner.append(mins[d] if bit == 0 else maxs[d])
                corners.append(corner)
            hull_points = np.array(corners)
            hull_vertices = np.arange(len(hull_points))
            hull_equations = np.zeros((2 * n_dims, n_dims + 1))
            # Axis-aligned bounding box equations
            for d in range(n_dims):
                # Lower bound: -x_d + min_d <= 0
                hull_equations[2 * d, d] = -1.0
                hull_equations[2 * d, -1] = mins[d]
                # Upper bound: x_d - max_d <= 0
                hull_equations[2 * d + 1, d] = 1.0
                hull_equations[2 * d + 1, -1] = -maxs[d]
            volume = float(np.prod(maxs - mins))

    # Determine unit label
    if n_dims == 1:
        volume_unit = "length"
    elif n_dims == 2:
        volume_unit = "area"
    elif n_dims == 3:
        volume_unit = "volume"
    else:
        volume_unit = f"{n_dims}-volume"

    result = {
        "hull_vertices": hull_vertices.tolist() if hasattr(hull_vertices, 'tolist') else hull_vertices,
        "hull_equations": hull_equations.tolist() if hasattr(hull_equations, 'tolist') else hull_equations,
        "hull_points": hull_points.tolist() if hasattr(hull_points, 'tolist') else hull_points,
        "volume": volume,
        "volume_unit": volume_unit,
        "n_dimensions": n_dims,
        "n_vertices": len(hull_vertices),
        "n_input_points": n_points,
        "is_degenerate": is_degenerate,
        "degenerate_reason": degenerate_reason,
    }

    return result


def identify_out_of_bounds(
    query_points: np.ndarray,
    hull_result: dict,
) -> np.ndarray:
    """Identify which query points fall outside the convex hull.

    Uses hull_equations to test point containment. A point is inside the
    convex hull if and only if A·x + b <= 0 for all hyperplane equations
    (with a small epsilon tolerance for numerical precision).

    Per D-10: out-of-bounds regions are explicitly identified. The output
    boolean mask can be used to set out-of-bounds cells to NaN in the
    exported matrix.

    Args:
        query_points: MxD array of points to test (M points, D dimensions).
        hull_result: dict from compute_convex_hull(), containing
            hull_equations and n_dimensions.

    Returns:
        np.ndarray of shape (M,) with boolean values. True = point is
        outside the convex hull (out of bounds). False = inside or on hull.

    Raises:
        ValueError: If query_points dimensionality doesn't match hull.
    """
    hull_equations = np.array(hull_result["hull_equations"])
    hull_dims = hull_result["n_dimensions"]

    if query_points.ndim == 1:
        query_points = query_points.reshape(1, -1)

    if query_points.shape[1] != hull_dims:
        raise ValueError(
            f"Query points have {query_points.shape[1]} dimensions, "
            f"but hull has {hull_dims} dimensions."
        )

    # Tolerance for numerical precision (points exactly on hull boundary)
    eps = 1e-10

    # For each hyperplane equation A·x + b <= 0:
    #   - A is hull_equations[:, :-1] (normal vector)
    #   - b is hull_equations[:, -1] (offset)
    #   - If A·x + b > eps for ANY equation, point is outside
    A = hull_equations[:, :-1]  # (n_equations, D)
    b = hull_equations[:, -1]    # (n_equations,)

    # Compute A·x for all points and all equations: (M, n_equations)
    dot_products = query_points @ A.T  # (M, n_equations)
    violations = dot_products + b  # A·x + b for each point-equation pair

    # A point is outside if ANY equation is violated (A·x + b > eps)
    out_of_bounds = np.any(violations > eps, axis=1)

    return out_of_bounds


def build_bounds_report(
    hull_result: dict,
    dimension_names: list[str],
    dim_bounds: dict[str, tuple[float, float]],
) -> str:
    """Build human-readable Markdown report of convex hull bounds.

    Per D-10: the report is included in export metadata and documents:
      - Which regions of parameter space are in/out of convex hull
      - Min/max bounds for each dimension
      - Warnings about extrapolation risk when querying outside hull
      - Degeneracy status and implications

    Args:
        hull_result: dict from compute_convex_hull().
        dimension_names: Human-readable names for each dimension
            (e.g. ["Tax Rate (IR)", "Spend Level"]).
        dim_bounds: dict mapping dimension name to (min, max) tuple
            as fraction of reference value.

    Returns:
        str: Markdown-formatted bounds report suitable for inclusion
        in sidecar metadata and developer documentation.
    """
    hull_points = np.array(hull_result["hull_points"])
    n_dims = hull_result["n_dimensions"]
    is_degenerate = hull_result.get("is_degenerate", False)

    lines = []
    lines.append("# Convex Hull Bounds Report")
    lines.append("")
    lines.append(f"**Dimensions:** {n_dims}")
    lines.append(f"**Vertices:** {hull_result['n_vertices']}")
    lines.append(
        f"**Volume:** {hull_result['volume']:.6f} ({hull_result['volume_unit']})"
    )
    lines.append(f"**Degenerate:** {'Yes' if is_degenerate else 'No'}")

    if hull_result.get("degenerate_reason"):
        lines.append(f"**Degeneracy note:** {hull_result['degenerate_reason']}")
        lines.append("")
        lines.append(
            "⚠️ **Warning:** The hull is degenerate. All points are "
            "collinear or coplanar in at least one subspace. "
            "Extrapolation outside the fitted subspace is unreliable."
        )

    lines.append("")
    lines.append("## Dimension Ranges")
    lines.append("")

    if hull_points.size > 0:
        hull_mins = hull_points.min(axis=0)
        hull_maxs = hull_points.max(axis=0)

        lines.append(
            "| Dimension | Min (Hull) | Max (Hull) | Reference Range |"
        )
        lines.append(
            "|-----------|-----------|-----------|----------------|"
        )

        for d in range(n_dims):
            name = dimension_names[d] if d < len(dimension_names) else f"Dim {d+1}"
            ref_range = dim_bounds.get(name, ("—", "—"))
            ref_str = f"{ref_range[0]} – {ref_range[1]}"
            lines.append(
                f"| {name} | {hull_mins[d]:.4f} | {hull_maxs[d]:.4f} "
                f"| {ref_str} |"
            )

    lines.append("")
    lines.append("## Coverage Analysis")
    lines.append("")

    n_input = hull_result["n_input_points"]
    n_hull = hull_result["n_vertices"]
    coverage_pct = (n_hull / n_input * 100) if n_input > 0 else 0

    lines.append(f"- **Input points:** {n_input}")
    lines.append(f"- **Hull vertices:** {n_hull} ({coverage_pct:.1f}% of input)")
    lines.append(
        f"- **Interior points:** {n_input - n_hull}"
    )

    lines.append("")
    lines.append("## Extrapolation Risk")
    lines.append("")

    if is_degenerate:
        lines.append(
            "⚠️ **HIGH RISK:** The convex hull is degenerate. "
            "All queries that depart from the fitted subspace may produce "
            "unreliable extrapolations. Phase 2 interpolator should return "
            "`Option::None` for out-of-hull queries."
        )
    else:
        lines.append(
            "Queries within the convex hull bounds are interpolated reliably. "
            "Queries outside bounds require extrapolation — the Phase 2 "
            "interpolator should return `Option::None` for out-of-hull queries "
            "per the macro engine contract (D-10)."
        )

    lines.append("")
    lines.append(
        "**Recommendation:** Use the `identify_out_of_bounds()` function "
        "to validate query points before interpolation. Set out-of-bounds "
        "matrix cells to NaN/null in the exported Parquet file."
    )

    return "\n".join(lines)
