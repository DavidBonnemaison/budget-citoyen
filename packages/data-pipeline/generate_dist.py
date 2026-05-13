"""Orchestrator script: generate all Phase 1 dist/ artifacts.

Run with: python generate_dist.py
Prerequisites: venv activated with jsonschema, openfisca-france installed.
"""

import json
import os
import sys
from pathlib import Path

# Ensure we can import the src/ modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Phase 1 modules (yaml2json, validation) — these are reviewed and maintained
# separately. Their contracts (function signatures, return types) are verified
# by Phase 2 integration before this pipeline depends on them.
from yaml2json.convert import convert_yaml_to_json
from validation.canonical_profiles import CANONICAL_PROFILES
from validation.export_fixtures import export_test_fixtures
from validation.reference_sim import validate_all_profiles


def main():
    # Script is in packages/data-pipeline/ — go up 2 levels to repo root
    repo_root = Path(__file__).parent.parent.parent
    dist_dir = repo_root / "packages" / "data-pipeline" / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("Phase 1 Artifact Generation")
    print("=" * 60)

    # ── Step 1: YAML → JSON conversion ──────────────────────────
    print("\n[1/5] Converting YAML parameters to JSON...")
    yaml_dir = str(repo_root / "packages" / "tax-rules" / "parameters")
    output_parameters_dir = str(dist_dir / "parameters-v2025.1")

    result = convert_yaml_to_json(
        yaml_dir=yaml_dir,
        output_dir=output_parameters_dir,
        schema_path=None,  # No schema yet — schema validation added in Plan 02-02
    )
    print(f"  ✓ Converted: {result['converted']} files")
    if result["failed"]:
        print(f"  ✗ Failed: {result['failed']} files")
        for err in result["errors"]:
            print(f"    - {err}")
    else:
        print("  All files converted successfully")

    # ── Step 2: Run reference simulation on canonical profiles ───
    print("\n[2/5] Running openfisca-france reference simulation...")
    ref_results = validate_all_profiles(
        profiles=CANONICAL_PROFILES,
        reference_year=2025,
    )
    print(f"  ✓ Profiles processed: {ref_results['passed']} passed, "
          f"{ref_results['failed']} failed")
    print(f"  Reference year: {ref_results['reference_year']}")
    print(f"  Precision threshold: {ref_results['precision']}")

    # ── Step 3: Export bilingual test fixtures ──────────────────
    print("\n[3/5] Exporting bilingual test fixtures JSON...")
    fixture_path = export_test_fixtures(
        profiles=CANONICAL_PROFILES,
        reference_results=ref_results,
        output_dir=str(dist_dir),
    )
    print(f"  ✓ Written: {fixture_path}")

    # Verify fixture keys
    with open(fixture_path) as f:
        doc = json.load(f)
    required_keys = ["test_fixtures", "reference_year", "generated_at", "openfisca_version"]
    missing = [k for k in required_keys if k not in doc]
    if missing:
        print(f"  ✗ Missing required keys: {missing}")
    else:
        print(f"  ✓ Required keys present: {required_keys}")
        print(f"  Total fixtures: {doc.get('total_fixtures', len(doc['test_fixtures']))}")

    # ── Step 4: Write parameters-v2025.1.json aggregate ──────────
    # Combine all individual parameter JSONs into one aggregate file
    print("\n[4/5] Aggregating parameters into parameters-v2025.1.json...")
    params_dir = Path(output_parameters_dir)
    aggregate = {}
    if params_dir.exists():
        for json_file in sorted(params_dir.rglob("*.json")):
            rel_path = str(json_file.relative_to(params_dir))
            with open(json_file) as f:
                aggregate[rel_path] = json.load(f)

    aggregate_path = dist_dir / "parameters-v2025.1.json"
    with open(aggregate_path, "w", encoding="utf-8") as f:
        json.dump(aggregate, f, indent=2, ensure_ascii=False)
    print(f"  ✓ Written: {aggregate_path}")
    print(f"  Aggregated {len(aggregate)} parameter files")

    # ── Step 5: Shock matrix stub ───────────────────────────────
    print("\n[5/5] Creating shock matrix stub (CASD data unavailable)...")
    import numpy as np

    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        _has_pyarrow = True
    except ImportError:
        _has_pyarrow = False

    if _has_pyarrow:
        # Create a minimal valid Parquet file as a stub
        # 3D Cartesian grid: tax_rate x spending x horizon_year -> 4 outputs
        n_tax = 5
        n_spend = 5
        n_horizon = 3
        n_outputs = 4

        records = []
        for tx in range(n_tax):
            for sp in range(n_spend):
                for yr in range(n_horizon):
                    records.append({
                        "tax_rate": float(tx) / (n_tax - 1),  # 0.0 to 1.0
                        "spending_level": float(sp) / (n_spend - 1),
                        "horizon_year": 2025 + yr,
                        "gdp_growth": 0.0,
                        "employment_change": 0.0,
                        "deficit_change": 0.0,
                        "debt_to_gdp_ratio": 100.0,
                    })

        table = pa.Table.from_pylist(records)
        parquet_path = str(dist_dir / "shockmatrix-v2025.1.parquet")
        pq.write_table(
            table,
            parquet_path,
            compression="zstd",
            compression_level=9,
            row_group_size=100,
        )
        file_size = Path(parquet_path).stat().st_size
        print(f"  ✓ Stub written: {parquet_path} ({file_size:,} bytes)")
        print(f"  ⚠ CASD data not available — grid contains zero values (placeholder)")
        print(f"  Dimensions: tax_rate(5) × spending(5) × horizon(3) → 4 outputs")
    else:
        # Fallback: create a JSON manifest
        manifest = {
            "version": "shockmatrix-v2025.1",
            "status": "stub",
            "reason": "CASD data unavailable — placeholder generated for development",
            "format": "json (manifest — pyarrow unavailable)",
            "dimensions": {
                "tax_rate": {"count": 5, "range": [0.0, 1.0]},
                "spending_level": {"count": 5, "range": [0.0, 1.0]},
                "horizon_year": {"count": 3, "range": [2025, 2027]},
            },
            "outputs": ["gdp_growth", "employment_change", "deficit_change", "debt_to_gdp_ratio"],
            "note": "Regenerate with real data when CASD access is granted (multi-month process). Install pyarrow for Parquet output.",
        }
        manifest_path = dist_dir / "shockmatrix-v2025.1.manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"  ✓ Manifest written: {manifest_path}")
        print(f"  ⚠ pyarrow not installed — JSON manifest written instead of Parquet")

    # Write a stub README
    readme_path = dist_dir / "README.md"
    with open(readme_path, "w") as f:
        f.write("""# Phase 1 Dist/ Artifacts

Generated by `packages/data-pipeline/generate_dist.py`.

## Files

| File | Description | Status |
|------|-------------|--------|
| `bilingual_test_fixtures.json` | 16 canonical profiles with openfisca-france reference results | ✅ Generated |
| `parameters-v2025.1.json` | Aggregated JSON tax parameters from 31 YAML files | ✅ Generated |
| `parameters-v2025.1/` | Individual per-file JSON outputs | ✅ Generated |
| `shockmatrix-v2025.1.parquet` | Shock matrix grid (Mésange model) | ⚠ Stub — CASD data unavailable |
| `population-v2025.1.json` | Synthetic population profiles | ⏳ Pending — CASD access required |

## Regeneration

```bash
cd packages/data-pipeline
source .venv/bin/activate
python generate_dist.py
```

## Shock Matrix Status

The shock matrix file is a **placeholder stub** containing a minimal 5×5×3 grid
with zero values. Real shock matrix data requires CASD (Centre d'Accès Sécurisé
aux Données) access — a multi-month INSEE approval process.

When CASD data becomes available, regenerate with:
```bash
python -m shock_matrix.export_parquet
```
""")
    print(f"  ✓ README written: {readme_path}")

    print("\n" + "=" * 60)
    print("Artifact generation complete!")
    print(f"Output directory: {dist_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
