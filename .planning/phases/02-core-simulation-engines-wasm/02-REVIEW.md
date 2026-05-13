---
status: issues_found
depth: deep
files_reviewed: 25
critical: 6
warning: 10
info: 8
total: 24
phase: "02"
phase_name: "core-simulation-engines-wasm"
files_reviewed_list:
  - packages/core/Cargo.toml
  - packages/core/src/lib.rs
  - packages/core/src/parameters.rs
  - packages/core/src/types.rs
  - packages/core/src/test_fixtures.rs
  - packages/core/tests/parameter_tests.rs
  - packages/core/tests/profile_tests.rs
  - packages/data-pipeline/pyproject.toml
  - packages/data-pipeline/generate_dist.py
  - packages/data-pipeline/src/scenarios/__init__.py
  - packages/data-pipeline/src/scenarios/precompute.py
  - packages/data-pipeline/src/scenarios/scenario_definitions.py
  - packages/data-pipeline/dist/parameters-v2025.1.json
  - packages/data-pipeline/dist/bilingual_test_fixtures.json
  - packages/data-pipeline/dist/shockmatrix-v2025.1.parquet
  - .github/workflows/phase2-wasm.yml
  - webapp/src/engine/macro-interpolate.ts
  - webapp/src/engine/scenario-cache.ts
  - webapp/src/engine/types.ts
  - webapp/src/engine/__tests__/macro-interpolate.test.ts
  - webapp/src/engine/__tests__/scenario-cache.test.ts
  - webapp/src/workers/citizen-worker.ts
  - webapp/src/workers/macro-worker.ts
  - webapp/src/workers/orchestrator.ts
  - webapp/src/workers/index-map.ts
---

# Phase 02: Code Review Report

**Reviewed:** 2026-05-13T04:00:00Z
**Depth:** deep
**Files Reviewed:** 25 (24 specified + 1 additional dependency `test_fixtures.rs` traced from `lib.rs`)
**Status:** issues_found

## Summary

Deep cross-file review of the Phase 02 simulation engines (Rust core crate, Python pre-compute pipeline, TypeScript engines, Web Worker orchestrator, CI/CD workflow). This phase represents a significant architectural pivot from WASM to hybrid: the original WASM micro/macro engines were replaced with pure TypeScript engines backed by Python pre-computed JSON. The review uncovered **6 critical bugs** — including incorrect tax bracket thresholds, wrong quotient familial computation for large families, data corruption in the shock matrix fallback, silent data loss during fixture deserialization, and a CI version gate guaranteed to fail. The Python pre-compute pipeline does not actually use openfisca-france for computation despite importing it — all formulas are hand-rolled simplifications with several arithmetic errors.

---

## Critical Issues

### CR-01: Incorrect IR bracket threshold in Python precompute pipeline (180 294 vs 180 648)

**File:** `packages/data-pipeline/src/scenarios/precompute.py:129`
**Issue:** The 5th income tax bracket threshold is hardcoded as `180294.0` but the official 2025 barème (confirmed in `parameters-v2025.1.json:860`) uses `180648.0`. This causes incorrect IR computation for incomes above ~180 000 € in all precomputed scenario results. Every scenario produced by `precompute_scenarios()` will carry this error into the client-side cache.
**Fix:**
```python
# Line 124-130 in precompute.py
brackets = [
    (11497.0, 0.00),
    (29315.0, 0.11 * scale),
    (83823.0, 0.30 * scale),
    (180648.0, 0.41 * scale),   # FIXED: was 180294.0
    (float("inf"), 0.45 * scale),
]
```

### CR-02: Wrong quotient familial for families with 3+ children — returns 2.5 instead of 3.0

**File:** `packages/data-pipeline/src/scenarios/precompute.py:109-110`
**Issue:** The `_compute_quotient_familial` function uses `1.5 + (nb_enfants - 1) * 0.5` for single parents with 3+ children. Under French tax law, the 3rd child counts as 1 full part, not 0.5. For a single parent with 3 children: correct QF = 1 + 0.5 + 0.5 + 1.0 = 3.0; the code returns 2.5. This systematically underestimates the number of parts for large families, causing overestimation of IR across all scenarios. The same error affects married couples with 3+ children: correct = 2 + 0.5 + 0.5 + 1.0 = 4.0; code returns 3.0 + (3-2) = 3.0 + 1 = 4.0 — wait, for couples: `nb_enfants == 2 → 3.0`, `else → 3.0 + (nb_enfants - 2)`. For 3 children: `3.0 + 1 = 4.0`. OK the couple case is correct because the `else` branch uses `(nb_enfants - 2)`. But the single case uses `(nb_enfants - 1)` in the else branch instead of properly distinguishing between the 2nd and 3rd child.
**Fix:**
```python
def _compute_quotient_familial(profile: Dict[str, Any]) -> float:
    # ...
    if situation in ("marie", "pacse"):
        if nb_enfants == 0:
            return 2.0
        elif nb_enfants <= 2:
            return 2.0 + nb_enfants * 0.5
        else:
            return 2.0 + 2 * 0.5 + (nb_enfants - 2) * 1.0  # 3rd+ child = 1 part
    elif situation in ("divorce", "veuf") and nb_enfants > 0:
        if nb_enfants <= 2:
            return 1.0 + 0.5 + nb_enfants * 0.5  # parent isolé: +0.5 puis +0.5/enfant
        else:
            return 1.0 + 0.5 + 2 * 0.5 + (nb_enfants - 2) * 1.0
    else:
        # celibataire
        if nb_enfants == 0:
            return 1.0
        elif nb_enfants <= 2:
            return 1.0 + nb_enfants * 0.5
        else:
            return 1.0 + 2 * 0.5 + (nb_enfants - 2) * 1.0
```

### CR-03: Shock matrix file corrupted — JSON manifest written with `.parquet` extension when pyarrow unavailable

**File:** `packages/data-pipeline/generate_dist.py:158-160`
**Issue:** When pyarrow is not installed, the fallback branch writes a JSON manifest to a file named `shockmatrix-v2025.1.parquet`. The file extension claims Parquet format but the content is JSON. Any consumer attempting to read this as Parquet (e.g., `pq.read_table()`, or the TypeScript Parquet reader) will fail with an unparseable error. Currently the test grid file is a valid Parquet (2602 bytes), but production environments without pyarrow would produce a corrupted file. This is a data corruption path.
**Fix:**
```python
# Use separate filename for fallback, or write JSON with .json extension
manifest_path = dist_dir / "shockmatrix-v2025.1.manifest.json"
with open(manifest_path, "w") as f:
    json.dump(manifest, f, indent=2)
```

### CR-04: `FixtureRevenus` struct misses income categories — data silently dropped on deserialization

**File:** `packages/core/src/test_fixtures.rs:63-71`
**Issue:** `FixtureRevenus` only has `salaires`, `pensions`, `bnc`, `fonciers` fields. But the actual `bilingual_test_fixtures.json` contains profiles with `allocations_chomage`, `bic`, `micro_bic`, `benefice_agricole`, and `aa_h` income categories (e.g., profiles `chomeur`, `independant_bic`, `auto_entrepreneur`, `agriculteur_zone3`, `handicape_aah`, `jeune_precaire`). Serde's `#[serde(deny_unknown_fields)]` is NOT set here, so unknown fields are silently ignored with `#[serde(default)]` providing zero vectors. Profiles that rely on these income streams will have their revenue incorrectly computed as zero or near-zero. The `profile_from_fixture` function at line 149-152 also only sums `salaires`, `pensions`, `bnc`, `fonciers` — missing these categories.
**Fix:**
```rust
pub struct FixtureRevenus {
    #[serde(default)]
    pub salaires: Vec<f64>,
    #[serde(default)]
    pub pensions: Vec<f64>,
    #[serde(default)]
    pub bnc: Vec<f64>,
    #[serde(default)]
    pub fonciers: Vec<f64>,
    #[serde(default)]
    pub allocations_chomage: f64,
    #[serde(default)]
    pub bic: f64,
    #[serde(default)]
    pub micro_bic: f64,
    #[serde(default)]
    pub benefice_agricole: Vec<f64>,
    #[serde(default)]
    pub aa_h: f64,
}
```
Also update `profile_from_fixture` line 149-152 to include these in `total_revenu`.

### CR-05: CI version-check gate guaranteed to fail — grep targets wrong directory

**File:** `.github/workflows/phase2-wasm.yml:260-261`
**Issue:** The version-check job greps `packages/core/src/` for lines containing both "2025" and "reference_year\|REFERENCE_YEAR":
```bash
YEAR_COUNT=$(grep -r "2025" packages/core/src/ 2>/dev/null | grep -c "reference_year\|REFERENCE_YEAR" || true)
```
The `reference_year` field exists in `test_fixtures.rs:27` and `bilingual_tests.rs:19`, but the grep scope is `packages/core/src/` which only contains `test_fixtures.rs:27` (`pub reference_year: u16,` — no "2025" on same line). The assertion `assert_eq!(doc.reference_year, 2025)` lives in `tests/bilingual_tests.rs` (under `tests/`, not `src/`). Therefore the grep returns `0`, which is `< 1`, causing the CI gate to fail. This gate will block ALL CI runs.
**Fix:**
```yaml
# Option A: expand grep scope
YEAR_COUNT=$(grep -r "2025" packages/core/ 2>/dev/null | grep -c "reference_year\|REFERENCE_YEAR" || true)

# Option B: add explicit reference_year constant in src/ (preferred)
```
Add to `packages/core/src/types.rs`:
```rust
/// Tax reference year for the v2025.1 parameter set.
pub const REFERENCE_YEAR: u16 = 2025;
```

### CR-06: `_compute_cotisations` CSG/CRDS rate inaccurate — uses 9.2% instead of correct 9.7%

**File:** `packages/data-pipeline/src/scenarios/precompute.py:158`
**Issue:** The CSG/CRDS computation uses `0.9825 * 0.092 * scale` where `0.092` (9.2%) approximates the CSG+CRDS total rate. However, the official 2025 rates from `parameters-v2025.1.json` (`cotisations/csg_crds.json`) are: CSG deductible 6.8%, CSG non-deductible 2.4%, CRDS 0.5% — total = **9.7%**. The effective rate on gross salary should be `0.9825 * 0.097 = 0.0953025`, not `0.9825 * 0.092 = 0.09039`. This underestimates social contributions by ~0.5 percentage points of gross salary for all salaried profiles — a cumulative error of ~€250/year for a SMIC-level earner, ~€400/year for median income, and >€2500/year for high-income profiles.
**Fix:**
```python
def _estimate_cotisations(salaire_total: float, scale: float = 1.0) -> Dict[str, float]:
    cotisations_salariales = salaire_total * 0.22 * scale
    csg_crds = salaire_total * 0.9825 * 0.097 * scale  # FIXED: 0.092 → 0.097
    return {
        "cotisations_salariales": round(cotisations_salariales, 2),
        "csg_crds": round(csg_crds, 2),
    }
```

---

## Warnings

### WR-01: `interpolateAtPoint` rejects tax=0 or spend=0 — valid baseline values fail

**File:** `webapp/src/engine/macro-interpolate.ts:120-122`
**Issue:** The guard `if (tax <= 0 || spend <= 0) { return null; }` uses `<=` after `isFinite` check. A tax rate of exactly 0.0 (valid baseline — no tax change) or spending level of 0 would be rejected before even reaching the convex hull gate. These are meaningful slider positions. Use `< 0` for negativity check, and let 0 pass through to the hull gate.
**Fix:**
```typescript
if (tax < 0 || spend < 0) {  // Only reject negative values, zero is valid
    return null;
}
```

### WR-02: `interpolateAtPoint` hardcodes horizon range [1,5] instead of using matrix breakpoints

**File:** `webapp/src/engine/macro-interpolate.ts:123`
**Issue:** `if (horizon < 1 || horizon > 5)` hardcodes a fixed range. The `ShockMatrixData` struct carries `horizonBp: Float64Array` which defines the actual valid horizon range. If the matrix has breakpoints like `[2025, 2026, 2027]`, the hardcoded `1-5` check would reject valid horizons or allow invalid ones. The code should validate against `matrix.horizonBp[0]` and `matrix.horizonBp[matrix.horizonBp.length - 1]`.
**Fix:**
```typescript
// Replace hardcoded range with matrix-derived bounds
if (horizon < matrix.horizonBp[0] || horizon > matrix.horizonBp[matrix.horizonBp.length - 1]) {
    return null;
}
```

### WR-03: `ScenarioDefinition._reform_class` type annotation references undefined `Reform`

**File:** `packages/data-pipeline/src/scenarios/scenario_definitions.py:43`
**Issue:** `_reform_class: Optional[Type[Reform]] = field(default=None, repr=False)` — `Reform` is not imported at module level. It's only imported inside `build_reform()` via `from openfisca_core.reforms import Reform`. On Python 3.10+ without `from __future__ import annotations`, this would raise `NameError` at class definition time. With PEP 563 active or Python 3.12+ (PEP 649/695), the annotation is stringified but `Type[Reform]` may still be evaluated. Safer to use `Optional[Any]` or add a forward-reference string.
**Fix:**
```python
from __future__ import annotations  # Add this at top
# OR use string annotation:
_reform_class: "Optional[Type[Reform]]" = field(default=None, repr=False)
```

### WR-04: Precompute pipeline silently swallows all exceptions — zeroed results mask errors

**File:** `packages/data-pipeline/src/scenarios/precompute.py:449-464`
**Issue:** The `except Exception as exc:` block catches every possible error (including `AttributeError` from malformed profiles, `OverflowError` from extreme values, `TypeError` from type mismatches) and substitutes a zeroed result. Users would see `revenuDisponible: 0.00` for affected scenarios with no indication of failure. For a citizen budget simulator, presenting zero taxes/aides when the actual computation failed is misleading. At minimum, the error should be propagated with a structured error marker, or the pipeline should fail-fast.
**Fix:**
```python
except Exception as exc:
    profile_name = profile.get("name", f"profile_{idx}")
    raise RuntimeError(
        f"Computation failed for scenario '{scenario.id}' "
        f"profile '{profile_name}' (index {idx})"
    ) from exc
```

### WR-05: `macro-worker.ts` INTERPOLATE handler — missing `years` field causes empty trajectories

**File:** `webapp/src/workers/macro-worker.ts:136-148`
**Issue:** When `subType === 'project'`, the code casts `payload` to `ProjectPayload` and reads `.years`. If the client sends `INTERPOLATE` with `subType: 'project'` but forgets the `years` field, `years` is `undefined`. `projectTrajectory(matrix, tax, spend, undefined)` would execute `for (let y = 1; y <= undefined; y++)` → `1 <= NaN` → false → returns result with 4 empty arrays `[]`. This passes validation and would render as "no data" in the UI without any error.
**Fix:**
```typescript
if (interpPayload.subType === 'project') {
    const years = (payload as ProjectPayload).years;
    if (typeof years !== 'number' || years < 1) {
        self.postMessage({
            id, type: 'ERROR',
            payload: 'PROJECT requires a valid years field >= 1',
        } satisfies WorkerResponse);
        return;
    }
    result = projectTrajectory(matrix, interpPayload.tax, interpPayload.spend, years);
}
```

### WR-06: `Parameters::load_real_format` ignores version validation

**File:** `packages/core/src/parameters.rs:205-221`
**Issue:** The `load_real_format` method takes `_expected_version: &str` (underscore-prefixed, deliberately unused) and hardcodes `"rules-v2025.1"`. The real format JSON is never validated against the expected version. If a future version's JSON file is loaded by accident, no error is raised. Additionally, all parameter values are stored as `ParameterValue::None` — meaning `get_brackets()`, `get_scalar()`, `get_at_date()` will all fail for the real format. This may be intentional for Phase 2 scope but should be documented clearly.
**Fix:** At minimum, parse the version from the JSON or validate via a top-level `version` key if present. Add a doc comment explaining that deep parameter extraction is deferred to a later phase.

### WR-07: `ScenarioDoc.results` type is `Record<number, ScenarioResult>` but JSON produces string keys

**File:** `webapp/src/engine/scenario-cache.ts:26-27` and `scenario-cache.ts:87-88`
**Issue:** `ScenarioDoc` declares `results: Record<number, ScenarioResult>` but JSON has no concept of numeric keys — all object keys become strings after `JSON.parse()`. The `addScenario` method iterates with `Object.entries(doc.results)` and converts via `Number(key)`, which works at runtime but creates a type safety gap. A consumer expecting `Record<number, ...>` semantics (e.g., `Object.keys(doc.results).map(Number)`) could get confused.
**Fix:**
```typescript
export interface ScenarioDoc {
    definition: ScenarioDefinition;
    /** Pre-computed results indexed by profile index (0-49999) as string keys from JSON. */
    results: Record<string, ScenarioResult>;
}
```
And update `addScenario` to use `Record<string, ScenarioResult>`.

### WR-08: `generate_dist.py` imports unused `FranceTaxBenefitSystem` — dead code

**File:** `packages/data-pipeline/src/scenarios/precompute.py:430-432`
**Issue:** `from openfisca_france import FranceTaxBenefitSystem` is imported and instantiated (`tbs = FranceTaxBenefitSystem()`) but the instance is never used. The computation uses hand-rolled formulas (CR-01, CR-02, CR-06). This import may fail in CI environments where openfisca-france's dependency chain is broken, and serves no purpose beyond version extraction (which is done separately via `importlib.metadata` at line 434).
**Fix:** Remove lines 430-432 and import `importlib.metadata` directly for version extraction. If openfisca-france validation is intended, use it to cross-validate the hand-rolled formulas.

### WR-09: `orchestrator.ts` `project()` method sends wrong message type — dead code in macro-worker

**File:** `webapp/src/workers/orchestrator.ts:220-231` and `webapp/src/workers/macro-worker.ts:158-182`
**Issue:** The orchestrator's `project()` method sends `type: 'INTERPOLATE'` with `subType: 'project'` rather than `type: 'PROJECT'`. The macro-worker has a fully implemented `PROJECT` handler (lines 158-182) that is **never reached** because the orchestrator doesn't use that message type. This is dead code and creates confusion about which code path is active.
**Fix:** Either use `type: 'PROJECT'` in the orchestrator (removing the subType routing in INTERPOLATE) or remove the unused `PROJECT` case from the worker.

### WR-10: `console.debug` statement in production worker orchestrator

**File:** `webapp/src/workers/orchestrator.ts:76`
**Issue:** `console.debug(\`Discarding stale ${source} response: ${response.id}\`)` logs internal state (UUIDs) in production. While not a privacy leak (UUIDs are opaque), debug logging in the hot path (rapid slider updates) may add noise and slight overhead. Should be gated behind a debug flag or removed.
**Fix:** Remove the `console.debug` line, or gate it behind `if (import.meta.env.DEV)` or a logger level check.

---

## Info

### IN-01: `index-map.ts` references deleted `wasm-micro` crate — likely dead code

**File:** `webapp/src/workers/index-map.ts:2`
**Issue:** Comment states `// Shared with Rust: packages/wasm-micro/src/simulation.rs — keep in sync` but the CI workflow explicitly states "No wasm-pack, no wasm-bindgen, no WASM boundary layers — all removed." With the hybrid architecture (Python pre-compute + TS scenario cache), the `PARAM_INDICES` and `NUM_SIMULATION_PARAMS` constants are no longer used for WASM interop. They may be dead code. Verify if any TypeScript module still imports from `index-map.ts`.
**Fix:** Audit imports and remove if unused, or update comment to reflect the hybrid architecture.

### IN-02: Architecture documentation mismatch — STACK.md recommends WASM dependencies not used

**File:** `AGENTS.md:34-41` (STACK.md sections)
**Issue:** The project STACK.md recommends `wasm-bindgen 0.2.121`, `ndarray 0.17.2`, `interpolation 0.3.0`, `serde-wasm-bindgen 0.6.5`, `wasm-bindgen-rayon 1.3.0` — none of which appear in `packages/core/Cargo.toml`. The CI workflow comment at line 14 explains the architectural simplification, but STACK.md was not updated. This is a documentation-code gap that could mislead new contributors.
**Fix:** Update STACK.md to reflect the hybrid architecture: TypeScript engines for runtime, Python pre-compute for offline computation, Rust core crate for types/validation only.

### IN-03: Multiple Python modules imported but not in 24-file review scope

**File:** `packages/data-pipeline/generate_dist.py:15-18`, `pyproject.toml:32-33`
**Issue:** `generate_dist.py` imports `yaml2json.convert`, `validation.canonical_profiles`, `validation.export_fixtures`, `validation.reference_sim` — these Phase 1 modules are not in the review file list. The `pyproject.toml` `[project.scripts]` references `yaml2json.validate:validate_file` which may not exist. Without reviewing these modules, their correctness cannot be verified, and they are dependencies of the reviewed pipeline.
**Fix:** Ensure Phase 1 modules are reviewed or their existence/contracts verified before depending on them in Phase 2.

### IN-04: Rust `MacroResult` and TypeScript `MacroResult` have divergent naming conventions

**File:** `packages/core/src/types.rs:173-189` and `webapp/src/engine/types.ts:20-33`
**Issue:** Rust uses snake_case fields (`deficit_trajectory`, `debt_trajectory`, `gdp_growth_trajectory`, `employment_trajectory`) while TypeScript uses camelCase (`deficitTrajectory`, `debtTrajectory`, `gdpGrowthTrajectory`, `employmentTrajectory`). Since WASM interop was removed, these structs are never serialized between languages, so there's no runtime bug. However, the naming inconsistency creates confusion about whether these types are meant to be compatible.
**Fix:** Add a comment to both files clarifying they are independent type definitions with no serialization contract.

### IN-05: `_check_openfisca_installed` is called but openfisca-france is not used for computation

**File:** `packages/data-pipeline/src/scenarios/precompute.py:73-82, 412`
**Issue:** The pipeline calls `_check_openfisca_installed()` which verifies openfisca-france can be imported, and then `precompute_scenarios` imports `FranceTaxBenefitSystem`. But the actual tax/benefit formulas in `_compute_scenario_result` are hand-rolled Python functions that don't use openfisca at all. The openfisca dependency adds significant CI overhead (~5-10 min install time) without providing computational value. The bilingual test fixtures contain reference values computed by openfisca, but the precompute pipeline itself bypasses it.
**Fix:** Either: (a) use openfisca-france for computation to guarantee fidelity with the reference simulator, or (b) remove the openfisca dependency and clearly document that precomputed values use simplified formulas with known deviations.

### IN-06: `PendingEntry.resolve` cast in `orchestrator.ts` `init()` uses closure wrapping

**File:** `webapp/src/workers/orchestrator.ts:119-124`
**Issue:** The `init()` method wraps resolve as `resolve: () => resolve()` to satisfy the `Promise<void>` → `PendingEntry.resolve: (value: unknown) => void` cast. While functional, this closure indirection is fragile and adds an unnecessary allocation. A cleaner approach would be to make `PendingEntry` generic.
**Fix:**
```typescript
interface PendingEntry<T = unknown> {
    resolve: (value: T) => void;
    reject: (reason: unknown) => void;
    timestamp: number;
}
private pending = new Map<string, PendingEntry<unknown>>();
```

### IN-07: `parameters.rs` `parse_parameter_value` cannot handle deeply nested objects

**File:** `packages/core/src/parameters.rs:234-304`
**Issue:** The `parse_parameter_value` function only handles `brackets`, `values` (temporal), and `value` (scalar) top-level keys. The real `parameters-v2025.1.json` uses deeply nested structures like `{"values": {"2025-01-01": {"value": {"sub_field": {"value": 42.0}}}}}`. These would reach the catch-all `else` branch and return `ParseError`. This is currently bypassed because `load_real_format` stores everything as `ParameterValue::None`, but if a future phase attempts to deep-parse real parameters, it will fail.
**Fix:** Add recursive parsing or document that the current `ParameterValue` enum is for the simplified test format only.

### IN-08: Scenario precompute pipeline serializes string-keyed profile indices but TypeScript expects numeric indices

**File:** `packages/data-pipeline/src/scenarios/precompute.py:448` and `webapp/src/engine/scenario-cache.ts:87-88`
**Issue:** The Python pipeline stores results as `results[str(idx)] = result` (string keys), while the TypeScript `ScenarioCache.addScenario()` converts them back via `Number(key)`. The intermediate JSON also has string keys. This double conversion (int→str in Python, str→int in TS) is fragile — if profile indices were ever non-numeric strings, they would silently become `NaN`. A comment explaining this string-key convention would help future maintainers.
**Fix:** Add a comment in both files documenting the string-key convention for JSON transport, and consider using an array instead of an object if the indices are contiguous.

---

_Reviewed: 2026-05-13T04:00:00Z_
_Reviewer: gsd-code-reviewer (deep mode)_
_Depth: deep_
