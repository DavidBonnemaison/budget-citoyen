---
iteration: 2
status: issues_found
depth: deep
files_reviewed: 24
critical: 2
warning: 2
info: 3
total: 7
phase: "02"
phase_name: "core-simulation-engines-wasm"
files_reviewed_list:
  - packages/core/Cargo.toml
  - packages/core/src/lib.rs
  - packages/core/src/parameters.rs
  - packages/core/src/test_fixtures.rs
  - packages/core/src/types.rs
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

# Phase 02: Code Review Report — Iteration 2

**Reviewed:** 2026-05-13T16:57:00Z
**Depth:** deep
**Files Reviewed:** 24
**Status:** issues_found

## Summary

Iteration 2 deep re-review of all 24 Phase 02 source files. All 6 original critical fixes (CR-01 through CR-06) were verified as correctly applied, and 8 of 10 warnings plus 7 of 8 info items were properly addressed. However, 2 new critical issues were discovered — one cross-language regression from CR-04 (Rust fixture fix not propagated to Python precompute) and one compile-breaking import error in the test suite. Both would block CI. Additionally, 2 warnings remain from incomplete fixes in the original review, and 3 info items document latent quality concerns.

### Fix Verification Summary

| Original ID | Description | Status |
|-------------|-------------|--------|
| CR-01 | IR bracket threshold 180648 | ✅ Fixed |
| CR-02 | QF for 3+ children | ✅ Fixed |
| CR-03 | .parquet extension fallback | ✅ Fixed |
| CR-04 | FixtureRevenus missing categories (Rust) | ✅ Fixed (Rust only — see CR-07) |
| CR-05 | CI grep gate | ✅ Fixed (REFERENCE_YEAR added) |
| CR-06 | CSG/CRDS rate 9.7% | ✅ Fixed |
| WR-01 | tax/spend ≤ 0 rejection | ✅ Fixed |
| WR-02 | Hardcoded horizon range | ✅ Fixed |
| WR-03 | Reform type annotation | ✅ Fixed |
| WR-04 | Silent exception swallowing | ✅ Fixed |
| WR-05 | Missing years field | ✅ Fixed (separate PROJECT type) |
| WR-06 | Version validation deferred | ✅ Documented |
| WR-07 | Record<number> → Record<string> | ✅ Fixed |
| WR-08 | Unused openfisca import | ✅ Fixed |
| WR-09 | Orchestrator PROJECT routing | ✅ Fixed |
| WR-10 | console.debug gating | ✅ Fixed |
| IN-02 | STACK.md docs | ✅ Updated |
| IN-04 | snake_case vs camelCase | ✅ Documented |
| IN-05 | openfisca not used for compute | ✅ Documented |
| IN-06 | PendingEntry.resolve cast | ✅ Fixed (generic) |
| IN-07 | Nested parameter parsing | ✅ Documented |
| IN-08 | String-keyed indices | ✅ Documented |

---

## Critical Issues

### CR-07: Python precompute ignores `bic`/`micro_bic`/`benefice_agricole`/`aa_h` income categories — silent data loss

**Files:** `packages/data-pipeline/src/scenarios/precompute.py:298-305` and `packages/core/src/test_fixtures.rs:159-167`
**Issue:** CR-04 fixed the Rust `FixtureRevenus` struct and `profile_from_fixture` to include all 9 income categories (salaires, pensions, bnc, fonciers, benefice_agricole, allocations_chomage, bic, micro_bic, aa_h). However, the Python `_compute_scenario_result` function was **never updated** — it only extracts `salaires`, `pensions`, `bnc`, `fonciers`, and `allocations_chomage`:

```python
# precompute.py lines 298-305
salaire_total = sum(input_data.get("revenus", {}).get("salaires", [0.0]))
pension_total = sum(input_data.get("revenus", {}).get("pensions", [0.0]))
bnc_total = sum(input_data.get("revenus", {}).get("bnc", [0.0]))
fonciers_total = sum(input_data.get("revenus", {}).get("fonciers", [0.0]))
chomage_total = input_data.get("revenus", {}).get("allocations_chomage", 0.0)
revenu_brut_global = (
    salaire_total + pension_total + bnc_total + fonciers_total + chomage_total
)
```

The fixture profiles `independant_bic` (bic: 45 000€), `agriculteur_zone3` (benefice_agricole: 28 000€), `auto_entrepreneur` (micro_bic: 25 000€), `handicape_aah` (aa_h: 12 192€), and `independant_famille_3enfants` (bnc: 45 000€) all have their **primary income stream ignored** — `revenu_brut_global` computes as 0.0 or near-zero for these profiles. All downstream tax, benefit, and disposable income calculations are therefore wrong for 5 of 32 fixture profiles.

The expected `revenu_disponible` from openfisca is: `independant_bic` → 45 000€, `agriculteur_zone3` → 9 309€, `auto_entrepreneur` → 25 000€. With `revenu_brut_global = 0`, the precompute would compute RSA/aides for zero-income profiles producing wildly different results.

**Fix:**
```python
# In _compute_scenario_result, add extraction for missing income categories:
bic_total = input_data.get("revenus", {}).get("bic", 0.0)
micro_bic_total = input_data.get("revenus", {}).get("micro_bic", 0.0)
benefice_agricole_total = sum(
    input_data.get("revenus", {}).get("benefice_agricole", [0.0])
)
aa_h_total = input_data.get("revenus", {}).get("aa_h", 0.0)

revenu_brut_global = (
    salaire_total + pension_total + bnc_total + fonciers_total
    + chomage_total + bic_total + micro_bic_total
    + benefice_agricole_total + aa_h_total
)
```
Additionally, `revenu_net_cat` (line 349) must include these categories with correct abattements:
```python
revenu_net_cat = (
    salaire_total * 0.9 + pension_total * 0.9
    + bnc_total * 0.9  # 10% abattement on BNC
    + bic_total * 0.5  # 50% abattement on BIC (micro-BIC regime)
    + micro_bic_total * 0.5  # 50% abattement on micro-BIC
    + benefice_agricole_total * 1.0  # agricultural income enters IR directly
)
```

### CR-08: `scenario-cache.test.ts` imports `ScenarioDoc` from wrong module — compile error

**File:** `webapp/src/engine/__tests__/scenario-cache.test.ts:8`
**Issue:** The test file imports `ScenarioDoc` from `'../types'`:
```typescript
import type { ScenarioDoc, ScenarioDefinition, ScenarioResult } from '../types';
```
But `ScenarioDoc` is defined and exported **only** in `'../scenario-cache'` (line 22: `export interface ScenarioDoc`). `types.ts` does not export `ScenarioDoc`. This causes a TypeScript compilation error (`Module '"../types"' has no exported member 'ScenarioDoc'`), which means `vitest` will fail to compile the test file — blocking the CI pipeline's `typescript-tests` job.

**Verification:** `grep "export.*ScenarioDoc"` across all TypeScript engine files confirms the only definition is in `scenario-cache.ts`.

**Fix:**
```typescript
// Change the import to:
import { ScenarioCache, type ScenarioDoc } from '../scenario-cache';
import type { ScenarioDefinition, ScenarioResult } from '../types';
```

---

## Warnings

### WR-11: `profile_from_fixture` quotient familial caps children at 2 parts — wrong for 3+ children

**File:** `packages/core/src/test_fixtures.rs:185`
**Issue:** The Rust QF formula uses `0.5 * (input.nb_enfants as f64).min(2.0)` which caps child parts at 2 children (max 1.0 part from children). Under French tax law, the 3rd child and beyond each count as **1.0 full part** (not 0.5). The fixture contains 3 profiles with 3+ children:
- `couple_mono_actif` (marié, 3 enfants): Rust QF = 3.0, correct QF = 4.0
- `famille_nombreuse` (marié, 4 enfants): Rust QF = 3.0, correct QF = 5.0
- `independant_famille_3enfants` (marié, 3 enfants): Rust QF = 3.0, correct QF = 4.0

The current bilingual tests (`bilingual_tests.rs`) only check that profiles load and validate — they don't compare QF or compute IR. So tests pass, but `nombre_parts` in the converted `Profile` structs is wrong for 5/32 profiles. This will cause incorrect results if any future test or engine uses these Profile values.

This is a regression from CR-02 — the Python QF was fixed (precompute.py:104-119) but the Rust equivalent was left with the old formula.

**Fix:**
```rust
// Replace test_fixtures.rs:180-186 with:
let adult_parts: f64 = match input.situation_familiale.as_str() {
    "marie" | "mariee" | "pacse" | "pacsee" => 2.0,
    _ => 1.0,
};

let nb_enfants = input.nb_enfants as f64;
let enfant_parts = if nb_enfants <= 2.0 {
    nb_enfants * 0.5
} else {
    2.0 * 0.5 + (nb_enfants - 2.0) * 1.0
};

let nombre_parts = adult_parts + enfant_parts;
```

### WR-12: `_compute_scenario_result` applies wrong abattements for independent/agricultural income

**File:** `packages/data-pipeline/src/scenarios/precompute.py:349`
**Issue:** Even after fixing CR-07 (extracting all income categories), the IR taxable income calculation `revenu_net_cat = salaire_total * 0.9 + pension_total * 0.9` applies the 10% professional abattement uniformly, which is incorrect for non-salary income:
- **BIC** (commercial): 50% abattement under micro-BIC regime
- **Micro-BIC** (auto-entrepreneur): 50% abattement  
- **Bénéfice agricole**: no abattement — enters IR directly
- **BNC** (non-commercial): 10% abattement (correctly included in the current formula)

The hand-rolled formulas produce IR values that diverge from the openfisca reference for these income types. For `independant_bic` (bic: 45 000€), correct taxable income = 45 000 × 0.5 = 22 500€, but the current code (after CR-07 fix) would use 45 000 × 0.9 = 40 500€ if the 10% rule were applied, or 45 000 × 1.0 = 45 000€ if no abattement — either way wrong.

**Fix:** See the expanded `revenu_net_cat` calculation in CR-07 fix above. Alternatively, document that the precompute uses simplified formulas and cross-validate against openfisca reference in bilingual tests before deploying to production.

---

## Info

### IN-09: `index-map.ts` remains dead code — no imports found in entire codebase

**File:** `webapp/src/workers/index-map.ts`
**Issue:** A grep across `webapp/` for `import.*index-map` returns zero results. The comment was updated to note the hybrid architecture (no WASM sync), but the file itself is never imported. The `PARAM_INDICES` constants and `NUM_SIMULATION_PARAMS` are unused. Dead code adds maintenance burden and confusion about whether deletion would break anything.
**Fix:** Remove the file and any references to it. If the constants serve as documentation, move them to a `docs/simulation-params.md` or similar documentation file outside the source tree.

### IN-10: `precompute.py` docstring claims openfisca-france is used for computation

**File:** `packages/data-pipeline/src/scenarios/precompute.py:1`
**Issue:** The module docstring line 1 reads: *"Scenario pre-compute pipeline using openfisca-france."* However, the code comment at lines 76-79 explicitly states openfisca-france is NOT used for computation — all formulas are hand-rolled. The docstring is misleading and contradicts the internal documentation. The `_check_openfisca_installed()` function also tells users "This package is required for the scenario pre-compute pipeline" (line 87) when it's actually only needed for version metadata extraction.
**Fix:** Update the module docstring to: *"Scenario pre-compute pipeline using simplified tax/benefit formulas (cross-validated against openfisca-france reference)."* And update the error message in `_check_openfisca_installed` to clarify it's only needed for metadata, not computation.

### IN-11: Test `"returns null for tax or spend ≤ 0"` is misleading — rejection comes from hull, not guard

**File:** `webapp/src/engine/__tests__/macro-interpolate.test.ts:296-301`
**Issue:** The test labelled *"returns null for tax or spend ≤ 0 (even if inside hull)"* tests `tax=0` and `spend=0` against a test matrix whose hull minimums are `taxBp[0]=0.5` and `spendBp[0]=0.7`. The `0` values are rejected by the **convex hull gate**, not by the `< 0` input guard (which was fixed in WR-01 from `<= 0` to `< 0`). The test passes for the wrong reason. If someone redefines the test matrix with hull bounds that include 0 (e.g., `taxBp = [0.0, 1.0]`), this test would **fail** because the guard no longer rejects 0. The test description is actively misleading about which code path is being exercised.
**Fix:** Either:
1. Change the test name to *"returns null for tax or spend at 0 due to hull rejection"*
2. Add a separate test that verifies the `< 0` guard specifically: `expect(interpolateAtPoint(matrix, -0.001, 1.0, 1.0)).toBeNull()` with a matrix that would otherwise accept small values
3. Remove this test and rely on the explicit negative-value tests (Test 6) which correctly exercise the guard

---

_Reviewed: 2026-05-13T16:57:00Z_
_Reviewer: gsd-code-reviewer (deep mode, iteration 2)_
_Depth: deep_
