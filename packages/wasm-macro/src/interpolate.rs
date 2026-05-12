// Multi-linear interpolation for macroeconomic shock matrix queries.
//
// Uses the `interpn` crate (v0.11.0) for N-dimensional multi-linear
// interpolation over the pre-computed Mésange shock matrix grid.
// Enforces convex hull boundary checking before calling interpn to
// prevent silent extrapolation (PITFALLS.md Pitfall 2).
//
// interpn API convention (from source): obs is dimension-major —
// obs[i] contains all coordinates for dimension i, and obs.len() == ndims.
// vals must have exactly product(grid_sizes) elements, so we add a 4th
// "output feature index" dimension [0.0, 1.0, 2.0, 3.0] to query all
// four output variables (gdp_growth, employment, deficit, debt) in one call.

use crate::matrix::ShockMatrix;
use budget_citoyen_core::types::MacroResult;
use interpn::multilinear::rectilinear;

/// Perform multi-linear interpolation at a single (tax, spend, horizon) point.
///
/// # Input validation
/// - All inputs must be finite (NaN/Infinity rejected — T-02-30 defense-in-depth).
/// - `tax` and `spend` must be > 0.0.
/// - `horizon` must be in [1.0, 5.0].
/// - Point must lie within the pre-computed convex hull.
///
/// # Grid convention
/// The 4D grid is indexed as (tax, spend, horizon, feature) where feature is
/// [0=gdp_growth, 1=employment, 2=deficit, 3=debt] in C-order.
///
/// # Returns
/// - `Some(MacroResult)` with single-element trajectory vectors if the point
///   lies inside the convex hull and interpolation succeeds.
/// - `None` if the point is outside the convex hull or fails input validation
///   (never silently extrapolates — see PITFALLS.md Pitfall 2).
///
/// # Panics
/// Panics if interpn fails for an in-bounds point (indicates grid corruption).
pub fn interpolate_at_point(
    matrix: &ShockMatrix,
    tax: f64,
    spend: f64,
    horizon: f64,
) -> Option<MacroResult> {
    // Input validation — defense-in-depth (T-02-30, T-02-31)
    if !tax.is_finite() || !spend.is_finite() || !horizon.is_finite() {
        return None; // Reject NaN/Infinity (T-02-30)
    }
    if tax <= 0.0 || spend <= 0.0 {
        return None;
    }
    if !(1.0..=5.0).contains(&horizon) {
        return None;
    }

    let point = [tax, spend, horizon];

    // Gate: convex hull containment check (PITFALLS.md Pitfall 2)
    if !matrix.is_inside_hull(&point) {
        return None;
    }

    // Prepare interpn inputs — 4D: tax, spend, horizon, feature_index
    // interpn obs convention (dimension-major): obs[i] = all coordinates for dim i
    let feature_bp: [f64; 4] = [0.0, 1.0, 2.0, 3.0];
    let grids: &[&[f64]] = &[
        &matrix.tax_bp,
        &matrix.spend_bp,
        &matrix.horizon_bp,
        &feature_bp,
    ];
    let obs: &[&[f64]] = &[
        &[tax; 4],
        &[spend; 4],
        &[horizon; 4],
        &feature_bp, // query at exact feature breakpoints
    ];
    let mut out = [0.0_f64; 4];

    // Perform multi-linear interpolation
    rectilinear::interpn(grids, &matrix.grid, obs, &mut out)
        .expect("interpn should succeed for validated in-bounds inputs");

    // Map interpn output to MacroResult fields
    // out[i] corresponds to feature breakpoint i
    Some(MacroResult {
        deficit_trajectory: vec![out[2]],
        debt_trajectory: vec![out[3]],
        gdp_growth_trajectory: vec![out[0]],
        employment_trajectory: vec![out[1]],
        is_out_of_bounds: false,
        warning_message: None,
    })
}
