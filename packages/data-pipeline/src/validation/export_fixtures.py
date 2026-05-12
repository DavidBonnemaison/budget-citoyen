"""JSON test fixture export for Phase 2 bilingual validation (D-14).

Generates JSON fixtures consumable by Phase 2's `cargo test` and
`wasm-pack test`, enabling cross-language validation of the WASM
microsimulation engine against the Python/openfisca-france reference.

Output format:
    {
      "test_fixtures": [
        {
          "name": "celibataire_smic",
          "input": { ... profile fields ... },
          "expected": { "ir": ..., "cotisations_salariales": ..., ... }
        },
        ...
      ],
      "reference_year": 2025,
      "generated_at": "2026-05-12T...",
      "openfisca_version": "..."
    }
"""

import datetime as _datetime
import json as _json
import os as _os
from pathlib import Path
from typing import Any, Dict, List


def export_test_fixtures(
    profiles: List[Dict[str, Any]],
    reference_results: Dict[str, Any],
    output_dir: str,
) -> str:
    """Export JSON test fixtures for Phase 2 bilingual validation.

    Generates a consolidated JSON file containing all canonical profile
    inputs and their expected reference results, structured for direct
    consumption by Rust test harnesses.

    Args:
        profiles: List of canonical profile dictionaries.
        reference_results: Results dict from validate_all_profiles()
            containing per-profile computed values.
        output_dir: Directory where the fixture JSON will be written.

    Returns:
        Absolute path to the generated fixture file.

    Raises:
        OSError: If the output directory cannot be created.
    """
    # Ensure output directory exists
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Extract openfisca version from first result if available
    openfisca_version = "unknown"
    for r in reference_results.get("results", []):
        if "computed" in r and "openfisca_version" in r["computed"]:
            openfisca_version = r["computed"]["openfisca_version"]
            break

    # Build fixture list
    fixtures: List[Dict[str, Any]] = []
    results_by_name: Dict[str, Dict[str, Any]] = {}

    for r in reference_results.get("results", []):
        name = r.get("name", "")
        if "computed" in r:
            # Store only the computed financial values, not metadata
            computed = r["computed"]
            results_by_name[name] = {
                k: v
                for k, v in computed.items()
                if k not in ("reference_year", "computed_at", "openfisca_version")
            }
        elif "error" in r:
            results_by_name[name] = {"error": r["error"]}

    for profile in profiles:
        name = profile.get("name", "")
        expected = results_by_name.get(name, {})

        fixture = {
            "name": name,
            "description": profile.get("description", ""),
            "input": {
                "situation_familiale": profile.get("situation_familiale", ""),
                "nb_enfants": profile.get("nb_enfants", 0),
                "revenus": profile.get("revenus", {}),
                "patrimoine": profile.get("patrimoine", {}),
                "zone_residence": profile.get("zone_residence", ""),
            },
            "expected": expected,
        }
        fixtures.append(fixture)

    # Build the output document
    doc = {
        "test_fixtures": fixtures,
        "reference_year": reference_results.get("reference_year", 2025),
        "generated_at": _datetime.datetime.now(_datetime.timezone.utc).isoformat(),
        "openfisca_version": openfisca_version,
        "total_fixtures": len(fixtures),
    }

    # Write to file
    output_file = output_path / "bilingual_test_fixtures.json"
    with open(output_file, "w", encoding="utf-8") as f:
        _json.dump(doc, f, indent=2, ensure_ascii=False)

    return str(output_file.resolve())


def load_test_fixtures(fixture_path: str) -> Dict[str, Any]:
    """Load and validate a test fixture JSON file.

    Args:
        fixture_path: Path to the bilingual_test_fixtures.json file.

    Returns:
        Parsed fixture document.

    Raises:
        FileNotFoundError: If the fixture file does not exist.
        ValueError: If the file is not valid JSON or missing required keys.
    """
    path = Path(fixture_path)
    if not path.exists():
        raise FileNotFoundError(f"Fixture file not found: {fixture_path}")

    with open(path, "r", encoding="utf-8") as f:
        doc = _json.load(f)

    # Validate required keys
    for key in ("test_fixtures", "reference_year", "generated_at"):
        if key not in doc:
            raise ValueError(f"Missing required key '{key}' in fixture file")

    return doc
