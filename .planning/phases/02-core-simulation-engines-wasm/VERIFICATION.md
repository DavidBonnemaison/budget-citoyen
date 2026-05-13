---
phase: 02-core-simulation-engines-wasm
verified: 2026-05-13T08:00:00Z
status: gaps_found
score: 1/5 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 2/5
  gaps_closed: []
  gaps_remaining:
    - "All 340+ generated formula functions are still 0.0_f64 stubs — no real micro computation (SC-1)"
    - "Performance criteria unverifiable — no benchmarks, stubs prevent measurement (SC-4)"
    - "WASM boundary tests require headless browser — cannot execute in cargo test (SC-5)"
    - "CI workflow never executed — no CI evidence of passing gates (SC-5)"
  regressions: []
  new_gaps:
    - "Architectural drift: 4 plans revised to hybrid architecture but codebase unchanged — 5 new-architecture files missing"
    - "Summary/Plan mismatch: 02-04, 02-06, 02-07, 02-08 SUMMARYs document old architecture, PLANs document new"
gaps:
  - truth: "The micro engine computes IR, IS, TVA, cotisations sociales, and aides sociales for any profile type, with results matching the OpenFisca Python reference to within 1e-6 precision across the bilingual test suite"
    status: failed
    reason: "All 340+ generated formula functions return 0.0_f64 (stub). IS hardcoded to 0.0, TVA module empty. The bilingual test suite validates structure (16 tests pass) but cannot assert precision because formulas produce no real output. This is the SAME gap from the previous verification — no gap closure occurred."
    artifacts:
      - path: "packages/wasm-micro/src/generated/ir.rs"
        issue: "67 formula functions return 0.0_f64; _bracket_calc helper exists but is never called by any formula"
      - path: "packages/wasm-micro/src/generated/aides.rs"
        issue: "199 formula functions return 0.0_f64"
      - path: "packages/wasm-micro/src/generated/cotisations.rs"
        issue: "63 formula functions return 0.0_f64"
      - path: "packages/wasm-micro/src/generated/is.rs"
        issue: "11 formula functions return 0.0_f64"
      - path: "packages/wasm-micro/src/generated/tva.rs"
        issue: "0 generated formulas — TVA module is empty placeholder"
      - path: "packages/wasm-micro/src/system.rs"
        issue: "IS hardcoded to 0.0 (line ~90); TVA hardcoded to 0.0 (line ~96)"
    missing:
      - "Complete Python→Rust formula translation for all 340+ generated functions — the codegen produced Rust source with embedded Python syntax that was stubbed out (Plan 02-06 Rule 3 auto-fix)"
      - "Working IS computation (requires enterprise profile data — Phase 3/4 extension)"
      - "Working TVA computation (requires consumption-estimate model — not in openfisca-france)"
      - "Bilingual precision validation suite comparing Rust output against OpenFisca Python reference at ≤1e-6 for all 32 canonical profiles"
  - truth: "A single-profile micro calculation completes in under 200ms (WASM execution + JS↔WASM serialization combined); a full macro interpolation completes in under 50ms"
    status: failed
    reason: "Performance cannot be measured. Micro formulas return 0.0 instantly (no computation to benchmark). Macro tested on synthetic 2×2×2×4 grid, not real 10×10×5 shock matrix. No criterion/benchmark infrastructure exists. WASM binary sizes: 173KB (micro), 50KB (macro). This is the SAME gap from the previous verification."
    artifacts:
      - path: "packages/wasm-micro/pkg/budget_citoyen_wasm_micro_bg.wasm"
        issue: "173KB WASM binary includes 340+ stub formulas — real computation overhead unknown"
    missing:
      - "WASM execution benchmark (criterion/cargo-criterion) for micro engine on real formulas"
      - "Macro interpolation benchmark on full 10×10×5 shock matrix (currently tested on 2×2×2 synthetic grid)"
  - truth: "Native Rust tests (cargo test with proptest property-based strategies) and WASM boundary tests (wasm-pack test) both pass in CI, confirming the core/wasm crate split prevents untestable logic"
    status: failed
    reason: "wasm-pack test --headless requires Chrome browser — 11 wasm-bindgen-test tests are authored but cannot execute outside browser context. CI workflow (.github/workflows/phase2-wasm.yml) exists (392 lines, 11 jobs) but has never been executed — no CI run history. Native cargo test: 55 pass (27 core + 16 wasm-micro + 12 wasm-macro), zero fail. This is the SAME gap from the previous verification."
    artifacts:
      - path: "packages/wasm-micro/tests/wasm_boundary.rs"
        issue: "5 wasm-bindgen-test tests require headless browser — not runnable in standard cargo test"
      - path: "packages/wasm-macro/tests/wasm_boundary.rs"
        issue: "6 wasm-bindgen-test tests require headless browser — not runnable in standard cargo test"
      - path: ".github/workflows/phase2-wasm.yml"
        issue: "CI workflow never executed — no CI run history"
    missing:
      - "wasm-pack test --headless --chrome for both wasm-micro and wasm-macro crates"
      - "At least one successful CI run of phase2-wasm.yml against a commit in this phase"
  - truth: "Architecture consistency: PLAN files, SUMMARY files, and codebase all reflect the same architectural decisions"
    status: failed
    reason: "Critical architectural drift. CONTEXT.md (revised 2026-05-13) declares a hybrid architecture (scenario pre-compute instead of formula porting). Plans 02-04, 02-06, 02-07, 02-08 were rewritten to match. But: (1) SUMMARYs still document the OLD architecture, (2) the codebase still implements the OLD architecture (with stub formulas), (3) 5 new-architecture files are MISSING from the codebase."
    artifacts:
      - path: ".planning/phases/02-core-simulation-engines-wasm/02-04-SUMMARY.md"
        issue: "SUMMARY describes 'code generator producing 340 generated Rust formulas' — but revised PLAN describes 'scenario data format & pre-compute pipeline'"
      - path: ".planning/phases/02-core-simulation-engines-wasm/02-06-SUMMARY.md"
        issue: "SUMMARY describes 'TaxBenefitSystem with formula dispatch' — but revised PLAN describes 'scenario data cache & lookup engine (ScenarioCache)'"
      - path: "packages/wasm-micro/src/cache.rs"
        issue: "MISSING — ScenarioCache required by revised Plan 02-06"
      - path: "packages/data-pipeline/src/scenarios/scenario_definitions.py"
        issue: "MISSING — required by revised Plan 02-04 Task 1"
      - path: "packages/data-pipeline/src/scenarios/precompute.py"
        issue: "MISSING — required by revised Plan 02-04 Task 2"
      - path: "packages/data-pipeline/dist/scenarios-v2025.1.json"
        issue: "MISSING — required by revised Plan 02-04"
      - path: "packages/core/src/scenario_types.rs"
        issue: "MISSING — required by revised Plan 02-04 Task 1 Part B"
    missing:
      - "Resolve the architectural direction: either commit to hybrid scenario pre-compute (implement the 5 missing files, delete generated/ stubs) OR revert to formula porting (fix codegen, implement real formulas)"
      - "Update all 4 SUMMARY files (02-04, 02-06, 02-07, 02-08) to match the chosen architecture"
      - "Ensure ROADMAP.md Success Criteria are consistent with the chosen architecture"
---

# Phase 2: Core Simulation Engines (WASM) Verification Report

**Phase Goal:** Both the microeconomic engine (IR, IS, TVA, cotisations, aides sociales) and macroeconomic engine (multi-linear interpolation over shock matrix) execute correctly in the browser via WebAssembly Web Workers, with batch interfaces avoiding serialization overhead, and pass bilingual validation against the OpenFisca Python reference — this is the computational heart of the platform.

**Verified:** 2026-05-13T08:00:00Z
**Status:** gaps_found
**Re-verification:** Yes — after gap closure (previous: gaps_found, score 2/5)

## Re-verification Summary

The previous verification (2026-05-12T22:00:00Z) found `gaps_found` with score 2/5. Four commits occurred after that date, all documentation-only (CONTEXT.md revision, plan rewrites). **No code changes** were made to close any gaps. Three new gaps emerged from architectural drift.

### Previous Gaps — Still Open

| Gap | Previous Status | Current Status |
|-----|----------------|----------------|
| All 340+ formula functions are 0.0_f64 stubs | ✗ FAILED | ✗ STILL FAILED |
| IS/TVA hardcoded to 0.0 | ✗ FAILED | ✗ STILL FAILED |
| Performance unverifiable (no benchmarks) | ✗ FAILED | ✗ STILL FAILED |
| WASM boundary tests + CI untested | ⚠️ PARTIAL | ⚠️ STILL PARTIAL |

### New Gaps (Architectural Drift)

| Gap | Status |
|-----|--------|
| 4 PLANs revised to hybrid architecture, codebase unchanged | ✗ NEW FAILURE |
| 4 SUMMARYs document old architecture, mismatch with revised PLANs | ✗ NEW FAILURE |
| 5 new-architecture files missing from codebase | ✗ MISSING |

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Micro engine computes IR, IS, TVA, cotisations, aides for any profile, matching OpenFisca Python ≤1e-6 | ✗ FAILED | All 340+ formula functions return `0.0_f64`. IS hardcoded to 0.0, TVA empty. `grep -c "0.0_f64" packages/wasm-micro/src/generated/ir.rs` → 71; aides → 203; cotisations → 67; is → 11. `_bracket_calc` helper exists in ir.rs but is never called by any formula. Bilingual test validates structure only (16 tests pass checking values exist, not that they're correct). |
| 2 | Macro engine performs multi-linear interpolation over shock matrix, returns `Option::None` outside convex hull | ✓ VERIFIED | `interpn 0.11.0` rectilinear interpolation with 4D grid. Convex hull boundary enforcement via `is_inside_hull()`. 12 tests pass (interpolation_tests.rs). Zero unsafe blocks. MACRO-05 compliant (no interest rate code). Input validation defense-in-depth. |
| 3 | Both engines run client-side in Web Workers, zero server round-trips, no data leaves browser | ⚠️ PARTIAL | 4 TypeScript worker files exist (461 lines total). `wasm-pack build --target web` succeeds for both crates. WASM pkg/ with .wasm + .js + .d.ts produced. D-12 enforced: zero `fetch()` calls in workers (confirmed via grep). BUT: micro engine formulas are stubs — no real computation runs. No `package.json`/`tsconfig.json` in webapp/ — workers cannot actually compile or execute in browser yet. |
| 4 | Micro <200ms, macro <50ms | ✗ FAILED | Formulas are stubs (return 0.0 instantly) — no real computation to benchmark. Macro tested on 2×2×2×4 synthetic grid, not real 10×10×5 matrix. No criterion/benchmark infrastructure exists. WASM bins: 173KB (micro) / 50KB (macro). |
| 5 | `cargo test` and `wasm-pack test` pass in CI | ⚠️ PARTIAL | Native `cargo test -p budget-citoyen-core`: 27 pass; `-p budget-citoyen-wasm-micro`: 16 pass; `-p budget-citoyen-wasm-macro`: 12 pass. Total: 55 native tests pass, 0 fail. `wasm-pack build` succeeds for both crates. CI workflow exists (11 jobs, 392 lines) but never executed. `wasm-pack test --headless` requires Chrome (not available in verification environment). 11 wasm-bindgen-test boundary tests authored but show 0 tests in native runner. |

**Score:** 1/5 truths verified (1 VERIFIED, 2 PARTIAL, 2 FAILED) — downgraded from previous 2/5 due to stricter evaluation of Truth 3 (workers not runnable).

**NEW TRUTH — Architecture Consistency:**

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 6 | PLANs, SUMMARYs, and codebase reflect the same architectural decisions | ✗ FAILED | 4 plans (02-04, 02-06, 02-07, 02-08) revised to hybrid architecture. 4 SUMMARYs still document old architecture. Codebase still implements old architecture. 5 new-architecture files missing. |

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `Cargo.toml` | Workspace root, 3 members, release profile | ✓ VERIFIED | 3 members: core, wasm-micro, wasm-macro. resolver=2. [profile.release] with opt-level="s", lto=true, panic="abort" |
| `packages/core/src/types.rs` | Profile, LoadError, enums, MicroResult, MacroResult | ✓ VERIFIED | 189 lines. Profile::validate() with 5 error variants. French-language errors. #[serde(deny_unknown_fields)]. |
| `packages/core/src/parameters.rs` | Parameters with BTreeMap date resolution | ✓ VERIFIED | 305 lines. Dual-format JSON loading. Version validation. get_brackets(), get_scalar(), get(). |
| `packages/core/src/test_fixtures.rs` | FixtureDoc loader, precision helpers | ✓ VERIFIED | 226 lines. include_str! embedding. assert_precision() with 1e-6 threshold. |
| `packages/wasm-micro/src/system.rs` | TaxBenefitSystem with formula dispatch | ✓ VERIFIED | 207 lines. Dispatches to generated::ir/is/tva/cotisations/aides. compute_all_taxes() with bounds-check. IS/TVA default to 0.0. **NOTE: this is OLD architecture — revised Plan 02-06 replaces with ScenarioCache.** |
| `packages/wasm-micro/src/simulation.rs` | SimulationState with flat &[f64] (D-09) | ✓ VERIFIED | 118 lines. 16 params. update_params() validates length, NaN, negative, excessive. |
| `packages/wasm-micro/src/generated/ir.rs` | Generated IR formulas | ✗ STUB | 67 functions, ALL return 0.0_f64. _bracket_calc helper exists but functions don't call it. |
| `packages/wasm-micro/src/generated/aides.rs` | Generated aides formulas | ✗ STUB | 199 functions, ALL return 0.0_f64. |
| `packages/wasm-micro/src/generated/cotisations.rs` | Generated cotisations formulas | ✗ STUB | 63 functions, ALL return 0.0_f64. |
| `packages/wasm-micro/src/generated/is.rs` | Generated IS formulas | ✗ STUB | 11 functions, ALL return 0.0_f64. |
| `packages/wasm-micro/src/generated/tva.rs` | TVA formulas | ⚠️ PLACEHOLDER | 0 generated formulas — TVA not modeled in openfisca-france. Module exists but empty. |
| `packages/wasm-macro/src/matrix.rs` | ShockMatrix struct | ✓ VERIFIED | 85 lines. Grid + breakpoints + convex hull equations. Shape validation in constructor. |
| `packages/wasm-macro/src/interpolate.rs` | interpn interpolation + hull check | ✓ VERIFIED | 93 lines. interpn::multilinear::rectilinear. Input validation. is_inside_hull(). Returns Option. |
| `packages/wasm-macro/src/projection.rs` | Trajectory projection | ✓ VERIFIED | 55 lines. Accumulates per-year interpolations. None propagation. |
| `packages/wasm-micro/src/lib.rs` | MicroEngine WASM exports | ✓ VERIFIED | #[wasm_bindgen] struct. new() constructor with D-16 validation. update_and_simulate(&[f64]). |
| `packages/wasm-macro/src/lib.rs` | MacroEngine WASM exports | ✓ VERIFIED | #[wasm_bindgen] struct. Postcard binary init. interpolate() → JsValue\|NULL. project(). |
| `webapp/src/workers/orchestrator.ts` | WorkerOrchestrator with correlation IDs | ✓ VERIFIED | 299 lines. Creates both workers. crypto.randomUUID() correlation IDs. Stale response discarding. |
| `webapp/src/workers/micro-worker.ts` | Micro engine Web Worker | ✓ VERIFIED | 62 lines. INIT + SIMULATE message handlers. D-12: zero fetch() calls. **NOTE: imports MicroEngine (old architecture).** |
| `webapp/src/workers/macro-worker.ts` | Macro engine Web Worker | ✓ VERIFIED | 74 lines. INIT + INTERPOLATE/project handlers. D-12: zero fetch() calls. |
| `webapp/src/workers/index-map.ts` | PARAM_INDICES constants | ✓ VERIFIED | 26 lines. 14 entries, indices 0-13. NUM_SIMULATION_PARAMS=16. |
| `.github/workflows/phase2-wasm.yml` | CI pipeline | ✓ VERIFIED | 392 lines, 11 jobs. Never executed. |
| **NEW ARCHITECTURE — MISSING:** | | | |
| `packages/wasm-micro/src/cache.rs` | ScenarioCache struct (Plan 02-06 revised) | ✗ MISSING | File does not exist. |
| `packages/data-pipeline/src/scenarios/scenario_definitions.py` | Scenario definitions (Plan 02-04 revised) | ✗ MISSING | File does not exist. |
| `packages/data-pipeline/src/scenarios/precompute.py` | Scenario precompute pipeline (Plan 02-04 revised) | ✗ MISSING | File does not exist. |
| `packages/data-pipeline/dist/scenarios-v2025.1.json` | Pre-computed scenario data | ✗ MISSING | File does not exist. |
| `packages/core/src/scenario_types.rs` | Rust scenario types (Plan 02-04 revised) | ✗ MISSING | File does not exist. |

**Artifacts:** 20/25 verified (5 stubs/placeholders, 5 missing new-architecture files)

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| TaxBenefitSystem | generated::ir formulas | `generated::ir::calculate_*()` calls | ✓ WIRED | system.rs dispatches to all 5 domains |
| TaxBenefitSystem | generated::aides formulas | `generated::aides::calculate_*()` calls | ✓ WIRED | RSA, AAH, APL, AF, ASPA all dispatched |
| MicroEngine::new() | TaxBenefitSystem + SimulationState | Constructor wraps both | ✓ WIRED | lib.rs instantiates TaxBenefitSystem with Parameters + Vec<Profile> |
| MacroEngine::new() | ShockMatrix | Postcard binary deserialization | ✓ WIRED | lib.rs deserializes via ShockMatrixData → ShockMatrix::new() |
| orchestrator.ts | micro-worker.ts | `new Worker(new URL(...))` | ✓ WIRED | Import path resolved |
| orchestrator.ts | macro-worker.ts | `new Worker(new URL(...))` | ✓ WIRED | Import path resolved |
| micro-worker.ts | WASM pkg | `import init, { MicroEngine }` | ✓ WIRED | Import path to wasm-micro/pkg |
| macro-worker.ts | WASM pkg | `import init, { MacroEngine }` | ✓ WIRED | Import path to wasm-macro/pkg |
| generated formulas | core types | `use budget_citoyen_core::types::Profile` | ✓ WIRED | All generated files import Profile + Parameters |
| Bilingual tests | fixture JSON | `include_str!("../../data-pipeline/dist/...")` | ✓ WIRED | test_fixtures.rs embeds fixtures at compile time |
| Macro interpolate | interpn crate | `use interpn::multilinear::rectilinear` | ✓ WIRED | interpolate.rs |
| WASM output | JS caller | `serde_wasm_bindgen::to_value()` | ✓ WIRED | Both engine lib.rs files use serde-wasm-bindgen |
| SimulationState | WASM input | `params: &[f64]` flat slice | ✓ WIRED | D-09: zero serialization overhead input boundary |

**Wiring:** 13/13 connections verified structurally. **However:** 5 of these links (TaxBenefitSystem → generated formulas) carry zero data because all formulas return 0.0_f64.

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|-------------|--------|-------------------|--------|
| TaxBenefitSystem::compute_all_taxes() | `ir_brut` | `generated::ir::calculate_ir_brut()` | ✗ No (returns 0.0_f64) | ✗ HOLLOW |
| TaxBenefitSystem::compute_all_taxes() | `cotisations_salariales` | `generated::cotisations::calculate_cotisations_salariales()` | ✗ No (returns 0.0_f64) | ✗ HOLLOW |
| TaxBenefitSystem::compute_all_taxes() | `rsa` | `generated::aides::calculate_rsa_montant()` | ✗ No (returns 0.0_f64) | ✗ HOLLOW |
| TaxBenefitSystem::compute_all_taxes() | `is_contribution` | Hardcoded `let is_contribution: f64 = 0.0;` | ✗ No (static 0.0) | ✗ HOLLOW |
| TaxBenefitSystem::compute_all_taxes() | `tva_acquittee` | Hardcoded `let tva_acquittee: f64 = 0.0;` | ✗ No (static 0.0) | ✗ HOLLOW |
| interpolate_at_point() | `out[0..4]` | `interpn::multilinear::rectilinear::interpn()` | ✓ Yes (synthetic grid data) | ✓ FLOWING |
| project_trajectory() | trajectory Vecs | `interpolate_at_point()` per year | ✓ Yes (synthetic grid data) | ✓ FLOWING |

**Data-Flow:** 2/7 flowing (macro engine works on synthetic grid; micro engine formulas are hollow — NO CHANGE from previous verification)

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Cargo workspace compiles | `cargo check --workspace` | exit 0 | ✓ PASS |
| Core tests | `cargo test -p budget-citoyen-core` | 27 passed (6 profile + 13 parameter + 8 bilingual) | ✓ PASS |
| Micro engine tests | `cargo test -p budget-citoyen-wasm-micro` | 16 passed (bilingual.rs) + 0 wasm_boundary | ✓ PASS (native only) |
| Macro engine tests | `cargo test -p budget-citoyen-wasm-macro` | 12 passed (interpolation_tests.rs) + 0 wasm_boundary | ✓ PASS (native only) |
| Micro engine WASM build | `wasm-pack build --target web packages/wasm-micro` | exit 0, pkg/ produced (173KB .wasm) | ✓ PASS |
| Macro engine WASM build | `wasm-pack build --target web packages/wasm-macro` | exit 0, pkg/ produced (50KB .wasm) | ✓ PASS |
| Zero unsafe blocks | `grep -rn "unsafe" packages/ --include="*.rs"` | 0 matches | ✓ PASS |
| MACRO-05 compliance | `grep -ri "interest_rate\|oat\|bond_yield" packages/wasm-macro/src/` | 0 matches | ✓ PASS |
| D-12: Workers never fetch() | `grep "fetch(" webapp/src/workers/*.ts` | Only in comments | ✓ PASS |
| WASM boundary tests | `wasm-pack test --headless packages/wasm-micro` | SKIPPED — requires Chrome browser | ? SKIP |
| WASM boundary tests | `wasm-pack test --headless packages/wasm-macro` | SKIPPED — requires Chrome browser | ? SKIP |
| No .map files in WASM pkg/ | `ls packages/*/pkg/*.map` | No matches (ASVS V7 ✓) | ✓ PASS |

### Test Suite Summary

| Crate | Test File | Tests | Status |
|-------|-----------|-------|--------|
| core | profile_tests.rs | 6 | ✓ PASS |
| core | parameter_tests.rs | 13 | ✓ PASS |
| core | bilingual_tests.rs | 8 | ✓ PASS (structural only — no precision comparison) |
| wasm-macro | interpolation_tests.rs | 12 | ✓ PASS |
| wasm-micro | bilingual.rs | 16 | ✓ PASS (structural only) |
| wasm-micro | wasm_boundary.rs | 5 | ? UNTESTED (needs Chrome) |
| wasm-macro | wasm_boundary.rs | 6 | ? UNTESTED (needs Chrome) |
| **Total** | | **55 native + 11 WASM** | **55/55 native pass; 11 WASM untested** |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|------------|------------|-------------|--------|----------|
| MICRO-01 | 02-03, 02-04, 02-06 | Le moteur calcule l'IR pour un profil type en WASM | ✗ BLOCKED | IR formulas return 0.0_f64 — no real computation |
| MICRO-02 | 02-03, 02-04, 02-06 | Le moteur couvre TVA, IS, cotisations sociales | ✗ BLOCKED | IS hardcoded to 0.0; TVA module empty; cotisations return 0.0_f64 |
| MICRO-03 | 02-03, 02-04, 02-06 | Le moteur calcule les aides sociales | ✗ BLOCKED | All 199 aides formulas return 0.0_f64 |
| MICRO-04 | 02-02, 02-07, 02-08 | Calcul exécuté côté client sans transfert de données | ⚠️ PARTIAL | WASM engines exist structurally but formulas don't compute; workers can't execute (no build config) |
| MICRO-05 | 02-07 | Temps de réponse < 200ms pour calcul sur profil type | ✗ BLOCKED | Formulas are stubs — cannot benchmark |
| MACRO-01 | 02-01, 02-05 | Interpolation estime la trajectoire du déficit | ✓ SATISFIED | interpn produces deficit projections on synthetic grid; 12 tests pass |
| MACRO-02 | 02-01, 02-05 | Interpolation estime la trajectoire de la dette | ✓ SATISFIED | interpn produces debt-to-GDP projections; 12 tests pass |
| MACRO-03 | 02-01, 02-05 | Interpolation estime PIB et emploi | ✓ SATISFIED | interpn produces GDP growth + employment projections; 12 tests pass |
| MACRO-04 | 02-05, 02-07, 02-08 | Résultats macro < 200ms après curseur | ⚠️ PARTIAL | Interpolation works structurally but tested on 2×2×2 grid; real 10×10×5 unbenchmarked |
| MACRO-05 | 02-05 | Taux d'intérêt lissés constants | ✓ SATISFIED | Zero references to interest_rate/oat/bond_yield in wasm-macro |

**Coverage:** 4/10 satisfied (MACRO-01/02/03/05), 2 partial (MICRO-04, MACRO-04), 4 blocked (MICRO-01/02/03/05)

**WARNING:** REQUIREMENTS.md marks all MICRO-* and MACRO-* requirements as `[x]` (completed). This is **incorrect** — MICRO-01/02/03/05 are blocked (formulas are stubs), and MICRO-04/MACRO-04 are only partial. The [x] markers should be downgraded to reflect the actual implementation state.

### Anti-Patterns Found

| File | Issue | Severity | Impact |
|------|-------|----------|--------|
| `packages/wasm-micro/src/generated/ir.rs` | 67 formula functions all return 0.0_f64 | 🛑 Blocker | No IR computation |
| `packages/wasm-micro/src/generated/aides.rs` | 199 formula functions all return 0.0_f64 | 🛑 Blocker | No aides computation |
| `packages/wasm-micro/src/generated/cotisations.rs` | 63 formula functions all return 0.0_f64 | 🛑 Blocker | No cotisations computation |
| `packages/wasm-micro/src/generated/is.rs` | 11 formula functions all return 0.0_f64 | 🛑 Blocker | No IS computation |
| `packages/wasm-micro/src/system.rs` | `let is_contribution: f64 = 0.0;` with comment "IS defaults to 0.0" | 🛑 Blocker | IS always zero |
| `packages/wasm-micro/src/system.rs` | `let tva_acquittee: f64 = 0.0;` with comment "0 TVA formulas" | 🛑 Blocker | TVA always zero |
| `packages/wasm-micro/src/generated/tva.rs` | Empty module — 0 generated formulas | ⚠️ Warning | TVA domain placeholder |
| `webapp/` | No `package.json`, `tsconfig.json`, or Vite config | ⚠️ Warning | Workers can't compile/execute in browser |
| `REQUIREMENTS.md` | MICRO-01/02/03/05 marked `[x]` but formulas are stubs | ⚠️ Warning | False completion markers |
| `02-04-SUMMARY.md` | Documents "code generator producing 340 generated Rust formulas" | ⚠️ Warning | Mismatch with revised Plan 02-04 (scenario pre-compute) |
| `02-06-SUMMARY.md` | Documents "TaxBenefitSystem with formula dispatch" | ⚠️ Warning | Mismatch with revised Plan 02-06 (ScenarioCache) |
| `02-07-SUMMARY.md` | Documents MicroEngine with update_and_simulate | ⚠️ Warning | Mismatch with revised Plan 02-07 (ScenarioCache) |
| `02-08-SUMMARY.md` | References MicroEngine constructor pattern | ⚠️ Warning | Mismatch with revised Plan 02-08 (ScenarioCache) |

**Anti-patterns:** 13 found (6 blockers, 7 warnings)

### Human Verification Required

N/A — Infrastructure/foundation phase with no user-facing elements. All acceptance criteria are verifiable programmatically. The gaps found are structural (stub formulas, architectural drift) and do not require human UX testing.

---

## Gaps Summary

### Critical Gaps (BLOCK progress — carried from previous verification)

**Gap 1: All 340+ generated formula functions are stubs (return `0.0_f64`)**
- **Evidence:** `grep -c "0.0_f64" packages/wasm-micro/src/generated/*.rs` returns 352 total matches. `_bracket_calc` helper exists in ir.rs but is never called by any formula.
- **Impact:** Success Criterion 1 (≤1e-6 bilingual precision) impossible. Requirements MICRO-01/02/03 blocked. TaxBenefitSystem infrastructure is structurally complete and correctly wired, but produces no real output.
- **Missing:** Complete Python→Rust formula translation for all 340+ generated functions. The codegen produced Rust source with embedded Python syntax that had to be stubbed out (Plan 02-06 Rule 3 auto-fix).

**Gap 2: IS and TVA permanently default to 0.0**
- **Evidence:** `system.rs` lines ~90: `let is_contribution: f64 = 0.0;` and ~96: `let tva_acquittee: f64 = 0.0;`
- **Impact:** Even after formula porting, IS and TVA will remain zero without data model extensions.
- **Scope:** Documented design limitations (flat Profile D-13, openfisca-france scope).

**Gap 3: Performance unverifiable (SC-4)**
- **Evidence:** No criterion/benchmark infrastructure. No `benches/` directories. Formulas are stubs — timing them measures instant returns.
- **Impact:** The <200ms/<50ms guarantees are unproven.

**Gap 4: WASM boundary tests and CI untested (SC-5)**
- **Evidence:** 11 wasm-bindgen-test tests authored but require headless Chrome. CI workflow exists but never executed.
- **Impact:** No proof that WASM boundary works end-to-end in browser context.

### NEW Critical Gap: Architectural Drift (PLANs vs SUMMARYs vs Codebase)

**Gap 5: Three-way architecture inconsistency**

The CONTEXT.md (revised 2026-05-13) declares a hybrid architecture where:
- D-05 (NEW): No formula porting — scenario pre-compute instead
- D-11 (NEW): wasm-micro is a SKELETON only (scenario cache)
- D-17 (NEW): Micro worker is optional

Plans 02-04, 02-06, 02-07, 02-08 were rewritten to match. But:

| Layer | 02-04 | 02-06 | 02-07 | 02-08 |
|-------|-------|-------|-------|-------|
| **CONTEXT.md** | Scenario pre-compute | Scenario cache (skeleton) | ScenarioCache WASM boundary | ScenarioCache workers |
| **PLAN.md** | Scenario data format & pre-compute pipeline ✓ | Scenario data cache & lookup engine ✓ | ScenarioCache boundary ✓ | ScenarioCache workers ✓ |
| **SUMMARY.md** | Code generator, 340 formulas ✗ | TaxBenefitSystem + formula dispatch ✗ | MicroEngine + update_and_simulate ✗ | MicroEngine constructor ✗ |
| **CODEBASE** | generated/ stubs present ✗ | system.rs present ✗ | MicroEngine (not ScenarioCache) ✗ | MicroEngine imports ✗ |

**Missing new-architecture files (5 files):**
1. `packages/wasm-micro/src/cache.rs` — ScenarioCache struct
2. `packages/data-pipeline/src/scenarios/scenario_definitions.py` — 3+ scenario definitions
3. `packages/data-pipeline/src/scenarios/precompute.py` — CI pipeline
4. `packages/data-pipeline/dist/scenarios-v2025.1.json` — pre-computed data
5. `packages/core/src/scenario_types.rs` — Rust scenario types

### Non-Critical Gaps (Can Defer to Phase 3)

1. **Web Workers not executable in browser** — `webapp/` lacks build tooling. Phase 3 adds this.
2. **TVA module is empty placeholder** — openfisca-france doesn't model TVA. Needs custom consumption-estimate model.
3. **REQUIREMENTS.md has false completion markers** — MICRO-01 through MICRO-05 marked `[x]` but only MICRO-04 is partial (the rest are blocked by stubs).

---

## Decision Coverage

All 21 CONTEXT.md decisions (D-01 through D-13 original, D-05 through D-23 NEW) tracked:

| Decision | Description | Status |
|----------|-------------|--------|
| D-01 | 3 crates (core, wasm-micro, wasm-macro) | ✓ Honored |
| D-02 | Core zero WASM deps | ✓ Honored |
| D-03 | Crates in packages/ | ✓ Honored |
| D-04 | CI workflow | ✓ Honored (exists, never run) |
| D-05 (NEW) | No formula porting — scenario pre-compute | ✗ NOT IMPLEMENTED |
| D-06 (NEW) | Candidate scenario selector | ✗ NOT IMPLEMENTED |
| D-07 (NEW) | CI pre-computes scenario data | ✗ NOT IMPLEMENTED |
| D-08 (NEW) | Expert mode → backend Python | ✗ NOT IMPLEMENTED |
| D-09 (NEW) | Privacy split: citizen vs expert | ✗ NOT IMPLEMENTED (no UI) |
| D-10 (NEW) | MICRO-04 waived for experts | ✗ NOT IMPLEMENTED |
| D-11 (NEW) | wasm-micro = skeleton only | ✗ STILL HAS TaxBenefitSystem |
| D-12 | Core crate scope | ✓ Honored |
| D-13 | packages/ location | ✓ Honored |
| D-14 | CI cargo test + wasm-pack test | ⚠️ Partial (CI never run) |
| D-15 | Macro &[f64] input | ✓ Honored |
| D-16 | Macro serde-wasm-bindgen output | ✓ Honored |
| D-17 (NEW) | Micro worker optional | ✗ STILL HAS micro worker importing MicroEngine |
| D-18 | Data loading via postMessage | ✓ Honored |
| D-19 | Flat Profile preserved | ✓ Honored |
| D-20 | validate() preserved | ✓ Honored |
| D-21 | Load-time validation | ✓ Honored |
| D-22 | Scenario data format <200ms | ✗ NOT IMPLEMENTED |
| D-23 | Scenario data version-locked | ✗ NOT IMPLEMENTED |

**Decision coverage:** 12/21 honored, 1 partial, 8 not implemented (all NEW decisions)

---

## Recommended Resolution Path

The project faces a critical architectural decision. Two valid paths exist:

### Path A: Commit to Hybrid Architecture (implement what CONTEXT.md declares)

**Tasks:**
1. Implement the 5 missing new-architecture files (ScenarioCache, scenario_definitions.py, precompute.py, scenarios-v2025.1.json, scenario_types.rs)
2. Remove the `packages/wasm-micro/src/generated/` directory (3,336 lines of stub formulas)
3. Replace `system.rs` TaxBenefitSystem with ScenarioCache
4. Update wasm-micro/src/lib.rs to export ScenarioCache instead of MicroEngine
5. Update webapp workers to import ScenarioCache
6. Update ROADMAP.md Success Criteria to reflect scenario pre-compute approach
7. Update REQUIREMENTS.md to clarify MICRO-01/02/03 are satisfied via pre-computation, not client-side computation
8. Rewrite all 4 SUMMARY files (02-04, 02-06, 02-07, 02-08) to match the new architecture
9. Run wasm-pack test --headless for both crates
10. Execute CI pipeline

### Path B: Revert to Formula Porting (fix what the codebase actually implements)

**Tasks:**
1. Revert CONTEXT.md D-05 through D-23 to the original codegen approach
2. Fix the Python→Rust code generator to produce syntactically valid Rust (no Python character literals, numpy calls)
3. Replace all 340+ stub function bodies with working Rust implementations
4. Run bilingual precision validation against OpenFisca Python at ≤1e-6
5. Add criterion benchmarks for micro engine
6. Run wasm-pack test --headless for both crates
7. Execute CI pipeline
8. Rewrite the 4 revised PLAN files (02-04, 02-06, 02-07, 02-08) back to the original architecture

**Recommendation:** Path A (commit to hybrid) is preferred — it was the considered architectural decision documented in CONTEXT.md and avoids the enormous Python→Rust porting effort. Path B would require fixing 340+ formula translations, which the original codegen already failed to do.

---

## Verification Metadata

**Verification approach:** Goal-backward re-verification (derived from ROADMAP.md success criteria + previous VERIFICATION.md gaps)
**Must-haves source:** ROADMAP.md Success Criteria + PLAN.md frontmatter must_haves + Architecture Consistency (new)
**Automated checks:** 10 passed, 2 skipped (Chrome-dependent), 0 failed
**Human checks required:** 0 (infrastructure phase — N/A)
**Previous verification gaps:** 3 (all still open)
**New gaps discovered:** 1 architectural drift (5 missing files + 4 SUMMARY mismatches)

---

*Verified: 2026-05-13T08:00:00Z*
*Verifier: the agent (gsd-verifier)*
*Re-verification: Yes — previous gaps_found at 2026-05-12T22:00:00Z*
