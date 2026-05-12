use wasm_bindgen::prelude::*;

pub mod matrix;
pub mod interpolate;
pub mod projection;

#[cfg(test)]
mod tests {
    use ndarray::Array3;
    use postcard;
    use serde::{Deserialize, Serialize};

    /// Postcard serialization round-trip test.
    /// Demonstrates the shock matrix binary loading strategy:
    /// 1. Load flat `Vec<f64>` from postcard+gzip HTTP response
    /// 2. Reshape into ndarray grid matching interpn conventions
    /// 3. Query via interpn::multilinear
    #[test]
    fn postcard_roundtrip_shock_matrix() {
        // Simulate a 3D shock matrix: tax_rate(5) × spending(5) × horizon(3) → 4 outputs
        let n_tax = 5usize;
        let n_spend = 5;
        let n_horizon = 3;
        let n_outputs = 4;
        let total_elements = n_tax * n_spend * n_horizon * n_outputs;

        // Create sample grid data (flat Vec<f64>)
        let grid_flat: Vec<f64> = (0..total_elements).map(|i| i as f64 * 0.1).collect();

        // Serialize to postcard (binary, ~10MB for full 50K-point grid)
        let serialized: Vec<u8> = postcard::to_allocvec(&grid_flat)
            .expect("postcard serialization should succeed");

        // Verify postcard output is compact (no schema overhead)
        let expected_min_size = total_elements * 8; // f64 = 8 bytes each
        assert!(
            serialized.len() >= expected_min_size,
            "postcard payload size {} should be >= minimum f64 data size {}",
            serialized.len(),
            expected_min_size
        );
        assert!(
            serialized.len() < expected_min_size + 100,
            "postcard overhead is minimal (< 100 bytes for Vec<f64>)"
        );

        // Deserialize back
        let deserialized: Vec<f64> = postcard::from_bytes(&serialized)
            .expect("postcard deserialization should succeed");
        assert_eq!(deserialized.len(), total_elements, "element count preserved");

        // Reshape into 4D: (tax, spend, horizon, outputs)
        let grid = Array3::from_shape_vec(
            (n_tax, n_spend, n_horizon * n_outputs),
            deserialized.clone(),
        )
        .expect("reshape into 3D Array3 should succeed");

        // Verify specific grid values after reshape (use approx for f64)
        assert!((grid[[0, 0, 0]] - 0.0).abs() < 1e-15);
        assert!((grid[[0, 0, 1]] - 0.1).abs() < 1e-15);
        // Last element: index 4 in dim0, 4 in dim1, 11 in dim2 (5*5*12=300 elements)
        assert!((grid[[4, 4, 11]] - 29.9).abs() < 1e-12);

        // Round-trip integrity: re-serialize and compare
        let reserialized = postcard::to_allocvec(&deserialized).unwrap();
        assert_eq!(serialized, reserialized, "round-trip byte-identical");

        // Estimate: full grid (tax_rate 10 × spending 10 × horizon 5 × 4 outputs)
        // = 2000 f64 = 16,000 bytes raw → ~3-5 KB postcard+gzip
        let full_grid_elements = 10 * 10 * 5 * 4; // 2000
        let full_grid_bytes = full_grid_elements * 8; // 16,000 bytes
        assert!(full_grid_bytes < 1_000_000, "full grid fits in < 1MB raw");
    }

    /// Verify that postcard works with serde-derived structs (for metadata)
    #[test]
    fn postcard_struct_roundtrip() {
        #[derive(Serialize, Deserialize, PartialEq, Debug)]
        struct ShockMatrixMetadata {
            version: String,
            reference_year: u16,
            dim_names: Vec<String>,
            breakpoints: Vec<Vec<f64>>,
        }

        let meta = ShockMatrixMetadata {
            version: "shockmatrix-v2025.1".into(),
            reference_year: 2025,
            dim_names: vec![
                "tax_rate".into(),
                "spending_level".into(),
                "horizon_year".into(),
            ],
            breakpoints: vec![
                vec![0.0, 0.25, 0.5, 0.75, 1.0],
                vec![0.0, 0.5, 1.0],
                vec![2025.0, 2026.0, 2027.0],
            ],
        };

        let bytes = postcard::to_allocvec(&meta).expect("struct serialization ok");
        let decoded: ShockMatrixMetadata =
            postcard::from_bytes(&bytes).expect("struct deserialization ok");

        assert_eq!(decoded, meta, "struct round-trip preserves all fields");
        assert_eq!(decoded.reference_year, 2025);
        assert_eq!(decoded.dim_names.len(), 3);
    }

    /// Verify the interpn crate compiles and basic API works
    #[test]
    fn interpn_basic_api() {
        // Create a 1D regular grid: f(x) at x = 0.0, 1.0, 2.0
        // values: f(0)=0.0, f(1)=2.0, f(2)=4.0
        let dims = &[3usize];
        let starts = &[0.0_f64];
        let steps = &[1.0_f64];
        let vals = &[0.0_f64, 2.0, 4.0];
        let obs = &[&[0.5_f64][..]];
        let mut out = [0.0_f64];

        let result = interpn::multilinear::regular::interpn(
            dims, starts, steps, vals, obs, &mut out,
        );

        assert!(result.is_ok(), "interpn multilinear::regular::interpn should succeed");
        assert!((out[0] - 1.0).abs() < 1e-10, "f(0.5) = 1.0");
    }
}
