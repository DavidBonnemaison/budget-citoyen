// Trajectory projection: accumulates per-year interpolations into
// multi-year macroeconomic projection vectors.
//
// Calls `interpolate_at_point` for each horizon year and accumulates
// the results into `Vec<f64>` trajectory arrays.

use crate::interpolate::interpolate_at_point;
use crate::matrix::ShockMatrix;
use budget_citoyen_core::types::MacroResult;

/// Project a macroeconomic trajectory over `horizon_years` by interpolating
/// each year independently.
///
/// # Parameters
/// - `matrix`: The pre-computed shock matrix with grid data and convex hull.
/// - `tax`: Tax rate multiplier (must be within convex hull bounds).
/// - `spend`: Spending level multiplier (must be within convex hull bounds).
/// - `horizon_years`: Number of years to project (1-5 for standard grid).
///
/// # Returns
/// - `Some(MacroResult)` with trajectory vectors of length `horizon_years` if
///   all per-year interpolations succeed (all points inside convex hull).
/// - `None` if any year's interpolated point falls outside the convex hull.
///   No partial results are returned.
pub fn project_trajectory(
    matrix: &ShockMatrix,
    tax: f64,
    spend: f64,
    horizon_years: usize,
) -> Option<MacroResult> {
    let mut deficit: Vec<f64> = Vec::with_capacity(horizon_years);
    let mut debt: Vec<f64> = Vec::with_capacity(horizon_years);
    let mut gdp_growth: Vec<f64> = Vec::with_capacity(horizon_years);
    let mut employment: Vec<f64> = Vec::with_capacity(horizon_years);

    for year in 1..=horizon_years {
        let yr = year as f64;
        let result = interpolate_at_point(matrix, tax, spend, yr)?;

        // Accumulate single-year values into trajectories
        deficit.push(result.deficit_trajectory[0]);
        debt.push(result.debt_trajectory[0]);
        gdp_growth.push(result.gdp_growth_trajectory[0]);
        employment.push(result.employment_trajectory[0]);
    }

    Some(MacroResult {
        deficit_trajectory: deficit,
        debt_trajectory: debt,
        gdp_growth_trajectory: gdp_growth,
        employment_trajectory: employment,
        is_out_of_bounds: false,
        warning_message: None,
    })
}
