"""Synthetic population pipeline for Budget Citoyen.

DATA-02 + DATA-03 — CopulaGAN training on real microdata,
OpenDP differential privacy with formal epsilon <= 1.0 proof,
SDMetrics quality + privacy evaluation, and JSON export with integrity hashes.
"""

from pathlib import Path
from typing import Optional

from .preprocess import load_real_data, preprocess_real_data, build_metadata
from .train import train_synthesizer, generate_synthetic_population
from .insee_loader import InseeAggregateLoader, build_insee_dataframe

__all__ = [
    "load_real_data",
    "preprocess_real_data",
    "build_metadata",
    "train_synthesizer",
    "generate_synthetic_population",
    "InseeAggregateLoader",
    "build_insee_dataframe",
    "generate_from_insee",
    "export_with_dp",
]


def export_with_dp(
    pipeline_result: dict,
    output_dir: Optional[str] = None,
) -> str:
    """Run DP injection on the synthetic population and export to JSON.

    Takes the output of generate_from_insee() from Plan 04, runs
    inject_dp_privacy() to add differential privacy noise to
    aggregate statistics, builds the French-language privacy
    statement, and exports the complete population-v2025.1.json
    with SHA-256 hash and .meta.json sidecar per D-11.

    Args:
        pipeline_result: dict from generate_from_insee() with keys:
            synthetic_df, quality_report
        output_dir: Output directory for population JSON.

    Returns:
        Path to the exported population JSON file.
    """
    from .dp_inject import inject_dp_privacy, build_privacy_statement
    from .export import export_synthetic_population

    synthetic_df = pipeline_result["synthetic_df"]

    # Run DP proof
    synthetic_df, dp_report = inject_dp_privacy(synthetic_df, epsilon_budget=1.0)

    # Add privacy statement to report
    privacy_statement = build_privacy_statement(dp_report, reference_year=2025)
    dp_report["privacy_statement"] = privacy_statement

    # Determine output path
    if output_dir is None:
        output_dir = str(
            Path(__file__).resolve().parent.parent.parent / "dist"
        )

    dist_path = Path(output_dir)
    dist_path.mkdir(parents=True, exist_ok=True)
    output_path = dist_path / "population-v2025.1.json"

    # Export with metadata
    exported = export_synthetic_population(
        synthetic_df, dp_report, str(output_path), reference_year=2025,
    )

    return exported


def generate_from_insee(
    epochs: int = 500,
    seed: int = 42,
    num_rows: int = 50000,
) -> dict:
    """Run the full CopulaGAN train + evaluate pipeline from INSEE aggregate data.

    Orchestrates the data → preprocess → train → generate → evaluate chain
    in a single call. Uses the InseeAggregateLoader (Plan 02.2-02) as the
    data source, feeds data through preprocess_real_data() and build_metadata(),
    trains a CopulaGANSynthesizer, generates synthetic profiles, and runs
    SDMetrics quality + privacy evaluation.

    Args:
        epochs: Training epochs (500 for full, 10 for CI).
        seed: Random seed for reproducibility.
        num_rows: Number of rows to generate (50000 for full, 2000 for CI).

    Returns:
        dict with keys:
            - synthesizer: Trained CopulaGANSynthesizer
            - synthetic_df: Generated synthetic population DataFrame
            - quality_report: SDMetrics evaluation results (fidelity + privacy)
            - metadata: SDV SingleTableMetadata
            - real_df: Preprocessed real data used for training
    """
    from .insee_loader import InseeAggregateLoader
    from .evaluate import generate_quality_report

    # 1. Load INSEE aggregate-derived data
    loader = InseeAggregateLoader(seed=seed, num_rows=num_rows)
    real_df = loader.load()

    # 2. Preprocess real data
    processed_df = preprocess_real_data(real_df)

    # 3. Build SDV metadata
    metadata = build_metadata(processed_df)

    # 4. Train CopulaGAN synthesizer
    synthesizer = train_synthesizer(metadata, processed_df, epochs=epochs)

    # 5. Generate synthetic population
    synthetic_df = generate_synthetic_population(synthesizer, num_rows=num_rows)

    # 6. Evaluate quality
    quality_report = generate_quality_report(processed_df, synthetic_df, metadata)

    return {
        "synthesizer": synthesizer,
        "synthetic_df": synthetic_df,
        "quality_report": quality_report,
        "metadata": metadata,
        "real_df": processed_df,
    }
