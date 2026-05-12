"""Data preprocessing module: real data loading, cleaning, and SDV metadata preparation.

D-04: SDV `CopulaGANSynthesizer` for multi-variable dependency preservation.
D-06: Reference data from CASD microdata (TOKENIZED_PATH) with INSEE ERFS fallback.
"""

import logging
import os
import sys
from typing import Optional

import numpy as np
import pandas as pd
from sdv.metadata import SingleTableMetadata

logger = logging.getLogger(__name__)

# Canonical column set for the synthetic population
COLUMNS = [
    "profile_id",
    "age",
    "patrimoine",
    "revenu_fiscal",
    "situation_familiale",
    "nombre_parts",
    "type_activite",
    "zone_residence",
]

# Valid categorical values
SITUATION_FAMILIALE_VALUES = ["celibataire", "marie", "pacse", "veuf", "divorce", "separe"]
TYPE_ACTIVITE_VALUES = ["salarie", "independant", "fonctionnaire", "retraite", "chomeur", "etudiant", "inactif"]
ZONE_RESIDENCE_VALUES = ["zone1", "zone2", "zone3"]


def _generate_fallback_data() -> pd.DataFrame:
    """Generate a 10-row placeholder DataFrame with realistic defaults.

    Used when real data file is unavailable.
    """
    logger.warning(
        "No real data source available — using 10-row placeholder for "
        "pipeline development. Replace with real CASD/INSEE data for production."
    )
    np.random.seed(42)
    n = 10
    return pd.DataFrame({
        "profile_id": list(range(1, n + 1)),
        "age": np.random.randint(20, 80, size=n).astype(float),
        "patrimoine": np.random.exponential(100_000, size=n).round(2),
        "revenu_fiscal": np.random.exponential(25_000, size=n).round(2),
        "situation_familiale": np.random.choice(
            SITUATION_FAMILIALE_VALUES, size=n
        ),
        "nombre_parts": np.clip(np.random.normal(2.0, 1.0, size=n), 1.0, 10.0).round(1),
        "type_activite": np.random.choice(TYPE_ACTIVITE_VALUES, size=n),
        "zone_residence": np.random.choice(ZONE_RESIDENCE_VALUES, size=n),
    })


def load_real_data(
    source_path: Optional[str] = None,
    source_type: str = "csv",
) -> pd.DataFrame:
    """Load real microdata from CASD or INSEE ERFS CSV/Parquet.

    Args:
        source_path: Path to the data file. If None, checks TOKENIZED_PATH env var.
        source_type: File format: "csv" or "parquet".

    Returns:
        DataFrame with canonical columns. Returns 10-row placeholder if file
        is nonexistent.

    D-06: Accepts TOKENIZED_PATH env var for CASD path; warns when falling back.
    """
    if source_path is None:
        source_path = os.environ.get("TOKENIZED_PATH")

    if source_path is None:
        logger.warning(
            "No source_path provided and TOKENIZED_PATH not set. "
            "Falling back to placeholder data."
        )
        return _generate_fallback_data()

    if not os.path.exists(source_path):
        logger.warning(
            f"Data file not found: {source_path}. "
            "Falling back to placeholder data for pipeline development."
        )
        return _generate_fallback_data()

    logger.info(f"Loading real data from: {source_path}")
    try:
        if source_type == "parquet":
            df = pd.read_parquet(source_path)
        else:
            df = pd.read_csv(source_path)
    except Exception as e:
        logger.error(f"Failed to load {source_path}: {e}")
        logger.warning("Falling back to placeholder data.")
        return _generate_fallback_data()

    # Log data shape only — never log records (T-02-01 mitigation)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns from {source_path}")

    return df


def preprocess_real_data(df: pd.DataFrame) -> pd.DataFrame:
    """Clean and prepare real data for CopulaGAN training.

    Operations:
        - Clip age to [18, 100]
        - Clip patrimoine to [0, 99th percentile]
        - Clip revenu_fiscal to [0, 99.9th percentile]
        - Drop rows with null revenu_fiscal or age
        - Add profile_id if missing

    Args:
        df: Raw DataFrame from load_real_data.

    Returns:
        Cleaned DataFrame ready for metadata/training.
    """
    df = df.copy()
    initial_count = len(df)
    initial_cols = len(df.columns)
    logger.info(f"Preprocessing {initial_count} rows, {initial_cols} columns")

    # Clip age
    if "age" in df.columns:
        df["age"] = df["age"].clip(lower=18, upper=100)

    # Clip patrimoine at 99th percentile
    if "patrimoine" in df.columns:
        p99_patrimoine = df["patrimoine"].quantile(0.99)
        df["patrimoine"] = df["patrimoine"].clip(lower=0, upper=p99_patrimoine)

    # Clip revenu_fiscal at 99.9th percentile
    if "revenu_fiscal" in df.columns:
        p999_revenu = df["revenu_fiscal"].quantile(0.999)
        df["revenu_fiscal"] = df["revenu_fiscal"].clip(lower=0, upper=p999_revenu)

    # Drop rows missing critical fields
    before_drop = len(df)
    if "revenu_fiscal" in df.columns:
        df = df.dropna(subset=["revenu_fiscal"])
    if "age" in df.columns:
        df = df.dropna(subset=["age"])
    after_drop = len(df)
    if before_drop != after_drop:
        logger.info(f"Dropped {before_drop - after_drop} rows with null revenue/age")

    # Add profile_id if missing
    if "profile_id" not in df.columns:
        df["profile_id"] = range(1, len(df) + 1)
        logger.info("Added profile_id column (sequential 1..N)")

    # Ensure profile_id is first column and integer
    cols = ["profile_id"] + [c for c in df.columns if c != "profile_id"]
    df = df[cols]
    df["profile_id"] = df["profile_id"].astype(int)

    logger.info(
        f"Preprocessing complete: {len(df)} rows remaining "
        f"({initial_count - len(df)} removed)"
    )

    return df


def build_metadata(df: pd.DataFrame) -> SingleTableMetadata:
    """Create SDV SingleTableMetadata with column type definitions.

    Defines per-column sdtype based on RESEARCH.md Pattern 3:
        - age: numerical, 0-120
        - patrimoine: numerical
        - revenu_fiscal: numerical
        - situation_familiale: categorical (celibataire, marie, pacse, veuf, divorce)
        - nombre_parts: numerical, 1.0-10.0
        - type_activite: categorical (salarie, independant, retraite, chomeur, etudiant, inactif)
        - zone_residence: categorical (zone1, zone2, zone3)
        - profile_id: primary_key

    Then calls metadata.detect_from_dataframe(df) for remaining column properties.

    Args:
        df: Preprocessed DataFrame.

    Returns:
        SDV SingleTableMetadata ready for synthesizer configuration.
    """
    metadata = SingleTableMetadata()

    # Explicit column type definitions
    metadata.add_column("age", sdtype="numerical")
    metadata.add_column("patrimoine", sdtype="numerical")
    metadata.add_column("revenu_fiscal", sdtype="numerical")
    metadata.add_column("situation_familiale", sdtype="categorical")
    metadata.add_column("nombre_parts", sdtype="numerical")
    metadata.add_column("type_activite", sdtype="categorical")
    metadata.add_column("zone_residence", sdtype="categorical")
    metadata.add_column("profile_id", sdtype="id")

    # Set primary key
    metadata.set_primary_key("profile_id")

    # Detect remaining properties from the dataframe
    metadata.detect_from_dataframe(df)

    logger.info(
        f"Metadata built: {len(metadata.columns)} columns, "
        f"primary_key={metadata.primary_key}"
    )

    return metadata
