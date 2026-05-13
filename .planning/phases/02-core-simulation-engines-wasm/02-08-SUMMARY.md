---
phase: 02-core-simulation-engines-wasm
plan: 08
subsystem: infra
tags: [web-workers, typescript, ci, github-actions, orchestrator, hybrid-architecture]

# Dependency graph
requires:
  - phase: 02-07
    provides: Pure TypeScript engines (macro-interpolate, scenario-cache, types)
provides:
  - Web Worker infrastructure (citizen/macro workers, orchestrator, index-map) with zero WASM
  - CI pipeline (phase2-wasm.yml) with 7 jobs: Phase 1 gate, rust fmt/clippy/test, scenario pre-compute, vitest, version gates
  - Typed message protocol (D-11) with correlation IDs and stale response discarding
  - D-12 privacy enforcement: workers never call fetch(), data arrives via postMessage with Transferable ArrayBuffers
affects: [03-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Web Worker message protocol with correlation IDs (D-11)"
    - "Typed request/response via discriminated unions in TypeScript"
    - "Stale response discarding for rapid slider interactions"
    - "WorkerOrchestrator: main-thread coordination with Promise-based API"
    - "Pure TypeScript workers — zero WASM imports, zero fetch() in workers (D-12)"
    - "CI gate summary with needs: + if: always() pattern (from Phase 1 convention)"
    - "Scenario pre-compute job in CI: Python openfisca-france pipeline with version gates"
    - "Vitest for TypeScript engine tests in CI"

key-files:
  created:
    - webapp/src/workers/citizen-worker.ts
    - webapp/src/workers/macro-worker.ts
    - webapp/src/workers/orchestrator.ts
    - webapp/src/workers/index-map.ts
    - .github/workflows/phase2-wasm.yml
  modified: []

key-decisions:
  - "Citizen worker uses ScenarioCache.fromDocs() — receives parsed JSON via postMessage, zero WASM"
  - "Macro worker parses binary ArrayBuffer into Float64Array views — zero-copy, zero WASM"
  - "WorkerOrchestrator owns both workers, dispatches with crypto.randomUUID() correlation IDs"
  - "D-12: orchestrator fetches static assets (JSON, binary matrix) on main thread, transfers zero-copy to workers"
  - "CI pipeline: removed wasm-pack, wasm-bindgen-test, WASM crate test jobs — added scenario pre-compute + vitest"
  - "INTERPOLATE messages use subType discriminator: 'interpolate' for single-point, 'project' for multi-year trajectory"

patterns-established:
  - "Pattern 1: WorkerOrchestrator — main-thread coordination, correlation IDs, stale discard, Promise API"
  - "Pattern 2: citizen-worker — ScenarioCache construction from postMessage JSON, O(1) SIMULATE lookups"
  - "Pattern 3: macro-worker — binary matrix parsing, Float64Array subviews, INTERPOLATE/PROJECT dispatch"
  - "Pattern 4: CI conventions — Phase 1 gate, scenario pre-compute, vitest, version gates, summary gate"

requirements-completed: [MICRO-04, MICRO-05, MACRO-04]

# Metrics
duration: 12 min
completed: 2026-05-12
---

# Phase 02 Plan 08: Web Workers, CI Pipeline Summary

**Simplified Web Worker infrastructure with zero WASM imports — citizen worker performs O(1) scenario cache lookups, macro worker runs pure TS trilinear interpolation, orchestrator coordinates both with correlation IDs and stale response discarding. CI pipeline updated with scenario pre-compute + vitest jobs.**

> **Architecture note (02-11 gap closure):** Plan 02-08 originally imported WASM engines via `wasm-pack pkg/` default exports with postcard binary deserialization. The simplified architecture (Plans 02-09/02-10/02-11) replaced all WASM imports with pure TypeScript engines. Workers now import `scenario-cache.ts` and `macro-interpolate.ts` directly — no wasm-pack, no postcard, no SharedArrayBuffer. This SUMMARY reflects the current architecture.

## Performance

- **Duration:** 12 min (original) + rewrite (02-11)
- **Started:** 2026-05-12T20:27:35Z
- **Completed:** 2026-05-13 (rewritten for hybrid architecture)
- **Tasks:** 3 (original) + rewrite
- **Files modified:** 5

## Accomplishments

- **Citizen worker** (`citizen-worker.ts`): constructs `ScenarioCache` from JSON received via postMessage INIT, handles SIMULATE requests with O(1) HashMap lookups — no computation, no WASM, no fetch()
- **Macro worker** (`macro-worker.ts`): parses binary shock matrix ArrayBuffer into Float64Array subviews (zero-copy), handles INTERPOLATE (single-point) and PROJECT (multi-year) requests using pure TS trilinear interpolation — no WASM, no postcard
- **WorkerOrchestrator** (`orchestrator.ts`): main-thread coordination class owning both workers, `init()` for parallel worker initialization with zero-copy ArrayBuffer transfer, `simulate()`/`interpolate()`/`project()` API with Promise return types, D-11 correlation IDs via `crypto.randomUUID()`, stale response discarding for rapid slider interactions
- **Index map** (`index-map.ts`): PARAM_INDICES constants shared with TypeScript engine — 14 entries (indices 0-13), NUM_SIMULATION_PARAMS = 16 (D-09 contract)
- **CI pipeline** (`phase2-wasm.yml`): 7 gating jobs — Phase 1 artifact gate, rust fmt, rust clippy, core cargo test, scenario pre-compute (Python openfisca-france), TypeScript vitest, version consistency gates — zero wasm-pack jobs

## Task Commits

1. **Task 1 (original): Web Workers** — `8839f20` (feat)
2. **Task 2 (original): CI workflow** — `79fcd6c` (feat)
3. **Task 3 (original): Release profile** — `d5ff90a` (feat)
4. **02-10 rewrite (workers):** — `1966f3c` (feat)
5. **02-11 CI rewrite:** — `f33f75a` (feat)

## Files Created/Modified

- `webapp/src/workers/citizen-worker.ts` — Citizen microsimulation worker: INIT (JSON parse → ScenarioCache), SIMULATE (O(1) lookup), ERROR handling, D-12 privacy enforcement
- `webapp/src/workers/macro-worker.ts` — Macroeconomic engine worker: INIT (binary ArrayBuffer parse → Float64Array ShockMatrixData), INTERPOLATE/PROJECT dispatch, null for OOB
- `webapp/src/workers/orchestrator.ts` — Main-thread coordinator: dual worker management, correlation IDs, stale response discarding, Promise-based API, zero-copy transfer
- `webapp/src/workers/index-map.ts` — Shared parameter index constants (14 entries) matching D-09 contract
- `.github/workflows/phase2-wasm.yml` — CI pipeline with scenario pre-compute + vitest + core cargo test + version gates

## Decisions Made

- **Pure TypeScript workers:** Replaced `import init, { MicroEngine } from '../../../packages/wasm-micro/pkg'` with `import { ScenarioCache } from '../engine/scenario-cache'`. Workers now compile and run entirely in the TypeScript/Vite toolchain — no wasm-pack build step needed.
- **Binary matrix parsing in worker:** The macro worker parses the binary shock matrix format (uint32 header + Float64 data) directly from the transferred ArrayBuffer. No postcard deserialization needed — the format is a simple binary layout documented in the worker source.
- **Orchestrator as single source of truth:** The WorkerOrchestrator is the only module that creates workers and dispatches requests. Phase 3 UI imports only this class — internal worker details are encapsulated.
- **CI simplification:** Removed 4 wasm-pack jobs (build + test for micro and macro), 2 workspace cargo test jobs, and the unsafe block audit. Added scenario pre-compute (Python) and vitest (TypeScript) jobs. Total CI jobs reduced from 11 to 7 — faster feedback, fewer transitive dependencies.

## Deviations from Plan

None in the current architecture. The original Plan 02-08 deviations (constructor pattern mismatch, D-12 grep false positive) are moot — no WASM constructors or wasm-pack imports exist.

## Issues Encountered

None.

## Next Phase Readiness

- All 11 Phase 2 plans complete — engines, workers, CI ready for Phase 3
- Phase 3 (Interactive Simulation Shell MVP) can import `WorkerOrchestrator` directly
- Worker files are TypeScript (.ts) — Phase 3 will add Vite + TypeScript config (tsconfig.json, vitest.config.ts) for compilation
- CI pipeline covers all correctness gates: native tests, scenario pre-compute, TypeScript vitest, version checks, format, lint
- Workers never touch the network (D-12) — all data arrives via postMessage from the main thread
- Stale response discarding (D-11) handles rapid slider dragging (60 req/s) correctly

---

*Phase: 02-core-simulation-engines-wasm*
*Completed: 2026-05-12 (original), rewritten: 2026-05-13 (02-11 gap closure)*
