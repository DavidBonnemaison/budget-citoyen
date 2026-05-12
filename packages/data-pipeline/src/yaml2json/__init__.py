"""YAML → JSON conversion and validation pipeline for Budget Citoyen tax rules.

This module converts OpenFisca-compatible YAML parameter files to validated JSON,
following the build-time-only conversion strategy (D-02). No YAML parsing occurs
in the WASM runtime — the engine consumes only validated JSON via serde_json.
"""

from .convert import convert_yaml_to_json, convert_all
from .validate import load_schema, validate_rules, validate_file

__all__ = [
    "convert_yaml_to_json",
    "convert_all",
    "load_schema",
    "validate_rules",
    "validate_file",
]
