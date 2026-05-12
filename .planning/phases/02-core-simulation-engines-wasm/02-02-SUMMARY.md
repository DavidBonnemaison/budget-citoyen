---
phase: 02-core-simulation-engines-wasm
plan: 02
subsystem: simulation-engine
tags: [rust, tdd, types, serde, proptest, profile, validation]

# Dependency graph
requires:
  - phase: 02-core-simulation-engines-wasm
    provides: Rust workspace with core crate, Cargo.toml with serde/proptest dependencies
provides:
  - Profile struct with serde Deserialize (consumed by micro engine, macro engine, Web Worker boundary)
  - LoadError enum with thiserror::Error derive and French-language validation messages
  - SituationFamiliale, TypeActivite enumerations
  - MicroResult, AidesResult, MacroResult output structs
  - Profile::validate() validation gate per D-16
  - proptest property-based validation tests
affects: ["03-tax-benefit-system", "04-web-worker", "05-macro-engine"]

# Tech tracking
tech-stack:
  added: [thiserror 2.0]
  patterns:
    - "TDD with RED-GREEN-REFACTOR: proptest failing tests -> minimal impl -> cargo fmt/clippy cleanup"
    - "#[serde(deny_unknown_fields)] on all deserialized structs at trust boundaries"
    - "Validation gate pattern: Profile::validate() returns Result<(), LoadError> — invalid data rejected before consumption"
    - "French-language error messages in Display impls for public-facing error types"

key-files:
  created:
    - packages/core/tests/profile_tests.rs
    - packages/core/tests/profile_tests.proptest-regressions
  modified:
    - packages/core/src/types.rs
    - packages/core/Cargo.toml

key-decisions:
  - "thiserror 2.0 for LoadError std::error::Error impl — lighter than manual impl, well-maintained ecosystem standard"
  - "Relative tolerance (f64::EPSILON * value * 10) for serde round-trip test — absolute 1e-10 fails for large f64 values in serde_json text serialization"

patterns-established:
  - "Validation gate: Result<(), LoadError> — single early-return pattern, rejects on first violation"
  - "Threat-informed serde: deny_unknown_fields + validate() gate between deserialization and business logic"
  - "Proptest regression files committed to VCS — captures known failure seeds for deterministic re-runs"

requirements-completed: [MICRO-04]

# Metrics
duration: 7min
completed: 2026-05-12
---

# Phase 2 Plan 2: Profile Validation & Core Types Summary

**Profile struct with strict validation gate, LoadError with French error messages, and property-based proptest coverage — all in the core crate with zero WASM dependencies**

## Performance

- **Duration:** 7 min
- **Started:** 2026-05-12T17:54:41Z
- **Completed:** 2026-05-12T18:01:45Z
- **Tasks:** 1 feature (TDD: RED → GREEN → REFACTOR)
- **Files modified:** 4

## Accomplishments
- Profile struct with 8 fields (profile_id, age, patrimoine, revenu_fiscal, situation_familiale, nombre_parts, type_activite, nb_enfants) — the universal data contract for micro/macro engines and Web Worker boundary
- LoadError enum with 5 variants: InvalidAge, NegativeWealth, NegativeIncome, InvalidParts, MissingField — French-language error messages via thiserror::Error derive
- Profile::validate() rejects invalid data at the trust boundary (age > 120, negative wealth/income, parts < 1.0) per D-16
- 6 proptest property-based tests covering valid profiles, all 4 validation failure paths, and serde JSON round-trip
- #[serde(deny_unknown_fields)] on Profile for strict deserialization (T-02-22 mitigation)
- Zero WASM dependencies in the core crate per D-02

## Task Commits

Each TDD phase was committed atomically:

1. **RED: Failing tests** - `496c580` (test) — 6 proptest tests fail with E0432: types/Profile not found
2. **GREEN: Implementation** - `accd346` (feat) — Profile, LoadError, enums, output structs; all 6 tests pass
3. **REFACTOR: Cleanup** - `16757f3` (refactor) — cargo fmt formatting, clippy passes with zero warnings

**Plan metadata:** _(forthcoming)_

## Files Created/Modified
- `packages/core/src/types.rs` - Profile struct, LoadError enum, SituationFamiliale/TypeActivite enums, MicroResult/AidesResult/MacroResult output structs, Profile::validate()
- `packages/core/tests/profile_tests.rs` - 6 proptest property-based tests for Profile validation and serde round-trip
- `packages/core/tests/profile_tests.proptest-regressions` - Proptest failure seed for deterministic regression testing
- `packages/core/Cargo.toml` - Added thiserror 2.0 dependency

## Decisions Made
- Used `thiserror` 2.0 for `LoadError` `std::error::Error` implementation — cleaner than manual `Display` + `Error` impl, well-maintained ecosystem standard
- Relative tolerance (`f64::EPSILON * value.abs().max(1.0) * 10.0`) for serde round-trip f64 comparison — absolute `1e-10` fails for large values in serde_json text serialization
- `#[serde(deny_unknown_fields)]` on Profile — rejects unexpected JSON keys at the deserialization boundary per threat model T-02-22
- French-language error messages in `LoadError` Display impl — matches project language, UI layer (Phase 3) will further sanitize before user display

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed floating-point tolerance in serde round-trip test**
- **Found during:** GREEN phase (verification)
- **Issue:** Round-trip test used absolute tolerance `1e-10` for f64 comparison. serde_json serializes large f64 values (~99M) with limited text precision, causing test failures.
- **Fix:** Replaced absolute tolerance with relative tolerance using `f64::EPSILON * value.abs().max(1.0) * 10.0`
- **Files modified:** packages/core/tests/profile_tests.rs
- **Verification:** All 6 proptest tests pass, including round-trip with proptest-generated extreme values
- **Committed in:** `accd346` (Task 1 GREEN commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug)
**Impact on plan:** Test-only fix — no behavior change to production code. Relative tolerance is mathematically correct for floating-point comparison.

## Issues Encountered
- Proptest generated a regression file (`profile_tests.proptest-regressions`) during the initial failing round-trip test — committed as recommended by proptest documentation (captures known failure seeds for deterministic re-runs in CI)

## User Setup Required
None — no external service configuration required.

## Next Phase Readiness
- Profile struct ready for consumption by Plan 02-03 (TaxBenefitSystem core types integration)
- LoadError enum ready for use in Phase 3 UI error display
- Core crate remains WASM-free per D-02 — ready for wasm-bindgen wrapper crate addition in Plan 02-06

---
*Phase: 02-core-simulation-engines-wasm*
*Completed: 2026-05-12*
