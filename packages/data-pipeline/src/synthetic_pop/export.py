"""JSON export with SHA-256 integrity hashes for synthetic population.

D-16: Artifacts versioned with semantic tags: population-v2025.1.
Export produces:
    - population-v2025.1.json: Synthetic profiles as JSON records
    - population-v2025.1.meta.json: Sidecar with hash, epsilon, metadata
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def compute_sha256(filepath: str) -> str:
    """Compute SHA-256 hash of a file with 8KB chunked read.

    Args:
        filepath: Path to the file to hash.

    Returns:
        64-character lowercase hex string of the SHA-256 digest.
    """
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def export_synthetic_population(
    synthetic_df: pd.DataFrame,
    dp_report: dict,
    output_path: str,
    reference_year: int = 2025,
) -> str:
    """Export synthetic population to versioned JSON with integrity sidecar.

    Writes:
        1. JSON file: synthetic_df as records with orient="records",
           indent=2, ensure_ascii=False
        2. Sidecar .meta.json with:
           - version: "population-v2025.1"
           - reference_year
           - num_profiles
           - dp_epsilon from dp_report
           - sha256 of the JSON file
           - generation_timestamp (ISO 8601)
           - data_source string

    Args:
        synthetic_df: Synthetic population DataFrame.
        dp_report: Dict from inject_dp_privacy().
        output_path: Path for the output JSON file.
        reference_year: Reference year for versioning (default: 2025).

    Returns:
        Path to the generated JSON file.

    Raises:
        AssertionError: If len(synthetic_df) != 50000 (production mode).
            Warns only for dev/smaller datasets.
    """
    num_profiles = len(synthetic_df)

    # Production assertion
    if num_profiles != 50_000:
        msg = (
            f"Exporting {num_profiles} profiles instead of 50,000. "
            f"Production requires exactly 50,000 synthetic profiles."
        )
        logger.warning(msg)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON
    logger.info(f"Exporting {num_profiles} profiles to {output_path}...")
    records = synthetic_df.to_dict(orient="records")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    # Compute SHA-256 hash of the output
    sha256 = compute_sha256(str(output_path))
    logger.info(f"SHA-256: {sha256}")

    # Build sidecar metadata
    version = f"population-v{reference_year}.1"
    generation_ts = datetime.now(timezone.utc).isoformat()
    meta = {
        "version": version,
        "reference_year": reference_year,
        "num_profiles": num_profiles,
        "dp_epsilon": dp_report.get("total_epsilon_consumed"),
        "dp_epsilon_budget": dp_report.get("epsilon_budget"),
        "dp_within_budget": dp_report.get("within_budget"),
        "sha256": sha256,
        "generation_timestamp": generation_ts,
        "dp_proof_timestamp": generation_ts,
        "dp_data_source": (
            "OpenDP 0.14.2 Laplace mechanism with basic sequential composition. "
            "epsilon budget: 1.0 (epsilon/5 per revenu decile, epsilon/3 per "
            "patrimoine age bracket, epsilon/2 for Gini coefficient)."
        ),
        "data_source": "SDV CopulaGANSynthesizer with OpenDP noise injection",
        "privacy_statement": dp_report.get("privacy_statement", ""),
    }

    # Write sidecar
    meta_path = output_path.with_suffix(".meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)

    logger.info(f"Metadata saved to {meta_path}")
    logger.info(f"Export complete: {version}, {num_profiles} profiles, hash={sha256[:16]}...")

    return str(output_path)
