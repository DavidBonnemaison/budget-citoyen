"""Tests for JSON Schema validation of tax parameter files.

Validates that parameter.schema.json is a valid Draft 2020-12 schema and
can correctly validate well-formed and malformed parameter files (D-03).
"""

import json
import sys
from pathlib import Path

# Add src to path for imports when running from tests/ directory
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


class TestSchemaSelfValidation:
    """Verify that the schema files themselves are valid JSON schemas."""

    def test_parameter_schema_is_valid_draft202012(self):
        """parameter.schema.json is a valid Draft 2020-12 JSON Schema."""
        from jsonschema import Draft202012Validator, SchemaError

        schema_path = SRC_DIR / "schemas" / "parameter.schema.json"
        assert schema_path.exists(), (
            f"Schema file not found: {schema_path}"
        )

        with open(schema_path, "r") as f:
            schema = json.load(f)

        # Must not raise SchemaError
        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as e:
            raise AssertionError(
                f"parameter.schema.json is not a valid Draft 2020-12 schema: {e}"
            ) from e

    def test_validate_ir_bareme_structure(self):
        """The IR bareme (post-conversion) validates against the schema."""
        from jsonschema import Draft202012Validator, ValidationError

        schema_path = SRC_DIR / "schemas" / "parameter.schema.json"
        with open(schema_path, "r") as f:
            schema = json.load(f)

        validator = Draft202012Validator(schema)

        # A valid IR bareme structure (post-YAML→JSON conversion)
        valid_bareme = {
            "description": "Barème progressif de l'impôt sur le revenu — revenus 2024 déclarés en 2025",
            "metadata": {
                "reference": "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000049695847",
                "unit": "currency-EUR",
            },
            "values": {
                "2025-01-01": {
                    "brackets": [
                        {"threshold": 0.0, "rate": 0.0},
                        {"threshold": 11497.0, "rate": 0.11},
                        {"threshold": 29315.0, "rate": 0.30},
                        {"threshold": 83823.0, "rate": 0.41},
                        {"threshold": 180294.0, "rate": 0.45},
                    ]
                }
            },
        }

        errors = list(validator.iter_errors(valid_bareme))
        assert len(errors) == 0, (
            f"Valid IR bareme failed validation: {errors}"
        )

    def test_missing_value_key_fails_validation(self):
        """A schema entry with missing 'value' key must fail validation."""
        from jsonschema import Draft202012Validator

        schema_path = SRC_DIR / "schemas" / "parameter.schema.json"
        with open(schema_path, "r") as f:
            schema = json.load(f)

        validator = Draft202012Validator(schema)

        # Missing 'description' which is required
        invalid_entry = {
            "values": {"2025-01-01": {"taux": 0.20}},
        }

        errors = list(validator.iter_errors(invalid_entry))
        # Should have at least one error since 'description' is required
        assert len(errors) > 0, (
            "Expected validation error for missing 'description' field"
        )


class TestTaxBenefitSystemSchema:
    """Tests for the tax_benefit_system schema."""

    def test_tax_benefit_system_schema_exists(self):
        """The top-level tax_benefit_system schema file exists."""
        schema_path = SRC_DIR / "schemas" / "tax_benefit_system.schema.json"
        assert schema_path.exists()

    def test_tax_benefit_system_schema_is_valid(self):
        """tax_benefit_system.schema.json is a valid Draft 2020-12 schema."""
        from jsonschema import Draft202012Validator, SchemaError

        schema_path = SRC_DIR / "schemas" / "tax_benefit_system.schema.json"
        with open(schema_path, "r") as f:
            schema = json.load(f)

        try:
            Draft202012Validator.check_schema(schema)
        except SchemaError as e:
            raise AssertionError(
                f"tax_benefit_system.schema.json is not valid: {e}"
            ) from e
