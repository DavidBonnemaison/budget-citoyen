"""YAML → JSON conversion with JSON Schema validation gate.

Converts OpenFisca-compatible YAML parameter files to JSON, performing
JSON Schema Draft 2020-12 validation BEFORE writing any output (fail-early
strategy per RESEARCH.md Pitfall anti-pattern).
"""

import datetime as _datetime
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from jsonschema import Draft202012Validator, ValidationError

from .validate import load_schema, validate_rules


def _date_keys_to_strings(data: Any) -> Any:
    """Recursively convert datetime.date keys to ISO format strings.

    PyYAML parses date keys (e.g., 2025-01-01) as datetime.date objects.
    JSON Schema's patternProperties only matches string keys, so we must
    convert date keys to strings BEFORE validation. This transformation
    is applied in-place on a copy of the data structure.

    Args:
        data: A parsed YAML data structure (dict, list, or scalar).

    Returns:
        The data structure with all datetime.date keys converted to strings.
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if isinstance(key, _datetime.date):
                key = key.isoformat()
            result[key] = _date_keys_to_strings(value)
        return result
    elif isinstance(data, list):
        return [_date_keys_to_strings(item) for item in data]
    return data


def _yaml_safe_load(yaml_path: Path) -> Dict:
    """Load a YAML file safely, with clear error reporting.

    Args:
        yaml_path: Path to the YAML file.

    Returns:
        Parsed YAML content as a dictionary.

    Raises:
        yaml.YAMLError: If the YAML is malformed.
    """
    with open(yaml_path, "r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(
                f"YAML parse error in {yaml_path}: {e}"
            ) from e

    if data is None:
        raise ValueError(f"Empty YAML file: {yaml_path}")

    return data


def _serialize_dates(obj):
    """Custom JSON serializer that handles datetime.date objects.

    PyYAML parses date keys (e.g., 2025-01-01) as datetime.date objects.
    This converter preserves them as ISO format strings for JSON compatibility.
    """
    import datetime
    if isinstance(obj, datetime.date):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def convert_yaml_to_json(
    yaml_dir: str,
    output_dir: str,
    schema_path: Optional[str] = None,
) -> Dict[str, Union[int, List[str]]]:
    """Convert all YAML parameter files to JSON, with optional schema validation.

    Scans yaml_dir recursively for *.yaml files (excluding index.yaml),
    converts each to JSON, and writes to output_dir preserving the relative
    directory structure.

    When schema_path is provided, each YAML file is validated against the
    JSON Schema BEFORE the JSON file is written (fail-early strategy).

    Args:
        yaml_dir: Root directory containing YAML parameter files.
        output_dir: Directory where JSON output will be written.
        schema_path: Optional path to a JSON Schema file for validation.

    Returns:
        Dictionary with:
            - "converted": Number of files successfully converted
            - "failed": Number of files that failed
            - "errors": List of error messages ("filename: message")
    """
    yaml_root = Path(yaml_dir)
    output_root = Path(output_dir)

    if not yaml_root.exists():
        raise FileNotFoundError(f"YAML directory not found: {yaml_dir}")

    schema = None
    if schema_path:
        schema = load_schema(schema_path)

    converted = 0
    failed = 0
    errors_list: List[str] = []

    for yaml_file in sorted(yaml_root.rglob("*.yaml")):
        # Skip index files (they contain metadata, not parameters)
        if yaml_file.name == "index.yaml":
            continue

        relative_path = yaml_file.relative_to(yaml_root)

        try:
            # Parse YAML
            raw_data = _yaml_safe_load(yaml_file)

            # Convert datetime.date keys to strings for JSON Schema compatibility.
            # PyYAML parses "2025-01-01" as datetime.date, but JSON Schema
            # patternProperties only matches string property names.
            data = _date_keys_to_strings(raw_data)

            # Validate against JSON Schema if provided
            if schema:
                validation_errors = validate_rules(data, schema)
                if validation_errors:
                    failed += 1
                    for err_msg in validation_errors:
                        errors_list.append(f"{relative_path}: {err_msg}")
                    continue

            # Write validated JSON (data already has date keys converted to strings)
            json_path = output_root / relative_path.with_suffix(".json")
            json_path.parent.mkdir(parents=True, exist_ok=True)

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(
                    data,
                    f,
                    indent=2,
                    ensure_ascii=False,
                    default=_serialize_dates,
                )

            converted += 1

        except (yaml.YAMLError, ValueError, ValidationError) as e:
            failed += 1
            errors_list.append(f"{relative_path}: {str(e)}")
        except Exception as e:
            failed += 1
            errors_list.append(f"{relative_path}: Unexpected error: {str(e)}")

    return {
        "converted": converted,
        "failed": failed,
        "errors": errors_list,
    }


def convert_all(**kwargs) -> Dict:
    """Main entry point with keyword arguments.

    Supports the same parameters as convert_yaml_to_json().

    Args:
        **kwargs: Keyword arguments passed to convert_yaml_to_json().

    Returns:
        Same dictionary as convert_yaml_to_json().
    """
    return convert_yaml_to_json(**kwargs)
