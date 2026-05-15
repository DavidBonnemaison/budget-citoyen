"""SDMetrics quality and privacy evaluation for synthetic population.

D-07: SDMetrics quality evaluation validates statistical fidelity,
privacy metrics, and detection reports before accepting the synthetic
population into CI.

Per RESEARCH.md Pattern 6 (lines 650-676).
"""

import json
import logging
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from sdmetrics.reports.single_table import QualityReport
from sdmetrics.single_table import DisclosureProtectionEstimate

logger = logging.getLogger(__name__)


def evaluate_quality(
    real_data: pd.DataFrame,
    synthetic_data: pd.DataFrame,
    metadata: Any,
    output_dir: Optional[Path] = None,
) -> dict:
    """Generate SDMetrics QualityReport for statistical fidelity evaluation.

    Produces scores for:
        - Overall quality score
        - Column Shapes score
        - Column Pair Trends score

    Args:
        real_data: Original real data DataFrame.
        synthetic_data: Generated synthetic population DataFrame.
        metadata: SDV SingleTableMetadata instance.
        output_dir: If provided, save quality_report.json here.

    Returns:
        dict with keys: overall_score, column_shapes_score,
            column_pair_trends_score, report_path.
    """
    logger.info("Generating SDMetrics QualityReport...")

    report = QualityReport()
    # SDMetrics 0.28+ requires metadata as a dict, not SingleTableMetadata object
    meta = metadata.to_dict() if hasattr(metadata, 'to_dict') else metadata
    report.generate(real_data, synthetic_data, meta)

    # Extract scores from the report
    # SDMetrics 0.28+ get_details returns DataFrame for Column Shapes
    overall_score = report.get_score()
    column_shapes_details = report.get_details("Column Shapes")
    if hasattr(column_shapes_details, 'iloc'):
        # DataFrame — average the Score column
        column_shapes_score = float(column_shapes_details["Score"].mean())
    else:
        column_shapes_score = (column_shapes_details or {}).get("Score", 0.0)

    column_pair_details = report.get_details("Column Pair Trends")
    if hasattr(column_pair_details, 'iloc'):
        column_pair_trends_score = float(column_pair_details["Score"].mean())
    else:
        column_pair_trends_score = (column_pair_details or {}).get("Score", 0.0)

    scores = {
        "overall_score": overall_score,
        "column_shapes_score": column_shapes_score,
        "column_pair_trends_score": column_pair_trends_score,
    }

    logger.info(
        f"Quality scores: overall={scores['overall_score']:.4f}, "
        f"shapes={scores['column_shapes_score']:.4f}, "
        f"trends={scores['column_pair_trends_score']:.4f}"
    )

    # Save to output directory if specified
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "quality_report.json"
        with open(report_path, "w") as f:
            json.dump(scores, f, indent=2, ensure_ascii=False)
        scores["report_path"] = str(report_path)
        logger.info(f"Quality report saved to {report_path}")

    return scores


def evaluate_privacy(
    real_data: pd.DataFrame,
    synthetic_data: pd.DataFrame,
) -> dict:
    """Run SDMetrics DisclosureProtectionEstimate for privacy validation.

    Configuration:
        - known_column_names: ["age", "situation_familiale"] (non-sensitive)
        - sensitive_column_names: ["patrimoine", "revenu_fiscal"]
        - num_rows_subsample: 5000
        - num_iterations: 50

    DPE score >= 0.7 indicates sufficient protection.

    Args:
        real_data: Original real data DataFrame.
        synthetic_data: Generated synthetic population DataFrame.

    Returns:
        dict with keys: dpe_score (float), is_protected (bool).
    """
    logger.info("Running DisclosureProtectionEstimate...")

    dpe_score = DisclosureProtectionEstimate.compute(
        real_data=real_data,
        synthetic_data=synthetic_data,
        known_column_names=["age", "situation_familiale"],
        sensitive_column_names=["patrimoine", "revenu_fiscal"],
        num_rows_subsample=5000,
        num_iterations=50,
    )

    is_protected = dpe_score >= 0.7

    logger.info(
        f"DisclosureProtectionEstimate: score={dpe_score:.4f}, "
        f"is_protected={is_protected} (threshold=0.7)"
    )

    return {
        "dpe_score": dpe_score,
        "is_protected": is_protected,
    }


def generate_quality_report(
    real_data: pd.DataFrame,
    synthetic_data: pd.DataFrame,
    metadata: Any,
    output_dir: Optional[Path] = None,
) -> dict:
    """Combine SDMetrics quality and privacy evaluation into a single report.

    Args:
        real_data: Original real data DataFrame.
        synthetic_data: Generated synthetic population DataFrame.
        metadata: SDV SingleTableMetadata instance.
        output_dir: Directory for report artifacts.

    Returns:
        dict with keys: fidelity (from evaluate_quality),
            privacy (from evaluate_privacy).
    """
    fidelity = evaluate_quality(real_data, synthetic_data, metadata, output_dir)
    privacy = evaluate_privacy(real_data, synthetic_data)

    combined = {
        "fidelity": fidelity,
        "privacy": privacy,
    }

    logger.info(
        f"Combined quality report: "
        f"overall={fidelity.get('overall_score', 'N/A')}, "
        f"dpe={privacy.get('dpe_score', 'N/A')}"
    )

    return combined
