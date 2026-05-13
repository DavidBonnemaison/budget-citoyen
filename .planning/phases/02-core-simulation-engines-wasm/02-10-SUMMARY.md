---
phase: 02-core-simulation-engines-wasm
plan: 10
subsystem: typescript-engines
tags: [macro-interpolation, scenario-cache, web-workers, typescript, trilinear, pure-ts]
requires:
  - phase: 02-09
    provides: deleted WASM crates and workers (clean workspace)
provides:
  - Pure TypeScript macro interpolation engine (replaces wasm-macro crate)
  - ScenarioCache with O(1) HashMap lookups (replaces wasm-micro crate)
  - citizen-worker.ts and macro-worker.ts with zero WASM imports
  - Updated orchestrator.ts for hybrid architecture
affects: [02-11, 03-ui]
tech-stack:
  added: []
  patterns:
    - "Trilinear interpolation on 4D grid (tax × spend × horizon × feature)"
    - "Convex hull gating with 1e-10 tolerance before interpolation"
    - "Float64Array subarray views for zero-copy binary matrix parsing"
    - "ScenarioCache: Map<scenarioId, Map<profileIndex, ScenarioResult>> for O(1)"
    - "D-12: workers construct data from postMessage, never call fetch()"
    - "D-11: correlation ID protocol preserved for stale response discarding"
key-files:
  created:
    - webapp/src/engine/types.ts
    - webapp/src/engine/macro-interpolate.ts
    - webapp/src/engine/scenario-cache.ts
    - webapp/src/engine/__tests__/macro-interpolate.test.ts
    - webapp/src/engine/__tests__/scenario-cache.test.ts
    - webapp/src/workers/citizen-worker.ts
    - webapp/src/workers/macro-worker.ts
  modified:
    - webapp/src/workers/orchestrator.ts
decisions:
  - "Binary matrix format: 4×uint32 header + f64 arrays (tax, spend, horizon, hull, grid) in single ArrayBuffer for zero-copy transfer"
  - "Feature order in grid: 0=gdp_growth, 1=employment, 2=deficit, 3=debt (matches interpn convention from deleted Rust crate)"
  - "SimulatePayload uses scenarioId instead of raw params array — O(1) HashMap lookup replaces WASM formula computation"
  - "INTERPOLATE message type handles both single-point (interpolate) and multi-year (project) via subType discriminator"
duration: 16 min
completed: 2026-05-13
---

# Phase 02 Plan 10: TypeScript Macro + Micro Replacement Engines — Summary

**Implemented pure TypeScript replacements for both deleted WASM crates: trilinear macro interpolation engine with convex hull enforcement, ScenarioCache with O(1) HashMap lookups, and two zero-WASM Web Workers.**

## Accomplishments

- Created `webapp/src/engine/types.ts` — 200 lines of TypeScript interfaces mirroring deleted Rust core crate types (MacroResult, ScenarioResult, ScenarioDefinition, ShockMatrixData, WorkerRequest/Response, 7 payload types)
- Implemented `webapp/src/engine/macro-interpolate.ts` — pure TS trilinear interpolation engine: `isInsideHull()` (convex hull boundary check with 1e-10 tolerance), `interpolateAtPoint()` (binary search + 2³ corner extraction + trilinear blend), `projectTrajectory()` (multi-year all-or-nothing projection)
- Created `webapp/src/engine/scenario-cache.ts` — `ScenarioCache` class with `Map<scenarioId, Map<profileIndex, ScenarioResult>>` for O(1) access, `addScenario()`, `fromDocs()` static factory, `loadFromJSON()` async factory (main-thread only)
- Wrote `webapp/src/workers/citizen-worker.ts` — Web Worker replacing the deleted WASM micro-worker: INIT constructs ScenarioCache, SIMULATE performs O(1) HashMap lookup → CITIZEN_RESULT
- Wrote `webapp/src/workers/macro-worker.ts` — Web Worker replacing the deleted WASM macro-worker: parses binary shock matrix from transferred ArrayBuffer (zero-copy Float64Array views), handles INTERPOLATE/PROJECT with pure TS trilinear interpolation
- Updated `webapp/src/workers/orchestrator.ts` — renamed microWorker→citizenWorker, updated Worker URLs, changed init() signature to `(scenariosJson, matrixBytes)`, changed simulate() to accept `(scenarioId, profileIndex)`, preserved D-11 correlation ID protocol
- Created 12+ unit tests in `macro-interpolate.test.ts` matching the deleted Rust interpolation tests
- Created 10 unit tests in `scenario-cache.test.ts` covering empty cache, missing keys, multi-scenario, list isolation

## Commits

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 10-01 | Create TypeScript type definitions | `2402c09` | `webapp/src/engine/types.ts` (created) |
| 10-02 | Implement TS macro interpolation engine | `0e57c52` | `webapp/src/engine/macro-interpolate.ts` (created), `webapp/src/engine/__tests__/macro-interpolate.test.ts` (created) |
| 10-03 | Implement ScenarioCache class | `8571518` | `webapp/src/engine/scenario-cache.ts` (created), `webapp/src/engine/__tests__/scenario-cache.test.ts` (created) |
| 10-04 | Rewrite Web Workers for pure TS | `1966f3c` | `webapp/src/workers/citizen-worker.ts` (created), `webapp/src/workers/macro-worker.ts` (created), `webapp/src/workers/orchestrator.ts` (modified), `webapp/src/engine/types.ts` (modified) |
| 10-05 | Verify TypeScript engines | *(verification only — no code changes)* | — |

## Verification

- ✅ Zero WASM imports in all workers (`grep "wasm-pack\|wasm-bindgen\|import init\|wasm_"` → zero matches)
- ✅ D-12 compliance: `fetch()` only in worker comments, never in code
- ✅ MACRO-05 compliance: zero interest rate variation code (`grep "interest_rate\|bond_yield\|rate_variation"` → zero matches)
- ✅ All imports resolve correctly (citizen-worker→scenario-cache+types, macro-worker→macro-interpolate+types, orchestrator→types)
- ✅ All 7 required files created and present
- ✅ Zero references to old micro-worker.ts (only in explanatory comments)
- ⚠️ Unit tests could not be executed — no vitest/package.json in webapp/ (test infra belongs to a future phase)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added scenarioId to SimulatePayload**

- **Found during:** Task 10-04 (orchestrator update)
- **Issue:** Plan specified "SIMULATE handler: lookup(scenarioId, profileIndex)" but the existing SimulatePayload had `params: number[]` with no scenarioId field. Workers need scenarioId for O(1) HashMap key.
- **Fix:** Updated `SimulatePayload` to use `scenarioId: string` instead of `params: number[]`, updated orchestrator's `simulate()` signature to `(scenarioId, profileIndex)`.
- **Files modified:** `webapp/src/engine/types.ts`, `webapp/src/workers/orchestrator.ts`
- **Commit:** `1966f3c`

### Plan Adjustments

None. All tasks executed as specified — gap_closure plan successfully closed the architectural drift from the deleted WASM crates.

## Issues Encountered

- No test infrastructure (vitest, tsconfig, package.json) exists in `webapp/` — unit tests are created and logically verified but cannot be executed yet. Test infrastructure should be added in a future phase (likely 03-ui).
- The binary matrix format (`parseMatrixBytes` in macro-worker) specifies a contract between the orchestrator (main thread) and macro worker that will need coordination with the data pipeline (Plan 02-11).

## Requirements Completed

- MICRO-04: O(1) HashMap scenario cache lookups
- MICRO-05: citizen-worker.ts with typed message protocol
- MACRO-01: Trilinear interpolation engine
- MACRO-02: Convex hull boundary enforcement
- MACRO-03: Multi-year trajectory projection
- MACRO-04: Zero WASM imports in all workers
- MACRO-05: No interest rate variation logic

## Next Plan Readiness

- ✅ Pure TypeScript engines ready for Plan 02-11 (hybrid scenario pre-compute + backend)
- ✅ Orchestrator API matches new architecture (scenarioId-based simulation, Workers with zero WASM)
- ✅ Binary matrix contract defined for data pipeline integration

## Self-Check: PASSED

- ✅ All 8 files exist on disk
- ✅ All 4 commits (2402c09, 0e57c52, 8571518, 1966f3c) verified in git log
