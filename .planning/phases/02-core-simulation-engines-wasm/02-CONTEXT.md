# Phase 2: Core Simulation Engines (WASM) - Context

**Gathered:** 2026-05-12
**Status:** Ready for planning

## Phase Boundary

This phase delivers the computational heart of the platform: two WASM engines (microeconomic tax calculator + macroeconomic shock interpolator) executing in separate Web Workers. The micro engine computes IR, IS, TVA, cotisations sociales, and aides sociales for any profile, matching OpenFisca Python to ≤1e-6 precision. The macro engine performs multi-linear interpolation over the Phase 1 shock matrix to project deficit, debt, GDP growth, and employment trajectories. Both engines run entirely client-side — zero data transfer.

## Implementation Decisions

### Crate Architecture & Code Organization
- **D-01:** 3 crates: `core` (shared types, parameter loading, profiles, validation), `wasm-micro` (TaxBenefitSystem + formula evaluation), `wasm-macro` (ShockMatrix + interpolation). Cargo workspace at repo root.
- **D-02:** Core crate scope: data types (Profile, Parameter), parameter tree loading from JSON, profile parsing, test fixtures. Engine-specific logic stays in engine crates. Both engine crates import core. No engine logic in core.
- **D-03:** Crates live in `packages/` (flat alongside `tax-rules/` and `data-pipeline/`): `packages/core`, `packages/wasm-micro`, `packages/wasm-macro`.
- **D-04:** Separate CI workflow `.github/workflows/phase2-wasm.yml` with `cargo test` (native, all crates) + `wasm-pack test` (browser context, wasm crates only). Phase 1's version-consistency gate runs first as prerequisite (produces JSON test fixtures consumed by `cargo test`).

### Formula Porting Strategy
- **D-05:** Code generation from OpenFisca Python source. A Python script introspects the `openfisca-france` variable graph and generates Rust source files. No manual formula porting — the codegen automates dependency discovery and function ordering.
- **D-06:** Full OpenFisca-France variable tree (~200+ variables) — no subsetting for v1. The code generator targets everything, avoiding cherry-picking decisions about which tax domains to include.
- **D-07:** Manual codegen run, commit generated code to repo. CI step emits a soft warning (not hard gate) if `openfisca-france` upstream has a newer version than what's pinned in `packages/data-pipeline/pyproject.toml`. Re-run codegen only when upstream formulas change.
- **D-08:** Code generator output: pure Rust functions with typed inputs + match on period. One module per tax domain. Each formula becomes `fn calculate_xxx(parameters: &Parameters, period: Date, profile: &Profile) -> f64`. Dependency ordering resolved at codegen time and embedded in generated code.

### WASM Boundary & Worker Protocol Design
- **D-09:** Input: flat `&[f64]` slice + index-based setters. All slider values cross the WASM boundary in a single slice. Rust-side has a constant index mapping and updates a pre-allocated `SimulationState` struct in-place. Zero serialization overhead.
- **D-10:** Output: structured result structs via `wasm-bindgen` + `serde-wasm-bindgen`. Returns typed `MicroResult` / `MacroResult` objects with auto-generated TypeScript declarations. Small overhead acceptable since results produced once per slider interaction.
- **D-11:** Web Worker message protocol: typed request/response with correlation IDs. Each `postMessage` carries `{ id: string, type: 'SIMULATE'|'INTERPOLATE'|'INIT', payload }`. Main thread tracks pending requests by ID and discards stale responses if a newer request superseded it.
- **D-12:** Data loading: main thread fetches all static assets (tax rules JSON ~200KB, population JSON ~10MB, shock matrix Parquet ~5MB) during initial load. Transfers to workers via `postMessage` with Transferable ArrayBuffers (zero-copy). Workers never touch the network directly.

### Profile Data Model
- **D-13:** Simplified flat `Profile` struct with all relevant attributes flattened (no OpenFisca entity hierarchy). The code generator resolves cross-entity references at codegen time by inlining the relevant attributes into the flat struct.
- **D-14:** Profile storage: `Vec<Profile>` in WASM linear memory. Single-profile: index into Vec. Batch (Phase 4): `rayon::par_iter()` for multicore parallelism. All 50K profiles loaded at init (~10MB).
- **D-15:** Profile struct definition derives from code generator output. The codegen introspects OpenFisca's leaf input variables and emits the Rust struct with exactly those fields. CI regenerates when OpenFisca-France updates. Synthetic population export adapts its JSON keys to match.
- **D-16:** Strict load-time validation: every profile deserializes via serde + passes a `validate()` method checking required fields and value ranges. Returns `Result<Profile, LoadError>`. Invalid profiles are rejected and counted (never silently loaded).

### the agent's Discretion
- Exact index mapping for the flat `&[f64]` input array (which index maps to which parameter)
- Cargo workspace configuration details (workspace members, dependency versions, feature flags)
- Code generator implementation details (introspection API, Rust code formatting, output directory structure)
- Worker initialization sequencing (which worker to init first, timeout/retry strategy)
- Production service worker integration for asset caching (deferred to Phase 3/5)
- COOP/COEP header strategy (test on target platform early per STACK.md warning)

## Canonical References

Downstream agents MUST read these before planning or implementing.

### Project-level
- `.planning/PROJECT.md` — Core value, constraints, out-of-scope boundaries
- `.planning/REQUIREMENTS.md` — v1 requirements (MICRO-01 through MICRO-05, MACRO-01 through MACRO-05)
- `.planning/ROADMAP.md` — Phase ordering, dependencies (Phase 2 depends on Phase 1)
- `.planning/phases/01-data-foundation-rules-engine/01-CONTEXT.md` — Phase 1 decisions (data format, versioning, validation, reference year 2025)

### Research
- `.planning/research/STACK.md` — Technology stack (Rust/WASM, wasm-bindgen 0.2.121, ndarray 0.17, interpolation 0.3, serde-wasm-bindgen 0.6.5)
- `.planning/research/ARCHITECTURE.md` — System architecture, Web Worker isolation pattern, multi-linear interpolation algorithm, data flow
- `.planning/research/PITFALLS.md` — Pitfall 1 (WASM serialization tax), Pitfall 2 (extrapolation beyond convex hull), Pitfall 3 (DP budget exhaustion)

### Phase 1 Data Artifacts (consumed by Phase 2)
- `packages/tax-rules/parameters/` — YAML tax rules (31 files across IR/IS/TVA/cotisations/aides) converted to JSON at build time
- `packages/data-pipeline/src/validation/export_fixtures.py` — JSON test fixtures for `cargo test` / `wasm-pack test`
- `packages/data-pipeline/src/shock_matrix/` — Grid construction (Smolyak sparse + Cartesian), convex hull computation, Parquet/Zstd export
- `packages/data-pipeline/src/synthetic_pop/` — Synthetic population export (JSON records, SHA-256 integrity hashes)

### External Domain References
- OpenFisca Core documentation — Entity/Parameter/Variable structure, formula API, period handling (used by code generator)
- `openfisca-france` Python package — Variable graph, formula implementations (~200+ variables)
- wasm-bindgen documentation — JS interop patterns, `wasm-pack build --target web`, serde integration
- wasm-bindgen-rayon documentation — Parallel WASM with SharedArrayBuffer + Web Workers
- ndarray crate documentation — Multi-dimensional arrays, slicing, broadcasting
- interpolation crate documentation — Multi-linear interpolation API

## Existing Code Insights

### Reusable Assets
- `packages/tax-rules/parameters/` — Complete YAML rules with OpenFisca-compatible schema (brackets, values, metadata.reference, metadata.unit). Build-time JSON conversion pipeline ready. Used by the micro engine for parameter loading.
- `packages/data-pipeline/src/validation/export_fixtures.py` — Generates JSON test fixtures with input profiles + expected OpenFisca-France outputs. Directly consumable by `cargo test` via `include_str!()` or test helper.
- `packages/data-pipeline/src/shock_matrix/export_parquet.py` — Exports shock matrix as Parquet/Zstd with `shockmatrix-v2025.1` version tag. Contains grid metadata (breakpoints per dimension, convex hull boundaries).
- `packages/data-pipeline/src/synthetic_pop/export.py` — Exports 50K profiles as JSON records with `population-v2025.1` version tag and integrity sidecar (SHA-256, dp_epsilon).

### Established Patterns
- Version-locking: all Phase 1 artifacts use semantic tags (`rules-v2025.1`, `population-v2025.1`, `shockmatrix-v2025.1`). Phase 2 must validate its inputs match these versions.
- Optional dependency pattern (from `shock_matrix/bootstrap.py`): try/except ImportError with fallbacks. Relevant if the WASM engine needs optional features (e.g., rayon).
- NumPy float32 for grid storage (memory-efficient). Rust equivalent: `f32` / `Float32Array`.
- CI version-consistency gate: grep-based checks on YAML date keys + Python assert for reference year. Phase 2 CI extends this pattern.

### Integration Points
- Phase 2 CI consumes JSON test fixtures from Phase 1 validation framework. Phase 1's `phase1-validate.yml` must pass before `phase2-wasm.yml` runs.
- WASM micro engine loads tax rules JSON (converted from YAML by Phase 1 pipeline) and synthetic population JSON (exported by Phase 1 pipeline).
- WASM macro engine loads shock matrix Parquet (exported by Phase 1 pipeline), decodes in WASM via `parquet2` crate.
- Bilingual validation: Python reference (openfisca-france) produces expected outputs → JSON fixtures → `cargo test` compares Rust outputs with ≤1e-6 tolerance.

## Specific Ideas

- The code generator should resolve OpenFisca's entity hierarchy (Individu, Famille, FoyerFiscal, Menage) into a flat Profile struct at codegen time, so the Rust runtime never sees entity relationships.
- The flat `&[f64]` input array should have a companion constant module (generated or hand-written) that documents the index→parameter mapping for both Rust and TypeScript sides.
- The shock matrix should be decoded from Parquet/Zstd in WASM (using `parquet2` crate) rather than JSON — the Phase 1 pipeline already exports in this format and it compresses ~5x better.
- The CI staleness check for OpenFisca-France should compare the pinned version in `pyproject.toml` against the latest PyPI release, emitting a GitHub Actions warning annotation if newer.

## Deferred Ideas

None — discussion stayed within phase scope.

---

*Phase: 2-Core Simulation Engines (WASM)*
*Context gathered: 2026-05-12*
