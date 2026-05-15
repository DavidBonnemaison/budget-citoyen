---
phase: "02"
fixed_at: "2026-05-13T21:00:00Z"
review_path: ".planning/phases/02-core-simulation-engines-wasm/02-REVIEW.md"
iteration: 3
findings_in_scope: 3
fixed: 3
skipped: 0
status: all_fixed
---

# Phase 02: Code Review Fix Report — Iteration 3

**Fixed at:** 2026-05-13T21:00:00Z
**Source review:** .planning/phases/02-core-simulation-engines-wasm/02-REVIEW.md
**Iteration:** 3

**Summary:**
- Findings in scope: 3 (Warnings only)
- Fixed: 3
- Skipped: 0

## Fixed Issues

### WR-13: `types.ts` feature order documentation contradicts actual implementation

**Files modified:** `webapp/src/engine/types.ts`
**Commit:** b3531b6
**Applied fix:** Corrected the `ShockMatrixData` JSDoc comment on line 89 to match the actual feature ordering used in `macro-interpolate.ts`. Changed `0=déficit, 1=dette, 2=croissance PIB, 3=emploi` to `0=croissance PIB, 1=emploi, 2=déficit, 3=dette`.

### WR-14: `loadFromJSON()` expects wrong JSON shape

**Files modified:** `webapp/src/engine/scenario-cache.ts`
**Commit:** 00079fb
**Applied fix:** Updated `ScenarioCache.loadFromJSON()` to handle both the bare-array format and the `{scenarios: [...], metadata: {...}}` wrapper produced by `precompute.py`. Uses `Array.isArray()` to detect format and falls back to `data.scenarios ?? []` for the wrapped format.

### WR-15: `_compute_scenario_result` omits `fonciers` and `allocations_chomage` from IR taxable base

**Files modified:** `packages/data-pipeline/src/scenarios/precompute.py`
**Commit:** 50c3677
**Applied fix:** Added `chomage_total * 0.9` (10% abattement on unemployment benefits) and `fonciers_total * 0.7` (30% abattement micro-foncier) to the `revenu_net_cat` calculation in `_compute_scenario_result()`. Both income categories are now correctly included in the IR taxable base per French tax law (CGI art. 14, 28-31 for fonciers; art. 79, 80 duodecies for chômage).

---

_Fixed: 2026-05-13T21:00:00Z_
_Fixer: the agent (gsd-code-fixer)_
_Iteration: 3_
