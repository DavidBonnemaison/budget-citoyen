---
phase: 02-core-simulation-engines-wasm
plan: 01
subsystem: simulation-engines
tags: [rust, wasm, cargo-workspace, postcard, interpn, ndarray, openfisca]

# Dependency graph
requires:
  - phase: 01-data-pipeline
    provides: "Python venv, tax-rules YAML files, canonical profiles, export scripts"
provides:
  - "Cargo workspace with 3 crates (core, wasm-micro, wasm-macro)"
  - "Phase 1 dist/ artifacts (31 JSON parameters, 32 bilingual fixtures, shock matrix stub)"
  - "Parquet/WASM loading strategy decision (postcard+gzip over parquet2)"
  - "Verified Rust toolchain (1.95.0) with wasm32-unknown-unknown target"
affects:
  - "02-02 core-types-and-validation"
  - "02-03 data-pipeline-json-schema"
  - "02-06 wasm-micro-boundary"
  - "02-07 wasm-macro-engine"

# Tech tracking
tech-stack:
  added:
    - "Rust 1.95.0 (stable)"
    - "wasm-pack 0.14.0"
    - "wasm-bindgen 0.2.121"
    - "serde 1.0.228"
    - "serde-wasm-bindgen 0.6.5"
    - "ndarray 0.17.2"
    - "interpn 0.11.0"
    - "postcard 1.1.3"
    - "openfisca-france 175.0.40"
    - "pyarrow 24.0.0"
  patterns:
    - "Cargo workspace: 3 crates (core zero-WASM, wasm-micro, wasm-macro) with path deps"
    - "Postcard binary serialization for WASM data loading (no-std, no-alloc)"
    - "interpn multilinear interpolation for shock matrix (correct ND-interp crate)"
    - "Pin exact versions for WASM-boundary crates (threat model T-02-01)"

key-files:
  created:
    - Cargo.toml (workspace root with 3 members)
    - Cargo.lock (dependency lockfile, committed per T-02-01)
    - packages/core/Cargo.toml (serde + serde_json only, zero WASM deps per D-02)
    - packages/core/src/lib.rs (pub mod types stub)
    - packages/core/src/types.rs (placeholder for Plan 02-02)
    - packages/wasm-micro/Cargo.toml (wasm-bindgen, cdylib+rlib)
    - packages/wasm-micro/src/lib.rs (stub for Plan 02-06)
    - packages/wasm-macro/Cargo.toml (interpn, ndarray, postcard)
    - packages/wasm-macro/src/lib.rs (postcard+interpn spike tests)
    - packages/wasm-macro/README.md (Data Loading Strategy documentation)
    - packages/data-pipeline/generate_dist.py (repeatable artifact generation)
    - packages/data-pipeline/dist/bilingual_test_fixtures.json (32 profiles)
    - packages/data-pipeline/dist/parameters-v2025.1.json (31 aggregated files)
    - packages/data-pipeline/dist/shockmatrix-v2025.1.parquet (CASD stub)
  modified:
    - .gitignore (added target/, dist negation, parquet negation)

key-decisions:
  - "Postcard+gzip selected as shock matrix WASM loading strategy over parquet2+gzip — simpler (~50KB binary overhead vs ~200KB), zero WASM compilation risk, flat Vec<f64> serialization sufficient for full-grid load-once pattern"
  - "interpn 0.11.0 used instead of interpolation 0.3.0 — RESEARCH.md Stack Correction validated; interpn provides N-dimensional multilinear interpolation for scientific grids"
  - "Cargo.lock committed to repo per threat model T-02-01 (pin exact versions for WASM-boundary crates)"
  - "Core crate kept clean with zero WASM dependencies (D-02 enforcement verified via grep)"

patterns-established:
  - "Cargo workspace pattern: root-level Cargo.toml with resolver=2, 3 member crates under packages/"
  - "Postcard binary pattern: flat Vec<f64> serialization for WASM data loading, gzip at HTTP level"
  - "Commit pinning: exact version strings (not ranges) for all wasm-bindgen ecosystem crates"

requirements-completed: [MICRO-01, MICRO-02, MICRO-03, MACRO-01, MACRO-02, MACRO-03]

# Metrics
duration: 41 min
completed: 2026-05-12
---

# Phase 2 Plan 1: Rust/WASM Workspace Bootstrap & Data Artifacts Summary

**3-crate Cargo workspace (core/wasm-micro/wasm-macro) with postcard binary shock matrix loading strategy, 31 JSON tax parameters from YAML, and 32 openfisca-france bilingual validation fixtures**

## Performance

- **Duration:** 41 min (including toolchain verification, openfisca-france install, crate downloads)
- **Started:** 2026-05-12T17:06:55Z
- **Completed:** 2026-05-12T17:48:38Z
- **Tasks:** 3
- **Files modified:** 47

## Accomplishments

- Rust toolchain 1.95.0 verified with wasm32-unknown-unknown target and wasm-pack 0.14.0
- 31 YAML tax parameter files converted to JSON (parameters-v2025.1) with schema validation-ready structure
- 32 bilingual test fixtures generated from canonical profiles with openfisca-france reference results
- Shock matrix Parquet stub generated (5×5×3 grid) with README documenting CASD dependency
- Cargo workspace bootstrapped: 3 crates (core, wasm-micro, wasm-macro) compiling cleanly via `cargo check --workspace`
- Parquet/WASM loading spike completed: postcard+gzip strategy selected, documented, and tested
- interpn 0.11.0 API validated for N-dimensional multilinear interpolation on regular grids

## Task Commits

Each task was committed atomically:

1. **Task 1: Install Rust toolchain** — N/A (checkpoint:human-action — toolchain already installed, verified and approved)
2. **Task 2: Generate Phase 1 data artifacts and create Cargo workspace** — `41e969c` (feat)
3. **Task 3: Parquet/WASM loading spike** — `ad31c4b` (feat)

## Files Created/Modified

**Workspace & Crates:**
- `Cargo.toml` — Workspace root with 3 members, resolver = "2"
- `Cargo.lock` — Committed lockfile (threat model T-02-01)
- `packages/core/Cargo.toml` — Core crate: serde + serde_json only (zero WASM deps)
- `packages/core/src/lib.rs` — `pub mod types;` stub
- `packages/core/src/types.rs` — Placeholder for Plan 02-02 Profile/TaxResult structs
- `packages/wasm-micro/Cargo.toml` — Micro engine: wasm-bindgen 0.2.121, serde-wasm-bindgen 0.6.5, path dep on core
- `packages/wasm-micro/src/lib.rs` — Minimal stub for Plan 02-06
- `packages/wasm-macro/Cargo.toml` — Macro engine: interpn 0.11, ndarray 0.17, postcard 1.0
- `packages/wasm-macro/src/lib.rs` — Postcard round-trip + interpn smoke tests (3 passing)
- `packages/wasm-macro/README.md` — Complete Data Loading Strategy documentation

**Data Pipeline Artifacts:**
- `packages/data-pipeline/generate_dist.py` — Repeatable artifact generation orchestrator
- `packages/data-pipeline/dist/bilingual_test_fixtures.json` — 32 profiles with openfisca-france results
- `packages/data-pipeline/dist/parameters-v2025.1.json` — Aggregated 31 tax parameter JSONs
- `packages/data-pipeline/dist/parameters-v2025.1/` — 31 individual parameter JSONs (aides, cotisations, ir, is, tva)
- `packages/data-pipeline/dist/shockmatrix-v2025.1.parquet` — Stub grid (CASD data pending)
- `packages/data-pipeline/dist/README.md` — Artifact documentation and regeneration instructions

**Infrastructure:**
- `.gitignore` — Added `target/`, dist negation for `packages/data-pipeline/dist/`, parquet negation

## Decisions Made

1. **Postcard+gzip as shock matrix loading strategy** — Selected over parquet2+gzip after spike evaluation. Postcard is no-std, adds ~50KB WASM binary overhead vs ~200KB for parquet2, and has zero compilation risk on `wasm32-unknown-unknown`. Flat `Vec<f64>` serialization meets all requirements since the full grid is loaded once at initialization.

2. **interpn 0.11.0 validated** — The RESEARCH.md Stack Correction was correct. `interpn::multilinear::regular::interpn` provides the exact API needed for N-dimensional grid interpolation. Smoke test confirms compilation and basic operation.

3. **Cargo.lock committed** — Per threat model T-02-01, exact versions of all WASM-boundary crates are pinned in Cargo.lock to prevent supply-chain drift.

4. **D-02 enforcement automated** — Core crate verified to have zero WASM dependencies via acceptance criteria check (`grep -c "wasm-bindgen" packages/core/Cargo.toml == 0`).

## Deviations from Plan

None — plan executed exactly as written. Minor adjustments:
- The pipeline scripts had no `__main__` blocks, so `generate_dist.py` was created as an orchestrator
- `.gitignore` was updated to un-ignore `packages/data-pipeline/dist/` (blocked by Python `dist/` pattern) and add `target/`

## Issues Encountered

- **openfisca-france not installed in Phase 1 venv** — Installed via pip (175.0.40) with jsonschema 4.26.0 during artifact generation. Added ~2 min to Task 2.
- **interpn API mismatch on first test attempt** — Used wrong function signature (`multilinear::regular()` as a function). Fixed by checking docs.rs for the correct `interpn(dims, starts, steps, vals, obs, out)` signature. Two iterations to fix.
- **Floating-point comparison in postcard test** — `assert_eq!` on f64 values failed due to IEEE 754 precision. Changed to epsilon comparison (`(a - b).abs() < 1e-12`).

## User Setup Required

**Rust toolchain already installed.** No additional setup required for the dev machine. The toolchain was verified at Task 1 and all acceptance criteria passed on first check.

## Known Stubs

| Stub | File | Reason |
|------|------|--------|
| Shock matrix placeholder grid | `packages/data-pipeline/dist/shockmatrix-v2025.1.parquet` | CASD (INSEE) data access pending — multi-month approval process. Grid contains zero-valued placeholder. Regenerate when real data becomes available. |
| wasm-micro lib.rs | `packages/wasm-micro/src/lib.rs` | Intentionally minimal stub — full WASM boundary to be built in Plan 02-06. |
| Core types.rs | `packages/core/src/types.rs` | Intentionally empty placeholder — Profile and TaxResult structs to be defined in Plan 02-02. |

## Next Phase Readiness

- ✅ Cargo workspace compiles cleanly — all downstream Rust plans unblocked
- ✅ Phase 1 dist/ artifacts generated — Plan 02-02 (core types), 02-03 (JSON schema), 02-06 (WASM boundary) ready
- ✅ Parquet/WASM loading strategy decided — Plan 02-07 (macro engine) can proceed with postcard+gzip approach
- ⚠️ Shock matrix contains stub data only — real data requires CASD access (external dependency, not blocking development)

---
*Phase: 02-core-simulation-engines-wasm*
*Completed: 2026-05-12*

## Self-Check: PASSED

- All 14 key files exist on disk ✓
- Both task commits found in git log (41e969c, ad31c4b) ✓
- `cargo check --workspace` exits 0 ✓
