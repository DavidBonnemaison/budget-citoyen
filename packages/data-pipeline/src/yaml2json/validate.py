"""JSON Schema validation for OpenFisca parameter files.

Uses jsonschema Draft 2020-12 validator to ensure all tax parameter files
conform to the expected structure before they are consumed by the WASM engine.
"""

import json
from pathlib import Path
from typing import Dict, List, Union

from jsonschema import Draft202012Validator, ValidationError, SchemaError


def load_schema(schema_path: str) -> Dict:
    """Load and return a JSON Schema from a file path.

    Args:
        schema_path: Path to the JSON Schema file.

    Returns:
        Parsed schema as a dictionary.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    schema_file = Path(schema_path)
    if not schema_file.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(schema_file, "r", encoding="utf-8") as f:
        schema = json.load(f)

    # Validate that the schema itself is a valid Draft 2020-12 schema
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as e:
        raise SchemaError(
            f"Invalid JSON Schema in {schema_path}: {e.message}"
        ) from e

    return schema


def validate_rules(rules_json: Dict, schema: Dict) -> List[str]:
    """Validate a rules JSON object against a JSON Schema.

    Uses jsonschema.Draft202012Validator to collect all validation errors.

    Args:
        rules_json: The parsed JSON/dict to validate.
        schema: The JSON Schema to validate against.

    Returns:
        List of human-readable error messages. Empty list = valid.
    """
    validator = Draft202012Validator(schema)
    errors = list(validator.iter_errors(rules_json))

    error_messages = []
    for error in errors:
        path = " → ".join(str(p) for p in error.absolute_path) if error.absolute_path else "(root)"
        error_messages.append(f"[{path}] {error.message}")

    return error_messages


def validate_file(json_path: str, schema_path: str) -> bool:
    """Validate a single JSON file against a schema.

    Convenience function that loads both the data file and schema,
    then runs validation.

    Args:
        json_path: Path to the JSON file to validate.
        schema_path: Path to the JSON Schema file.

    Returns:
        True if valid.

    Raises:
        ValidationError: If validation fails, with source file name in the message.
    """
    data_file = Path(json_path)
    if not data_file.exists():
        raise FileNotFoundError(f"JSON file not found: {json_path}")

    with open(data_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    schema = load_schema(schema_path)
    errors = validate_rules(data, schema)

    if errors:
        raise ValidationError(
            f"Schema validation failed for {json_path}:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )

    return True
