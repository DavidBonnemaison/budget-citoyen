---
phase: 01-data-foundation-rules-engine
reviewed: 2026-05-12T00:00:00Z
depth: standard
files_reviewed: 54
files_reviewed_list:
  - .github/workflows/phase1-validate.yml
  - packages/data-pipeline/pyproject.toml
  - packages/data-pipeline/src/schemas/parameter.schema.json
  - packages/data-pipeline/src/schemas/synthetic_profile.schema.json
  - packages/data-pipeline/src/schemas/tax_benefit_system.schema.json
  - packages/data-pipeline/src/shock_matrix/__init__.py
  - packages/data-pipeline/src/shock_matrix/bootstrap.py
  - packages/data-pipeline/src/shock_matrix/convex_hull.py
  - packages/data-pipeline/src/shock_matrix/export_parquet.py
  - packages/data-pipeline/src/shock_matrix/grid_build.py
  - packages/data-pipeline/src/synthetic_pop/__init__.py
  - packages/data-pipeline/src/synthetic_pop/dp_inject.py
  - packages/data-pipeline/src/synthetic_pop/evaluate.py
  - packages/data-pipeline/src/synthetic_pop/export.py
  - packages/data-pipeline/src/synthetic_pop/preprocess.py
  - packages/data-pipeline/src/synthetic_pop/train.py
  - packages/data-pipeline/src/validation/__init__.py
  - packages/data-pipeline/src/validation/canonical_profiles.py
  - packages/data-pipeline/src/validation/export_fixtures.py
  - packages/data-pipeline/src/validation/impots_gouv_validator.py
  - packages/data-pipeline/src/validation/reference_sim.py
  - packages/data-pipeline/src/yaml2json/convert.py
  - packages/data-pipeline/src/yaml2json/validate.py
  - packages/data-pipeline/tests/test_conversion.py
  - packages/data-pipeline/tests/test_schema_validation.py
  - packages/data-pipeline/tests/test_shock_matrix.py
  - packages/data-pipeline/tests/test_synthetic_pop.py
  - packages/data-pipeline/tests/test_validation.py
  - packages/tax-rules/parameters/aides/aah.yaml
  - packages/tax-rules/parameters/aides/allocation_rentree_scolaire.yaml
  - packages/tax-rules/parameters/aides/allocations_familiales.yaml
  - packages/tax-rules/parameters/aides/apl.yaml
  - packages/tax-rules/parameters/aides/are.yaml
  - packages/tax-rules/parameters/aides/aspa.yaml
  - packages/tax-rules/parameters/aides/cheque_energie.yaml
  - packages/tax-rules/parameters/aides/css.yaml
  - packages/tax-rules/parameters/aides/index.yaml
  - packages/tax-rules/parameters/aides/paje.yaml
  - packages/tax-rules/parameters/aides/prime_activite.yaml
  - packages/tax-rules/parameters/aides/rsa.yaml
  - packages/tax-rules/parameters/cotisations/allegements_fillon.yaml
  - packages/tax-rules/parameters/cotisations/csg_crds.yaml
  - packages/tax-rules/parameters/cotisations/forfait_social.yaml
  - packages/tax-rules/parameters/cotisations/index.yaml
  - packages/tax-rules/parameters/cotisations/pass.yaml
  - packages/tax-rules/parameters/cotisations/patronales.yaml
  - packages/tax-rules/parameters/cotisations/salariales.yaml
  - packages/tax-rules/parameters/ir/bareme.yaml
  - packages/tax-rules/parameters/ir/cehr.yaml
  - packages/tax-rules/parameters/ir/credits.yaml
  - packages/tax-rules/parameters/ir/decote.yaml
  - packages/tax-rules/parameters/ir/deductions.yaml
  - packages/tax-rules/parameters/ir/index.yaml
  - packages/tax-rules/parameters/ir/plafonnement_qf.yaml
  - packages/tax-rules/parameters/ir/quotient_familial.yaml
  - packages/tax-rules/parameters/is/CVAE.yaml
  - packages/tax-rules/parameters/is/exonerations.yaml
  - packages/tax-rules/parameters/is/index.yaml
  - packages/tax-rules/parameters/is/report_deficits.yaml
  - packages/tax-rules/parameters/is/taux.yaml
  - packages/tax-rules/parameters/tva/exonerations.yaml
  - packages/tax-rules/parameters/tva/franchise.yaml
  - packages/tax-rules/parameters/tva/index.yaml
  - packages/tax-rules/parameters/tva/taux.yaml
findings:
  critical: 5
  warning: 6
  info: 4
  total: 15
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-05-12
**Depth:** standard
**Files Reviewed:** 54
**Status:** issues_found

## Summary

Reviewed 54 source files comprising the Phase 1 data pipeline: JSON schemas, the YAML→JSON conversion pipeline, shock matrix pre-computation, synthetic population generation (SDV + OpenDP), bilingual validation framework, canonical profiles, CI workflow, and 53 YAML tax parameter files.

Five critical issues were found — the most serious being a schema/implementation mismatch between `synthetic_profile.schema.json` and the Python code (`zone_1/2/3` vs `zone1/2/3`), plus test files that call APIs with wrong signatures (these tests would fail at runtime). Additionally, the debt/GDP shock response in `bootstrap.py` has inverted sign logic for both tax and spending effects. Six warnings cover code quality issues including silent NaN suppression, unused dead code, incorrect decile computation, and a missing `"veuf"` case in the QF calculator. Four informational items note CI duplication and fragile inline checks.

## Critical Issues

### CR-01: Schema/Implementation Zone Residence Value Mismatch

**File:** `packages/data-pipeline/src/schemas/synthetic_profile.schema.json:68` vs `packages/data-pipeline/src/synthetic_pop/preprocess.py:33` and `packages/data-pipeline/src/validation/canonical_profiles.py` (all profiles)

**Issue:** The JSON schema defines `zone_residence` enum as `["zone_1", "zone_2", "zone_3"]` (with underscores), but every Python source file uses `"zone1"`, `"zone2"`, `"zone3"` (without underscores). This means:
- All 32 canonical profiles use values that would fail schema validation
- `ZONE_RESIDENCE_VALUES` in `preprocess.py` uses the wrong format
- Any synthetic population JSON exported with these values will be rejected by downstream schema validation

**Fix:** Unify on one format. Since the canonical profiles and reference simulator already use the no-underscore form, update the schema:

```json
"zone_residence": {
  "type": "string",
  "enum": ["zone1", "zone2", "zone3"],
  "description": "Geographic zone of residence (1 = Île-de-France, 2 = major cities, 3 = rest of territory)"
}
```

### CR-02: Missing Enum Values in Preprocessing Module

**File:** `packages/data-pipeline/src/synthetic_pop/preprocess.py:31-32`
vs `packages/data-pipeline/src/schemas/synthetic_profile.schema.json:37-43,55-63`

**Issue:** The preprocessing module's valid categorical value lists are missing entries that exist in the JSON schema:

- `SITUATION_FAMILIALE_VALUES` is missing `"separe"` (present in schema line 43)
- `TYPE_ACTIVITE_VALUES` is missing `"fonctionnaire"` (present in schema line 58)

Generated synthetic data using these truncated lists will never produce `"separe"` or `"fonctionnaire"` values, contradicting the schema contract.

**Fix:**
```python
SITUATION_FAMILIALE_VALUES = ["celibataire", "marie", "pacse", "veuf", "divorce", "separe"]
TYPE_ACTIVITE_VALUES = ["salarie", "independant", "fonctionnaire", "retraite", "chomeur", "etudiant", "inactif"]
```

### CR-03: Inverted Debt/GDP Shock Response Signs

**File:** `packages/data-pipeline/src/shock_matrix/bootstrap.py:127,178`

**Issue:** The `generate_placeholder_shocks()` function has inverted multiplier signs for the `debt_to_gdp_ratio` output variable:

- **Tax effect** (line 127): multiplier = `1.5` — A tax increase (+5%) produces `+0.075` effect, meaning debt/GDP *increases* when taxes rise. This is economically wrong: tax increases reduce deficits and should decrease debt/GDP. The multiplier should be `-1.5`.

- **Spend effect** (line 178): multiplier = `-1.5` — A spending increase (+5%) produces `-0.075` effect, meaning debt/GDP *decreases* when spending rises. This is also wrong: spending increases raise deficits and should increase debt/GDP. The multiplier should be `+1.5`.

**Fix:**
```python
# Line 127 — tax effect on debt/GDP:
multiplier = -1.5  # tax increase → lower debt

# Line 178 — spend effect on debt/GDP:
multiplier = 1.5  # spend increase → higher debt
```

### CR-04: Test Calls Wrong API Signature for `export_shock_matrix`

**File:** `packages/data-pipeline/tests/test_shock_matrix.py:107-118,120-137`

**Issue:** The test `test_export_shock_matrix_type_constraints` calls `export_shock_matrix()` with parameter names that don't match the function signature. The function requires `(grid, breakpoints, convex_hull, output_path, reference_year)`, but the test provides `(grid=..., output_path=..., variable_name=...)` — missing required positional arguments `breakpoints` and `convex_hull`, and passing unknown keyword `variable_name`.

Similarly, `test_export_sidecar_metadata_has_ref_year` calls `export_sidecar_metadata()` with `data_path` and `variable_names` which don't match the actual parameters `(breakpoints, convex_hull, grid_shape, output_path, reference_year)`.

These tests will raise `TypeError` at runtime and are effectively dead.

**Fix:** Update tests to match the actual API signatures. For `test_export_shock_matrix_type_constraints`:
```python
result = export_shock_matrix(
    grid=grid,
    breakpoints={"dim_0": np.arange(100).tolist()},
    convex_hull={"is_degenerate": False, "n_dimensions": 2},
    output_path=output_path,
)
assert Path(output_path).exists()
```

For `test_export_sidecar_metadata_has_ref_year`:
```python
result = export_sidecar_metadata(
    breakpoints={"dim_0": [0, 1, 2]},
    convex_hull={"is_degenerate": False, "n_dimensions": 2},
    grid_shape=(3,),
    output_path=str(tmp_path / "test.parquet"),
)
```

### CR-05: Test Passes Wrong Type to `build_metadata`

**File:** `packages/data-pipeline/tests/test_synthetic_pop.py:70-72`

**Issue:** The test `test_build_metadata_returns_correct_type` calls `build_metadata(COLUMNS)` where `COLUMNS` is a `list[str]` (from line 19 of `preprocess.py`). However, `build_metadata(df: pd.DataFrame)` expects a DataFrame and calls `metadata.add_column(...)` and `metadata.detect_from_dataframe(df)` on it. Passing a list will raise `AttributeError` at runtime.

**Fix:**
```python
def test_build_metadata_returns_correct_type(self):
    from sdv.metadata import SingleTableMetadata
    from synthetic_pop.preprocess import build_metadata

    df = pd.DataFrame({
        "age": [25, 40],
        "patrimoine": [10000.0, 200000.0],
        "revenu_fiscal": [20000.0, 50000.0],
        "situation_familiale": ["celibataire", "marie"],
        "nombre_parts": [1.0, 2.0],
        "type_activite": ["salarie", "independant"],
        "zone_residence": ["zone2", "zone1"],
        "profile_id": [1, 2],
    })
    metadata = build_metadata(df)
    assert isinstance(metadata, SingleTableMetadata)
```

## Warnings

### WR-01: Unused Dead Variable

**File:** `packages/data-pipeline/src/shock_matrix/grid_build.py:314`

**Issue:** `points_set = set()` is created but never used. The code uses `all_points_list` and `sorted(set(all_points_list))` directly instead.

**Fix:** Remove the unused line 314.

### WR-02: `assert` Used for Runtime Enforcement

**File:** `packages/data-pipeline/src/shock_matrix/export_parquet.py:164`

**Issue:** The D-09 5 MB size limit is enforced with `assert compressed_size < MAX_COMPRESSED_SIZE`. Python `assert` statements can be disabled with the `-O` (optimize) flag, silently removing this critical check in production.

**Fix:**
```python
if compressed_size >= MAX_COMPRESSED_SIZE:
    raise ValueError(
        f"Shock matrix exceeds 5 MB limit (D-09): "
        f"{compressed_size:,} bytes ({compressed_size / 1_000_000:.2f} MB). "
        f"Reduce breakpoints (currently {grid_shape}) or use Smolyak sparse grid."
    )
```

### WR-03: Silent NaN/Inf Suppression

**File:** `packages/data-pipeline/src/shock_matrix/export_parquet.py:207,239`

**Issue:** Both `_flatten_cartesian` and `_flatten_smolyak` silently replace `NaN` and `Inf` values with `0.0`:
```python
val = 0.0 if np.isnan(val) or np.isinf(val) else val
```
This silently drops real data problems. A NaN in the shock matrix means a grid cell was never computed — replacing with 0.0 is a data corruption risk. These should at minimum log a warning.

**Fix:** Log a warning before replacing, or propagate NaN to the output so downstream consumers can detect missing data:
```python
if np.isnan(val) or np.isinf(val):
    logger.warning(f"NaN/Inf value at grid cell {indices}, output {output_names[o]}")
    val = float("nan")  # Preserve, don't silently zero
```

### WR-04: Unused Import

**File:** `packages/data-pipeline/src/shock_matrix/bootstrap.py:15`

**Issue:** `Union` is imported from `typing` but never used anywhere in the file. Only `Optional` is used (lines 226-227).

**Fix:** Change the import to `from typing import Optional` only.

### WR-05: Incorrect Decile Computation (Cumulative Groups)

**File:** `packages/data-pipeline/src/synthetic_pop/dp_inject.py:188-191`

**Issue:** The decile DP injection loop computes cumulative groups instead of per-decile ranges:
```python
for p in [10 * i for i in range(1, 11)]:
    decile_bound = int(np.percentile(revenu, p))
    decile_data = revenu[revenu <= decile_bound]  # BUG: cumulative
```
For `p=20`, this includes all values ≤ 20th percentile, which includes the 0-10th percentile range. Each subsequent group includes all previous groups, so the DP noise is applied to overlapping (not disjoint) data subsets. The second decile should be `revenu[(revenu > prev_bound) & (revenu <= decile_bound)]`.

**Fix:**
```python
prev_bound = float("-inf")
for p in [10 * i for i in range(1, 11)]:
    decile_bound = int(np.percentile(revenu, p))
    decile_data = revenu[(revenu > prev_bound) & (revenu <= decile_bound)]
    prev_bound = decile_bound
    if len(decile_data) > 0:
        result = prove_dp_guarantee(list(decile_data), epsilon_target=decile_eps)
        decile_epsilons.append(result["actual_epsilon"])
```

### WR-06: Missing `"veuf"` Case in Quotient Familial Calculator

**File:** `packages/data-pipeline/src/validation/reference_sim.py:162-184`

**Issue:** The `_compute_quotient_familial` function treats `"veuf"` (widowed) the same as `"celibataire"` (single), falling through to the `else` branch. However, a widowed person with children should receive the same parent isolé treatment as a divorced person with children (1 part + 0.5 parent isolé + 0.5 per child). Currently, a `"veuf"` with children gets only the celibataire calculation.

**Fix:** Add `"veuf"` to the parent isolé condition:
```python
elif situation in ("divorce", "veuf") and nb_enfants > 0:
    return 1.0 + 0.5 + (nb_enfants * 0.5)
```

## Info

### IN-01: CI Workflow Duplication

**File:** `.github/workflows/phase1-validate.yml` (lines 34-265)

**Issue:** Five jobs (`schema-validation`, `conversion-test`, `synth-pop-test`, `shock-matrix-test`, `validation-test`) each repeat the identical 3-step Python setup (checkout, setup-python, pip install). Consider using a reusable workflow or composite action. Not a bug — the caching layer mitigates the performance impact.

### IN-02: CI Summary Doesn't Detect Skipped/Cancelled Jobs

**File:** `.github/workflows/phase1-validate.yml:377-386`

**Issue:** The `ci-summary` job's failure check only matches `"failure"` status. If any upstream job is `"skipped"` or `"cancelled"`, it won't be flagged as a gate failure despite the job not having succeeded.

**Fix:** Check for `"success"` explicitly rather than `"failure"`:
```bash
if [[ "${{ needs.X.result }}" != "success" ]]; then
    ...
fi
```

### IN-03: No-Op Inline Python Assertion

**File:** `.github/workflows/phase1-validate.yml:176`

**Issue:** The inline Python script contains `assert expected == 2025` where `expected` is hardcoded to `2025` on the previous line. This check is tautological and will never fail. The real validation relies on the `grep` subprocess check that follows — the tautological assertion is dead code.

### IN-04: No Profile for `"separe"` and `"fonctionnaire"` in Canonical Set

**File:** `packages/data-pipeline/src/validation/canonical_profiles.py`

**Issue:** The JSON schema includes `"separe"` (for `situation_familiale`) and `"fonctionnaire"` (for `type_activite`) as valid enum values, but no canonical profile exercises these values. Adding profiles for these cases would improve test coverage. (Note: this relates to CR-02 — fix the enum values first, then add profiles.)

---

_Reviewed: 2026-05-12T00:00:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
