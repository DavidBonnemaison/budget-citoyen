// ShockMatrix: pre-computed macroeconomic shock matrix storage.
//
// Stores the N-dimensional grid of pre-calculated Mésange model outputs
// (GDP growth, employment change, deficit change, debt-to-GDP ratio) along
// with breakpoint vectors for each dimension and convex hull hyperplane
// equations for boundary enforcement (PITFALLS.md Pitfall 2).

/// A pre-computed macroeconomic shock matrix with grid data and convex hull
/// boundary equations.
///
/// # Grid Layout
/// The grid is stored as a flat `Vec<f64>` in C-order with shape
/// `(n_tax × n_spend × n_horizon × 4)`, where the last dimension holds:
/// - index 0: GDP growth (%)
/// - index 1: Employment change (thousands)
/// - index 2: Deficit change (% of GDP)
/// - index 3: Debt-to-GDP ratio change (pp)
///
/// # Convex Hull
/// `hull_equations` contains hyperplane equations from Phase 1's
/// `scipy.spatial.ConvexHull`. Each equation is `[a1, a2, a3, b]` where
/// `a1*x + a2*y + a3*z + b ≤ 0` defines one face of the convex hull.
pub struct ShockMatrix {
    /// Tax rate multiplier breakpoints (e.g., [0.5, 0.6, ..., 2.0])
    pub tax_bp: Vec<f64>,
    /// Spending level multiplier breakpoints (e.g., [0.7, 0.8, ..., 1.5])
    pub spend_bp: Vec<f64>,
    /// Horizon year breakpoints (e.g., [1.0, 2.0, 3.0, 4.0, 5.0])
    pub horizon_bp: Vec<f64>,
    /// Flattened C-order grid data: shape (n_tax × n_spend × n_horizon × 4)
    pub grid: Vec<f64>,
    /// Convex hull hyperplane equations from scipy.spatial.ConvexHull.
    /// Each inner Vec is `[a1, a2, a3, b]` for the hyperplane `a·x + b ≤ 0`.
    pub hull_equations: Vec<Vec<f64>>,
}

impl ShockMatrix {
    /// Create a new ShockMatrix with shape validation.
    ///
    /// # Panics
    /// Panics if `grid.len()` does not equal
    /// `tax_bp.len() × spend_bp.len() × horizon_bp.len() × 4`.
    pub fn new(
        tax_bp: Vec<f64>,
        spend_bp: Vec<f64>,
        horizon_bp: Vec<f64>,
        grid: Vec<f64>,
        hull_equations: Vec<Vec<f64>>,
    ) -> Self {
        let expected_grid_len = tax_bp.len() * spend_bp.len() * horizon_bp.len() * 4;
        assert_eq!(
            grid.len(),
            expected_grid_len,
            "grid length {} does not match shape ({} {} {} 4) = {}",
            grid.len(),
            tax_bp.len(),
            spend_bp.len(),
            horizon_bp.len(),
            expected_grid_len,
        );

        ShockMatrix {
            tax_bp,
            spend_bp,
            horizon_bp,
            grid,
            hull_equations,
        }
    }

    /// Check if a 3D point `[tax, spend, horizon]` lies inside the convex hull.
    ///
    /// Uses the hyperplane equations from Phase 1's `scipy.spatial.ConvexHull`.
    /// A point is inside the hull if it satisfies all hyperplane inequalities:
    /// `a1*x + a2*y + a3*z + b ≤ 0` (within numerical tolerance of 1e-10).
    pub fn is_inside_hull(&self, point: &[f64; 3]) -> bool {
        for eq in &self.hull_equations {
            let dot = eq[0] * point[0] + eq[1] * point[1] + eq[2] * point[2] + eq[3];
            if dot > 1e-10 {
                return false;
            }
        }
        true
    }
}
