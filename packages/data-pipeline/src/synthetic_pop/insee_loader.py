"""INSEE aggregate data loader for synthetic population generation.

Implements the D-03 common tabular interface: a `load(source_type: str) -> pd.DataFrame`
protocol that produces microdata rows sampled from publicly available INSEE aggregate
distribution tables (ERFS, Recensement, Enquête Patrimoine, Enquête Emploi).

The default path constructs a synthetic dataset from known French statistical marginal
distributions when no source file is available. This allows the CopulaGAN pipeline to
train on 50K rows with realistic univariate marginals, while the copula structure
learns joint dependencies from the independent samples.

When CASD microdata becomes available, the loader is swapped via the common tabular
interface — the rest of the pipeline is unchanged.

References:
  - INSEE Recensement 2023 — age pyramid (beta distribution mode ~45)
  - INSEE Enquête Patrimoine 2021 — wealth distribution (log-normal, median ~€115K)
  - INSEE ERFS 2021 — revenu_fiscal decile distribution (gamma, mean ~€30K)
  - INSEE Enquête Emploi 2023 — activity type distribution
  - D-01: INSEE aggregate tables as primary data source until CASD access
  - D-03: Common tabular interface (load → preprocess → train → generate → export)
"""

import logging
import os
from typing import Optional

import numpy as np
import pandas as pd

from .preprocess import (
    COLUMNS,
    SITUATION_FAMILIALE_VALUES,
    TYPE_ACTIVITE_VALUES,
    ZONE_RESIDENCE_VALUES,
)

logger = logging.getLogger(__name__)


def _sample_age(rng: np.random.Generator, num_rows: int) -> np.ndarray:
    """Sample ages from French age pyramid (INSEE Recensement 2023).

    Beta distribution scaled to 18-100, mode ~45 years.
    """
    raw = rng.beta(a=2.5, b=3.0, size=num_rows)
    return (raw * 82 + 18).astype(int).astype(float)


def _sample_patrimoine(rng: np.random.Generator, num_rows: int) -> np.ndarray:
    """Sample wealth from log-normal matching Enquête Patrimoine 2021.

    Median ~€115K, mean ~€230K. Clipped to [0, 10M].
    """
    raw = rng.normal(loc=11.65, scale=1.2, size=num_rows)
    return np.clip(np.exp(raw), 0, 10_000_000).round(2)


def _sample_revenu_fiscal(rng: np.random.Generator, num_rows: int) -> np.ndarray:
    """Sample fiscal income from gamma matching ERFS 2021 decile distribution.

    Median ~€22K, mean ~€30K. Clipped to [0, 500K].
    """
    raw = rng.gamma(shape=2.0, scale=15000, size=num_rows)
    return np.clip(raw, 0, 500_000).round(2)


def _sample_situation_familiale(rng: np.random.Generator, num_rows: int) -> np.ndarray:
    """Sample family situation from INSEE demographic distribution.

    ~40% marie, ~30% celibataire, ~10% divorce, ~8% pacse, ~7% veuf, ~5% separe.
    """
    return rng.choice(
        SITUATION_FAMILIALE_VALUES,
        size=num_rows,
        p=[0.30, 0.40, 0.08, 0.07, 0.10, 0.05],
    )


def _sample_nombre_parts(
    rng: np.random.Generator, situation: np.ndarray
) -> np.ndarray:
    """Derive nombre_parts from situation_familiale + random children count.

    Married/PACSed → 2.0 base. Celibataire → 1.0 base.
    Children = Poisson(λ=1.2) clamped to 0-19, +0.5 part per child.
    Rounded to nearest 0.5, clamped to [1.0, 10.0].
    """
    is_couple = np.isin(situation, ["marie", "pacse"])
    base_parts = np.where(is_couple, 2.0, 1.0)
    children = np.clip(rng.poisson(lam=1.2, size=len(situation)), 0, 19)
    parts = base_parts + children * 0.5
    # Round to nearest 0.5
    parts = np.round(parts * 2) / 2
    return np.clip(parts, 1.0, 10.0)


def _sample_type_activite(
    rng: np.random.Generator, num_rows: int, ages: np.ndarray
) -> np.ndarray:
    """Sample activity type from INSEE Enquête Emploi 2023 distribution.

    ~45% salarie, ~21% retraite, ~8% independant, ~6% fonctionnaire,
    ~7% chomeur, ~8% etudiant, ~5% inactif.

    Age-conditional adjustments:
      - age >= 65 → higher probability of retraite
      - age < 25 → higher probability of etudiant or chomeur
    """
    # Base probabilities
    probs = np.array([0.45, 0.08, 0.06, 0.21, 0.07, 0.08, 0.05])

    # Age-conditional adjustments
    is_elderly = ages >= 65
    is_young = ages < 25

    result = np.empty(num_rows, dtype=object)
    for i in range(num_rows):
        p = probs.copy()
        if is_elderly[i]:
            p[3] += 0.25  # boost retraite
            p = p / p.sum()
        elif is_young[i]:
            p[5] += 0.30  # boost etudiant
            p[4] += 0.10  # boost chomeur
            p = p / p.sum()
        result[i] = rng.choice(TYPE_ACTIVITE_VALUES, p=p)
    return result


def _sample_zone_residence(rng: np.random.Generator, num_rows: int) -> np.ndarray:
    """Sample residence zone from INSEE population distribution.

    ~19% zone1 (Île-de-France), ~28% zone2 (grandes villes), ~53% zone3 (reste).
    """
    return rng.choice(
        ZONE_RESIDENCE_VALUES,
        size=num_rows,
        p=[0.19, 0.28, 0.53],
    )


class InseeAggregateLoader:
    """INSEE aggregate data loader implementing the D-03 common tabular interface.

    Produces microdata rows by sampling from publicly available INSEE
    marginal distributions. The CopulaGAN synthesizer learns joint
    dependencies from these independent samples via copula structure.

    Attributes:
        seed: Random seed for reproducibility.
        num_rows: Target number of rows to generate.
    """

    MAX_ROWS = 100_000

    def __init__(self, seed: int = 42, num_rows: int = 50_000):
        if num_rows > self.MAX_ROWS:
            raise ValueError(
                f"num_rows ({num_rows}) exceeds maximum ({self.MAX_ROWS}). "
                f"Reduce the target count."
            )
        self.seed = seed
        self.num_rows = num_rows

    def load(self, source_path: Optional[str] = None) -> pd.DataFrame:
        """Load or generate microdata rows with canonical COLUMNS.

        If source_path is provided and exists, attempts to parse INSEE
        tables from CSV. Otherwise falls through to synthetic generation
        from known French marginal distributions.

        Args:
            source_path: Optional path to INSEE aggregate data file.

        Returns:
            DataFrame with canonical COLUMNS matching preprocess.py.
        """
        # Attempt file-based loading if a valid source is provided
        if source_path is not None:
            if os.path.exists(source_path):
                try:
                    df = pd.read_csv(source_path)
                    logger.info(
                        "Loaded %d rows from %s", len(df), source_path
                    )
                    return df
                except Exception as exc:
                    logger.warning(
                        "Failed to parse %s: %s. Falling back to synthetic generation.",
                        source_path, exc,
                    )
            else:
                logger.info(
                    "Source path %s not found. Using synthetic generation.",
                    source_path,
                )

        # Build synthetic dataset from INSEE marginal distributions
        return self._build_synthetic()

    def _build_synthetic(self) -> pd.DataFrame:
        """Build synthetic microdata from INSEE marginal distributions."""
        rng = np.random.default_rng(self.seed)

        ages = _sample_age(rng, self.num_rows)
        situations = _sample_situation_familiale(rng, self.num_rows)

        df = pd.DataFrame({
            "profile_id": list(range(1, self.num_rows + 1)),
            "age": ages,
            "patrimoine": _sample_patrimoine(rng, self.num_rows),
            "revenu_fiscal": _sample_revenu_fiscal(rng, self.num_rows),
            "situation_familiale": situations,
            "nombre_parts": _sample_nombre_parts(rng, situations),
            "type_activite": _sample_type_activite(rng, self.num_rows, ages),
            "zone_residence": _sample_zone_residence(rng, self.num_rows),
        })

        logger.info(
            "Built synthetic dataset: %d rows × %d columns (seed=%d)",
            self.num_rows, len(COLUMNS), self.seed,
        )
        return df


def build_insee_dataframe(
    num_rows: int = 50_000, seed: int = 42
) -> pd.DataFrame:
    """Standalone entry point: build synthetic INSEE microdata DataFrame.

    Skips file loading and directly constructs the dataset from known
    French statistical distributions. Used by the test suite and as
    the primary pipeline entry point when no data file exists.

    Args:
        num_rows: Number of synthetic profiles to generate.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with canonical COLUMNS matching preprocess.py.
    """
    loader = InseeAggregateLoader(seed=seed, num_rows=num_rows)
    return loader.load()
