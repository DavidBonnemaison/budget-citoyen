---
phase: 02-core-simulation-engines-wasm
plan: 08
subsystem: infra
tags: [web-workers, wasm, ci, github-actions, typescript, cargo, release-profile]

# Dependency graph
requires:
  - phase: 02-07
    provides: WASM boundary layers (MicroEngine, MacroEngine) with wasm-pack pkg/ output
provides:
  - Web Worker infrastructure (micro/macro workers, orchestrator, index-map) for browser-side WASM execution
  - CI pipeline (phase2-wasm.yml) with 11 jobs gating all engine correctness
  - Release profile for production WASM binary optimization
affects: [03-ui]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Web Worker message protocol with correlation IDs (D-11)"
    - "Typed request/response via discriminated unions in TypeScript"
    - "Stale response discarding for rapid slider interactions"
    - "WASM import via wasm-pack pkg/ default export"
    - "CI gate summary with needs: + if: always() pattern (from Phase 1 convention)"
    - "Release profile: opt-level='s' + lto=true + panic='abort' for production WASM"

key-files:
  created:
    - webapp/src/workers/micro-worker.ts
    - webapp/src/workers/macro-worker.ts
    - webapp/src/workers/orchestrator.ts
    - webapp/src/workers/index-map.ts
    - .github/workflows/phase2-wasm.yml
  modified:
    - Cargo.toml

key-decisions:
  - "MicroEngine constructor uses `new MicroEngine(paramsJson, populationJson)` — not `MicroEngine.new()` factory pattern from PATTERNS.md (actual wasm-bindgen exports regular constructor)"
  - "Macro worker INIT receives binary Uint8Array (matrix_bytes), micro worker INIT receives JSON strings — different init payloads per engine type per their WASM signatures"
  - "Release profile uses `panic = 'abort'` for ASVS V7 compliance — prevents stack trace exposure in production WASM"
  - "Macro worker INTERPOLATE message distinguished by `subType` field: 'interpolate' for single-point, 'project' for multi-year trajectory"
  - "11 CI jobs structured with needs dependency chain matching Phase 1 convention: setup → fmt/clippy/test → build → wasm-test → version-check → summary gate"

patterns-established:
  - "Pattern 1: Worker import pattern — `import init, { EngineName } from '../../../packages/wasm-name/pkg'`"
  - "Pattern 2: Orchestrator correlation ID — `crypto.randomUUID()` per request, `latest{Source}Id` for stale discard"
  - "Pattern 3: CI conventions — header comments, `{domain}-{action}` job naming, `::error::` / `::warning::` annotations, summary gate with `if: always()`"

requirements-completed: [MICRO-04, MICRO-05, MACRO-04]

# Metrics
duration: 12 min
completed: 2026-05-12
---

# Phase 02 Plan 08: Web Workers, CI Pipeline & Release Profile Summary

**Web Worker infrastructure loading WASM engines via postMessage protocol with correlation IDs, 11-job CI pipeline gating all engine correctness, and release profile for production WASM optimization — all 8 Phase 2 plans complete**

## Performance

- **Duration:** 12 min
- **Started:** 2026-05-12T20:27:35Z
- **Completed:** 2026-05-12T20:39:15Z
- **Tasks:** 3
- **Files modified:** 6

## Accomplishments

- Four TypeScript Web Worker files (micro-worker, macro-worker, orchestrator, index-map) that load WASM engines in the browser with typed message protocol (D-11) and zero network access (D-12 privacy guarantee)
- CI pipeline (.github/workflows/phase2-wasm.yml) with 11 jobs: Phase 1 gate, rust-setup, cargo-fmt, cargo-clippy, cargo-test-core, cargo-test-workspace, wasm-pack-build, wasm-test-micro, wasm-test-macro, version-check (with OpenFisca staleness soft warning per D-07), and ci-summary gate
- Release profile ([profile.release]) in workspace Cargo.toml with size optimization, LTO, panic=abort, and debug stripping for ASVS V7 production compliance — both WASM crates build under 200KB

## Task Commits

Each task was committed atomically:

1. **Task 1: Create TypeScript Web Workers with typed message protocol** — `8839f20` (feat)
2. **Task 2: Create CI workflow with cargo test, wasm-pack test, version gates, and OpenFisca staleness check** — `79fcd6c` (feat)
3. **Task 3: Add release profile configuration for WASM binary size optimization** — `d5ff90a` (feat)

## Files Created/Modified

- `webapp/src/workers/micro-worker.ts` — Microsimulation engine Web Worker: imports WASM, handles INIT + SIMULATE messages with try/catch error handling
- `webapp/src/workers/macro-worker.ts` — Macroeconomic engine Web Worker: imports WASM, handles INIT + INTERPOLATE messages (single-point and multi-year projection via subType discriminator)
- `webapp/src/workers/orchestrator.ts` — WorkerOrchestrator class: creates both workers, dispatches requests with correlation IDs, discards stale responses (D-11), provides simulate/interpolate/project/init API with Promise-based interface
- `webapp/src/workers/index-map.ts` — PARAM_INDICES constant (14 entries, indices 0-13) + NUM_SIMULATION_PARAMS = 16, shared with Rust simulation.rs (D-09)
- `.github/workflows/phase2-wasm.yml` — 11-job CI pipeline: Phase 1 gate (D-04), rust-setup, format, clippy, core tests, workspace tests, WASM builds, headless WASM tests, version gates with OpenFisca staleness (D-07, soft warning), unsafe block audit (MACRO-05), ci-summary gate
- `Cargo.toml` — Added [profile.release] section with opt-level="s", debug=false, lto=true, panic="abort", codegen-units=1

## Decisions Made

- Used actual WASM constructor signatures (`new MicroEngine(paramsJson, populationJson)`, `new MacroEngine(matrixBytes)`) rather than the `Engine.new()` factory pattern in PATTERNS.md — the wasm-bindgen output exports regular constructors
- Macro worker INIT receives binary `Uint8Array` (postcard-encoded shock matrix), micro worker INIT receives JSON strings (parameters + population) — different payload shapes per engine type
- Macro worker INTERPOLATE messages use a `subType` discriminator field: `'interpolate'` for single-point queries, `'project'` for multi-year trajectory projections — both route through the same worker message type
- Release profile uses `panic = "abort"` for ASVS V7 compliance — prevents unwinding with memory exposure in production WASM

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed constructor pattern mismatch between PATTERNS.md and actual WASM bindings**
- **Found during:** Task 1 (worker implementation)
- **Issue:** PATTERNS.md and RESEARCH.md code examples use `MicroEngine.new(paramsJson, populationJson)` factory pattern, but the actual wasm-bindgen `.d.ts` declarations export a regular constructor: `constructor(params_json: string, population_json: string)` → `new MicroEngine(...)`
- **Fix:** Used `new MicroEngine(paramsJson, populationJson)` and `new MacroEngine(new Uint8Array(matrixBytes))` — matching actual TypeScript declarations
- **Files modified:** `webapp/src/workers/micro-worker.ts`, `webapp/src/workers/macro-worker.ts`
- **Verification:** TypeScript constructor calls match the `.d.ts` signatures exactly
- **Committed in:** `8839f20` (Task 1 commit)

**2. [Rule 1 - Bug] D-12 verification grep matches comment text**
- **Found during:** Task 1 (verification)
- **Issue:** The plan's D-12 verification `grep -c "fetch("` matches the privacy guarantee comment text "NEVER calls fetch()" — producing false positive count of 1 for each worker file. No actual `fetch()` function calls exist in the code.
- **Fix:** Verified with `grep -v "//" | grep -v "\*"` that zero functional `fetch()` calls exist. No code change needed — the comment is part of the D-12 enforcement documentation.
- **Files modified:** None (verification clarification only)
- **Verification:** Grep excluding comment lines returns 0 matches
- **Committed in:** N/A (verification note, no code change)

---

**Total deviations:** 2 auto-fixed (2 Rule 1 bugs)
**Impact on plan:** Minimal — constructor pattern mismatch required adaptation but actual behavior identical. D-12 grep false positive is a verification quirk, not a code issue.

## Issues Encountered

- PATTERNS.md code patterns use `MicroEngine.new()` factory convention but wasm-bindgen generates regular constructors — needed to verify against actual `.d.ts` files to determine correct API
- D-12 verification grep command matches the privacy comment text "NEVER calls fetch()" — the plan's grep-based check needs comment-exclusion for accurate results, but functionally the guarantee holds

## Next Phase Readiness

- All 8 Phase 2 plans complete — WASM engines, workers, CI, release profile ready for Phase 3
- Phase 3 (Interactive Simulation Shell MVP) can now import orchestrator.ts and worker infrastructure directly
- Worker files are TypeScript (.ts) — Phase 3 will add Vite + TypeScript config (tsconfig.json) for compilation
- WASM import paths use relative paths (`../../../packages/`) — Phase 3 may configure path aliases in vite.config.ts
- CI pipeline covers all correctness gates: native tests, WASM tests, version checks, format, lint — ready for PR workflows
- Release profile ready for production builds — Phase 5 hardening will verify COOP/COEP headers for SharedArrayBuffer (wasm-bindgen-rayon)

---
*Phase: 02-core-simulation-engines-wasm*
*Completed: 2026-05-12*
