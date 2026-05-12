"""CopulaGAN training module for synthetic population generation.

D-04: SDV `CopulaGANSynthesizer` for multi-variable dependency preservation
(age ↔ patrimony ↔ income covariance). Configured per RESEARCH.md Pattern 3.
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd
from sdv.metadata import SingleTableMetadata
from sdv.single_table import CopulaGANSynthesizer

logger = logging.getLogger(__name__)

# Default checkpoint directory for trained models
DEFAULT_MODEL_DIR = Path("models")


def train_synthesizer(
    metadata: SingleTableMetadata,
    real_data: pd.DataFrame,
    epochs: int = 500,
    model_dir: Optional[Path] = None,
) -> CopulaGANSynthesizer:
    """Train a CopulaGANSynthesizer on real microdata.

    Per RESEARCH.md Pattern 3:
        - enforce_min_max_values=True (keep within real data ranges)
        - enforce_rounding=True (match real data decimal precision)
        - numerical_distributions: age=beta, patrimoine=gamma, revenu_fiscal=gamma
        - epochs=500 (sufficient for 50K profiles)
        - verbose=True for training progress

    Saves the trained model to {model_dir}/{epochs}epochs/ via synthesizer.save().

    Args:
        metadata: SDV SingleTableMetadata with column type definitions.
        real_data: Preprocessed real data DataFrame.
        epochs: Number of training epochs (default: 500).
        model_dir: Directory for model checkpoints. Defaults to models/.

    Returns:
        Trained CopulaGANSynthesizer instance ready for sampling.
    """
    logger.info(
        f"Initializing CopulaGANSynthesizer: epochs={epochs}, "
        f"enforce_min_max_values=True, enforce_rounding=True"
    )

    synthesizer = CopulaGANSynthesizer(
        metadata,
        enforce_min_max_values=True,
        enforce_rounding=True,
        numerical_distributions={
            "age": "beta",
            "patrimoine": "gamma",
            "revenu_fiscal": "gamma",
        },
        epochs=epochs,
        verbose=True,
    )

    logger.info(f"Training CopulaGAN on {len(real_data)} rows for {epochs} epochs...")
    synthesizer.fit(real_data)

    # Save model checkpoint
    if model_dir is None:
        model_dir = DEFAULT_MODEL_DIR
    checkpoint_dir = model_dir / f"{epochs}epochs"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = checkpoint_dir / "synthesizer.pkl"
    synthesizer.save(str(checkpoint_path))
    logger.info(f"Model saved to {checkpoint_path}")

    return synthesizer


def generate_synthetic_population(
    synthesizer: CopulaGANSynthesizer,
    num_rows: int = 50_000,
) -> pd.DataFrame:
    """Generate synthetic population from trained CopulaGAN.

    Samples the specified number of rows and validates:
        - No nulls in critical columns (age, patrimoine, revenu_fiscal)
        - Output has exactly num_rows rows

    Args:
        synthesizer: Trained CopulaGANSynthesizer.
        num_rows: Number of synthetic profiles to generate (default: 50,000).

    Returns:
        DataFrame with num_rows synthetic profiles.

    Raises:
        AssertionError: If critical columns contain nulls.
        AssertionError: If row count mismatch (strict for production, warn-only for dev).
    """
    logger.info(f"Generating {num_rows:,} synthetic profiles...")
    synthetic_df = synthesizer.sample(num_rows=num_rows)

    # Validate no nulls in critical columns
    critical_cols = ["age", "patrimoine", "revenu_fiscal"]
    null_counts = synthetic_df[critical_cols].isnull().sum()
    null_cols = null_counts[null_counts > 0]
    if not null_cols.empty:
        logger.error(f"Null values found in critical columns: {dict(null_cols)}")
        raise AssertionError(
            f"Critical columns contain nulls: {dict(null_cols)}"
        )

    actual_rows = len(synthetic_df)
    if actual_rows != num_rows:
        msg = (
            f"Row count mismatch: expected {num_rows}, got {actual_rows}"
        )
        if num_rows == 50_000:
            # Production: strict assertion
            logger.error(msg)
            raise AssertionError(msg)
        else:
            # Dev: warning only
            logger.warning(msg)

    logger.info(
        f"Synthetic population generated: {actual_rows} rows, "
        f"{len(synthetic_df.columns)} columns"
    )

    return synthetic_df
