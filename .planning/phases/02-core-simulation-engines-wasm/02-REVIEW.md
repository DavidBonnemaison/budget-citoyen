---
iteration: 3
status: issues_found
depth: deep
files_reviewed: 24
critical: 0
warning: 3
info: 4
total: 7
phase: "02"
phase_name: "core-simulation-engines-wasm"
files_reviewed_list:
  - .github/workflows/phase2-wasm.yml
  - packages/core/Cargo.toml
  - packages/core/src/lib.rs
  - packages/core/src/parameters.rs
  - packages/core/src/test_fixtures.rs
  - packages/core/src/types.rs
  - packages/core/tests/parameter_tests.rs
  - packages/core/tests/profile_tests.rs
  - packages/data-pipeline/dist/bilingual_test_fixtures.json
  - packages/data-pipeline/dist/parameters-v2025.1.json
  - packages/data-pipeline/dist/shockmatrix-v2025.1.parquet
  - packages/data-pipeline/generate_dist.py
  - packages/data-pipeline/pyproject.toml
  - packages/data-pipeline/src/scenarios/__init__.py
  - packages/data-pipeline/src/scenarios/precompute.py
  - packages/data-pipeline/src/scenarios/scenario_definitions.py
  - webapp/src/engine/__tests__/macro-interpolate.test.ts
  - webapp/src/engine/__tests__/scenario-cache.test.ts
  - webapp/src/engine/macro-interpolate.ts
  - webapp/src/engine/scenario-cache.ts
  - webapp/src/engine/types.ts
  - webapp/src/workers/citizen-worker.ts
  - webapp/src/workers/macro-worker.ts
  - webapp/src/workers/orchestrator.ts
---

# Phase 02: Code Review Report — Iteration 3 (FINAL)

**Reviewed:** 2026-05-13T20:15:00Z
**Depth:** deep
**Files Reviewed:** 24
**Status:** issues_found

## Summary

Iteration 3 (final) deep re-review of all 24 Phase 02 source files. All 7 issues from iteration 2 (CR-07, CR-08, WR-11, WR-12, IN-09, IN-10, IN-11) have been **correctly fixed** and verified. The previous 17 fixes from iteration 1 remain intact with no regressions detected.

However, 7 new issues were discovered in this final pass — 3 warnings and 4 info items. None are critical (no security vulnerabilities, no crashes, no data corruption), but they represent documentation inconsistencies, type safety gaps, and latent correctness concerns that should be addressed before the Phase 3 integration.

### Fix Verification — Iteration 2 Issues

| ID | Description | Status |
|----|-------------|--------|
| CR-07 | Python precompute ignores bic/micro_bic/benefice_agricole/aa_h | ✅ **Fixed** — `_compute_scenario_result` now extracts all 9 income categories (lines 298-315) |
| CR-08 | `scenario-cache.test.ts` import from wrong module | ✅ **Fixed** — imports `ScenarioDoc` from `'../scenario-cache'` (line 7) |
| WR-11 | Rust QF caps children at 2 parts | ✅ **Fixed** — formula now correctly handles 3+ children with full parts (lines 185-190) |
| WR-12 | Wrong abattements for independent/agricultural income | ✅ **Fixed** — `revenu_net_cat` applies 50% for BIC/micro-BIC, 100% for agricole (lines 358-364) |
| IN-09 | `index-map.ts` dead code | ✅ **Fixed** — file removed from codebase |
| IN-10 | precompute docstring misleading | ✅ **Fixed** — docstring updated to "simplified formulas...cross-validated" (line 1) |
| IN-11 | Test name misleading about hull rejection | ✅ **Fixed** — updated to "hull rejection" (line 296) |

### Fix Verification — Iteration 1 Issues

All 17 iteration 1 fixes (CR-01 through CR-06, WR-01 through WR-10, IN-01 through IN-08) remain correctly applied with no regressions. Key highlights:
- CR-01: IR bracket threshold 180648 → `_compute_ir_bareme()` line 138 ✓
- CR-02: QF formula in Python → `_compute_quotient_familial()` lines 92-120 ✓
- CR-06: CSG/CRDS rate 9.7% → `_estimate_cotisations()` line 168 ✓
- WR-02: Dynamic horizon bounds → `interpolateAtPoint()` line 123 ✓

### Cross-File Regression Check

No regressions detected. All cross-module contracts verified:
- `scenario_definitions.py` → `precompute.py`: `ScenarioDefinition` import and parameter extraction correct
- `macro-interpolate.ts` → `macro-worker.ts`: `interpolateAtPoint`/`projectTrajectory` call signatures match
- `orchestrator.ts` → `macro-worker.ts`: `INTERPOLATE` and `PROJECT` message types correctly routed
- `citizen-worker.ts` → `scenario-cache.ts`: `ScenarioCache.fromDocs()` correctly consumes `ScenarioDoc[]`
- `test_fixtures.rs` → `types.rs`: `Profile` struct fields all populated by `profile_from_fixture`
- `parameters.rs` → `types.rs`: `Bracket` re-export path resolved correctly
- CI workflow → all gates: `REFERENCE_YEAR` constant found, `v2025.1` tags confirmed, all 7 jobs defined

---

## Warnings

### WR-13: `types.ts` feature order documentation contradicts actual implementation

**File:** `webapp/src/engine/types.ts:89` vs `webapp/src/engine/macro-interpolate.ts:94,188`
**Issue:** The `ShockMatrixData` JSDoc in types.ts documents:
```
featureIdx: 0=déficit, 1=dette, 2=croissance PIB, 3=emploi
```
But the actual implementation in `macro-interpolate.ts` uses:
```
feature order is: 0=gdp_growth, 1=employment, 2=deficit, 3=debt
```
And the return statement confirms this (line 188-189):
```typescript
// Feature order: results[0]=gdp_growth, results[1]=employment,
//               results[2]=deficit, results[3]=debt
return {
    deficitTrajectory: [results[2]],      // index 2, NOT 0
    debtTrajectory: [results[3]],         // index 3, NOT 1
    gdpGrowthTrajectory: [results[0]],    // index 0, NOT 2
    employmentTrajectory: [results[1]],   // index 1, NOT 3
};
```
The types.ts documentation is inverted relative to reality. If a developer reads types.ts and builds a binary shock matrix with features in the documented order (déficit=0, dette=1, ...), the interpolation engine would swap gdp↔deficit and employment↔debt — producing silently incorrect macroeconomic projections.

The actual ordering matches the Parquet schema in `generate_dist.py` (fields: gdp_growth, employment_change, deficit_change, debt_to_gdp_ratio), so the code is consistent — but the documentation betrays it.

**Fix:**
```typescript
// In webapp/src/engine/types.ts, line 89, replace:
// * où featureIdx: 0=déficit, 1=dette, 2=croissance PIB, 3=emploi.
// with:
// * où featureIdx: 0=croissance PIB, 1=emploi, 2=déficit, 3=dette.
```

---

### WR-14: `loadFromJSON()` in `scenario-cache.ts` expects wrong JSON shape — would fail at runtime

**File:** `webapp/src/engine/scenario-cache.ts:126-135`
**Issue:** The static method `ScenarioCache.loadFromJSON(url)` fetches a URL and does:
```typescript
const docs: ScenarioDoc[] = await response.json();
return ScenarioCache.fromDocs(docs);
```
It expects the response to be an array of `ScenarioDoc[]`. However, the actual precompute output file `scenarios-v2025.1.json` (generated by `precompute.py` lines 495-508) has structure:
```json
{
  "scenarios": [ /* ScenarioDoc[] */ ],
  "metadata": {
    "version": "v2025.1",
    "reference_year": 2025,
    ...
  }
}
```
The top-level is an **object**, not an array. If `loadFromJSON` is ever called with the real precompute URL, `response.json()` returns `{ scenarios: [...], metadata: {...} }` which would be cast to `ScenarioDoc[]` — the `ScenarioCache.fromDocs()` would then receive an object instead of an array, causing a runtime error (`docs is not iterable` or silent type confusion).

Currently, `loadFromJSON` is never called in the existing code path (the orchestrator's `init()` receives pre-parsed JSON as a string). But the method is public, exported, and documented as "the primary constructor" approach. It's a latent footgun.

**Fix:**
```typescript
static async loadFromJSON(url: string): Promise<ScenarioCache> {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(
      `Failed to load scenario data: ${response.status} ${response.statusText}`,
    );
  }
  const data = await response.json();
  // Support both formats: bare array and { scenarios: [...] } wrapper
  const docs: ScenarioDoc[] = Array.isArray(data) ? data : data.scenarios ?? [];
  return ScenarioCache.fromDocs(docs);
}
```

---

### WR-15: `_compute_scenario_result` omits `fonciers` and `allocations_chomage` from IR taxable base

**File:** `packages/data-pipeline/src/scenarios/precompute.py:358-364`
**Issue:** The `revenu_net_cat` calculation (lines 358-364) determines the IR taxable income but only includes `salaires`, `pensions`, `bnc`, `bic`, `micro_bic`, and `benefice_agricole` — it omits `fonciers_total` (rental income) and `allocations_chomage` (unemployment benefits). Under French tax law (Code général des impôts):
- **Revenus fonciers** (art. 14, 28-31): Subject to IR under micro-foncier regime (30% abattement if < 15 000 €) or régime réel
- **Allocations chômage** (art. 79, 80 duodecies): Subject to IR after 10% abattement for frais professionnels

Both are included in `revenu_brut_global` (lines 311-315) for computing `revenu_disponible_avant_tva` but excluded from IR calculation. This means:
- Profiles with rental income (e.g., `multi_proprietaire` with 30 000 € fonciers, `rentier_foncier` with 50 000 €) have their IR understated
- Profiles with unemployment benefits (e.g., `chomeur` with 18 000 €) have their IR potentially misstated

The bilingual test fixtures' expected IR values happen to match the simplified formulas for the specific 32 profiles (either because the missing income is zero, or because bracket effects cancel out). But if new fixtures are added or the scenario modifies IR rates, these profiles would produce incorrect IR projections.

**Fix:**
```python
# Add fonciers and allocations_chomage to revenu_net_cat with correct abattements:
revenu_net_cat = (
    salaire_total * 0.9 + pension_total * 0.9   # 10% abattement professionnel
    + chomage_total * 0.9                        # 10% abattement on unemployment
    + bnc_total * 0.9                            # 10% abattement on BNC
    + bic_total * 0.5                            # 50% abattement under micro-BIC
    + micro_bic_total * 0.5                      # 50% abattement on micro-BIC
    + benefice_agricole_total * 1.0              # enters IR directly
    + fonciers_total * 0.7                       # 30% abattement micro-foncier
)
# NOTE: Micro-foncier regime applies only if total ≤ 15 000 €.
# Above threshold, régime réel applies — consider adding a conditional.
```

---

## Info

### IN-12: `ProjectPayload.subType` is required but never sent by orchestrator nor read by macro-worker

**File:** `webapp/src/engine/types.ts:194` + `webapp/src/workers/orchestrator.ts:222-229`
**Issue:** The `ProjectPayload` interface declares `subType: 'project'` as a **required** field, but:
- `orchestrator.ts` `project()` method (lines 222-229) sends `{ tax, spend, years }` — **without** `subType`
- `macro-worker.ts` PROJECT handler (lines 155-161) casts `payload as ProjectPayload` but never accesses `subType`

The TypeScript compiler doesn't catch this because `WorkerRequest.payload` is typed `unknown`, and the `satisfies WorkerRequest` annotation doesn't enforce the inner payload shape. The runtime cast `as ProjectPayload` is unsafe. The `subType` field exists only as dead bytes in the type definition — it serves no purpose and masks a type-safety gap.

**Fix:** Make `subType` optional in `ProjectPayload`:
```typescript
export interface ProjectPayload {
  tax: number;
  spend: number;
  years: number;
  subType?: 'project';  // ← make optional
}
```
Or remove it entirely since it's unused.

---

### IN-13: Test description references outdated hardcoded horizon range `[1, 5]`

**File:** `webapp/src/engine/__tests__/macro-interpolate.test.ts:304`
**Issue:** The test description reads:
```typescript
it('returns null for horizon outside [1, 5] range', () => {
```
But WR-02 replaced the hardcoded `[1, 5]` range with dynamic matrix-derived bounds (`matrix.horizonBp[0]` to `matrix.horizonBp[matrix.horizonBp.length - 1]`). For the test matrix, the actual range is `[1.0, 2.0]`. The test correctly tests against the matrix bounds, but the description references the old hardcoded range. This is misleading during test failure diagnosis.

**Fix:**
```typescript
it('returns null for horizon outside matrix bounds', () => {
```

---

### IN-14: `makeDoc()` test helper uses `Record<number, …>` but `ScenarioDoc.results` expects `Record<string, …>`

**File:** `webapp/src/engine/__tests__/scenario-cache.test.ts:31-36`
**Issue:** The test helper `makeDoc` types its `results` parameter as `Record<number, ScenarioResult>`:
```typescript
function makeDoc(
  definition: ScenarioDefinition,
  results: Record<number, ScenarioResult>,  // ← number keys
): ScenarioDoc {
  return { definition, results };
}
```
But `ScenarioDoc.results` is `Record<string, ScenarioResult>`. TypeScript considers `Record<number, T>` non-assignable to `Record<string, T>` because a `string`-indexed type could have non-numeric keys. Vitest may transpile without strict checking, so this compiles silently — but strict mode (`strict: true` in tsconfig) would flag it.

**Fix:**
```typescript
function makeDoc(
  definition: ScenarioDefinition,
  results: Record<string, ScenarioResult>,  // ← match the interface
): ScenarioDoc {
  return { definition, results };
}
```

---

### IN-15: `INTERPOLATE` payload includes unused `subType` field sent by orchestrator

**File:** `webapp/src/workers/orchestrator.ts:200`
**Issue:** The orchestrator's `interpolate()` method sends:
```typescript
payload: { tax, spend, horizon, subType: 'interpolate' },
```
The `subType` field is present but never read by `macro-worker.ts` INTERPOLATE handler (the comment on line 128 says "subType removed — PROJECT type handles multi-year"). This is wasted bytes in the postMessage transfer. Not harmful, but residual from the pre-WR-09 architecture where INTERPOLATE handled both single-point and multi-year via subType routing.

**Fix:** Remove `subType` from the payload:
```typescript
payload: { tax, spend, horizon },
```
And remove `subType` from `InterpolatePayload` interface in types.ts if no other consumers use it.

---

## Security Scan

- **Hardcoded secrets:** None detected (grepped for `password\|secret\|api_key\|token`)
- **Dangerous functions:** None (`eval`/`innerHTML`/`dangerouslySetInnerHTML`/`exec`/`system`/`shell_exec` not found in source)
- **Debug artifacts:** `console.debug` in `orchestrator.ts` is gated behind `import.meta.env.DEV` (WR-10 fix verified)
- **Empty catch blocks:** None found
- **Path traversal:** No file path construction from user input
- **CI workflow supply chain:** `actions-rs/toolchain@v1` is a known version (widely used, no known vulnerabilities). `actions/setup-python@v5` and `actions/setup-node@v4` are current.
- **D-12 privacy enforcement:** Verified — `citizen-worker.ts` and `macro-worker.ts` have zero `fetch()`/`XMLHttpRequest` calls. All data arrives via `postMessage`.

---

_Reviewed: 2026-05-13T20:15:00Z_
_Reviewer: gsd-code-reviewer (deep mode, iteration 3)_
_Depth: deep_
