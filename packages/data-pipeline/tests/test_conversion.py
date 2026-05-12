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
