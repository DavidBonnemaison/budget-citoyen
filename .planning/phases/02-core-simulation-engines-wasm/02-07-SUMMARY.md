---
phase: 02-core-simulation-engines-wasm
plan: 07
subsystem: wasm-boundary
tags: [wasm-bindgen, serde-wasm-bindgen, postcard, wasm-pack, wasm-bindgen-test, rust, wasm]

# Dependency graph
requires:
  - phase: 02-05
    provides: Macro interpolation engine (ShockMatrix, interpn, convex hull)
  - phase: 02-06
    provides: Bilingual fixtures, SimulationState, compute_all_taxes
provides:
  - MicroEngine WASM exports (constructor + update_and_simulate with flat &[f64] input)
  - MacroEngine WASM exports (constructor + interpolate + project with postcard binary init)
  - WASM boundary test suites (11 browser-context tests via wasm-bindgen-test)
  - panic hook configuration (debug-only console output, ASVS V7 compliance)
  - wasm-pack build output (.wasm + .js + .d.ts for both engines)
affects: [02-08, 03-ui]

# Tech tracking
tech-stack:
  added: [console_error_panic_hook 0.1, js-sys 0.3 (dev)]
  patterns:
    - "Thin WASM boundary: all business logic in modules, lib.rs is #[wasm_bindgen] glue only"
    - "Flat &[f64] input for simulation params (D-09) — zero serialization overhead"
    - "serde-wasm-bindgen::to_value output (D-10) — typed JsValue, no JSON.stringify"
    - "Postcard binary deserialization for shock matrix init (D-12)"
    - "JsValue::NULL for out-of-bounds (Pitfall 2 — no silent extrapolation)"
    - "cfg!(debug_assertions) panic hook — debug=console, release=no-op (ASVS V7)"
    - "wasm-bindgen-test with inline test data (no external JSON files required)"

key-files:
  created:
    - packages/wasm-micro/tests/wasm_boundary.rs
    - packages/wasm-macro/tests/wasm_boundary.rs
  modified:
    - packages/wasm-micro/src/lib.rs
    - packages/wasm-macro/src/lib.rs
    - packages/wasm-micro/Cargo.toml
    - packages/wasm-macro/Cargo.toml

key-decisions:
  - "Parameters::load_from_json() used instead of serde_json::from_str — Parameters does not derive Deserialize (plan correction)"
  - "SimulationState has no compute_for_profile method — boundary delegates directly to TaxBenefitSystem::compute_all_taxes() (plan correction — PATTERNS.md assumed non-existent API)"
  - "Inline JSON test data instead of include_str! — real parameter/population files do not exist yet"
  - "ShockMatrixData intermediate struct for postcard deserialization — ShockMatrix fields are individual, not a single serde type"

patterns-established:
  - "Pattern 1: MicroEngine wraps TaxBenefitSystem + SimulationState, exposes update_and_simulate(&[f64])"
	- "Pattern 2: MacroEngine wraps ShockMatrix, exposes interpolate(f64,f64,f64) → JsValue|NULL"
  - "Pattern 3: WASM panic hook: #[wasm_bindgen(start)] with cfg!(debug_assertions) gate"

requirements-completed: [MICRO-04, MICRO-05, MACRO-04]

# Metrics
duration: 14 min
completed: 2026-05-12
---

# Phase 02 Plan 07: WASM Boundary Layers Summary

**Thin #[wasm_bindgen] wrappers for both engines with flat &[f64] slice input (D-09), typed JsValue output via serde-wasm-bindgen (D-10), and 11 browser-context wasm-bindgen-test validation tests passing in headless Chrome**

## Performance

- **Duration:** 14 min
- **Started:** 2026-05-12T20:08:33Z
- **Completed:** 2026-05-12T20:23:13Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments

- MicroEngine WASM boundary: `#[wasm_bindgen]` struct with `new(params_json, population_json)` constructor validating all profiles per D-16, and `update_and_simulate(&[f64], profile_index)` accepting flat slices with zero serialization overhead
- MacroEngine WASM boundary: `#[wasm_bindgen]` struct with postcard binary `new(matrix_bytes)` constructor, `interpolate(tax, spend, horizon)` returning JsValue or JsValue::NULL for out-of-bounds (Pitfall 2), and `project(tax, spend, years)` returning multi-year trajectory vectors
- WASM boundary test suites: 5 wasm-micro tests (round-trip, invalid index, D-16 validation, malformed JSON, wrong-size params) and 6 wasm-macro tests (in-bounds, out-of-bounds null, NaN rejection, trajectory projection, partial OOB, malformed binary) — all 11 pass in headless Chrome
- ASVS V7 compliance: panic hook configured with `cfg!(debug_assertions)` gate — `console_error_panic_hook` in debug, no-op in release (no linear memory dump to browser console)
- `wasm-pack build --target web` succeeds for both crates producing .wasm, .js, .d.ts, and package.json in pkg/ directories

## Task Commits

Each task was committed atomically:

1. **Task 1: MicroEngine WASM boundary** - `a3e3158` (feat) — MicroEngine struct + constructor + update_and_simulate + panic hook + console_error_panic_hook dep
2. **Task 2: MacroEngine WASM boundary + tests** - `6998e44` (feat) — MacroEngine struct + postcard init + interpolate + project + 11 WASM boundary tests + js-sys dev-dep
3. **Task 3: Test suite verification** — No code changes (verification-only; all 71 tests pass)

## Files Created/Modified

- `packages/wasm-micro/src/lib.rs` — Full MicroEngine WASM boundary with flat &[f64] input, D-10 output, D-16 validation
- `packages/wasm-macro/src/lib.rs` — Full MacroEngine WASM boundary with postcard binary init, interpolate, project, JsValue::NULL for OOB
- `packages/wasm-micro/Cargo.toml` — Added console_error_panic_hook dependency, js-sys dev-dependency
- `packages/wasm-macro/Cargo.toml` — Added console_error_panic_hook dependency, js-sys dev-dependency
- `packages/wasm-micro/tests/wasm_boundary.rs` — 5 WASM boundary round-trip tests
- `packages/wasm-macro/tests/wasm_boundary.rs` — 6 WASM boundary round-trip tests with synthetic postcard data

## Decisions Made

- **Parameters::load_from_json() over serde_json::from_str:** Parameters does not derive Deserialize — it has a custom `load_from_json(json, expected_version)` constructor with version validation and dual-format auto-detection. Plan action described `serde_json::from_str` which would fail to compile. Used the existing `load_from_json` API.
- **Boundary delegates to TaxBenefitSystem directly:** PATTERNS.md assumed `SimulationState::compute_for_profile()` existed, but SimulationState only has `update_params()`. The boundary calls `self.system.compute_all_taxes(profile_index)` directly — keeps the boundary thin and avoids adding business logic to SimulationState.
- **Inline test data over include_str!:** Real Phase 1 parameter and population JSON files don't exist yet. Tests use inline JSON strings for parameters (simplified format with version + parameters) and profiles (single valid/invalid profile) — tests are self-contained and runnable before Phase 1 data pipeline completes.
- **ShockMatrixData intermediate struct:** ShockMatrix::new() takes individual Vec fields, not a single deserializable struct. Created a `ShockMatrixData` helper in the boundary that mirrors the postcard format contract, then destructures into ShockMatrix::new().

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed MicroEngine Debug derive for test ergonomics**
- **Found during:** Task 2 (WASM boundary test compilation)
- **Issue:** Test code used `result.unwrap_err()` which requires `E: Debug`. MicroEngine didn't derive Debug since it's a #[wasm_bindgen] struct.
- **Fix:** Added `#[derive(Debug)]` to MicroEngine struct definition.
- **Files modified:** `packages/wasm-micro/src/lib.rs`
- **Verification:** All native and WASM tests compile and pass
- **Committed in:** `6998e44` (Task 2 commit)

**2. [Rule 1 - Bug] Fixed test code mutability — engine must be `let mut`**
- **Found during:** Task 2 (cargo test compilation)
- **Issue:** `update_and_simulate(&mut self, ...)` requires `engine` to be `mut`. Several test functions used `let engine = ...` without mut.
- **Fix:** Changed 3 test functions from `let engine` to `let mut engine`.
- **Files modified:** `packages/wasm-micro/tests/wasm_boundary.rs`
- **Verification:** All tests compile and pass
- **Committed in:** `6998e44` (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (1 Debug derive, 1 mutability fix)
**Impact on plan:** Both auto-fixes necessary for compilation correctness. No scope creep. Plan corrections documented above (load_from_json API, compute_for_profile gap, inline test data) are clarifications, not fixes.

## Issues Encountered

- **wasm-pack test filter not matching:** `wasm-pack test --headless -- *filter*` didn't discover #[wasm_bindgen_test] tests with the file-name filter. Running without filter (`wasm-pack test --headless --chrome packages/wasm-micro`) discovered and ran all 11 tests correctly.
- **Parameters doesn't derive Deserialize:** Plan action referenced `serde_json::from_str` for Parameters, but Parameters uses a custom `load_from_json` constructor. Used the correct API — documented as plan correction in decisions.

## Next Phase Readiness

- Both WASM engines export typed interfaces ready for TypeScript integration (Plan 02-08 — TypeScript types from .d.ts and integration connector)
- WASM boundary tests validate JS↔WASM round-trip correctness — Phase 3 UI can immediately consume the pkg/ outputs
- Panic hook ASVS V7 compliant — production builds suppress all console output
- Ready for `wasm-pack build --target web` deployment of both crates

---
*Phase: 02-core-simulation-engines-wasm*
*Completed: 2026-05-12*
