"""Synthetic population pipeline for Budget Citoyen.

DATA-02 + DATA-03 — CopulaGAN training on real microdata,
OpenDP differential privacy with formal epsilon <= 1.0 proof,
SDMetrics quality + privacy evaluation, and JSON export with integrity hashes.
"""

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
]
