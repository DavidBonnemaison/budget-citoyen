---
phase: 02-core-simulation-engines-wasm
plan: 09
type: gap_closure
status: complete
duration: "2 tasks"
completed: 2026-05-13
---

# Phase 02 Plan 09: Remove Old WASM Architecture — Summary

**Deleted 7,745 lines across 30 files. Removed all WASM crates, generated stub formulas, codegen pipeline, WASM workers, and WASM CI jobs. Cargo workspace now contains only the core crate.**

## Accomplishments

- Deleted `packages/wasm-micro/` crate entirely (3,800 lines including 340+ stub formulas, TaxBenefitSystem, SimulationState, MicroEngine)
- Deleted `packages/wasm-macro/` crate entirely (540 lines of interpolation logic — moved to TypeScript in Plan 02-10)
- Deleted `packages/data-pipeline/src/codegen/` pipeline (1,626 lines of Python→Rust transpiler — replaced by scenario pre-compute in Plan 02-11)
- Removed WASM-specific CI jobs: wasm-pack-build, wasm-test-micro, wasm-test-macro
- Removed wasm-pack installation from CI (wasm32 target installs also removed)
- Deleted old TypeScript workers (`micro-worker.ts`, `macro-worker.ts`) that imported WASM
- Updated CI summary gate to exclude WASM jobs
- Cargo workspace now has single member: `packages/core`

## TDD/Cleanup Commits

1. **chore(02-09): remove wasm-micro and wasm-macro crates and codegen pipeline** — `35dcb48` — 7,494 deletes, 27 files removed
2. **chore(02-09): remove WASM workers and update CI to drop wasm-pack jobs** — `2095591` — 251 deletes, 3 files changed

## Verification

- `cargo check --workspace`: passes
- `cargo test -p budget-citoyen-core`: 27/27 tests pass
- Zero wasm-bindgen references in any Cargo.toml
- Zero wasm-pack or wasm32 references in CI workflow
- `packages/wasm-micro/` and `packages/wasm-macro/` directories: gone
- `packages/data-pipeline/src/codegen/` directory: gone
- Old worker files: gone

## Deviations from Plan

None. All tasks completed as specified.

## Issues Encountered

None. Simple deletions with no cascading failures — core crate had zero WASM dependencies by design (D-02).

## Next Plan Readiness

- Cargo workspace is clean and ready for Plan 02-10 (TypeScript engines)
- Old worker files removed — Plan 02-10 will recreate `macro-worker.ts` and new `citizen-worker.ts`
- CI simplified — Plan 02-11 will add TypeScript vitest jobs and scenario pre-compute
- All stub formulas gone — no more `0.0_f64` anywhere in the codebase

---
*Phase: 02-core-simulation-engines-wasm*
*Completed: 2026-05-13*
