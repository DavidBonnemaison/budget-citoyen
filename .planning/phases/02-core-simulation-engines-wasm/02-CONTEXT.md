# Phase 2: Core Simulation Engines (WASM) - Context

**Gathered:** 2026-05-13
**Status:** Updated — hybrid architecture replaces codegen port

## Phase Boundary

This phase delivers the computational heart of the platform: a dual-mode architecture where citizens get instant pre-computed scenario results (zero data transfer) and experts access backend Python OpenFisca computation on-demand. The macro engine (multi-linear interpolation over the Phase 1 shock matrix) remains in WASM, projecting deficit, debt, GDP, and employment trajectories. **The Python-to-Rust formula codegen approach (D-05 through D-08, original) is replaced** — no OpenFisca logic is ported to Rust.

## Implementation Decisions

### Hybrid Architecture — Formula Porting Strategy (REPLACES original D-05 through D-08)

- **D-05 (NEW):** No Python-to-Rust formula porting. The 3,336 lines of generated Rust formula code in `wasm-micro/src/generated/` become removable. Citizens get pre-computed scenario results (static lookup, zero data transfer). Experts use backend Python OpenFisca compute on-demand (no 200ms constraint, explicit privacy tradeoff).
- **D-06 (NEW):** Citizen mode uses candidate scenario selector — user picks from a fixed list (e.g., 2027 presidential candidates' reform programs). Sub-scenarios per candidate possible later (Option A+). The macro engine sliders remain for exploring trajectory projections within each scenario.
- **D-07 (NEW):** Pre-computed scenario data generated in CI pipeline by running official Python `openfisca-france` against canonical profiles for each candidate scenario. Results stored as compressed static file (Parquet/JSON/Binary) and loaded by the browser on first access. Re-generated when OpenFisca-France updates (PLF cycle).
- **D-08 (NEW):** Expert mode — backend Python OpenFisca compute triggered by a "calculate" button. No 200ms latency constraint applies. Privacy: experts knowingly send anonymized profiles to backend; PII-free validation middleware ensures nothing identifiable enters the request body. Computation handled by a stateless API endpoint (Phase 5).

### Privacy Boundary (NEW)

- **D-09 (NEW):** Privacy split is explicit and per-mode: citizen mode = zero data transfer (static lookup file only, no requests), expert mode = voluntary backend compute with anonymized profiles. Both modes are clearly documented in the UI. No data from citizen mode ever reaches a server.
- **D-10 (NEW):** MICRO-04 (zero client data transfer) is met for citizens, explicitly waived for experts. This satisfies the project's core promise (Privacy by Design for the general public) while enabling advanced analysis.

### Crate Architecture & Code Organization (PRESERVED with scope reduction)

- **D-11:** 3 crates: `core` (shared types, parameter loading, profiles, validation), `wasm-macro` (ShockMatrix + interpolation + scenario data loading), `wasm-micro` (skeleton only — scenario data cache, no formula engine).
- **D-12:** Core crate scope unchanged: data types (Profile, Parameter), parameter tree loading from JSON, profile parsing, test fixtures. Engine-specific logic stays in engine crates.
- **D-13:** Crates live in `packages/`: `packages/core`, `packages/wasm-micro`, `packages/wasm-macro`.
- **D-14:** CI workflow tests `cargo test` (native) + `wasm-pack test` (wasm crates). Phase 1 version-consistency gate runs first.

### WASM Boundary & Worker Architecture (ADJUSTED)

- **D-15:** Macro engine input unchanged: flat `&[f64]` slice + index-based setters for slider values. Zero serialization overhead for macro interpolation.
- **D-16:** Macro engine output unchanged: structured `MacroResult` via `serde-wasm-bindgen` with auto-generated TypeScript declarations.
- **D-17:** Worker model: macro worker remains (interpn + projection). Micro worker becomes optional — may be absorbed into main thread for scenario data loading/caching, or kept as a lightweight worker for the scenario lookup table.
- **D-18:** Data loading: main thread fetches static assets (scenario lookup table, shock matrix). Transfers to macro worker via `postMessage` with Transferable ArrayBuffers (zero-copy).

### Profile Data Model (PRESERVED)

- **D-19:** Simplified flat `Profile` struct — still needed for backend Python compute, canonical profile validation, and scenario data schema. No longer driven by codegen; derives from canonical profile schema documented in Phase 1.
- **D-20:** Profile validation unchanged: `validate()` method checking required fields and value ranges. Returns `Result<Profile, LoadError>`.
- **D-21:** Strict load-time validation preserved for any browser-loaded profile data.

### Scenario Data Format (NEW)

- **D-22:** Pre-computed scenario data format and loading strategy deferred to planner/researcher — candidates include Parquet, flat binary, or compressed JSON. Key constraint: <200ms load and lookup latency.
- **D-23:** Scenario data version-locked following Phase 1 pattern: `scenarios-v2025.1` tag, CI version consistency gate against reference OpenFisca-France version.

### the agent's Discretion

- Exact scenario data file format (Parquet vs JSON vs binary vs hybrid)
- Scenario lookup table schema (candidate × profile × metric dimensions)
- Micro crate disposition (skeleton, gutted, or removed entirely)
- Worker architecture optimization (single macro worker vs dual-worker)
- Exact index mapping for the macro engine's `&[f64]` input array
- Production service worker integration for asset caching (Phase 3/5)
- COOP/COEP header strategy (test on target platform early)
- Backend OpenFisca compute endpoint design (Phase 5)

## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project-level
- `.planning/PROJECT.md` — Core value, constraints, out-of-scope, key decisions
- `.planning/REQUIREMENTS.md` — v1 requirements (MICRO-01 through MICRO-05, MACRO-01 through MACRO-05)
- `.planning/ROADMAP.md` — Phase ordering, dependencies, success criteria
- `.planning/phases/01-data-foundation-rules-engine/01-CONTEXT.md` — Phase 1 decisions (data format, versioning, validation, reference year 2025)

### Research
- `.planning/research/STACK.md` — Technology stack (Rust/WASM, wasm-bindgen 0.2.121, ndarray 0.17, interpn 0.11.0, serde-wasm-bindgen 0.6.5)
- `.planning/research/ARCHITECTURE.md` — System architecture, Web Worker isolation, multi-linear interpolation, data flow
- `.planning/research/PITFALLS.md` — Pitfall 1 (WASM serialization tax), Pitfall 2 (extrapolation beyond convex hull), Pitfall 3 (DP budget exhaustion)

### Phase 1 Data Artifacts (consumed by Phase 2)
- `packages/tax-rules/parameters/` — YAML tax rules (31 files across IR/IS/TVA/cotisations/aides)
- `packages/data-pipeline/src/validation/export_fixtures.py` — JSON test fixtures for scenario pre-compute CI
- `packages/data-pipeline/src/shock_matrix/` — Grid construction, convex hull computation, Parquet/Zstd export
- `packages/data-pipeline/src/synthetic_pop/` — Synthetic population export (50K profiles, JSON, integrity hashes)

### External Domain References
- OpenFisca Core documentation — Entity/Parameter/Variable structure, formula API, period handling (used by backend + scenario pre-compute pipeline)
- `openfisca-france` Python package — Variable graph, formula implementations (source of truth for all fiscal computation)
- wasm-bindgen documentation — JS interop patterns, `wasm-pack build --target web`, serde integration
- interpn 0.11.0 documentation — Multi-linear interpolation API, dimension-major obs convention
- Postcard specification — Binary serialization format for shock matrix data transfer

## Existing Code Insights

### Reusable Assets
- `packages/wasm-macro/src/` — ShockMatrix, interpn interpolation, convex hull gating, trajectory projection. All preserved and battle-tested (12 tests passing, MACRO-05 compliant).
- `packages/core/src/` — Profile, Parameters, MicroResult, MacroResult, test fixtures. All preserved.
- `packages/tax-rules/parameters/` — Complete YAML rules. Used by scenario pre-compute CI pipeline (Python OpenFisca) instead of Rust runtime.
- `packages/data-pipeline/src/validation/` — Bilingual test fixtures. Adaptable for scenario pre-compute result validation.

### Deprecatable Code
- `packages/wasm-micro/src/generated/` — 3,336 lines of auto-generated Rust formula code. Replaced by scenario pre-compute + backend approach. Can be removed in a subsequent plan.
- `packages/wasm-micro/src/system.rs` — TaxBenefitSystem dispatcher calling generated formulas. Can be replaced with scenario data cache/loader.
- Code generator pipeline (`packages/data-pipeline/src/codegen/` or equivalent) — Python→Rust transpiler. No longer needed.

### Established Patterns
- Version-locking: all artifacts use semantic tags. Scenario data follows this pattern.
- CI version-consistency gate: grep-based checks. Extends to scenario data version validation.
- Postcard+gzip for WASM data loading (02-01). Candidate for scenario data transport.
- Dimension-major obs convention for interpn (02-05). Macro engine must preserve this.

### Integration Points
- Scenario pre-compute CI pipeline runs `openfisca-france` in CI, produces static data file consumed by browser.
- Macro engine (wasm-macro) integrates with scenario selector UI — sliders drive interpolation, scenario choice drives pre-computed citizen results.
- Backend OpenFisca endpoint (Phase 5) exposes compute for expert mode.

## Specific Ideas

- The scenario selector should start simple — a list of candidate names with a brief reform summary. Sub-scenarios (policy variants per candidate) can be added later.
- Macro engine sliders should remain functional in citizen mode — the citizen explores macro trajectory projections within their chosen scenario, even though the micro (household) results are pre-computed.
- The scenario pre-compute pipeline should reuse the Phase 1 bilingual validation framework — iterate canonical profiles through Python OpenFisca for each candidate's parameter set, export structured results.

## Deferred Ideas

- **Option A+ (sub-scenarios per candidate):** Extending candidate scenarios with policy variants (e.g., "Candidate A — full program" vs "Candidate A — tax only"). Future enhancement, not v1.
- **Fine-tuning sliders within scenarios:** Allowing citizens to adjust individual parameters beyond the pre-computed candidate program. Future phase — adds dimensionality to scenario data.

---

*Phase: 2-Core Simulation Engines (WASM)*
*Context gathered: 2026-05-13 (updated from 2026-05-12 original)*
