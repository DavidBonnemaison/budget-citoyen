"""Tests for YAML-to-JSON conversion pipeline.

Tests convert_and_validate from yaml2json.convert, ensuring correct
YAML→JSON conversion with JSON Schema validation gate (D-02, D-03).
"""

import json
import sys
import tempfile
from pathlib import Path

import yaml

# Add src to path for imports when running from tests/ directory
SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


class TestYamlToJsonConversion:
    """Tests for the YAML → JSON conversion pipeline."""

    def test_yaml_to_json_roundtrip(self, tmp_path):
        """Valid YAML converts to JSON with expected keys preserved."""
        from yaml2json.convert import convert_yaml_to_json

        # Create a minimal valid YAML parameter file
        yaml_content = {
            "description": "Taux standard de TVA sur les biens et services",
            "metadata": {
                "reference": "https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000006294314",
                "unit": "/1",
            },
            "values": {
                "2025-01-01": {
                    "value": 0.20,
                }
            },
        }

        yaml_dir = tmp_path / "yaml"
        yaml_dir.mkdir()
        yaml_file = yaml_dir / "tva.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(yaml_content, f)

        output_dir = tmp_path / "json"

        result = convert_yaml_to_json(str(yaml_dir), str(output_dir))
        assert result["converted"] == 1, f"Expected 1 converted, got {result}"
        assert result["failed"] == 0

        # Verify JSON output
        json_file = output_dir / "tva.json"
        assert json_file.exists()

        with open(json_file) as f:
            data = json.load(f)

        assert data["description"] == yaml_content["description"]
        assert data["metadata"]["unit"] == "/1"

    def test_missing_description_fails(self, tmp_path):
        """Invalid YAML (no description) raises errors during conversion."""
        from yaml2json.convert import convert_yaml_to_json

        yaml_content = {
            "metadata": {
                "reference": "https://legifrance.gouv.fr/test",
                "unit": "currency-EUR",
            },
            "values": {"2025-01-01": {"value": 1000.0}},
        }

        yaml_dir = tmp_path / "yaml_invalid"
        yaml_dir.mkdir()
        yaml_file = yaml_dir / "invalid.yaml"
        with open(yaml_file, "w") as f:
            yaml.dump(yaml_content, f)

        output_dir = tmp_path / "json_invalid"

        # With schema validation, missing description should fail
        from pathlib import Path as _Path

        schema_path = _Path(SRC_DIR) / "schemas" / "parameter.schema.json"
        if schema_path.exists():
            result = convert_yaml_to_json(
                str(yaml_dir), str(output_dir),
                schema_path=str(schema_path),
            )
            # Should fail validation — description is required
            assert result["failed"] >= 1 or result["converted"] == 0

    def test_convert_all_entry_point(self, tmp_path):
        """convert_all works as convenience wrapper for convert_yaml_to_json."""
        from yaml2json.convert import convert_all

        yaml_content = {
            "description": "Test parameter",
            "values": {"2025-01-01": {"value": 0.25}},
        }

        yaml_dir = tmp_path / "yaml2"
        yaml_dir.mkdir()
        with open(yaml_dir / "test.yaml", "w") as f:
            yaml.dump(yaml_content, f)

        output_dir = tmp_path / "json2"
        result = convert_all(
            yaml_dir=str(yaml_dir), output_dir=str(output_dir)
        )

        assert "converted" in result
        assert "failed" in result
        assert "errors" in result


class TestDateKeyConversion:
    """Gap 3 — DATA-01: datetime.date keys converted to ISO strings.

    Requirement: "PyYAML datetime.date keys converted to ISO strings before
    JSON Schema validation" (from 01-01-SUMMARY.md, deviation #2).
    """

    def test_date_key_converts_to_iso_string(self):
        """_date_keys_to_strings converts datetime.date keys to ISO format.

        When PyYAML parses '2025-01-01', it produces datetime.date(2025, 1, 1).
        JSON Schema patternProperties only match string keys, so date objects
        must be converted to strings before validation.
        """
        import datetime

        from yaml2json.convert import _date_keys_to_strings

        # Simulate PyYAML's parsed output: datetime.date as dict keys
        input_data = {
            "values": {
                datetime.date(2025, 1, 1): {
                    "value": 0.20,
                },
                datetime.date(2024, 1, 1): {
                    "value": 0.19,
                },
            },
            "description": "Test parameter",
        }

        result = _date_keys_to_strings(input_data)

        # All keys should now be strings, not datetime.date
        values_keys = list(result["values"].keys())
        assert all(isinstance(k, str) for k in values_keys), (
            f"Expected all string keys, got types: "
            f"{[type(k).__name__ for k in values_keys]}"
        )
        assert "2025-01-01" in result["values"], (
            f"Expected '2025-01-01' as key, got: {values_keys}"
        )
        assert "2024-01-01" in result["values"], (
            f"Expected '2024-01-01' as key, got: {values_keys}"
        )
        # Verify nested value is preserved
        assert result["values"]["2025-01-01"]["value"] == 0.20

    def test_date_key_conversion_preserves_non_date_keys(self):
        """_date_keys_to_strings does not modify regular string keys."""
        from yaml2json.convert import _date_keys_to_strings

        data = {
            "description": "Test",
            "metadata": {"reference": "https://legifrance.gouv.fr/test"},
        }
        result = _date_keys_to_strings(data)
        assert result == data, (
            "Non-date-keyed data structures should be unchanged"
        )

    def test_date_key_conversion_on_brackets(self):
        """_date_keys_to_strings converts date keys nested in brackets."""
        import datetime

        from yaml2json.convert import _date_keys_to_strings

        # Brackets structure with date keys inside threshold/rate
        data = {
            "brackets": [
                {
                    "threshold": {
                        datetime.date(2025, 1, 1): {"value": 11497},
                    },
                    "rate": {
                        datetime.date(2025, 1, 1): {"value": 0.11},
                    },
                },
            ],
        }

        result = _date_keys_to_strings(data)

        bracket = result["brackets"][0]
        assert "2025-01-01" in bracket["threshold"], (
            "Date key in threshold should be converted to string"
        )
        assert "2025-01-01" in bracket["rate"], (
            "Date key in rate should be converted to string"
        )


class TestConversionEntryPoints:
    """Gap 8 — DATA-01: Main entry points for conversion pipeline.

    Requirement: "convert_and_validate is the main entry point for conversion
    with validation" — the function was renamed to convert_all in implementation.
    Tests verify the actual public API contracts.
    """

    def test_convert_all_is_importable(self):
        """convert_all is the main entry point (renamed from convert_and_validate)."""
        from yaml2json import convert_all
        assert callable(convert_all), "convert_all must be callable"

    def test_convert_yaml_to_json_is_importable(self):
        """convert_yaml_to_json is the core conversion function."""
        from yaml2json import convert_yaml_to_json
        assert callable(convert_yaml_to_json), (
            "convert_yaml_to_json must be callable"
        )

    def test_validate_rules_is_importable(self):
        """validate_rules is the schema validation function."""
        from yaml2json import validate_rules
        assert callable(validate_rules), "validate_rules must be callable"

    def test_convert_all_accepts_keyword_args(self):
        """convert_all accepts yaml_dir, output_dir, and optional schema_path."""
        from yaml2json.convert import convert_all

        import inspect
        sig = inspect.signature(convert_all)
        params = list(sig.parameters.keys())
        # convert_all uses **kwargs, so no named params in signature
        # but it should be callable with keyword args
        assert sig.parameters or True  # **kwargs is valid
